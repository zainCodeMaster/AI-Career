"""JobSource abstraction and base adapter framework.

A ``JobSource`` represents a single integration with a job board,
government portal, company career page, or remote aggregator.

Sources are pluggable: each adapter implements ``fetch()`` and returns
``list[RawJob]``. The ``JobDiscoveryEngine`` orchestrates all enabled
sources, normalizes their output, deduplicates, and persists results.

This module also ships a small ``StaticListSource`` (deterministic, no
network) so the discovery engine and API can be exercised in tests without
attempting to scrape or contact external systems.
"""
from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable, Optional

import httpx

from app.core.config import get_settings
from app.services.job_normalizer import RawJob

logger = logging.getLogger("app.jobs")


class JobSourceError(Exception):
    """Raised when a job source fails to fetch or parse data."""


@dataclass
class SourceFetchResult:
    """Outcome of a single ``fetch()`` call."""

    source_id: str
    jobs: list[RawJob]
    error: Optional[str] = None


class BaseJobSource(ABC):
    """Abstract base for all job source adapters."""

    source_id: str = ""
    category: str = ""
    integration_method: str = ""

    # Source-specific defaults; subclasses may override.
    base_url: Optional[str] = None
    user_agent: str = "CareerOS-Bot/1.0 (+https://careeros.local/bot)"
    request_timeout: float = 20.0
    max_retries: int = 2
    retry_backoff: float = 1.0
    request_delay: float = 1.0

    @abstractmethod
    def fetch(self, *, max_results: int = 200, timeout: float = 20.0) -> list[RawJob]:
        """Fetch raw jobs from this source.

        Implementations should respect the provided ``max_results`` cap and
        ``timeout`` hint. They MUST NOT bypass anti-bot protections,
        CAPTCHAs, or rate limits. They MUST NOT fabricate data.
        """

    def is_connected(self) -> bool:
        """Optional liveness check. Default returns True."""
        return True

    # ------------------------------------------------------------------
    # HTTP helper methods — shared across all network-based adapters.
    # These provide bounded retries with exponential backoff, request
    # timeouts, and a configurable delay between requests to avoid
    # overwhelming the source.
    # ------------------------------------------------------------------

    def _get(self, url: str, *, params: Optional[dict] = None) -> httpx.Response:
        """Perform an HTTP GET with retry/backoff.

        Respects ``request_timeout``, ``max_retries``, ``retry_backoff``,
        and ``request_delay``. Raises ``JobSourceError`` on persistent
        failure.
        """
        settings = get_settings()
        headers = {"User-Agent": self.user_agent}
        delay = self.request_delay
        last_exc: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            if attempt > 0:
                backoff = self.retry_backoff * (2 ** (attempt - 1))
                logger.warning(
                    "Source %s: retry %d/%d after %ss delay",
                    self.source_id, attempt, self.max_retries, backoff,
                )
                time.sleep(backoff)

            try:
                time.sleep(delay)
                resp = httpx.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.request_timeout,
                    follow_redirects=True,
                )
                if resp.status_code == 429:
                    logger.warning("Source %s: rate-limited (429)", self.source_id)
                    raise JobSourceError(f"Source {self.source_id} returned 429 rate limit")
                resp.raise_for_status()
                return resp
            except httpx.HTTPStatusError as exc:
                if exc.response is not None and 400 <= exc.response.status_code < 500:
                    # Client error (4xx): don't retry
                    raise JobSourceError(
                        f"Source {self.source_id} returned {exc.response.status_code}: {exc.response.text[:200]}"
                    ) from exc
                last_exc = exc
            except (httpx.TimeoutException, httpx.ConnectError, httpx.RequestError) as exc:
                last_exc = exc
                logger.warning("Source %s: request error: %s", self.source_id, exc)

        raise JobSourceError(
            f"Source {self.source_id} failed after {self.max_retries + 1} attempts: {last_exc}"
        ) from last_exc


# Backwards-compatible alias: the prompt names the abstract class ``JobSource``.
JobSource = BaseJobSource


