"""Job persistence, deduplication, and discovery engine.

Responsibilities:
- Persist normalized jobs to the database, respecting the unique
  ``(source, source_job_id)`` constraint
- Conservative deduplication: merge jobs only when evidence indicates they
  are the same underlying listing (same source_job_id or identical
  ``normalized_hash`` with matching company+title+location)
- Expire stale jobs (not seen for N days)
- Track discovery runs with per-source statistics
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models.jobs import Job, JobDiscoveryRun, JobExternalReference, JobSource as JobSourceModel
from app.services.job_normalizer import NormalizedJob
from app.services.job_sources import (
    BaseJobSource,
    JobSourceError,
    SourceFetchResult,
    build_source,
)

logger = logging.getLogger("app.jobs")


@dataclass
class DiscoveryStats:
    """Aggregate statistics for a full discovery run."""

    sources_attempted: int = 0
    sources_succeeded: int = 0
    sources_failed: int = 0
    jobs_found: int = 0
    jobs_created: int = 0
    jobs_updated: int = 0
    jobs_skipped: int = 0
    jobs_expired: int = 0
    error_count: int = 0


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def upsert_job(db: Session, job: NormalizedJob) -> tuple[Job, bool]:
    """Insert or update a normalized job.

    Returns ``(job, created)`` where ``created`` is True if a new row was
    created, False if an existing row was updated.

    Dedup policy:
    1. If a job with the same ``(source, source_job_id)`` exists, update it.
    2. Else, if a job with the same ``normalized_hash`` (and matching
       company + title) exists from a *different* source, prefer the newer
       source: update the existing row to reflect the newer observation
       and add the new source to ``raw_source_metadata``. Conservative
       matching: only merges when the normalized identity matches.
    3. Else, insert a new row.
    """
    existing = db.query(Job).filter(
        Job.source == job.source, Job.source_job_id == job.source_job_id
    ).first()

    if existing is not None:
        result = _apply_update(existing, job)
        _upsert_external_reference(db, existing.id, job)
        return result, False

    # Cross-source dedup: only when company + title align exactly with the
    # normalized identity. This avoids merging distinct jobs with similar
    # titles.
    dup = db.query(Job).filter(
        and_(
            Job.normalized_hash == job.normalized_hash,
            Job.company_name == job.company_name,
            Job.title == job.title,
        )
    ).first()
    if dup is not None and dup.source != job.source:
        result = _apply_update(dup, job)
        _upsert_external_reference(db, dup.id, job)
        return result, False

    new_job = Job(
        source=job.source,
        source_job_id=job.source_job_id,
        source_url=job.source_url,
        raw_source_metadata=job.raw_source_metadata,
        title=job.title,
        company_name=job.company_name,
        company_url=job.company_url,
        description=job.description,
        requirements=job.requirements,
        responsibilities=job.responsibilities,
        skills=job.skills,
        employment_type=job.employment_type,
        workplace_type=job.workplace_type,
        department=job.department,
        category=job.category,
        location=job.location,
        city=job.city,
        province=job.province,
        country=job.country or "PK",
        is_remote=job.is_remote,
        is_pakistan_eligible=job.is_pakistan_eligible,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        salary_currency=job.salary_currency,
        salary_period=job.salary_period,
        experience_min=job.experience_min,
        experience_max=job.experience_max,
        education_requirements=job.education_requirements,
        posted_at=job.posted_at,
        closing_at=job.closing_at,
        discovered_at=datetime.now(timezone.utc),
        last_seen_at=datetime.now(timezone.utc),
        status=job.status,
        is_active=job.is_active,
        eligibility=job.eligibility,
        content_hash=job.content_hash,
        normalized_hash=job.normalized_hash,
    )
    db.add(new_job)
    db.flush()

    # Track external provenance
    _upsert_external_reference(db, new_job.id, job)

    return new_job, True


def _upsert_external_reference(db: Session, job_id: str, job: NormalizedJob) -> None:
    """Track that a source has observed a canonical job (cross-source provenance)."""
    now = datetime.now(timezone.utc)
    ref = (
        db.query(JobExternalReference)
        .filter(
            JobExternalReference.job_id == job_id,
            JobExternalReference.source_id == job.source,
            JobExternalReference.source_job_id == job.source_job_id,
        )
        .first()
    )
    if ref is None:
        ref = JobExternalReference(
            job_id=job_id,
            source_id=job.source,
            source_job_id=job.source_job_id,
            source_url=job.source_url,
            first_seen_at=now,
            last_seen_at=now,
        )
        db.add(ref)
    else:
        ref.last_seen_at = now
        ref.source_url = job.source_url or ref.source_url


def _apply_update(existing: Job, job: NormalizedJob) -> Job:
    """Apply a normalized job onto an existing row (dedup-safe)."""
    # Trust the latest observation for volatile fields.
    existing.source_url = job.source_url or existing.source_url
    existing.last_seen_at = datetime.now(timezone.utc)
    if job.content_hash != existing.content_hash:
        existing.title = job.title
        existing.company_name = job.company_name
        existing.company_url = job.company_url or existing.company_url
        existing.description = job.description or existing.description
        existing.requirements = job.requirements or existing.requirements
        existing.responsibilities = job.responsibilities or existing.responsibilities
        existing.skills = job.skills or existing.skills
        existing.employment_type = job.employment_type or existing.employment_type
        existing.workplace_type = job.workplace_type or existing.workplace_type
        existing.department = job.department or existing.department
        existing.category = job.category or existing.category
        existing.location = job.location or existing.location
        existing.city = job.city or existing.city
        existing.province = job.province or existing.province
        existing.salary_min = job.salary_min if job.salary_min is not None else existing.salary_min
        existing.salary_max = job.salary_max if job.salary_max is not None else existing.salary_max
        existing.salary_currency = job.salary_currency or existing.salary_currency
        existing.salary_period = job.salary_period or existing.salary_period
        existing.experience_min = job.experience_min if job.experience_min is not None else existing.experience_min
        existing.experience_max = job.experience_max if job.experience_max is not None else existing.experience_max
        existing.education_requirements = job.education_requirements or existing.education_requirements
        existing.posted_at = job.posted_at or existing.posted_at
        existing.closing_at = job.closing_at or existing.closing_at
        existing.is_remote = job.is_remote
        existing.is_pakistan_eligible = job.is_pakistan_eligible
        existing.content_hash = job.content_hash
        existing.status = "active"
        existing.is_active = True
    return existing


def expire_stale_jobs(db: Session, days: Optional[int] = None) -> int:
    """Soft-expire jobs not seen for ``days`` days."""
    settings = get_settings()
    cutoff = datetime.now(timezone.utc) - timedelta(days=days or settings.job_discovery_stale_days)
    stale = (
        db.query(Job)
        .filter(Job.is_active.is_(True), Job.last_seen_at < cutoff)
        .all()
    )
    for job in stale:
        job.is_active = False
        job.status = "expired"
    db.flush()
    return len(stale)


# ---------------------------------------------------------------------------
# Source health
# ---------------------------------------------------------------------------


def record_source_success(
    db: Session,
    source_id: str,
    jobs_discovered: int,
) -> None:
    src = db.get(JobSourceModel, source_id)
    if src is None:
        return
    now = datetime.now(timezone.utc)
    src.last_run_at = now
    src.last_success_at = now
    src.consecutive_failures = 0
    src.total_jobs_discovered += jobs_discovered
    src.last_error = None


def record_source_failure(db: Session, source_id: str, error: str) -> None:
    src = db.get(JobSourceModel, source_id)
    if src is None:
        return
    now = datetime.now(timezone.utc)
    src.last_run_at = now
    src.last_failure_at = now
    src.consecutive_failures += 1
    # Sanitize error message: do not store full stack traces or raw payloads.
    sanitized = error.strip().splitlines()[0][:500] if error else "unknown error"
    src.last_error = sanitized


# ---------------------------------------------------------------------------
# Discovery engine
# ---------------------------------------------------------------------------


def _start_run(db: Session, source_id: Optional[str]) -> JobDiscoveryRun:
    run = JobDiscoveryRun(
        source_id=source_id,
        started_at=datetime.now(timezone.utc),
        status="running",
    )
    db.add(run)
    db.flush()
    return run


def _finish_run(run: JobDiscoveryRun, *, status: str, error: Optional[str] = None) -> None:
    run.completed_at = datetime.now(timezone.utc)
    run.duration_ms = int((run.completed_at - run.started_at).total_seconds() * 1000)
    run.status = status
    if error:
        run.error_message = error.strip().splitlines()[0][:500]


def discover_source(
    db: Session,
    source_id: str,
    *,
    max_results: Optional[int] = None,
    timeout: Optional[float] = None,
) -> SourceFetchResult:
    """Run a single source and persist its results.

    Returns a ``SourceFetchResult`` describing the outcome. The caller may
    inspect the result even if the source failed. All DB writes are
    committed by this function.
    """
    settings = get_settings()
    max_results = max_results or settings.job_discovery_max_results_per_source
    timeout = timeout or settings.job_discovery_timeout_seconds

    run = _start_run(db, source_id)
    try:
        try:
            source: BaseJobSource = build_source(source_id)
        except (KeyError, TypeError) as exc:
            run.jobs_found = run.jobs_created = run.jobs_updated = 0
            _finish_run(run, status="failed", error=f"source not registered: {exc}")
            record_source_failure(db, source_id, str(exc))
            db.commit()
            return SourceFetchResult(source_id=source_id, jobs=[], error=str(exc))

        try:
            raw_jobs = source.fetch(max_results=max_results, timeout=timeout)
        except JobSourceError as exc:
            run.jobs_found = run.jobs_created = run.jobs_updated = 0
            _finish_run(run, status="failed", error=str(exc))
            record_source_failure(db, source_id, str(exc))
            db.commit()
            return SourceFetchResult(source_id=source_id, jobs=[], error=str(exc))
        except Exception as exc:  # defensive: never let a source crash the engine
            logger.exception("Unhandled error from source %s", source_id)
            run.jobs_found = run.jobs_created = run.jobs_updated = 0
            _finish_run(run, status="failed", error=str(exc))
            record_source_failure(db, source_id, str(exc))
            db.commit()
            return SourceFetchResult(source_id=source_id, jobs=[], error=str(exc))

        # Normalize and upsert each job.
        from app.services.job_normalizer import normalize
        found = len(raw_jobs)
        created = updated = skipped = errors = 0
        for raw in raw_jobs:
            try:
                norm = normalize(raw)
            except Exception as exc:
                logger.warning("Failed to normalize job from %s: %s", source_id, exc)
                errors += 1
                continue
            try:
                _, was_created = upsert_job(db, norm)
            except Exception as exc:
                logger.warning("Failed to upsert job from %s: %s", source_id, exc)
                db.rollback()
                errors += 1
                continue
            if was_created:
                created += 1
            else:
                updated += 1

        run.jobs_found = found
        run.jobs_created = created
        run.jobs_updated = updated
        run.jobs_skipped = skipped
        run.error_count = errors
        status = "success" if errors == 0 else "partial"
        _finish_run(run, status=status)
        record_source_success(db, source_id, found)
        db.commit()
        return SourceFetchResult(source_id=source_id, jobs=raw_jobs, error=None)
    except Exception as exc:
        logger.exception("Critical failure in discover_source(%s)", source_id)
        db.rollback()
        _finish_run(run, status="failed", error=str(exc))
        try:
            record_source_failure(db, source_id, str(exc))
            db.commit()
        except Exception:
            db.rollback()
        return SourceFetchResult(source_id=source_id, jobs=[], error=str(exc))


def discover_all_enabled(
    db: Session,
    *,
    max_results: Optional[int] = None,
    timeout: Optional[float] = None,
) -> DiscoveryStats:
    """Run discovery for every enabled source. Continues on failure."""
    stats = DiscoveryStats()
    sources = db.query(JobSourceModel).filter(JobSourceModel.enabled.is_(True), JobSourceModel.is_active.is_(True)).all()
    stats.sources_attempted = len(sources)
    for src in sources:
        result = discover_source(db, src.id, max_results=max_results, timeout=timeout)
        if result.error:
            stats.sources_failed += 1
            stats.error_count += 1
        else:
            stats.sources_succeeded += 1
        # Pull the latest run stats for this source.
        run = (
            db.query(JobDiscoveryRun)
            .filter(JobDiscoveryRun.source_id == src.id)
            .order_by(JobDiscoveryRun.started_at.desc())
            .first()
        )
        if run is not None:
            stats.jobs_found += run.jobs_found
            stats.jobs_created += run.jobs_created
            stats.jobs_updated += run.jobs_updated
            stats.jobs_skipped += run.jobs_skipped
            stats.error_count += run.error_count

    stats.jobs_expired = expire_stale_jobs(db)
    db.commit()
    return stats
