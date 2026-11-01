"""Pydantic schemas for Phase 7 Career CRM.

Application lifecycle management with companies, contacts, interviews,
follow-ups, offers/rejections, activity timeline, and AI recommendations.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.jobs import JobSummary
from app.schemas.resume import ResumeSummary


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ApplicationStatusResponse(str, PyEnum):
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


class ApplicationPriorityResponse(str, PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ApplicationSourceResponse(str, PyEnum):
    MANUAL = "manual"
    AI = "ai"
    AUTOMATION = "automation"
    SYSTEM = "system"


class ActorTypeResponse(str, PyEnum):
    MANUAL = "manual"
    AI = "ai"
    AUTOMATION = "automation"
    SYSTEM = "system"


class ActivityEventTypeResponse(str, PyEnum):
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


class ContactRoleResponse(str, PyEnum):
    RECRUITER = "recruiter"
    HIRING_MANAGER = "hiring_manager"
    INTERVIEWER = "interviewer"
    REFERRAL = "referral"
    OTHER = "other"


class InterviewTypeResponse(str, PyEnum):
    HR_SCREEN = "hr_screen"
    TECHNICAL = "technical"
    CODING = "coding"
    SYSTEM_DESIGN = "system_design"
    BEHAVIORAL = "behavioral"
    FINAL = "final"
    OTHER = "other"


class InterviewStatusResponse(str, PyEnum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


class InterviewOutcomeResponse(str, PyEnum):
    PASSED = "passed"
    FAILED = "failed"
    PENDING = "pending"
    UNKNOWN = "unknown"


class FollowUpTypeResponse(str, PyEnum):
    RECRUITER_FOLLOW_UP = "recruiter_follow_up"
    STATUS_CHECK = "status_check"
    INTERVIEW_PREP = "interview_prep"
    THANK_YOU_NOTE = "thank_you_note"
    DEADLINE = "deadline"
    CUSTOM = "custom"


class FollowUpStatusResponse(str, PyEnum):
    PENDING = "pending"
    DONE = "done"
    SNOOZED = "snoozed"
    CANCELLED = "cancelled"


class OfferStatusResponse(str, PyEnum):
    RECEIVED = "received"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"
    NEGOTIATING = "negotiating"


# ---------------------------------------------------------------------------
# Company
# ---------------------------------------------------------------------------


class CompanyBase(BaseModel):
    """Base company schema."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., max_length=255)
    website: Optional[str] = Field(default=None, max_length=512)
    industry: Optional[str] = Field(default=None, max_length=255)
    location: Optional[str] = Field(default=None, max_length=512)
    size: Optional[str] = Field(default=None, max_length=64)
    description: Optional[str] = None
    logo_url: Optional[str] = Field(default=None, max_length=512)


class CompanyCreate(CompanyBase):
    """Create company request."""

    pass


class CompanyUpdate(BaseModel):
    """Update company request."""

    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(default=None, max_length=255)
    website: Optional[str] = Field(default=None, max_length=512)
    industry: Optional[str] = Field(default=None, max_length=255)
    location: Optional[str] = Field(default=None, max_length=512)
    size: Optional[str] = Field(default=None, max_length=64)
    description: Optional[str] = None
    logo_url: Optional[str] = Field(default=None, max_length=512)


class CompanyResponse(CompanyBase):
    """Company response."""

    id: UUID
    normalized_name: str
    canonical_name: Optional[str] = None
    domain: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class UserCompanyLinkBase(BaseModel):
    """Base user company link schema."""

    model_config = ConfigDict(from_attributes=True)

    notes: Optional[str] = None
    relationship_status: Optional[str] = Field(default=None, max_length=64)
    is_favorite: bool = False


class UserCompanyLinkCreate(UserCompanyLinkBase):
    """Create user company link request."""

    company_id: UUID


class UserCompanyLinkUpdate(BaseModel):
    """Update user company link request."""

    model_config = ConfigDict(from_attributes=True)

    notes: Optional[str] = None
    relationship_status: Optional[str] = Field(default=None, max_length=64)
    is_favorite: Optional[bool] = None


class UserCompanyLinkResponse(UserCompanyLinkBase):
    """User company link response."""

    id: UUID
    user_id: UUID
    company_id: UUID
    company: CompanyResponse
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------


