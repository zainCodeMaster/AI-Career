"""Recommendation service for Phase 7 CRM.

Deterministic rules first, LLM optional for phrasing.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.crm import Application, Recommendation, FollowUp, FollowUpStatus
from app.db.models.crm import ActivityEventType, ActorType
from app.services.crm.timeline_service import TimelineService


class RecommendationService:
    """Career Copilot recommendation service.

    Deterministic rules first. LLM is optional and failure-tolerant.
    """

    @staticmethod
    def generate_for_application(db: Session, application: Application) -> List[Recommendation]:
        """Generate recommendations for a single application.

        Always returns a list (possibly empty) of Recommendation objects.
        Never raises.
        """
        recommendations: List[Recommendation] = []
        recommendations.extend(
            RecommendationService._stale_application_check(db, application)
        )
        recommendations.extend(
            RecommendationService._deadline_check(db, application)
        )
        recommendations.extend(
            RecommendationService._missing_artifacts_check(db, application)
        )
        recommendations.extend(
            RecommendationService._resume_mismatch_check(db, application)
        )
        return recommendations

    @staticmethod
    def _stale_application_check(db: Session, application: Application) -> List[Recommendation]:
        """Detect applications with no recent activity."""
        recommendations = []
        if not application.last_activity_at:
            return recommendations
        stale_days = 14
        if application.status in [
            ApplicationStatus.INTERVIEW,
            ApplicationStatus.TECHNICAL_INTERVIEW,
            ApplicationStatus.FINAL_INTERVIEW,
        ]:
            stale_days = 7
        if datetime.now(timezone.utc) - application.last_activity_at > timedelta(days=stale_days):
            recommendations.append(Recommendation(
                user_id=application.user_id,
                application_id=application.id,
                recommendation_type="stale_application",
                severity="warning",
                title=f"No activity for {stale_days}+ days",
                explanation=f"Application for {application.job_title_snapshot or 'job'} has had no activity for {stale_days} days.",
                evidence=[f"last_activity_at={application.last_activity_at.isoformat()}"],
                suggested_action="Consider sending a follow-up or updating the status.",
                confidence=1.0,
                provider="rule",
                model=None,
                prompt_version=None,
            ))
        return recommendations

    @staticmethod
    def _deadline_check(db: Session, application: Application) -> List[Recommendation]:
        """Detect approaching or missed deadlines."""
        recommendations = []
        if not application.deadline_at:
            return recommendations
        now = datetime.now(timezone.utc)
        if application.deadline_at < now:
            recommendations.append(Recommendation(
                user_id=application.user_id,
                application_id=application.id,
                recommendation_type="deadline_passed",
                severity="error",
                title="Application deadline passed",
                explanation=f"Deadline for {application.job_title_snapshot or 'job'} was {application.deadline_at.isoformat()}.",
                evidence=[f"deadline_at={application.deadline_at.isoformat()}"],
                suggested_action="Withdraw or mark as expired.",
                confidence=1.0,
                provider="rule",
                model=None,
                prompt_version=None,
            ))
        elif application.deadline_at - now < timedelta(days=3):
            recommendations.append(Recommendation(
                user_id=application.user_id,
                application_id=application.id,
                recommendation_type="deadline_approaching",
                severity="warning",
                title="Deadline approaching",
                explanation=f"Deadline for {application.job_title_snapshot or 'job'} is in less than 3 days.",
                evidence=[f"deadline_at={application.deadline_at.isoformat()}"],
                suggested_action="Complete and submit application soon.",
                confidence=1.0,
                provider="rule",
                model=None,
                prompt_version=None,
            ))
        return recommendations

    @staticmethod
    def _missing_artifacts_check(db: Session, application: Application) -> List[Recommendation]:
        """Detect missing required artifacts."""
        recommendations = []
        if application.status == ApplicationStatus.APPLIED and not application.resume_version_id:
            recommendations.append(Recommendation(
                user_id=application.user_id,
                application_id=application.id,
                recommendation_type="missing_resume",
                severity="warning",
                title="No resume attached",
                explanation="Application is marked as applied but no resume version is linked.",
                evidence=["resume_version_id is null"],
                suggested_action="Attach a resume version to preserve the submitted snapshot.",
                confidence=1.0,
                provider="rule",
                model=None,
                prompt_version=None,
            ))
        return recommendations

    @staticmethod
    def _resume_mismatch_check(db: Session, application: Application) -> List[Recommendation]:
        """Detect resume mismatch with job match score."""
        recommendations = []
        if application.match_snapshot and application.status in [
            ApplicationStatus.APPLIED,
            ApplicationStatus.SCREENING,
            ApplicationStatus.INTERVIEW,
        ]:
            score = application.match_snapshot.get("overall_score")
            if score is not None and score < 50:
                recommendations.append(Recommendation(
                    user_id=application.user_id,
                    application_id=application.id,
                    recommendation_type="low_match_score",
                    severity="info",
                    title="Low match score at application time",
                    explanation=f"Match score was {score}/100 when applied. Consider tailoring a stronger resume.",
                    evidence=[f"match_snapshot.overall_score={score}"],
                    suggested_action="Use the tailoring engine to improve alignment.",
                    confidence=0.8,
                    provider="rule",
                    model=None,
                    prompt_version=None,
                ))
        return recommendations

    @staticmethod
    def generate_and_persist(db: Session, application: Application) -> List[Recommendation]:
        """Generate recommendations and persist them, dismissing old ones."""
        db.query(Recommendation).filter(
            Recommendation.application_id == application.id,
            Recommendation.dismissed == False,  # noqa: E712
        ).update({"dismissed": True, "dismissed_at": datetime.now(timezone.utc)})
        new_recs = RecommendationService.generate_for_application(db, application)
        for rec in new_recs:
            rec.generated_at = datetime.now(timezone.utc)
            db.add(rec)
            TimelineService.add_event(
                db,
                application_id=application.id,
                user_id=application.user_id,
                event_type=ActivityEventType.AI_RECOMMENDATION_GENERATED,
                title=f"Recommendation: {rec.title}",
                actor_type=ActorType.AI,
                related_entity_type="recommendation",
                related_entity_id=rec.id,
            )
        db.flush()
        return new_recs

    @staticmethod
    def get_pending(db: Session, user_id: UUID, application_id: Optional[UUID] = None) -> List[Recommendation]:
        """Get pending recommendations for a user."""
        stmt = select(Recommendation).where(
            Recommendation.user_id == user_id,
            Recommendation.dismissed == False,  # noqa: E712
        )
        if application_id:
            stmt = stmt.where(Recommendation.application_id == application_id)
        stmt = stmt.order_by(Recommendation.generated_at.desc())
        return list(db.execute(stmt).scalars().all())
