"""Phase 7 — Career CRM database models.

Structured application lifecycle tracking with companies, contacts, interviews,
follow-ups, offers/rejections, activity timeline, and AI recommendations.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    JSON,
    desc,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ApplicationStatus(str, PyEnum):
    """Application lifecycle states."""

    SAVED = "saved"
    READY_TO_APPLY = "ready_to_apply"
    APPLIED = "applied"
    APPLICATION_VIEWED = "application_viewed"
    SCREENING = "screening"
    INTERVIEW = "interview"
    TECHNICAL_INTERVIEW = "technical_interview"
    FINAL_INTERVIEW = "final_interview"
    OFFER = "offer"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"
    ON_HOLD = "on_hold"


class ApplicationPriority(str, PyEnum):
    """Application priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ApplicationSource(str, PyEnum):
    """How the application was created."""

    MANUAL = "manual"
    AI = "ai"
    AUTOMATION = "automation"
    SYSTEM = "system"


class ContactRole(str, PyEnum):
    """Role of a contact in relation to an application."""

    RECRUITER = "recruiter"
    HIRING_MANAGER = "hiring_manager"
    INTERVIEWER = "interviewer"
    REFERRAL = "referral"
    OTHER = "other"


class InterviewType(str, PyEnum):
    """Types of interviews."""

    HR_SCREEN = "hr_screen"
    TECHNICAL = "technical"
    CODING = "coding"
    SYSTEM_DESIGN = "system_design"
    BEHAVIORAL = "behavioral"
    FINAL = "final"
    OTHER = "other"


class InterviewStatus(str, PyEnum):
    """Interview scheduling status."""

    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


class InterviewOutcome(str, PyEnum):
    """Interview outcome."""

    PASSED = "passed"
    FAILED = "failed"
    PENDING = "pending"
    UNKNOWN = "unknown"


class OfferStatus(str, PyEnum):
    """Offer lifecycle status."""

    RECEIVED = "received"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"
    NEGOTIATING = "negotiating"


class FollowUpType(str, PyEnum):
    """Follow-up category."""

    RECRUITER_FOLLOW_UP = "recruiter_follow_up"
    STATUS_CHECK = "status_check"
    INTERVIEW_PREP = "interview_prep"
    THANK_YOU_NOTE = "thank_you_note"
    DEADLINE = "deadline"
    CUSTOM = "custom"


class FollowUpStatus(str, PyEnum):
    """Follow-up completion status."""

    PENDING = "pending"
    DONE = "done"
    SNOOZED = "snoozed"
    CANCELLED = "cancelled"


class AutomationState(str, PyEnum):
    """Automation state for Phase 8/9 compatibility."""

    NOT_ATTEMPTED = "not_attempted"
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"


class ActivityEventType(str, PyEnum):
    """Application activity event types."""

    APPLICATION_CREATED = "application_created"
    JOB_SAVED = "job_saved"
    APPLICATION_SUBMITTED = "application_submitted"
    STATUS_CHANGED = "status_changed"
    RESUME_ATTACHED = "resume_attached"
    COVER_LETTER_ATTACHED = "cover_letter_attached"
    CONTACT_ADDED = "contact_added"
    EMAIL_LOGGED = "email_logged"
    EMAIL_SENT = "email_sent"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_COMPLETED = "interview_completed"
    FOLLOW_UP_CREATED = "follow_up_created"
    FOLLOW_UP_COMPLETED = "follow_up_completed"
    OFFER_RECEIVED = "offer_received"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    AI_RECOMMENDATION_GENERATED = "ai_recommendation_generated"
    AUTOMATION_EXECUTED = "automation_executed"


class ActorType(str, PyEnum):
    """Who performed an action."""

    MANUAL = "manual"
    AI = "ai"
    AUTOMATION = "automation"
    SYSTEM = "system"


# ---------------------------------------------------------------------------
# Company
# ---------------------------------------------------------------------------


