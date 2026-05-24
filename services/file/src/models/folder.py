"""
Folder model for File Service
"""

from sqlalchemy import UUID, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func

from src.models import Base


class Folder(Base):
    """Folder model"""

    __tablename__ = "folders"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=func.gen_random_uuid())
    user_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    parent_id = Column(PGUUID(as_uuid=True), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    path = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Folder(id={self.id}, name='{self.name}', user_id={self.user_id})>"
