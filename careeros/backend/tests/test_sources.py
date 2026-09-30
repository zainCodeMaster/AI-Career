"""Tests for source adapters: parsing, normalization, error handling, dedup."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import pytest

from app.services.sources.html_parser import clean_text, parse_date_flexible, parse_html
from app.services.job_normalizer import NormalizedJob, RawJob, normalize
from app.services.job_sources import (
    SOURCE_REGISTRY,
    BaseJobSource,
    FailingSource,
    JobSourceError,
    StaticListSource,
    build_source,
)
from app.services.sources.unsupported import UnsupportedSource


# ---------------------------------------------------------------------------
# HTML parser utility tests
# ---------------------------------------------------------------------------


class TestHTMLParser:
    def test_clean_text_strips_and_collapses(self):
        assert clean_text("  hello   world  ") == "hello world"

    def test_clean_text_none(self):
        assert clean_text(None) is None

    def test_clean_text_empty(self):
        assert clean_text("") is None
        assert clean_text("   ") is None

    def test_parse_html(self):
        soup = parse_html("<div class='job'>Job A</div>")
        assert soup.find("div", class_="job").text == "Job A"

    def test_parse_date_flexible_formats(self):
        assert parse_date_flexible("15 Jan 2024") is not None
        assert parse_date_flexible("2024-01-15") is not None
        assert parse_date_flexible("January 15, 2024") is not None
        assert parse_date_flexible("15/01/2024") is not None

    def test_parse_date_flexible_none(self):
        assert parse_date_flexible(None) is None
        assert parse_date_flexible("") is None

    def test_parse_date_flexible_invalid(self):
        assert parse_date_flexible("not a date") is None


# ---------------------------------------------------------------------------
# Source registry tests
# ---------------------------------------------------------------------------


class TestSourceRegistry:
    def test_all_real_sources_registered(self):
        """All expected real sources must be in the registry."""
        expected = {
            "pk_fpsc", "pk_ppsc", "pk_nts", "pk_pts", "pk_ots",
            "pk_njp", "pk_punjab_jobs",
            "pk_rozee", "pk_mustakbil", "pk_brightspyre",
            "company_template",
            "linkedin_pk", "indeed_pk", "google_jobs",
            "static_list", "failing_source",
        }
        assert expected.issubset(set(SOURCE_REGISTRY.keys()))

    def test_government_sources_have_correct_category(self):
        from app.services.sources.government import FPSCSource, PPSCSource
        assert FPSCSource.category == "government"
        assert PPSCSource.category == "government"
        assert FPSCSource.integration_method == "public_page"

    def test_private_board_sources_have_correct_category(self):
        from app.services.sources.private_board import RozeeSource, MustakbilSource
        assert RozeeSource.category == "private_board"
        assert MustakbilSource.category == "private_board"

    def test_unsupported_sources_raise_on_fetch(self):
        src = build_source("linkedin_pk")
        assert src.integration_method == "unsupported"
        with pytest.raises(JobSourceError):
            src.fetch()

    def test_unsupported_source_reason_is_set(self):
        from app.services.sources.unsupported import LinkedInSource, IndeedSource
        linkedin = LinkedInSource()
        assert linkedin.reason is not None
        assert "authorized" in linkedin.reason.lower() or "tos" in linkedin.reason.lower()
        indeed = IndeedSource()
        assert indeed.reason is not None

    def test_company_career_source_configurable(self):
        from app.services.sources.company_career import CompanyCareerSource
        src = CompanyCareerSource()
        assert src.category == "company_career"
        assert src.integration_method == "json_ld"

    def test_build_source_creates_correct_type(self):
        src = build_source("pk_fpsc")
        from app.services.sources.government import FPSCSource
        assert isinstance(src, FPSCSource)
        assert isinstance(src, BaseJobSource)


# ---------------------------------------------------------------------------
# Government source adapter tests
# ---------------------------------------------------------------------------


class TestGovernmentSources:
    def test_fpsc_source_metadata(self):
        src = build_source("pk_fpsc")
        assert src.source_id == "pk_fpsc"
        assert "FPSC" in src.name
        assert src.country == "PK"
        assert src.job_listing_url.startswith("https://")

    def test_ppsc_source_metadata(self):
        src = build_source("pk_ppsc")
        assert src.source_id == "pk_ppsc"
        assert "PPSC" in src.name

    def test_nts_source_metadata(self):
        src = build_source("pk_nts")
        assert src.source_id == "pk_nts"

    def test_pts_source_metadata(self):
        src = build_source("pk_pts")
        assert src.source_id == "pk_pts"

    def test_ots_source_metadata(self):
        src = build_source("pk_ots")
        assert src.source_id == "pk_ots"

    def test_njp_source_metadata(self):
        src = build_source("pk_njp")
        assert src.source_id == "pk_njp"

    def test_punjab_jobs_source_metadata(self):
        src = build_source("pk_punjab_jobs")
        assert src.source_id == "pk_punjab_jobs"

    def test_government_source_has_request_defaults(self):
        src = build_source("pk_fpsc")
        assert src.request_timeout > 0
        assert src.max_retries >= 0
        assert src.request_delay > 0

    def test_government_source_extract_job_id_from_url(self):
        from app.services.sources.government import FPSCSource
        src = FPSCSource()
        job_id = src._extract_job_id("https://example.com/jobs/detail/123")
        assert "123" in job_id


# ---------------------------------------------------------------------------
# Private board source adapter tests
# ---------------------------------------------------------------------------


class TestPrivateBoardSources:
    def test_rozee_source_metadata(self):
        src = build_source("pk_rozee")
        assert src.source_id == "pk_rozee"
        assert src.name == "Rozee.pk"
        assert src.base_url.startswith("https://")

    def test_rozee_has_pagination_limit(self):
        src = build_source("pk_rozee")
        assert src.max_pages > 0

    def test_mustakbil_source_metadata(self):
        src = build_source("pk_mustakbil")
        assert src.source_id == "pk_mustakbil"

    def test_brightspyre_source_metadata(self):
        src = build_source("pk_brightspyre")
        assert src.source_id == "pk_brightspyre"


# ---------------------------------------------------------------------------
# Company career source tests (JSON-LD parsing)
# ---------------------------------------------------------------------------


class TestCompanyCareerSource:
    def test_jsonld_extraction(self):
        from app.services.sources.company_career import CompanyCareerSource

        class TestCompanySource(CompanyCareerSource):
            source_id = "test_company"
            name = "Test Company"
            career_page_url = "https://test.com/careers"

        src = TestCompanySource()

        html = """
        <html><head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org/",
            "@type": "JobPosting",
            "title": "Senior Backend Engineer",
            "hiringOrganization": {"name": "Test Corp"},
            "jobLocation": {
                "address": {
                    "addressLocality": "Lahore",
                    "addressRegion": "Punjab",
                    "addressCountry": "PK"
                }
            },
            "datePosted": "2024-01-15",
            "validThrough": "2024-02-15",
            "employmentType": "FULL_TIME",
            "description": "We are looking for a Senior Backend Engineer.",
            "identifier": {"name": "Test Corp", "value": "job-123"},
            "url": "https://test.com/careers/job-123"
        }
        </script>
        </head><body></body></html>
        """
        from app.services.sources.html_parser import parse_html
        soup = parse_html(html)
        postings = src._extract_job_postings_from_jsonld(soup)
        assert len(postings) == 1
        assert postings[0]["title"] == "Senior Backend Engineer"
        assert postings[0]["hiringOrganization"]["name"] == "Test Corp"

    def test_jsonld_multiple_postings(self):
        from app.services.sources.company_career import CompanyCareerSource

        class TestCompanySource(CompanyCareerSource):
            source_id = "test_multi"
            name = "Test Multi"
            career_page_url = "https://test.com/careers"

        src = TestCompanySource()

        html = """
        <html><head>
        <script type="application/ld+json">
        [{"@type": "JobPosting", "title": "Job 1", "hiringOrganization": {"name": "Corp"}},
        {"@type": "JobPosting", "title": "Job 2", "hiringOrganization": {"name": "Corp"}}]
        </script>
        </head></html>
        """
        from app.services.sources.html_parser import parse_html
        soup = parse_html(html)
        postings = src._extract_job_postings_from_jsonld(soup)
        assert len(postings) == 2

    def test_jsonld_invalid_json_ignored(self):
        from app.services.sources.company_career import CompanyCareerSource

        class TestCompanySource(CompanyCareerSource):
            source_id = "test_invalid"
            name = "Test Invalid"
            career_page_url = "https://test.com/careers"

        src = TestCompanySource()

        html = """
        <html><head>
        <script type="application/ld+json">not valid json {{{</script>
        </head></html>
        """
        from app.services.sources.html_parser import parse_html
        soup = parse_html(html)
        postings = src._extract_job_postings_from_jsonld(soup)
        assert len(postings) == 0

    def test_jsonld_to_rawjob_conversion(self):
        from app.services.sources.company_career import CompanyCareerSource

        class TestCompanySource(CompanyCareerSource):
            source_id = "test_conv"
            name = "Test Conv"
            career_page_url = "https://test.com/careers"

        src = TestCompanySource()

        posting = {
            "@type": "JobPosting",
            "title": "Developer",
            "hiringOrganization": {"name": "DevCorp"},
            "jobLocation": {
                "address": {
                    "addressLocality": "Karachi",
                    "addressRegion": "Sindh",
                }
            },
            "datePosted": "2024-01-15",
            "validThrough": "2024-02-15",
            "employmentType": "FULL_TIME",
            "description": "Build things",
            "identifier": {"name": "DevCorp", "value": "job-456"},
            "url": "https://test.com/careers/job-456",
        }

        raw = src._jsonld_to_rawjob(posting, "https://test.com/careers")
        assert raw is not None
        assert raw.title == "Developer"
        assert raw.company_name == "DevCorp"
        assert raw.location == "Karachi, Sindh"
        assert raw.posted_at is not None
        assert raw.closing_at is not None
        assert raw.employment_type == "full_time"


# ---------------------------------------------------------------------------
# Unsupported source tests
# ---------------------------------------------------------------------------


class TestUnsupportedSources:
    def test_linkedin_is_unsupported(self):
        src = build_source("linkedin_pk")
        assert src.integration_method == "unsupported"
        with pytest.raises(JobSourceError):
            src.fetch()

    def test_indeed_is_unsupported(self):
        src = build_source("indeed_pk")
        assert src.integration_method == "unsupported"

    def test_google_jobs_is_unsupported(self):
        src = build_source("google_jobs")
        assert src.integration_method == "unsupported"

    def test_remote_generic_is_unsupported(self):
        src = build_source("remote_generic")
        assert src.integration_method == "unsupported"


# ---------------------------------------------------------------------------
# RawJob normalization tests for source data
# ---------------------------------------------------------------------------


class TestSourceRawJobNormalization:
    def test_raw_job_defaults(self):
        raw = RawJob(source="test", source_job_id="1", title="Engineer")
        assert raw.source == "test"
        assert raw.source_job_id == "1"
        assert raw.is_pakistan_eligible is True
        assert raw.is_remote is False
        assert raw.skills is None
        assert raw.extra == {}

    def test_normalize_preserves_source_identity(self):
        raw = RawJob(
            source="pk_fpsc",
            source_job_id="adv-2024-001",
            title="Assistant Director",
            company_name="Government of Pakistan",
            location="Islamabad, ICT",
        )
        norm = normalize(raw)
        assert norm.source == "pk_fpsc"
        assert norm.source_job_id == "adv-2024-001"
        assert norm.country == "PK"

    def test_normalize_does_not_invent_company(self):
        raw = RawJob(source="test", source_job_id="1", title="Job")
        norm = normalize(raw)
        assert norm.company_name == ""

    def test_normalize_handles_missing_location(self):
        raw = RawJob(source="test", source_job_id="1", title="Job", company_name="Corp")
        norm = normalize(raw)
        assert norm.location is None
        assert norm.city is None
        assert norm.province is None

    def test_normalize_hash_is_stable(self):
        raw = RawJob(
            source="test", source_job_id="1", title="Engineer",
            company_name="Corp", location="Lahore",
        )
        h1 = normalize(raw).content_hash
        h2 = normalize(raw).content_hash
        assert h1 == h2
