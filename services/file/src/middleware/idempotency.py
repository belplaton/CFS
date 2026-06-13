"""
Idempotency-Key support for unsafe (POST/PUT/DELETE) endpoints.

Clients that retry requests (mobile apps on flaky networks, scripts
that re-send after a timeout) can attach an ``Idempotency-Key``
header.  The first successful response is cached in Redis; subsequent
requests with the same key — and the same body fingerprint — return
the cached response instead of executing the handler again.

This is the simplest and most common shape:

* If the key is new → run the handler, cache the response.
* If the key exists and body fingerprint matches → return cached.
* If the key exists and body fingerprint differs → 409 Conflict.

The TTL is conservative (24h).  A longer TTL would make
cross-instance retries safer but we don't need to keep the cache
around forever.

References: Stripe / IETF draft-ietf-httpapi-idempotency-key-header.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Optional
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.utils.logging import get_logger
from src.utils.rate_limiter import get_redis


logger = get_logger("idempotency")

_TTL_SECONDS = 24 * 60 * 60


def _fingerprint(body: bytes) -> str:
    return hashlib.sha256(body or b"").hexdigest()


def _cache_key(user_id: UUID, idempotency_key: str) -> str:
    return f"idemp:{user_id}:{idempotency_key}"


async def get_cached(
    redis: aioredis.Redis, user_id: UUID, idempotency_key: str
) -> Optional[dict[str, Any]]:
    raw = await redis.get(_cache_key(user_id, idempotency_key))
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


async def set_cached(
    redis: aioredis.Redis,
    user_id: UUID,
    idempotency_key: str,
    *,
    status_code: int,
    body: bytes,
    body_fingerprint: str,
) -> None:
    payload = {
        "status_code": status_code,
        "body": body.decode("utf-8", errors="replace"),
        "fingerprint": body_fingerprint,
    }
    await redis.set(
        _cache_key(user_id, idempotency_key),
        json.dumps(payload),
        ex=_TTL_SECONDS,
    )


# ==================== Middleware ====================
#
# Why middleware instead of a per-route dependency?  The handler has
# already read the (potentially large) request body by the time a
# dependency could fingerprint it.  Middleware gets the body once,
# fingerprints it, and (if a cache hit) returns immediately.  This
# also makes the protection work uniformly for every mutating
# endpoint, not just upload.


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Apply to the routes that should be idempotent.  The wrapped routes
    are matched on ``method + path prefix`` via ``PROTECTED``.
    """

    PROTECTED: list[tuple[str, str]] = [
        # (HTTP method, path prefix)
        ("POST", "/api/files/upload"),
    ]

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        path = request.url.path
        method = request.method

        if not any(method == m and path.startswith(p) for m, p in self.PROTECTED):
            return await call_next(request)

        key = request.headers.get("Idempotency-Key")
        if not key:
            # Header missing — behave as before, the handler still works.
            return await call_next(request)

        # Resolve user id.  This is a *second* decode of the JWT; the
        # handler will do it again, but JWT verification is cheap (HMAC
        # + dict lookups) and we want a clean error if the key is sent
        # anonymously.
        from jose import JWTError, jwt  # local import keeps middleware module light

        from src.config import settings

        auth = request.headers.get("Authorization", "")
        if not auth.lower().startswith("bearer "):
            return await call_next(request)

        token = auth.split(" ", 1)[1].strip()
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
                audience=settings.jwt_audience,
                issuer=settings.jwt_issuer,
            )
        except JWTError:
            return await call_next(request)
        if payload.get("type") != "access":
            return await call_next(request)

        sub = payload.get("sub")
        if not sub or not isinstance(sub, str):
            return await call_next(request)
        try:
            user_id = UUID(sub)
        except (ValueError, TypeError):
            return await call_next(request)

        # Buffer the body so we can both fingerprint and forward it.
        body_bytes = await request.body()

        # Re-inject the body for downstream handlers.
        async def _receive() -> dict[str, Any]:
            return {"type": "http.request", "body": body_bytes, "more_body": False}

        request._receive = _receive  # type: ignore[attr-defined]

        fingerprint = _fingerprint(body_bytes)
        redis = get_redis()
        cached = await get_cached(redis, user_id, key)
        if cached is not None:
            if cached.get("fingerprint") != fingerprint:
                logger.info(
                    "idempotency.conflict",
                    user_id=str(user_id),
                    idempotency_key=key[:8] + "...",
                )
                return JSONResponse(
                    status_code=status.HTTP_409_CONFLICT,
                    content={
                        "error": "idempotency_conflict",
                        "detail": "Idempotency-Key was already used with a different request body",
                    },
                )
            logger.info(
                "idempotency.cache_hit",
                user_id=str(user_id),
                idempotency_key=key[:8] + "...",
            )
            return Response(
                content=cached["body"],
                status_code=cached["status_code"],
                media_type="application/json",
            )

        response: Response = await call_next(request)
        if 200 <= response.status_code < 300:
            resp_body = b""
            async for chunk in response.body_iterator:  # type: ignore[attr-defined]
                resp_body += chunk
            await set_cached(
                redis,
                user_id,
                key,
                status_code=response.status_code,
                body=resp_body,
                body_fingerprint=fingerprint,
            )
            # Re-build the response with a readable body iterator since
            # the original has been consumed.
            return Response(
                content=resp_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
        return response
