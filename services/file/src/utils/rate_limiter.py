"""
Redis-backed fixed-window rate limiter.

Used to throttle abuse on expensive endpoints (uploads, deletes,
search, ...).  Returns 429 with ``Retry-After`` once the per-user
counter for the current window exceeds the configured limit.

The implementation is intentionally simple — a single ``INCR`` +
``EXPIRE`` per request — because:

* it is atomic on the Redis side (single command);
* per-window accuracy is more than good enough for "stop the abuse"
  use cases;
* we get free horizontal scalability (any service replica can check
  the same key).

The trade-off is bursty behaviour at the window boundary: a client can
fire ``2 * limit`` requests across two adjacent windows.  For the file
service this is acceptable; switch to a sliding window or token bucket
only if measured abuse patterns demand it.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, status

from src.config import settings
from src.utils.dependencies import get_current_user_id
from src.utils.logging import get_logger


logger = get_logger(__name__)


# ==================== Redis client ====================

_redis: Optional[aioredis.Redis] = None


def get_redis() -> aioredis.Redis:
    """Lazy singleton (matching the pattern used for the MinIO client)."""
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis


async def close_redis() -> None:
    """Close the Redis connection pool (call on shutdown)."""
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


# ==================== Configuration ====================


@dataclass(frozen=True)
class RateLimit:
    """A single rate-limit policy."""

    name: str           # Bucket name; included in the Redis key and logs.
    limit: int          # Max requests in the window.
    window_seconds: int # Window size.


# Sensible defaults for the file service.  These are not security
# secrets — they live in code so the policy is reviewable in PRs.
POLICY_UPLOAD = RateLimit(name="upload", limit=20, window_seconds=60)
POLICY_DELETE = RateLimit(name="delete", limit=60, window_seconds=60)
POLICY_DEFAULT = RateLimit(name="default", limit=300, window_seconds=60)


# ==================== Core check ====================


async def _consume(redis: aioredis.Redis, policy: RateLimit, user_id: str) -> int:
    """
    Atomically increment the per-user counter for ``policy`` and return
    the new value.  The counter expires after one window so that an
    inactive user does not accumulate counters indefinitely.
    """
    now = int(time.time())
    window_id = now // policy.window_seconds
    key = f"rl:{policy.name}:{user_id}:{window_id}"
    pipe = redis.pipeline(transaction=True)
    pipe.incr(key)
    pipe.expire(key, policy.window_seconds)
    new_value, _ = await pipe.execute()
    return int(new_value)


async def check_rate_limit(
    policy: RateLimit,
    user_id: str,
) -> None:
    """
    Verify the user is under ``policy``.  Raises ``HTTPException(429)``
    with a ``Retry-After`` header when the limit is exceeded.

    On Redis errors we fail **open**: a broken rate limiter must never
    break legitimate uploads.  The error is logged at WARN for
    operators.
    """
    try:
        count = await _consume(get_redis(), policy, user_id)
    except Exception as exc:  # noqa: BLE001 — fail open on any redis error
        logger.warning("rate_limiter.redis_error", error=str(exc), policy=policy.name)
        return

    if count > policy.limit:
        retry_after = policy.window_seconds - (int(time.time()) % policy.window_seconds)
        logger.info(
            "rate_limiter.exceeded",
            user_id=user_id,
            policy=policy.name,
            count=count,
            limit=policy.limit,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(max(1, retry_after))},
        )


# ==================== FastAPI dependency factory ====================


def rate_limit(policy: RateLimit):
    """
    Build a FastAPI dependency that enforces ``policy`` for the
    authenticated user.

    Usage::

        @router.post("/upload", dependencies=[Depends(rate_limit(POLICY_UPLOAD))])
        async def upload(...): ...
    """

    async def _dep(user_id=Depends(get_current_user_id)) -> None:
        await check_rate_limit(policy, str(user_id))

    return _dep
