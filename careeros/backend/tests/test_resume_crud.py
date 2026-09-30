"""Phase 6 — Resume CRUD tests.

Tests for:
- Resume creation
- Resume listing (with pagination and filters)
- Resume retrieval by ID
- Resume update
- Resume archive (soft delete)
- Resume delete (hard delete)
- Resume versioning
"""

import pytest
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.resume import Resume, ResumeSection
from app.db.models.user import User
from app.core.security import get_password_hash
from app.services.resume.resume_service import ResumeService
from app.services.resume.section_service import ResumeSectionService
from app.schemas.resume import (
    ResumeCreate,
    ResumeUpdate,
    ResumeTypeResponse,
    ResumeStatusResponse,
)


def _register(client: TestClient, email: str, full_name: str = "Test User") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123", "full_name": full_name},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _login(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPass123"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _register_and_login(client: TestClient, email: str, full_name: str = "Test User") -> dict[str, str]:
    _register(client, email, full_name)
    token = _login(client, email)
    return _headers(token)


def _create_test_resume(db_session: Session, user_id: UUID, name: str = "Test Resume") -> Resume:
    """Helper to create a resume directly in the database."""
    resume = Resume(
        user_id=user_id,
        name=name,
        resume_type="base",
        status="draft",
        structured_data={"summary": "Test summary"},
        version_number=1,
    )
    db_session.add(resume)
    db_session.commit()
    return resume


