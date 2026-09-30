"""Career Profile model."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Float, Integer
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class CareerProfile(Base):
    """
    User's main career profile.
    
    One profile per user, containing professional summary and career preferences.
    """

    __tablename__ = "career_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    professional_title = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)
    location = Column(String(255), nullable=True)
    
    linkedin_url = Column(String(512), nullable=True)
    github_url = Column(String(512), nullable=True)
    portfolio_url = Column(String(512), nullable=True)
    
    years_of_experience = Column(Integer, nullable=True)
    preferred_job_title = Column(String(255), nullable=True)
    preferred_location = Column(String(255), nullable=True)
    remote_preference = Column(String(50), nullable=True)  # e.g., "remote", "on-site", "hybrid"
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<CareerProfile(id={self.id}, user_id={self.user_id}, title={self.professional_title})>"