# ---------------------------------------------------------------------------
# Real source adapters (imported here to populate the registry)
# ---------------------------------------------------------------------------

# Government sources
from app.services.sources.government import (  # noqa: E402
    FPSCSource,
    NJPSource,
    NTSSource,
    OTSSource,
    PPSCSource,
    PTSSource,
    PunjabJobsSource,
)

# Private board sources
from app.services.sources.private_board import (  # noqa: E402
    BrightSpyreSource,
    MustakbilSource,
    RozeeSource,
)

# Company career page source
from app.services.sources.company_career import CompanyCareerSource  # noqa: E402

# International remote sources
from app.services.sources.international import (  # noqa: E402
    HimalayasSource,
    RemoteOKSource,
)

# Unsupported sources (LinkedIn, Indeed, Google Jobs)
from app.services.sources.unsupported import (  # noqa: E402
    GoogleJobsSource,
    IndeedSource,
    LinkedInSource,
    RemoteGenericSource,
    UnsupportedSource,
)


class StaticListSource(BaseJobSource):
    """Deterministic offline source used for tests and demos.

    Accepts a pre-built list of ``RawJob`` objects and returns it from
    ``fetch()``. This is the canonical way to test the discovery pipeline
    end-to-end without contacting any external system.
    """

    source_id = "static_list"
    category = "private_board"
    integration_method = "static"

    # Class-level storage so tests can populate jobs on the class and the
    # discovery engine will see them on each freshly-constructed instance.
    _class_jobs: list[RawJob] = []

    def __init__(self, jobs: Optional[Iterable[RawJob]] = None) -> None:
        if jobs is not None:
            self._jobs: list[RawJob] = list(jobs)
        else:
            self._jobs = list(type(self)._class_jobs)

    def set_jobs(self, jobs: Iterable[RawJob]) -> None:
        self._jobs = list(jobs)

    def fetch(self, *, max_results: int = 200, timeout: float = 20.0) -> list[RawJob]:
        return list(self._jobs[:max_results])


class FailingSource(BaseJobSource):
    """Source that always raises. Used in tests for failure handling."""

    source_id = "failing_source"
    category = "private_board"
    integration_method = "test"

    def __init__(self, message: str = "intentional test failure") -> None:
        self._message = message

    def fetch(self, *, max_results: int = 200, timeout: float = 20.0) -> list[RawJob]:
        raise JobSourceError(self._message)


# ---------------------------------------------------------------------------
# Source registry
# ---------------------------------------------------------------------------


# Map of source_id -> JobSource subclass. The discovery engine instantiates
# these per-run. The mapping is intentionally pluggable so the project can
# register adapters without modifying this file.
SOURCE_REGISTRY: dict[str, type[BaseJobSource]] = {
    # Test/deterministic sources
    "static_list": StaticListSource,
    "failing_source": FailingSource,
    # Government sources (Tier 1)
    "pk_fpsc": FPSCSource,
    "pk_ppsc": PPSCSource,
    "pk_nts": NTSSource,
    "pk_pts": PTSSource,
    "pk_ots": OTSSource,
    "pk_njp": NJPSource,
    "pk_punjab_jobs": PunjabJobsSource,
    # Private job boards (Tier 2)
    "pk_rozee": RozeeSource,
    "pk_mustakbil": MustakbilSource,
    "pk_brightspyre": BrightSpyreSource,
    # International remote sources
    "remote_ok": RemoteOKSource,
    "himalayas": HimalayasSource,
    # Company career pages
    "company_template": CompanyCareerSource,
    # Unsupported sources (no authorized integration)
    "linkedin_pk": LinkedInSource,
    "indeed_pk": IndeedSource,
    "google_jobs": GoogleJobsSource,
    "remote_generic": RemoteGenericSource,
}


def build_source(source_id: str, **kwargs) -> BaseJobSource:
    """Instantiate a source by id from the registry."""
    cls = SOURCE_REGISTRY.get(source_id)
    if cls is None:
        raise KeyError(f"Unknown job source: {source_id}")
    return cls(**kwargs)
