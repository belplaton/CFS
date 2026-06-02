"""
Internal API: per-user storage quota (Phase 4.3).

This endpoint is consumed by the file service on every upload to
decide whether the bytes fit the user's plan.  It is gated by
``X-API-Key`` rather than a user JWT — only sibling services are
allowed to call it.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.exceptions import UserNotFoundError
from src.models import get_db
from src.repositories.user import UserRepository
from src.schemas import QuotaResponse


router = APIRouter(prefix="/api/users", tags=["users"])


def _require_service_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    """Verify the caller is a sibling service.

    We accept either ``X-API-Key`` matching the configured shared
    secret OR a user JWT (left for the future ``/api/auth/...`` use).
    """
    if x_api_key is None or x_api_key != settings.service_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid X-API-Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )


@router.get(
    "/{user_id}/quota",
    response_model=QuotaResponse,
    dependencies=[Depends(_require_service_key)],
)
async def get_user_quota(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> QuotaResponse:
    user = await UserRepository.get_by_id(db, user_id)
    if user is None:
        raise UserNotFoundError(f"User {user_id} not found")
    # The tier is encoded in the quota itself: any value above the
    # default is treated as premium.  When the user model gains a
    # dedicated ``tier`` column in a later migration, replace this
    # heuristic with the column read.
    tier = "premium" if user.storage_quota > settings.default_storage_quota else "free"
    return QuotaResponse(
        user_id=user.id,
        tier=tier,
        storage_quota=user.storage_quota,
        used_storage=user.used_storage,
    )
