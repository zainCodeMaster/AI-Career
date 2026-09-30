"""Follow-up service for Phase 7 CRM."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.crm import FollowUp, FollowUpStatus
from app.db.models.crm import ApplicationActivity, ActivityEventType, ActorType
from app.services.crm.timeline_service import TimelineService


class FollowUpService:
    """Follow-up CRUD and next-action computation."""

    @staticmethod
    def create(
        db: Session,
        user_id: UUID,
        application_id: Optional[UUID] = None,
        contact_id: Optional[UUID] = None,
        follow_up_type: str = "custom",
        title: str = "",
        notes: Optional[str] = None,
        due_at: Optional[datetime] = None,
        priority: str = "medium",
        reminder_at: Optional[datetime] = None,
        created_by: str = "manual",
    ) -> FollowUp:
        follow_up = FollowUp(
            user_id=user_id,
            application_id=application_id,
            contact_id=contact_id,
            follow_up_type=follow_up_type,
            title=title,
            notes=notes,
            due_at=due_at or datetime.now(timezone.utc),
            priority=priority,
            reminder_at=reminder_at,
            created_by=created_by,
        )
        db.add(follow_up)
        db.flush()
        if application_id:
            TimelineService.add_event(
                db,
                application_id=application_id,
                user_id=user_id,
                event_type=ActivityEventType.FOLLOW_UP_CREATED,
                title=f"Follow-up created: {title}",
                actor_type=ActorType.MANUAL,
                related_entity_type="follow_up",
                related_entity_id=follow_up.id,
            )
            db.flush()
        return follow_up

    @staticmethod
    def get(db: Session, follow_up_id: UUID, user_id: UUID) -> Optional[FollowUp]:
        return db.query(FollowUp).filter(
            FollowUp.id == follow_up_id, FollowUp.user_id == user_id
        ).first()

    @staticmethod
    def list_for_application(db: Session, user_id: UUID, application_id: UUID) -> List[FollowUp]:
        return list(db.query(FollowUp).filter(
            FollowUp.user_id == user_id,
            FollowUp.application_id == application_id,
        ).order_by(FollowUp.due_at.desc()).all())

    @staticmethod
    def list_due_before(db: Session, user_id: UUID, before: datetime) -> List[FollowUp]:
        """Return open follow-ups due before the given timestamp for a user."""
        return list(db.query(FollowUp).filter(
            FollowUp.user_id == user_id,
            FollowUp.status == FollowUpStatus.PENDING,
            FollowUp.due_at <= before,
        ).order_by(FollowUp.due_at.asc()).all())

    @staticmethod
    def complete(db: Session, follow_up: FollowUp) -> FollowUp:
        follow_up.status = FollowUpStatus.DONE
        follow_up.completed_at = datetime.now(timezone.utc)
        follow_up.updated_at = datetime.now(timezone.utc)
        db.flush()
        if follow_up.application_id:
            TimelineService.add_event(
                db,
                application_id=follow_up.application_id,
                user_id=follow_up.user_id,
                event_type=ActivityEventType.FOLLOW_UP_COMPLETED,
                title=f"Follow-up completed: {follow_up.title}",
                actor_type=ActorType.MANUAL,
                related_entity_type="follow_up",
                related_entity_id=follow_up.id,
            )
            db.flush()
        return follow_up

    @staticmethod
    def update(db: Session, follow_up: FollowUp, **kwargs) -> FollowUp:
        for key, value in kwargs.items():
            if value is not None:
                setattr(follow_up, key, value)
        follow_up.updated_at = datetime.now(timezone.utc)
        db.flush()
        return follow_up

    @staticmethod
    def delete(db: Session, follow_up: FollowUp) -> None:
        db.delete(follow_up)
        db.flush()
