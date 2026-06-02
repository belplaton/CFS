"""
File repository — all SQL for the ``files`` table.

The service layer is supposed to know nothing about ``select``,
``func``, or ``deleted_at IS NULL``.  When a new query is needed,
add it here and have the service call the repository.  This keeps the
business logic readable and makes it trivial to swap the storage
backend (Postgres → something else) without touching service code.
"""
from __future__ import annotations

from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.file import File


class FileRepository:
    """Stateless — every method takes a session so the repository can
    participate in the caller's transaction."""

    @staticmethod
    async def get_active(
        db: AsyncSession, file_id: UUID, user_id: UUID
    ) -> Optional[File]:
        """Return the file if it exists, belongs to the user, and is
        not soft-deleted.  ``None`` otherwise."""
        result = await db.execute(
            select(File).where(
                File.id == file_id,
                File.user_id == user_id,
                File.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_any_state(
        db: AsyncSession, file_id: UUID, user_id: UUID
    ) -> Optional[File]:
        """Return the file regardless of soft-delete state.  Used for
        ``/permanent`` deletes where the file may already be in trash."""
        result = await db.execute(
            select(File).where(
                File.id == file_id,
                File.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_trashed(
        db: AsyncSession, file_id: UUID, user_id: UUID
    ) -> Optional[File]:
        """Return a soft-deleted file (only matches rows where
        ``deleted_at IS NOT NULL``)."""
        result = await db.execute(
            select(File).where(
                File.id == file_id,
                File.user_id == user_id,
                File.deleted_at.isnot(None),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_in_folder(
        db: AsyncSession,
        user_id: UUID,
        folder_id: Optional[UUID],
        *,
        limit: int = 200,
        offset: int = 0,
    ) -> Sequence[File]:
        """List active files in ``folder_id`` for ``user_id``."""
        result = await db.execute(
            select(File)
            .where(
                File.user_id == user_id,
                File.folder_id == folder_id,
                File.deleted_at.is_(None),
            )
            .order_by(File.name)
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    @staticmethod
    async def list_trashed(
        db: AsyncSession, user_id: UUID
    ) -> Sequence[File]:
        """List soft-deleted files for ``user_id`` (newest first)."""
        result = await db.execute(
            select(File)
            .where(
                File.user_id == user_id,
                File.deleted_at.isnot(None),
            )
            .order_by(File.deleted_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def search_by_name(
        db: AsyncSession, user_id: UUID, pattern: str, limit: int = 50
    ) -> Sequence[File]:
        """Case-insensitive substring search over ``name``."""
        result = await db.execute(
            select(File)
            .where(
                File.user_id == user_id,
                File.deleted_at.is_(None),
                File.name.ilike(pattern),
            )
            .order_by(File.name)
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def add(db: AsyncSession, file: File) -> None:
        """Add a new ``File`` to the session and flush so the PK is
        populated by the database default."""
        db.add(file)
        await db.flush()
        await db.refresh(file)

    @staticmethod
    async def delete(db: AsyncSession, file: File) -> None:
        await db.delete(file)
        await db.flush()
