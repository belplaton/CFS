"""
Pydantic schemas for the file service.

Phase 2.11: schemas are now split by resource (one module per
resource).  This module re-exports every public symbol so existing
``from src.schemas import FooBar`` imports keep working — the public
API surface did not change, only the internal layout.
"""
from src.schemas.bulk import (
    MAX_BULK_ITEMS,
    BulkDeleteRequest,
    BulkMoveRequest,
    BulkOperationResult,
)
from src.schemas.common import ItemResponse, Page, QuotaResponse
from src.schemas.file import (
    FileMoveRequest,
    FileRenameRequest,
    FileResponse,
    FileUploadResponse,
)
from src.schemas.folder import FolderCreate, FolderResponse, FolderUpdate
from src.schemas.search import SearchResponse
from src.schemas.trash import TrashItemResponse

__all__ = [
    "MAX_BULK_ITEMS",
    "BulkDeleteRequest",
    "BulkMoveRequest",
    "BulkOperationResult",
    "FileMoveRequest",
    "FileRenameRequest",
    "FileResponse",
    "FileUploadResponse",
    "FolderCreate",
    "FolderResponse",
    "FolderUpdate",
    "ItemResponse",
    "Page",
    "QuotaResponse",
    "SearchResponse",
    "TrashItemResponse",
]
