"""Integration tests for Phase 4.x — end-to-end discovery pipeline.

Tests the full flow:
  Source → Fetch → Normalize → Deduplicate → Database → Phase 5 Match
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.db.models.jobs import Job, JobExternalReference, JobSource
from app.services.job_discovery import discover_source, discover_all_enabled, upsert_job
from app.services.job_normalizer import NormalizedJob, RawJob, normalize
from app.services.job_sources import SOURCE_REGISTRY, StaticListSource, build_source
from app.services.match_engine import MatchEngine, PersonalizedRanker
from app.services.user_profile_aggregator import UserProfileAggregator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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
    )
    fields.update(overrides)
    return RawJob(**fields)


# ---------------------------------------------------------------------------
# Source → Fetch → Normalize → Deduplicate → DB pipeline
# ---------------------------------------------------------------------------


class TestDiscoveryPipeline:
    def test_full_pipeline_static_source(self, db_session, test_user):
        """Test: StaticListSource → fetch → normalize → upsert → DB."""
        # Register a test source
        class _PipelineSource(StaticListSource):
            source_id = "pipeline_test"
        SOURCE_REGISTRY["pipeline_test"] = _PipelineSource

        try:
            src_row = JobSource(
                id="pipeline_test", name="Pipeline Test", category="private_board",
                source_type="test", integration_method="static",
                country="PK", enabled=True, is_active=True,
            )
            db_session.add(src_row)
            db_session.commit()

            # Populate source jobs
            _PipelineSource._class_jobs = [
                _make_raw(source="pipeline_test", source_job_id="j1", title="Job One"),
                _make_raw(source="pipeline_test", source_job_id="j2", title="Job Two"),
            ]

            # Run discovery
            from app.services.job_discovery import discover_source
            result = discover_source(db_session, "pipeline_test")

            assert result.error is None
            assert len(result.jobs) == 2

            # Verify jobs are in DB
            jobs = db_session.query(Job).filter(Job.source == "pipeline_test").all()
            assert len(jobs) == 2
            titles = {j.title for j in jobs}
            assert titles == {"Job One", "Job Two"}

            # Verify external references
            refs = db_session.query(JobExternalReference).filter(
                JobExternalReference.source_id == "pipeline_test"
            ).all()
            assert len(refs) == 2

            # Verify discovery run was logged
            from app.db.models.jobs import JobDiscoveryRun
            run = db_session.query(JobDiscoveryRun).filter(
                JobDiscoveryRun.source_id == "pipeline_test"
            ).order_by(JobDiscoveryRun.started_at.desc()).first()
            assert run is not None
            assert run.status == "success"
            assert run.jobs_created == 2
        finally:
            SOURCE_REGISTRY.pop("pipeline_test", None)

    def test_pipeline_no_duplicates_on_rerun(self, db_session, test_user):
        """Running discovery twice should not create duplicate jobs."""
        class _DedupSource(StaticListSource):
            source_id = "dedup_test"
        SOURCE_REGISTRY["dedup_test"] = _DedupSource

        try:
            db_session.add(JobSource(
                id="dedup_test", name="Dedup Test", category="private_board",
                source_type="test", integration_method="static",
                country="PK", enabled=True, is_active=True,
            ))
            db_session.commit()

            _DedupSource._class_jobs = [
                _make_raw(source="dedup_test", source_job_id="d1", title="Job D"),
            ]

            # First run
            discover_source(db_session, "dedup_test")
            count_after_first = db_session.query(Job).filter(Job.source == "dedup_test").count()
            assert count_after_first == 1

            # Second run — should update, not create
            discover_source(db_session, "dedup_test")
            count_after_second = db_session.query(Job).filter(Job.source == "dedup_test").count()
            assert count_after_second == 1  # Still 1, not 2

            # Verify external reference was updated, not duplicated
            refs = db_session.query(JobExternalReference).filter(
                JobExternalReference.source_id == "dedup_test"
            ).all()
            assert len(refs) == 1
        finally:
            SOURCE_REGISTRY.pop("dedup_test", None)

    def test_pipeline_cross_source_dedup(self, db_session):
        """Same job from different sources should be deduplicated."""
        class _SrcA(StaticListSource):
            source_id = "cross_a"
        class _SrcB(StaticListSource):
            source_id = "cross_b"
        SOURCE_REGISTRY["cross_a"] = _SrcA
        SOURCE_REGISTRY["cross_b"] = _SrcB

        try:
            db_session.add(JobSource(
                id="cross_a", name="Cross A", category="private_board",
                source_type="test", integration_method="static",
                country="PK", enabled=True, is_active=True,
            ))
            db_session.add(JobSource(
                id="cross_b", name="Cross B", category="private_board",
                source_type="test", integration_method="static",
                country="PK", enabled=True, is_active=True,
            ))
            db_session.commit()

            # Same title + company + location → should dedup across sources
            _SrcA._class_jobs = [_make_raw(
                source="cross_a", source_job_id="xa1",
                title="Shared Engineer", company="SharedCorp", location="Lahore, Punjab",
            )]
            _SrcB._class_jobs = [_make_raw(
                source="cross_b", source_job_id="xb1",
                title="Shared Engineer", company="SharedCorp", location="Lahore, Punjab",
            )]

            discover_source(db_session, "cross_a")
            discover_source(db_session, "cross_b")

            total = db_session.query(Job).filter(
                Job.source.in_(["cross_a", "cross_b"])
            ).count()
            assert total == 1  # Deduplicated

            # External references should track both sources
            refs = db_session.query(JobExternalReference).filter(
                JobExternalReference.job_id == db_session.query(Job).first().id
            ).all()
            assert len(refs) == 2
        finally:
            SOURCE_REGISTRY.pop("cross_a", None)
            SOURCE_REGISTRY.pop("cross_b", None)

    def test_pipeline_failure_isolation(self, db_session):
        """A failing source should not crash the discovery run."""
        from app.services.job_sources import FailingSource

        class _FailSource(FailingSource):
            source_id = "iso_fail"
        SOURCE_REGISTRY["iso_fail"] = _FailSource

        try:
            db_session.add(JobSource(
                id="iso_fail", name="Fail Test", category="private_board",
                source_type="test", integration_method="static",
                country="PK", enabled=True, is_active=True,
            ))
            db_session.commit()

            # Failing source should return error but not crash
            result = discover_source(db_session, "iso_fail")
            assert result.error is not None

            # Verify failure was logged in source health
            src = db_session.get(JobSource, "iso_fail")
            assert src.consecutive_failures == 1
            assert src.last_error is not None
        finally:
            SOURCE_REGISTRY.pop("iso_fail", None)


# ---------------------------------------------------------------------------
# End-to-end: Source → Discovery → Matching
# ---------------------------------------------------------------------------


class TestEndToEndDiscoveryToMatching:
    def test_discovered_jobs_flow_into_matching(self, client, db_session):
        """Verified that real discovered jobs work with Phase 5 matching."""
        headers = _register_and_login(client, "e2e_match@example.com")

        # Create a static source with a job
        class _E2ESource(StaticListSource):
            source_id = "e2e_match_src"
        SOURCE_REGISTRY["e2e_match_src"] = _E2ESource

        try:
            db_session.add(JobSource(
                id="e2e_match_src", name="E2E Match", category="private_board",
                source_type="test", integration_method="static",
                country="PK", enabled=True, is_active=True,
            ))
            db_session.commit()

            _E2ESource._class_jobs = [_make_raw(
                source="e2e_match_src", source_job_id="m1",
                title="Python Developer",
                company="TechCorp",
                location="Lahore, Punjab",
                skills="python, django, postgresql",
                description="Python developer role with Django experience.",
                employment_type="full_time",
                experience_min=3,
                experience_max=5,
            )]

            # Run discovery
            result = discover_source(db_session, "e2e_match_src")
            assert result.error is None

            # Get the discovered job
            job = db_session.query(Job).filter(Job.source == "e2e_match_src").first()
            assert job is not None

            # Now use the Phase 5 matching endpoint
            r = client.get(f"/api/v1/jobs/{job.id}/match", headers=headers)
            assert r.status_code == 200
            match_data = r.json()
            assert "overall_score" in match_data
            assert 0 <= match_data["overall_score"] <= 100
            assert "breakdown" in match_data
            assert "explanation" in match_data
            assert "profile_completeness" in match_data
        finally:
            SOURCE_REGISTRY.pop("e2e_match_src", None)

    def test_discovered_jobs_appear_in_job_feed(self, client, db_session):
        """Discovered jobs should appear in the job listing endpoint."""
        headers = _register_and_login(client, "e2e_feed@example.com")

        class _E2EFeedSource(StaticListSource):
            source_id = "e2e_feed_src"
        SOURCE_REGISTRY["e2e_feed_src"] = _E2EFeedSource

        try:
            db_session.add(JobSource(
                id="e2e_feed_src", name="E2E Feed", category="private_board",
                source_type="test", integration_method="static",
                country="PK", enabled=True, is_active=True,
            ))
            db_session.commit()

            _E2EFeedSource._class_jobs = [_make_raw(
                source="e2e_feed_src", source_job_id="f1",
                title="Data Engineer",
                company="DataCo",
                location="Karachi, Sindh",
            )]

            discover_source(db_session, "e2e_feed_src")

            # Verify the job appears in the jobs listing
            r = client.get("/api/v1/jobs", headers=headers)
            data = r.json()
            titles = {j["title"] for j in data["items"]}
            assert "Data Engineer" in titles
        finally:
            SOURCE_REGISTRY.pop("e2e_feed_src", None)


# ---------------------------------------------------------------------------
# Date/salary parsing integration
# ---------------------------------------------------------------------------


class TestParsingIntegration:
    def test_date_parsing_from_source(self, db_session):
        """Verify that dates from sources are properly parsed and stored."""
        posted = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        closing = datetime(2024, 2, 15, 10, 0, 0, tzinfo=timezone.utc)

        raw = RawJob(
            source="test_date",
            source_job_id="d1",
            title="Date Test Job",
            company_name="DateCorp",
            posted_at=posted,
            closing_at=closing,
        )
        norm = normalize(raw)
        job, created = upsert_job(db_session, norm)
        db_session.commit()

        fetched = db_session.get(Job, job.id)
        # SQLite strips timezone info; compare naive values
        assert fetched.posted_at.replace(tzinfo=None) == posted.replace(tzinfo=None)
        assert fetched.closing_at.replace(tzinfo=None) == closing.replace(tzinfo=None)

    def test_salary_parsing_from_text(self, db_session):
        """Verify salary is parsed from description text when explicit fields absent."""
        raw = RawJob(
            source="test_salary",
            source_job_id="s1",
            title="Salary Test Job",
            company_name="SalaryCorp",
            description="PKR 80,000 - 120,000 monthly salary",
        )
        norm = normalize(raw)
        assert norm.salary_min == 80000.0
        assert norm.salary_max == 120000.0
        assert norm.salary_currency == "PKR"
        assert norm.salary_period == "monthly"

    def test_missing_fields_stay_null(self, db_session):
        """Verify that unknown values remain null — no invented data."""
        raw = RawJob(
            source="test_null",
            source_job_id="n1",
            title="Null Test",
            company_name="NullCorp",
        )
        norm = normalize(raw)
        assert norm.location is None
        assert norm.city is None
        assert norm.province is None
        assert norm.salary_min is None
        assert norm.experience_min is None
        assert norm.posted_at is None
        assert norm.closing_at is None

    def test_employment_type_mapping(self, db_session):
        """Verify employment type mapping works from source data."""
        raw = RawJob(
            source="test_et",
            source_job_id="et1",
            title="ET Test",
            company_name="ETCorp",
            employment_type="Full-Time",
        )
        norm = normalize(raw)
        assert norm.employment_type == "full_time"

    def test_workplace_type_detection(self, db_session):
        """Verify workplace type detection from location/description."""
        raw = RawJob(
            source="test_wt",
            source_job_id="wt1",
            title="Remote Test",
            company_name="RemoteCorp",
            location="Remote - Pakistan",
        )
        norm = normalize(raw)
        assert norm.workplace_type == "remote"
        assert norm.is_remote is True


# ---------------------------------------------------------------------------
# Helper for registration (reused from test_jobs.py pattern)
# ---------------------------------------------------------------------------


def _register(client, email, full_name="Test User"):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123", "full_name": full_name},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _login(client, email):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPass123"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _register_and_login(client, email, full_name="Test User"):
    _register(client, email, full_name)
    token = _login(client, email)
    return _headers(token)
