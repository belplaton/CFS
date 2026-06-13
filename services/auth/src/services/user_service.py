"""
User service for Auth Service (Phase 3: SQLAlchemy 2.0, UUID PKs).

The service is intentionally thin — repositories (Phase 3.11) own the
SQL; here we encode the user-management business rules (uniqueness,
password hashing, token issuance, last-login bookkeeping).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import secrets
from uuid import UUID

import httpx

from src.config import settings
from src.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
    ValidationError,
)
from src.models.token import VerificationToken
from src.models.user import User
from src.repositories.user import UserRepository
from src.repositories.verification_token import VerificationTokenRepository
from src.schemas import UserCreate
from src.utils.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)


class UserService:
    """Service for user operations."""

    EMAIL_VERIFICATION_TOKEN_TYPE = "email_verification"
    PASSWORD_RESET_TOKEN_TYPE = "password_reset"

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

        Raises ``UserAlreadyExistsError`` (409) if the email is already
        registered.
        """
        normalized_email = user_data.email.lower().strip()

        existing = await self.get_user_by_email(normalized_email)
        if existing is not None:
            raise UserAlreadyExistsError("Email already registered")

        user = User(
            email=normalized_email,
            password_hash=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            is_active=True,
            is_verified=False,
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

    async def update_user_plan(self, user: User, plan: str) -> User:
        normalized_plan = plan.lower().strip()
        plan_quotas = {
            "free": settings.default_storage_quota,
            "pro": settings.premium_storage_quota,
            "team": settings.team_storage_quota,
        }

        if normalized_plan not in plan_quotas:
            raise ValidationError("Unsupported plan")

        new_quota = plan_quotas[normalized_plan]
        if user.used_storage > new_quota:
            raise ValidationError("Current usage exceeds selected plan quota")

        user.storage_quota = new_quota
        await self.db.flush()
        await self._invalidate_file_service_quota_cache(user.id)
        return user

    async def _invalidate_file_service_quota_cache(self, user_id: UUID) -> None:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                await client.delete(
                    f"{settings.file_service_url.rstrip('/')}/api/internal/quota-cache/{user_id}",
                    headers={"X-API-Key": settings.service_api_key},
                )
        except Exception:
            # Plan switch should still succeed even if file-service cache
            # invalidation misses; frontend updates local quota immediately.
            return

    async def create_verification_token(
        self,
        user: User,
        *,
        token_type: str,
        expires_in_hours: int,
    ) -> VerificationToken:
        await VerificationTokenRepository.invalidate_for_user(
            self.db,
            user.id,
            token_type=token_type,
        )

        token = VerificationToken(
            user_id=user.id,
            token=secrets.token_urlsafe(32),
            token_type=token_type,
            expires_at=datetime.now(timezone.utc).replace(microsecond=0) + timedelta(hours=expires_in_hours),
        )
        await VerificationTokenRepository.add(self.db, token)
        return token

    def build_action_url(self, path: str, *, token: str, email: str) -> str:
        return f"{settings.frontend_url}{path}?token={token}&email={email}"

    async def request_email_verification(self, user: User) -> tuple[str, str]:
        token = await self.create_verification_token(
            user,
            token_type=self.EMAIL_VERIFICATION_TOKEN_TYPE,
            expires_in_hours=24,
        )
        action_url = self.build_action_url(
            "/verify-email",
            token=token.token,
            email=user.email,
        )
        return token.token, action_url

    async def consume_email_verification_token(self, token_value: str) -> User:
        token = await VerificationTokenRepository.get_active_by_token(
            self.db,
            token_value,
            token_type=self.EMAIL_VERIFICATION_TOKEN_TYPE,
            now=datetime.now(timezone.utc),
        )
        if token is None:
            raise AuthenticationError("Invalid or expired verification token")

        user = await self.get_user_by_id(token.user_id)
        if user is None:
            raise UserNotFoundError("User not found")

        await self.verify_user_email(user)
        await VerificationTokenRepository.mark_used(self.db, token)
        return user

    async def request_password_reset(self, email: str) -> tuple[str | None, str | None]:
        user = await self.get_user_by_email(email.lower().strip())
        if user is None:
            return None, None

        token = await self.create_verification_token(
            user,
            token_type=self.PASSWORD_RESET_TOKEN_TYPE,
            expires_in_hours=1,
        )
        action_url = self.build_action_url(
            "/reset-password",
            token=token.token,
            email=user.email,
        )
        return token.token, action_url

    async def reset_password_with_token(self, token_value: str, new_password: str) -> User:
        token = await VerificationTokenRepository.get_active_by_token(
            self.db,
            token_value,
            token_type=self.PASSWORD_RESET_TOKEN_TYPE,
            now=datetime.now(timezone.utc),
        )
        if token is None:
            raise AuthenticationError("Invalid or expired reset token")

        user = await self.get_user_by_id(token.user_id)
        if user is None:
            raise UserNotFoundError("User not found")

        user.password_hash = get_password_hash(new_password)
        await VerificationTokenRepository.mark_used(self.db, token)
        await VerificationTokenRepository.invalidate_for_user(
            self.db,
            user.id,
            token_type=self.PASSWORD_RESET_TOKEN_TYPE,
        )
        await self.db.flush()
        return user
