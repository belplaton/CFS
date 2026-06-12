"""
Folder API endpoints (Phase 1: cycle-safe, uses domain exceptions).
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import get_db
from src.schemas import FolderCreate, FolderResponse, FolderUpdate
from src.services.folder_service import FolderService
from src.utils.dependencies import get_current_user_id
from src.utils.rate_limiter import POLICY_DEFAULT, rate_limit


router = APIRouter(prefix="/api/folders", tags=["Folders"])


@router.post(
    "/",
    response_model=FolderResponse,
    status_code=201,
    dependencies=[Depends(rate_limit(POLICY_DEFAULT))],
)
async def create_folder(
    body: FolderCreate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await FolderService(db).create_folder(user_id, body.name, body.parent_id)


@router.get(
    "/",
    response_model=list[FolderResponse],
    dependencies=[Depends(rate_limit(POLICY_DEFAULT))],
)
async def list_folders(
    parent_id: Optional[UUID] = None,
    limit: int = 200,
    offset: int = 0,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await FolderService(db).list_folders(
        user_id, parent_id, limit=limit, offset=offset
    )


@router.get(
    "/{folder_id}",
    response_model=FolderResponse,
    dependencies=[Depends(rate_limit(POLICY_DEFAULT))],
)
async def get_folder(
    folder_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await FolderService(db).get_folder(folder_id, user_id)


@router.patch(
    "/{folder_id}",
    dependencies=[Depends(rate_limit(POLICY_DEFAULT))],
)
async def update_folder(
    folder_id: UUID,
    body: FolderUpdate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = FolderService(db)
    payload = body.model_dump(exclude_unset=True)
    if "name" in payload:
        await svc.rename_folder(folder_id, user_id, payload["name"])
    if "parent_id" in payload:
        await svc.move_folder(folder_id, user_id, payload["parent_id"])
    return {"status": "updated"}


@router.delete(
    "/{folder_id}",
    dependencies=[Depends(rate_limit(POLICY_DEFAULT))],
)
async def delete_folder(
    folder_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await FolderService(db).delete_folder(folder_id, user_id)
    return {"status": "moved to trash"}
