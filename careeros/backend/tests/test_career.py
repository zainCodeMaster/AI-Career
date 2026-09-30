"""Tests for Phase 2 career profile entities: profile, education, experience, skills, certifications."""

import pytest
from fastapi.testclient import TestClient


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


# ---------------------------------------------------------------------------
# Authentication required
# ---------------------------------------------------------------------------


class TestAuthRequired:
    """Phase 2 endpoints must require authentication."""

    @pytest.mark.parametrize(
        "method,path",
        [
            ("GET", "/api/v1/profile"),
            ("POST", "/api/v1/profile"),
            ("PUT", "/api/v1/profile"),
            ("GET", "/api/v1/education"),
            ("POST", "/api/v1/education"),
            ("GET", "/api/v1/experience"),
            ("POST", "/api/v1/experience"),
            ("GET", "/api/v1/skills"),
            ("POST", "/api/v1/skills"),
            ("GET", "/api/v1/certifications"),
            ("POST", "/api/v1/certifications"),
        ],
    )
    def test_endpoints_require_auth(self, client, method, path):
        response = client.request(method, path, json={})
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Career Profile
# ---------------------------------------------------------------------------


class TestCareerProfile:
    """Test career profile CRUD operations."""

    def test_create_profile(self, client):
        headers = _register_and_login(client, "profile_a@example.com")
        response = client.post(
            "/api/v1/profile",
            json={"professional_title": "Software Engineer", "summary": "Experienced developer"},
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["professional_title"] == "Software Engineer"
        assert data["summary"] == "Experienced developer"
        assert "id" in data
        assert "user_id" in data

    def test_get_profile(self, client):
        headers = _register_and_login(client, "profile_b@example.com")
        client.post(
            "/api/v1/profile",
            json={"professional_title": "Data Scientist"},
            headers=headers,
        )
        response = client.get("/api/v1/profile", headers=headers)
        assert response.status_code == 200
        assert response.json()["professional_title"] == "Data Scientist"

    def test_get_profile_not_found(self, client):
        headers = _register_and_login(client, "profile_c@example.com")
        response = client.get("/api/v1/profile", headers=headers)
        assert response.status_code == 404

    def test_update_profile(self, client):
        headers = _register_and_login(client, "profile_d@example.com")
        client.post(
            "/api/v1/profile",
            json={"professional_title": "Junior Developer"},
            headers=headers,
        )
        response = client.put(
            "/api/v1/profile",
            json={"professional_title": "Senior Developer"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["professional_title"] == "Senior Developer"

    def test_update_profile_not_found(self, client):
        headers = _register_and_login(client, "profile_e@example.com")
        response = client.put(
            "/api/v1/profile",
            json={"professional_title": "Senior Developer"},
            headers=headers,
        )
        assert response.status_code == 404

    def test_duplicate_profile_rejected(self, client):
        headers = _register_and_login(client, "profile_f@example.com")
        first = client.post(
            "/api/v1/profile",
            json={"professional_title": "Engineer"},
            headers=headers,
        )
        second = client.post(
            "/api/v1/profile",
            json={"professional_title": "Manager"},
            headers=headers,
        )
        assert first.status_code == 201
        assert second.status_code == 409

    def test_profile_response_excludes_secret_fields(self, client):
        headers = _register_and_login(client, "profile_g@example.com")
        client.post(
            "/api/v1/profile",
            json={"professional_title": "Engineer"},
            headers=headers,
        )
        response = client.get("/api/v1/profile", headers=headers)
        data = response.json()
        assert "password" not in data
        assert "password_hash" not in data

    def test_valid_urls_accepted(self, client):
        """Valid URLs in profile URL fields are accepted."""
        headers = _register_and_login(client, "profile_urls_ok@example.com")
        response = client.post(
            "/api/v1/profile",
            json={
                "professional_title": "Engineer",
                "linkedin_url": "https://linkedin.com/in/test",
                "github_url": "https://github.com/test",
                "portfolio_url": "https://example.com/portfolio",
            },
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["linkedin_url"] == "https://linkedin.com/in/test"
        assert data["github_url"] == "https://github.com/test"
        assert data["portfolio_url"] == "https://example.com/portfolio"

    def test_invalid_url_rejected(self, client):
        """Non-URL strings in URL fields are rejected with 422."""
        headers = _register_and_login(client, "profile_urls_bad@example.com")
        response = client.post(
            "/api/v1/profile",
            json={"linkedin_url": "not-a-valid-url"},
            headers=headers,
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Education
# ---------------------------------------------------------------------------


class TestEducation:
    """Test education CRUD operations."""

    def test_create_education(self, client):
        headers = _register_and_login(client, "edu_a@example.com")
        response = client.post(
            "/api/v1/education",
            json={
                "institution": "MIT",
                "degree": "Bachelor",
                "field_of_study": "Computer Science",
                "start_date": "2016-09-01",
                "end_date": "2020-06-01",
            },
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["institution"] == "MIT"
        assert data["degree"] == "Bachelor"
        assert "id" in data

    def test_list_education(self, client):
        headers = _register_and_login(client, "edu_b@example.com")
        client.post("/api/v1/education", json={"institution": "MIT"}, headers=headers)
        client.post("/api/v1/education", json={"institution": "Stanford"}, headers=headers)
        response = client.get("/api/v1/education", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_education(self, client):
        headers = _register_and_login(client, "edu_c@example.com")
        created = client.post(
            "/api/v1/education",
            json={"institution": "Harvard"},
            headers=headers,
        ).json()
        response = client.get(f"/api/v1/education/{created['id']}", headers=headers)
        assert response.status_code == 200
        assert response.json()["institution"] == "Harvard"

    def test_update_education(self, client):
        headers = _register_and_login(client, "edu_d@example.com")
        created = client.post(
            "/api/v1/education",
            json={"institution": "MIT", "degree": "Bachelor"},
            headers=headers,
        ).json()
        response = client.put(
            f"/api/v1/education/{created['id']}",
            json={"degree": "Master"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["degree"] == "Master"
        assert response.json()["institution"] == "MIT"

    def test_delete_education(self, client):
        headers = _register_and_login(client, "edu_e@example.com")
        created = client.post(
            "/api/v1/education",
            json={"institution": "MIT"},
            headers=headers,
        ).json()
        response = client.delete(f"/api/v1/education/{created['id']}", headers=headers)
        assert response.status_code == 204
        response = client.get(f"/api/v1/education/{created['id']}", headers=headers)
        assert response.status_code == 404

    def test_get_education_not_found(self, client):
        headers = _register_and_login(client, "edu_f@example.com")
        response = client.get(
            "/api/v1/education/00000000-0000-0000-0000-000000000000",
            headers=headers,
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Work Experience
# ---------------------------------------------------------------------------


class TestWorkExperience:
    """Test work experience CRUD operations."""

    def test_create_experience(self, client):
        headers = _register_and_login(client, "exp_a@example.com")
        response = client.post(
            "/api/v1/experience",
            json={
                "company": "Acme Corp",
                "job_title": "Software Engineer",
                "start_date": "2020-01-01",
                "end_date": "2022-01-01",
                "description": "Built things",
            },
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["company"] == "Acme Corp"
        assert data["job_title"] == "Software Engineer"

    def test_list_experience(self, client):
        headers = _register_and_login(client, "exp_b@example.com")
        client.post(
            "/api/v1/experience",
            json={"company": "Acme", "job_title": "Dev", "start_date": "2020-01-01"},
            headers=headers,
        )
        client.post(
            "/api/v1/experience",
            json={"company": "Globex", "job_title": "Lead", "start_date": "2022-01-01"},
            headers=headers,
        )
        response = client.get("/api/v1/experience", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_experience(self, client):
        headers = _register_and_login(client, "exp_c@example.com")
        created = client.post(
            "/api/v1/experience",
            json={"company": "Acme", "job_title": "Dev", "start_date": "2020-01-01"},
            headers=headers,
        ).json()
        response = client.get(f"/api/v1/experience/{created['id']}", headers=headers)
        assert response.status_code == 200
        assert response.json()["company"] == "Acme"

    def test_update_experience(self, client):
        headers = _register_and_login(client, "exp_d@example.com")
        created = client.post(
            "/api/v1/experience",
            json={"company": "Acme", "job_title": "Dev", "start_date": "2020-01-01"},
            headers=headers,
        ).json()
        response = client.put(
            f"/api/v1/experience/{created['id']}",
            json={"job_title": "Senior Dev"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["job_title"] == "Senior Dev"

    def test_delete_experience(self, client):
        headers = _register_and_login(client, "exp_e@example.com")
        created = client.post(
            "/api/v1/experience",
            json={"company": "Acme", "job_title": "Dev", "start_date": "2020-01-01"},
            headers=headers,
        ).json()
        response = client.delete(f"/api/v1/experience/{created['id']}", headers=headers)
        assert response.status_code == 204
        response = client.get(f"/api/v1/experience/{created['id']}", headers=headers)
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------


class TestSkills:
    """Test skills CRUD operations."""

    def test_create_skill(self, client):
        headers = _register_and_login(client, "skill_a@example.com")
        response = client.post(
            "/api/v1/skills",
            json={"name": "Python", "category": "Technical", "proficiency": "Expert"},
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Python"
        assert data["proficiency"] == "Expert"

    def test_list_skills(self, client):
        headers = _register_and_login(client, "skill_b@example.com")
        client.post("/api/v1/skills", json={"name": "Python"}, headers=headers)
        client.post("/api/v1/skills", json={"name": "Rust"}, headers=headers)
        response = client.get("/api/v1/skills", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_skill(self, client):
        headers = _register_and_login(client, "skill_c@example.com")
        created = client.post(
            "/api/v1/skills",
            json={"name": "Python"},
            headers=headers,
        ).json()
        response = client.get(f"/api/v1/skills/{created['id']}", headers=headers)
        assert response.status_code == 200
        assert response.json()["name"] == "Python"

    def test_update_skill(self, client):
        headers = _register_and_login(client, "skill_d@example.com")
        created = client.post(
            "/api/v1/skills",
            json={"name": "Python", "proficiency": "Intermediate"},
            headers=headers,
        ).json()
        response = client.put(
            f"/api/v1/skills/{created['id']}",
            json={"proficiency": "Expert"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["proficiency"] == "Expert"

    def test_delete_skill(self, client):
        headers = _register_and_login(client, "skill_e@example.com")
        created = client.post(
            "/api/v1/skills",
            json={"name": "Python"},
            headers=headers,
        ).json()
        response = client.delete(f"/api/v1/skills/{created['id']}", headers=headers)
        assert response.status_code == 204
        response = client.get(f"/api/v1/skills/{created['id']}", headers=headers)
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Certifications
# ---------------------------------------------------------------------------


class TestCertifications:
    """Test certifications CRUD operations."""

    def test_create_certification(self, client):
        headers = _register_and_login(client, "cert_a@example.com")
        response = client.post(
            "/api/v1/certifications",
            json={
                "name": "AWS Solutions Architect",
                "issuing_organization": "Amazon",
                "issue_date": "2023-01-01",
                "credential_id": "AWS-12345",
            },
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "AWS Solutions Architect"
        assert data["issuing_organization"] == "Amazon"

    def test_list_certifications(self, client):
        headers = _register_and_login(client, "cert_b@example.com")
        client.post(
            "/api/v1/certifications",
            json={"name": "AWS"},
            headers=headers,
        )
        client.post(
            "/api/v1/certifications",
            json={"name": "GCP"},
            headers=headers,
        )
        response = client.get("/api/v1/certifications", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_certification(self, client):
        headers = _register_and_login(client, "cert_c@example.com")
        created = client.post(
            "/api/v1/certifications",
            json={"name": "AWS"},
            headers=headers,
        ).json()
        response = client.get(f"/api/v1/certifications/{created['id']}", headers=headers)
        assert response.status_code == 200
        assert response.json()["name"] == "AWS"

    def test_update_certification(self, client):
        headers = _register_and_login(client, "cert_d@example.com")
        created = client.post(
            "/api/v1/certifications",
            json={"name": "AWS Associate"},
            headers=headers,
        ).json()
        response = client.put(
            f"/api/v1/certifications/{created['id']}",
            json={"name": "AWS Professional"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "AWS Professional"

    def test_delete_certification(self, client):
        headers = _register_and_login(client, "cert_e@example.com")
        created = client.post(
            "/api/v1/certifications",
            json={"name": "AWS"},
            headers=headers,
        ).json()
        response = client.delete(f"/api/v1/certifications/{created['id']}", headers=headers)
        assert response.status_code == 204
        response = client.get(f"/api/v1/certifications/{created['id']}", headers=headers)
        assert response.status_code == 404

    def test_valid_credential_url_accepted(self, client):
        headers = _register_and_login(client, "cert_url_ok@example.com")
        response = client.post(
            "/api/v1/certifications",
            json={"name": "AWS", "credential_url": "https://aws.amazon.com/verify/12345"},
            headers=headers,
        )
        assert response.status_code == 201
        assert response.json()["credential_url"] == "https://aws.amazon.com/verify/12345"

    def test_invalid_credential_url_rejected(self, client):
        headers = _register_and_login(client, "cert_url_bad@example.com")
        response = client.post(
            "/api/v1/certifications",
            json={"name": "AWS", "credential_url": "not-a-url"},
            headers=headers,
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Cross-user isolation (NON-NEGOTIABLE)
# ---------------------------------------------------------------------------


class TestCrossUserIsolation:
    """Verify User B cannot access or modify User A's resources."""

    @pytest.fixture()
    def two_users(self, client):
        headers_a = _register_and_login(client, "isolation_a@example.com", "User A")
        headers_b = _register_and_login(client, "isolation_b@example.com", "User B")
        return headers_a, headers_b

    def test_profile_isolation(self, client, two_users):
        headers_a, headers_b = two_users
        # User A creates a profile
        client.post(
            "/api/v1/profile",
            json={"professional_title": "Engineer A"},
            headers=headers_a,
        )
        # User B cannot see it
        response = client.get("/api/v1/profile", headers=headers_b)
        assert response.status_code == 404
        # User B cannot update it
        response = client.put(
            "/api/v1/profile",
            json={"professional_title": "Hacked"},
            headers=headers_b,
        )
        assert response.status_code == 404
        # User A still sees their own
        response = client.get("/api/v1/profile", headers=headers_a)
        assert response.status_code == 200
        assert response.json()["professional_title"] == "Engineer A"

    def test_education_isolation(self, client, two_users):
        headers_a, headers_b = two_users
        created = client.post(
            "/api/v1/education",
            json={"institution": "MIT"},
            headers=headers_a,
        ).json()
        eid = created["id"]

        # User B cannot read, update, or delete User A's education
        assert client.get(f"/api/v1/education/{eid}", headers=headers_b).status_code == 404
        assert client.put(
            f"/api/v1/education/{eid}", json={"institution": "Hacked"}, headers=headers_b
        ).status_code == 404
        assert client.delete(f"/api/v1/education/{eid}", headers=headers_b).status_code == 404

        # User A still owns it
        response = client.get(f"/api/v1/education/{eid}", headers=headers_a)
        assert response.status_code == 200
        assert response.json()["institution"] == "MIT"

    def test_education_list_only_returns_own(self, client, two_users):
        headers_a, headers_b = two_users
        client.post("/api/v1/education", json={"institution": "MIT"}, headers=headers_a)
        client.post("/api/v1/education", json={"institution": "Stanford"}, headers=headers_a)
        client.post("/api/v1/education", json={"institution": "Oxford"}, headers=headers_b)

        list_a = client.get("/api/v1/education", headers=headers_a).json()
        list_b = client.get("/api/v1/education", headers=headers_b).json()

        assert len(list_a) == 2
        assert len(list_b) == 1
        assert all(item["institution"] != "Oxford" for item in list_a)
        assert all(item["institution"] != "MIT" for item in list_b)
        assert all(item["institution"] != "Stanford" for item in list_b)

    def test_experience_isolation(self, client, two_users):
        headers_a, headers_b = two_users
        created = client.post(
            "/api/v1/experience",
            json={"company": "Acme", "job_title": "Dev", "start_date": "2020-01-01"},
            headers=headers_a,
        ).json()
        eid = created["id"]

        assert client.get(f"/api/v1/experience/{eid}", headers=headers_b).status_code == 404
        assert client.put(
            f"/api/v1/experience/{eid}", json={"company": "Hacked"}, headers=headers_b
        ).status_code == 404
        assert client.delete(f"/api/v1/experience/{eid}", headers=headers_b).status_code == 404

        response = client.get(f"/api/v1/experience/{eid}", headers=headers_a)
        assert response.status_code == 200
        assert response.json()["company"] == "Acme"

    def test_skill_isolation(self, client, two_users):
        headers_a, headers_b = two_users
        created = client.post(
            "/api/v1/skills",
            json={"name": "Python"},
            headers=headers_a,
        ).json()
        sid = created["id"]

        assert client.get(f"/api/v1/skills/{sid}", headers=headers_b).status_code == 404
        assert client.put(
            f"/api/v1/skills/{sid}", json={"name": "Hacked"}, headers=headers_b
        ).status_code == 404
        assert client.delete(f"/api/v1/skills/{sid}", headers=headers_b).status_code == 404

        response = client.get(f"/api/v1/skills/{sid}", headers=headers_a)
        assert response.status_code == 200
        assert response.json()["name"] == "Python"

    def test_certification_isolation(self, client, two_users):
        headers_a, headers_b = two_users
        created = client.post(
            "/api/v1/certifications",
            json={"name": "AWS"},
            headers=headers_a,
        ).json()
        cid = created["id"]

        assert client.get(f"/api/v1/certifications/{cid}", headers=headers_b).status_code == 404
        assert client.put(
            f"/api/v1/certifications/{cid}", json={"name": "Hacked"}, headers=headers_b
        ).status_code == 404
        assert client.delete(f"/api/v1/certifications/{cid}", headers=headers_b).status_code == 404

        response = client.get(f"/api/v1/certifications/{cid}", headers=headers_a)
        assert response.status_code == 200
        assert response.json()["name"] == "AWS"
