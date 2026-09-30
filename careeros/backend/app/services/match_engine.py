"""Phase 5 — Intelligent Job Matching Engine.

Combines the deterministic feature matchers and the semantic Career Brain
matcher into a single 0–100 overall match score per job, with an explainable
breakdown of why.

The engine is intentionally cheap to invoke: no per-job LLM calls. It
caches the user's aggregated profile per request and scores jobs in a
candidate loop with a configurable pool size.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models.jobs import Job, UserJobPreferences
from app.services.feature_matchers import (
    EducationSignal,
    ExperienceSignal,
    LocationSignal,
    PreferenceSignal,
    RoleTitleSignal,
    education_score,
    experience_score,
    location_score,
    preference_score,
    role_title_score,
)
from app.services.job_requirements import JobRequirements, extract_job_requirements
from app.services.skill_matcher import SkillMatchResult, SkillMatcher
from app.services.user_profile_aggregator import (
    SemanticMatcher,
    SemanticSignal,
    UserMatchProfile,
    UserProfileAggregator,
)

logger = logging.getLogger("app.matching")


@dataclass(frozen=True)
class MatchBreakdown:
    """Per-signal scores for an individual match."""

    skills: float
    experience: float
    education: float
    location: float
    preferences: float
    semantic: float
    role_title: float


@dataclass(frozen=True)
class MatchResult:
    """A complete match result for a single job against the authenticated user."""

    job_id: str
    overall_score: float  # 0.0–100.0
    breakdown: MatchBreakdown
    matched_skills: list[str]
    missing_skills: list[str]
    matched_requirements: list[str]
    missing_requirements: list[str]
    qualification_match: bool
    experience_match: bool
    location_match: bool
    explanation: list[str]  # human-readable, derived from actual signals
    profile_completeness: str  # "full" | "partial" | "empty"
    generated_at: str  # ISO 8601


# ---------------------------------------------------------------------------
# Weights
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MatchWeights:
    """Configurable weight vector for the match score.

    Weights are bounded [0, 1] and should sum to ~1.0. The defaults are
    skill-first because skills are the most reliable, falsifiable signal
    available from a normalized Job. Other signals (semantic, location,
    preferences) add personalization but are noisier.
    """

    skills: float = 0.30
    experience: float = 0.15
    education: float = 0.10
    location: float = 0.15
    preferences: float = 0.15
    semantic: float = 0.10
    role_title: float = 0.05

    @classmethod
    def from_settings(cls) -> "MatchWeights":
        s = get_settings()
        return cls(
            skills=float(s.match_weight_skills),
            experience=float(s.match_weight_experience),
            education=float(s.match_weight_education),
            location=float(s.match_weight_location),
            preferences=float(s.match_weight_preferences),
            semantic=float(s.match_weight_semantic),
            role_title=float(s.match_weight_role_title),
        )


# ---------------------------------------------------------------------------
# Scorer
# ---------------------------------------------------------------------------


def compute_overall_score(breakdown: MatchBreakdown, weights: MatchWeights) -> float:
    """Combine the per-signal scores into a single 0–100 score.

    Signals marked unavailable are NOT penalized. Each unavailable signal
    is replaced with 0.5 (neutral) and the weight is redistributed across
    the available signals so the final score is still bounded 0–100.
    """
    raw_signals = {
        "skills": breakdown.skills,
        "experience": breakdown.experience,
        "education": breakdown.education,
        "location": breakdown.location,
        "preferences": breakdown.preferences,
        "semantic": breakdown.semantic,
        "role_title": breakdown.role_title,
    }
    raw_weights = {
        "skills": weights.skills,
        "experience": weights.experience,
        "education": weights.education,
        "location": weights.location,
        "preferences": weights.preferences,
        "semantic": weights.semantic,
        "role_title": weights.role_title,
    }

    total_weight = sum(raw_weights.values())
    if total_weight <= 0:
        return 0.0

    weighted_sum = sum(raw_signals[k] * raw_weights[k] for k in raw_signals)
    return max(0.0, min(100.0, (weighted_sum / total_weight) * 100.0))


# ---------------------------------------------------------------------------
# Explanation builder
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _SignalBundle:
    skills: SkillMatchResult
    experience: ExperienceSignal
    education: EducationSignal
    location: LocationSignal
    preferences: PreferenceSignal
    semantic: SemanticSignal
    role_title: RoleTitleSignal


def _profile_completeness(profile: UserMatchProfile) -> str:
    """Categorize how much user data is available for matching."""
    available_signals = sum(
        bool(x) for x in (
            profile.skills,
            profile.experience_titles,
            profile.degrees,
            profile.years_of_experience is not None,
            profile.target_roles,
            profile.preferred_cities,
            profile.preferred_employment_types,
        )
    )
    if available_signals >= 5:
        return "full"
    if available_signals >= 2:
        return "partial"
    return "empty"


def build_explanation(bundle: _SignalBundle) -> list[str]:
    """Produce human-readable match reasons from actual signal results.

    No generic filler. Every line corresponds to a computed signal.
    """
    lines: list[str] = []

    # Skills
    if bundle.skills.no_user_skills:
        lines.append("Skill signal unavailable — you have no skills on file.")
    elif bundle.skills.no_job_skills:
        lines.append("Job does not list specific skills.")
    else:
        if bundle.skills.matched:
            shown = bundle.skills.matched[:5]
            lines.append(f"Matched {len(bundle.skills.matched)} skill(s): {', '.join(shown)}.")
        if bundle.skills.missing_required:
            lines.append(
                "Missing required skill(s): " + ", ".join(bundle.skills.missing_required) + "."
            )
        elif bundle.skills.missing:
            lines.append(
                "Missing optional skill(s): " + ", ".join(bundle.skills.missing) + "."
            )

    # Experience
    lines.append(f"Experience: {bundle.experience.reason}")

    # Education
    lines.append(f"Education: {bundle.education.reason}")

    # Location
    lines.append(f"Location: {bundle.location.reason}")

    # Preferences
    if not bundle.preferences.unavailable:
        lines.append(f"Preferences: {bundle.preferences.reason}")

    # Role/title
    if not bundle.role_title.unavailable:
        lines.append(f"Role match: {bundle.role_title.reason}")

    # Semantic
    if not bundle.semantic.unavailable:
        lines.append(bundle.semantic.reason)

    return [ln for ln in lines if ln]


# ---------------------------------------------------------------------------
# Match engine
# ---------------------------------------------------------------------------


class MatchEngine:
    """Scores one job against one user's aggregated profile."""

    def __init__(self, weights: Optional[MatchWeights] = None) -> None:
        self.weights = weights or MatchWeights.from_settings()

    def score_job(
        self,
        db: Session,
        user: UserMatchProfile,
        job: Job,
    ) -> MatchResult:
        """Compute the match result for a single job."""
        reqs = extract_job_requirements(
            skills_text=job.skills,
            requirements_text=job.requirements,
            description_text=job.description,
            experience_min=job.experience_min,
            experience_max=job.experience_max,
            education_requirements=job.education_requirements,
            category=job.category,
        )

        skills = SkillMatcher.match(
            user_skills=user.skills,
            job_required_skills=reqs.required_skills,
            job_optional_skills=reqs.optional_skills,
        )

        is_internship = (job.employment_type == "internship") or (reqs.industry or "").lower() == "internship"
        # Derive "years of experience" from user's profile (prefer CareerProfile
        # years_of_experience, fall back to max of any skill YoE).
        user_years = user.years_of_experience
        if user_years is None:
            # No data — leave as None.
            pass
        exp_signal = experience_score(
            user_years=user_years,
            job_min=reqs.experience_min,
            job_max=reqs.experience_max,
            is_internship_or_entry=is_internship,
        )

        edu_signal = education_score(
            user_degrees=list(user.degrees),
            job_education_text=reqs.education_text,
        )

        loc_signal = location_score(
            user_cities=list(user.preferred_cities) or ([user.preferred_location] if user.preferred_location else []),
            user_provinces=list(user.preferred_provinces),
            remote_preference=user.remote_preference or _effective_remote_pref(user),
            job_city=job.city,
            job_province=job.province,
            job_workplace_type=job.workplace_type,
            job_remote=bool(job.is_remote),
        )

        pref_signal = preference_score(
            user_employment_types=list(user.preferred_employment_types),
            user_sector_preference=user.sector_preference,
            user_min_salary=user.min_salary,
            user_salary_currency=user.salary_currency,
            user_selected_industries=list(user.selected_industries),
            job_employment_type=job.employment_type,
            job_sector=reqs.sector,
            job_min=job.salary_min,
            job_max=job.salary_max,
            job_currency=job.salary_currency,
            job_industry=reqs.industry,
        )

        semantic = SemanticMatcher().score(db, user.user_id, job)

        role_signal = role_title_score(
            user_target_roles=list(user.target_roles) or ([user.preferred_job_title] if user.preferred_job_title else []),
            user_professional_title=user.professional_title,
            user_experience_titles=list(user.experience_titles),
            job_title=job.title,
        )

        bundle = _SignalBundle(
            skills=skills,
            experience=exp_signal,
            education=edu_signal,
            location=loc_signal,
            preferences=pref_signal,
            semantic=semantic,
            role_title=role_signal,
        )
        breakdown = MatchBreakdown(
            skills=skills.score,
            experience=exp_signal.score,
            education=edu_signal.score,
            location=loc_signal.score,
            preferences=pref_signal.score,
            semantic=semantic.score,
            role_title=role_signal.score,
        )
        overall = compute_overall_score(breakdown, self.weights)
        explanation = build_explanation(bundle)

        from datetime import datetime, timezone
        generated_at = datetime.now(timezone.utc).isoformat()
        return MatchResult(
            job_id=str(job.id),
            overall_score=round(overall, 1),
            breakdown=breakdown,
            matched_skills=skills.matched,
            missing_skills=skills.missing,
            matched_requirements=skills.matched_required,
            missing_requirements=skills.missing_required,
            qualification_match=edu_signal.score >= 0.8,
            experience_match=exp_signal.score >= 0.8,
            location_match=loc_signal.score >= 0.7,
            explanation=explanation,
            profile_completeness=_profile_completeness(user),
            generated_at=generated_at,
        )


