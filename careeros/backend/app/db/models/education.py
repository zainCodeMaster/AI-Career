"""Education model."""

from datetime import datetime, timezone, date
from uuid import uuid4

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class Education(Base):
    """Education and academic credentials."""

    __tablename__ = "education"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    institution = Column(String(255), nullable=False)
    degree = Column(String(100), nullable=True)  # e.g., "Bachelor", "Master", "PhD"
    field_of_study = Column(String(255), nullable=True)
    
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    
    grade = Column(String(10), nullable=True)  # e.g., "3.8", "A", "Distinction"
    description = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<Education(id={self.id}, user_id={self.user_id}, institution={self.institution})>"
