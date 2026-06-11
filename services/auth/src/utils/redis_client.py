"""
Tiny async Redis client singleton.

Centralises the connection so the rate limiter and (future)
refresh-token revocation list share a single asyncio pool.  When
Redis is unconfigured we return a no-op stub that swallows writes
and returns ``None`` for reads; this keeps the rest of the
application code branch-free.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import redis.asyncio as aioredis

from src.config import settings
from src.utils.logging import get_logger


logger = get_logger(__name__)


_client: Optional[aioredis.Redis] = None
_initialised: bool = False


class _NullRedis:
    """No-op Redis stub used when REDIS_URL is unset."""

    def __init__(self) -> None:
        self._values: dict[str, tuple[str, datetime | None]] = {}

    def _cleanup(self, key: str) -> None:
        value = self._values.get(key)
        if value is None:
            return
        _, expires_at = value
        if expires_at is not None and expires_at <= datetime.now(timezone.utc):
            self._values.pop(key, None)

    async def incr(self, *_args, **_kwargs):
        return 0

    async def get(self, *_args, **_kwargs):
        key = _args[0] if _args else None
        if key is None:
            return None
        self._cleanup(key)
        value = self._values.get(key)
        return value[0] if value else None

    async def set(self, *_args, **_kwargs):
        if len(_args) >= 2:
            self._values[_args[0]] = (str(_args[1]), None)
        return True

    async def setex(self, *_args, **_kwargs):
        if len(_args) >= 3:
            key = _args[0]
            seconds = int(_args[1])
            value = str(_args[2])
            self._values[key] = (
                value,
                datetime.now(timezone.utc) + timedelta(seconds=seconds),
            )
        return True

    async def delete(self, *_args, **_kwargs):
        deleted = 0
        for key in _args:
            if key in self._values:
                self._values.pop(key, None)
                deleted += 1
        return deleted

    async def ping(self):
        return 0

    async def close(self):
        self._values.clear()
        return None

    async def sadd(self, *_args, **_kwargs):
        return 0

    async def srem(self, *_args, **_kwargs):
        return 0

    async def sismember(self, *_args, **_kwargs):
        return False

    async def exists(self, *_args, **_kwargs):
        count = 0
        for key in _args:
            self._cleanup(key)
            if key in self._values:
                count += 1
        return count

    async def ttl(self, *_args, **_kwargs):
        key = _args[0] if _args else None
        if key is None:
            return -1
        self._cleanup(key)
        value = self._values.get(key)
        if value is None or value[1] is None:
            return -1
        delta = value[1] - datetime.now(timezone.utc)
        return max(int(delta.total_seconds()), -1)

    async def expire(self, *_args, **_kwargs):
        if len(_args) < 2:
            return False
        key = _args[0]
        seconds = int(_args[1])
        value = await self.get(key)
        if value is None:
            return False
        self._values[key] = (
            value,
            datetime.now(timezone.utc) + timedelta(seconds=seconds),
        )
        return True


_null = _NullRedis()


def get_redis() -> aioredis.Redis:
    """Return the shared async Redis client, or the no-op stub."""
    global _client, _initialised
    if _initialised:
        return _client or _null

    _initialised = True
    url = settings.redis_url
    if not url:
        logger.warning("redis_not_configured", hint="rate limiter is in fail-open mode")
        return _null

    try:
        _client = aioredis.from_url(url, encoding="utf-8", decode_responses=True)
    except Exception as exc:  # noqa: BLE001
        logger.error("redis_init_failed", error=str(exc))
        _client = None
    return _client or _null


async def close_redis() -> None:
    """Close the shared client on shutdown."""
    global _client, _initialised
    if _client is not None:
        try:
            await _client.close()
        except Exception:  # noqa: BLE001
            pass
    _client = None
    _initialised = False