class ApplicationBase(BaseModel):
    """Base application schema."""

    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(default=None, max_length=255)
    priority: ApplicationPriorityResponse = ApplicationPriorityResponse.MEDIUM
    source: ApplicationSourceResponse = ApplicationSourceResponse.MANUAL
    notes: Optional[str] = None
    application_url: Optional[str] = Field(default=None, max_length=1024)
    external_application_id: Optional[str] = Field(default=None, max_length=255)


class ApplicationCreate(ApplicationBase):
    """Create application request."""

    job_id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    job_title_snapshot: Optional[str] = Field(default=None, max_length=512)
    resume_version_id: Optional[UUID] = None
    cover_letter_document_id: Optional[UUID] = None
    primary_contact_id: Optional[UUID] = None
    deadline_at: Optional[datetime] = None


class ApplicationUpdate(BaseModel):
    """Update application request."""

    model_config = ConfigDict(from_attributes=True)

    status: Optional[ApplicationStatusResponse] = None
    previous_status: Optional[str] = Field(default=None, max_length=32)
    priority: Optional[ApplicationPriorityResponse] = None
    source: Optional[ApplicationSourceResponse] = None
    notes: Optional[str] = None
    application_url: Optional[str] = Field(default=None, max_length=1024)
    external_application_id: Optional[str] = Field(default=None, max_length=255)
    resume_version_id: Optional[UUID] = None
    cover_letter_document_id: Optional[UUID] = None
    primary_contact_id: Optional[UUID] = None
    deadline_at: Optional[datetime] = None


class ApplicationTransitionRequest(BaseModel):
    """Request to transition application status."""

    model_config = ConfigDict(from_attributes=True)

    to_status: ApplicationStatusResponse
    reason: Optional[str] = Field(default=None, max_length=255)
    metadata: Optional[Dict[str, Any]] = None


class ApplicationTransitionResponse(BaseModel):
    """Response from status transition."""

    model_config = ConfigDict(from_attributes=True)

    application_id: UUID
    from_status: str
    to_status: str
    transitioned_at: datetime
    message: Optional[str] = None


class ApplicationSummary(BaseModel):
    """Lightweight application representation for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: Optional[str] = None
    job_id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    status: ApplicationStatusResponse
    priority: ApplicationPriorityResponse
    source: ApplicationSourceResponse
    notes: Optional[str] = None
    job_title_snapshot: Optional[str] = None
    applied_at: Optional[datetime] = None
    deadline_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None
    next_action_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ApplicationResponse(ApplicationSummary):
    """Full application response."""

    job: Optional[JobSummary] = None
    company: Optional[CompanyResponse] = None
    resume_version: Optional[ResumeSummary] = None
    primary_contact: Optional["ContactResponse"] = None
    activities: List["ApplicationActivityResponse"] = []
    documents: List["ApplicationDocumentResponse"] = []
    interviews: List["InterviewResponse"] = []
    follow_ups: List["FollowUpResponse"] = []
    offer: Optional["OfferResponse"] = None
    rejection: Optional["RejectionResponse"] = None
    recommendations: List["RecommendationResponse"] = []


class ApplicationListResponse(BaseModel):
    """Paginated application list response."""

    items: List[ApplicationSummary]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Activity Timeline
# ---------------------------------------------------------------------------


class ApplicationActivityResponse(BaseModel):
    """Application activity timeline event."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_id: UUID
    event_type: ActivityEventTypeResponse
    occurred_at: datetime
    actor_type: ActorTypeResponse
    actor_id: Optional[UUID] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[UUID] = None
    title: str
    description: Optional[str] = None
    event_metadata: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Application Documents
# ---------------------------------------------------------------------------


class ApplicationDocumentBase(BaseModel):
    """Base application document schema."""

    model_config = ConfigDict(from_attributes=True)

    document_type: str = Field(..., max_length=64)
    file_url: Optional[str] = Field(default=None, max_length=512)
    file_name: Optional[str] = Field(default=None, max_length=255)
    file_size: Optional[int] = None
    mime_type: Optional[str] = Field(default=None, max_length=128)
    document_metadata: Optional[Dict[str, Any]] = None


