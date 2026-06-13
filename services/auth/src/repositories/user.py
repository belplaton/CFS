"""
User repository — all SQL for the ``users`` table.

The service layer is supposed to know nothing about ``select`` or
column defaults.  When a new query is needed, add it here and have the
service call the repository.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User


class UserRepository:
    """Stateless — every method takes a session so the repository can
    participate in the caller's transaction."""

    @staticmethod
    async def get_by_id(
        db: AsyncSession, user_id: UUID
    ) -> Optional[User]:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(
        db: AsyncSession, email: str
    ) -> Optional[User]:
        """Case-insensitive email lookup — caller must pass a
        already-normalized (lowered, stripped) email so the index
        can be used."""
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def add(db: AsyncSession, user: User) -> None:
        """Add a new ``User`` to the session and flush so the PK is
        populated by the database default."""
        db.add(user)
        await db.flush()
        await db.refresh(user)

    @staticmethod
    async def delete(db: AsyncSession, user: User) -> None:
        await db.delete(user)
        await db.flush()
