"""Phase 7 CRM API endpoint tests."""

import pytest
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.crm import Application, ApplicationStatus, ApplicationPriority, FollowUp, Interview, Offer, Recommendation
from app.db.models.user import User
from app.services.crm.application_service import ApplicationService
from app.core.security import get_password_hash


@pytest.fixture
def test_user_obj(db_session: Session) -> User:
    user = User(
        email="crm_api_full@example.com",
        full_name="CRM API User",
        password_hash=get_password_hash("StrongPass123"),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestCRMAPI:
    def test_list_applications_empty(self, client: TestClient, auth_helpers):
        headers = auth_helpers.register_and_login(client, "crm_list@example.com", "List User")
        response = client.get("/api/v1/applications", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    def test_create_and_get_application(self, client: TestClient, auth_helpers, db_session: Session, test_user_obj: User):
        headers = auth_helpers.register_and_login(client, "crm_create@example.com", "Create User")
        create_resp = client.post("/api/v1/applications", json={"name": "API App"}, headers=headers)
        assert create_resp.status_code == 201
        app_id = create_resp.json()["id"]
        get_resp = client.get(f"/api/v1/applications/{app_id}", headers=headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["name"] == "API App"

    def test_patch_application(self, client: TestClient, auth_helpers, db_session: Session, test_user_obj: User):
        token = auth_helpers.login(client, test_user_obj.email)
        headers = auth_helpers.token_headers(token)
        app = ApplicationService.create(db_session, user_id=test_user_obj.id, name="Patch App")
        response = client.patch(
            f"/api/v1/applications/{app.id}",
            json={"notes": "Updated via API"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["notes"] == "Updated via API"

    def test_delete_application(self, client: TestClient, auth_helpers, db_session: Session, test_user_obj: User):
        token = auth_helpers.login(client, test_user_obj.email)
        headers = auth_helpers.token_headers(token)
        app = ApplicationService.create(db_session, user_id=test_user_obj.id, name="Delete App")
        response = client.delete(f"/api/v1/applications/{app.id}", headers=headers)
        assert response.status_code == 204

    def test_state_machine_info(self, client: TestClient, auth_helpers):
        headers = auth_helpers.register_and_login(client, "crm_sm@example.com", "SM User")
        response = client.get("/api/v1/applications/state-machine?status=saved", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["current_status"] == "saved"
        assert len(data["allowed_transitions"]) > 0

    def test_application_transition(self, client: TestClient, auth_helpers, db_session: Session, test_user_obj: User):
        token = auth_helpers.login(client, test_user_obj.email)
        headers = auth_helpers.token_headers(token)
        app = ApplicationService.create(db_session, user_id=test_user_obj.id, name="Trans App")
        response = client.post(
            f"/api/v1/applications/{app.id}/transitions",
            json={"to_status": "applied", "reason": "Submitting now"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["to_status"] == "applied"

    def test_invalid_transition_returns_409(self, client: TestClient, auth_helpers, db_session: Session, test_user_obj: User):
        token = auth_helpers.login(client, test_user_obj.email)
        headers = auth_helpers.token_headers(token)
        app = ApplicationService.create(db_session, user_id=test_user_obj.id, name="Invalid Trans App")
        response = client.post(
            f"/api/v1/applications/{app.id}/transitions",
            json={"to_status": "rejected"},
            headers=headers,
        )
        assert response.status_code == 409

    def test_dashboard(self, client: TestClient, auth_helpers):
        headers = auth_helpers.register_and_login(client, "crm_dash@example.com", "Dash User")
        response = client.get("/api/v1/crm/dashboard", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "active" in data

    def test_pipeline(self, client: TestClient, auth_helpers):
        headers = auth_helpers.register_and_login(client, "crm_pipe@example.com", "Pipe User")
        response = client.get("/api/v1/crm/pipeline", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "stages" in data

    def test_analytics(self, client: TestClient, auth_helpers):
        headers = auth_helpers.register_and_login(client, "crm_analytics@example.com", "Analytics User")
        response = client.get("/api/v1/crm/analytics", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "stages" in data

    def test_companies_crud(self, client: TestClient, auth_helpers):
        headers = auth_helpers.register_and_login(client, "crm_company@example.com", "Company User")
        create_resp = client.post("/api/v1/companies", json={"name": "TestCorp Inc."}, headers=headers)
        assert create_resp.status_code == 201
        company_id = create_resp.json()["id"]
        get_resp = client.get(f"/api/v1/companies/{company_id}", headers=headers)
        assert get_resp.status_code == 200
        patch_resp = client.patch(f"/api/v1/companies/{company_id}", json={"industry": "Tech"}, headers=headers)
        assert patch_resp.status_code == 200
        assert patch_resp.json()["industry"] == "Tech"

    def test_contacts_crud(self, client: TestClient, auth_helpers):
        headers = auth_helpers.register_and_login(client, "crm_contact@example.com", "Contact User")
        create_resp = client.post("/api/v1/contacts", json={"name": "Jane Doe"}, headers=headers)
        assert create_resp.status_code == 201
        contact_id = create_resp.json()["id"]
        get_resp = client.get(f"/api/v1/contacts/{contact_id}", headers=headers)
        assert get_resp.status_code == 200
        patch_resp = client.patch(f"/api/v1/contacts/{contact_id}", json={"email": "jane@example.com"}, headers=headers)
        assert patch_resp.status_code == 200
        assert patch_resp.json()["email"] == "jane@example.com"

    def test_follow_ups_crud(self, client: TestClient, auth_helpers):
        headers = auth_helpers.register_and_login(client, "crm_followup@example.com", "FollowUp User")
        create_resp = client.post("/api/v1/applications", json={"name": "FollowUp App"}, headers=headers)
        app_id = create_resp.json()["id"]
        from datetime import datetime, timezone
        create_resp = client.post(
            "/api/v1/follow-ups",
            json={"application_id": app_id, "follow_up_type": "status_check", "title": "Follow up", "due_at": datetime.now(timezone.utc).isoformat()},
            headers=headers,
        )
        assert create_resp.status_code == 201
        follow_up_id = create_resp.json()["id"]
        complete_resp = client.post(f"/api/v1/follow-ups/{follow_up_id}/complete", headers=headers)
        assert complete_resp.status_code == 200

    def test_interviews_crud(self, client: TestClient, auth_helpers):
        headers = auth_helpers.register_and_login(client, "crm_interview@example.com", "Interview User")
        create_resp = client.post("/api/v1/applications", json={"name": "Interview App"}, headers=headers)
        app_id = create_resp.json()["id"]
        from datetime import datetime, timezone
        create_resp = client.post(
            "/api/v1/interviews",
            json={"application_id": app_id, "interview_type": "hr_screen", "scheduled_at": datetime.now(timezone.utc).isoformat()},
            headers=headers,
        )
        assert create_resp.status_code == 201
        interview_id = create_resp.json()["id"]
        get_resp = client.get(f"/api/v1/interviews/{interview_id}", headers=headers)
        assert get_resp.status_code == 200

    def test_offers_crud(self, client: TestClient, auth_helpers):
        headers = auth_helpers.register_and_login(client, "crm_offer@example.com", "Offer User")
        create_resp = client.post("/api/v1/applications", json={"name": "Offer App"}, headers=headers)
        app_id = create_resp.json()["id"]
        create_resp = client.put(
            f"/api/v1/applications/{app_id}/offer",
            json={"base_salary": 100000, "currency": "USD"},
            headers=headers,
        )
        assert create_resp.status_code in (200, 201)
