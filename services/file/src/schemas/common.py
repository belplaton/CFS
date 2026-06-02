"""
Common Pydantic schemas shared across endpoints.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
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
