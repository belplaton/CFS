"""
Bulk operation schemas (Phase 4.6).

The endpoints accept up to ``MAX_BULK_ITEMS`` ids per request — beyond
that the client must chunk.  This keeps the outer transaction bounded
and prevents a single request from monopolising the worker.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


MAX_BULK_ITEMS = 200


class BulkDeleteRequest(BaseModel):
    """Body of ``POST /api/files/bulk-delete``."""

    ids: List[UUID] = Field(..., min_length=1, max_length=MAX_BULK_ITEMS)


class BulkMoveRequest(BaseModel):
    """Body of ``POST /api/files/bulk-move``."""

    ids: List[UUID] = Field(..., min_length=1, max_length=MAX_BULK_ITEMS)
    folder_id: Optional[UUID] = Field(
        None,
        description="Target folder.  ``null`` moves to the user root.",
    )


class BulkOperationResult(BaseModel):
    """
    Result envelope for a bulk operation.

    ``failed`` carries per-id error reasons so the client can show
    them next to the offending row in the UI without re-fetching.
    """

    succeeded: int
    failed: int
    errors: dict[str, str] = Field(
        default_factory=dict,
        description="Map of ``id`` (UUID-строка) → error reason",
    )