class ApplicationDocumentCreate(ApplicationDocumentBase):
    """Create application document request."""

    pass


class ApplicationDocumentUpdate(BaseModel):
    """Update application document request."""

    model_config = ConfigDict(from_attributes=True)

    document_type: Optional[str] = Field(default=None, max_length=64)
    file_url: Optional[str] = Field(default=None, max_length=512)
    file_name: Optional[str] = Field(default=None, max_length=255)
    file_size: Optional[int] = None
    mime_type: Optional[str] = Field(default=None, max_length=128)
    document_metadata: Optional[Dict[str, Any]] = None


class ApplicationDocumentResponse(ApplicationDocumentBase):
    """Application document response."""

    id: UUID
    application_id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Contact
# ---------------------------------------------------------------------------


class ContactBase(BaseModel):
    """Base contact schema."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., max_length=255)
    title: Optional[str] = Field(default=None, max_length=255)
    email: Optional[str] = Field(default=None, max_length=255)
    linkedin_url: Optional[str] = Field(default=None, max_length=512)
    phone: Optional[str] = Field(default=None, max_length=64)
    notes: Optional[str] = None
    relationship_status: Optional[str] = Field(default=None, max_length=64)


class ContactCreate(ContactBase):
    """Create contact request."""

    company_id: Optional[UUID] = None


class ContactUpdate(BaseModel):
    """Update contact request."""

    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(default=None, max_length=255)
    title: Optional[str] = Field(default=None, max_length=255)
    email: Optional[str] = Field(default=None, max_length=255)
    linkedin_url: Optional[str] = Field(default=None, max_length=512)
    phone: Optional[str] = Field(default=None, max_length=64)
    notes: Optional[str] = None
    relationship_status: Optional[str] = Field(default=None, max_length=64)
    last_contacted_at: Optional[datetime] = None
    next_follow_up_at: Optional[datetime] = None


class ContactResponse(ContactBase):
    """Contact response."""

    id: UUID
    user_id: UUID
    company_id: Optional[UUID] = None
    company: Optional[CompanyResponse] = None
    last_contacted_at: Optional[datetime] = None
    next_follow_up_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ApplicationContactResponse(BaseModel):
    """Application contact link response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_id: UUID
    contact: ContactResponse
    role: ContactRoleResponse
    created_at: datetime


# ---------------------------------------------------------------------------
# Interview
# ---------------------------------------------------------------------------


class InterviewBase(BaseModel):
    """Base interview schema."""

    model_config = ConfigDict(from_attributes=True)

    interview_type: InterviewTypeResponse
    scheduled_at: datetime
    duration_minutes: Optional[int] = Field(default=None, ge=1, le=480)
    timezone: Optional[str] = Field(default=None, max_length=64)
    location_or_meeting_url: Optional[str] = Field(default=None, max_length=1024)
    interviewer_contact_ids: Optional[List[UUID]] = None
    notes: Optional[str] = None
    preparation_notes: Optional[str] = None
    feedback: Optional[str] = None


class InterviewCreate(InterviewBase):
    """Create interview request."""

    application_id: UUID


class InterviewUpdate(BaseModel):
    """Update interview request."""

    model_config = ConfigDict(from_attributes=True)

    interview_type: Optional[InterviewTypeResponse] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(default=None, ge=1, le=480)
    timezone: Optional[str] = Field(default=None, max_length=64)
    location_or_meeting_url: Optional[str] = Field(default=None, max_length=1024)
    interviewer_contact_ids: Optional[List[UUID]] = None
    status: Optional[InterviewStatusResponse] = None
    notes: Optional[str] = None
    preparation_notes: Optional[str] = None
    outcome: Optional[InterviewOutcomeResponse] = None
    feedback: Optional[str] = None


class InterviewResponse(InterviewBase):
    """Interview response."""

    id: UUID
    application_id: UUID
    user_id: UUID
    status: InterviewStatusResponse
    outcome: InterviewOutcomeResponse
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Follow-up
# ---------------------------------------------------------------------------


class FollowUpBase(BaseModel):
    """Base follow-up schema."""

    model_config = ConfigDict(from_attributes=True)

    follow_up_type: FollowUpTypeResponse
    title: str = Field(..., max_length=255)
    notes: Optional[str] = None
    due_at: datetime
    priority: str = Field(default="medium", max_length=32)
    reminder_at: Optional[datetime] = None


