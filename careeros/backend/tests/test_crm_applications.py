"""Phase 7 CRM application CRUD and isolation tests."""

import pytest
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.crm import Application, ApplicationStatus
from app.db.models.user import User
from app.services.crm.application_service import ApplicationService
from app.core.security import get_password_hash


@pytest.fixture
def test_user_obj(db_session: Session) -> User:
    user = User(
        email="crm_app@example.com",
        full_name="App User",
        password_hash=get_password_hash("StrongPass123"),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def other_user_obj(db_session: Session) -> User:
    user = User(
        email="crm_app_other@example.com",
        full_name="Other App User",
        password_hash=get_password_hash("StrongPass123"),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestApplicationService:
    def test_create_application(self, db_session: Session, test_user_obj: User):
        app = ApplicationService.create(
            db_session,
            user_id=test_user_obj.id,
            name="My Application",
            priority="high",
        )
        assert app.id is not None
        assert app.status == ApplicationStatus.SAVED

    def test_get_application(self, db_session: Session, test_user_obj: User):
        app = ApplicationService.create(db_session, user_id=test_user_obj.id, name="Test App")
        fetched = ApplicationService.get(db_session, app.id, test_user_obj.id)
        assert fetched is not None
        assert fetched.id == app.id

    def test_get_other_user_application_returns_none(self, db_session: Session, test_user_obj: User, other_user_obj: User):
        app = ApplicationService.create(db_session, user_id=test_user_obj.id, name="Test App")
        fetched = ApplicationService.get(db_session, app.id, other_user_obj.id)
        assert fetched is None

    def test_list_applications(self, db_session: Session, test_user_obj: User):
        ApplicationService.create(db_session, user_id=test_user_obj.id, name="App 1")
        ApplicationService.create(db_session, user_id=test_user_obj.id, name="App 2")
        items, total = ApplicationService.list(db_session, test_user_obj.id)
        assert total == 2

    def test_update_application(self, db_session: Session, test_user_obj: User):
        app = ApplicationService.create(db_session, user_id=test_user_obj.id, name="Test App")
        updated = ApplicationService.update(db_session, app, notes="Updated notes")
        assert updated.notes == "Updated notes"

    def test_delete_application(self, db_session: Session, test_user_obj: User):
        app = ApplicationService.create(db_session, user_id=test_user_obj.id, name="Test App")
        ApplicationService.delete(db_session, app)
        assert db_session.get(Application, app.id) is None

    def test_transition_success(self, db_session: Session, test_user_obj: User):
        app = ApplicationService.create(db_session, user_id=test_user_obj.id, name="Test App")
        app, error = ApplicationService.transition(db_session, app, "applied", test_user_obj.id, reason="Submitting")
        assert error == ""
        assert app.status == ApplicationStatus.APPLIED
        assert app.applied_at is not None

    def test_transition_failure(self, db_session: Session, test_user_obj: User):
        app = ApplicationService.create(db_session, user_id=test_user_obj.id, name="Test App")
        app, error = ApplicationService.transition(db_session, app, "rejected", test_user_obj.id)
        assert error != ""


class TestApplicationAPI:
    def test_create_application_api(self, client: TestClient, auth_helpers):
        headers = auth_helpers.register_and_login(client, "crm_api@example.com", "CRM API User")
        response = client.post("/api/v1/applications", json={"name": "API Application"}, headers=headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "API Application"
        assert data["status"] == "saved"

    def test_get_application_api(self, client: TestClient, auth_helpers, db_session: Session, test_user_obj: User):
        headers = auth_helpers.register_and_login(client, "crm_api2@example.com", "CRM API User 2")
        app = ApplicationService.create(db_session, user_id=test_user_obj.id, name="Test App")
        response = client.get(f"/api/v1/applications/{app.id}", headers=headers)
        assert response.status_code == 404

    def test_unauthorized_access(self, client: TestClient):
        response = client.get("/api/v1/applications")
        assert response.status_code == 401

    def test_patch_direct_status_change_rejected(self, client: TestClient, auth_helpers, db_session: Session, test_user_obj: User):
        token = auth_helpers.login(client, test_user_obj.email)
        headers = auth_helpers.token_headers(token)
        app = ApplicationService.create(db_session, user_id=test_user_obj.id, name="Patch App")
        response = client.patch(
            f"/api/v1/applications/{app.id}",
            json={"status": "applied"},
            headers=headers,
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["code"] == "INVALID_STATUS_UPDATE"

    def test_patch_non_status_fields_still_work(self, client: TestClient, auth_helpers, db_session: Session, test_user_obj: User):
        token = auth_helpers.login(client, test_user_obj.email)
        headers = auth_helpers.token_headers(token)
        app = ApplicationService.create(db_session, user_id=test_user_obj.id, name="Patch App")
        response = client.patch(
            f"/api/v1/applications/{app.id}",
            json={"notes": "Updated notes"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["notes"] == "Updated notes"

    def test_valid_transition_through_state_machine(self, client: TestClient, auth_helpers, db_session: Session, test_user_obj: User):
        token = auth_helpers.login(client, test_user_obj.email)
        headers = auth_helpers.token_headers(token)
        app = ApplicationService.create(db_session, user_id=test_user_obj.id, name="Trans App")
        response = client.post(
            f"/api/v1/applications/{app.id}/transitions",
            json={"to_status": "applied", "reason": "Submitting now"},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["to_status"] == "applied"
        assert data["from_status"] == "saved"

    def test_invalid_transition_through_state_machine_rejected(self, client: TestClient, auth_helpers, db_session: Session, test_user_obj: User):
        token = auth_helpers.login(client, test_user_obj.email)
        headers = auth_helpers.token_headers(token)
        app = ApplicationService.create(db_session, user_id=test_user_obj.id, name="Invalid Trans App")
        response = client.post(
            f"/api/v1/applications/{app.id}/transitions",
            json={"to_status": "rejected"},
            headers=headers,
        )
        assert response.status_code == 409

    def test_transition_creates_timeline_entry(self, client: TestClient, auth_helpers, db_session: Session, test_user_obj: User):
        token = auth_helpers.login(client, test_user_obj.email)
        headers = auth_helpers.token_headers(token)
        app = ApplicationService.create(db_session, user_id=test_user_obj.id, name="Timeline App")
        client.post(
            f"/api/v1/applications/{app.id}/transitions",
            json={"to_status": "applied", "reason": "Submitting"},
            headers=headers,
        )
        timeline_resp = client.get(f"/api/v1/applications/{app.id}/timeline", headers=headers)
        assert timeline_resp.status_code == 200
        timeline_data = timeline_resp.json()
        assert timeline_data["total"] >= 1
        event_types = [e["event_type"] for e in timeline_data["items"]]
        assert "status_changed" in event_types

    def test_user_isolation_on_patch(self, client: TestClient, auth_helpers, db_session: Session, test_user_obj: User, other_user_obj: User):
        token = auth_helpers.login(client, test_user_obj.email)
        headers = auth_helpers.token_headers(token)
        app = ApplicationService.create(db_session, user_id=test_user_obj.id, name="Isolation App")
        other_token = auth_helpers.login(client, other_user_obj.email)
        other_headers = auth_helpers.token_headers(other_token)
        response = client.patch(
            f"/api/v1/applications/{app.id}",
            json={"notes": "Hacked"},
            headers=other_headers,
        )
        assert response.status_code == 404
