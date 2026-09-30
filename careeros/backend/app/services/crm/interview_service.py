"""Interview service for Phase 7 CRM."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.crm import Interview, InterviewStatus, InterviewOutcome
from app.db.models.crm import ApplicationActivity, ActivityEventType, ActorType
from app.services.crm.timeline_service import TimelineService


class InterviewService:
    """Interview CRUD service."""

    @staticmethod
    def create(
        db: Session,
        user_id: UUID,
        application_id: UUID,
        interview_type: str,
        scheduled_at: datetime,
        duration_minutes: Optional[int] = None,
        timezone: Optional[str] = None,
        location_or_meeting_url: Optional[str] = None,
        interviewer_contact_ids: Optional[list[str]] = None,
        notes: Optional[str] = None,
        preparation_notes: Optional[str] = None,
    ) -> Interview:
        interview = Interview(
            user_id=user_id,
            application_id=application_id,
            interview_type=interview_type,
            scheduled_at=scheduled_at,
            duration_minutes=duration_minutes,
            timezone=timezone,
            location_or_meeting_url=location_or_meeting_url,
            interviewer_contact_ids=interviewer_contact_ids,
            notes=notes,
            preparation_notes=preparation_notes,
        )
        db.add(interview)
        db.flush()
        TimelineService.add_event(
            db,
            application_id=application_id,
            user_id=user_id,
            event_type=ActivityEventType.INTERVIEW_SCHEDULED,
            title=f"Interview scheduled: {interview_type}",
            description=f"Scheduled for {scheduled_at.isoformat()}",
            actor_type=ActorType.MANUAL,
            related_entity_type="interview",
            related_entity_id=interview.id,
        )
        db.flush()
        return interview

    @staticmethod
    def get(db: Session, interview_id: UUID, user_id: UUID) -> Optional[Interview]:
        return db.query(Interview).filter(
            Interview.id == interview_id, Interview.user_id == user_id
        ).first()

    @staticmethod
    def list_for_application(db: Session, user_id: UUID, application_id: UUID) -> List[Interview]:
        return list(db.query(Interview).filter(
            Interview.user_id == user_id,
            Interview.application_id == application_id,
        ).order_by(Interview.scheduled_at.desc()).all())

    @staticmethod
    def update(db: Session, interview: Interview, **kwargs) -> Interview:
        for key, value in kwargs.items():
            if value is not None:
                setattr(interview, key, value)
        interview.updated_at = datetime.now(timezone.utc)
        db.flush()
        return interview

    @staticmethod
    def complete(db: Session, interview: Interview, outcome: str = "pending", feedback: Optional[str] = None) -> Interview:
        interview.status = InterviewStatus.COMPLETED
        interview.outcome = InterviewOutcome(outcome)
        if feedback:
            interview.feedback = feedback
        interview.updated_at = datetime.now(timezone.utc)
        db.flush()
        TimelineService.add_event(
            db,
            application_id=interview.application_id,
            user_id=interview.user_id,
            event_type=ActivityEventType.INTERVIEW_COMPLETED,
            title=f"Interview completed: {interview.interview_type}",
            description=f"Outcome: {interview.outcome.value}",
            actor_type=ActorType.MANUAL,
            related_entity_type="interview",
            related_entity_id=interview.id,
        )
        db.flush()
        return interview

    @staticmethod
    def cancel(db: Session, interview: Interview) -> Interview:
        interview.status = InterviewStatus.CANCELLED
        interview.updated_at = datetime.now(timezone.utc)
        db.flush()
        return interview

    @staticmethod
    def delete(db: Session, interview: Interview) -> None:
        db.delete(interview)
        db.flush()
