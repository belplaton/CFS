"""
Repository queries for ``verification_tokens``.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.token import VerificationToken


class VerificationTokenRepository:
    @staticmethod
    async def add(db: AsyncSession, token: VerificationToken) -> None:
        db.add(token)
        await db.flush()
        await db.refresh(token)

    @staticmethod
    async def get_active_by_token(
        db: AsyncSession,
        token: str,
        *,
        token_type: str | None = None,
        now: datetime,
    ) -> VerificationToken | None:
        stmt = select(VerificationToken).where(
            VerificationToken.token == token,
            VerificationToken.is_used.is_(False),
            VerificationToken.expires_at > now,
        )
        if token_type is not None:
            stmt = stmt.where(VerificationToken.token_type == token_type)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def invalidate_for_user(
        db: AsyncSession,
        user_id: UUID,
        *,
        token_type: str,
    ) -> None:
        await db.execute(
            delete(VerificationToken).where(
                VerificationToken.user_id == user_id,
                VerificationToken.token_type == token_type,
            )
        )
        await db.flush()

    @staticmethod
    async def mark_used(db: AsyncSession, token: VerificationToken) -> None:
        token.is_used = True
        await db.flush()
