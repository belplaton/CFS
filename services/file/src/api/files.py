"""
File API endpoints (Phase 1: streaming upload + proxied download).
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.exceptions import PayloadTooLarge
from src.models import get_db
from src.schemas import (
    FileMoveRequest,
    FileRenameRequest,
    FileResponse,
    FileUploadResponse,
    ItemResponse,
    QuotaResponse,
)
from src.services.file_service import FileService
from src.services.folder_service import FolderService
from src.utils.dependencies import get_current_user_id
from src.utils.rate_limiter import POLICY_DELETE, POLICY_UPLOAD, rate_limit
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

@router.get("/", response_model=list[ItemResponse])
async def list_files(
    folder_id: Optional[UUID] = None,
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    file_svc = FileService(db)
    folder_svc = FolderService(db)

    folders = await folder_svc.list_folders(user_id, folder_id, limit=limit, offset=offset)
    files = await file_svc.list_files(user_id, folder_id, limit=limit, offset=offset)

    items: list[ItemResponse] = []
    for f in folders:
        items.append(ItemResponse(
            id=f.id, kind="folder", name=f.name,
            parent_id=f.parent_id, created_at=f.created_at, updated_at=f.updated_at,
        ))
    for f in files:
        items.append(ItemResponse(
            id=f.id, kind="file", name=f.name, size=f.size,
            mime_type=f.mime_type, parent_id=f.folder_id,
            created_at=f.created_at, updated_at=f.updated_at,
        ))
    return items


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
    )


# ==================== Single file ====================

@router.get("/quota", response_model=QuotaResponse)
async def get_quota(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    used, total = await FileService(db).get_quota(user_id)
    percent = round((used / max(total, 1)) * 100, 1)
    return QuotaResponse(used=used, total=total, percent=percent)


@router.get("/{file_id}", response_model=FileResponse)
async def get_file_meta(
    file_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await FileService(db).get_file(file_id, user_id)


# ==================== Download (proxied) ====================

@router.get("/{file_id}/download")
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


@router.post("/{file_id}/restore")
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


@router.post("/{file_id}/move")
async def move_file(
    file_id: UUID,
    body: FileMoveRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await FileService(db).move_file(file_id, user_id, body.folder_id)
    return {"status": "moved"}


@router.patch("/{file_id}/rename")
async def rename_file(
    file_id: UUID,
    body: FileRenameRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await FileService(db).rename_file(file_id, user_id, body.name)
    return {"status": "renamed"}
