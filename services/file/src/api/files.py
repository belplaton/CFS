"""
File API endpoints (Phase 1: streaming upload + proxied download).
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.exceptions import PayloadTooLarge
from src.models import get_db
from src.schemas import (
    BulkDeleteRequest,
    BulkMoveRequest,
    BulkOperationResult,
    DirectoryListingResponse,
    FileMoveRequest,
    FileRenameRequest,
    FileResponse,
    TextPreviewResponse,
    FileUploadResponse,
    ItemResponse,
    QuotaResponse,
)
from src.services.file_service import FileService
from src.services.folder_service import FolderService
from src.utils.cursor import Cursor, CursorError
from src.utils.dependencies import get_current_user_id
from src.utils.rate_limiter import (
    POLICY_DEFAULT,
    POLICY_DELETE,
    POLICY_UPLOAD,
    rate_limit,
)
from src.utils.validators import content_disposition_filename


router = APIRouter(prefix="/api/files", tags=["Files"])


# ==================== Helpers ====================


async def _read_upload_with_limit(file: UploadFile, limit: int) -> bytes:
    """
    Read the entire ``UploadFile`` body in chunks, aborting as soon as the
    running total exceeds ``limit``. This is the simple MVP path; for
    multi-hundred-MB objects a true multipart upload to MinIO would be the
    next step.
    """
    chunk_size = settings.stream_chunk_size
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total += len(chunk)
        if total > limit:
            raise PayloadTooLarge(
                f"File exceeds the {limit}-byte upload limit",
                extra={"limit": limit},
            )
        chunks.append(chunk)
    return b"".join(chunks)


# ==================== Listing ====================


@router.get(
    "/",
    response_model=DirectoryListingResponse,
    dependencies=[Depends(rate_limit(POLICY_DEFAULT))],
)
async def list_files(
    folder_id: Optional[UUID] = None,
    limit: int = Query(200, ge=1, le=1000),
    folders_cursor: Optional[str] = Query(
        None,
        description=(
            "Opaque pagination cursor returned in ``next_folders_cursor`` "
            "from a previous response."
        ),
    ),
    files_cursor: Optional[str] = Query(
        None,
        description=(
            "Opaque pagination cursor returned in ``next_files_cursor`` "
            "from a previous response."
        ),
    ),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    List folders and files in a directory with independent cursors.

    ``limit`` applies per collection. The client paginates folders
    and files independently using ``next_folders_cursor`` and
    ``next_files_cursor``.
    """
    try:
        parsed_folders_cursor = Cursor.try_decode(folders_cursor)
        parsed_files_cursor = Cursor.try_decode(files_cursor)
    except CursorError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid cursor: {exc}") from exc

    file_svc = FileService(db)
    folder_svc = FolderService(db)

    folders, f_next = await folder_svc.list_folders_page(
        user_id, folder_id, limit=limit, cursor=parsed_folders_cursor
    )
    files, files_next = await file_svc.list_files_page(
        user_id, folder_id, limit=limit, cursor=parsed_files_cursor
    )
    folder_sizes = await folder_svc.get_recursive_sizes(
        user_id,
        [folder.id for folder in folders],
    )

    folder_items: list[ItemResponse] = []
    for f in folders:
        folder_items.append(
            ItemResponse(
                id=f.id,
                kind="folder",
                name=f.name,
                size=folder_sizes.get(f.id, 0),
                parent_id=f.parent_id,
                created_at=f.created_at,
                updated_at=f.updated_at,
            )
        )
    file_items: list[ItemResponse] = []
    for f in files:
        file_items.append(
            ItemResponse(
                id=f.id,
                kind="file",
                name=f.name,
                size=f.size,
                mime_type=f.mime_type,
                parent_id=f.folder_id,
                created_at=f.created_at,
                updated_at=f.updated_at,
            )
        )

    return DirectoryListingResponse(
        folders=folder_items,
        files=file_items,
        next_folders_cursor=f_next,
        next_files_cursor=files_next,
    )


# ==================== Upload ====================


