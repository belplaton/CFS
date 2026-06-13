"""
Internal service-to-service endpoints.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, status

from src.config import settings
from src.utils import auth_client


router = APIRouter(prefix="/api/internal", tags=["internal"])


def _require_service_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    if x_api_key is None or x_api_key != settings.service_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid X-API-Key",
        )


@router.delete("/quota-cache/{user_id}")
async def invalidate_quota_cache(
    user_id: UUID,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    _require_service_key(x_api_key)
    auth_client.invalidate(user_id)
    return {"status": "invalidated", "user_id": str(user_id)}
