"""
User model for Auth Service
"""
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.models import Base


class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    # Profile
    full_name = Column(String(255), nullable=True)
    avatar_url = Column(String(512), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)

    # Storage quota (in bytes)
    storage_quota = Column(BigInteger, default=5 * 1024 * 1024 * 1024)  # 5 GB
    used_storage = Column(BigInteger, default=0)

    # 2FA
    totp_secret = Column(String(255), nullable=True)
    is_2fa_enabled = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    verification_tokens = relationship("VerificationToken", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
