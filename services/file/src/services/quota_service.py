"""
Quota service — storage limit checks and atomic reservations.

Phase 1 implementation: all users share the default quota tier. The hook
for a premium tier is already in place via ``get_storage_quota`` so that
Phase 2 only has to swap in a call to the Auth service.

The race-condition fix is the important bit: we use a Postgres
``pg_advisory_xact_lock`` keyed on ``user_id`` so that two concurrent
uploads for the same user serialise on a transaction-scoped lock. The
lock is released automatically on commit or rollback.
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.exceptions import QuotaExceeded
from src.utils.logging import get_logger


logger = get_logger(__name__)


# ==================== Quota tier ====================

async def get_storage_quota(_user_id: UUID) -> int:
    """
    Return the quota in bytes for the given user.

    Phase 1 always returns the default tier. Phase 2 will call the Auth
    service to resolve a per-user ``subscription`` (free / premium).
    """
    return settings.default_storage_quota


# ==================== Atomic reservation ====================

async def reserve_quota(
    db: AsyncSession,
    user_id: UUID,
    incoming_size: int,
) -> int:
    """
    Reserve storage for an upload of ``incoming_size`` bytes.

    Must be called inside the same transaction that inserts the ``File``
    row. Returns the new used-storage value (for instrumentation /
    quota-bar response).

    Raises ``QuotaExceeded`` if the upload would push the user over the
    limit.
    """
    if incoming_size < 0:
        raise ValueError("incoming_size must be non-negative")

    quota = await get_storage_quota(user_id)

    # Serialise concurrent uploads for this user. The lock is auto-released
    # on commit/rollback because we use the ``_xact_`` variant.
    # ``hashtextextended`` returns a bigint; using the user id as the seed
    # makes the lock key deterministic per user.
    await db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(CAST(:uid AS text), 0))"),
        {"uid": str(user_id)},
    )

    used = await _sum_active_size(db, user_id)

    if used + incoming_size > quota:
        logger.info(
            "quota.exceeded",
            user_id=str(user_id),
            used=used,
            incoming=incoming_size,
            quota=quota,
        )
        raise QuotaExceeded(
            "Storage quota exceeded",
            extra={"used": used, "incoming": incoming_size, "quota": quota},
        )

    return used + incoming_size


async def _sum_active_size(db: AsyncSession, user_id: UUID) -> int:
    """Sum sizes of non-deleted files for the user."""
    result = await db.execute(
        text(
            """
            SELECT COALESCE(SUM(size), 0)
            FROM files
            WHERE user_id = :uid AND deleted_at IS NULL
            """
        ),
        {"uid": str(user_id)},
    )
    return int(result.scalar() or 0)


async def get_usage(db: AsyncSession, user_id: UUID) -> int:
    """Public read-only helper used by GET /quota and similar endpoints."""
    return await _sum_active_size(db, user_id)
