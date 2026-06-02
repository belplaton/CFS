"""
Pydantic schemas for the folder resource.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FolderCreate(BaseModel):
    """Body of POST /api/folders."""

    name: str = Field(..., min_length=1, max_length=255)
    parent_id: Optional[UUID] = None


class FolderUpdate(BaseModel):
    """Body of PATCH /api/folders/{folder_id}."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    parent_id: Optional[UUID] = None


class FolderResponse(BaseModel):
    """Folder metadata returned by the folder endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    parent_id: Optional[UUID] = None
    path: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
