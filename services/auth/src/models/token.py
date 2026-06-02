"""
Verification Token model for Auth Service (SQLAlchemy 2.0 style).

Used for email verification and password-reset flows.  The ``token``
column is the only piece of secret material the table holds — keep
its index tight and never log it.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models import Base


class VerificationToken(Base):
    """Verification Token model for email verification and password reset."""

    __tablename__ = "verification_tokens"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Token details
    token: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    token_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Status
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Relationship
    user = relationship("User", back_populates="verification_tokens")

    def __repr__(self) -> str:
        return f"<VerificationToken(id={self.id}, type={self.token_type})>"
