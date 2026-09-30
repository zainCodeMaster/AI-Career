"""Offer and rejection service for Phase 7 CRM."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.crm import Offer, OfferStatus, Rejection
from app.db.models.crm import ApplicationActivity, ActivityEventType, ActorType
from app.services.crm.timeline_service import TimelineService


class OfferService:
    """Offer CRUD service."""

    @staticmethod
    def create(
        db: Session,
        user_id: UUID,
        application_id: UUID,
        base_salary: Optional[int] = None,
        currency: Optional[str] = None,
        bonus: Optional[int] = None,
        equity_notes: Optional[str] = None,
        employment_type: Optional[str] = None,
        location: Optional[str] = None,
        work_mode: Optional[str] = None,
        start_date: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
        benefits_notes: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Offer:
        offer = Offer(
            user_id=user_id,
            application_id=application_id,
            base_salary=base_salary,
            currency=currency,
            bonus=bonus,
            equity_notes=equity_notes,
            employment_type=employment_type,
            location=location,
            work_mode=work_mode,
            start_date=start_date,
            expires_at=expires_at,
            benefits_notes=benefits_notes,
            notes=notes,
        )
        db.add(offer)
        db.flush()
        TimelineService.add_event(
            db,
            application_id=application_id,
            user_id=user_id,
            event_type=ActivityEventType.OFFER_RECEIVED,
            title="Offer received",
            actor_type=ActorType.MANUAL,
            related_entity_type="offer",
            related_entity_id=offer.id,
        )
        db.flush()
        return offer

    @staticmethod
    def get(db: Session, offer_id: UUID, user_id: UUID) -> Optional[Offer]:
        return db.query(Offer).filter(Offer.id == offer_id, Offer.user_id == user_id).first()

    @staticmethod
    def get_by_application(db: Session, application_id: UUID, user_id: UUID) -> Optional[Offer]:
        return db.query(Offer).filter(
            Offer.application_id == application_id, Offer.user_id == user_id
        ).first()

    @staticmethod
    def update(db: Session, offer: Offer, **kwargs) -> Offer:
        for key, value in kwargs.items():
            if value is not None:
                setattr(offer, key, value)
        offer.updated_at = datetime.now(timezone.utc)
        db.flush()
        return offer

    @staticmethod
    def delete(db: Session, offer: Offer) -> None:
        db.delete(offer)
        db.flush()


class RejectionService:
    """Rejection CRUD service."""

    @staticmethod
    def create(
        db: Session,
        user_id: UUID,
        application_id: UUID,
        stage: Optional[str] = None,
        reason: Optional[str] = None,
        details: Optional[str] = None,
        is_employer_initiated: bool = True,
    ) -> Rejection:
        rejection = Rejection(
            user_id=user_id,
            application_id=application_id,
            stage=stage,
            reason=reason,
            details=details,
            is_employer_initiated=is_employer_initiated,
            rejected_at=datetime.now(timezone.utc),
        )
        db.add(rejection)
        db.flush()
        TimelineService.add_event(
            db,
            application_id=application_id,
            user_id=user_id,
            event_type=ActivityEventType.REJECTED,
            title="Application rejected",
            description=reason or stage or "No reason provided",
            actor_type=ActorType.SYSTEM if is_employer_initiated else ActorType.MANUAL,
            related_entity_type="rejection",
            related_entity_id=rejection.id,
        )
        db.flush()
        return rejection

    @staticmethod
    def get(db: Session, rejection_id: UUID, user_id: UUID) -> Optional[Rejection]:
        return db.query(Rejection).filter(
            Rejection.id == rejection_id, Rejection.user_id == user_id
        ).first()

    @staticmethod
    def get_by_application(db: Session, application_id: UUID, user_id: UUID) -> Optional[Rejection]:
        return db.query(Rejection).filter(
            Rejection.application_id == application_id, Rejection.user_id == user_id
        ).first()

    @staticmethod
    def delete(db: Session, rejection: Rejection) -> None:
        db.delete(rejection)
        db.flush()
