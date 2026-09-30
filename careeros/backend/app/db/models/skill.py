"""Skill model."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class Skill(Base):
    """Professional skills and competencies."""

    __tablename__ = "skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)  # e.g., "Technical", "Soft Skills", "Languages"
    proficiency = Column(String(50), nullable=True)  # e.g., "Beginner", "Intermediate", "Expert"
    
    years_of_experience = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<Skill(id={self.id}, user_id={self.user_id}, name={self.name})>"
