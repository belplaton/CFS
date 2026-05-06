"""
User service for Auth Service
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import secrets

from src.models.user import User
from src.schemas import UserCreate, UserResponse
from src.utils.security import get_password_hash, verify_password, create_access_token, create_refresh_token


class UserService:
    """Service for user operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str) -> User | None:
        """Get user by email (case-insensitive)"""
        normalized_email = email.lower().strip()
        result = await self.db.execute(select(User).where(User.email == normalized_email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> User | None:
        """Get user by ID"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        # Normalize email
        normalized_email = user_data.email.lower().strip()

        # Check if user already exists
        existing_user = await self.get_user_by_email(normalized_email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create new user
        db_user = User(
            email=normalized_email,  # Store normalized email
            password_hash=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            is_active=True,
            is_verified=True,  # Email verification disabled for now
        )

        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user

    async def authenticate_user(self, email: str, password: str) -> User | None:
        """Authenticate user with email and password"""
        # Normalize email for lookup
        normalized_email = email.lower().strip()
        user = await self.get_user_by_email(normalized_email)
        if not user:
            return None
        # type: ignore - SQLAlchemy Column vs str
        if not verify_password(password, user.password_hash):  # type: ignore[arg-type]
            return None
        return user

    async def create_tokens_for_user(self, user: User) -> dict:
        """Create access and refresh tokens for user"""
        token_data = {"sub": str(user.id), "email": user.email}

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        # Update last login
        user.last_login = datetime.utcnow()  # type: ignore[assignment]
        await self.db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    async def verify_user_email(self, user: User) -> None:
        """Mark user as verified"""
        user.is_verified = True  # type: ignore[assignment]
        await self.db.commit()
