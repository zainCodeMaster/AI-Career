"""Application timeline service for Phase 7 CRM."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.crm import ApplicationActivity
from app.schemas.crm import ApplicationActivityResponse
from app.db.models.crm import ActivityEventType, ActorType


class TimelineService:
    """Append-only activity timeline for applications."""

    @staticmethod
    def add_event(
        db: Session,
        application_id: UUID,
        user_id: UUID,
        event_type: ActivityEventType,
        title: str,
        description: Optional[str] = None,
        actor_type: ActorType = ActorType.MANUAL,
        actor_id: Optional[UUID] = None,
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[UUID] = None,
        event_metadata: Optional[dict] = None,
    ) -> ApplicationActivity:
        """Append an event to the application timeline.

        Writes happen inside the caller's transaction.
        """
        event = ApplicationActivity(
            application_id=application_id,
            user_id=user_id,
            event_type=event_type,
            title=title,
            description=description,
            occurred_at=datetime.now(timezone.utc),
            actor_type=actor_type,
            actor_id=actor_id,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            event_metadata=event_metadata,
        )
        db.add(event)
        db.flush()
        return event

    @staticmethod
    def list_events(
        db: Session,
        user_id: UUID,
        application_id: Optional[UUID] = None,
        event_type: Optional[ActivityEventType] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[ApplicationActivityResponse], int]:
        """List timeline events, optionally filtered by application and event type."""
        stmt = select(ApplicationActivity).where(ApplicationActivity.user_id == user_id)
        if application_id:
            stmt = stmt.where(ApplicationActivity.application_id == application_id)
        if event_type:
            stmt = stmt.where(ApplicationActivity.event_type == event_type)
        total = len(db.execute(stmt).scalars().all())
        stmt = stmt.order_by(ApplicationActivity.occurred_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        events = list(db.execute(stmt).scalars().all())
        return [ApplicationActivityResponse.model_validate(e) for e in events], total

    @staticmethod
    def get_event(db: Session, event_id: UUID, user_id: UUID) -> Optional[ApplicationActivity]:
        """Get a single timeline event by ID."""
        return db.get(ApplicationActivity, event_id)
