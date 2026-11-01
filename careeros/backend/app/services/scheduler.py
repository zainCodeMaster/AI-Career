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
import threading
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
        self._scheduler_started: bool = False
        self._run_in_progress: bool = False
        self._run_lock = threading.Lock()
        self._last_run_at: Optional[datetime] = None
        self._last_run_duration_ms: Optional[int] = None
        self._last_run_status: Optional[str] = None
        self._last_run_error: Optional[str] = None
        self._next_run_at: Optional[datetime] = None
        self._settings = get_settings()

    @property
    def is_enabled(self) -> bool:
        return self._settings.job_discovery_scheduler_enabled

    @property
    def interval_minutes(self) -> int:
        return self._settings.job_discovery_interval_minutes

    @property
    def running(self) -> bool:
        return self._scheduler_started

    @property
    def run_in_progress(self) -> bool:
        return self._run_in_progress

    @property
    def last_run_at(self) -> Optional[datetime]:
        return self._last_run_at

    @property
    def last_run_duration_ms(self) -> Optional[int]:
        return self._last_run_duration_ms

    @property
    def last_run_status(self) -> Optional[str]:
        return self._last_run_status

    @property
    def last_run_error(self) -> Optional[str]:
        return self._last_run_error

    @property
    def next_run_at(self) -> Optional[datetime]:
        return self._next_run_at

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
        self._scheduler_started = True
        self._update_next_run_time()
        logger.info(
            "Discovery scheduler started (interval=%dm)",
            self.interval_minutes,
        )

    def _update_next_run_time(self) -> None:
        """Update the next scheduled run time."""
        if self._scheduler:
            job = self._scheduler.get_job("job_discovery")
            if job and job.next_run_time:
                self._next_run_at = job.next_run_time
            else:
                self._next_run_at = None
        else:
            self._next_run_at = None

    def shutdown(self) -> None:
        """Shut down the background scheduler."""
        if self._scheduler is not None:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None
        self._scheduler_started = False
        self._run_in_progress = False
        self._next_run_at = None
        logger.info("Discovery scheduler shut down")

    def _run_discovery(self) -> None:
        """Run discovery in its own DB session (background job).
        
        Uses a threading lock to prevent concurrent runs. 
        APScheduler's max_instances=1 also helps, but this provides 
        an additional safety layer and proper state tracking.
        """
        # Check if a run is already in progress (fast path for tests and manual checks)
        if self._run_in_progress:
            logger.warning("Discovery run already in progress, skipping")
            return

        # Try to acquire lock (non-blocking)
        if not self._run_lock.acquire(blocking=False):
            logger.warning("Discovery run already in progress (lock), skipping")
            return

        self._run_in_progress = True
        run_id = str(uuid.uuid4())
        started_at = datetime.now(timezone.utc)
        self._last_run_at = started_at
        self._last_run_status = "running"
        self._last_run_error = None
        logger.info("Starting scheduled discovery run (id=%s)", run_id)

        db: Session = SessionLocal()
        try:
            stats = job_discovery.discover_all_enabled(db)
            completed_at = datetime.now(timezone.utc)
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)
            self._last_run_duration_ms = duration_ms
            self._last_run_status = "success"
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
            completed_at = datetime.now(timezone.utc)
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)
            self._last_run_duration_ms = duration_ms
            self._last_run_status = "failed"
            self._last_run_error = str(exc)
            logger.error("Discovery run %s failed: %s", run_id, exc, exc_info=True)
        finally:
            self._run_in_progress = False
            self._run_lock.release()
            self._update_next_run_time()
            db.close()

    def _on_job_executed(self, event) -> None:
        logger.info(
            "Discovery job executed (run_id=%s, duration_ms=%s)",
            getattr(event, "job_id", "?"),
            getattr(event, "duration", 0),
        )
        self._update_next_run_time()

    def _on_job_error(self, event) -> None:
        logger.error(
            "Discovery job errored (run_id=%s): %s",
            getattr(event, "job_id", "?"),
            getattr(event, "exception", "unknown"),
        )
        self._update_next_run_time()

    def _on_job_missed(self, event) -> None:
        logger.warning(
            "Discovery job missed schedule (run_id=%s)",
            getattr(event, "job_id", "?"),
        )
        self._update_next_run_time()


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