class Company(Base):
    """Global normalized company catalog.

    Companies are global resources. User-specific data (notes, relationship
    status, preferences) lives in ``UserCompanyLink``.
    """

    __tablename__ = "companies"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    canonical_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True
    )
    website: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    industry: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    size: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint("domain", name="uq_companies_domain"),
        UniqueConstraint("normalized_name", name="uq_companies_normalized_name"),
        Index("ix_companies_industry", "industry"),
    )

    links: Mapped[list["UserCompanyLink"]] = relationship(
        "UserCompanyLink", back_populates="company", cascade="all, delete-orphan"
    )
    applications: Mapped[list["Application"]] = relationship(
        "Application", back_populates="company"
    )
    contacts: Mapped[list["Contact"]] = relationship(
        "Contact", back_populates="company"
    )

    def __repr__(self) -> str:
        return f"<Company(id={self.id}, name={self.name}, domain={self.domain})>"


class UserCompanyLink(Base):
    """User-scoped overlay on a global Company."""

    __tablename__ = "user_company_links"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    company_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    relationship_status: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )
    is_favorite: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint("user_id", "company_id", name="uq_user_company_link"),
    )

    user: Mapped["User"] = relationship("User", lazy="selectin")
    company: Mapped["Company"] = relationship("Company", back_populates="links")

    def __repr__(self) -> str:
        return f"<UserCompanyLink(id={self.id}, user_id={self.user_id}, company_id={self.company_id})>"


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------


