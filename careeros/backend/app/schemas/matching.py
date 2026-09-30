"""Pydantic schemas for Phase 5 job matching."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.jobs import JobSummary


class MatchBreakdownResponse(BaseModel):
    """Per-signal score breakdown for a single match."""

    model_config = ConfigDict(from_attributes=True)

    skills: float
    experience: float
    education: float
    location: float
    preferences: float
    semantic: float
    role_title: float


class JobMatchResponse(BaseModel):
    """Match result for a single job against the authenticated user."""

    model_config = ConfigDict(from_attributes=True)

    job_id: str
    overall_score: float = Field(..., ge=0, le=100)
    breakdown: MatchBreakdownResponse
    matched_skills: list[str]
    missing_skills: list[str]
    matched_requirements: list[str]
    missing_requirements: list[str]
    qualification_match: bool
    experience_match: bool
    location_match: bool
    explanation: list[str]
    profile_completeness: str
    generated_at: str


class JobMatchWithJobResponse(BaseModel):
    """A match result bundled with the job summary, for the personalized feed."""

    match: JobMatchResponse
    job: JobSummary


class MatchFeedResponse(BaseModel):
    """Paginated personalized match feed."""

    items: list[JobMatchWithJobResponse]
    total: int
    page: int
    page_size: int
    profile_completeness: str
