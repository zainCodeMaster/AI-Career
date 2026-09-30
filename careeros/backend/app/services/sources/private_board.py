"""Private job board source adapters for Pakistan job boards.

These adapters use public page parsing or RSS feeds where available.
No authentication required. No API keys needed.

Sources implemented:
- Rozee.pk (public job listing pages)
- Mustakbil.com (public job listing pages)
- BrightSpyre.com (public job listing pages)

Each adapter respects rate limits and uses bounded request counts.
"""
from __future__ import annotations

import logging
from typing import Optional

from app.services.job_normalizer import RawJob
from app.services.job_sources import BaseJobSource, JobSourceError
from app.services.sources.html_parser import (
    clean_text,
    parse_date_flexible,
    parse_html,
)

logger = logging.getLogger("app.jobs")


class PrivateBoardSource(BaseJobSource):
    """Base class for private job board adapters."""

    category = "private_board"
    source_type = "private_board"
    integration_method = "public_page"
    country = "PK"

    # Subclasses override these
    job_listing_url: str = ""
    job_list_item_selector: str = ""
    job_link_selector: str = "a"
    max_pages: int = 3  # prevent infinite pagination

    def _extract_job_id(self, url: str) -> str:
        """Extract a stable identifier from a job URL."""
        return url.strip("/").split("/")[-1] or url

    def fetch(self, *, max_results: int = 200, timeout: float = 20.0) -> list[RawJob]:
        """Fetch jobs from the private job board.

        Iterates through paginated listing pages, capped at ``max_pages``
        and ``max_results`` to prevent runaway requests.
        """
        jobs: list[RawJob] = []
        results_per_page = 20
        total_pages = min(
            self.max_pages,
            max(1, (max_results + results_per_page - 1) // results_per_page),
        )

        for page_num in range(1, total_pages + 1):
            try:
                url = self._build_page_url(page_num) if page_num > 1 else self.job_listing_url
                resp = self._get(url, params=self._page_params(page_num))
                soup = parse_html(resp.text)
                items = soup.select(self.job_list_item_selector)

                if not items:
                    break

                for item in items:
                    if len(jobs) >= max_results:
                        break
                    try:
                        link = item.select_one(self.job_link_selector)
                        if link is None or not link.get("href"):
                            continue
                        href = link["href"]
                        # Normalize relative URLs
                        from urllib.parse import urljoin
                        full_url = urljoin(self.job_listing_url, href)
                        title = clean_text(link.get_text())
                        source_job_id = self._extract_job_id(full_url)

                        # Try to extract company from the listing item
                        company = self._extract_company(item) or self.name
                        location = self._extract_location(item)
                        posted_at = self._extract_posted_date(item)

                        jobs.append(RawJob(
                            source=self.source_id,
                            source_job_id=source_job_id,
                            source_url=full_url,
                            title=title or "Untitled",
                            company_name=company,
                            description=clean_text(item.get_text()),
                            location=location,
                            posted_at=posted_at,
                            is_remote=False,
                            is_pakistan_eligible=True,
                        ))
                    except Exception as exc:
                        logger.warning("Source %s: failed to parse job item: %s", self.source_id, exc)
                        continue
            except JobSourceError as exc:
                logger.warning("Source %s: page %d failed: %s", self.source_id, page_num, exc)
                break
            except Exception as exc:
                logger.warning("Source %s: unexpected error on page %d: %s", self.source_id, page_num, exc)
                break

        return jobs

    def _build_page_url(self, page: int) -> str:
        """Build the URL for a given page number. Override in subclass."""
        return f"{self.job_listing_url}?page={page}"

    def _page_params(self, page: int) -> Optional[dict]:
        """Return query params for pagination. Override in subclass."""
        return None

    def _extract_company(self, item) -> Optional[str]:
        """Extract company name from a job listing item. Override in subclass."""
        return None

    def _extract_location(self, item) -> Optional[str]:
        """Extract location from a job listing item. Override in subclass."""
        return None

    def _extract_posted_date(self, item) -> Optional[object]:
        """Extract posted date from a job listing item. Override in subclass."""
        return None


class RozeeSource(PrivateBoardSource):
    """Rozee.pk — Pakistan's largest job portal.

    Uses public job listing pages. No API key required.
    """
    source_id = "pk_rozee"
    name = "Rozee.pk"
    base_url = "https://www.rozee.pk/"
    job_listing_url = "https://www.rozee.pk/jobs"

    job_list_item_selector = ".job-listing, .campaign-job, .job-card, .job-item"
    job_link_selector = "a"


class MustakbilSource(PrivateBoardSource):
    """Mustakbil.com — Pakistan job board.

    Uses public job listing pages.
    """
    source_id = "pk_mustakbil"
    name = "Mustakbil"
    base_url = "https://www.mustakbil.com/"
    job_listing_url = "https://www.mustakbil.com/jobs"

    job_list_item_selector = ".job-listing, .job-card, .search-result"
    job_link_selector = "a"


class BrightSpyreSource(PrivateBoardSource):
    """BrightSpyre.com — Pakistan job board.

    Uses public job listing pages.
    """
    source_id = "pk_brightspyre"
    name = "BrightSpyre"
    base_url = "https://www.brightspyre.com/"
    job_listing_url = "https://www.brightspyre.com/jobs"

    job_list_item_selector = ".job-listing, .job-card, .search-result, .job-item"
    job_link_selector = "a"
