"""
Pydantic schemas for the trash resource.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TrashItemResponse(BaseModel):
    """A soft-deleted file or folder as returned by GET /api/trash."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    kind: str  # "file" or "folder"
    size: int = 0
    mime_type: Optional[str] = None
    original_parent_id: Optional[UUID] = None
    deleted_at: datetime
