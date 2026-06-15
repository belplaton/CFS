"""
Search service — case-insensitive ILIKE search across file and folder names.

Phase 1 uses simple ``ILIKE '%query%'`` for portability. Phase 3 will swap
this for the ``pg_trgm`` extension to support typo-tolerant ranking.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.file import FileRepository
from src.repositories.folder import FolderRepository
from src.schemas import ItemResponse


class SearchService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def search(
        self, user_id: UUID, query: str, limit: int = 50
    ) -> list[ItemResponse]:
        pattern = f"%{query}%"

        files = await FileRepository.search_by_name(self.db, user_id, pattern, limit)
        folders = await FolderRepository.search_by_name(
            self.db, user_id, pattern, limit
        )
        folder_sizes = await FolderRepository.get_recursive_sizes(
            self.db,
            user_id,
            [folder.id for folder in folders],
        )

        results: list[ItemResponse] = []
        for f in folders:
            results.append(
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
        for f in files:
            results.append(
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
        return results
