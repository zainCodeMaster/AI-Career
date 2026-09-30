"""User profile aggregator and semantic matcher for Phase 5 matching.

The ``UserProfileAggregator`` loads the authenticated user's career data
from Phase 2 (profile, skills, experience, education, certifications) and
Phase 4 (preferences) into a single ``UserMatchProfile`` object that the
matcher consumes.

The ``SemanticMatcher`` reuses the Phase 3 Career Brain to answer
"how similar is this job to the user's overall career profile?" without
ever leaking data across users.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.career_profile import CareerProfile
from app.db.models.certification import Certification
from app.db.models.education import Education
from app.db.models.jobs import Job, UserJobPreferences
from app.db.models.skill import Skill
from app.db.models.work_experience import WorkExperience
from app.services.career_brain import CareerBrainRetriever


# ---------------------------------------------------------------------------
# Aggregated user profile
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class UserMatchProfile:
    """Everything the matcher needs about the authenticated user."""

    user_id: str
    has_career_brain: bool
    professional_title: Optional[str] = None
    years_of_experience: Optional[int] = None
    preferred_job_title: Optional[str] = None
    preferred_location: Optional[str] = None
    remote_preference: Optional[str] = None
    skills: tuple[str, ...] = field(default_factory=tuple)
    experience_titles: tuple[str, ...] = field(default_factory=tuple)
    degrees: tuple[tuple[str, str], ...] = field(default_factory=tuple)  # (degree, field)
    target_roles: tuple[str, ...] = field(default_factory=tuple)
    preferred_cities: tuple[str, ...] = field(default_factory=tuple)
    preferred_provinces: tuple[str, ...] = field(default_factory=tuple)
    preferred_employment_types: tuple[str, ...] = field(default_factory=tuple)
    experience_level_pref: Optional[str] = None
    min_salary: Optional[float] = None
    salary_currency: Optional[str] = None
    sector_preference: Optional[str] = None
    selected_industries: tuple[str, ...] = field(default_factory=tuple)

    @property
    def has_any_data(self) -> bool:
        return bool(
            self.skills
            or self.professional_title
            or self.experience_titles
            or self.degrees
            or self.years_of_experience is not None
            or self.target_roles
            or self.preferred_cities
            or self.preferred_employment_types
        )


class UserProfileAggregator:
    """Loads the user's career data from Phase 2 + Phase 4."""

    @staticmethod
    def load(db: Session, user_id: UUID | str) -> UserMatchProfile:
        # Convert to UUID for compatibility with UUID(as_uuid=True) columns
        uid = UUID(str(user_id))

        profile = (
            db.query(CareerProfile).filter(CareerProfile.user_id == uid).first()
        )
        skills_rows = db.query(Skill).filter(Skill.user_id == uid).all()
        exp_rows = db.query(WorkExperience).filter(WorkExperience.user_id == uid).all()
        edu_rows = db.query(Education).filter(Education.user_id == uid).all()
        cert_rows = (
            db.query(Certification).filter(Certification.user_id == uid).all()
        )
        prefs_row = (
            db.query(UserJobPreferences)
            .filter(UserJobPreferences.user_id == uid)
            .first()
        )

        def _json_list(value: Optional[str]) -> list[str]:
            if not value:
                return []
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [str(x) for x in parsed]
            except (ValueError, TypeError):
                pass
            return []

        return UserMatchProfile(
            user_id=uid,
            has_career_brain=bool(skills_rows) or bool(exp_rows) or bool(edu_rows) or bool(cert_rows) or bool(profile),
            professional_title=profile.professional_title if profile else None,
            years_of_experience=profile.years_of_experience if profile else None,
            preferred_job_title=profile.preferred_job_title if profile else None,
            preferred_location=profile.preferred_location if profile else None,
            remote_preference=profile.remote_preference if profile else None,
            skills=tuple(s.name for s in skills_rows if s.name),
            experience_titles=tuple(e.job_title for e in exp_rows if e.job_title),
            degrees=tuple(
                (e.degree or "", e.field_of_study or "")
                for e in edu_rows
            ),
            target_roles=tuple(_json_list(prefs_row.target_roles) if prefs_row else []),
            preferred_cities=tuple(_json_list(prefs_row.preferred_cities) if prefs_row else []),
            preferred_provinces=tuple(_json_list(prefs_row.preferred_provinces) if prefs_row else []),
            preferred_employment_types=tuple(_json_list(prefs_row.employment_types) if prefs_row else []),
            experience_level_pref=prefs_row.experience_level if prefs_row else None,
            min_salary=prefs_row.min_salary if prefs_row else None,
            salary_currency=prefs_row.salary_currency if prefs_row else None,
            sector_preference=prefs_row.sector_preference if prefs_row else None,
            selected_industries=tuple(_json_list(prefs_row.selected_industries) if prefs_row else []),
        )


# ---------------------------------------------------------------------------
# Semantic match (reuses Phase 3 Career Brain)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SemanticSignal:
    score: float  # 0.0–1.0
    reason: str
    unavailable: bool = False
    top_evidence: tuple[str, ...] = field(default_factory=tuple)


class SemanticMatcher:
    """Uses the user's Career Brain to score how well the job fits their
    overall career profile. Falls back to a neutral 0.5 if no Career Brain
    data exists. Always user-scoped."""

    def __init__(self) -> None:
        self._retriever = CareerBrainRetriever()

    def score(
        self,
        db: Session,
        user_id: UUID | str,
        job: Job,
    ) -> SemanticSignal:
        uid = UUID(str(user_id)) if not isinstance(user_id, UUID) else user_id
        # Build a query that captures the job's primary characteristics.
        query_parts = [job.title or "", job.company_name or "", job.description or ""]
        query = " ".join(p for p in query_parts if p).strip() or job.title or ""
        if not query:
            return SemanticSignal(
                score=0.5,
                reason="Job has insufficient text for semantic matching.",
                unavailable=True,
            )

        try:
            chunks = self._retriever.search(db, uid, query, top_k=5)
        except Exception:
            return SemanticSignal(
                score=0.5,
                reason="Career Brain retrieval unavailable for this user.",
                unavailable=True,
            )

        if not chunks:
            return SemanticSignal(
                score=0.5,
                reason="No Career Brain data for this user — semantic signal unavailable.",
                unavailable=True,
            )

        # Use the best chunk score (already in [0, 1]) as the semantic signal.
        best = max(c.score for c in chunks)
        top_evidence = tuple(
            c.title or "(untitled)" for c in sorted(chunks, key=lambda x: -x.score)[:3]
        )
        return SemanticSignal(
            score=best,
            reason=f"Semantic similarity to your career profile (top: {top_evidence[0] if top_evidence else 'n/a'}).",
            top_evidence=top_evidence,
        )