class Application(Base):
    """Core CRM application entity."""

    __tablename__ = "applications"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # Application metadata
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    # Job references
    job_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("jobs.id"), nullable=True, index=True
    )
    job_match_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True, index=True
    )
    job_title_snapshot: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True
    )
    company_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("companies.id"), nullable=True, index=True
    )

    # Status and priority
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, native_enum=False, values_callable=lambda cls: [e.value for e in cls]),
        nullable=False,
        index=True,
        default=ApplicationStatus.SAVED,
    )
    previous_status: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True
    )
    priority: Mapped[ApplicationPriority] = mapped_column(
        Enum(ApplicationPriority, native_enum=False, values_callable=lambda cls: [e.value for e in cls]),
        nullable=False,
        default=ApplicationPriority.MEDIUM,
        index=True,
    )
    source: Mapped[ApplicationSource] = mapped_column(
        Enum(ApplicationSource, native_enum=False, values_callable=lambda cls: [e.value for e in cls]),
        nullable=False,
        default=ApplicationSource.MANUAL,
    )

    # Resume and documents
    resume_version_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("resumes.id"), nullable=True, index=True
    )
    cover_letter_document_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True, index=True
    )
    primary_contact_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("contacts.id"), nullable=True, index=True
    )

    # Dates
    applied_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    deadline_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    last_activity_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    next_action_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # External references
    application_url: Mapped[Optional[str]] = mapped_column(
        String(1024), nullable=True
    )
    external_application_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )

    # Notes and metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    match_snapshot: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )
    automation_metadata: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )
    automation_state: Mapped[AutomationState] = mapped_column(
        Enum(AutomationState, native_enum=False, values_callable=lambda cls: [e.value for e in cls]),
        nullable=False,
        default=AutomationState.NOT_ATTEMPTED,
        index=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", lazy="selectin")
    job: Mapped[Optional["Job"]] = relationship("Job", lazy="selectin")
    company: Mapped[Optional["Company"]] = relationship(
        "Company", back_populates="applications", lazy="selectin"
    )
    resume_version: Mapped[Optional["Resume"]] = relationship(
        "Resume", lazy="selectin"
    )
    activities: Mapped[list["ApplicationActivity"]] = relationship(
        "ApplicationActivity",
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="ApplicationActivity.occurred_at.desc()",
    )
    documents: Mapped[list["ApplicationDocument"]] = relationship(
        "ApplicationDocument",
        back_populates="application",
        cascade="all, delete-orphan",
    )
    application_contacts: Mapped[list["ApplicationContact"]] = relationship(
        "ApplicationContact",
        back_populates="application",
        cascade="all, delete-orphan",
    )
    interviews: Mapped[list["Interview"]] = relationship(
        "Interview",
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="Interview.scheduled_at.desc()",
    )
    follow_ups: Mapped[list["FollowUp"]] = relationship(
        "FollowUp",
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="FollowUp.due_at.desc()",
    )
    offer: Mapped[Optional["Offer"]] = relationship(
        "Offer",
        back_populates="application",
        uselist=False,
        cascade="all, delete-orphan",
    )
    rejection: Mapped[Optional["Rejection"]] = relationship(
        "Rejection",
        back_populates="application",
        uselist=False,
        cascade="all, delete-orphan",
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        "Recommendation",
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="Recommendation.generated_at.desc()",
    )

    __table_args__ = (
        Index("ix_applications_user_status", "user_id", "status"),
        Index("ix_applications_user_next_action", "user_id", "next_action_at"),
        Index("ix_applications_user_deadline", "user_id", "deadline_at"),
        Index("ix_applications_user_created", "user_id", "created_at"),
        Index("ix_applications_company", "company_id"),
        Index("ix_applications_job", "job_id"),
        Index(
            "uq_active_application_per_user_job",
            "user_id",
            "job_id",
            unique=True,
            postgresql_where=(status.in_([
                ApplicationStatus.SAVED.value,
                ApplicationStatus.READY_TO_APPLY.value,
                ApplicationStatus.APPLIED.value,
                ApplicationStatus.APPLICATION_VIEWED.value,
                ApplicationStatus.SCREENING.value,
                ApplicationStatus.INTERVIEW.value,
                ApplicationStatus.TECHNICAL_INTERVIEW.value,
                ApplicationStatus.FINAL_INTERVIEW.value,
                ApplicationStatus.ON_HOLD.value,
                ApplicationStatus.OFFER.value,
            ])),
        ),
    )

    def __repr__(self) -> str:
        return f"<Application(id={self.id}, user_id={self.user_id}, status={self.status}, job_id={self.job_id})>"


# ---------------------------------------------------------------------------
# Application Activity Timeline
# ---------------------------------------------------------------------------


class ApplicationActivity(Base):
    """Append-only activity timeline event for an application."""

    __tablename__ = "application_activities"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    application_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[ActivityEventType] = mapped_column(
        Enum(ActivityEventType, native_enum=False, values_callable=lambda cls: [e.value for e in cls]),
        nullable=False,
        index=True,
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True
    )
    actor_type: Mapped[ActorType] = mapped_column(
        Enum(ActorType, native_enum=False, values_callable=lambda cls: [e.value for e in cls]),
        nullable=False,
        default=ActorType.MANUAL,
    )
    actor_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    related_entity_type: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )
    related_entity_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    event_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    application: Mapped["Application"] = relationship(
        "Application", back_populates="activities"
    )

    __table_args__ = (
        Index("ix_application_activities_app_occurred", "application_id", desc("occurred_at")),
    )

    def __repr__(self) -> str:
        return f"<ApplicationActivity(id={self.id}, application_id={self.application_id}, event={self.event_type})>"


# ---------------------------------------------------------------------------
# Application Documents
# ---------------------------------------------------------------------------


class ApplicationDocument(Base):
    """Documents linked to an application (resume versions, cover letters)."""

    __tablename__ = "application_documents"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    application_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    document_type: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    # resume | cover_letter | portfolio | other
    file_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    document_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    application: Mapped["Application"] = relationship(
        "Application", back_populates="documents"
    )

    __table_args__ = (
        Index("ix_application_documents_app_type", "application_id", "document_type"),
    )

    def __repr__(self) -> str:
        return f"<ApplicationDocument(id={self.id}, application_id={self.application_id}, type={self.document_type})>"


