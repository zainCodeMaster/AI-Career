"""Unsupported source stubs.

These sources are registered in the job_sources table for completeness
but have no working adapter. They exist so the system can report their
status accurately.

LinkedIn, Indeed, and Google Jobs all have terms of service that prohibit
unauthorized scraping. CareerOS does NOT implement any scraping or
anti-bot bypass for these sources.

Future authorized integrations (e.g., official APIs with proper credentials)
can be added later by replacing these stubs with real adapters.
"""
from __future__ import annotations

from app.services.job_sources import BaseJobSource, JobSourceError


class UnsupportedSource(BaseJobSource):
    """Source that is registered but not supported.

    Used for sources where legitimate integration is unavailable.
    """

    source_id = "unsupported"
    category = "private_board"
    integration_method = "unsupported"
    source_type = "unsupported"
    reason: str = "No authorized integration configured"

    def fetch(self, *, max_results: int = 200, timeout: float = 20.0) -> list:
        raise JobSourceError(
            f"Source {self.source_id} is unsupported: {self.reason}"
        )


class LinkedInSource(UnsupportedSource):
    """LinkedIn — no authorized integration.

    LinkedIn's Terms of Service prohibit scraping. We do NOT implement
    any scraping, anti-bot bypass, or unauthorized API access.
    """
    source_id = "linkedin_pk"
    name = "LinkedIn — Pakistan"
    reason = "No authorized integration configured. LinkedIn ToS prohibits scraping."


class IndeedSource(UnsupportedSource):
    """Indeed — no authorized integration.

    Indeed blocks automated access in its ToS. We do NOT implement
    any scraping or anti-bot bypass.
    """
    source_id = "indeed_pk"
    name = "Indeed — Pakistan"
    reason = "No authorized integration configured. Indeed ToS prohibits scraping."


class GoogleJobsSource(UnsupportedSource):
    """Google Jobs — no authorized integration.

    Google Jobs has no public API for job listings. We do NOT implement
    any scraping of Google search results.
    """
    source_id = "google_jobs"
    name = "Google Jobs"
    reason = "No authorized integration configured. Google Jobs has no public API."


class RemoteGenericSource(UnsupportedSource):
    """Generic remote jobs — no dedicated integration configured."""
    source_id = "remote_generic"
    name = "Generic Remote Jobs"
    reason = "No remote job aggregator integration configured."