@pytest.fixture
def test_user_obj(db_session):
    """Create a test user directly in DB."""
    user = User(
        email="crud_test@example.com",
        full_name="CRUD Test User",
        password_hash=get_password_hash("StrongPass123"),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


# ---------------------------------------------------------------------------
# Resume CRUD Tests
# ---------------------------------------------------------------------------


class TestResumeCRUD:
    """Tests for ResumeService CRUD operations."""

    def test_create_resume(self, db_session, test_user_obj):
        """Test creating a resume."""
        resume_data = ResumeCreate(
            name="My Resume",
            resume_type=ResumeTypeResponse.BASE,
            status=ResumeStatusResponse.DRAFT,
        )

        resume = ResumeService.create(db_session, test_user_obj.id, resume_data)

        assert resume.name == "My Resume"
        assert resume.resume_type == "base"
        assert resume.status == "draft"
        assert resume.user_id == test_user_obj.id
        assert resume.version_number == 1

    def test_create_tailored_resume_requires_target_job(self, db_session, test_user_obj):
        """Test that tailored resumes require a target_job_id."""
        resume_data = ResumeCreate(
            name="Tailored Resume",
            resume_type=ResumeTypeResponse.TAILORED,
        )

        with pytest.raises(ValueError, match="target_job_id is required for tailored resumes"):
            ResumeService.create(db_session, test_user_obj.id, resume_data)

    def test_get_resume(self, db_session, test_user_obj):
        """Test retrieving a resume by ID."""
        resume = _create_test_resume(db_session, test_user_obj.id, "Get Test")

        fetched = ResumeService.get(db_session, test_user_obj.id, resume.id)
        assert fetched is not None
        assert fetched.name == "Get Test"

    def test_get_resume_nonexistent(self, db_session, test_user_obj):
        """Test getting a non-existent resume returns None."""
        result = ResumeService.get(db_session, test_user_obj.id, str(uuid4()))
        assert result is None

    def test_get_resume_other_user(self, db_session, test_user_obj):
        """Test that a user cannot retrieve another user's resume."""
        other_user = User(
            email="other@example.com",
            full_name="Other User",
            password_hash=get_password_hash("StrongPass123"),
            is_active=True,
        )
        db_session.add(other_user)
        db_session.commit()

        resume = Resume(
            user_id=other_user.id,
            name="Other's Resume",
        )
        db_session.add(resume)
        db_session.commit()

        # Should not be found by other user
        result = ResumeService.get(db_session, test_user_obj.id, resume.id)
        assert result is None

    def test_list_resumes(self, db_session, test_user_obj):
        """Test listing resumes with pagination."""
        for i in range(5):
            _create_test_resume(db_session, test_user_obj.id, f"Resume {i}")

        items, total = ResumeService.list(db_session, test_user_obj.id, page=1, page_size=10)
        assert len(items) == 5
        assert total == 5

    def test_list_resumes_pagination(self, db_session, test_user_obj):
        """Test pagination of resume list."""
        for i in range(15):
            _create_test_resume(db_session, test_user_obj.id, f"Page Resume {i}")

        items, total = ResumeService.list(db_session, test_user_obj.id, page=2, page_size=10)
        assert len(items) == 5
        assert total == 15

    def test_list_resumes_filter_by_status(self, db_session, test_user_obj):
        """Test filtering resumes by status."""
        r1 = Resume(user_id=test_user_obj.id, name="Draft", status="draft")
        r2 = Resume(user_id=test_user_obj.id, name="Ready", status="ready")
        r3 = Resume(user_id=test_user_obj.id, name="Archived", status="archived")
        db_session.add_all([r1, r2, r3])
        db_session.commit()

        items, total = ResumeService.list(db_session, test_user_obj.id, page=1, page_size=100, status="ready")
        assert total == 1
        assert items[0].name == "Ready"

    def test_list_resumes_filter_by_type(self, db_session, test_user_obj):
        """Test filtering resumes by type."""
        r1 = Resume(user_id=test_user_obj.id, name="Base", resume_type="base")
        r2 = Resume(user_id=test_user_obj.id, name="Tailored", resume_type="tailored")
        db_session.add_all([r1, r2])
        db_session.commit()

        items, total = ResumeService.list(db_session, test_user_obj.id, page=1, page_size=100, resume_type="base")
        assert total == 1
        assert items[0].name == "Base"

    def test_list_resumes_user_isolation(self, db_session, test_user_obj):
        """Test that users only see their own resumes."""
        other_user = User(
            email="list_isolation@example.com",
            full_name="Other User",
            password_hash=get_password_hash("StrongPass123"),
            is_active=True,
        )
        db_session.add(other_user)
        db_session.commit()

        # Create resumes for both users
        _create_test_resume(db_session, test_user_obj.id, "My Resume")
        Resume(user_id=other_user.id, name="Other's Resume")
        db_session.commit()

        items, total = ResumeService.list(db_session, test_user_obj.id, page=1, page_size=100)
        assert total == 1
        assert items[0].name == "My Resume"

    def test_update_resume(self, db_session, test_user_obj):
        """Test updating a resume."""
        resume = _create_test_resume(db_session, test_user_obj.id, "Original Name")

        resume_data = ResumeUpdate(name="Updated Name", status=ResumeStatusResponse.READY)
        updated = ResumeService.update(db_session, test_user_obj.id, resume.id, resume_data)

        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.status == "ready"

    def test_update_resume_nonexistent(self, db_session, test_user_obj):
        """Test updating a non-existent resume."""
        resume_data = ResumeUpdate(name="Updated")
        result = ResumeService.update(db_session, test_user_obj.id, str(uuid4()), resume_data)
        assert result is None

    def test_archive_resume(self, db_session, test_user_obj):
        """Test archiving a resume."""
        resume = _create_test_resume(db_session, test_user_obj.id, "To Archive")

        result = ResumeService.archive(db_session, test_user_obj.id, resume.id)
        assert result is True

        fetched = ResumeService.get(db_session, test_user_obj.id, resume.id)
        assert fetched.status == "archived"

    def test_delete_resume(self, db_session, test_user_obj):
        """Test deleting a resume."""
        resume = _create_test_resume(db_session, test_user_obj.id, "To Delete")

        result = ResumeService.delete(db_session, test_user_obj.id, resume.id)
        assert result is True

        fetched = ResumeService.get(db_session, test_user_obj.id, resume.id)
        assert fetched is None

    def test_get_versions(self, db_session, test_user_obj):
        """Test getting all versions of a resume."""
        base = Resume(
            user_id=test_user_obj.id,
            name="Base Resume",
            version_number=1,
        )
        db_session.add(base)
        db_session.flush()

        v2 = Resume(
            user_id=test_user_obj.id,
            name="Base Resume",
            version_number=2,
            parent_resume_id=base.id,
        )
        db_session.add(v2)
        db_session.commit()

        versions = ResumeService.get_versions(db_session, test_user_obj.id, base.id)
        assert len(versions) == 2
        assert versions[0].version_number == 1
        assert versions[1].version_number == 2


# ---------------------------------------------------------------------------
# Section Service Tests
# ---------------------------------------------------------------------------


class TestResumeSectionService:
    """Tests for ResumeSectionService."""

    def test_add_section(self, db_session, test_user_obj):
        """Test adding a section to a resume."""
        resume = _create_test_resume(db_session, test_user_obj.id)

        section = ResumeSectionService.add_section(
            db_session, test_user_obj.id, resume.id,
            section_type="skills",
            content="Python, Django",
            section_title="Technical Skills",
            display_order=1,
        )

        assert section.section_type == "skills"
        assert section.content == "Python, Django"
        assert section.section_title == "Technical Skills"
        assert section.display_order == 1

    def test_get_sections(self, db_session, test_user_obj):
        """Test getting all sections of a resume."""
        resume = _create_test_resume(db_session, test_user_obj.id)

        ResumeSectionService.add_section(
            db_session, test_user_obj.id, resume.id,
            section_type="summary", content="Summary", display_order=0,
        )
        ResumeSectionService.add_section(
            db_session, test_user_obj.id, resume.id,
            section_type="skills", content="Skills", display_order=0,
        )

        sections = ResumeSectionService.get_sections(db_session, test_user_obj.id, resume.id)
        assert len(sections) == 2
        assert sections[0].section_type == "summary"
        assert sections[1].section_type == "skills"

    def test_update_section(self, db_session, test_user_obj):
        """Test updating a section."""
        resume = _create_test_resume(db_session, test_user_obj.id)

        section = ResumeSectionService.add_section(
            db_session, test_user_obj.id, resume.id,
            section_type="skills", content="Old content", display_order=0,
        )

        updated = ResumeSectionService.update_section(
            db_session, test_user_obj.id, section.id,
            content="New content", section_title="Updated Title",
        )

        assert updated.content == "New content"
        assert updated.section_title == "Updated Title"

    def test_delete_section(self, db_session, test_user_obj):
        """Test deleting a section."""
        resume = _create_test_resume(db_session, test_user_obj.id)

        section = ResumeSectionService.add_section(
            db_session, test_user_obj.id, resume.id,
            section_type="skills", content="Python", display_order=0,
        )

        result = ResumeSectionService.delete_section(db_session, test_user_obj.id, section.id)
        assert result is True

        sections = ResumeSectionService.get_sections(db_session, test_user_obj.id, resume.id)
        assert len(sections) == 0


# ---------------------------------------------------------------------------
# API Endpoint Tests
# ---------------------------------------------------------------------------


class TestResumeAPI:
    """Tests for resume API endpoints."""

    def test_create_resume_api(self, client):
        """Test creating a resume via API."""
        headers = _register_and_login(client, "api_create@example.com")

        response = client.post(
            "/api/v1/resumes",
            json={
                "name": "API Resume",
                "resume_type": "base",
                "status": "draft",
            },
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "API Resume"
        assert data["resume_type"] == "base"

    def test_list_resumes_api(self, client):
        """Test listing resumes via API."""
        headers = _register_and_login(client, "api_list@example.com")

        # Create two resumes
        for name in ["Resume A", "Resume B"]:
            client.post(
                "/api/v1/resumes",
                json={"name": name, "resume_type": "base"},
                headers=headers,
            )

        response = client.get("/api/v1/resumes", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_get_resume_api(self, client):
        """Test getting a resume via API."""
        headers = _register_and_login(client, "api_get@example.com")

        # Create a resume
        create_resp = client.post(
            "/api/v1/resumes",
            json={"name": "Get Resume", "resume_type": "base"},
            headers=headers,
        )
        resume_id = create_resp.json()["id"]

        # Get it
        response = client.get(f"/api/v1/resumes/{resume_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Get Resume"

    def test_get_resume_not_found_api(self, client):
        """Test getting a non-existent resume."""
        headers = _register_and_login(client, "api_notfound@example.com")

        response = client.get(f"/api/v1/resumes/{uuid4()}", headers=headers)
        assert response.status_code == 404

    def test_update_resume_api(self, client):
        """Test updating a resume via API."""
        headers = _register_and_login(client, "api_update@example.com")

        # Create
        create_resp = client.post(
            "/api/v1/resumes",
            json={"name": "Original", "resume_type": "base"},
            headers=headers,
        )
        resume_id = create_resp.json()["id"]

        # Update
        response = client.put(
            f"/api/v1/resumes/{resume_id}",
            json={"name": "Updated", "status": "ready"},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated"
        assert data["status"] == "ready"

    def test_delete_resume_api(self, client):
        """Test deleting a resume via API."""
        headers = _register_and_login(client, "api_delete@example.com")

        # Create
        create_resp = client.post(
            "/api/v1/resumes",
            json={"name": "To Delete", "resume_type": "base"},
            headers=headers,
        )
        resume_id = create_resp.json()["id"]

        # Delete
        response = client.delete(f"/api/v1/resumes/{resume_id}", headers=headers)
        assert response.status_code == 204

        # Verify gone
        response = client.get(f"/api/v1/resumes/{resume_id}", headers=headers)
        assert response.status_code == 404

    def test_auth_required(self, client):
        """Test that auth is required for resume endpoints."""
        response = client.get("/api/v1/resumes")
        assert response.status_code in (401, 403)

    def test_list_pagination_api(self, client):
        """Test pagination on resume list API."""
        headers = _register_and_login(client, "api_pagination@example.com")

        # Create 5 resumes
        for i in range(5):
            client.post(
                "/api/v1/resumes",
                json={"name": f"Resume {i}", "resume_type": "base"},
                headers=headers,
            )

        # Get page 1 with size 2
        response = client.get("/api/v1/resumes?page=2&page_size=2", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert data["page"] == 2
        assert data["page_size"] == 2
        assert len(data["items"]) == 2
        assert data["has_next"] is True
        assert data["has_prev"] is True
