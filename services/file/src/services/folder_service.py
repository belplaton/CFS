"""
Folder service — business logic for folder operations (Phase 2: repository pattern).

Cycle detection on ``move_folder`` is the main business rule;
everything else (CRUD, listing, soft-delete) goes through
:class:`src.repositories.folder.FolderRepository`.
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions import CycleDetected, FolderNotFound
from src.models.folder import Folder
from src.repositories.folder import FolderRepository
from src.services import audit_service
from src.utils.validators import sanitize_filename


# Guard against pathologically deep folder chains.
_MAX_ANCESTOR_HOPS = 1000


class FolderService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ==================== Read ====================

    async def get_folder(self, folder_id: UUID, user_id: UUID) -> Folder:
        folder = await FolderRepository.get_active(self.db, folder_id, user_id)
        if folder is None:
            raise FolderNotFound("Folder not found")
        return folder

    async def list_folders(
        self,
        user_id: UUID,
        parent_id: UUID | None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[Folder]:
        return list(
            await FolderRepository.list_in_folder(
                self.db, user_id, parent_id, limit=limit, offset=offset
            )
        )

    # ==================== Create / rename / move / delete ====================

    async def create_folder(
        self, user_id: UUID, raw_name: str, parent_id: UUID | None
    ) -> Folder:
        name = sanitize_filename(raw_name)
        if parent_id is not None:
            await self.get_folder(parent_id, user_id)

        folder = Folder(
            user_id=user_id,
            parent_id=parent_id,
            name=name,
        )
        await FolderRepository.add(self.db, folder)
        await audit_service.record_event(
            self.db,
            actor_id=user_id,
            event="folder.create",
            target_id=folder.id,
            target_kind="folder",
            extra={"name": name, "parent_id": str(parent_id) if parent_id else None},
        )
        return folder

    async def rename_folder(self, folder_id: UUID, user_id: UUID, raw_name: str) -> None:
        folder = await self.get_folder(folder_id, user_id)
        new_name = sanitize_filename(raw_name)
        folder.name = new_name
        await self.db.flush()
        await audit_service.record_event(
            self.db,
            actor_id=user_id,
            event="folder.rename",
            target_id=folder_id,
            target_kind="folder",
            extra={"new_name": new_name},
        )

    async def move_folder(
        self, folder_id: UUID, user_id: UUID, parent_id: UUID | None
    ) -> None:
        folder = await self.get_folder(folder_id, user_id)

        if parent_id is not None:
            # Validate the destination exists and belongs to the user.
            await self.get_folder(parent_id, user_id)
            # Reject cycles: walking up from the destination must never
            # bring us back to the folder being moved.
            await self._assert_no_cycle(folder_id, parent_id, user_id)

        folder.parent_id = parent_id
        await self.db.flush()
        await audit_service.record_event(
            self.db,
            actor_id=user_id,
            event="folder.move",
            target_id=folder_id,
            target_kind="folder",
            extra={"parent_id": str(parent_id) if parent_id else None},
        )

    async def delete_folder(self, folder_id: UUID, user_id: UUID) -> None:
        folder = await self.get_folder(folder_id, user_id)
        folder_name = folder.name
        folder.deleted_at = func.now()
        await self.db.flush()
        await audit_service.record_event(
            self.db,
            actor_id=user_id,
            event="folder.soft_delete",
            target_id=folder_id,
            target_kind="folder",
            extra={"name": folder_name},
        )
        # Phase 4: cascade soft-delete to descendants + MinIO objects.

    # ==================== Helpers ====================

    async def _assert_no_cycle(
        self, moving_id: UUID, target_parent_id: UUID, user_id: UUID
    ) -> None:
        """
        Walk up the parent chain from ``target_parent_id``. If we encounter
        ``moving_id``, the move would create a cycle.
        """
        current_id: UUID | None = target_parent_id
        hops = 0
        while current_id is not None:
            if current_id == moving_id:
                raise CycleDetected(
                    "Cannot move a folder into one of its descendants"
                )
            current_id = await FolderRepository.get_parent_id(
                self.db, current_id, user_id
            )
            hops += 1
            if hops > _MAX_ANCESTOR_HOPS:
                # Defensive: if a corrupted tree exists, fail closed.
                raise CycleDetected("Folder hierarchy is too deep")