class FollowUpCreate(FollowUpBase):
    """Create follow-up request."""

    application_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None


class FollowUpUpdate(BaseModel):
    """Update follow-up request."""

    model_config = ConfigDict(from_attributes=True)

    follow_up_type: Optional[FollowUpTypeResponse] = None
    title: Optional[str] = Field(default=None, max_length=255)
    notes: Optional[str] = None
    due_at: Optional[datetime] = None
    priority: Optional[str] = Field(default=None, max_length=32)
    status: Optional[FollowUpStatusResponse] = None
    reminder_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class FollowUpResponse(FollowUpBase):
    """Follow-up response."""

    id: UUID
    application_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    status: FollowUpStatusResponse
    completed_at: Optional[datetime] = None
    created_by: ActorTypeResponse
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Offer
# ---------------------------------------------------------------------------


class OfferBase(BaseModel):
    """Base offer schema."""

    model_config = ConfigDict(from_attributes=True)

    base_salary: Optional[int] = Field(default=None, ge=0)
    currency: Optional[str] = Field(default=None, max_length=8)
    bonus: Optional[int] = Field(default=None, ge=0)
    equity_notes: Optional[str] = None
    employment_type: Optional[str] = Field(default=None, max_length=64)
    location: Optional[str] = Field(default=None, max_length=512)
    work_mode: Optional[str] = Field(default=None, max_length=32)
    start_date: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    benefits_notes: Optional[str] = None
    document_id: Optional[UUID] = None
    notes: Optional[str] = None


class OfferCreate(OfferBase):
    """Create offer request."""

    application_id: UUID


class OfferUpdate(BaseModel):
    """Update offer request."""

    model_config = ConfigDict(from_attributes=True)

    base_salary: Optional[int] = Field(default=None, ge=0)
    currency: Optional[str] = Field(default=None, max_length=8)
    bonus: Optional[int] = Field(default=None, ge=0)
    equity_notes: Optional[str] = None
    employment_type: Optional[str] = Field(default=None, max_length=64)
    location: Optional[str] = Field(default=None, max_length=512)
    work_mode: Optional[str] = Field(default=None, max_length=32)
    start_date: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    benefits_notes: Optional[str] = None
    status: Optional[OfferStatusResponse] = None
    document_id: Optional[UUID] = None
    notes: Optional[str] = None


class OfferResponse(OfferBase):
    """Offer response."""

    id: UUID
    application_id: UUID
    user_id: UUID
    status: OfferStatusResponse
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Rejection
# ---------------------------------------------------------------------------


class RejectionBase(BaseModel):
    """Base rejection schema."""

    model_config = ConfigDict(from_attributes=True)

    stage: Optional[str] = Field(default=None, max_length=64)
    reason: Optional[str] = Field(default=None, max_length=255)
    details: Optional[str] = None
    is_employer_initiated: bool = True


class RejectionCreate(RejectionBase):
    """Create rejection request."""

    application_id: UUID


class RejectionResponse(RejectionBase):
    """Rejection response."""

    id: UUID
    application_id: UUID
    user_id: UUID
    rejected_at: datetime
    created_at: datetime


# ---------------------------------------------------------------------------
# Recommendation
# ---------------------------------------------------------------------------


class RecommendationBase(BaseModel):
    """Base recommendation schema."""

    model_config = ConfigDict(from_attributes=True)

    recommendation_type: str = Field(..., max_length=64)
    severity: str = Field(default="info", max_length=32)
    title: str = Field(..., max_length=255)
    explanation: Optional[str] = None
    evidence: Optional[List[str]] = None
    suggested_action: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    model: Optional[str] = Field(default=None, max_length=128)
    provider: Optional[str] = Field(default=None, max_length=128)
    prompt_version: Optional[str] = Field(default=None, max_length=32)
    expires_at: Optional[datetime] = None


class RecommendationCreate(RecommendationBase):
    """Create recommendation request."""

    application_id: Optional[UUID] = None


