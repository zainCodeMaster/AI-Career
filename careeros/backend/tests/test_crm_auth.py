"""Phase 7 CRM authentication and isolation tests."""

import pytest
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.crm import Application, Company, Contact, Interview, FollowUp, Offer, Rejection, ApplicationActivity
from app.db.models.user import User
from app.services.crm.application_service import ApplicationService
from app.core.security import get_password_hash


@pytest.fixture
def user_a(db_session: Session) -> User:
    user = User(
        email="crm_auth_a@example.com",
        full_name="User A",
        password_hash=get_password_hash("StrongPass123"),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def user_b(db_session: Session) -> User:
    user = User(
        email="crm_auth_b@example.com",
        full_name="User B",
        password_hash=get_password_hash("StrongPass123"),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth_headers(client: TestClient, email: str, password: str = "StrongPass123") -> dict:
    client.post("/api/v1/auth/register", json={"email": email, "password": password, "full_name": email})
    token = client.post("/api/v1/auth/login", json={"email": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestCRMIsolation:
    def test_user_cannot_attach_contact_to_another_users_company(
        self, client: TestClient, db_session: Session, user_a: User, user_b: User
    ):
        company = Company(name="Private Company", normalized_name="private-company")
        db_session.add(company)
        db_session.flush()
        from app.db.models.crm import UserCompanyLink
        db_session.add(UserCompanyLink(user_id=user_a.id, company_id=company.id))
        db_session.commit()
        headers_b = _auth_headers(client, "crm_company_iso_b@example.com")
        response = client.post(
            "/api/v1/contacts",
            json={"name": "Unauthorized Contact", "company_id": str(company.id)},
            headers=headers_b,
        )
        assert response.status_code == 404

    def test_user_b_cannot_read_user_a_application(self, client: TestClient, db_session: Session, user_a: User, user_b: User):
        app = ApplicationService.create(db_session, user_id=user_a.id, name="User A App")
        headers_b = _auth_headers(client, "crm_iso_b@example.com")
        response = client.get(f"/api/v1/applications/{app.id}", headers=headers_b)
        assert response.status_code == 404

    def test_user_b_cannot_update_user_a_application(self, client: TestClient, db_session: Session, user_a: User, user_b: User):
        app = ApplicationService.create(db_session, user_id=user_a.id, name="User A App")
        headers_b = _auth_headers(client, "crm_iso_b2@example.com")
        response = client.patch(f"/api/v1/applications/{app.id}", json={"notes": "hacked"}, headers=headers_b)
        assert response.status_code == 404

    def test_user_b_cannot_delete_user_a_application(self, client: TestClient, db_session: Session, user_a: User, user_b: User):
        app = ApplicationService.create(db_session, user_id=user_a.id, name="User A App")
        headers_b = _auth_headers(client, "crm_iso_b3@example.com")
        response = client.delete(f"/api/v1/applications/{app.id}", headers=headers_b)
        assert response.status_code == 404

    def test_user_b_cannot_transition_user_a_application(self, client: TestClient, db_session: Session, user_a: User, user_b: User):
        app = ApplicationService.create(db_session, user_id=user_a.id, name="User A App")
        headers_b = _auth_headers(client, "crm_iso_b4@example.com")
        response = client.post(
            f"/api/v1/applications/{app.id}/transitions",
            json={"to_status": "applied"},
            headers=headers_b,
        )
        assert response.status_code == 404

    def test_user_b_cannot_read_user_a_activities(self, client: TestClient, db_session: Session, user_a: User, user_b: User):
        app = ApplicationService.create(db_session, user_id=user_a.id, name="User A App")
        headers_b = _auth_headers(client, "crm_iso_b5@example.com")
        response = client.get(f"/api/v1/applications/{app.id}/timeline", headers=headers_b)
        assert response.status_code == 404

    def test_unauthorized_access_returns_401(self, client: TestClient):
        response = client.get("/api/v1/applications")
        assert response.status_code == 401
