"""
Tiny async Redis client singleton.

Centralises the connection so the rate limiter and (future)
refresh-token revocation list share a single asyncio pool.  When
Redis is unconfigured we return a no-op stub that swallows writes
and returns ``None`` for reads; this keeps the rest of the
application code branch-free.
"""
from __future__ import annotations

from typing import Optional

import redis.asyncio as aioredis

from src.config import settings
from src.utils.logging import get_logger


logger = get_logger(__name__)


_client: Optional[aioredis.Redis] = None
_initialised: bool = False


class _NullRedis:
    """No-op Redis stub used when REDIS_URL is unset."""

    async def incr(self, *_args, **_kwargs):
        return 0

    async def expire(self, *_args, **_kwargs):
        return True

    async def ttl(self, *_args, **_kwargs):
        return -1

    async def get(self, *_args, **_kwargs):
        return None

    async def set(self, *_args, **_kwargs):
        return True

    async def setex(self, *_args, **_kwargs):
        return True

    async def delete(self, *_args, **_kwargs):
        return 0

    async def ping(self):
        return False

    async def close(self):
        return None

    async def sadd(self, *_args, **_kwargs):
        return 0

    async def srem(self, *_args, **_kwargs):
        return 0

    async def sismember(self, *_args, **_kwargs):
        return False

    async def exists(self, *_args, **_kwargs):
        return 0


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
