"""
Phase 2 unit tests — no Postgres/MinIO/Redis required.

These tests cover the components that can be exercised in isolation:

* ``RequestIDMiddleware`` — generates / propagates ``X-Request-ID``
* ``RequestMetaMiddleware`` — captures client IP and User-Agent
* ``utils.rate_limiter`` — INCR-based fixed-window limit
* ``utils.idempotency`` — body-fingerprint cache + 409 on mismatch
* ``api.health`` — returns 200 / 503 based on probe results

The remaining Phase 2 surfaces (audit log persistence, schema
migrations) are covered by the testcontainers tests in
``test_file_service.py``.
"""
from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.middleware.idempotency import (
    _fingerprint,
    get_cached,
    set_cached,
)
from src.middleware.request_id import RequestIDMiddleware
from src.middleware.request_meta import RequestMetaMiddleware


# ==================== Fake Redis ====================


class FakeRedis:
    """Minimal in-memory Redis stand-in. Implements the subset of the
    ``redis.asyncio.Redis`` API used by the rate limiter and idempotency
    middleware: ``pipeline()``, ``incr``, ``expire``, ``get``, ``set``,
    ``ping``.
    """

    def __init__(self) -> None:
        self.kv: dict[str, tuple[str, int | None]] = {}  # key -> (value, expire-at or None)
        self.pings = 0

    async def ping(self) -> bool:
        self.pings += 1
        return True

    def pipeline(self, transaction: bool = True) -> "FakePipeline":
        return FakePipeline(self)

    async def get(self, key: str) -> str | None:
        self._expire_if_needed(key)
        if key not in self.kv:
            return None
        return self.kv[key][0]

    async def set(self, key: str, value: str, ex: int | None = None) -> bool:
        import time

        self.kv[key] = (value, int(time.time()) + ex if ex else None)
        return True

    async def incr(self, key: str) -> int:
        self._expire_if_needed(key)
        cur = int(self.kv.get(key, ("0", None))[0])
        cur += 1
        self.kv[key] = (str(cur), self.kv.get(key, (None, None))[1])
        return cur

    async def expire(self, key: str, ttl: int) -> bool:
        import time

        if key in self.kv:
            value, _ = self.kv[key]
            self.kv[key] = (value, int(time.time()) + ttl)
        return True

    def _expire_if_needed(self, key: str) -> None:
        import time

        if key in self.kv and self.kv[key][1] is not None and time.time() > self.kv[key][1]:
            del self.kv[key]


class FakePipeline:
    def __init__(self, redis: FakeRedis) -> None:
        self.redis = redis
        self._ops: list[tuple[str, tuple, dict]] = []

    def incr(self, key: str) -> "FakePipeline":
        self._ops.append(("incr", (key,), {}))
        return self

    def expire(self, key: str, ttl: int) -> "FakePipeline":
        self._ops.append(("expire", (key, ttl), {}))
        return self

    async def execute(self) -> list[Any]:
        results = []
        for op, args, kwargs in self._ops:
            results.append(await getattr(self.redis, op)(*args, **kwargs))
        return results


# ==================== Request ID ====================


def _build_request_id_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/echo")
    async def echo() -> dict:
        return {"ok": True}

    return app


@pytest.mark.asyncio
async def test_request_id_generated_when_absent() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_build_request_id_app()),
        base_url="http://test",
    ) as client:
        r = await client.get("/echo")
    assert r.status_code == 200
    assert "X-Request-ID" in r.headers
    assert len(r.headers["X-Request-ID"]) > 8  # uuid4 hex


@pytest.mark.asyncio
async def test_request_id_propagated_when_present() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_build_request_id_app()),
        base_url="http://test",
    ) as client:
        r = await client.get("/echo", headers={"X-Request-ID": "abc-123"})
    assert r.headers["X-Request-ID"] == "abc-123"


# ==================== Request meta ====================


def _build_request_meta_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestMetaMiddleware)

    @app.get("/meta")
    async def meta() -> dict:
        from src.utils.request_meta import current_request_meta

        m = current_request_meta()
        return {"ip": m.ip, "ua": m.user_agent}

    return app


@pytest.mark.asyncio
async def test_request_meta_captures_ip_and_ua() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_build_request_meta_app()),
        base_url="http://test",
    ) as client:
        r = await client.get(
            "/meta",
            headers={
                "User-Agent": "pytest-agent/1.0",
                "X-Forwarded-For": "203.0.113.5, 10.0.0.1",
            },
        )
    assert r.status_code == 200
    data = r.json()
    assert data["ip"] == "203.0.113.5"  # leftmost wins
    assert data["ua"] == "pytest-agent/1.0"


# ==================== Rate limiter ====================