class RecommendationResponse(RecommendationBase):
    """Recommendation response."""

    id: UUID
    application_id: Optional[UUID] = None
    generated_at: datetime
    dismissed: bool = False
    dismissed_at: Optional[datetime] = None
    created_at: datetime


# ---------------------------------------------------------------------------
# State machine helpers
# ---------------------------------------------------------------------------


class StateTransitionResponse(BaseModel):
    """Describes a single legal state transition."""

    from_status: ApplicationStatusResponse
    to_status: ApplicationStatusResponse
    allowed: bool
    requires_reason: bool = False
    message: Optional[str] = None


class StateMachineInfoResponse(BaseModel):
    """State machine metadata for a given application."""

    current_status: ApplicationStatusResponse
    allowed_transitions: List[StateTransitionResponse]
    is_terminal: bool
    can_reopen: bool = False


class AllowedTransitionResponse(BaseModel):
    """A single allowed transition with metadata."""

    to_status: ApplicationStatusResponse
    label: str
    requires_reason: bool = False


# ---------------------------------------------------------------------------
# Dashboard / Pipeline / Analytics
# ---------------------------------------------------------------------------


class ApplicationStatsResponse(BaseModel):
    """Aggregated application statistics."""

    model_config = ConfigDict(from_attributes=True)

    total: int = 0
    active: int = 0
    saved: int = 0
    ready_to_apply: int = 0
    applied: int = 0
    screening: int = 0
    interview: int = 0
    technical_interview: int = 0
    final_interview: int = 0
    offer: int = 0
    accepted: int = 0
    rejected: int = 0
    withdrawn: int = 0
    expired: int = 0
    on_hold: int = 0
    response_rate: float = 0.0
    interview_rate: float = 0.0
    offer_rate: float = 0.0
    upcoming_interviews: int = 0
    pending_follow_ups: int = 0
    stale_applications: int = 0


class PipelineStageResponse(BaseModel):
    """Kanban pipeline stage."""

    model_config = ConfigDict(from_attributes=True)

    status: ApplicationStatusResponse
    label: str
    count: int
    applications: List[ApplicationSummary] = []


class PipelineResponse(BaseModel):
    """Pipeline board payload."""

    stages: List[PipelineStageResponse]
    total: int


class FunnelStageResponse(BaseModel):
    """Funnel stage for analytics."""

    stage: ApplicationStatusResponse
    count: int
    conversion_rate: float = 0.0


class FunnelResponse(BaseModel):
    """Application funnel analytics."""

    stages: List[FunnelStageResponse]
    total_applications: int
    total_offers: int
    total_rejections: int
    average_days_to_offer: Optional[float] = None


class ActivityFeedResponse(BaseModel):
    """Cross-application activity feed."""

    items: List[ApplicationActivityResponse]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Notification Schemas
# ---------------------------------------------------------------------------


class NotificationTypeResponse(str, PyEnum):
    INTERVIEW_REMINDER = "interview_reminder"
    FOLLOW_UP_REMINDER = "follow_up_reminder"
    APPLICATION_STATUS_CHANGED = "application_status_changed"
    JOB_MATCH = "job_match"
    SYSTEM = "system"
    CAREER_BRAIN = "career_brain"


class NotificationResponse(BaseModel):
    """Notification payload."""

    id: str
    user_id: str
    type: NotificationTypeResponse
    title: str
    message: str
    read: bool
    target_url: Optional[str] = None
    created_at: datetime
    read_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    """Paginated notification list."""

    items: List[NotificationResponse]
    total: int
    page: int
    page_size: int
    unread_count: int


class MarkReadRequest(BaseModel):
    """Mark notification(s) as read."""

    notification_ids: List[str]
    mark_all: bool = False


# ---------------------------------------------------------------------------
# Forward references
# ---------------------------------------------------------------------------

# Resolve forward references after all models are defined.
ApplicationResponse.model_rebuild()
ApplicationActivityResponse.model_rebuild()
ApplicationDocumentResponse.model_rebuild()
ApplicationContactResponse.model_rebuild()
InterviewResponse.model_rebuild()
FollowUpResponse.model_rebuild()
OfferResponse.model_rebuild()
RejectionResponse.model_rebuild()
RecommendationResponse.model_rebuild()
UserCompanyLinkResponse.model_rebuild()
NotificationResponse.model_rebuild()

