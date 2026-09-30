"""Dashboard aggregation service for Phase 7 CRM."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db.models.crm import (
    Application,
    ApplicationStatus,
    Interview,
    FollowUp,
    FollowUpStatus,
    Offer,
    Recommendation,
)


class DashboardService:
    """Aggregated CRM dashboard statistics."""

    @staticmethod
    def get_stats(db: Session, user_id: UUID) -> dict:
        """Return aggregated stats for the authenticated user."""
        apps_stmt = select(Application).where(Application.user_id == user_id)
        applications = list(db.execute(apps_stmt).scalars().all())
        total = len(applications)
        counts = {s: 0 for s in ApplicationStatus}
        for app in applications:
            counts[app.status] = counts.get(app.status, 0) + 1
        active = sum(
            counts.get(s, 0)
            for s in [
                ApplicationStatus.SAVED,
                ApplicationStatus.READY_TO_APPLY,
                ApplicationStatus.APPLIED,
                ApplicationStatus.APPLICATION_VIEWED,
                ApplicationStatus.SCREENING,
                ApplicationStatus.INTERVIEW,
                ApplicationStatus.TECHNICAL_INTERVIEW,
                ApplicationStatus.FINAL_INTERVIEW,
                ApplicationStatus.ON_HOLD,
                ApplicationStatus.OFFER,
            ]
        )
        applied_count = counts.get(ApplicationStatus.APPLIED, 0)
        interview_count = counts.get(
            ApplicationStatus.INTERVIEW, 0
        ) + counts.get(ApplicationStatus.TECHNICAL_INTERVIEW, 0) + counts.get(
            ApplicationStatus.FINAL_INTERVIEW, 0
        )
        offer_count = counts.get(ApplicationStatus.OFFER, 0) + counts.get(
            ApplicationStatus.ACCEPTED, 0
        )
        rejected_count = counts.get(ApplicationStatus.REJECTED, 0)
        response_rate = (interview_count / total * 100) if total > 0 else 0.0
        interview_rate = (interview_count / applied_count * 100) if applied_count > 0 else 0.0
        offer_rate = (offer_count / applied_count * 100) if applied_count > 0 else 0.0
        now = datetime.now(timezone.utc)
        upcoming_interviews = db.query(func.count(Interview.id)).filter(
            Interview.user_id == user_id,
            Interview.status == "scheduled",
            Interview.scheduled_at >= now,
        ).scalar() or 0
        pending_follow_ups = db.query(func.count(FollowUp.id)).filter(
            FollowUp.user_id == user_id,
            FollowUp.status == FollowUpStatus.PENDING,
            FollowUp.due_at >= now,
        ).scalar() or 0
        stale_threshold = now - timedelta(days=14)
        stale_applications = db.query(func.count(Application.id)).filter(
            Application.user_id == user_id,
            Application.last_activity_at <= stale_threshold,
            Application.status.in_([
                ApplicationStatus.APPLIED.value,
                ApplicationStatus.SCREENING.value,
                ApplicationStatus.INTERVIEW.value,
                ApplicationStatus.TECHNICAL_INTERVIEW.value,
                ApplicationStatus.FINAL_INTERVIEW.value,
                ApplicationStatus.ON_HOLD.value,
            ]),
        ).scalar() or 0
        return {
            "total": total,
            "active": active,
            "saved": counts.get(ApplicationStatus.SAVED, 0),
            "ready_to_apply": counts.get(ApplicationStatus.READY_TO_APPLY, 0),
            "applied": applied_count,
            "screening": counts.get(ApplicationStatus.SCREENING, 0),
            "interview": interview_count,
            "technical_interview": counts.get(ApplicationStatus.TECHNICAL_INTERVIEW, 0),
            "final_interview": counts.get(ApplicationStatus.FINAL_INTERVIEW, 0),
            "offer": offer_count,
            "accepted": counts.get(ApplicationStatus.ACCEPTED, 0),
            "rejected": rejected_count,
            "withdrawn": counts.get(ApplicationStatus.WITHDRAWN, 0),
            "expired": counts.get(ApplicationStatus.EXPIRED, 0),
            "on_hold": counts.get(ApplicationStatus.ON_HOLD, 0),
            "response_rate": round(response_rate, 1),
            "interview_rate": round(interview_rate, 1),
            "offer_rate": round(offer_rate, 1),
            "upcoming_interviews": upcoming_interviews,
            "pending_follow_ups": pending_follow_ups,
            "stale_applications": stale_applications,
        }

    @staticmethod
    def get_pipeline(db: Session, user_id: UUID) -> List[dict]:
        """Return pipeline stages with counts for kanban board."""
        stages = [
            ApplicationStatus.SAVED,
            ApplicationStatus.READY_TO_APPLY,
            ApplicationStatus.APPLIED,
            ApplicationStatus.SCREENING,
            ApplicationStatus.INTERVIEW,
            ApplicationStatus.TECHNICAL_INTERVIEW,
            ApplicationStatus.FINAL_INTERVIEW,
            ApplicationStatus.OFFER,
        ]
        result = []
        for stage in stages:
            count = db.query(func.count(Application.id)).filter(
                Application.user_id == user_id,
                Application.status == stage,
            ).scalar() or 0
            result.append({
                "status": stage.value,
                "label": stage.value.replace("_", " ").title(),
                "count": count,
            })
        return result

    @staticmethod
    def get_funnel(db: Session, user_id: UUID) -> List[dict]:
        """Return funnel stages with conversion rates."""
        stages = [
            ApplicationStatus.SAVED,
            ApplicationStatus.READY_TO_APPLY,
            ApplicationStatus.APPLIED,
            ApplicationStatus.SCREENING,
            ApplicationStatus.INTERVIEW,
            ApplicationStatus.OFFER,
            ApplicationStatus.ACCEPTED,
        ]
        counts = {}
        for stage in stages:
            counts[stage] = db.query(func.count(Application.id)).filter(
                Application.user_id == user_id,
                Application.status == stage,
            ).scalar() or 0
        applied = counts.get(ApplicationStatus.APPLIED, 0)
        result = []
        for i, stage in enumerate(stages):
            count = counts.get(stage, 0)
            prev_count = counts.get(stages[i - 1], 0) if i > 0 else count
            conversion = (count / prev_count * 100) if prev_count > 0 else 0.0
            result.append({
                "stage": stage.value,
                "count": count,
                "conversion_rate": round(conversion, 1),
            })
        return result
