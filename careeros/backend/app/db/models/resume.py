"""Phase 6 — Resume Engine database models.

Structured resume management with versioning and ATS analysis capabilities.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class ResumeType(PyEnum):
    """Types of resumes in the system."""
    
    BASE = "base"  # User's master resume built from Career Profile
    TAILORED = "tailored"  # Resume tailored for a specific job
    IMPORTED = "imported"  # Resume imported from external file (PDF/DOCX)


class ResumeStatus(PyEnum):
    """Status of a resume."""
    
    DRAFT = "draft"
    READY = "ready"
    ARCHIVED = "archived"


class Resume(Base):
    """User's resume document.
    
    Resumes are user-scoped and can be:
    - BASE: Built from user's verified Career Profile data
    - TAILORED: Customized for a specific job application
    - IMPORTED: Uploaded external resume (PDF/DOCX) that's been parsed
    
    Each resume can have multiple versions (for iterative improvements).
    """
    
    __tablename__ = "resumes"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    
    # Ownership
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    
    # Resume metadata
    name: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g., "Software Engineer Resume"
    resume_type: Mapped[ResumeType] = mapped_column(
        Enum(ResumeType, native_enum=False, values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        nullable=False, index=True, default=ResumeType.BASE
    )
    status: Mapped[ResumeStatus] = mapped_column(
        Enum(ResumeStatus, native_enum=False, values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        nullable=False, index=True, default=ResumeStatus.DRAFT
    )
    
    # For tailored resumes, reference the target job
    target_job_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("jobs.id"), nullable=True, index=True
    )
    
    # For versioned resumes, reference the parent resume
    parent_resume_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resumes.id"), nullable=True, index=True
    )
    
    # Version tracking
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    
    # Structured resume data (JSON blob for flexibility)
    # Format: {
    #   "summary": "Professional summary...",
    #   "skills": [{"name": "Python", "category": "technical", "proficiency": "advanced"}],
    #   "experience": [...],
    #   "education": [...],
    #   "projects": [...],
    #   "certifications": [...],
    #   "achievements": [...],
    #   "custom_sections": {...}
    # }
    structured_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Import metadata (for imported resumes)
    source_file_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    source_file_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True  # pdf, docx, txt
    )
    import_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # ATS analysis cache (latest analysis for this resume)
    ats_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ats_breakdown: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ats_analyzed_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ats_analyzed_for_job_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("jobs.id"), nullable=True, index=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user: Mapped["app.db.models.user.User"] = relationship(
        "app.db.models.user.User", lazy="selectin"
    )
    target_job: Mapped[Optional["Job"]] = relationship(
        "Job", lazy="selectin", foreign_keys=[target_job_id]
    )
    parent_resume: Mapped[Optional["Resume"]] = relationship(
        "Resume", lazy="selectin", remote_side=[id], foreign_keys=[parent_resume_id]
    )
    # Versions (child resumes)
    versions: Mapped[list["Resume"]] = relationship(
        "Resume", lazy="selectin",
        foreign_keys="Resume.parent_resume_id",
        cascade="all, delete-orphan",
        overlaps="parent_resume"
    )
    analyzed_for_job: Mapped[Optional["Job"]] = relationship(
        "Job", lazy="selectin", foreign_keys=[ats_analyzed_for_job_id]
    )

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("user_id", "name", "version_number", name="uq_resume_user_name_version"),
        Index("ix_resumes_user_type", "user_id", "resume_type"),
        Index("ix_resumes_target_job", "target_job_id"),
        Index("ix_resumes_parent", "parent_resume_id"),
        Index("ix_resumes_ats_analyzed", "ats_analyzed_for_job_id"),
    )

    def __repr__(self) -> str:
        return f"<Resume(id={self.id}, user_id={self.user_id}, name='{self.name}', type={self.resume_type}, version={self.version_number})>"


class ResumeSection(Base):
    """Individual sections of a resume for granular versioning and tracking.
    
    This model allows for more granular tracking of changes between resume versions
    and enables section-level ATS analysis and recommendations.
    """
    
    __tablename__ = "resume_sections"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    
    # Ownership
    resume_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False, index=True
    )
    
    # Section identification
    section_type: Mapped[String] = mapped_column(
        String(50), nullable=False, index=True
    )  # summary, skills, experience, education, etc.
    section_title: Mapped[Optional[String]] = mapped_column(
        String(255), nullable=True
    )  # e.g., "Professional Experience", "Technical Skills"
    
    # Section content
    content: Mapped[Text] = mapped_column(Text, nullable=False)
    display_order: Mapped[Integer] = mapped_column(Integer, nullable=False, default=0)
    
    # Metadata
    is_custom: Mapped[Boolean] = mapped_column(
        Boolean, nullable=False, default=False
    )  # User-created vs standard section
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    resume: Mapped["Resume"] = relationship(
        "Resume", lazy="selectin", backref="sections"
    )

    # Indexes
    __table_args__ = (
        Index("ix_resume_sections_resume_type", "resume_id", "section_type"),
        Index("ix_resume_sections_order", "resume_id", "display_order"),
    )

    def __repr__(self) -> str:
        return f"<ResumeSection(id={self.id}, resume_id={self.resume_id}, type='{self.section_type}', order={self.display_order})>"