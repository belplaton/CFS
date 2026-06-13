"""Simple in-memory fixed-window rate limiter."""

from __future__ import annotations

from collections import defaultdict
import time

from fastapi import HTTPException, status

_rate_limit_store: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 30  # per window per user


def check_rate_limit(user_key: str) -> None:
    """Enforce a fixed-window rate limit. Raises 429 when exceeded."""
    now = time.monotonic()
    window_start = now - RATE_LIMIT_WINDOW
    _rate_limit_store[user_key] = [
        ts for ts in _rate_limit_store[user_key] if ts > window_start
    ]
    if len(_rate_limit_store[user_key]) >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again later.",
        )
    _rate_limit_store[user_key].append(now)
