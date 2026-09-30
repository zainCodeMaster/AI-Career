"""Automatic job discovery scheduler.

Uses APScheduler to run discovery on a configurable interval. The scheduler
is started during application startup (if enabled) and shut down on exit.

Configuration:
- ``job_discovery_scheduler_enabled``: Enable/disable automatic discovery (bool)
- ``job_discovery_interval_minutes``: Interval between discovery runs (int)

The scheduler runs ``job_discovery.discover_all_enabled`` in a background
thread. It uses its own database session per run to avoid conflicts with
request-time sessions.

Safety:
- If a run is already in progress, a new run is skipped (duplicate prevention)
- Source failures are caught and logged, never crash the scheduler
- The scheduler is only started in the main process (not in test workers)
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.database import SessionLocal
from app.services import job_discovery

logger = logging.getLogger("app.scheduler")


class DiscoveryScheduler:
    """Manages scheduled automatic job discovery.

    Usage:
        scheduler = DiscoveryScheduler()
        scheduler.start()  # starts background scheduler
        ...
        scheduler.shutdown()  # stops scheduler
    """

    def __init__(self) -> None:
        self._scheduler: Optional[BackgroundScheduler] = None
        self._running: bool = False
        self._settings = get_settings()

    @property
    def is_enabled(self) -> bool:
        return self._settings.job_discovery_scheduler_enabled

    @property
    def interval_minutes(self) -> int:
        return self._settings.job_discovery_interval_minutes

    @property
    def running(self) -> bool:
        return self._running

    def start(self) -> None:
        """Start the background scheduler if enabled."""
        if not self.is_enabled:
            logger.info("Discovery scheduler is disabled (job_discovery_scheduler_enabled=false)")
            return

        if self._scheduler is not None:
            logger.warning("Discovery scheduler already started")
            return

        self._scheduler = BackgroundScheduler(
            timezone="UTC",
            daemon=True,
        )

        # Register event listeners for observability
        self._scheduler.add_listener(self._on_job_executed, EVENT_JOB_EXECUTED)
        self._scheduler.add_listener(self._on_job_error, EVENT_JOB_ERROR)
        self._scheduler.add_listener(self._on_job_missed, EVENT_JOB_MISSED)

        # Schedule the discovery job
        self._scheduler.add_job(
            func=self._run_discovery,
            trigger=IntervalTrigger(minutes=self.interval_minutes),
            id="job_discovery",
            name="Automatic Job Discovery",
            replace_existing=True,
            max_instances=1,
        )

        self._scheduler.start()
        self._running = True
        logger.info(
            "Discovery scheduler started (interval=%dm)",
            self.interval_minutes,
        )

    def shutdown(self) -> None:
        """Shut down the background scheduler."""
        if self._scheduler is not None:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None
        self._running = False
        logger.info("Discovery scheduler shut down")

    def _run_discovery(self) -> None:
        """Run discovery in its own DB session (background job)."""
        if self._running:
            # This shouldn't happen since max_instances=1, but guard anyway
            logger.warning("Discovery run already in progress, skipping")
            return

        self._running = True
        run_id = str(uuid.uuid4())
        logger.info("Starting scheduled discovery run (id=%s)", run_id)

        db: Session = SessionLocal()
        try:
            stats = job_discovery.discover_all_enabled(db)
            logger.info(
                "Discovery run %s completed: %d sources attempted, %d succeeded, "
                "%d failed, %d jobs created, %d updated",
                run_id,
                stats.sources_attempted,
                stats.sources_succeeded,
                stats.sources_failed,
                stats.jobs_created,
                stats.jobs_updated,
            )
        except Exception as exc:
            logger.error("Discovery run %s failed: %s", run_id, exc, exc_info=True)
        finally:
            self._running = False
            db.close()

    def _on_job_executed(self, event) -> None:
        logger.info(
            "Discovery job executed (run_id=%s, duration_ms=%s)",
            getattr(event, "job_id", "?"),
            getattr(event, "duration", 0),
        )

    def _on_job_error(self, event) -> None:
        logger.error(
            "Discovery job errored (run_id=%s): %s",
            getattr(event, "job_id", "?"),
            getattr(event, "exception", "unknown"),
        )

    def _on_job_missed(self, event) -> None:
        logger.warning(
            "Discovery job missed schedule (run_id=%s)",
            getattr(event, "job_id", "?"),
        )


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_scheduler_instance: Optional[DiscoveryScheduler] = None


def get_scheduler() -> DiscoveryScheduler:
    """Get or create the singleton scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = DiscoveryScheduler()
    return _scheduler_instance


def start_scheduler() -> None:
    """Start the automatic discovery scheduler (called from app lifespan).

    Failures are caught and logged — the scheduler is best-effort and
    must not prevent the application from starting.
    """
    scheduler = get_scheduler()
    try:
        scheduler.start()
    except Exception as exc:
        logger.warning("Failed to start discovery scheduler: %s", exc)


def stop_scheduler() -> None:
    """Stop the automatic discovery scheduler (called from app lifespan)."""
    scheduler = get_scheduler()
    scheduler.shutdown()
