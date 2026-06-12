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

from src.config import settings
from src.exceptions import ConflictError, CycleDetected, FileNameConflict, FolderNotFound
from src.models.folder import Folder
from src.repositories.file import FileRepository
from src.repositories.folder import FolderRepository
from src.services import audit_service
from src.utils import minio_client
from src.utils.cursor import Cursor
from src.utils.logging import get_logger
from src.utils.validators import sanitize_filename


logger = get_logger(__name__)


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

    async def list_folders_page(
        self,
        user_id: UUID,
        parent_id: UUID | None,
        *,
        limit: int = 200,
        cursor: Cursor | None = None,
    ) -> tuple[list[Folder], str | None]:
        """Cursor-paginated variant of :meth:`list_folders` (Phase 4.5)."""
        fetch = limit + 1
        if cursor is None:
            rows = list(
                await FolderRepository.list_in_folder(
                    self.db, user_id, parent_id, limit=fetch, offset=0
                )
            )
        else:
            rows = list(
                await FolderRepository.list_in_folder_after(
                    self.db, user_id, parent_id, cursor, limit=fetch
                )
            )
        next_cursor: str | None = None
        if len(rows) > limit:
            rows = rows[:limit]
            last = rows[-1]
            next_cursor = Cursor(name=last.name, id=last.id).encode()
        return rows, next_cursor

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

    async def rename_folder(
        self, folder_id: UUID, user_id: UUID, raw_name: str
    ) -> None:
        folder = await self.get_folder(folder_id, user_id)
        new_name = sanitize_filename(raw_name)
        # Check for name conflict in the same parent.
        existing_names = await FolderRepository.list_existing_names_in_parent(
            self.db, user_id, folder.parent_id
        )
        if new_name in existing_names and new_name != folder.name:
            raise FileNameConflict(
                f"A folder named '{new_name}' already exists here",
                extra={"name": new_name},
            )
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
        """
        Soft-delete a folder and cascade to every descendant (Phase 4.1).

        The cascade runs in three steps inside the caller's transaction:

        1. BFS-walk the folder subtree (folder → children → grandchildren).
        2. Mark every visited folder ``deleted_at = now()``.
        3. Move every active file's MinIO object to ``trash/`` and
           mark the row ``deleted_at = now()``.

        Step 3 runs *after* step 2 so the file list query is bounded
        to the cascade set.  The MinIO copy is best-effort: a failure
        is logged but does not roll back the DB-side delete, because
        the TTL cleanup (Phase 4.2) will pick up the orphan on its
        next pass.  The DB row is the source of truth, not the bucket.
        """
        folder = await self.get_folder(folder_id, user_id)
        root_name = folder.name
        root_id = folder.id

        # 1. Collect the entire subtree (root + every descendant).
        subtree: list[UUID] = [root_id]
        frontier: list[UUID] = [root_id]
        hops = 0
        while frontier:
            children = await FolderRepository.list_child_ids(self.db, frontier, user_id)
            if not children:
                break
            subtree.extend(children)
            frontier = children
            hops += 1
            if hops > _MAX_ANCESTOR_HOPS:
                raise CycleDetected("Folder hierarchy is too deep to safely cascade")

        # 2. Mark every folder in the subtree as deleted.
        for fid in subtree:
            await self.db.execute(
                # Use a parameterised UPDATE; reload to keep ORM cache
                # consistent for the audit step below.
                Folder.__table__.update()
                .where(Folder.id == fid)
                .values(deleted_at=func.now())
            )

        # 3. Cascade to files: move each object's MinIO key to ``trash/``
        #    and mark the row deleted.
        files = list(
            await FolderRepository.list_active_files_in_folders(
                self.db, subtree, user_id
            )
        )
        for f in files:
            ext = minio_client.extract_extension(f.minio_object_id)
            new_key = minio_client.trash_object_key(user_id, ext)
            try:
                minio_client.move(
                    settings.minio_bucket,
                    f.minio_object_id,
                    new_key,
                    f.mime_type or "application/octet-stream",
                )
            except Exception as exc:  # noqa: BLE001 — best-effort
                logger.warning(
                    "trash.cascade.minio_failed",
                    file_id=str(f.id),
                    user_id=str(user_id),
                    error=str(exc),
                )
                # Reuse a fresh UUID-style key so a later retry does
                # not collide with a partially-moved object.
                new_key = f.minio_object_id
            f.minio_object_id = new_key
            f.deleted_at = func.now()

        await self.db.flush()

        # Audit per-item so the trash log has a row for every deleted
        # object (root folder + descendants + files).
        await audit_service.record_event(
            self.db,
            actor_id=user_id,
            event="folder.soft_delete",
            target_id=root_id,
            target_kind="folder",
            extra={
                "name": root_name,
                "cascaded_folders": len(subtree) - 1,
                "cascaded_files": len(files),
            },
        )
        for fid in subtree:
            if fid == root_id:
                continue
            await audit_service.record_event(
                self.db,
                actor_id=user_id,
                event="folder.soft_delete",
                target_id=fid,
                target_kind="folder",
                extra={"via_cascade": str(root_id)},
            )
        for f in files:
            await audit_service.record_event(
                self.db,
                actor_id=user_id,
                event="file.soft_delete",
                target_id=f.id,
                target_kind="file",
                extra={"via_cascade": str(root_id)},
            )

    async def restore_folder(self, folder_id: UUID, user_id: UUID) -> None:
        folder = await FolderRepository.get_trashed(self.db, folder_id, user_id)
        if folder is None:
            raise FolderNotFound("Folder not found in trash")

        subtree = await self._collect_subtree_ids(folder.id, user_id, any_state=True)
        subtree_set = set(subtree)

        if folder.parent_id is not None:
            parent = await FolderRepository.get_active(
                self.db, folder.parent_id, user_id
            )
            if parent is None:
                raise ConflictError(
                    "Cannot restore folder: original parent is missing or still trashed"
                )

        folders: list[Folder] = []
        for fid in subtree:
            row = await FolderRepository.get_any_state(self.db, fid, user_id)
            if row is not None:
                folders.append(row)

        files = list(
            await FolderRepository.list_files_in_folders(self.db, subtree, user_id)
        )

        await self._assert_restore_conflicts(user_id, folders, files, subtree_set)

        for row in folders:
            row.deleted_at = None

        for file in files:
            ext = minio_client.extract_extension(file.minio_object_id)
            new_key = minio_client.files_object_key(user_id, ext)
            try:
                minio_client.move(
                    settings.minio_bucket,
                    file.minio_object_id,
                    new_key,
                    file.mime_type or "application/octet-stream",
                )
                file.minio_object_id = new_key
            except Exception as exc:  # noqa: BLE001 — fail-open, DB key stays valid
                logger.warning(
                    "restore.folder.minio_move_failed",
                    file_id=str(file.id),
                    folder_id=str(folder_id),
                    user_id=str(user_id),
                    error=str(exc),
                )
            file.deleted_at = None

        await self.db.flush()
        await audit_service.record_event(
            self.db,
            actor_id=user_id,
            event="folder.restore",
            target_id=folder.id,
            target_kind="folder",
            extra={
                "restored_folders": len(folders),
                "restored_files": len(files),
            },
        )

    async def permanent_delete_folder(self, folder_id: UUID, user_id: UUID) -> None:
        folder = await FolderRepository.get_trashed(self.db, folder_id, user_id)
        if folder is None:
            raise FolderNotFound("Folder not found in trash")

        subtree = await self._collect_subtree_ids(folder.id, user_id, any_state=True)
        files = list(
            await FolderRepository.list_files_in_folders(self.db, subtree, user_id)
        )

        for file in files:
            # DB delete first, then MinIO remove.
            await self.db.delete(file)
            try:
                minio_client.remove(settings.minio_bucket, file.minio_object_id)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "permanent_delete_folder.minio_failed",
                    file_id=str(file.id),
                    key=file.minio_object_id,
                    error=str(exc),
                )

        await self.db.flush()
        await FolderRepository.delete(self.db, folder)
        await audit_service.record_event(
            self.db,
            actor_id=user_id,
            event="folder.permanent_delete",
            target_id=folder_id,
            target_kind="folder",
            extra={
                "deleted_folders": len(subtree),
                "deleted_files": len(files),
            },
        )

    # ==================== Helpers ====================

    async def _collect_subtree_ids(
        self,
        root_id: UUID,
        user_id: UUID,
        *,
        any_state: bool = False,
    ) -> list[UUID]:
        subtree: list[UUID] = [root_id]
        frontier: list[UUID] = [root_id]
        hops = 0
        while frontier:
            if any_state:
                children = await FolderRepository.list_child_ids_any_state(
                    self.db, frontier, user_id
                )
            else:
                children = await FolderRepository.list_child_ids(
                    self.db, frontier, user_id
                )
            if not children:
                break
            subtree.extend(children)
            frontier = children
            hops += 1
            if hops > _MAX_ANCESTOR_HOPS:
                raise CycleDetected("Folder hierarchy is too deep")
        return subtree

    async def _assert_restore_conflicts(
        self,
        user_id: UUID,
        folders: list[Folder],
        files: list,
        subtree_set: set[UUID],
    ) -> None:
        for folder in folders:
            existing_folder_names = (
                await FolderRepository.list_existing_names_in_parent(
                    self.db, user_id, folder.parent_id
                )
            )
            if folder.name in existing_folder_names:
                raise ConflictError(
                    f"Cannot restore folder '{folder.name}': name conflict in target parent"
                )

        for file in files:
            if file.folder_id is not None and file.folder_id not in subtree_set:
                parent = await FolderRepository.get_active(
                    self.db, file.folder_id, user_id
                )
                if parent is None:
                    raise ConflictError(
                        f"Cannot restore file '{file.name}': original parent is missing or still trashed"
                    )
            existing_file_names = await FileRepository.list_existing_names_in_folder(
                self.db, user_id, file.folder_id
            )
            if file.name in existing_file_names:
                raise ConflictError(
                    f"Cannot restore file '{file.name}': name conflict in target folder"
                )

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
                raise CycleDetected("Cannot move a folder into one of its descendants")
            current_id = await FolderRepository.get_parent_id(
                self.db, current_id, user_id
            )
            hops += 1
            if hops > _MAX_ANCESTOR_HOPS:
                # Defensive: if a corrupted tree exists, fail closed.
                raise CycleDetected("Folder hierarchy is too deep")
