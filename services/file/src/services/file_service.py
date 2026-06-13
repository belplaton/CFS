"""
File service — business logic for file operations (Phase 2: repository pattern).

All persistence goes through :class:`src.repositories.file.FileRepository`
and :class:`src.repositories.folder.FolderRepository`; this module only
encodes the rules: validation, ownership, quota, soft-delete semantics,
and audit logging.
"""

from __future__ import annotations

import os
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.exceptions import (
    ConflictError,
    FileNameConflict,
    FileNotFound,
    FolderNotFound,
    InvalidFileName,
    PayloadTooLarge,
)
from src.models.file import File
from src.repositories.file import FileRepository
from src.repositories.folder import FolderRepository
from src.schemas import FileUploadResponse
from src.services import audit_service, quota_service
from src.utils import minio_client
from src.utils.conflict import find_available_name, suggest_rename
from src.utils.cursor import Cursor
from src.utils.logging import get_logger
from src.utils.validators import (
    sanitize_filename,
    validate_extension,
    validate_mime_type,
)


logger = get_logger(__name__)

_TEXT_PREVIEW_MAX_BYTES = 256 * 1024


class FileService:
    """Stateless service — ``db`` is the only collaborator it needs."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ==================== Read ====================

    async def get_file(self, file_id: UUID, user_id: UUID) -> File:
        file = await FileRepository.get_active(self.db, file_id, user_id)
        if file is None:
            raise FileNotFound("File not found")
        return file

    async def list_files(
        self,
        user_id: UUID,
        folder_id: UUID | None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[File]:
        return list(
            await FileRepository.list_in_folder(
                self.db, user_id, folder_id, limit=limit, offset=offset
            )
        )

    async def list_files_page(
        self,
        user_id: UUID,
        folder_id: UUID | None,
        *,
        limit: int = 200,
        cursor: Cursor | None = None,
    ) -> tuple[list[File], str | None]:
        """
        Cursor-paginated list (Phase 4.5).

        Fetches ``limit + 1`` rows: if the extra row is present there
        is at least one more page, and we encode the *last returned*
        item as the next cursor.
        """
        fetch = limit + 1
        if cursor is None:
            rows = list(
                await FileRepository.list_in_folder(
                    self.db, user_id, folder_id, limit=fetch, offset=0
                )
            )
        else:
            rows = list(
                await FileRepository.list_in_folder_after(
                    self.db, user_id, folder_id, cursor, limit=fetch
                )
            )
        next_cursor: str | None = None
        if len(rows) > limit:
            rows = rows[:limit]
            last = rows[-1]
            next_cursor = Cursor(name=last.name, id=last.id).encode()
        return rows, next_cursor

    # ==================== Upload ====================

    async def upload_file(
        self,
        user_id: UUID,
        folder_id: UUID | None,
        raw_filename: str | None,
        content_type: str | None,
        file_data: bytes,
        *,
        on_conflict: str = "reject",
    ) -> FileUploadResponse:
        """
        Atomically upload a file.

        Steps:
            1. Sanitize filename + validate extension and MIME.
            2. Enforce size limit.
            3. Verify folder ownership (if given).
            4. Resolve name conflicts (``on_conflict="reject"|"rename"``).
            5. Take a per-user advisory lock and check the quota.
            6. Stream the bytes into MinIO under a unique key.
            7. Insert the ``File`` row.

        If step 6 succeeds but step 7 fails, we make a best-effort attempt
        to delete the MinIO object so the storage does not leak.
        """
        # 1. Filename
        filename = sanitize_filename(raw_filename)
        # Extension must match the whitelist. Use the *sanitized* name so
        # a sneaky "report.pdf.exe" cannot bypass the check.
        validate_extension(filename)
        ext = os.path.splitext(filename)[1].lstrip(".").lower()

        # 2. Size
        size = len(file_data)
        if size == 0:
            raise InvalidFileName("Empty file is not allowed")
        if size > settings.max_upload_size:
            raise PayloadTooLarge(
                f"File exceeds the {settings.max_upload_size}-byte upload limit",
                extra={"size": size, "limit": settings.max_upload_size},
            )

        # 3. MIME (best-effort validation of the declared content type)
        mime = validate_mime_type(content_type)

        # 4. Folder ownership (raises FolderNotFound -> 404 if not owned)
        if folder_id is not None:
            await self._assert_folder_owned(folder_id, user_id)

        # 5. Conflict resolution (Phase 4.4)
        if on_conflict == "rename":
            filename = await find_available_name(self.db, user_id, folder_id, filename)
        else:
            from src.exceptions import FileNameConflict

            existing = await FileRepository.list_existing_names_in_folder(
                self.db, user_id, folder_id
            )
            existing |= await FolderRepository.list_existing_names_in_parent(
                self.db, user_id, folder_id
            )
            if filename in existing:
                raise FileNameConflict(
                    f"A file named '{filename}' already exists in this folder",
                    suggested_name=suggest_rename(filename),
                    extra={"name": filename},
                )

        # 6. Quota reservation — acquires per-user advisory lock
        await quota_service.reserve_quota(self.db, user_id, size)
        # Invalidate the per-user quota cache so the next read reflects
        # the new usage.  We invalidate *after* reserve_quota — if it
        # raised, the in-memory cache is still valid.
        from src.utils import auth_client

        auth_client.invalidate(user_id)

        # 6. Upload to MinIO
        object_key = minio_client.files_object_key(user_id, ext)
        try:
            minio_client.put_bytes(
                settings.minio_bucket,
                object_key,
                file_data,
                mime,
            )
        except Exception:
            # Nothing to roll back in the DB yet — let the exception
            # propagate and let ``get_db`` rollback the transaction.
            logger.exception(
                "minio.upload.failed",
                user_id=str(user_id),
                object_key=object_key,
            )
            raise

        # 7. Insert DB row
        file_row = File(
            user_id=user_id,
            folder_id=folder_id,
            name=filename,
            size=size,
            mime_type=mime,
            minio_object_id=object_key,
        )
        try:
            await FileRepository.add(self.db, file_row)
        except Exception:
            logger.exception(
                "db.insert.failed.compensating",
                user_id=str(user_id),
                object_key=object_key,
            )
            minio_client.remove(settings.minio_bucket, object_key)
            raise

        logger.info(
            "file.uploaded",
            file_id=str(file_row.id),
            user_id=str(user_id),
            name=filename,
            size=size,
        )

        await audit_service.record_event(
            self.db,
            actor_id=user_id,
            event="file.upload",
            target_id=file_row.id,
            target_kind="file",
            extra={"name": filename, "size": size, "mime_type": mime},
        )

        return FileUploadResponse(
            id=file_row.id,
            name=file_row.name,
            size=file_row.size,
            mime_type=file_row.mime_type or mime,
        )

    # ==================== Soft delete / restore / purge ====================

    async def delete_file(self, file_id: UUID, user_id: UUID) -> None:
        file = await self.get_file(file_id, user_id)
        new_key = minio_client.trash_object_key(
            user_id, minio_client.extract_extension(file.minio_object_id)
        )
        minio_client.move(
            settings.minio_bucket,
            file.minio_object_id,
            new_key,
            file.mime_type or "application/octet-stream",
        )
        file.minio_object_id = new_key
        file.deleted_at = func.now()
        await self.db.flush()
        await audit_service.record_event(
            self.db,
            actor_id=user_id,
            event="file.soft_delete",
            target_id=file_id,
            target_kind="file",
            extra={"name": file.name},
        )

    async def restore_file(self, file_id: UUID, user_id: UUID) -> None:
        # Trashed rows aren't returned by ``get_active`` — use the
        # trashed-state lookup.
        file = await FileRepository.get_trashed(self.db, file_id, user_id)
        if file is None:
            raise FileNotFound("File not found in trash")
        if file.folder_id is not None:
            folder = await FolderRepository.get_active(self.db, file.folder_id, user_id)
            if folder is None:
                raise ConflictError(
                    "Cannot restore file: original parent folder is missing or still trashed"
                )
        existing_names = await FileRepository.list_existing_names_in_folder(
            self.db, user_id, file.folder_id
        )
        if file.name in existing_names:
            raise ConflictError(
                f"Cannot restore file '{file.name}': name conflict in target folder"
            )
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
                "restore.file.minio_move_failed",
                file_id=str(file_id),
                user_id=str(user_id),
                error=str(exc),
            )
        file.deleted_at = None
        await self.db.flush()
        await audit_service.record_event(
            self.db,
            actor_id=user_id,
            event="file.restore",
            target_id=file_id,
            target_kind="file",
        )

    async def permanent_delete_file(self, file_id: UUID, user_id: UUID) -> None:
        # Even for permanent delete we look up the file in any state. If
        # it's currently in trash, the MinIO key already points at the
        # trash prefix and the remove still works.
        file = await FileRepository.get_any_state(self.db, file_id, user_id)
        if file is None:
            raise FileNotFound("File not found")
        file_name = file.name
        # DB delete first, then MinIO remove — if MinIO fails the row
        # is already gone and TTL cleanup won't re-process it, but a
        # missing object is safer than a phantom DB reference.
        await FileRepository.delete(self.db, file)
        try:
            minio_client.remove(settings.minio_bucket, file.minio_object_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "permanent_delete.minio_failed",
                file_id=str(file_id),
                key=file.minio_object_id,
                error=str(exc),
            )
        await audit_service.record_event(
            self.db,
            actor_id=user_id,
            event="file.permanent_delete",
            target_id=file_id,
            target_kind="file",
            extra={"name": file_name},
        )

    # ==================== Move / rename ====================

    async def move_file(
        self, file_id: UUID, user_id: UUID, folder_id: UUID | None
    ) -> None:
        file = await self.get_file(file_id, user_id)
        if folder_id is not None:
            await self._assert_folder_owned(folder_id, user_id)
        # Check for name conflict in the target folder.
        existing_names = await FileRepository.list_existing_names_in_folder(
            self.db, user_id, folder_id
        )
        existing_names |= await FolderRepository.list_existing_names_in_parent(
            self.db, user_id, folder_id
        )
        if file.name in existing_names:
            raise FileNameConflict(
                f"An item named '{file.name}' already exists in the target folder",
                suggested_name=suggest_rename(file.name),
                extra={"name": file.name},
            )
        file.folder_id = folder_id
        await self.db.flush()
        await audit_service.record_event(
            self.db,
            actor_id=user_id,
            event="file.move",
            target_id=file_id,
            target_kind="file",
            extra={"folder_id": str(folder_id) if folder_id else None},
        )

    async def rename_file(self, file_id: UUID, user_id: UUID, name: str) -> None:
        file = await self.get_file(file_id, user_id)
        new_name = sanitize_filename(name)
        validate_extension(new_name)
        # Check for name conflict in the same folder.
        existing_names = await FileRepository.list_existing_names_in_folder(
            self.db, user_id, file.folder_id
        )
        existing_names |= await FolderRepository.list_existing_names_in_parent(
            self.db, user_id, file.folder_id
        )
        if new_name in existing_names and new_name != file.name:
            raise FileNameConflict(
                f"A file named '{new_name}' already exists in this folder",
                suggested_name=suggest_rename(new_name),
                extra={"name": new_name},
            )
        file.name = new_name
        await self.db.flush()
        await audit_service.record_event(
            self.db,
            actor_id=user_id,
            event="file.rename",
            target_id=file_id,
            target_kind="file",
            extra={"new_name": new_name},
        )

    # ==================== Quota ====================

    async def get_quota(self, user_id: UUID) -> tuple[int, int]:
        used = await quota_service.get_usage(self.db, user_id)
        total = await quota_service.get_storage_quota(user_id)
        return used, total

    # ==================== Presigned URLs (short-lived) ====================

    async def get_presigned_url(self, file_id: UUID, user_id: UUID) -> str:
        file = await self.get_file(file_id, user_id)
        return minio_client.presigned_get_url(
            settings.minio_bucket, file.minio_object_id
        )

    # ==================== Streamed download ====================

    async def stream_file(self, file_id: UUID, user_id: UUID):
        """Yield chunks of the file body for ``StreamingResponse``."""
        file = await self.get_file(file_id, user_id)
        return minio_client.get_stream(
            settings.minio_bucket,
            file.minio_object_id,
            chunk_size=settings.stream_chunk_size,
        ), file

    async def get_text_preview(self, file_id: UUID, user_id: UUID) -> tuple[str, bool]:
        """Return UTF-8 text preview for small text-like files."""
        file = await self.get_file(file_id, user_id)
        payload = minio_client.get_bytes(
            settings.minio_bucket,
            file.minio_object_id,
            max_bytes=_TEXT_PREVIEW_MAX_BYTES + 1,
        )
        truncated = len(payload) > _TEXT_PREVIEW_MAX_BYTES
        if truncated:
            payload = payload[:_TEXT_PREVIEW_MAX_BYTES]
        return payload.decode("utf-8", errors="replace"), truncated

    # ==================== Helpers ====================

    async def _assert_folder_owned(self, folder_id: UUID, user_id: UUID) -> None:
        """Verify the folder exists, belongs to the user, and is not in trash."""
        folder = await FolderRepository.get_active(self.db, folder_id, user_id)
        if folder is None:
            raise FolderNotFound("Target folder not found")

    # ==================== Bulk operations (Phase 4.6) ====================

    async def bulk_delete(
        self,
        ids: list[UUID],
        user_id: UUID,
    ) -> tuple[int, dict[str, str]]:
        """
        Soft-delete every file in ``ids`` that belongs to ``user_id``.

        Each id is processed in isolation: a failure on one row does
        not abort the rest.  Returns ``(succeeded, errors)`` where
        ``errors`` is a ``{id: reason}`` map.  The whole call runs in
        the caller-supplied transaction; outer ``get_db`` commits at
        the end.
        """
        from src.exceptions import FileNotFound

        errors: dict[str, str] = {}
        succeeded = 0
        for fid in ids:
            try:
                # Re-raise FileNotFound as a per-id error so the
                # remaining ids still get processed.
                file = await FileRepository.get_active(self.db, fid, user_id)
                if file is None:
                    raise FileNotFound("not found or not owned")
                await self.delete_file(fid, user_id)
                succeeded += 1
            except Exception as exc:  # noqa: BLE001 — bulk reports per-id
                errors[str(fid)] = type(exc).__name__ + ": " + str(exc)
        return succeeded, errors

    async def bulk_move(
        self,
        ids: list[UUID],
        user_id: UUID,
        target_folder_id: UUID | None,
    ) -> tuple[int, dict[str, str]]:
        """Move every file in ``ids`` to ``target_folder_id``.

        Same per-id isolation as :meth:`bulk_delete`.  Each row's
        quota/ownership/folder-existence check runs independently so
        one bad id does not poison the batch.
        """
        errors: dict[str, str] = {}
        succeeded = 0
        for fid in ids:
            try:
                await self.move_file(fid, user_id, target_folder_id)
                succeeded += 1
            except Exception as exc:  # noqa: BLE001
                errors[str(fid)] = type(exc).__name__ + ": " + str(exc)
        return succeeded, errors
