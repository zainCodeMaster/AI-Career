"""Experience, education, location, and preference matchers.

Each matcher is a small deterministic function that takes structured user
data and structured job data and returns a ``MatchSignal`` (a 0.0–1.0 score
plus a human-readable note). Signals are composed by the scorer in
``match_engine.py``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# ---------------------------------------------------------------------------
# Experience
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExperienceSignal:
    score: float  # 0.0–1.0
    user_years: Optional[int]
    job_min: Optional[int]
    job_max: Optional[int]
    is_internship_or_entry: bool
    reason: str  # human-readable, always present
    unavailable: bool = False


def experience_score(
    user_years: Optional[int],
    job_min: Optional[int],
    job_max: Optional[int],
    *,
    is_internship_or_entry: bool = False,
) -> ExperienceSignal:
    """Compare user experience against the job's experience range.

    - If both sides are unknown, the signal is unavailable and scored 0.5
      (neutral). The explanation will say "unavailable".
    - For internships/entry-level roles, lack of experience is NOT
      penalized — the user is expected to be early-career.
    - Otherwise, a 5-year absolute tolerance window is applied: experience
      slightly above the job max is not penalized (e.g. 7 yrs for a 5–6 yr
      role still scores highly) to avoid penalizing over-qualified
      candidates. Experience below the job minimum is penalized linearly.
    """
    if user_years is None or (job_min is None and job_max is None):
        return ExperienceSignal(
            score=0.5,
            user_years=user_years,
            job_min=job_min,
            job_max=job_max,
            is_internship_or_entry=is_internship_or_entry,
            reason="Experience data unavailable; signal treated as neutral.",
            unavailable=True,
        )

    if is_internship_or_entry:
        return ExperienceSignal(
            score=1.0,
            user_years=user_years,
            job_min=job_min,
            job_max=job_max,
            is_internship_or_entry=True,
            reason="Internship/entry-level role — experience requirement waived.",
        )

    # If job has no experience requirement at all, user matches fully.
    if job_min is None and job_max is None:
        return ExperienceSignal(
            score=1.0,
            user_years=user_years,
            job_min=None,
            job_max=None,
            is_internship_or_entry=False,
            reason="No experience requirement stated.",
        )

    # If user is above the upper bound + 5-year tolerance window, slight
    # penalty (over-qualified but still close).
    ceiling = (job_max or job_min) + 5
    floor = job_min

    if user_years >= floor and user_years <= ceiling:
        # In range: full credit.
        if job_max is not None and user_years > job_max:
            return ExperienceSignal(
                score=0.9,
                user_years=user_years,
                job_min=job_min,
                job_max=job_max,
                is_internship_or_entry=False,
                reason=f"Meets the experience requirement ({job_min}–{job_max} yrs).",
            )
        return ExperienceSignal(
            score=1.0,
            user_years=user_years,
            job_min=job_min,
            job_max=job_max,
            is_internship_or_entry=False,
            reason=f"Meets the experience requirement ({job_min}–{job_max} yrs).",
        )

    if user_years < floor:
        # Below requirement: linear penalty.
        gap = floor - user_years
        score = max(0.0, 1.0 - gap * 0.2)
        return ExperienceSignal(
            score=score,
            user_years=user_years,
            job_min=job_min,
            job_max=job_max,
            is_internship_or_entry=False,
            reason=(
                f"Experience below the {job_min}–{job_max or job_min} yr requirement "
                f"(gap: {gap} yr)."
            ),
        )

    # Over the ceiling.
    return ExperienceSignal(
        score=0.85,
        user_years=user_years,
        job_min=job_min,
        job_max=job_max,
        is_internship_or_entry=False,
        reason=f"Experience above requirement ({job_min}–{job_max} yrs); over-qualified.",
    )


# ---------------------------------------------------------------------------
# Education
# ---------------------------------------------------------------------------


_DEGREE_LEVEL: dict[str, int] = {
    "phd": 4,
    "doctorate": 4,
    "masters": 3,
    "master": 3,
    "msc": 3,
    "ms": 3,
    "mba": 3,
    "bachelors": 2,
    "bachelor": 2,
    "bsc": 2,
    "bs": 2,
    "bba": 2,
    "associate": 1,
    "diploma": 1,
    "high school": 0,
    "intermediate": 0,
    "matric": 0,
    "matriculation": 0,
}


# Field-of-study compatibility groups. A user with a degree in any key of a
# group satisfies a job requirement for any other key in the same group.
_FIELD_GROUPS: list[set[str]] = [
    {"computer science", "computerscience", "cs", "software engineering", "softwareengineering",
     "information technology", "informationtechnology", "it", "computer engineering",
     "computerengineering", "computing"},
    {"electrical engineering", "electricalengineering", "electronics", "telecommunications",
     "telecom"},
    {"mechanical engineering", "mechanicalengineering", "mechanical"},
    {"civil engineering", "civilengineering"},
    {"business administration", "businessadministration", "business", "commerce", "mba",
     "marketing", "finance", "accounting"},
    {"data science", "datascience", "statistics", "mathematics", "applied mathematics"},
    {"biology", "biotechnology", "biomedical engineering", "biomedicalengineering", "bioinformatics"},
    {"economics", "finance", "accounting"},
    {"english", "literature", "linguistics"},
    {"physics", "applied physics"},
    {"chemistry", "chemical engineering", "chemicalengineering"},
]


def _normalize_field(value: str) -> str:
    """Normalize a field-of-study string for comparison."""
    s = value.lower().strip()
    s = s.replace("-", " ").replace("/", " ")
    s = "".join(ch for ch in s if ch.isalnum() or ch.isspace())
    s = " ".join(s.split())
    # Remove degree-level prefixes.
    for prefix in ("bachelor of", "master of", "bachelors in", "masters in",
                   "bsc in", "msc in", "bs in", "ms in", "phd in", "doctorate in",
                   "bachelor in", "master in", "associate in", "diploma in"):
        if s.startswith(prefix + " "):
            s = s[len(prefix) + 1:]
            break
    return s.strip()


def _field_in_any_group(field: str) -> int:
    """Return the group index if the field belongs to one, else -1."""
    for idx, group in enumerate(_FIELD_GROUPS):
        if field in group:
            return idx
    return -1


def _degree_level(value: str | None) -> Optional[int]:
    if not value:
        return None
    key = value.lower().strip()
    key = key.replace("'s", "s").replace("'", "")
    return _DEGREE_LEVEL.get(key)


def _extract_required_level(text: str) -> Optional[int]:
    """Extract the minimum degree level implied by a free-text requirement."""
    text_l = text.lower()
    for keyword, level in _DEGREE_LEVEL.items():
        if keyword in text_l:
            return max(level, _extract_required_level(text_l.replace(keyword, "")) or 0)
    # Common abbreviations
    if "bs " in text_l or " bs," in text_l or " bsc" in text_l:
        return _DEGREE_LEVEL["bs"]
    if "ms " in text_l or " ms," in text_l or " msc" in text_l:
        return _DEGREE_LEVEL["ms"]
    if "phd" in text_l or "doctorate" in text_l:
        return _DEGREE_LEVEL["phd"]
    return None


@dataclass(frozen=True)
class EducationSignal:
    score: float
    reason: str
    required_level: Optional[int] = None
    user_level: Optional[int] = None
    field_compatible: Optional[bool] = None
    unavailable: bool = False


def education_score(
    user_degrees: list[tuple[str, str]],  # list of (degree, field_of_study)
    job_education_text: Optional[str],
) -> EducationSignal:
    """Compare user education against a job's education requirement.

    ``user_degrees`` is a list of ``(degree, field_of_study)`` pairs. The
    matcher uses the highest user degree level and checks field compatibility
    against the job's free-text requirement.
    """
    if not job_education_text or not job_education_text.strip():
        return EducationSignal(
            score=0.5,
            reason="No education requirement stated; signal treated as neutral.",
            unavailable=True,
        )

    job_text = job_education_text.lower()
    required_level = _extract_required_level(job_text)

    if not user_degrees:
        return EducationSignal(
            score=0.4 if required_level is not None else 0.5,
            reason="User has no education data on file.",
            required_level=required_level,
            unavailable=True,
        )

    # Use the highest user degree level.
    best_user_level = -1
    for degree, _field in user_degrees:
        lvl = _degree_level(degree) if degree else None
        if lvl is not None and lvl > best_user_level:
            best_user_level = lvl

    if best_user_level < 0:
        user_level = None
    else:
        user_level = best_user_level

    # Field compatibility: if the job mentions a field the user has, or one
    # in the same compatibility group, treat as compatible.
    job_text_norm = job_text
    field_compatible: Optional[bool] = None
    for _degree, user_field in user_degrees:
        norm = _normalize_field(user_field or "")
        if not norm:
            continue
        if norm in job_text_norm or any(
            group_member in job_text_norm
            for group in _FIELD_GROUPS
            for group_member in group
            if _field_in_any_group(norm) == _field_in_any_group(group_member) and norm != group_member
        ):
            field_compatible = True
            break

    if field_compatible is None and any(
        kw in job_text_norm for kw in ("degree", "bachelor", "master", "phd", "bs", "ms", "education", "qualification")
    ):
        # Job explicitly mentions a field we cannot parse → conservative.
        field_compatible = None

    if required_level is None:
        # No explicit level stated; fall back to field compatibility if any.
        if field_compatible is True:
            return EducationSignal(
                score=1.0,
                reason="Field of study matches the role.",
                user_level=user_level,
                required_level=None,
                field_compatible=True,
            )
        return EducationSignal(
            score=0.5,
            reason="No explicit degree level required.",
            user_level=user_level,
            required_level=None,
            field_compatible=field_compatible,
            unavailable=True,
        )

    if user_level is None:
        return EducationSignal(
            score=0.3,
            reason="User's degree level could not be determined.",
            user_level=None,
            required_level=required_level,
            field_compatible=field_compatible,
            unavailable=True,
        )

    if user_level >= required_level:
        return EducationSignal(
            score=1.0 if field_compatible is not False else 0.8,
            reason=(
                f"Meets education requirement (level {user_level} ≥ required {required_level})."
                if field_compatible is not False
                else f"Meets degree level but field of study may differ."
            ),
            user_level=user_level,
            required_level=required_level,
            field_compatible=field_compatible,
        )

    # Below required level.
    gap = required_level - user_level
    return EducationSignal(
        score=max(0.0, 0.6 - 0.3 * gap),
        reason=(
            f"Degree level ({user_level}) below required ({required_level})."
        ),
        user_level=user_level,
        required_level=required_level,
        field_compatible=field_compatible,
    )


# ---------------------------------------------------------------------------
# Location
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LocationSignal:
    score: float
    reason: str
    user_cities: tuple[str, ...]
    user_provinces: tuple[str, ...]
    remote_preference: Optional[str]
    job_city: Optional[str]
    job_province: Optional[str]
    job_workplace_type: Optional[str]
    job_remote: bool
    unavailable: bool = False


def _norm_loc(value: str | None) -> str:
    if not value:
        return ""
    return value.strip().lower()


def location_score(
    user_cities: list[str],
    user_provinces: list[str],
    remote_preference: Optional[str],
    job_city: Optional[str],
    job_province: Optional[str],
    job_workplace_type: Optional[str],
    job_remote: bool,
) -> LocationSignal:
    """Score location/workplace compatibility.

    Rules (in priority order):
    1. If the user wants remote-only and the job is remote → strong match.
    2. If the job is remote and the user has not excluded remote → strong match.
    3. Exact city match → strong match.
    4. Same province → partial match.
    5. Otherwise → mismatch.
    """
    cities = tuple(_norm_loc(c) for c in user_cities if c)
    provinces = tuple(_norm_loc(p) for p in user_provinces if p)
    jcity = _norm_loc(job_city)
    jprov = _norm_loc(job_province)
    jwtype = _norm_loc(job_workplace_type)

    is_remote_job = job_remote or jwtype == "remote"
    is_hybrid_job = jwtype == "hybrid"
    is_onsite_job = jwtype == "onsite" or (not is_remote_job and not is_hybrid_job)

    pref = _norm_loc(remote_preference) if remote_preference else ""

    if not cities and not provinces and not pref and not jcity and not jprov and not jwtype and not job_remote:
        return LocationSignal(
            score=0.5,
            reason="Location preference and job location both unavailable.",
            user_cities=cities,
            user_provinces=provinces,
            remote_preference=remote_preference,
            job_city=job_city,
            job_province=job_province,
            job_workplace_type=job_workplace_type,
            job_remote=job_remote,
            unavailable=True,
        )

    # 1. User wants remote-only and job is remote
    if pref == "remote_only" and is_remote_job:
        return LocationSignal(
            score=1.0,
            reason="Remote job matches your remote-only preference.",
            user_cities=cities,
            user_provinces=provinces,
            remote_preference=remote_preference,
            job_city=job_city,
            job_province=job_province,
            job_workplace_type=job_workplace_type,
            job_remote=job_remote,
        )

    # 2. Job is remote, user has not excluded remote
    if is_remote_job and pref != "onsite_ok":
        return LocationSignal(
            score=0.9,
            reason="Remote job — compatible with your workplace preferences.",
            user_cities=cities,
            user_provinces=provinces,
            remote_preference=remote_preference,
            job_city=job_city,
            job_province=job_province,
            job_workplace_type=job_workplace_type,
            job_remote=job_remote,
        )

    # 3. Exact city match
    if jcity and cities and jcity in cities:
        return LocationSignal(
            score=1.0,
            reason=f"Job is located in {job_city}, one of your preferred cities.",
            user_cities=cities,
            user_provinces=provinces,
            remote_preference=remote_preference,
            job_city=job_city,
            job_province=job_province,
            job_workplace_type=job_workplace_type,
            job_remote=job_remote,
        )

    # 4. Same province
    if jprov and provinces and jprov in provinces:
        return LocationSignal(
            score=0.75,
            reason=f"Job is in {job_province or jprov.title()}, one of your preferred provinces.",
            user_cities=cities,
            user_provinces=provinces,
            remote_preference=remote_preference,
            job_city=job_city,
            job_province=job_province,
            job_workplace_type=job_workplace_type,
            job_remote=job_remote,
        )

    # 5. User prefers on-site only and job is remote/other city → mismatch
    if pref == "onsite_ok" and is_remote_job:
        return LocationSignal(
            score=0.2,
            reason="Remote job does not match your on-site preference.",
            user_cities=cities,
            user_provinces=provinces,
            remote_preference=remote_preference,
            job_city=job_city,
            job_province=job_province,
            job_workplace_type=job_workplace_type,
            job_remote=job_remote,
        )

    if (jcity or jprov) and (cities or provinces):
        return LocationSignal(
            score=0.3,
            reason=f"Job location ({job_city or job_province}) is outside your preferred areas.",
            user_cities=cities,
            user_provinces=provinces,
            remote_preference=remote_preference,
            job_city=job_city,
            job_province=job_province,
            job_workplace_type=job_workplace_type,
            job_remote=job_remote,
        )

    # Only one side has data → neutral
    return LocationSignal(
        score=0.5,
        reason="Location data is partial; unable to determine fit.",
        user_cities=cities,
        user_provinces=provinces,
        remote_preference=remote_preference,
        job_city=job_city,
        job_province=job_province,
        job_workplace_type=job_workplace_type,
        job_remote=job_remote,
        unavailable=True,
    )


# ---------------------------------------------------------------------------
# Preferences (employment type, sector, salary, industries)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PreferenceSignal:
    score: float
    reason: str
    employment_match: Optional[bool] = None
    sector_match: Optional[bool] = None
    salary_match: Optional[bool] = None
    industry_match: Optional[bool] = None
    unavailable: bool = False


def _norm_set(values: list[str] | None) -> set[str]:
    if not values:
        return set()
    return {_norm_loc(v) for v in values if v}


def preference_score(
    user_employment_types: list[str] | None,
    user_sector_preference: Optional[str],
    user_min_salary: Optional[float],
    user_salary_currency: Optional[str],
    user_selected_industries: list[str] | None,
    job_employment_type: Optional[str],
    job_sector: Optional[str],
    job_min: Optional[float],
    job_max: Optional[float],
    job_currency: Optional[str],
    job_industry: Optional[str],
) -> PreferenceSignal:
    """Score against user-stated job preferences."""
    reasons: list[str] = []
    sub_scores: list[float] = []
    emp_match: Optional[bool] = None
    sec_match: Optional[bool] = None
    sal_match: Optional[bool] = None
    ind_match: Optional[bool] = None

    # Employment type
    if user_employment_types:
        allowed = _norm_set(user_employment_types)
        if allowed and job_employment_type:
            emp_match = _norm_loc(job_employment_type) in allowed
            sub_scores.append(1.0 if emp_match else 0.0)
            reasons.append(
                "Employment type matches your preferences." if emp_match
                else f"Employment type ({job_employment_type}) is outside your preferred types."
            )

    # Sector
    sector_pref = _norm_loc(user_sector_preference) if user_sector_preference else ""
    if sector_pref and sector_pref != "any" and job_sector:
        sec_match = _norm_loc(job_sector) == sector_pref
        sub_scores.append(1.0 if sec_match else 0.0)
        reasons.append(
            f"Sector matches your preference ({job_sector})." if sec_match
            else f"Sector ({job_sector}) does not match your preference ({user_sector_preference})."
        )

    # Salary
    if user_min_salary is not None and (job_min is not None or job_max is not None):
        # Require the same currency to compare. If currencies differ or are
        # unknown, mark as unavailable.
        if user_salary_currency and job_currency and user_salary_currency.upper() != job_currency.upper():
            sal_match = None
            reasons.append(f"Currency differs ({user_salary_currency} vs {job_currency}).")
        else:
            ceiling = job_max if job_max is not None else job_min
            sal_match = ceiling is not None and ceiling >= user_min_salary
            sub_scores.append(1.0 if sal_match else 0.0)
            if sal_match:
                reasons.append("Salary range meets your minimum.")
            else:
                reasons.append("Salary range is below your stated minimum.")

    # Industries
    user_ind = _norm_set(user_selected_industries)
    if user_ind and job_industry:
        job_ind_norm = _norm_loc(job_industry)
        ind_match = job_ind_norm in user_ind
        sub_scores.append(1.0 if ind_match else 0.0)
        reasons.append(
            "Industry matches your selected industries." if ind_match
            else f"Industry ({job_industry}) is outside your selected industries."
        )

    if not sub_scores:
        return PreferenceSignal(
            score=0.5,
            reason="No job preferences set; signal treated as neutral.",
            unavailable=True,
        )

    return PreferenceSignal(
        score=sum(sub_scores) / len(sub_scores),
        reason=" ".join(reasons) if reasons else "Preferences evaluated.",
        employment_match=emp_match,
        sector_match=sec_match,
        salary_match=sal_match,
        industry_match=ind_match,
    )


# ---------------------------------------------------------------------------
# Role / title similarity
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RoleTitleSignal:
    score: float
    reason: str
    matched_role: Optional[str] = None
    unavailable: bool = False


def role_title_score(
    user_target_roles: list[str] | None,
    user_professional_title: Optional[str],
    user_experience_titles: list[str] | None,
    job_title: str,
) -> RoleTitleSignal:
    """Score how well the job title matches the user's target roles.

    Combines the user's declared target roles, current professional title,
    and prior job titles (from WorkExperience). The best match wins.
    """
    candidates: list[str] = []
    if user_target_roles:
        candidates.extend(user_target_roles)
    if user_professional_title:
        candidates.append(user_professional_title)
    if user_experience_titles:
        candidates.extend(user_experience_titles)

    if not candidates or not job_title:
        return RoleTitleSignal(
            score=0.5,
            reason="No target roles or job title available for comparison.",
            unavailable=not candidates,
        )

    job_norm = _norm_loc(job_title)
    # Token overlap
    job_tokens = set(job_norm.split())
    best = 0.0
    best_role: Optional[str] = None
    for cand in candidates:
        cand_norm = _norm_loc(cand)
        if not cand_norm:
            continue
        # Exact or substring match
        if cand_norm == job_norm or cand_norm in job_norm or job_norm in cand_norm:
            score = 1.0
        else:
            cand_tokens = set(cand_norm.split())
            if not cand_tokens:
                continue
            score = len(job_tokens & cand_tokens) / max(1, len(job_tokens | cand_tokens))
        if score > best:
            best = score
            best_role = cand

    if best >= 0.8:
        return RoleTitleSignal(
            score=best,
            matched_role=best_role,
            reason=f"Job title matches your role profile ({best_role}).",
        )
    if best >= 0.4:
        return RoleTitleSignal(
            score=best,
            matched_role=best_role,
            reason="Job title is related to your role profile.",
        )
    return RoleTitleSignal(
        score=best,
        matched_role=best_role,
        reason="Job title is not closely related to your target roles.",
    )
