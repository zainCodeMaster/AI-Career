"""Phase 4 Job Discovery API routes.

Route ordering note: static paths (e.g. ``/jobs/saved``, ``/jobs/_discovery/run``)
MUST be defined before the dynamic ``/jobs/{job_id}`` route so that
``saved`` and ``_discovery`` are not captured as a ``job_id`` parameter.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.db.models.jobs import (
    Job,
    JobDiscoveryRun,
    JobSource,
    UserJobPreferences,
    UserSavedJob,
)
from app.db.models.user import User
from app.schemas.jobs import (
    DiscoveryRunRequest,
    DiscoveryRunResult,
    DiscoveryRunsResponse,
    DiscoveryRunSummary,
    JobDetail,
    JobListResponse,
    JobPreferencesResponse,
    JobPreferencesUpdate,
    JobSummary,
    SaveJobRequest,
    SavedJobResponse,
    SourceDetail,
    SourceHealthEntry,
    SourceHealthResponse,
    SourceSummary,
)
from app.services import job_discovery

router = APIRouter(tags=["jobs"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _job_to_summary(job: Job) -> JobSummary:
    return JobSummary.model_validate(job)


def _job_to_detail(job: Job) -> JobDetail:
    return JobDetail.model_validate(job)


def _parse_uuid(value: str) -> UUID:
    try:
        return UUID(value)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid id format")


def _coerce_list(value: Optional[str]) -> list[str]:
    """Parse a JSON list or comma-separated string from a text column."""
    if not value:
        return []
    import json
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [str(x) for x in parsed]
    except (ValueError, TypeError):
        pass
    return [x.strip() for x in value.split(",") if x.strip()]


def _preferences_to_response(prefs: UserJobPreferences) -> JobPreferencesResponse:
    return JobPreferencesResponse(
        target_roles=_coerce_list(prefs.target_roles),
        preferred_cities=_coerce_list(prefs.preferred_cities),
        preferred_provinces=_coerce_list(prefs.preferred_provinces),
        remote_preference=prefs.remote_preference,
        employment_types=_coerce_list(prefs.employment_types),
        experience_level=prefs.experience_level,
        min_salary=prefs.min_salary,
        salary_currency=prefs.salary_currency,
        sector_preference=prefs.sector_preference,
        selected_industries=_coerce_list(prefs.selected_industries),
    )


# ---------------------------------------------------------------------------
# STATIC routes (defined first so they are not shadowed by /jobs/{job_id})
# ---------------------------------------------------------------------------


@router.get("/jobs", response_model=JobListResponse)
def list_jobs(
    keyword: Optional[str] = Query(default=None, max_length=200),
    title: Optional[str] = Query(default=None, max_length=200),
    company: Optional[str] = Query(default=None, max_length=200),
    city: Optional[str] = Query(default=None, max_length=100),
    province: Optional[str] = Query(default=None, max_length=100),
    country: Optional[str] = Query(default=None, max_length=2),
    remote: Optional[bool] = Query(default=None),
    hybrid: Optional[bool] = Query(default=None),
    onsite: Optional[bool] = Query(default=None),
    employment_type: Optional[str] = Query(default=None, max_length=50),
    internship: Optional[bool] = Query(default=None),
    entry_level: Optional[bool] = Query(default=None),
    min_salary: Optional[float] = Query(default=None, ge=0),
    max_salary: Optional[float] = Query(default=None, ge=0),
    industry: Optional[str] = Query(default=None, max_length=100),
    source: Optional[str] = Query(default=None, max_length=64),
    sector: Optional[str] = Query(default=None, max_length=32, description="government|private|remote|any"),
    posted_within_days: Optional[int] = Query(default=None, ge=1, le=365),
    closing_within_days: Optional[int] = Query(default=None, ge=1, le=365),
    is_active: Optional[bool] = Query(default=None),
    is_pakistan: Optional[bool] = Query(default=None),
    page: int = Query(default=1, ge=1, le=1000),
    page_size: int = Query(default=20, ge=1, le=100),
    sort: str = Query(default="posted_desc"),
    _current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> JobListResponse:
    """Search and filter jobs. All filters are optional."""
    stmt = select(Job)

    conditions = []
    if keyword:
        conditions.append(
            or_(
                Job.title.ilike(f"%{keyword}%"),
                Job.description.ilike(f"%{keyword}%"),
                Job.company_name.ilike(f"%{keyword}%"),
            )
        )
    if title:
        conditions.append(Job.title.ilike(f"%{title}%"))
    if company:
        conditions.append(Job.company_name.ilike(f"%{company}%"))
    if city:
        conditions.append(Job.city.ilike(f"%{city}%"))
    if province:
        conditions.append(Job.province.ilike(f"%{province}%"))
    if country:
        conditions.append(Job.country == country.upper())
    if is_pakistan is not None:
        conditions.append(Job.is_pakistan_eligible.is_(is_pakistan))
    elif is_pakistan is None:
        conditions.append(Job.is_pakistan_eligible.is_(True))
    if remote is True:
        conditions.append(Job.workplace_type == "remote")
    if onsite is True:
        conditions.append(Job.workplace_type == "onsite")
    if hybrid is True:
        conditions.append(Job.workplace_type == "hybrid")
    if employment_type:
        conditions.append(Job.employment_type == employment_type)
    if internship:
        conditions.append(Job.employment_type == "internship")
    if entry_level:
        conditions.append(or_(Job.experience_min.is_(None), Job.experience_min <= 2))
    if min_salary is not None:
        conditions.append(or_(Job.salary_max.is_(None), Job.salary_max >= min_salary))
    if max_salary is not None:
        conditions.append(or_(Job.salary_min.is_(None), Job.salary_min <= max_salary))
    if industry:
        conditions.append(Job.category.ilike(f"%{industry}%"))
    if source:
        conditions.append(Job.source == source)
    if sector:
        if sector == "government":
            conditions.append(
                Job.source.in_(
                    [
                        "pk_fpsc", "pk_ppsc", "pk_spsc", "pk_kppsc", "pk_bpsc",
                        "pk_nts", "pk_pts", "pk_ots", "pk_njp", "pk_punjab_jobs",
                    ]
                )
            )
        elif sector == "private":
            conditions.append(
                Job.source.in_(["pk_rozee", "pk_mustakbil", "pk_brightspyre", "linkedin_pk", "indeed_pk"])
            )
        elif sector == "remote":
            conditions.append(Job.source == "remote_generic")
    if posted_within_days is not None:
        from datetime import timezone as _tz
        cutoff_dt = datetime.fromtimestamp(
            datetime.now(_tz.utc).timestamp() - posted_within_days * 86400, tz=_tz.utc
        )
        conditions.append(Job.posted_at >= cutoff_dt)
    if closing_within_days is not None:
        from datetime import timezone as _tz
        now = datetime.now(_tz.utc)
        closing_cutoff = datetime.fromtimestamp(now.timestamp() + closing_within_days * 86400, tz=_tz.utc)
        conditions.append(Job.closing_at.isnot(None))
        conditions.append(Job.closing_at <= closing_cutoff)
        conditions.append(Job.closing_at >= now)
    if is_active is not None:
        conditions.append(Job.is_active.is_(is_active))
    else:
        conditions.append(Job.is_active.is_(True))

    if conditions:
        stmt = stmt.where(and_(*conditions))

    if sort == "posted_desc":
        stmt = stmt.order_by(Job.posted_at.desc().nulls_last(), Job.discovered_at.desc())
    elif sort == "posted_asc":
        stmt = stmt.order_by(Job.posted_at.asc().nulls_last())
    elif sort == "closing_asc":
        stmt = stmt.order_by(Job.closing_at.asc().nulls_last())
    elif sort == "salary_desc":
        stmt = stmt.order_by(Job.salary_max.desc().nulls_last())
    elif sort == "salary_asc":
        stmt = stmt.order_by(Job.salary_min.asc().nulls_last())
    else:
        stmt = stmt.order_by(Job.discovered_at.desc())

    from sqlalchemy import func
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar() or 0
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    rows = db.execute(stmt).scalars().all()

    return JobListResponse(
        items=[_job_to_summary(r) for r in rows],
        total=int(total),
        page=page,
        page_size=page_size,
    )


@router.get("/jobs/saved", response_model=list[SavedJobResponse])
def list_saved_jobs(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[SavedJobResponse]:
    """List the authenticated user's saved jobs."""
    rows = (
        db.query(UserSavedJob, Job)
        .join(Job, Job.id == UserSavedJob.job_id)
        .filter(UserSavedJob.user_id == str(current_user.id))
        .order_by(UserSavedJob.saved_at.desc())
        .all()
    )
    return [
        SavedJobResponse(
            id=str(saved.id),
            job=_job_to_summary(job),
            saved_at=saved.saved_at,
            notes=saved.notes,
        )
        for saved, job in rows
    ]


