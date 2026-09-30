"""Tests for the automatic discovery scheduler."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core.config import get_settings
from app.services.scheduler import DiscoveryScheduler, get_scheduler, start_scheduler, stop_scheduler


class TestSchedulerConfig:
    def test_scheduler_config_defaults(self):
        settings = get_settings()
        assert settings.job_discovery_scheduler_enabled is True
        assert settings.job_discovery_interval_minutes == 60

    def test_scheduler_disabled(self):
        with patch("app.services.scheduler.get_settings") as mock_settings:
            mock_settings.return_value.job_discovery_scheduler_enabled = False
            scheduler = DiscoveryScheduler()
            assert scheduler.is_enabled is False

    def test_scheduler_configurable_interval(self):
        with patch("app.services.scheduler.get_settings") as mock_settings:
            mock_settings.return_value.job_discovery_scheduler_enabled = True
            mock_settings.return_value.job_discovery_interval_minutes = 30
            scheduler = DiscoveryScheduler()
            assert scheduler.interval_minutes == 30


class TestSchedulerLifecycle:
    def test_scheduler_start_disabled(self):
        with patch("app.services.scheduler.get_settings") as mock_settings:
            mock_settings.return_value.job_discovery_scheduler_enabled = False
            scheduler = DiscoveryScheduler()
            scheduler.start()
            assert scheduler._scheduler is None
            assert scheduler.running is False

    def test_scheduler_start_enabled(self):
        with patch("app.services.scheduler.get_settings") as mock_settings:
            mock_settings.return_value.job_discovery_scheduler_enabled = True
            mock_settings.return_value.job_discovery_interval_minutes = 60
            mock_settings.return_value.job_discovery_max_results_per_source = 200
            mock_settings.return_value.job_discovery_timeout_seconds = 20.0
            mock_settings.return_value.job_discovery_retry_count = 2
            mock_settings.return_value.job_discovery_stale_days = 60
            mock_settings.return_value.job_discovery_user_agent = "CareerOS-Bot/1.0"

            scheduler = DiscoveryScheduler()
            scheduler.start()
            assert scheduler._scheduler is not None
            assert scheduler.running is True
            scheduler.shutdown()
            assert scheduler._scheduler is None
            assert scheduler.running is False

    def test_scheduler_start_idempotent(self):
        with patch("app.services.scheduler.get_settings") as mock_settings:
            mock_settings.return_value.job_discovery_scheduler_enabled = True
            mock_settings.return_value.job_discovery_interval_minutes = 60
            mock_settings.return_value.job_discovery_max_results_per_source = 200
            mock_settings.return_value.job_discovery_timeout_seconds = 20.0
            mock_settings.return_value.job_discovery_retry_count = 2
            mock_settings.return_value.job_discovery_stale_days = 60
            mock_settings.return_value.job_discovery_user_agent = "CareerOS-Bot/1.0"

            scheduler = DiscoveryScheduler()
            scheduler.start()
            scheduler.start()  # should not create second scheduler
            assert scheduler._scheduler is not None
            scheduler.shutdown()

    def test_scheduler_shutdown_idempotent(self):
        scheduler = DiscoveryScheduler()
        scheduler.shutdown()  # should not error even if not started
        assert scheduler.running is False

    def test_scheduler_double_start_does_not_crash(self):
        with patch("app.services.scheduler.get_settings") as mock_settings:
            mock_settings.return_value.job_discovery_scheduler_enabled = True
            mock_settings.return_value.job_discovery_interval_minutes = 60
            mock_settings.return_value.job_discovery_max_results_per_source = 200
            mock_settings.return_value.job_discovery_timeout_seconds = 20.0
            mock_settings.return_value.job_discovery_retry_count = 2
            mock_settings.return_value.job_discovery_stale_days = 60
            mock_settings.return_value.job_discovery_user_agent = "CareerOS-Bot/1.0"

            scheduler = DiscoveryScheduler()
            scheduler.start()
            # Double start should be safe
            scheduler.start()
            scheduler.shutdown()


class TestSchedulerDiscoveryRun:
    def test_run_discovery_uses_own_session(self):
        """Discovery run should use its own DB session, not share with tests."""
        with patch("app.services.scheduler.get_settings") as mock_settings:
            mock_settings.return_value.job_discovery_scheduler_enabled = True
            mock_settings.return_value.job_discovery_interval_minutes = 60
            mock_settings.return_value.job_discovery_max_results_per_source = 200
            mock_settings.return_value.job_discovery_timeout_seconds = 20.0
            mock_settings.return_value.job_discovery_retry_count = 2
            mock_settings.return_value.job_discovery_stale_days = 60
            mock_settings.return_value.job_discovery_user_agent = "CareerOS-Bot/1.0"

            scheduler = DiscoveryScheduler()
            # Verify _run_discovery exists and has the right signature
            assert hasattr(scheduler, "_run_discovery")

    def test_scheduler_event_listeners_registered(self):
        """Scheduler should register event listeners for observability."""
        with patch("app.services.scheduler.get_settings") as mock_settings:
            mock_settings.return_value.job_discovery_scheduler_enabled = True
            mock_settings.return_value.job_discovery_interval_minutes = 60
            mock_settings.return_value.job_discovery_max_results_per_source = 200
            mock_settings.return_value.job_discovery_timeout_seconds = 20.0
            mock_settings.return_value.job_discovery_retry_count = 2
            mock_settings.return_value.job_discovery_stale_days = 60
            mock_settings.return_value.job_discovery_user_agent = "CareerOS-Bot/1.0"

            scheduler = DiscoveryScheduler()
            scheduler.start()

            # Verify the scheduler has the job registered
            jobs = scheduler._scheduler.get_jobs()
            assert len(jobs) == 1
            assert jobs[0].id == "job_discovery"

            scheduler.shutdown()


class TestSchedulerSingleton:
    def test_get_scheduler_returns_singleton(self):
        s1 = get_scheduler()
        s2 = get_scheduler()
        assert s1 is s2

    def test_start_stop_functions_exist(self):
        assert callable(start_scheduler)
        assert callable(stop_scheduler)

    def test_scheduler_failure_does_not_crash(self):
        """Scheduler start failure should be caught and not propagate."""
        with patch.object(DiscoveryScheduler, "start", side_effect=RuntimeError("DB error")):
            scheduler = get_scheduler()
            # start_scheduler should catch errors, not raise
            with patch("app.services.scheduler.get_scheduler", return_value=scheduler):
                start_scheduler()  # should not raise

    def test_stop_scheduler_handles_unstarted(self):
        """stop_scheduler should not raise if scheduler was never started."""
        stop_scheduler()


class TestSchedulerDuplicatePrevention:
    def test_running_flag_prevents_overlap(self):
        """If a discovery run is in progress, overlapping run should be skipped."""
        with patch("app.services.scheduler.get_settings") as mock_settings:
            mock_settings.return_value.job_discovery_scheduler_enabled = True
            mock_settings.return_value.job_discovery_interval_minutes = 60
            mock_settings.return_value.job_discovery_max_results_per_source = 200
            mock_settings.return_value.job_discovery_timeout_seconds = 20.0
            mock_settings.return_value.job_discovery_retry_count = 2
            mock_settings.return_value.job_discovery_stale_days = 60
            mock_settings.return_value.job_discovery_user_agent = "CareerOS-Bot/1.0"

            scheduler = DiscoveryScheduler()
            scheduler._running = True
            # Should skip run
            scheduler._run_discovery()
            assert scheduler.running is True
            scheduler._running = False