@pytest.mark.asyncio
async def test_rate_limiter_increments_and_blocks(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.utils import rate_limiter

    fake = FakeRedis()
    monkeypatch.setattr(rate_limiter, "get_redis", lambda: fake)

    # 5 calls under the limit succeed (none raise).
    for _ in range(5):
        await rate_limiter.check_rate_limit(
            rate_limiter.RateLimit(name="test", limit=5, window_seconds=60),
            user_id="00000000-0000-0000-0000-000000000001",
        )

    # 6th call is over the limit.
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await rate_limiter.check_rate_limit(
            rate_limiter.RateLimit(name="test", limit=5, window_seconds=60),
            user_id="00000000-0000-0000-0000-000000000001",
        )
    assert exc.value.status_code == 429
    assert "Retry-After" in exc.value.headers


@pytest.mark.asyncio
async def test_rate_limiter_fails_open_on_redis_error(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.utils import rate_limiter

    class BrokenRedis:
        def pipeline(self, transaction: bool = True):
            raise RuntimeError("redis down")

        async def get(self, key: str):
            raise RuntimeError("redis down")

    monkeypatch.setattr(rate_limiter, "get_redis", lambda: BrokenRedis())

    # Should not raise even though Redis is down.
    await rate_limiter.check_rate_limit(
        rate_limiter.RateLimit(name="test", limit=1, window_seconds=60),
        user_id="00000000-0000-0000-0000-000000000002",
    )


# ==================== Idempotency ====================


@pytest.mark.asyncio
async def test_idempotency_fingerprint_changes_with_body() -> None:
    assert _fingerprint(b"hello") != _fingerprint(b"world")
    assert _fingerprint(b"") != _fingerprint(b"x")


@pytest.mark.asyncio
async def test_idempotency_cache_round_trip() -> None:
    fake = FakeRedis()
    user_id = uuid4()
    key = "test-key-1"

    cached = await get_cached(fake, user_id, key)
    assert cached is None

    await set_cached(
        fake, user_id, key,
        status_code=201,
        body=b'{"id":"abc"}',
        body_fingerprint="deadbeef",
    )
    cached = await get_cached(fake, user_id, key)
    assert cached is not None
    assert cached["status_code"] == 201
    assert json.loads(cached["body"]) == {"id": "abc"}
    assert cached["fingerprint"] == "deadbeef"


# ==================== Health check ====================


def _build_health_app() -> FastAPI:
    from src.api.health import _PROBES, router

    app = FastAPI()
    # Swap in fake probes for deterministic tests.
    new_probes = []
    for name, _ in _PROBES:
        new_probes.append((name, _fake_probe_factory(name)))
    # Mutating the global is fine in tests — pytest runs in fresh
    # interpreter per process when isolated.
    _PROBES.clear()
    _PROBES.extend(new_probes)
    app.include_router(router)
    return app


def _fake_probe_factory(name: str):
    """Build a probe that returns the value of ``HEALTH_STATE[name]``."""
    state = {"ok": True, "error": None}

    async def _probe() -> dict:
        return dict(state)

    # Tests mutate ``state`` via this side channel.
    _probe.state = state  # type: ignore[attr-defined]
    return _probe


@pytest.mark.asyncio
async def test_health_ok_when_all_probes_succeed() -> None:
    from src.api.health import _PROBES

    app = _build_health_app()
    # All probes default to ok=True.
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "healthy"
    for name, _ in _PROBES:
        assert body["checks"][name]["ok"] is True


@pytest.mark.asyncio
async def test_health_503_when_one_probe_fails() -> None:
    from src.api.health import _PROBES

    app = _build_health_app()
    # Make the database probe fail.  _PROBES is a list of (name, probe_fn)
    # tuples after _build_health_app has run.
    db_probe = next(p for n, p in _PROBES if n == "database")
    db_probe.state["ok"] = False
    db_probe.state["error"] = "connection refused"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/health")
    assert r.status_code == 503
    body = r.json()
    assert body["status"] == "unhealthy"
    assert body["checks"]["database"]["ok"] is False
    assert body["checks"]["minio"]["ok"] is True
    assert body["checks"]["redis"]["ok"] is True


# ==================== Logging ====================


def test_structlog_configures_json_in_production(capsys: pytest.CaptureFixture) -> None:
    from src.utils import logging as slog

    slog.configure_logging(env="production")
    log = slog.get_logger("test")
    log.info("event.test", foo="bar")
    out = capsys.readouterr().out
    assert "event.test" in out
    assert '"foo": "bar"' in out
    slog.clear_contextvars()


def test_structlog_console_in_development(capsys: pytest.CaptureFixture) -> None:
    from src.utils import logging as slog

    slog.configure_logging(env="development")
    log = slog.get_logger("test")
    log.info("dev.test", x=1)
    out = capsys.readouterr().out
    # ConsoleRenderer produces key=value style.
    assert "x=1" in out or "x = 1" in out
    slog.clear_contextvars()
