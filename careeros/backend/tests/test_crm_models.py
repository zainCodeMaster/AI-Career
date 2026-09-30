"""Phase 7 CRM model tests."""

import pytest
from sqlalchemy.orm import Session

from app.db.models.crm import (
    Application,
    ApplicationStatus,
    ApplicationPriority,
    ApplicationSource,
    Company,
    UserCompanyLink,
    Contact,
    Interview,
    FollowUp,
    Offer,
    Rejection,
    Recommendation,
    AutomationState,
    ActivityEventType,
    ActorType,
    ContactRole,
    FollowUpStatus,
    InterviewStatus,
    InterviewOutcome,
    InterviewType,
    OfferStatus,
)
from app.db.models.user import User
from app.core.security import get_password_hash


@pytest.fixture
def test_user_obj(db_session: Session) -> User:
    user = User(
        email="crm_model@example.com",
        full_name="CRM Model User",
        password_hash=get_password_hash("StrongPass123"),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestCompanyModel:
    def test_create_company(self, db_session: Session):
        company = Company(
            name="Tech Corp",
            normalized_name="tech corp",
            canonical_name="Tech Corp",
            website="https://techcorp.com",
            domain="techcorp.com",
            industry="Technology",
            location="Lahore, Pakistan",
            size="100-500",
        )
        db_session.add(company)
        db_session.commit()
        assert company.id is not None
        assert company.normalized_name == "tech corp"
        assert company.domain == "techcorp.com"

    def test_company_unique_domain(self, db_session: Session):
        c1 = Company(name="Corp A", normalized_name="corp a", canonical_name="Corp A", domain="example.com")
        c2 = Company(name="Corp B", normalized_name="corp b", canonical_name="Corp B", domain="example.com")
        db_session.add(c1)
        db_session.add(c2)
        with pytest.raises(Exception):
            db_session.commit()
        db_session.rollback()


class TestApplicationModel:
    def test_create_application(self, db_session: Session, test_user_obj: User):
        app = Application(
            user_id=test_user_obj.id,
            name="My Application",
            status=ApplicationStatus.SAVED,
            priority=ApplicationPriority.MEDIUM,
            source=ApplicationSource.MANUAL,
            automation_state=AutomationState.NOT_ATTEMPTED,
        )
        db_session.add(app)
        db_session.commit()
        assert app.id is not None
        assert app.status == ApplicationStatus.SAVED
        assert app.automation_state == AutomationState.NOT_ATTEMPTED

    def test_application_defaults(self, db_session: Session, test_user_obj: User):
        app = Application(user_id=test_user_obj.id)
        db_session.add(app)
        db_session.commit()
        assert app.status == ApplicationStatus.SAVED
        assert app.priority == ApplicationPriority.MEDIUM
        assert app.source == ApplicationSource.MANUAL
        assert app.automation_state == AutomationState.NOT_ATTEMPTED


class TestContactModel:
    def test_create_contact(self, db_session: Session, test_user_obj: User):
        contact = Contact(
            user_id=test_user_obj.id,
            name="John Doe",
            email="john@example.com",
            title="Recruiter",
        )
        db_session.add(contact)
        db_session.commit()
        assert contact.id is not None
        assert contact.name == "John Doe"


class TestInterviewModel:
    def test_create_interview(self, db_session: Session, test_user_obj: User):
        from datetime import datetime, timezone
        app = Application(user_id=test_user_obj.id, name="Test App")
        db_session.add(app)
        db_session.commit()
        interview = Interview(
            user_id=test_user_obj.id,
            application_id=app.id,
            interview_type=InterviewType.HR_SCREEN,
            scheduled_at=datetime.now(timezone.utc),
            status=InterviewStatus.SCHEDULED,
            outcome=InterviewOutcome.PENDING,
        )
        db_session.add(interview)
        db_session.commit()
        assert interview.id is not None
        assert interview.interview_type == InterviewType.HR_SCREEN


class TestFollowUpModel:
    def test_create_follow_up(self, db_session: Session, test_user_obj: User):
        from datetime import datetime, timezone
        app = Application(user_id=test_user_obj.id, name="Test App")
        db_session.add(app)
        db_session.commit()
        follow_up = FollowUp(
            user_id=test_user_obj.id,
            application_id=app.id,
            follow_up_type="status_check",
            title="Follow up",
            due_at=datetime.now(timezone.utc),
            status=FollowUpStatus.PENDING,
            created_by=ActorType.MANUAL,
        )
        db_session.add(follow_up)
        db_session.commit()
        assert follow_up.id is not None
        assert follow_up.status == FollowUpStatus.PENDING


class TestOfferModel:
    def test_create_offer(self, db_session: Session, test_user_obj: User):
        app = Application(user_id=test_user_obj.id, name="Test App")
        db_session.add(app)
        db_session.commit()
        offer = Offer(
            user_id=test_user_obj.id,
            application_id=app.id,
            base_salary=100000,
            currency="USD",
            status=OfferStatus.RECEIVED,
        )
        db_session.add(offer)
        db_session.commit()
        assert offer.id is not None
        assert offer.base_salary == 100000


class TestRejectionModel:
    def test_create_rejection(self, db_session: Session, test_user_obj: User):
        app = Application(user_id=test_user_obj.id, name="Test App")
        db_session.add(app)
        db_session.commit()
        rejection = Rejection(
            user_id=test_user_obj.id,
            application_id=app.id,
            stage="screening",
            reason="Not qualified",
        )
        db_session.add(rejection)
        db_session.commit()
        assert rejection.id is not None
        assert rejection.stage == "screening"


class TestRecommendationModel:
    def test_create_recommendation(self, db_session: Session, test_user_obj: User):
        app = Application(user_id=test_user_obj.id, name="Test App")
        db_session.add(app)
        db_session.commit()
        rec = Recommendation(
            user_id=test_user_obj.id,
            application_id=app.id,
            recommendation_type="stale_application",
            severity="warning",
            title="Stale application",
            confidence=0.9,
            provider="rule",
        )
        db_session.add(rec)
        db_session.commit()
        assert rec.id is not None
        assert rec.dismissed is False
