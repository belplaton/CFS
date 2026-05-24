"""
File model for File Service
"""

from sqlalchemy import UUID, BigInteger, Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func

from src.models import Base


class File(Base):
    """File model"""

    __tablename__ = "files"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=func.gen_random_uuid())
    user_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    folder_id = Column(PGUUID(as_uuid=True), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=True)
    minio_object_id = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_permanently = Column(Boolean, default=False)

    def __repr__(self):
        return f"<File(id={self.id}, name='{self.name}', user_id={self.user_id}, size={self.size})>"
