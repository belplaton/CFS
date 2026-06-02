"""
User service for Auth Service (Phase 3: SQLAlchemy 2.0, UUID PKs).

The service is intentionally thin — repositories (Phase 3.11) own the
SQL; here we encode the user-management business rules (uniqueness,
password hashing, token issuance, last-login bookkeeping).
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status

from src.models.user import User
from src.repositories.user import UserRepository
from src.schemas import UserCreate
from src.utils.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)


class UserService:
    """Service for user operations."""

    def __init__(self, db) -> None:
        self.db = db

    # ==================== Read ====================

    async def get_user_by_email(self, email: str) -> User | None:
        return await UserRepository.get_by_email(self.db, email)

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        return await UserRepository.get_by_id(self.db, user_id)

    # ==================== Create ====================

    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user.

        Raises ``HTTPException(400)`` if the email is already registered.
        """
        normalized_email = user_data.email.lower().strip()

        existing = await self.get_user_by_email(normalized_email)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        user = User(
            email=normalized_email,
            password_hash=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            is_active=True,
            # Email verification is disabled for now — flip to False once
            # the verification flow is wired up.
            is_verified=True,
        )
        await UserRepository.add(self.db, user)
        return user

    # ==================== Authenticate ====================

    async def authenticate_user(self, email: str, password: str) -> User | None:
        """Return the user iff the credentials are valid, else ``None``."""
        user = await self.get_user_by_email(email)
        if user is None:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    # ==================== Tokens ====================

    async def create_tokens_for_user(self, user: User) -> dict:
        """Mint a fresh access / refresh pair for ``user`` and update
        ``last_login`` in the same transaction."""
        token_data = {"sub": str(user.id), "email": user.email}

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        # ``expire_on_commit=False`` on the engine + an explicit
        # assignment means the new value is visible to the caller even
        # before commit (the FastAPI dependency will commit on the way
        # out via ``get_db``).
        user.last_login = datetime.now(timezone.utc)
        await self.db.flush()
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    # ==================== Misc ====================

    async def verify_user_email(self, user: User) -> None:
        user.is_verified = True
        await self.db.flush()
