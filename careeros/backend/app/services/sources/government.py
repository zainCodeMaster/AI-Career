"""Government source adapters for Pakistan public service commissions.

These adapters use public HTML page parsing — no authentication, no
API keys, no anti-bot bypass. They respect robots.txt and rate limits.

Sources implemented:
- FPSC (Federal Public Service Commission)
- PPSC (Punjab Public Service Commission)
- NJP (National Jobs Portal)
- PunjabJobs (Punjab Jobs Online)
- NTS (National Testing Service)
- PTS (Pakistan Testing Service)
- OTS (Open Testing Service)

Each adapter is independently testable and replaceable.
"""
from __future__ import annotations

import logging
from typing import Optional
from urllib.parse import urljoin, urlparse

from app.services.job_normalizer import RawJob
from app.services.job_sources import BaseJobSource, JobSourceError
from app.services.sources.html_parser import (
    clean_text,
    parse_date_flexible,
    parse_html,
)

logger = logging.getLogger("app.jobs")


class GovernmentSource(BaseJobSource):
    """Base class for Pakistan government job portals.

    Subclasses define:
    - ``source_id``: unique identifier
    - ``job_listing_url``: the public job listing page URL
    - ``job_detail_path``: CSS/XPath selectors for extracting job data

    All parsing is done from publicly accessible HTML pages.
    """

    category = "government"
    source_type = "government"
    integration_method = "public_page"
    country = "PK"

    # Subclasses must override
    job_listing_url: str = ""
    # CSS selector for individual job entries on the listing page
    job_list_item_selector: str = ""
    # CSS selector for the link to the job detail page (relative to list item)
    job_link_selector: str = ""

    def _extract_job_id(self, url: str) -> str:
        """Extract a stable identifier from a job URL."""
        path = urlparse(url).path
        return path.strip("/").replace("/", "_") or url

    def _fetch_listing_page(self) -> str:
        """Fetch the main job listing page HTML."""
        if not self.job_listing_url:
            raise JobSourceError(f"Source {self.source_id} has no job_listing_url configured")
        resp = self._get(self.job_listing_url)
        return resp.text

    def _fetch_detail_page(self, url: str) -> str:
        """Fetch an individual job detail page."""
        full_url = urljoin(self.job_listing_url, url)
        resp = self._get(full_url)
        return resp.text

    def fetch(self, *, max_results: int = 200, timeout: float = 20.0) -> list[RawJob]:
        """Fetch jobs from the government portal listing page."""
        try:
            html = self._fetch_listing_page()
        except JobSourceError:
            raise

        soup = parse_html(html)
        items = soup.select(self.job_list_item_selector)
        logger.info("Source %s: found %d job listings", self.source_id, len(items))

        jobs: list[RawJob] = []
        for item in items[:max_results]:
            try:
                link_elem = item.select_one(self.job_link_selector)
                if link_elem is None or link_elem.get("href") is None:
                    continue

                detail_url = link_elem["href"]
                full_url = urljoin(self.job_listing_url, detail_url)
                title = clean_text(link_elem.get_text())
                source_job_id = self._extract_job_id(full_url)

                # Fetch detail page for full description
                try:
                    detail_html = self._fetch_detail_page(detail_url)
                    detail_soup = parse_html(detail_html)
                    description = self._parse_detail_description(detail_soup)
                    location = self._parse_detail_location(detail_soup) or clean_text(item.get_text())
                    posted_at = self._parse_detail_posted_date(detail_soup)
                    closing_at = self._parse_detail_closing_date(detail_soup)
                    employment_type = self._parse_detail_employment_type(detail_soup)
                    skills = self._parse_detail_skills(detail_soup)
                except JobSourceError:
                    # Fall back to listing data only
                    description = None
                    location = clean_text(item.get_text())
                    posted_at = None
                    closing_at = None
                    employment_type = None
                    skills = None

                jobs.append(RawJob(
                    source=self.source_id,
                    source_job_id=source_job_id,
                    source_url=full_url,
                    title=title or "Untitled",
                    company_name=self._get_company_name(),
                    company_url=self.base_url,
                    description=description,
                    location=location,
                    employment_type=employment_type,
                    skills=skills,
                    posted_at=posted_at,
                    closing_at=closing_at,
                    is_remote=False,
                    is_pakistan_eligible=True,
                ))
            except Exception as exc:
                logger.warning("Source %s: failed to parse job item: %s", self.source_id, exc)
                continue

        return jobs

    def _get_company_name(self) -> str:
        """Return the company/organization name for this source."""
        return self.name.split("—")[-1].strip() if self.name else self.source_id

    def _parse_detail_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Override in subclass to extract description from detail page."""
        return None

    def _parse_detail_location(self, soup: BeautifulSoup) -> Optional[str]:
        """Override in subclass to extract location from detail page."""
        return None

    def _parse_detail_posted_date(self, soup: BeautifulSoup) -> Optional[object]:
        """Override in subclass to extract posted date from detail page."""
        return None

    def _parse_detail_closing_date(self, soup: BeautifulSoup) -> Optional[object]:
        """Override in subclass to extract application deadline from detail page."""
        return None

    def _parse_detail_employment_type(self, soup: BeautifulSoup) -> Optional[str]:
        """Override in subclass to extract employment type from detail page."""
        return None

    def _parse_detail_skills(self, soup: BeautifulSoup) -> Optional[str]:
        """Override in subclass to extract skills from detail page."""
        return None


# Lazy import to avoid circular dependency
from bs4 import BeautifulSoup  # noqa: E402


class FPSCSource(GovernmentSource):
    """Federal Public Service Commission — https://www.fpsc.gov.pk/

    Parses publicly accessible job listings from the FPSC website.
    No authentication required.
    """
    source_id = "pk_fpsc"
    name = "FPSC — Federal Public Service Commission"
    base_url = "https://www.fpsc.gov.pk/"
    job_listing_url = "https://www.fpsc.gov.pk/jobs"

    job_list_item_selector = ".view-id-latest_jobs .view-row, .job-listing-item, .view-row"
    job_link_selector = "a"


class PPSCSource(GovernmentSource):
    """Punjab Public Service Commission — https://www.ppsc.gop.pk/

    Parses publicly accessible job listings from the PPSC website.
    """
    source_id = "pk_ppsc"
    name = "PPSC — Punjab Public Service Commission"
    base_url = "https://www.ppsc.gop.pk/"
    job_listing_url = "https://www.ppsc.gop.pk/jobs"

    job_list_item_selector = ".view-id-job .view-row, .job-item, .listing-item"
    job_link_selector = "a"


class NTSSource(GovernmentSource):
    """National Testing Service — https://www.nts.org.pk/

    Parses publicly accessible job listings from the NTS website.
    """
    source_id = "pk_nts"
    name = "NTS — National Testing Service"
    base_url = "https://www.nts.org.pk/"
    job_listing_url = "https://www.nts.org.pk/jobs"

    job_list_item_selector = ".view-id-latest_jobs .view-row, .job-listing, .listing-item"
    job_link_selector = "a"


class PTSSource(GovernmentSource):
    """Pakistan Testing Service — https://pts.org.pk/

    Parses publicly accessible job listings from the PTS website.
    """
    source_id = "pk_pts"
    name = "PTS — Pakistan Testing Service"
    base_url = "https://pts.org.pk/"
    job_listing_url = "https://pts.org.pk/jobs"

    job_list_item_selector = ".view-id-latest_jobs .view-row, .job-listing, .listing-item"
    job_link_selector = "a"


class OTSSource(GovernmentSource):
    """Open Testing Service — https://ots.org.pk/

    Parses publicly accessible job listings from the OTS website.
    """
    source_id = "pk_ots"
    name = "OTS — Open Testing Service"
    base_url = "https://ots.org.pk/"
    job_listing_url = "https://ots.org.pk/jobs"

    job_list_item_selector = ".view-id-latest_jobs .view-row, .job-listing, .listing-item"
    job_link_selector = "a"


class NJPSource(GovernmentSource):
    """National Jobs Portal — https://njp.gov.pk/

    Parses publicly accessible job listings from the National Jobs Portal.
    """
    source_id = "pk_njp"
    name = "National Jobs Portal"
    base_url = "https://njp.gov.pk/"
    job_listing_url = "https://njp.gov.pk/jobs"

    job_list_item_selector = ".job-item, .view-row, .listing-item"
    job_link_selector = "a"


class PunjabJobsSource(GovernmentSource):
    """Punjab Jobs Online — https://jobs.punjab.gov.pk/

    Parses publicly accessible job listings from the Punjab government jobs portal.
    """
    source_id = "pk_punjab_jobs"
    name = "Punjab Jobs Online"
    base_url = "https://jobs.punjab.gov.pk/"
    job_listing_url = "https://jobs.punjab.gov.pk/"

    job_list_item_selector = ".job-item, .view-row, .listing-item, .row"
    job_link_selector = "a"
