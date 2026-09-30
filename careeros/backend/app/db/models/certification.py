"""Certification model."""

from datetime import datetime, timezone, date
from uuid import uuid4

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class Certification(Base):
    """Professional certifications and credentials."""

    __tablename__ = "certifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    issuing_organization = Column(String(255), nullable=True)
    
    issue_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    
    credential_id = Column(String(255), nullable=True)
    credential_url = Column(String(512), nullable=True)
    
    description = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<Certification(id={self.id}, user_id={self.user_id}, name={self.name})>"
