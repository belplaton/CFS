"""
Trash service — list, restore, and purge soft-deleted items (Phase 2).

Phase 4 will add:
    * Cron job that purges items older than the retention window (30 days).
    * Cascading soft-delete when a folder is moved to trash.

All DB queries go through the file / folder repositories so this
module is purely orchestration.
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.exceptions import FileNotFound
from src.repositories.file import FileRepository
from src.repositories.folder import FolderRepository
from src.services import audit_service
from src.services.file_service import FileService
from src.services.folder_service import FolderService
from src.utils import minio_client
from src.utils.logging import get_logger


logger = get_logger(__name__)


class TrashService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_trash(self, user_id: UUID) -> list[dict]:
        files = await FileRepository.list_trashed(self.db, user_id)
        folders = await FolderRepository.list_trashed(self.db, user_id)

        items: list[dict] = []
        for f in folders:
            items.append({
                "id": f.id,
                "kind": "folder",
                "name": f.name,
                "size": 0,
                "original_parent_id": f.parent_id,
                "deleted_at": f.deleted_at,
            })
        for f in files:
            items.append({
                "id": f.id,
                "kind": "file",
                "name": f.name,
                "size": f.size,
                "mime_type": f.mime_type,
                "original_parent_id": f.folder_id,
                "deleted_at": f.deleted_at,
            })
        return items

    async def restore_item(self, item_id: UUID, user_id: UUID) -> None:
        if await FileRepository.get_trashed(self.db, item_id, user_id) is not None:
            await FileService(self.db).restore_file(item_id, user_id)
            return
        if await FolderRepository.get_trashed(self.db, item_id, user_id) is not None:
            await FolderService(self.db).restore_folder(item_id, user_id)
            return
        raise FileNotFound("Trash item not found")

    async def permanent_delete_item(self, item_id: UUID, user_id: UUID) -> None:
        if await FileRepository.get_trashed(self.db, item_id, user_id) is not None:
            await FileService(self.db).permanent_delete_file(item_id, user_id)
            return
        if await FolderRepository.get_trashed(self.db, item_id, user_id) is not None:
            await FolderService(self.db).permanent_delete_folder(item_id, user_id)
            return
        raise FileNotFound("Trash item not found")

    async def empty_trash(self, user_id: UUID) -> int:
        """
        Permanently delete everything in the user's trash.

        MinIO deletions are best-effort: failures are logged so that the
        DB-side cleanup can still proceed. A background reaper (Phase 4)
        will eventually collect any orphaned objects.
        """
        files = await FileRepository.list_trashed(self.db, user_id)

        count = 0
        for f in files:
            try:
                minio_client.remove(settings.minio_bucket, f.minio_object_id)
            except Exception:
                logger.exception(
                    "trash.minio_remove.failed",
                    object_key=f.minio_object_id,
                    user_id=str(user_id),
                )
            await FileRepository.delete(self.db, f)
            count += 1

        folders = await FolderRepository.list_trashed(self.db, user_id)
        for f in folders:
            await FolderRepository.delete(self.db, f)
            count += 1

        await self.db.flush()
        await audit_service.record_event(
            self.db,
            actor_id=user_id,
            event="trash.empty",
            extra={"files": len(files), "folders": len(folders)},
        )
        return count