# ---------------------------------------------------------------------------
# Contact
# ---------------------------------------------------------------------------


class Contact(Base):
    """User-owned contact record, linked to a company."""

    __tablename__ = "contacts"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    company_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("companies.id"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    relationship_status: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )
    last_contacted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_follow_up_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    company: Mapped[Optional["Company"]] = relationship(
        "Company", back_populates="contacts", lazy="selectin"
    )
    application_links: Mapped[list["ApplicationContact"]] = relationship(
        "ApplicationContact", back_populates="contact", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_contacts_user_company", "user_id", "company_id"),
    )

    def __repr__(self) -> str:
        return f"<Contact(id={self.id}, user_id={self.user_id}, name={self.name})>"


class ApplicationContact(Base):
    """Join table between applications and contacts with a role."""

    __tablename__ = "application_contacts"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    application_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    contact_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[ContactRole] = mapped_column(
        Enum(ContactRole, native_enum=False, values_callable=lambda cls: [e.value for e in cls]),
        nullable=False,
        default=ContactRole.OTHER,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint("application_id", "contact_id", name="uq_application_contact"),
    )

    application: Mapped["Application"] = relationship(
        "Application", back_populates="application_contacts"
    )
    contact: Mapped["Contact"] = relationship(
        "Contact", back_populates="application_links"
    )

    def __repr__(self) -> str:
        return f"<ApplicationContact(id={self.id}, application_id={self.application_id}, contact_id={self.contact_id}, role={self.role})>"


# ---------------------------------------------------------------------------
# Interview
# ---------------------------------------------------------------------------


class Interview(Base):
    """Interview record linked to an application."""

    __tablename__ = "interviews"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    application_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    interview_type: Mapped[InterviewType] = mapped_column(
        Enum(InterviewType, native_enum=False, values_callable=lambda cls: [e.value for e in cls]),
        nullable=False,
        index=True,
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    duration_minutes: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    timezone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    location_or_meeting_url: Mapped[Optional[str]] = mapped_column(
        String(1024), nullable=True
    )
    interviewer_contact_ids: Mapped[Optional[list[str]]] = mapped_column(
        JSON, nullable=True
    )
    status: Mapped[InterviewStatus] = mapped_column(
        Enum(InterviewStatus, native_enum=False, values_callable=lambda cls: [e.value for e in cls]),
        nullable=False,
        default=InterviewStatus.SCHEDULED,
        index=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preparation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    outcome: Mapped[InterviewOutcome] = mapped_column(
        Enum(InterviewOutcome, native_enum=False, values_callable=lambda cls: [e.value for e in cls]),
        nullable=False,
        default=InterviewOutcome.PENDING,
        index=True,
    )
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    application: Mapped["Application"] = relationship(
        "Application", back_populates="interviews"
    )

    __table_args__ = (
        Index("ix_interviews_user_application", "user_id", "application_id"),
        Index("ix_interviews_scheduled", "scheduled_at"),
    )

    def __repr__(self) -> str:
        return f"<Interview(id={self.id}, application_id={self.application_id}, type={self.interview_type}, status={self.status})>"


# ---------------------------------------------------------------------------
# Follow-up
# ---------------------------------------------------------------------------


class FollowUp(Base):
    """Follow-up task linked to an application or contact."""

    __tablename__ = "follow_ups"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    application_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    contact_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    follow_up_type: Mapped[FollowUpType] = mapped_column(
        Enum(FollowUpType, native_enum=False, values_callable=lambda cls: [e.value for e in cls]),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    due_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    priority: Mapped[str] = mapped_column(
        String(32), nullable=False, default="medium", index=True
    )
    status: Mapped[FollowUpStatus] = mapped_column(
        Enum(FollowUpStatus, native_enum=False, values_callable=lambda cls: [e.value for e in cls]),
        nullable=False,
        default=FollowUpStatus.PENDING,
        index=True,
    )
    reminder_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_by: Mapped[ActorType] = mapped_column(
        Enum(ActorType, native_enum=False, values_callable=lambda cls: [e.value for e in cls]),
        nullable=False,
        default=ActorType.MANUAL,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    application: Mapped[Optional["Application"]] = relationship(
        "Application", back_populates="follow_ups"
    )

    __table_args__ = (
        Index("ix_follow_ups_user_status_due", "user_id", "status", "due_at"),
    )

    def __repr__(self) -> str:
        return f"<FollowUp(id={self.id}, user_id={self.user_id}, application_id={self.application_id}, status={self.status})>"


# ---------------------------------------------------------------------------
# Offer
# ---------------------------------------------------------------------------


class Offer(Base):
    """Job offer record linked to an application."""

    __tablename__ = "offers"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    application_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    base_salary: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Base salary in minor units (e.g. cents)"
    )
    currency: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    bonus: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Bonus in minor units"
    )
    equity_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    employment_type: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )
    location: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    work_mode: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True
    )
    # remote | hybrid | onsite
    start_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    benefits_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[OfferStatus] = mapped_column(
        Enum(OfferStatus, native_enum=False, values_callable=lambda cls: [e.value for e in cls]),
        nullable=False,
        default=OfferStatus.RECEIVED,
        index=True,
    )
    document_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True, index=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    application: Mapped["Application"] = relationship(
        "Application", back_populates="offer"
    )

    __table_args__ = (
        Index("ix_offers_user_application", "user_id", "application_id"),
    )

    def __repr__(self) -> str:
        return f"<Offer(id={self.id}, application_id={self.application_id}, status={self.status})>"


