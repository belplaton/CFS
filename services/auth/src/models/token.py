"""
Verification Token model for Auth Service
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.models import Base


class VerificationToken(Base):
    """Verification Token model for email verification and password reset"""
    __tablename__ = "verification_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Token details
    token = Column(String(255), unique=True, nullable=False, index=True)
    token_type = Column(String(50), nullable=False)  # 'email_verification', 'password_reset'

    # Status
    is_used = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Relationship
    user = relationship("User", back_populates="verification_tokens")

    def __repr__(self):
        return f"<VerificationToken(id={self.id}, type={self.token_type})>"
