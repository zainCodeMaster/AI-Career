"""Work Experience model."""

from datetime import datetime, timezone, date
from uuid import uuid4

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Date, Boolean
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class WorkExperience(Base):
    """Work experience and employment history."""

    __tablename__ = "work_experience"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    company = Column(String(255), nullable=False)
    job_title = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    is_current = Column(Boolean, nullable=False, default=False, index=True)
    
    description = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<WorkExperience(id={self.id}, user_id={self.user_id}, company={self.company}, title={self.job_title})>"
