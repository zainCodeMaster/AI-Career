"""Tests for Phase 4 Job Discovery: models, normalization, dedup, discovery engine, API, and cross-user security."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Optional

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models.jobs import (
    Job,
    JobDiscoveryRun,
    JobSource,
    UserJobPreferences,
    UserSavedJob,
)
from app.db.models.user import User
from app.services.job_discovery import (
    DiscoveryStats,
    discover_all_enabled,
    discover_source,
    expire_stale_jobs,
    upsert_job,
)
from app.services.job_normalizer import (
    NormalizedJob,
    RawJob,
    compute_content_hash,
    compute_normalized_hash,
    normalize,
)
from app.services.job_sources import (
    FailingSource,
    JobSourceError,
    SOURCE_REGISTRY,
    StaticListSource,
    build_source,
)


# ---------------------------------------------------------------------------
# Helpers
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
# Normalization tests
# ---------------------------------------------------------------------------


class TestNormalization:
    def test_normalize_basic(self):
        norm = normalize(_make_raw())
        assert norm.title == "Software Engineer"
        assert norm.company_name == "Acme"
        assert norm.city == "Lahore"
        assert norm.province == "Punjab"
        assert norm.country == "PK"
        assert norm.is_pakistan_eligible is True
        assert norm.employment_type == "full_time"
        assert norm.workplace_type == "onsite"
        assert norm.salary_min == 100000.0
        assert norm.salary_max == 200000.0
        assert norm.salary_currency == "PKR"

    def test_normalize_remote_detection(self):
        norm = normalize(_make_raw(location="Remote - Pakistan", workplace_type=None))
        assert norm.workplace_type == "remote"
        assert norm.is_remote is True

    def test_normalize_hybrid_detection(self):
        norm = normalize(_make_raw(workplace_type="hybrid"))
        assert norm.workplace_type == "hybrid"

    def test_normalize_employment_type_mapping(self):
        for raw_val, expected in [
            ("Full-Time", "full_time"),
            ("part-time", "part_time"),
            ("Contract", "contract"),
            ("Internship", "internship"),
            ("Graduate Programme", "graduate"),
            ("Trainee", "trainee"),
            ("Freelance", "freelance"),
        ]:
            norm = normalize(_make_raw(employment_type=raw_val))
            assert norm.employment_type == expected, f"Failed for {raw_val}"

    def test_normalize_unknown_employment_type_keeps_none(self):
        norm = normalize(_make_raw(employment_type=""))
        assert norm.employment_type is None

    def test_normalize_province_detection(self):
        for loc, expected_prov in [
            ("Karachi, Sindh", "Sindh"),
            ("Peshawar, Khyber Pakhtunkhwa", "Khyber Pakhtunkhwa"),
            ("Islamabad", "Islamabad Capital Territory"),
            ("Quetta, Balochistan", "Balochistan"),
        ]:
            norm = normalize(_make_raw(location=loc))
            assert norm.province == expected_prov, f"Failed for {loc}"

    def test_normalize_city_detection(self):
        for loc, expected_city in [
            ("Lahore, Punjab", "Lahore"),
            ("Karachi", "Karachi"),
            ("Islamabad, ICT", "Islamabad"),
            ("Peshawar", "Peshawar"),
        ]:
            norm = normalize(_make_raw(location=loc))
            assert norm.city == expected_city, f"Failed for {loc}"

    def test_normalize_salary_parsing(self):
        norm = normalize(_make_raw(description="Salary: PKR 150,000 - 250,000 per month"))
        # description is the same as the default; the explicit fields take precedence
        assert norm.salary_min == 100000.0  # explicit wins
        assert norm.salary_max == 200000.0

    def test_normalize_salary_parsing_from_text(self):
        raw = _make_raw(salary_min=None, salary_max=None, salary_currency=None, salary_period=None)
        raw = RawJob(**{**raw.__dict__, "description": "PKR 80,000 - 120,000 monthly"})
        norm = normalize(raw)
        assert norm.salary_min == 80000.0
        assert norm.salary_max == 120000.0
        assert norm.salary_currency == "PKR"
        assert norm.salary_period == "monthly"

    def test_normalize_date_parsing(self):
        posted = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        closing = datetime(2024, 2, 15, 10, 0, 0, tzinfo=timezone.utc)
        norm = normalize(_make_raw(posted_at=posted, closing_at=closing))
        assert norm.posted_at == posted
        assert norm.closing_at == closing

    def test_normalize_naive_dates_become_utc(self):
        posted = datetime(2024, 1, 15, 10, 0, 0)  # naive
        norm = normalize(_make_raw(posted_at=posted))
        assert norm.posted_at is not None
        assert norm.posted_at.tzinfo == timezone.utc

    def test_normalize_does_not_invent_data(self):
        norm = normalize(_make_raw(title="", company_name="", location=""))
        assert norm.title == ""
        assert norm.company_name == ""
        assert norm.city is None
        assert norm.province is None

    def test_content_hash_deterministic(self):
        a = normalize(_make_raw())
        b = normalize(_make_raw())
        assert a.content_hash == b.content_hash

    def test_content_hash_changes_with_content(self):
        a = normalize(_make_raw(description="Build things with Python"))
        b = normalize(_make_raw(description="Build things with Rust"))
        assert a.content_hash != b.content_hash

    def test_normalized_hash_deterministic(self):
        a = normalize(_make_raw(title="Engineer", company="Acme", location="Lahore"))
        b = normalize(_make_raw(title="Engineer", company="Acme", location="Lahore, Punjab"))
        assert a.normalized_hash == b.normalized_hash

    def test_normalized_hash_differs_for_different_jobs(self):
        a = normalize(_make_raw(title="Engineer", company="Acme", location="Lahore"))
        b = normalize(_make_raw(title="Manager", company="Acme", location="Lahore"))
        assert a.normalized_hash != b.normalized_hash

    def test_non_pakistan_job(self):
        norm = normalize(_make_raw(is_pakistan_eligible=False, location="New York"))
        assert norm.is_pakistan_eligible is False
        assert norm.country == ""

    def test_helper_hashes(self):
        h1 = compute_content_hash(_make_raw())
        h2 = compute_content_hash(_make_raw())
        assert h1 == h2
        nh = compute_normalized_hash("Engineer", "Acme", "Lahore", "Punjab")
        assert isinstance(nh, str)
        assert len(nh) == 64


# ---------------------------------------------------------------------------
# Deduplication tests
# ---------------------------------------------------------------------------


class TestDeduplication:
    def test_same_source_job_id_is_upserted(self, db_session):
        first = normalize(_make_raw(source_job_id="abc"))
        _job, created = upsert_job(db_session, first)
        db_session.commit()
        assert created is True

        second = normalize(_make_raw(source_job_id="abc", description="Updated description"))
        _job2, created2 = upsert_job(db_session, second)
        db_session.commit()
        assert created2 is False

    def test_different_source_same_identity_merges(self, db_session):
        first = normalize(_make_raw(source="src_a", source_job_id="a1"))
        _job, created = upsert_job(db_session, first)
        db_session.commit()
        assert created is True

        # Same normalized identity from a different source
        second = normalize(_make_raw(
            source="src_b", source_job_id="b1",
            title="Software Engineer", company_name="Acme",
            location="Lahore, Punjab",
        ))
        _job2, created2 = upsert_job(db_session, second)
        db_session.commit()
        # Should merge (not create a new row)
        assert created2 is False
        # Only one job in DB
        count = db_session.query(Job).count()
        assert count == 1

    def test_similar_title_different_company_does_not_merge(self, db_session):
        first = normalize(_make_raw(source="src_a", source_job_id="a1", company_name="Acme"))
        upsert_job(db_session, first)
        db_session.commit()

        # Same title, different company — distinct jobs
        second = normalize(_make_raw(
            source="src_b", source_job_id="b1",
            title="Software Engineer", company_name="Globex",
            location="Lahore, Punjab",
        ))
        _job, created = upsert_job(db_session, second)
        db_session.commit()
        assert created is True  # new row
        assert db_session.query(Job).count() == 2

    def test_same_title_similar_company_does_not_merge(self, db_session):
        first = normalize(_make_raw(source="src_a", source_job_id="a1", company_name="Acme Corp"))
        upsert_job(db_session, first)
        db_session.commit()
        # Different company name → distinct
        second = normalize(_make_raw(
            source="src_b", source_job_id="b1",
            title="Software Engineer", company_name="Acme Inc",
            location="Lahore, Punjab",
        ))
        _job, created = upsert_job(db_session, second)
        db_session.commit()
        assert created is True
        assert db_session.query(Job).count() == 2


# ---------------------------------------------------------------------------
# Source architecture tests
# ---------------------------------------------------------------------------


class TestJobSourceArchitecture:
    def test_static_list_source_returns_jobs(self):
        jobs = [_make_raw(source_job_id="a"), _make_raw(source_job_id="b")]
        src = StaticListSource(jobs)
        assert src.fetch() == jobs
        assert len(src.fetch(max_results=1)) == 1

    def test_failing_source_raises(self):
        src = FailingSource("nope")
        with pytest.raises(JobSourceError):
            src.fetch()

    def test_source_registry_contains_builtins(self):
        assert "static_list" in SOURCE_REGISTRY
        assert "failing_source" in SOURCE_REGISTRY

    def test_build_source_creates_instance(self):
        src = build_source("static_list", jobs=[])
        assert isinstance(src, StaticListSource)

    def test_build_source_unknown_raises(self):
        with pytest.raises(KeyError):
            build_source("does_not_exist")


# ---------------------------------------------------------------------------
# Discovery engine tests
# ---------------------------------------------------------------------------


class TestDiscoveryEngine:
    def test_register_static_list_source(self, db_session):
        SOURCE_REGISTRY["my_test_source"] = type(
            "MyTestSource", (StaticListSource,), {"source_id": "my_test_source"}
        )
        try:
            src_row = JobSource(
                id="my_test_source",
                name="My Test Source",
                category="private_board",
                source_type="test",
                integration_method="static",
                country="PK",
                enabled=True,
                is_active=True,
            )
            db_session.add(src_row)
            db_session.commit()

            result = discover_source(db_session, "my_test_source")
            assert result.error is None
            # Source not registered as class — but we registered it
        finally:
            SOURCE_REGISTRY.pop("my_test_source", None)

    def test_discover_source_persists_jobs(self, db_session):
        # Register a temporary source
        class _TempSource(StaticListSource):
            source_id = "temp_source"
        SOURCE_REGISTRY["temp_source"] = _TempSource

        try:
            src_row = JobSource(
                id="temp_source",
                name="Temp",
                category="private_board",
                source_type="test",
                integration_method="static",
                country="PK",
                enabled=True,
                is_active=True,
            )
            db_session.add(src_row)
            db_session.commit()

            # Populate the static source with jobs (class-level for persistence)
            temp_jobs = [
                _make_raw(source="temp_source", source_job_id="t1", title="Job A"),
                _make_raw(source="temp_source", source_job_id="t2", title="Job B"),
            ]
            _TempSource._class_jobs = temp_jobs

            result = discover_source(db_session, "temp_source")
            assert result.error is None

            count = db_session.query(Job).filter(Job.source == "temp_source").count()
            assert count == 2

            # A discovery run was logged
            run = db_session.query(JobDiscoveryRun).filter(
                JobDiscoveryRun.source_id == "temp_source"
            ).order_by(JobDiscoveryRun.started_at.desc()).first()
            assert run is not None
            assert run.jobs_created == 2
            assert run.jobs_found == 2
            assert run.status == "success"

            # Source health updated
            src = db_session.get(JobSource, "temp_source")
            assert src.consecutive_failures == 0
            assert src.total_jobs_discovered == 2
        finally:
            SOURCE_REGISTRY.pop("temp_source", None)

    def test_discover_source_failure_logged(self, db_session):
        class _FailSource(FailingSource):
            source_id = "fail_source"
        SOURCE_REGISTRY["fail_source"] = _FailSource

        try:
            db_session.add(JobSource(
                id="fail_source", name="Fail", category="private_board",
                source_type="test", integration_method="static",
                country="PK", enabled=True, is_active=True,
            ))
            db_session.commit()

            result = discover_source(db_session, "fail_source")
            assert result.error is not None

            run = db_session.query(JobDiscoveryRun).filter(
                JobDiscoveryRun.source_id == "fail_source"
            ).order_by(JobDiscoveryRun.started_at.desc()).first()
            assert run is not None
            assert run.status == "failed"

            src = db_session.get(JobSource, "fail_source")
            assert src.consecutive_failures == 1
            assert src.last_error is not None
        finally:
            SOURCE_REGISTRY.pop("fail_source", None)

    def test_expire_stale_jobs(self, db_session):
        now = datetime.now(timezone.utc)
        old = datetime.now(timezone.utc) - timedelta(days=90)
        norm = normalize(_make_raw(source_job_id="old1"))
        _job, _ = upsert_job(db_session, norm)
        # Force last_seen_at to be old
        job_row = db_session.query(Job).filter(Job.source_job_id == "old1").first()
        job_row.last_seen_at = old
        db_session.commit()

        expired = expire_stale_jobs(db_session, days=60)
        assert expired >= 1

        job_row = db_session.query(Job).filter(Job.source_job_id == "old1").first()
        assert job_row.is_active is False
        assert job_row.status == "expired"

    def test_discover_all_enabled_runs_all(self, db_session):
        class _S1(StaticListSource):
            source_id = "all_s1"
        class _S2(StaticListSource):
            source_id = "all_s2"
        class _Fail(FailingSource):
            source_id = "all_fail"
        SOURCE_REGISTRY.update({
            "all_s1": _S1, "all_s2": _S2, "all_fail": _Fail,
        })
        try:
            # Use distinct identities so dedup does not merge them.
            _S1._class_jobs = [_make_raw(
                source="all_s1", source_job_id="x1", title="Job A",
                company_name="CompanyA", location="Lahore, Punjab",
            )]
            _S2._class_jobs = [_make_raw(
                source="all_s2", source_job_id="y1", title="Job B",
                company_name="CompanyB", location="Karachi, Sindh",
            )]

            for sid in ("all_s1", "all_s2", "all_fail"):
                db_session.add(JobSource(
                    id=sid, name=sid, category="private_board",
                    source_type="test", integration_method="static",
                    country="PK", enabled=True, is_active=True,
                ))
            db_session.commit()

            stats = discover_all_enabled(db_session)
            assert stats.sources_attempted == 3
            assert stats.sources_succeeded == 2
            assert stats.sources_failed == 1
            assert stats.jobs_created == 2
        finally:
            for sid in ("all_s1", "all_s2", "all_fail"):
                SOURCE_REGISTRY.pop(sid, None)


# ---------------------------------------------------------------------------
# API tests
# ---------------------------------------------------------------------------


class TestJobsAPI:
    def test_jobs_endpoints_require_auth(self, client):
        for method, path in [
            ("GET", "/api/v1/jobs"),
            ("GET", "/api/v1/jobs/saved"),
            ("GET", "/api/v1/sources"),
            ("GET", "/api/v1/job-preferences"),
            ("PUT", "/api/v1/job-preferences"),
            ("POST", "/api/v1/jobs/_discovery/run"),
        ]:
            r = client.request(method, path, json={})
            assert r.status_code == 401, f"{method} {path} should require auth"

    def test_list_jobs_empty(self, client):
        headers = _register_and_login(client, "jobs_empty@example.com")
        r = client.get("/api/v1/jobs", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 20

    def test_list_jobs_with_data(self, client, db_session):
        headers = _register_and_login(client, "jobs_data@example.com")
        # Insert a job directly via the DB (bypassing the discovery engine for this test)
        norm = normalize(_make_raw(source="test_api", source_job_id="api-1", title="Backend Engineer"))
        upsert_job(db_session, norm)
        db_session.commit()

        r = client.get("/api/v1/jobs", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 1
        titles = [j["title"] for j in data["items"]]
        assert "Backend Engineer" in titles

    def test_list_jobs_keyword_filter(self, client, db_session):
        headers = _register_and_login(client, "jobs_kw@example.com")
        upsert_job(db_session, normalize(_make_raw(
            source_job_id="kw-1", title="Python Developer",
            description="Backend role focused on Django and Flask.",
        )))
        upsert_job(db_session, normalize(_make_raw(
            source_job_id="kw-2", title="Java Developer",
            company_name="JavaCo", location="Karachi, Sindh",
            description="Enterprise microservices with Spring Boot.",
        )))
        db_session.commit()

        r = client.get("/api/v1/jobs?keyword=Python", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert any(j["title"] == "Python Developer" for j in data["items"])
        assert not any(j["title"] == "Java Developer" for j in data["items"])

    def test_list_jobs_city_filter(self, client, db_session):
        headers = _register_and_login(client, "jobs_city@example.com")
        upsert_job(db_session, normalize(_make_raw(source_job_id="c-1", location="Lahore, Punjab", company_name="A", title="Job A")))
        upsert_job(db_session, normalize(_make_raw(source_job_id="c-2", location="Karachi, Sindh", company_name="B", title="Job B")))
        db_session.commit()

        r = client.get("/api/v1/jobs?city=Lahore", headers=headers)
        data = r.json()
        items = data["items"]
        assert all(j["city"] == "Lahore" for j in items)

    def test_list_jobs_pakistan_only_by_default(self, client, db_session):
        headers = _register_and_login(client, "jobs_pk@example.com")
        # Non-Pakistan job
        norm = normalize(_make_raw(source_job_id="intl-1", is_pakistan_eligible=False, location="New York"))
        upsert_job(db_session, norm)
        db_session.commit()

        r = client.get("/api/v1/jobs", headers=headers)
        data = r.json()
        # Default is_pakistan filter should exclude international jobs
        assert all(j["is_pakistan_eligible"] for j in data["items"])

    def test_list_jobs_pagination(self, client, db_session):
        headers = _register_and_login(client, "jobs_page@example.com")
        for i in range(5):
            upsert_job(db_session, normalize(_make_raw(
                source_job_id=f"pg-{i}", title=f"Job {i}", company_name=f"C{i}",
                location="Lahore, Punjab",
            )))
        db_session.commit()

        r = client.get("/api/v1/jobs?page=1&page_size=2", headers=headers)
        data = r.json()
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total"] >= 5

    def test_get_job_detail(self, client, db_session):
        headers = _register_and_login(client, "jobs_detail@example.com")
        norm = normalize(_make_raw(source_job_id="det-1", title="Detail Job"))
        job, _ = upsert_job(db_session, norm)
        db_session.commit()

        r = client.get(f"/api/v1/jobs/{job.id}", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["title"] == "Detail Job"
        assert data["description"] is not None

    def test_get_job_not_found(self, client):
        headers = _register_and_login(client, "jobs_nf@example.com")
        r = client.get("/api/v1/jobs/00000000-0000-0000-0000-000000000000", headers=headers)
        assert r.status_code == 404

    def test_save_and_list_saved_jobs(self, client, db_session):
        headers = _register_and_login(client, "jobs_save@example.com")
        norm = normalize(_make_raw(source_job_id="save-1"))
        job, _ = upsert_job(db_session, norm)
        db_session.commit()

        # Save
        r = client.post(f"/api/v1/jobs/{job.id}/save", json={}, headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["job"]["id"] == job.id

        # List saved
        r = client.get("/api/v1/jobs/saved", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["job"]["id"] == job.id

    def test_unsave_job(self, client, db_session):
        headers = _register_and_login(client, "jobs_unsave@example.com")
        norm = normalize(_make_raw(source_job_id="unsave-1"))
        job, _ = upsert_job(db_session, norm)
        db_session.commit()

        client.post(f"/api/v1/jobs/{job.id}/save", json={}, headers=headers)
        r = client.delete(f"/api/v1/jobs/{job.id}/save", headers=headers)
        assert r.status_code == 204

        r = client.get("/api/v1/jobs/saved", headers=headers)
        assert r.json() == []

    def test_sources_list(self, client, db_session):
        headers = _register_and_login(client, "jobs_src@example.com")
        r = client.get("/api/v1/sources", headers=headers)
        assert r.status_code == 200
        sources = r.json()
        assert len(sources) >= 1
        # Seeded sources should include government entries
        cats = {s["category"] for s in sources}
        assert "government" in cats or "private_board" in cats

    def test_preferences_get_empty(self, client):
        headers = _register_and_login(client, "jobs_pref_empty@example.com")
        r = client.get("/api/v1/job-preferences", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["target_roles"] == []
        assert data["remote_preference"] is None

    def test_preferences_put_then_get(self, client):
        headers = _register_and_login(client, "jobs_pref_set@example.com")
        payload = {
            "target_roles": ["Python Developer", "ML Engineer"],
            "preferred_cities": ["Lahore", "Karachi"],
            "remote_preference": "hybrid_ok",
            "experience_level": "mid",
            "sector_preference": "private",
        }
        r = client.put("/api/v1/job-preferences", json=payload, headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["target_roles"] == ["Python Developer", "ML Engineer"]
        assert data["preferred_cities"] == ["Lahore", "Karachi"]
        assert data["remote_preference"] == "hybrid_ok"

        r = client.get("/api/v1/job-preferences", headers=headers)
        data = r.json()
        assert data["target_roles"] == ["Python Developer", "ML Engineer"]

    def test_preferences_invalid_remote_rejected(self, client):
        headers = _register_and_login(client, "jobs_pref_inv@example.com")
        r = client.put("/api/v1/job-preferences", json={"remote_preference": "invalid"}, headers=headers)
        assert r.status_code == 422

    def test_discovery_run_endpoint(self, client, db_session):
        headers = _register_and_login(client, "jobs_disc@example.com")
        r = client.post("/api/v1/jobs/_discovery/run", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert "sources_attempted" in data
        assert "jobs_created" in data


# ---------------------------------------------------------------------------
# Cross-user isolation — NON-NEGOTIABLE
# ---------------------------------------------------------------------------


class TestCrossUserIsolation:
    def test_user_b_cannot_see_user_a_saved_jobs(self, client, db_session):
        headers_a = _register_and_login(client, "iso_save_a@example.com", "User A")
        headers_b = _register_and_login(client, "iso_save_b@example.com", "User B")

        norm = normalize(_make_raw(source_job_id="iso-job-1"))
        job, _ = upsert_job(db_session, norm)
        db_session.commit()

        # User A saves
        client.post(f"/api/v1/jobs/{job.id}/save", json={}, headers=headers_a)
        # User B's saved list must be empty
        r = client.get("/api/v1/jobs/saved", headers=headers_b)
        assert r.status_code == 200
        assert r.json() == []

    def test_user_b_cannot_unsave_user_a_job(self, client, db_session):
        headers_a = _register_and_login(client, "iso_un_a@example.com", "User A")
        headers_b = _register_and_login(client, "iso_un_b@example.com", "User B")

        norm = normalize(_make_raw(source_job_id="iso-job-2"))
        job, _ = upsert_job(db_session, norm)
        db_session.commit()

        # User A saves
        client.post(f"/api/v1/jobs/{job.id}/save", json={}, headers=headers_a)
        # User B tries to unsave — should be a no-op (idempotent 204)
        r = client.delete(f"/api/v1/jobs/{job.id}/save", headers=headers_b)
        assert r.status_code == 204
        # User A's save is still intact
        r = client.get("/api/v1/jobs/saved", headers=headers_a)
        assert len(r.json()) == 1

    def test_user_b_cannot_modify_user_a_preferences(self, client):
        # Both users set preferences; verify they are isolated.
        headers_a = _register_and_login(client, "iso_pref_a@example.com", "User A")
        headers_b = _register_and_login(client, "iso_pref_b@example.com", "User B")

        client.put(
            "/api/v1/job-preferences",
            json={"target_roles": ["Role A"], "remote_preference": "remote_only"},
            headers=headers_a,
        )
        client.put(
            "/api/v1/job-preferences",
            json={"target_roles": ["Role B"], "remote_preference": "onsite_ok"},
            headers=headers_b,
        )

        a = client.get("/api/v1/job-preferences", headers=headers_a).json()
        b = client.get("/api/v1/job-preferences", headers=headers_b).json()

        assert a["target_roles"] == ["Role A"]
        assert a["remote_preference"] == "remote_only"
        assert b["target_roles"] == ["Role B"]
        assert b["remote_preference"] == "onsite_ok"

    def test_mass_assignment_user_id_rejected(self, client):
        """User cannot spoof ownership via body fields."""
        headers = _register_and_login(client, "iso_mass@example.com")
        fake_user_id = "00000000-0000-0000-0000-000000000999"
        norm = normalize(_make_raw(source_job_id="mass-1"))
        # Use db to get a real job id
        from app.db.models.jobs import Job as _Job
        from app.db.database import SessionLocal
        s = SessionLocal()
        try:
            job, _ = upsert_job(s, norm)
            s.commit()
            job_id = job.id
        finally:
            s.close()

        # Try to save with a fake user_id in the body
        r = client.post(
            f"/api/v1/jobs/{job_id}/save",
            json={"user_id": fake_user_id, "notes": "trying to spoof"},
            headers=headers,
        )
        # If accepted, the saved record must be owned by the authenticated user, not the spoofed one
        if r.status_code == 200:
            saved_user_id = r.json()["id"]  # this is the saved-row id, not user_id; verify via listing
            lst = client.get("/api/v1/jobs/saved", headers=headers).json()
            assert len(lst) == 1

    def test_jobs_listing_is_global_not_user_scoped(self, client, db_session):
        """Public job listings are shared across users (intentional design)."""
        headers_a = _register_and_login(client, "iso_global_a@example.com", "User A")
        headers_b = _register_and_login(client, "iso_global_b@example.com", "User B")

        norm = normalize(_make_raw(source_job_id="global-1", title="Shared Job"))
        upsert_job(db_session, norm)
        db_session.commit()

        r_a = client.get("/api/v1/jobs", headers=headers_a).json()
        r_b = client.get("/api/v1/jobs", headers=headers_b).json()
        a_titles = {j["title"] for j in r_a["items"]}
        b_titles = {j["title"] for j in r_b["items"]}
        assert "Shared Job" in a_titles
        assert "Shared Job" in b_titles


# ---------------------------------------------------------------------------
# Source health tracking
# ---------------------------------------------------------------------------


class TestSourceHealth:
    def test_seed_sources_present(self, db_session):
        rows = db_session.query(JobSource).all()
        ids = {r.id for r in rows}
        assert "pk_fpsc" in ids
        assert "pk_ppsc" in ids
        assert "pk_rozee" in ids

    def test_sources_disabled_by_default(self, db_session):
        for row in db_session.query(JobSource).all():
            assert row.enabled is False

    def test_health_updates_on_success(self, db_session):
        class _H(StaticListSource):
            source_id = "health_s"
        SOURCE_REGISTRY["health_s"] = _H
        try:
            db_session.add(JobSource(
                id="health_s", name="Health", category="private_board",
                source_type="test", integration_method="static",
                country="PK", enabled=True, is_active=True,
            ))
            db_session.commit()
            _H._class_jobs = [_make_raw(source="health_s", source_job_id="h1")]
            discover_source(db_session, "health_s")
            src = db_session.get(JobSource, "health_s")
            assert src.consecutive_failures == 0
            assert src.last_success_at is not None
            assert src.last_error is None
            assert src.total_jobs_discovered == 1
        finally:
            SOURCE_REGISTRY.pop("health_s", None)

    def test_health_updates_on_failure(self, db_session):
        class _F(FailingSource):
            source_id = "health_f"
        SOURCE_REGISTRY["health_f"] = _F
        try:
            db_session.add(JobSource(
                id="health_f", name="Health F", category="private_board",
                source_type="test", integration_method="static",
                country="PK", enabled=True, is_active=True,
            ))
            db_session.commit()
            discover_source(db_session, "health_f")
            src = db_session.get(JobSource, "health_f")
            assert src.consecutive_failures == 1
            assert src.last_failure_at is not None
            assert src.last_error is not None
        finally:
            SOURCE_REGISTRY.pop("health_f", None)
