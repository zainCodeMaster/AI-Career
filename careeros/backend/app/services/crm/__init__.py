"""Phase 7 CRM services."""

from app.services.crm.state_machine import ApplicationStateMachine
from app.services.crm.company_service import CompanyService
from app.services.crm.application_service import ApplicationService
from app.services.crm.timeline_service import TimelineService
from app.services.crm.followup_service import FollowUpService
from app.services.crm.interview_service import InterviewService
from app.services.crm.offer_service import OfferService, RejectionService
from app.services.crm.dashboard import DashboardService
from app.services.crm.recommendations import RecommendationService

__all__ = [
    "ApplicationStateMachine",
    "CompanyService",
    "ApplicationService",
    "TimelineService",
    "FollowUpService",
    "InterviewService",
    "OfferService",
    "RejectionService",
    "DashboardService",
    "RecommendationService",
]
