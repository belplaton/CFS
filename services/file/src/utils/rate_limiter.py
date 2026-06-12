"""
Redis-backed fixed-window rate limiter.

Used to throttle abuse on expensive endpoints (uploads, deletes,
search, ...).  Returns 429 with ``Retry-After`` once the per-IP
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
from fastapi import Request

from src.config import settings
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

    name: str  # Bucket name; included in the Redis key and logs.
    limit: int  # Max requests in the window.
    window_seconds: int  # Window size.


# Sensible defaults for the file service.  These are not security
# secrets — they live in code so the policy is reviewable in PRs.
POLICY_UPLOAD = RateLimit(name="upload", limit=20, window_seconds=60)
POLICY_DELETE = RateLimit(name="delete", limit=60, window_seconds=60)
POLICY_DEFAULT = RateLimit(name="default", limit=300, window_seconds=60)


# ==================== Client IP resolution ====================


def _resolve_client_ip(request: Request) -> str:
    """Extract the client IP from X-Forwarded-For / X-Real-IP / peer."""
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    xri = request.headers.get("X-Real-IP")
    if xri:
        return xri.strip()
    if request.client:
        return request.client.host
    return "unknown"


# ==================== Core check ====================


async def _consume(redis: aioredis.Redis, policy: RateLimit, key_id: str) -> int:
    """
    Atomically increment the per-key counter for ``policy`` and return
    the new value.  The counter expires after one window so that an
    inactive key does not accumulate counters indefinitely.
    """
    now = int(time.time())
    window_id = now // policy.window_seconds
    key = f"rl:{policy.name}:{key_id}:{window_id}"
    pipe = redis.pipeline(transaction=True)
    pipe.incr(key)
    pipe.expire(key, policy.window_seconds)
    new_value, _ = await pipe.execute()
    return int(new_value)


async def check_rate_limit(
    policy: RateLimit,
    key_id: str,
) -> None:
    """
    Verify the caller is under ``policy``.  Raises a ``DomainError``
    (mapped to 429 by ``exception_handlers``) with the contract-
    compliant JSON body when the limit is exceeded.

    On Redis errors we fail **open**: a broken rate limiter must never
    break legitimate uploads.  The error is logged at WARN for
    operators.
    """
    try:
        count = await _consume(get_redis(), policy, key_id)
    except Exception as exc:  # noqa: BLE001 — fail open on any redis error
        logger.warning("rate_limiter.redis_error", error=str(exc), policy=policy.name)
        return

    if count > policy.limit:
        retry_after = policy.window_seconds - (int(time.time()) % policy.window_seconds)
        logger.info(
            "rate_limiter.exceeded",
            key_id=key_id,
            policy=policy.name,
            count=count,
            limit=policy.limit,
        )
        from src.exceptions import RateLimitExceeded

        raise RateLimitExceeded(retry_after=max(1, retry_after))


# ==================== FastAPI dependency factory ====================


def rate_limit(policy: RateLimit):
    """
    Build a FastAPI dependency that enforces ``policy`` for the
    caller's client IP (via ``X-Forwarded-For`` / ``X-Real-IP`` /
    ``request.client.host``).

    Usage::

        @router.post("/upload", dependencies=[Depends(rate_limit(POLICY_UPLOAD))])
        async def upload(...): ...
    """

    async def _dep(request: Request) -> None:
        ip = _resolve_client_ip(request)
        await check_rate_limit(policy, ip)

    return _dep
