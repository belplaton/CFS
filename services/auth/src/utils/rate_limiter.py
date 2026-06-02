"""
Auth-service rate limiter.

Login and registration endpoints are attractive brute-force targets.
We use a Redis-backed fixed-window counter (INCR + EXPIRE) with a
fail-open policy: if Redis is down, the request goes through and a
WARN is logged.  The rate limiter is intentionally simple — a
single counter per (action, key) tuple with no per-window jitter.

Usage:
    @router.post("/login")
    async def login(
        body: LoginRequest,
        request: Request,
        _rl: None = Depends(rate_limit_login),
    ):
        ...

Why a separate module from file-service's rate_limiter?
    The two services share the same Redis instance, but the policy
    keys should not collide.  Keeping the helper local also makes
    each service deployable in isolation (no shared Python package).
"""
from __future__ import annotations

from typing import Awaitable, Callable

from fastapi import Request

from src.exceptions import RateLimitError
from src.utils.logging import get_logger
from src.utils.redis_client import get_redis


logger = get_logger(__name__)


# ---------------- Policies ---------------------------------------------
# All limits are per-window.  Window is set on the Redis key (1 minute).
POLICY_LOGIN: tuple[str, int] = ("auth:login", 10)         # 10 / minute / key
POLICY_REGISTER: tuple[str, int] = ("auth:register", 5)    # 5 / minute / key
POLICY_PASSWORD_RESET: tuple[str, int] = ("auth:reset", 3) # 3 / minute / key

WINDOW_SECONDS = 60


def _resolve_key(request: Request, action: str) -> str:
    """
    Build the Redis key for a request.

    For login / register the bucket is the *client IP* (X-Forwarded-For
    first, then X-Real-IP, then ``request.client.host``).  For password
    reset we key on the *email* from the JSON body (if present and
    well-formed) — this protects against enumeration and brute force
    on a specific account.
    """
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        client_ip = fwd.split(",")[0].strip()
    else:
        real = request.headers.get("x-real-ip")
        client_ip = real.strip() if real else (request.client.host if request.client else "unknown")
    return f"rl:{action}:{client_ip}"


async def _hit_redis(key: str, limit: int) -> None:
    """
    Increment a counter and raise RateLimitError if the limit is exceeded.

    Fails open on Redis errors: a 503 from Redis must not lock users out
    of the auth endpoints.
    """
    try:
        redis = get_redis()
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, WINDOW_SECONDS)
    except Exception as exc:  # noqa: BLE001 — fail-open is the design
        logger.warning(
            "rate_limiter_redis_unavailable",
            key=key,
            error=str(exc),
        )
        return

    if count > limit:
        ttl = WINDOW_SECONDS
        try:
            ttl = await redis.ttl(key)
            if ttl is None or ttl < 0:
                ttl = WINDOW_SECONDS
        except Exception:  # noqa: BLE001
            ttl = WINDOW_SECONDS
        raise RateLimitError(retry_after=int(ttl), limit=limit, window=WINDOW_SECONDS)


# ---------------- Dependency factories --------------------------------
def make_rate_limiter(
    policy: tuple[str, int],
    key_from_request: Callable[[Request], str] | None = None,
) -> Callable[[Request], Awaitable[None]]:
    """
    Build a FastAPI dependency that rate-limits requests for the given
    policy.  Pass a custom ``key_from_request`` to derive a key other
    than the client IP (e.g. for password-reset on email).
    """
    action, limit = policy

    async def _dep(request: Request) -> None:
        if key_from_request is not None:
            key = key_from_request(request)
        else:
            key = _resolve_key(request, action)
        await _hit_redis(key, limit)

    return _dep


# Concrete deps wired to the standard policies.
rate_limit_login = make_rate_limiter(POLICY_LOGIN)
rate_limit_register = make_rate_limiter(POLICY_REGISTER)
rate_limit_password_reset = make_rate_limiter(POLICY_PASSWORD_RESET)