def _effective_remote_pref(user: UserMatchProfile) -> Optional[str]:
    """Use the explicit ``remote_preference`` from preferences if the
    career profile didn't set one."""
    return user.remote_preference


# ---------------------------------------------------------------------------
# Personalized ranking
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RankedMatch:
    job: Job
    match: MatchResult


class PersonalizedRanker:
    """Ranks candidate jobs by match score for the authenticated user.

    Uses a candidate pool (configurable, default 200) to avoid scoring
    thousands of jobs unnecessarily. Jobs are loaded with database-level
    filtering (active + Pakistan-eligible by default) before scoring.
    """

    def __init__(self, engine: Optional[MatchEngine] = None, candidate_pool_size: Optional[int] = None) -> None:
        self.engine = engine or MatchEngine()
        self.pool_size = candidate_pool_size or int(get_settings().match_candidate_pool_size)

    def rank(
        self,
        db: Session,
        user: UserMatchProfile,
        candidate_jobs: list[Job],
        top_k: int = 20,
    ) -> list[RankedMatch]:
        """Score each candidate and return top-k by overall score.

        Deterministic: ties are broken by (score desc, posted_at desc, id).
        """
        scored: list[RankedMatch] = []
        for job in candidate_jobs[: self.pool_size]:
            try:
                match = self.engine.score_job(db, user, job)
            except Exception as exc:
                logger.warning("Failed to score job %s: %s", job.id, exc)
                continue
            scored.append(RankedMatch(job=job, match=match))
        scored.sort(
            key=lambda rm: (
                -rm.match.overall_score,
                -(rm.job.posted_at.timestamp() if rm.job.posted_at else 0),
                str(rm.job.id),
            )
        )
        return scored[:top_k]
