"""Phase 6 — Resume authentication and multi-user isolation tests.

Tests for:
- Authentication required for all resume endpoints
- User A cannot access User B's resumes
- User A cannot update User B's resumes
- User A cannot delete User B's resumes
- User A cannot tailor User B's resumes
"""

import pytest
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.resume import Resume
from app.db.models.user import User
from app.core.security import get_password_hash


def _register_and_login(client: TestClient, email: str, full_name: str = "Test User") -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123", "full_name": full_name},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPass123"},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestResumeAuth:
    """Authentication tests for resume endpoints."""

    @pytest.mark.parametrize(
        "method,path,body",
        [
            ("GET", "/api/v1/resumes", None),
            ("GET", "/api/v1/resumes/some-id", None),
            ("POST", "/api/v1/resumes", {"name": "Test", "resume_type": "base"}),
            ("PUT", "/api/v1/resumes/some-id", {"name": "Updated"}),
            ("DELETE", "/api/v1/resumes/some-id", None),
            ("GET", "/api/v1/resumes/some-id/sections", None),
            ("POST", "/api/v1/resumes/some-id/sections", {"section_type": "skills", "content": "Python"}),
            ("GET", "/api/v1/resumes/some-id/versions", None),
            ("POST", "/api/v1/resumes/ats/analyze", {"resume_id": "x", "job_id": "y"}),
            ("POST", "/api/v1/resumes/tailor", {"base_resume_id": "x", "target_job_id": "y"}),
        ],
    )
    def test_auth_required(self, client, method, path, body):
        """All resume endpoints require authentication."""
        kwargs = {"headers": {}} if body else {}
        if body:
            kwargs["json"] = body
        
        response = client.request(method, path, **kwargs)
        assert response.status_code in (401, 403), f"Expected 401/403 for {method} {path}, got {response.status_code}"


class TestResumeMultiUserIsolation:
    """Multi-user isolation tests for resume endpoints."""

    def _create_user_and_resume(self, db_session: Session, email: str, resume_name: str) -> tuple[User, Resume]:
        """Helper: create user and their resume."""
        user = User(
            email=email,
            full_name=email.split("@")[0],
            password_hash=get_password_hash("StrongPass123"),
            is_active=True,
        )
        db_session.add(user)
        db_session.flush()

        resume = Resume(
            user_id=user.id,
            name=resume_name,
            resume_type="base",
            status="ready",
        )
        db_session.add(resume)
        db_session.commit()

        return user, resume

    def test_user_cannot_get_other_user_resume(self, client, db_session):
        """User A cannot retrieve User B's resume."""
        user_a, resume_b = self._create_user_and_resume(
            db_session, "usera_isolation@example.com", "User B Resume"
        )
        headers = _register_and_login(client, "usera_iso@example.com")

        response = client.get(f"/api/v1/resumes/{resume_b.id}", headers=headers)
        assert response.status_code == 404

    def test_user_cannot_update_other_user_resume(self, client, db_session):
        """User A cannot update User B's resume."""
        _, resume_b = self._create_user_and_resume(
            db_session, "userb_isolation@example.com", "Original"
        )
        headers = _register_and_login(client, "usera_update@example.com")

        response = client.put(
            f"/api/v1/resumes/{resume_b.id}",
            json={"name": "Hacked Name"},
            headers=headers,
        )
        assert response.status_code == 404

    def test_user_cannot_delete_other_user_resume(self, client, db_session):
        """User A cannot delete User B's resume."""
        _, resume_b = self._create_user_and_resume(
            db_session, "userb_delete@example.com", "Do Not Delete"
        )
        headers = _register_and_login(client, "userhdel@example.com")

        response = client.delete(f"/api/v1/resumes/{resume_b.id}", headers=headers)
        assert response.status_code == 404

    def test_user_cannot_list_other_user_resumes(self, client, db_session):
        """User A cannot see User B's resumes in list."""
        self._create_user_and_resume(db_session, "private@example.com", "Private Resume")
        headers = _register_and_login(client, "other@example.com")

        response = client.get("/api/v1/resumes", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    def test_user_cannot_get_other_user_resume_sections(self, client, db_session):
        """User A cannot access User B's resume sections."""
        _, resume_b = self._create_user_and_resume(
            db_session, "sections_isolation@example.com", "Section Resume"
        )
        headers = _register_and_login(client, "sections_other@example.com")

        response = client.get(f"/api/v1/resumes/{resume_b.id}/sections", headers=headers)
        assert response.status_code == 404

    def test_user_cannot_add_section_to_other_resume(self, client, db_session):
        """User A cannot add sections to User B's resume."""
        _, resume_b = self._create_user_and_resume(
            db_session, "section_add@example.com", "Section Add Resume"
        )
        headers = _register_and_login(client, "section_add_other@example.com")

        response = client.post(
            f"/api/v1/resumes/{resume_b.id}/sections",
            json={"section_type": "skills", "content": "Hacked skill"},
            headers=headers,
        )
        assert response.status_code == 403

    def test_user_cannot_get_other_user_resume_versions(self, client, db_session):
        """User A cannot see User B's resume versions."""
        _, resume_b = self._create_user_and_resume(
            db_session, "versions_isolation@example.com", "Version Resume"
        )
        headers = _register_and_login(client, "versions_other@example.com")

        response = client.get(f"/api/v1/resumes/{resume_b.id}/versions", headers=headers)
        assert response.status_code == 404

    def test_user_cannot_tailor_other_user_resume(self, client, db_session):
        """User A cannot tailor User B's resume."""
        _, base_resume = self._create_user_and_resume(
            db_session, "tailor_isolation_base@example.com", "Base Resume"
        )
        headers = _register_and_login(client, "tailor_isolation_other@example.com")

        response = client.post(
            "/api/v1/resumes/tailor",
            json={
                "base_resume_id": str(base_resume.id),
                "target_job_id": "00000000-0000-0000-0000-000000000000",
                "name": "Hacked Tailored",
            },
            headers=headers,
        )
        # Should fail because the base resume doesn't belong to this user
        assert response.status_code in (400, 403, 404)

    def test_user_cannot_analyze_other_user_resume(self, client, db_session):
        """User A cannot run ATS analysis on User B's resume."""
        _, resume_b = self._create_user_and_resume(
            db_session, "ats_isolation@example.com", "ATS Resume"
        )
        
        # Create a job for the analysis
        from app.db.models.jobs import Job
        job = Job(
            title="Test Job",
            company_name="Test Corp",
            description="Test",
            source="test",
            source_job_id="test-ats-1",
            content_hash="abc",
            normalized_hash="def",
        )
        db_session.add(job)
        db_session.commit()

        headers = _register_and_login(client, "ats_iso_other@example.com")

        response = client.post(
            "/api/v1/resumes/ats/analyze",
            json={"resume_id": str(resume_b.id), "job_id": str(job.id)},
            headers=headers,
        )
        assert response.status_code == 404
