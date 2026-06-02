"""
Pydantic schemas for the file resource.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FileResponse(BaseModel):
    """File metadata returned by GET /api/files/{file_id}."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    size: int
    mime_type: Optional[str] = None
    folder_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


class FileUploadResponse(BaseModel):
    """Confirmation body returned by POST /api/files/upload."""

    id: UUID
    name: str
    size: int
    mime_type: str


class FileMoveRequest(BaseModel):
    """Body of POST /api/files/{file_id}/move."""

    folder_id: Optional[UUID] = None


class FileRenameRequest(BaseModel):
    """Body of PATCH /api/files/{file_id}/rename."""

    name: str = Field(..., min_length=1, max_length=255)
