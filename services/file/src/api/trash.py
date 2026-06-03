"""
Trash API endpoints
"""
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import get_db
from src.schemas import TrashItemResponse
from src.services.trash_service import TrashService
from src.utils.dependencies import get_current_user_id

router = APIRouter(prefix="/api/trash", tags=["Trash"])


@router.get("/", response_model=list[TrashItemResponse])
async def list_trash(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    items = await TrashService(db).list_trash(user_id)
    return items


@router.post("/{item_id}/restore")
async def restore_from_trash(
    item_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await TrashService(db).restore_item(item_id, user_id)
    return {"status": "restored"}


@router.delete("/{item_id}/permanent")
async def permanent_delete(
    item_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await TrashService(db).permanent_delete_item(item_id, user_id)
    return {"status": "deleted permanently"}


@router.post("/empty")
async def empty_trash(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    count = await TrashService(db).empty_trash(user_id)
    return {"status": "trash emptied", "deleted": count}
