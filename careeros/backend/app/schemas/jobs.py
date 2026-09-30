"""Pydantic schemas for Phase 4 Job Discovery."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------


class JobSummary(BaseModel):
    """Lightweight job representation for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    source: str
    source_url: Optional[str] = None
    title: str
    company_name: str
    company_url: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    country: str
    is_remote: bool
    is_pakistan_eligible: bool
    employment_type: Optional[str] = None
    workplace_type: Optional[str] = None
    category: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    salary_period: Optional[str] = None
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    posted_at: Optional[datetime] = None
    closing_at: Optional[datetime] = None
    status: str
    is_active: bool


class JobDetail(JobSummary):
    """Full job representation including description fields."""

    description: Optional[str] = None
    requirements: Optional[str] = None
    responsibilities: Optional[str] = None
    skills: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    education_requirements: Optional[str] = None
    discovered_at: datetime
    last_seen_at: datetime
    eligibility: Optional[str] = None


class JobListResponse(BaseModel):
    """Paginated job list response."""

    items: list[JobSummary]
    total: int
    page: int
    page_size: int


class SourceSummary(BaseModel):
    """Public source metadata — visible to all authenticated users."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    category: str
    source_type: str
    integration_method: str
    country: str
    enabled: bool
    is_active: bool
    last_run_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    consecutive_failures: int
    total_jobs_discovered: int
    last_error: Optional[str] = None


class SourceDetail(SourceSummary):
    """Detailed source metadata — visible to authenticated users."""

    base_url: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SourceHealthEntry(BaseModel):
    """Health information for a single source."""

    source_id: str
    source_name: str
    last_run_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    consecutive_failures: int
    total_jobs_discovered: int
    last_error: Optional[str] = None
    status: str  # "active" | "degraded" | "failed" | "unknown"
    enabled: bool


class SourceHealthResponse(BaseModel):
    """Aggregate health response for all sources."""

    sources: list[SourceHealthEntry]


class DiscoveryRunSummary(BaseModel):
    """Summary of a single discovery run."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    source_id: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str  # "running" | "success" | "partial" | "failed"
    jobs_found: int
    jobs_created: int
    jobs_updated: int
    jobs_skipped: int
    jobs_expired: int
    error_count: int
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None


# ---------------------------------------------------------------------------
# Saved jobs
# ---------------------------------------------------------------------------


class SavedJobResponse(BaseModel):
    """A saved job with the saved_at timestamp."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    job: JobSummary
    saved_at: datetime
    notes: Optional[str] = None


class SaveJobRequest(BaseModel):
    """Optional notes when saving a job."""

    notes: Optional[str] = Field(default=None, max_length=2000)


# ---------------------------------------------------------------------------
# Job preferences
# ---------------------------------------------------------------------------


class JobPreferencesResponse(BaseModel):
    """User job discovery preferences."""

    model_config = ConfigDict(from_attributes=True)

    target_roles: list[str] = Field(default_factory=list)
    preferred_cities: list[str] = Field(default_factory=list)
    preferred_provinces: list[str] = Field(default_factory=list)
    remote_preference: Optional[str] = None
    employment_types: list[str] = Field(default_factory=list)
    experience_level: Optional[str] = None
    min_salary: Optional[float] = None
    salary_currency: Optional[str] = None
    sector_preference: Optional[str] = None
    selected_industries: list[str] = Field(default_factory=list)


class JobPreferencesUpdate(BaseModel):
    """Partial update for job preferences."""

    target_roles: Optional[list[str]] = None
    preferred_cities: Optional[list[str]] = None
    preferred_provinces: Optional[list[str]] = None
    remote_preference: Optional[str] = None
    employment_types: Optional[list[str]] = None
    experience_level: Optional[str] = None
    min_salary: Optional[float] = None
    salary_currency: Optional[str] = None
    sector_preference: Optional[str] = None
    selected_industries: Optional[list[str]] = None

    @field_validator("remote_preference")
    @classmethod
    def _check_remote(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        allowed = {"remote_only", "hybrid_ok", "onsite_ok", "any"}
        if v not in allowed:
            raise ValueError(f"remote_preference must be one of {sorted(allowed)}")
        return v

    @field_validator("experience_level")
    @classmethod
    def _check_exp(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        allowed = {"entry", "mid", "senior", "executive", "any"}
        if v not in allowed:
            raise ValueError(f"experience_level must be one of {sorted(allowed)}")
        return v

    @field_validator("sector_preference")
    @classmethod
    def _check_sector(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        allowed = {"government", "private", "remote", "any"}
        if v not in allowed:
            raise ValueError(f"sector_preference must be one of {sorted(allowed)}")
        return v


# ---------------------------------------------------------------------------
# Internal discovery trigger (system-only)
# ---------------------------------------------------------------------------


class DiscoveryRunResult(BaseModel):
    """Result of a discovery run."""

    sources_attempted: int
    sources_succeeded: int
    sources_failed: int
    jobs_found: int
    jobs_created: int
    jobs_updated: int
    jobs_skipped: int
    jobs_expired: int
    error_count: int


class DiscoveryRunRequest(BaseModel):
    """Request body for triggering a specific source discovery run."""

    source_id: Optional[str] = None
    max_results: Optional[int] = None
    timeout: Optional[float] = None


class DiscoveryRunsResponse(BaseModel):
    """Paginated list of discovery run summaries."""

    items: list[DiscoveryRunSummary]
    total: int
    page: int
    page_size: int
