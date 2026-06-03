"""
Folder repository — all SQL for the ``folders`` table.

Same contract as :mod:`src.repositories.file`: stateless methods that
take an ``AsyncSession`` and return ORM models (or ``None``).
"""
from __future__ import annotations

from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.folder import Folder
from src.utils.cursor import Cursor


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
    async def get_trashed(
        db: AsyncSession, folder_id: UUID, user_id: UUID
    ) -> Optional[Folder]:
        result = await db.execute(
            select(Folder).where(
                Folder.id == folder_id,
                Folder.user_id == user_id,
                Folder.deleted_at.isnot(None),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_any_state(
        db: AsyncSession, folder_id: UUID, user_id: UUID
    ) -> Optional[Folder]:
        result = await db.execute(
            select(Folder).where(
                Folder.id == folder_id,
                Folder.user_id == user_id,
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
            .order_by(Folder.name, Folder.id)
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    @staticmethod
    async def list_in_folder_after(
        db: AsyncSession,
        user_id: UUID,
        parent_id: Optional[UUID],
        cursor: Cursor,
        *,
        limit: int = 200,
    ) -> Sequence[Folder]:
        """Cursor-paginated variant of :meth:`list_in_folder`."""
        result = await db.execute(
            select(Folder)
            .where(
                Folder.user_id == user_id,
                Folder.parent_id == parent_id,
                Folder.deleted_at.is_(None),
                tuple_(Folder.name, Folder.id) > tuple_(cursor.name, cursor.id),
            )
            .order_by(Folder.name, Folder.id)
            .limit(limit)
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
    async def list_child_ids(
        db: AsyncSession,
        parent_ids: list[UUID],
        user_id: UUID,
    ) -> list[UUID]:
        """
        Return the IDs of every active folder whose ``parent_id`` is
        in ``parent_ids``.  Used by the recursive trash cascade to
        walk a folder subtree one level at a time.
        """
        if not parent_ids:
            return []
        result = await db.execute(
            select(Folder.id).where(
                Folder.user_id == user_id,
                Folder.parent_id.in_(parent_ids),
                Folder.deleted_at.is_(None),
            )
        )
        return [row[0] for row in result.all()]

    @staticmethod
    async def list_child_ids_any_state(
        db: AsyncSession,
        parent_ids: list[UUID],
        user_id: UUID,
    ) -> list[UUID]:
        if not parent_ids:
            return []
        result = await db.execute(
            select(Folder.id).where(
                Folder.user_id == user_id,
                Folder.parent_id.in_(parent_ids),
            )
        )
        return [row[0] for row in result.all()]

    @staticmethod
    async def list_active_files_in_folders(
        db: AsyncSession,
        folder_ids: list[UUID],
        user_id: UUID,
    ) -> Sequence:
        """
        Return every active file whose ``folder_id`` is in ``folder_ids``.

        The return type is intentionally loose (``Sequence``) — the
        concrete row class lives in :mod:`src.models.file` and we do
        not want a static import here to avoid a circular dependency
        on the file service layer.
        """
        from src.models.file import File

        if not folder_ids:
            return []
        result = await db.execute(
            select(File).where(
                File.user_id == user_id,
                File.folder_id.in_(folder_ids),
                File.deleted_at.is_(None),
            )
        )
        return result.scalars().all()

    @staticmethod
    async def list_files_in_folders(
        db: AsyncSession,
        folder_ids: list[UUID],
        user_id: UUID,
    ) -> Sequence:
        from src.models.file import File

        if not folder_ids:
            return []
        result = await db.execute(
            select(File).where(
                File.user_id == user_id,
                File.folder_id.in_(folder_ids),
            )
        )
        return result.scalars().all()

    @staticmethod
    async def list_trashed_before(
        db: AsyncSession,
        cutoff,
        *,
        limit: int = 500,
    ) -> Sequence:
        """
        Return up to ``limit`` soft-deleted folders whose ``deleted_at``
        is older than ``cutoff`` (Phase 4.2 TTL cleanup).
        """
        result = await db.execute(
            select(Folder)
            .where(
                Folder.deleted_at.isnot(None),
                Folder.deleted_at < cutoff,
            )
            .order_by(Folder.id)
            .limit(limit)
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
    async def list_existing_names_in_parent(
        db: AsyncSession,
        user_id: UUID,
        parent_id: Optional[UUID],
    ) -> set[str]:
        result = await db.execute(
            select(Folder.name).where(
                Folder.user_id == user_id,
                Folder.parent_id == parent_id,
                Folder.deleted_at.is_(None),
            )
        )
        return {row[0] for row in result.all()}

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
