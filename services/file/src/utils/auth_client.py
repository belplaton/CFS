"""
Auth Service HTTP client (Phase 4.3).

Used by the file service to ask Auth "what's this user's quota?".
The client is intentionally minimal — a single endpoint, with a
TTL cache to avoid hitting Auth on every upload.

Cache strategy
--------------
* Per-user ``QuotaInfo`` cached for ``QUOTA_CACHE_TTL`` seconds.
* Cache miss + Auth call failure → fall back to the
  ``settings.default_storage_quota`` and log a warning.  This is
  the same fail-open policy as the rate limiter: better to
  occasionally over-quota a user than to deny all uploads when
  Auth is down.
* Cache hit → no network call.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

import httpx

from src.config import settings
from src.utils.logging import get_logger


logger = get_logger(__name__)


QUOTA_CACHE_TTL = 60.0  # seconds


@dataclass(frozen=True)
class QuotaInfo:
    user_id: UUID
    tier: str
    storage_quota: int
    used_storage: int


_cache: dict[UUID, tuple[float, QuotaInfo]] = {}


async def fetch_quota(user_id: UUID) -> QuotaInfo:
    """
    Return the user's quota, cached for ``QUOTA_CACHE_TTL`` seconds.

    Falls back to the local default on cache miss + Auth failure.
    """
    now = time.monotonic()
    cached = _cache.get(user_id)
    if cached is not None and now - cached[0] < QUOTA_CACHE_TTL:
        return cached[1]

    info: Optional[QuotaInfo] = None
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(
                f"{settings.auth_service_url.rstrip('/')}/api/users/{user_id}/quota",
                headers={"X-API-Key": settings.service_api_key},
            )
            if resp.status_code == 200:
                data = resp.json()
                info = QuotaInfo(
                    user_id=user_id,
                    tier=str(data.get("tier", "free")),
                    storage_quota=int(data["storage_quota"]),
                    used_storage=int(data.get("used_storage", 0)),
                )
            else:
                logger.warning(
                    "auth.quota.bad_status",
                    user_id=str(user_id),
                    status_code=resp.status_code,
                )
    except Exception as exc:  # noqa: BLE001 — fail-open
        logger.warning(
            "auth.quota.unreachable",
            user_id=str(user_id),
            error=str(exc),
        )

    if info is None:
        info = QuotaInfo(
            user_id=user_id,
            tier="free",
            storage_quota=settings.default_storage_quota,
            used_storage=0,
        )

    _cache[user_id] = (now, info)
    return info


def invalidate(user_id: UUID) -> None:
    """Drop the cached entry — call after a successful upload."""
    _cache.pop(user_id, None)