@router.post(
    "/upload",
    response_model=FileUploadResponse,
    status_code=201,
    dependencies=[Depends(rate_limit(POLICY_UPLOAD))],
)
async def upload_file(
    file: UploadFile,
    folder_id: Optional[UUID] = None,
    on_conflict: str = Query(
        "reject",
        pattern="^(reject|rename)$",
        description=(
            "What to do when a file with the same name already exists in "
            "the target folder. ``reject`` returns 409 with a suggested "
            "name; ``rename`` silently appends ``(1)``, ``(2)``... to "
            "the uploaded filename."
        ),
    ),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    data = await _read_upload_with_limit(file, settings.max_upload_size)
    await file.close()

    file_svc = FileService(db)
    return await file_svc.upload_file(
        user_id=user_id,
        folder_id=folder_id,
        raw_filename=file.filename,
        content_type=file.content_type,
        file_data=data,
        on_conflict=on_conflict,
    )


# ==================== Single file ====================


@router.get(
    "/quota",
    response_model=QuotaResponse,
    dependencies=[Depends(rate_limit(POLICY_DEFAULT))],
)
async def get_quota(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    used, total = await FileService(db).get_quota(user_id)
    percent = round((used / max(total, 1)) * 100, 1)
    return QuotaResponse(used=used, total=total, percent=percent)


@router.get(
    "/{file_id}",
    response_model=FileResponse,
    dependencies=[Depends(rate_limit(POLICY_DEFAULT))],
)
async def get_file_meta(
    file_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await FileService(db).get_file(file_id, user_id)


@router.get(
    "/{file_id}/text-preview",
    response_model=TextPreviewResponse,
    dependencies=[Depends(rate_limit(POLICY_DEFAULT))],
)
async def get_text_preview(
    file_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    content, truncated = await FileService(db).get_text_preview(file_id, user_id)
    return TextPreviewResponse(content=content, truncated=truncated)


# ==================== Download (proxied) ====================


@router.get(
    "/{file_id}/download",
    dependencies=[Depends(rate_limit(POLICY_DEFAULT))],
)
async def download_file(
    file_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    file_svc = FileService(db)
    stream_iter, file = await file_svc.stream_file(file_id, user_id)
    headers = {
        "Content-Disposition": content_disposition_filename(file.name),
        "Content-Length": str(file.size),
        "X-Content-Type-Options": "nosniff",
    }
    return StreamingResponse(
        stream_iter,
        media_type=file.mime_type or "application/octet-stream",
        headers=headers,
    )


# ==================== Bulk operations (Phase 4.6) ====================


@router.post(
    "/bulk-delete",
    response_model=BulkOperationResult,
    dependencies=[Depends(rate_limit(POLICY_DELETE))],
)
async def bulk_delete_files(
    payload: BulkDeleteRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete up to ``MAX_BULK_ITEMS`` files in a single call."""
    file_svc = FileService(db)
    succeeded, errors = await file_svc.bulk_delete(payload.ids, user_id)
    return BulkOperationResult(
        succeeded=succeeded,
        failed=len(errors),
        errors=errors,
    )


@router.post(
    "/bulk-move",
    response_model=BulkOperationResult,
    dependencies=[Depends(rate_limit(POLICY_DEFAULT))],
)
async def bulk_move_files(
    payload: BulkMoveRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Move up to ``MAX_BULK_ITEMS`` files to ``folder_id`` (``null`` = root)."""
    file_svc = FileService(db)
    succeeded, errors = await file_svc.bulk_move(
        payload.ids, user_id, payload.folder_id
    )
    return BulkOperationResult(
        succeeded=succeeded,
        failed=len(errors),
        errors=errors,
    )


# ==================== Mutations ====================


@router.delete(
    "/{file_id}",
    dependencies=[Depends(rate_limit(POLICY_DELETE))],
)
async def delete_file(
    file_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await FileService(db).delete_file(file_id, user_id)
    return {"status": "moved to trash"}


@router.post(
    "/{file_id}/restore",
    dependencies=[Depends(rate_limit(POLICY_DEFAULT))],
)
async def restore_file(
    file_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await FileService(db).restore_file(file_id, user_id)
    return {"status": "restored"}


@router.delete(
    "/{file_id}/permanent",
    dependencies=[Depends(rate_limit(POLICY_DELETE))],
)
async def permanent_delete_file(
    file_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await FileService(db).permanent_delete_file(file_id, user_id)
    return {"status": "deleted permanently"}


@router.post(
    "/{file_id}/move",
    dependencies=[Depends(rate_limit(POLICY_DEFAULT))],
)
async def move_file(
    file_id: UUID,
    body: FileMoveRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await FileService(db).move_file(file_id, user_id, body.folder_id)
    return {"status": "moved"}


@router.patch(
    "/{file_id}/rename",
    dependencies=[Depends(rate_limit(POLICY_DEFAULT))],
)
async def rename_file(
    file_id: UUID,
    body: FileRenameRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await FileService(db).rename_file(file_id, user_id, body.name)
    return {"status": "renamed"}
