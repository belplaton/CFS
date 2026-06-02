"""
Folder repository — all SQL for the ``folders`` table.

Same contract as :mod:`src.repositories.file`: stateless methods that
take an ``AsyncSession`` and return ORM models (or ``None``).
"""
from __future__ import annotations

from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.folder import Folder


class FolderRepository:
    @staticmethod
    async def get_active(
        db: AsyncSession, folder_id: UUID, user_id: UUID
    ) -> Optional[Folder]:
        result = await db.execute(
            select(Folder).where(
                Folder.id == folder_id,
                Folder.user_id == user_id,
                Folder.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_in_folder(
        db: AsyncSession,
        user_id: UUID,
        parent_id: Optional[UUID],
        *,
        limit: int = 200,
        offset: int = 0,
    ) -> Sequence[Folder]:
        result = await db.execute(
            select(Folder)
            .where(
                Folder.user_id == user_id,
                Folder.parent_id == parent_id,
                Folder.deleted_at.is_(None),
            )
            .order_by(Folder.name)
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    @staticmethod
    async def list_trashed(
        db: AsyncSession, user_id: UUID
    ) -> Sequence[Folder]:
        result = await db.execute(
            select(Folder)
            .where(
                Folder.user_id == user_id,
                Folder.deleted_at.isnot(None),
            )
            .order_by(Folder.deleted_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def search_by_name(
        db: AsyncSession, user_id: UUID, pattern: str, limit: int = 50
    ) -> Sequence[Folder]:
        result = await db.execute(
            select(Folder)
            .where(
                Folder.user_id == user_id,
                Folder.deleted_at.is_(None),
                Folder.name.ilike(pattern),
            )
            .order_by(Folder.name)
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def get_parent_id(
        db: AsyncSession, folder_id: UUID, user_id: UUID
    ) -> Optional[UUID]:
        """Return just the ``parent_id`` column — used by the cycle
        detector in :class:`src.services.folder_service.FolderService`."""
        result = await db.execute(
            select(Folder.parent_id).where(
                Folder.id == folder_id,
                Folder.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def add(db: AsyncSession, folder: Folder) -> None:
        db.add(folder)
        await db.flush()
        await db.refresh(folder)

    @staticmethod
    async def delete(db: AsyncSession, folder: Folder) -> None:
        await db.delete(folder)
        await db.flush()
