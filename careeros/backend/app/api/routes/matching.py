"""Phase 5 Job Matching API routes.

- GET /api/v1/jobs/{job_id}/match     — match score for a specific job
- GET /api/v1/jobs/matches             — personalized ranked feed
- GET /api/v1/jobs/matches/{job_id}    — detailed match explanation (same as match)
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.db.models.jobs import Job, UserJobPreferences
from app.db.models.user import User
from app.schemas.jobs import JobSummary
from app.schemas.matching import (
    JobMatchResponse,
    JobMatchWithJobResponse,
    MatchFeedResponse,
)
from app.services.match_engine import MatchEngine, PersonalizedRanker
from app.services.user_profile_aggregator import UserProfileAggregator

router = APIRouter(tags=["job-matching"])


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _job_to_summary(job: Job) -> JobSummary:
    return JobSummary.model_validate(job)


def _parse_uuid(value: str) -> UUID:
    try:
        return UUID(value)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid id format")


# ---------------------------------------------------------------------------
# Match endpoints
# ---------------------------------------------------------------------------


@router.get("/jobs/{job_id}/match", response_model=JobMatchResponse)
def get_job_match(
    job_id: str,
    _current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> JobMatchResponse:
    """Calculate and return the match result for the authenticated user against a specific job.

    Returns the overall match score (0-100), per-signal breakdown, matched/missing
    skills, requirements, and a human-readable explanation.
    """
    job_id_uuid = _parse_uuid(job_id)
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    user_profile = UserProfileAggregator.load(db, _current_user.id)
    engine = MatchEngine()
    result = engine.score_job(db, user_profile, job)

    return JobMatchResponse.model_validate(result)


@router.get("/jobs/matches", response_model=MatchFeedResponse)
def get_personalized_matches(
    page: int = Query(default=1, ge=1, le=1000),
    page_size: int = Query(default=20, ge=1, le=100),
    keyword: Optional[str] = Query(default=None, max_length=200),
    city: Optional[str] = Query(default=None, max_length=100),
    remote: Optional[bool] = Query(default=None),
    employment_type: Optional[str] = Query(default=None, max_length=50),
    sector: Optional[str] = Query(default=None, max_length=32, description="government|private|remote|any"),
    min_score: float = Query(default=0.0, ge=0, le=100),
    _current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> MatchFeedResponse:
    """Return a personalized, ranked list of job matches for the authenticated user.

    Supports filtering by keyword, city, remote, employment type, sector, and
    minimum match score. Results are ranked by match score (descending),
    then by posted date (newest first), then by job ID for determinism.

    Pagination: page (1-indexed) and page_size (1-100).
    """
    # Build the base candidate pool using the same filters as the regular
    # job search. We apply the filters at the DB level to keep the candidate
    # pool small before scoring.
    from sqlalchemy import and_, or_
    from sqlalchemy import select as _select

    stmt = select(Job).where(Job.is_active.is_(True))

    # Only Pakistan-eligible by default
    stmt = stmt.where(Job.is_pakistan_eligible.is_(True))

    filters = []
    if keyword:
        pattern = f"%{keyword}%"
        filters.append(
            or_(
                Job.title.ilike(pattern),
                Job.description.ilike(pattern),
                Job.company_name.ilike(pattern),
            )
        )
    if city:
        filters.append(Job.city.ilike(f"%{city}%"))
    if remote is True:
        from sqlalchemy import or_
        filters.append(or_(Job.is_remote.is_(True), Job.workplace_type == "remote"))
    if employment_type:
        filters.append(Job.employment_type == employment_type)
    if sector:
        if sector == "government":
            filters.append(Job.source.in_(["pk_fpsc", "pk_ppsc", "pk_spsc", "pk_kppsc", "pk_bpsc", "pk_nts", "pk_pts", "pk_ots", "pk_njp", "pk_punjab_jobs"]))
        elif sector == "private":
            filters.append(Job.source.in_(["pk_rozee", "pk_mustakbil", "pk_brightspyre", "linkedin_pk", "indeed_pk"]))
        elif sector == "remote":
            filters.append(Job.source == "remote_generic")

    if filters:
        from sqlalchemy import and_
        from sqlalchemy import and_ as _and
        stmt = stmt.where(_and(*filters))

    # Sort candidates by recency before scoring to give fresh jobs a chance
    stmt = stmt.order_by(Job.posted_at.desc().nulls_last(), Job.discovered_at.desc())
    stmt = stmt.limit(500)  # hard cap on candidate pool before scoring

    candidate_jobs = db.execute(stmt).scalars().all()

    user_profile = UserProfileAggregator.load(db, _current_user.id)
    ranker = PersonalizedRanker(candidate_pool_size=len(candidate_jobs))
    ranked = ranker.rank(db, UserProfileAggregator.load(db, _current_user.id), candidate_jobs, top_k=500)

    # Filter by minimum score
    ranked = [rm for rm in ranked if rm.match.overall_score >= min_score]

    # Pagination
    total = len(ranked)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = ranked[start:end]

    user_profile = UserProfileAggregator.load(db, _current_user.id)
    return MatchFeedResponse(
        items=[
            JobMatchWithJobResponse(
                match=rm.match,
                job=_job_to_summary(rm.job),
            )
            for rm in ranked[start:end]
        ],
        total=len(ranked),
        page=page,
        page_size=page_size,
        profile_completeness="full" if (ranked and ranked[0].match.profile_completeness == "full") else "partial",
    )


@router.get("/jobs/matches/{job_id}", response_model=JobMatchResponse)
def get_match_detail(
    job_id: str,
    _current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> JobMatchResponse:
    """Alias for /jobs/{job_id}/match — returns the full match explanation."""
    return get_job_match(job_id, _current_user, db)