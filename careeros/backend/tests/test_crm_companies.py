"""Phase 7 CRM company tests."""

import pytest
from sqlalchemy.orm import Session

from app.db.models.crm import Company, UserCompanyLink
from app.db.models.user import User
from app.services.crm.company_service import CompanyService
from app.core.security import get_password_hash


@pytest.fixture
def test_user_obj(db_session: Session) -> User:
    user = User(
        email="crm_company@example.com",
        full_name="Company User",
        password_hash=get_password_hash("StrongPass123"),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestCompanyService:
    def test_get_or_create_new(self, db_session: Session):
        company = CompanyService.get_or_create(
            db_session,
            "TechCorp",
            website="https://techcorp.com",
            industry="Software",
            location="Lahore",
            size="51-200",
            description="A technology company",
            logo_url="https://techcorp.com/logo.png",
        )
        assert company.id is not None
        assert company.normalized_name == "techcorp"
        assert company.industry == "Software"
        assert company.location == "Lahore"
        assert company.size == "51-200"
        assert company.description == "A technology company"
        assert company.logo_url == "https://techcorp.com/logo.png"

    def test_get_or_create_existing_by_name(self, db_session: Session):
        c1 = CompanyService.get_or_create(db_session, "TechCorp")
        c2 = CompanyService.get_or_create(db_session, "TechCorp")
        assert c1.id == c2.id

    def test_get_or_create_existing_by_domain(self, db_session: Session):
        c1 = CompanyService.get_or_create(db_session, "TechCorp", website="https://techcorp.com")
        c2 = CompanyService.get_or_create(db_session, "Other Name", website="https://techcorp.com")
        assert c1.id == c2.id

    def test_normalization_strips_suffixes(self, db_session: Session):
        company = CompanyService.get_or_create(db_session, "TechCorp Inc.", website="https://techcorp.com")
        assert "inc" not in company.normalized_name

    def test_user_link(self, db_session: Session, test_user_obj: User):
        company = CompanyService.get_or_create(db_session, "TechCorp")
        link = CompanyService.create_or_update_user_link(
            db_session, test_user_obj.id, company.id, notes="Great place", is_favorite=True
        )
        assert link.user_id == test_user_obj.id
        assert link.company_id == company.id
        assert link.is_favorite is True

    def test_get_user_companies(self, db_session: Session, test_user_obj: User):
        company = CompanyService.get_or_create(db_session, "TechCorp")
        CompanyService.create_or_update_user_link(db_session, test_user_obj.id, company.id)
        companies = CompanyService.get_user_companies(db_session, test_user_obj.id)
        assert len(companies) >= 1
