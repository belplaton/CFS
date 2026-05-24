"""
File Service API router
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, UploadFile
from fastapi import File as FastAPIFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models import File, Folder, get_db
from src.utils.minio_client import get_minio_client

router = APIRouter(prefix="/files", tags=["files"])


# Simple service-to-service authentication via X-API-Key header
async def verify_service_key(x_api_key: Optional[str] = Header(None)):
    if x_api_key != settings.service_api_key:
        raise HTTPException(status_code=403, detail="Invalid service API key")
    return True


# Helper to fetch folder, ensure it belongs to user (user_id placeholder for now)
async def get_folder(
    session: AsyncSession, folder_id: Optional[UUID]
) -> Optional[Folder]:
    if folder_id is None:
        return None
    result = await session.get(Folder, folder_id)
    return result


@router.get("/", response_model=List[dict])
async def list_items(
    folder_id: Optional[UUID] = Query(None, description="Folder to list contents of"),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_service_key),
):
    """List files and sub‑folders inside a folder (or root)."""
    query = db.query(File).filter(
        File.folder_id == folder_id, File.deleted_at.is_(None)
    )
    files = await query.all()
    folder_query = db.query(Folder).filter(
        Folder.parent_id == folder_id, Folder.deleted_at.is_(None)
    )
    folders = await folder_query.all()
    # Simplified response – real implementation would use pydantic models
    result = []
    for f in folders:
        result.append(
            {
                "id": str(f.id),
                "kind": "folder",
                "name": f.name,
                "parent_id": str(f.parent_id) if f.parent_id else None,
            }
        )
    for f in files:
        result.append(
            {
                "id": str(f.id),
                "kind": "file",
                "name": f.name,
                "size": f.size,
                "mime_type": f.mime_type,
                "parent_id": str(f.folder_id) if f.folder_id else None,
            }
        )
    return result


@router.post("/folders", response_model=dict)
async def create_folder(
    name: str = Query(..., description="Folder name"),
    parent_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_service_key),
):
    """Create a new folder for a user (user_id is placeholder)."""
    # In a real system we would extract user_id from JWT; here we use a dummy UUID
    dummy_user_id = UUID("00000000-0000-0000-0000-000000000001")
    folder = Folder(name=name, parent_id=parent_id, user_id=dummy_user_id)
    db.add(folder)
    await db.flush()
    await db.refresh(folder)
    return {
        "id": str(folder.id),
        "name": folder.name,
        "parent_id": str(folder.parent_id) if folder.parent_id else None,
    }


@router.post("/upload", response_model=dict)
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    folder_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_service_key),
):
    """Upload a file to MinIO and store metadata in DB."""
    dummy_user_id = UUID("00000000-0000-0000-0000-000000000001")
    minio_client = get_minio_client()
    # Generate a unique object name
    object_name = f"{dummy_user_id}/{folder_id or 'root'}/{file.filename}"
    # Upload stream directly
    await minio_client.put_object(
        bucket_name=settings.minio_bucket,
        object_name=object_name,
        data=file.file,
        length=-1,  # unknown size – streaming
        content_type=file.content_type,
    )
    # Store metadata
    new_file = File(
        user_id=dummy_user_id,
        folder_id=folder_id,
        name=file.filename,
        size=file.headers.get("content-length") or 0,
        mime_type=file.content_type,
        minio_object_id=object_name,
    )
    db.add(new_file)
    await db.flush()
    await db.refresh(new_file)
    return {"id": str(new_file.id), "name": new_file.name}


@router.get("/{file_id}/url", response_model=dict)
async def get_file_url(
    file_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_service_key),
):
    """Return a presigned URL for downloading a file."""
    file_obj = await db.get(File, file_id)
    if not file_obj or file_obj.deleted_at:
        raise HTTPException(status_code=404, detail="File not found")
    minio_client = get_minio_client()
    url = minio_client.presigned_get_object(
        settings.minio_bucket, file_obj.minio_object_id
    )
    return {"url": url}


@router.delete("/{file_id}")
async def move_to_trash(
    file_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_service_key),
):
    """Soft‑delete (move to trash)."""
    file_obj = await db.get(File, file_id)
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")
    file_obj.deleted_at = func.now()
    await db.flush()
    return {"status": "moved to trash"}


@router.post("/{file_id}/restore")
async def restore_file(
    file_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_service_key),
):
    """Restore a soft‑deleted file."""
    file_obj = await db.get(File, file_id)
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")
    file_obj.deleted_at = None
    await db.flush()
    return {"status": "restored"}


@router.delete("/{file_id}/permanent")
async def delete_permanent(
    file_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_service_key),
):
    """Permanently delete a file (remove from MinIO and DB)."""
    file_obj = await db.get(File, file_id)
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")
    minio_client = get_minio_client()
    await minio_client.remove_object(settings.minio_bucket, file_obj.minio_object_id)
    await db.delete(file_obj)
    await db.flush()
    return {"status": "deleted permanently"}


@router.get("/quota", response_model=dict)
async def get_quota(
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_service_key),
):
    """Return used / total quota for the dummy user (replace with real user logic)."""
    dummy_user_id = UUID("00000000-0000-0000-0000-000000000001")
    result = await db.execute(
        "SELECT COALESCE(SUM(size),0) FROM files WHERE user_id = :uid AND deleted_at IS NULL",
        {"uid": dummy_user_id},
    )
    used = result.scalar() or 0
    total = settings.default_storage_quota
    return {"used": used, "total": total}
