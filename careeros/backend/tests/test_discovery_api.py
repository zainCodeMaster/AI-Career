"""Tests for Phase 4.x new API endpoints — source details, health, discovery runs."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.db.models.jobs import Job, JobDiscoveryRun, JobExternalReference, JobSource
from app.services.job_normalizer import RawJob, normalize
from app.services.job_discovery import upsert_job


# ---------------------------------------------------------------------------
# Helpers (reused pattern from test_jobs.py)
# ---------------------------------------------------------------------------


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


def _make_raw(
    source: str = "test_source",
    source_job_id: str = "src-1",
    title: str = "Software Engineer",
    company: str = "Acme",
    location: str = "Lahore, Punjab",
    **overrides,
) -> RawJob:
    fields = dict(
        source=source,
        source_job_id=source_job_id,
        source_url="https://example.com/job/1",
        title=title,
        company_name=company,
        company_url="https://acme.example.com",
        description="Build things with Python and FastAPI.",
        requirements="3+ years experience",
        responsibilities="Develop backend services",
        skills="python, fastapi, postgresql",
        employment_type="full_time",
        workplace_type="onsite",
        department="Engineering",
        category="Software",
        location=location,
        salary_min=100000.0,
        salary_max=200000.0,
        salary_currency="PKR",
        salary_period="monthly",
        experience_min=3,
        experience_max=6,
        education_requirements="Bachelors",
        posted_at=datetime.now(timezone.utc),
        closing_at=None,
        is_remote=False,
        is_pakistan_eligible=True,
        eligibility="Open to Pakistani citizens",
    )
    fields.update(overrides)
    return RawJob(**fields)


# ---------------------------------------------------------------------------
# Source detail endpoint
# ---------------------------------------------------------------------------


class TestSourceDetailEndpoint:
    def test_get_source_detail_found(self, client, db_session):
        headers = _register_and_login(client, "src_detail@example.com")
        r = client.get("/api/v1/sources/pk_fpsc", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == "pk_fpsc"
        assert "base_url" in data
        assert "notes" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_get_source_detail_not_found(self, client, db_session):
        headers = _register_and_login(client, "src_detail_nf@example.com")
        r = client.get("/api/v1/sources/nonexistent_source", headers=headers)
        assert r.status_code == 404

    def test_get_source_detail_requires_auth(self, client):
        r = client.get("/api/v1/sources/pk_fpsc")
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# Source health endpoint
# ---------------------------------------------------------------------------


class TestSourceHealthEndpoint:
    def test_get_sources_health(self, client, db_session):
        headers = _register_and_login(client, "src_health@example.com")
        r = client.get("/api/v1/sources/health", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert "sources" in data
        assert len(data["sources"]) >= 1

    def test_health_returns_status_field(self, client, db_session):
        headers = _register_and_login(client, "src_health2@example.com")
        r = client.get("/api/v1/sources/health", headers=headers)
        data = r.json()
        for entry in data["sources"]:
            assert "status" in entry
            assert "source_id" in entry
            assert "source_name" in entry
            assert "enabled" in entry
            assert entry["status"] in {"active", "degraded", "failed", "unknown"}

    def test_health_requires_auth(self, client):
        r = client.get("/api/v1/sources/health")
        assert r.status_code == 401

    def test_health_shows_degraded_for_failing_source(self, client, db_session):
        """A source with consecutive failures > 0 but < 3 should be 'degraded'."""
        headers = _register_and_login(client, "src_health_deg@example.com")

        # Create a source and mark it as degraded
        src = db_session.get(JobSource, "pk_fpsc")
        src.consecutive_failures = 1
        src.last_failure_at = datetime.now(timezone.utc)
        src.last_error = "Test failure"
        db_session.commit()

        r = client.get("/api/v1/sources/health", headers=headers)
        data = r.json()
        fp = next(s for s in data["sources"] if s["source_id"] == "pk_fpsc")
        assert fp["status"] == "degraded"

    def test_health_shows_failed_for_multiple_failures(self, client, db_session):
        """A source with consecutive failures >= 3 should be 'failed'."""
        headers = _register_and_login(client, "src_health_fail@example.com")

        src = db_session.get(JobSource, "pk_rozee")
        src.consecutive_failures = 3
        src.last_failure_at = datetime.now(timezone.utc)
        db_session.commit()

        r = client.get("/api/v1/sources/health", headers=headers)
        data = r.json()
        rozee = next(s for s in data["sources"] if s["source_id"] == "pk_rozee")
        assert rozee["status"] == "failed"

    def test_health_shows_active_for_healthy_source(self, client, db_session):
        """A source with last_success_at and 0 failures should be 'active'."""
        headers = _register_and_login(client, "src_health_ok@example.com")

        # pk_fpsc is seeded in conftest
        src = db_session.get(JobSource, "pk_fpsc")
        src.consecutive_failures = 0
        src.last_success_at = datetime.now(timezone.utc)
        src.last_run_at = datetime.now(timezone.utc)
        db_session.commit()

        r = client.get("/api/v1/sources/health", headers=headers)
        data = r.json()
        fp = next(s for s in data["sources"] if s["source_id"] == "pk_fpsc")
        assert fp["status"] == "active"


# ---------------------------------------------------------------------------
# Discovery runs endpoint
# ---------------------------------------------------------------------------


class TestDiscoveryRunsEndpoint:
    def test_list_discovery_runs_empty(self, client, db_session):
        headers = _register_and_login(client, "runs_empty@example.com")
        r = client.get("/api/v1/jobs/discovery/runs", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_discovery_runs_with_data(self, client, db_session):
        headers = _register_and_login(client, "runs_data@example.com")

        # Create a discovery run directly
        run = JobDiscoveryRun(
            source_id="pk_fpsc",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            status="success",
            jobs_found=5,
            jobs_created=3,
            jobs_updated=2,
        )
        db_session.add(run)
        db_session.commit()

        r = client.get("/api/v1/jobs/discovery/runs", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["status"] == "success"
        assert data["items"][0]["jobs_found"] == 5

    def test_list_discovery_runs_pagination(self, client, db_session):
        headers = _register_and_login(client, "runs_page@example.com")

        for i in range(5):
            run = JobDiscoveryRun(
                source_id="pk_fpsc",
                started_at=datetime.now(timezone.utc) - timedelta(hours=i),
                completed_at=datetime.now(timezone.utc),
                status="success",
                jobs_found=i,
            )
            db_session.add(run)
        db_session.commit()

        r = client.get("/api/v1/jobs/discovery/runs?page=1&page_size=2", headers=headers)
        data = r.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5

    def test_list_discovery_runs_filter_by_source(self, client, db_session):
        headers = _register_and_login(client, "runs_filter_src@example.com")

        db_session.add(JobDiscoveryRun(
            source_id="pk_fpsc", started_at=datetime.now(timezone.utc),
            status="success", jobs_found=3,
        ))
        db_session.add(JobDiscoveryRun(
            source_id="pk_ppsc", started_at=datetime.now(timezone.utc),
            status="success", jobs_found=5,
        ))
        db_session.commit()

        r = client.get("/api/v1/jobs/discovery/runs?source_id=pk_fpsc", headers=headers)
        data = r.json()
        assert data["total"] == 1
        assert data["items"][0]["source_id"] == "pk_fpsc"

    def test_list_discovery_runs_filter_by_status(self, client, db_session):
        headers = _register_and_login(client, "runs_filter_status@example.com")

        db_session.add(JobDiscoveryRun(
            source_id="pk_fpsc", started_at=datetime.now(timezone.utc),
            status="success", jobs_found=3,
        ))
        db_session.add(JobDiscoveryRun(
            source_id="pk_fpsc", started_at=datetime.now(timezone.utc),
            status="failed", jobs_found=0,
        ))
        db_session.commit()

        r = client.get("/api/v1/jobs/discovery/runs?status=failed", headers=headers)
        data = r.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "failed"

    def test_discovery_runs_requires_auth(self, client):
        r = client.get("/api/v1/jobs/discovery/runs")
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# Updated discovery run endpoint with source_id
# ---------------------------------------------------------------------------


class TestSelectiveDiscoveryRun:
    def test_trigger_specific_source(self, client, db_session):
        from app.services.job_sources import StaticListSource, SOURCE_REGISTRY
        headers = _register_and_login(client, "sel_disc@example.com")

        class _TempSource(StaticListSource):
            source_id = "sel_disc_test"
        SOURCE_REGISTRY["sel_disc_test"] = _TempSource
        _TempSource._class_jobs = []

        try:
            db_session.add(JobSource(
                id="sel_disc_test", name="Sel Test", category="private_board",
                source_type="test", integration_method="static",
                country="PK", enabled=True, is_active=True,
            ))
            db_session.commit()

            r = client.post("/api/v1/jobs/_discovery/run", json={"source_id": "sel_disc_test"}, headers=headers)
            assert r.status_code == 200
            data = r.json()
            assert data["sources_attempted"] == 1
        finally:
            SOURCE_REGISTRY.pop("sel_disc_test", None)

    def test_trigger_unknown_source(self, client, db_session):
        headers = _register_and_login(client, "sel_disc_unknown@example.com")
        r = client.post("/api/v1/jobs/_discovery/run", json={"source_id": "nonexistent_source"}, headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["sources_failed"] == 1
        assert data["error_count"] == 1

    def test_trigger_all_sources_no_payload(self, client, db_session):
        headers = _register_and_login(client, "sel_disc_all@example.com")
        r = client.post("/api/v1/jobs/_discovery/run", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert "sources_attempted" in data