class Rejection(Base):
    """Rejection record linked to an application."""

    __tablename__ = "rejections"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    application_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    stage: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="Stage at which rejection occurred"
    )
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rejected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True
    )
    is_employer_initiated: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    application: Mapped["Application"] = relationship(
        "Application", back_populates="rejection"
    )

    __table_args__ = (
        Index("ix_rejections_user_application", "user_id", "application_id"),
    )

    def __repr__(self) -> str:
        return f"<Rejection(id={self.id}, application_id={self.application_id}, stage={self.stage})>"


# ---------------------------------------------------------------------------
# Recommendation
# ---------------------------------------------------------------------------


class Recommendation(Base):
    """AI or deterministic recommendation for an application."""

    __tablename__ = "recommendations"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    application_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    recommendation_type: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    severity: Mapped[str] = mapped_column(
        String(32), nullable=False, default="info", index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    suggested_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True
    )
    model: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    provider: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    prompt_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    dismissed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    dismissed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    application: Mapped[Optional["Application"]] = relationship(
        "Application", back_populates="recommendations"
    )

    __table_args__ = (
        Index("ix_recommendations_user_app", "user_id", "application_id"),
        Index("ix_recommendations_dismissed", "dismissed"),
    )

    def __repr__(self) -> str:
        return f"<Recommendation(id={self.id}, type={self.recommendation_type}, severity={self.severity})>"


# ---------------------------------------------------------------------------
# Notification
# ---------------------------------------------------------------------------


class NotificationType(str, PyEnum):
    """Notification type categories."""

    INTERVIEW_REMINDER = "interview_reminder"
    FOLLOW_UP_REMINDER = "follow_up_reminder"
    APPLICATION_STATUS_CHANGED = "application_status_changed"
    JOB_MATCH = "job_match"
    SYSTEM = "system"
    CAREER_BRAIN = "career_brain"


class Notification(Base):
    """In-app notification for a user.

    Notifications are user-scoped and user-owned. They carry a title,
    message, type, read/unread status, and optional deep-link target.
    """

    __tablename__ = "notifications"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    target_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("ix_notifications_user_read", "user_id", "read"),
        Index("ix_notifications_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, type={self.type}, read={self.read})>"