@router.post("/jobs/_discovery/run", response_model=DiscoveryRunResult)
def trigger_discovery(
    payload: Optional[DiscoveryRunRequest] = None,
    _current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> DiscoveryRunResult:
    """Trigger a discovery run.

    If ``source_id`` is provided, only that source is run.
    Otherwise, all enabled sources are discovered.
    """
    if payload and payload.source_id:
        result = job_discovery.discover_source(
            db,
            payload.source_id,
            max_results=payload.max_results,
            timeout=payload.timeout,
        )
        db.commit()
        return DiscoveryRunResult(
            sources_attempted=1,
            sources_succeeded=0 if result.error else 1,
            sources_failed=1 if result.error else 0,
            jobs_found=len(result.jobs),
            jobs_created=0,
            jobs_updated=0,
            jobs_skipped=0,
            jobs_expired=0,
            error_count=1 if result.error else 0,
        )

    stats = job_discovery.discover_all_enabled(db)
    db.commit()
    return DiscoveryRunResult(
        sources_attempted=stats.sources_attempted,
        sources_succeeded=stats.sources_succeeded,
        sources_failed=stats.sources_failed,
        jobs_found=stats.jobs_found,
        jobs_created=stats.jobs_created,
        jobs_updated=stats.jobs_updated,
        jobs_skipped=stats.jobs_skipped,
        jobs_expired=stats.jobs_expired,
        error_count=stats.error_count,
    )


# ---------------------------------------------------------------------------
# DYNAMIC routes (defined after static routes)
# ---------------------------------------------------------------------------


@router.get("/jobs/{job_id}", response_model=JobDetail)
def get_job(
    job_id: str,
    _current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> JobDetail:
    """Get a single job by id."""
    _ = _parse_uuid(job_id)
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_to_detail(job)


@router.post("/jobs/{job_id}/save", response_model=SavedJobResponse, status_code=status.HTTP_200_OK)
def save_job(
    job_id: str,
    payload: Optional[SaveJobRequest] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SavedJobResponse:
    """Save a job to the authenticated user's bookmarks."""
    _ = _parse_uuid(job_id)
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    existing = (
        db.query(UserSavedJob)
        .filter(UserSavedJob.user_id == str(current_user.id), UserSavedJob.job_id == job_id)
        .first()
    )
    if existing is not None:
        if payload and payload.notes is not None:
            existing.notes = payload.notes
        db.commit()
        db.refresh(existing)
        return SavedJobResponse(
            id=str(existing.id),
            job=_job_to_summary(job),
            saved_at=existing.saved_at,
            notes=existing.notes,
        )

    saved = UserSavedJob(
        user_id=str(current_user.id),
        job_id=job_id,
        notes=(payload.notes if payload else None),
    )
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return SavedJobResponse(
        id=str(saved.id),
        job=_job_to_summary(job),
        saved_at=saved.saved_at,
        notes=saved.notes,
    )


@router.delete("/jobs/{job_id}/save", status_code=status.HTTP_204_NO_CONTENT)
def unsave_job(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    """Remove a saved job bookmark."""
    _ = _parse_uuid(job_id)
    (
        db.query(UserSavedJob)
        .filter(UserSavedJob.user_id == str(current_user.id), UserSavedJob.job_id == job_id)
        .delete(synchronize_session=False)
    )
    db.commit()


# ---------------------------------------------------------------------------
# Sources (read-only)
# ---------------------------------------------------------------------------


@router.get("/sources", response_model=list[SourceSummary])
def list_sources(
    _current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[SourceSummary]:
    """List registered job sources (read-only)."""
    rows = db.query(JobSource).order_by(JobSource.category, JobSource.name).all()
    return [SourceSummary.model_validate(r) for r in rows]


@router.get("/sources/health", response_model=SourceHealthResponse)
def get_sources_health(
    _current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SourceHealthResponse:
    """Get health status for all sources.

    Returns the current status of each source: ``active`` (working),
    ``degraded`` (some recent failures), ``failed`` (consecutive failures),
    or ``unknown`` (never run).
    """
    rows = db.query(JobSource).order_by(JobSource.category, JobSource.name).all()
    entries: list[SourceHealthEntry] = []
    for src in rows:
        status = "unknown"
        if src.last_success_at is not None and src.consecutive_failures == 0:
            status = "active"
        elif src.last_failure_at is not None:
            if src.consecutive_failures >= 3:
                status = "failed"
            else:
                status = "degraded"
        elif src.consecutive_failures > 0:
            status = "degraded"

        entries.append(SourceHealthEntry(
            source_id=src.id,
            source_name=src.name,
            last_run_at=src.last_run_at,
            last_success_at=src.last_success_at,
            last_failure_at=src.last_failure_at,
            consecutive_failures=src.consecutive_failures,
            total_jobs_discovered=src.total_jobs_discovered,
            last_error=src.last_error,
            status=status,
            enabled=src.enabled,
        ))
    return SourceHealthResponse(sources=entries)


@router.get("/sources/{source_id}", response_model=SourceDetail)
def get_source(
    source_id: str,
    _current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SourceDetail:
    """Get detailed information about a single source."""
    src = db.get(JobSource, source_id)
    if src is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return SourceDetail.model_validate(src)


@router.get("/jobs/discovery/runs", response_model=DiscoveryRunsResponse)
def list_discovery_runs(
    page: int = Query(default=1, ge=1, le=1000),
    page_size: int = Query(default=20, ge=1, le=100),
    source_id: Optional[str] = Query(default=None, max_length=64),
    status: Optional[str] = Query(default=None, max_length=32),
    _current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> DiscoveryRunsResponse:
    """List recent discovery run history.

    Supports optional filtering by ``source_id`` and ``status``.
    """
    from sqlalchemy import func
    stmt = select(JobDiscoveryRun).order_by(JobDiscoveryRun.started_at.desc())
    conditions = []
    if source_id:
        conditions.append(JobDiscoveryRun.source_id == source_id)
    if status:
        conditions.append(JobDiscoveryRun.status == status)
    if conditions:
        stmt = stmt.where(and_(*conditions))
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar() or 0
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    runs = db.execute(stmt).scalars().all()
    return DiscoveryRunsResponse(
        items=[DiscoveryRunSummary.model_validate(r) for r in runs],
        total=int(total),
        page=page,
        page_size=page_size,
    )


# ---------------------------------------------------------------------------
# Preferences
# ---------------------------------------------------------------------------


@router.get("/job-preferences", response_model=JobPreferencesResponse)
def get_preferences(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> JobPreferencesResponse:
    """Get the authenticated user's job discovery preferences."""
    prefs = (
        db.query(UserJobPreferences)
        .filter(UserJobPreferences.user_id == str(current_user.id))
        .first()
    )
    if prefs is None:
        return JobPreferencesResponse()
    return _preferences_to_response(prefs)


@router.put("/job-preferences", response_model=JobPreferencesResponse)
def update_preferences(
    payload: JobPreferencesUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> JobPreferencesResponse:
    """Create or replace the authenticated user's job preferences."""
    import json
    prefs = (
        db.query(UserJobPreferences)
        .filter(UserJobPreferences.user_id == str(current_user.id))
        .first()
    )
    if prefs is None:
        prefs = UserJobPreferences(user_id=str(current_user.id))
        db.add(prefs)

    data = payload.model_dump(exclude_unset=True)
    if "target_roles" in data:
        prefs.target_roles = json.dumps(data["target_roles"] or [])
    if "preferred_cities" in data:
        prefs.preferred_cities = json.dumps(data["preferred_cities"] or [])
    if "preferred_provinces" in data:
        prefs.preferred_provinces = json.dumps(data["preferred_provinces"] or [])
    if "remote_preference" in data:
        prefs.remote_preference = data["remote_preference"]
    if "employment_types" in data:
        prefs.employment_types = json.dumps(data["employment_types"] or [])
    if "experience_level" in data:
        prefs.experience_level = data["experience_level"]
    if "min_salary" in data:
        prefs.min_salary = data["min_salary"]
    if "salary_currency" in data:
        prefs.salary_currency = data["salary_currency"]
    if "sector_preference" in data:
        prefs.sector_preference = data["sector_preference"]
    if "selected_industries" in data:
        prefs.selected_industries = json.dumps(data["selected_industries"] or [])

    db.commit()
    db.refresh(prefs)
    return _preferences_to_response(prefs)
