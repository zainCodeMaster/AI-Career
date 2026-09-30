"""Application service for Phase 7 CRM."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models.crm import (
    Application,
    ApplicationStatus,
    ApplicationPriority,
    ApplicationSource,
    ActivityEventType,
    ActorType,
    ApplicationActivity,
)
from app.services.crm.company_service import CompanyService
from app.services.crm.state_machine import ApplicationStateMachine
from app.services.crm.timeline_service import TimelineService
from app.services.crm.recommendations import RecommendationService
from app.db.models.resume import Resume


class ApplicationService:
    """Application CRUD and transition service."""

    @staticmethod
    def create(
        db: Session,
        user_id: UUID,
        name: Optional[str] = None,
        job_id: Optional[UUID] = None,
        company_id: Optional[UUID] = None,
        job_title_snapshot: Optional[str] = None,
        resume_version_id: Optional[UUID] = None,
        cover_letter_document_id: Optional[UUID] = None,
        primary_contact_id: Optional[UUID] = None,
        priority: str = "medium",
        source: str = "manual",
        application_url: Optional[str] = None,
        external_application_id: Optional[str] = None,
        notes: Optional[str] = None,
        deadline_at: Optional[datetime] = None,
        match_snapshot: Optional[dict] = None,
    ) -> Application:
        app = Application(
            user_id=user_id,
            name=name,
            job_id=job_id,
            company_id=company_id,
            job_title_snapshot=job_title_snapshot,
            resume_version_id=resume_version_id,
            cover_letter_document_id=cover_letter_document_id,
            primary_contact_id=primary_contact_id,
            priority=ApplicationPriority(priority),
            source=ApplicationSource(source),
            application_url=application_url,
            external_application_id=external_application_id,
            notes=notes,
            deadline_at=deadline_at,
            match_snapshot=match_snapshot,
            status=ApplicationStatus.SAVED,
        )
        db.add(app)
        db.flush()
        TimelineService.add_event(
            db,
            application_id=app.id,
            user_id=user_id,
            event_type=ActivityEventType.APPLICATION_CREATED,
            title="Application created",
            actor_type=ActorType.MANUAL,
            related_entity_type="application",
            related_entity_id=app.id,
        )
        db.flush()
        return app

    @staticmethod
    def get(db: Session, application_id: UUID, user_id: UUID) -> Optional[Application]:
        return db.query(Application).filter(
            Application.id == application_id, Application.user_id == user_id
        ).first()

    @staticmethod
    def list(
        db: Session,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        status: Optional[List[str]] = None,
        company_id: Optional[UUID] = None,
        priority: Optional[str] = None,
        source: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
    ) -> tuple[List[Application], int]:
        stmt = select(Application).where(Application.user_id == user_id)
        if status:
            stmt = stmt.where(Application.status.in_(status))
        if company_id:
            stmt = stmt.where(Application.company_id == company_id)
        if priority:
            stmt = stmt.where(Application.priority == priority)
        if source:
            stmt = stmt.where(Application.source == source)
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Application.job_title_snapshot.ilike(pattern),
                    Application.notes.ilike(pattern),
                )
            )
        allowed_sorts = {
            "created_at": Application.created_at,
            "updated_at": Application.updated_at,
            "status": Application.status,
            "priority": Application.priority,
            "applied_at": Application.applied_at,
            "deadline_at": Application.deadline_at,
            "next_action_at": Application.next_action_at,
        }
        sort_col = allowed_sorts.get(sort_by, Application.created_at)
        if sort_dir == "asc":
            stmt = stmt.order_by(sort_col.asc(), Application.id.asc())
        else:
            stmt = stmt.order_by(sort_col.desc(), Application.id.desc())
        total = len(db.execute(stmt).scalars().all())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        return list(db.execute(stmt).scalars().all()), total

    @staticmethod
    def update(db: Session, application: Application, **kwargs) -> Application:
        for key, value in kwargs.items():
            setattr(application, key, value)
        application.updated_at = datetime.now(timezone.utc)
        db.flush()
        return application

    @staticmethod
    def delete(db: Session, application: Application) -> None:
        db.delete(application)
        db.flush()

    @staticmethod
    def transition(
        db: Session,
        application: Application,
        to_status: str,
        user_id: UUID,
        reason: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> tuple[Application, str]:
        target = ApplicationStatus(to_status)
        success, error = ApplicationStateMachine.record_transition(
            application=application,
            to_status=target,
            reason=reason,
            actor_type="manual",
            actor_id=str(user_id),
        )
        if not success:
            return application, error or "Invalid transition"
        application.last_activity_at = datetime.now(timezone.utc)
        db.flush()
        title_map = {
            ApplicationStatus.APPLIED: "Application submitted",
            ApplicationStatus.REJECTED: "Application rejected",
            ApplicationStatus.WITHDRAWN: "Application withdrawn",
            ApplicationStatus.OFFER: "Offer received",
            ApplicationStatus.ACCEPTED: "Offer accepted",
            ApplicationStatus.ON_HOLD: "Application put on hold",
        }
        title = title_map.get(target, f"Status changed to {target.value}")
        TimelineService.add_event(
            db,
            application_id=application.id,
            user_id=user_id,
            event_type=ActivityEventType.STATUS_CHANGED,
            title=title,
            description=reason,
            actor_type=ActorType.MANUAL,
            related_entity_type="application",
            related_entity_id=application.id,
            event_metadata={
                "from_status": application.previous_status,
                "to_status": target.value,
                "reason": reason,
                **(metadata or {}),
            },
        )
        db.flush()
        return application, ""

    @staticmethod
    def attach_resume(
        db: Session,
        application: Application,
        resume_version_id: UUID,
        user_id: UUID,
    ) -> Application:
        application.resume_version_id = resume_version_id
        application.updated_at = datetime.now(timezone.utc)
        db.flush()
        TimelineService.add_event(
            db,
            application_id=application.id,
            user_id=user_id,
            event_type=ActivityEventType.RESUME_ATTACHED,
            title="Resume attached",
            actor_type=ActorType.MANUAL,
            related_entity_type="resume",
            related_entity_id=resume_version_id,
        )
        db.flush()
        return application

    @staticmethod
    def get_career_context(db: Session, application: Application) -> dict:
        """Assemble the Career Context panel for an application."""
        context = {
            "match_score": application.match_snapshot,
            "resume_used": None,
            "job": None,
            "company": None,
        }
        if application.resume_version_id:
            from app.db.models.resume import Resume
            resume = db.get(Resume, application.resume_version_id)
            if resume and resume.user_id == application.user_id:
                context["resume_used"] = {
                    "id": str(resume.id),
                    "name": resume.name,
                    "version_number": resume.version_number,
                    "resume_type": resume.resume_type.value if hasattr(resume.resume_type, "value") else str(resume.resume_type),
                }
        if application.job_id:
            from app.db.models.jobs import Job
            job = db.get(Job, application.job_id)
            if job:
                context["job"] = {
                    "id": str(job.id),
                    "title": job.title,
                    "company_name": job.company_name,
                    "location": job.location,
                }
        if application.company_id:
            from app.services.crm.company_service import CompanyService
            company = CompanyService.get(db, application.company_id)
            if company:
                context["company"] = {
                    "id": str(company.id),
                    "name": company.name,
                    "domain": company.domain,
                    "industry": company.industry,
                }
        return context

    @staticmethod
    def get_activity_timeline(
        db: Session,
        user_id: UUID,
        application_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20,
    ):
        return TimelineService.list_events(db, user_id, application_id, page=page, page_size=page_size)

    @staticmethod
    def get_recommendations(db: Session, application_id: UUID, user_id: UUID):
        application = ApplicationService.get(db, application_id, user_id)
        if not application:
            return []
        return RecommendationService.get_pending(db, user_id, application_id)

    @staticmethod
    def refresh_recommendations(db: Session, application_id: UUID, user_id: UUID):
        application = ApplicationService.get(db, application_id, user_id)
        if not application:
            return []
        return RecommendationService.generate_and_persist(db, application)
