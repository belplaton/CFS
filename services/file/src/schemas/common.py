"""
Common Pydantic schemas shared across endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel


class ItemResponse(BaseModel):
    """A unified file/folder item used by listing and search endpoints."""

    id: UUID
    kind: str  # "file" or "folder"
    name: str
    size: int = 0
    mime_type: Optional[str] = None
    parent_id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class QuotaResponse(BaseModel):
    """Storage usage summary returned by GET /api/files/quota."""

    used: int
    total: int
    percent: float = 0.0


class DirectoryListingResponse(BaseModel):
    """Directory listing with independent cursors for folders and files."""

    folders: List[ItemResponse]
    files: List[ItemResponse]
    next_folders_cursor: Optional[str] = None
    next_files_cursor: Optional[str] = None


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """
    Cursor-paginated response (Phase 4.5).

    ``next_cursor`` is ``None`` when there are no more results.
    Clients keep calling with that cursor until they get ``None`` back.
    """

    items: List[T]
    next_cursor: Optional[str] = None
