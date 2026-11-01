"""Job normalization pipeline.

Converts raw source data (a dict or a ``RawJob`` dataclass) into a normalized
``NormalizedJob`` dataclass that can be persisted to the ``Job`` model.

Normalization responsibilities:
- Clean and standardize text fields (title, company, location, province)
- Map free-form employment / workplace types to a controlled vocabulary
- Parse salary, dates, and experience ranges
- Compute a deterministic ``content_hash`` and ``normalized_hash`` for
  deduplication
- Never invent information that the source did not provide; missing data
  stays as ``None`` or empty
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

# Controlled vocabularies
EMPLOYMENT_TYPES: dict[str, str] = {
    "full_time": "full_time",
    "full-time": "full_time",
    "fulltime": "full_time",
    "permanent": "full_time",
    "part_time": "part_time",
    "part-time": "part_time",
    "parttime": "part_time",
    "contract": "contract",
    "contractual": "contract",
    "temporary": "temporary",
    "temp": "temporary",
    "internship": "internship",
    "intern": "internship",
    "graduate": "graduate",
    "trainee": "trainee",
    "apprenticeship": "apprenticeship",
    "freelance": "freelance",
    "project": "project",
}

WORKPLACE_TYPES = {"remote", "hybrid", "onsite"}

# Pakistan provinces
PAKISTAN_PROVINCES: set[str] = {
    "punjab",
    "sindh",
    "khyber pakhtunkhwa",
    "kp",
    "balochistan",
    "islamabad capital territory",
    "ict",
    "azad jammu and kashmir",
    "ajk",
    "gilgit-baltistan",
    "gb",
    "fata",
}

# Major cities (used to infer city from a free-form location string)
PAKISTAN_CITIES: set[str] = {
    "karachi", "lahore", "islamabad", "rawalpindi", "faisalabad",
    "multan", "peshawar", "quetta", "sialkot", "gujranwala",
    "hyderabad", "bahawalpur", "abbottabad", "mardan", "sargodha",
    "sahiwal", "okara", "rahim yar khan", "kasur", "jhelum",
    "sheikhupura", "gujrat", "dera ghazi khan", "sahiwal", "mirpur",
    "muzaffarabad", "gilgit", "skardu", "turbat", "quetta",
    "mingora", "bannu", "abbottabad", "nowshera", "charsadda",
}

_WHITESPACE = re.compile(r"\s+")
_NON_ALNUM = re.compile(r"[^a-z0-9\s]")
_SALARY_RANGE = re.compile(
    r"(?P<cur>PKR|RS|USD|€|EUR|£|GBP|\$)?\s*"
    r"(?P<min>[\d,]+(?:\.\d+)?)\s*"
    r"(?:-\s*|–\s*|to\s*)?"
    r"(?P<max>[\d,]+(?:\.\d+)?)?",
    re.IGNORECASE,
)


def _normalize_text(value: Optional[str]) -> Optional[str]:
    """Lowercase, collapse whitespace, strip punctuation for hashing/matching."""
    if value is None:
        return None
    cleaned = _NON_ALNUM.sub(" ", value.lower())
    cleaned = _WHITESPACE.sub(" ", cleaned).strip()
    return cleaned or None


def _stable_id(*parts: Optional[str]) -> str:
    """Build a deterministic string for hashing."""
    return "|".join((p or "").strip().lower() for p in parts)


def compute_content_hash(raw: dict[str, Any] | "RawJob") -> str:
    """Hash of the *raw* source payload — detects changes to the underlying listing."""
    if isinstance(raw, RawJob):
        blob = _stable_id(
            raw.source,
            raw.source_job_id,
            raw.title,
            raw.company_name,
            raw.description,
            raw.location,
        )
    else:
        blob = _stable_id(
            str(raw.get("source", "")),
            str(raw.get("source_job_id", "")),
            str(raw.get("title", "")),
            str(raw.get("company_name", "")),
            str(raw.get("description", "")),
            str(raw.get("location", "")),
        )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def compute_normalized_hash(title: str, company: str, city: str, province: str) -> str:
    """Hash of the *normalized* identity — used to detect cross-source duplicates."""
    blob = _stable_id(
        _normalize_text(title),
        _normalize_text(company),
        _normalize_text(city),
        _normalize_text(province),
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


@dataclass
class RawJob:
    """Minimal raw job representation produced by a JobSource adapter."""

    source: str
    source_job_id: str
    source_url: Optional[str] = None
    title: str = ""
    company_name: str = ""
    company_url: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    responsibilities: Optional[str] = None
    skills: Optional[str] = None
    employment_type: Optional[str] = None
    workplace_type: Optional[str] = None
    department: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    salary_period: Optional[str] = None
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    education_requirements: Optional[str] = None
    posted_at: Optional[datetime] = None
    closing_at: Optional[datetime] = None
    is_remote: bool = False
    # Deprecated: use eligibility field instead (kept for test compatibility)
    is_pakistan_eligible: bool = True
    # Single canonical three-state eligibility: eligible | ineligible | unknown
    eligibility: Optional[str] = None
    eligibility_reason: Optional[str] = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizedJob:
    """A normalized, deduplicatable job ready for persistence."""

    source: str
    source_job_id: str
    source_url: Optional[str]
    title: str
    company_name: str
    company_url: Optional[str]
    description: Optional[str]
    requirements: Optional[str]
    responsibilities: Optional[str]
    skills: Optional[str]
    employment_type: Optional[str]
    workplace_type: Optional[str]
    department: Optional[str]
    category: Optional[str]
    location: Optional[str]
    city: Optional[str]
    province: Optional[str]
    country: str
    is_remote: bool
    # Single canonical three-state eligibility: eligible | ineligible | unknown
    eligibility: Optional[str]
    eligibility_reason: Optional[str]
    salary_min: Optional[float]
    salary_max: Optional[float]
    salary_currency: Optional[str]
    salary_period: Optional[str]
    experience_min: Optional[int]
    experience_max: Optional[int]
    education_requirements: Optional[str]
    posted_at: Optional[datetime]
    closing_at: Optional[datetime]
    status: str
    is_active: bool
    raw_source_metadata: str
    content_hash: str
    normalized_hash: str

    @property
    def is_pakistan_eligible(self) -> bool:
        """Backward compatibility: map three-state eligibility to boolean."""
        return self.eligibility == "eligible"


def _detect_workplace_type(text: Optional[str], explicit: Optional[str]) -> str:
    if explicit:
        e = explicit.lower().strip()
        if e in ("remote", "work_from_home", "wfh"):
            return "remote"
        if e in ("hybrid",):
            return "hybrid"
        if e in ("onsite", "on_site", "on-site", "office"):
            return "onsite"
    if not text:
        return "onsite"
    t = text.lower()
    if "remote" in t or "work from home" in t:
        return "remote"
    if "hybrid" in t:
        return "hybrid"
    return "onsite"


def _detect_employment_type(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    key = value.lower().strip().replace(" ", "_").replace("-", "_")
    if key in EMPLOYMENT_TYPES:
        return EMPLOYMENT_TYPES[key]
    for needle, mapped in EMPLOYMENT_TYPES.items():
        if needle.replace("_", " ") in value.lower():
            return mapped
    return None


def _detect_province(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    t = text.lower()
    for prov in PAKISTAN_PROVINCES:
        if prov in t:
            # Normalize KP variants
            if prov == "kp":
                return "Khyber Pakhtunkhwa"
            if prov == "ict":
                return "Islamabad Capital Territory"
            if prov == "ajk":
                return "Azad Jammu and Kashmir"
            if prov == "gb":
                return "Gilgit-Baltistan"
            return prov.title()
    # If the city is Islamabad, the province is ICT
    if "islamabad" in t:
        return "Islamabad Capital Territory"
    # If the city is a known provincial capital, infer the province
    city_to_province = {
        "karachi": "Sindh",
        "lahore": "Punjab",
        "peshawar": "Khyber Pakhtunkhwa",
        "quetta": "Balochistan",
    }
    for city, prov in city_to_province.items():
        if city in t:
            return prov
    return None


def _detect_city(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    t = text.lower()
    for city in PAKISTAN_CITIES:
        if city in t:
            return city.title()
    return None


def _detect_country(text: Optional[str]) -> Optional[str]:
    """Detect country from explicit location text without guessing."""
    if not text:
        return ""
    t = text.lower()
    
    # Pakistan locations
    pakistan_indicators = [
        "pakistan", "pk", "lahore", "karachi", "islamabad", "rawalpindi", 
        "faisalabad", "multan", "peshawar", "quetta", "sialkot", "gujranwala",
        "punjab", "sindh", "khyber", "balochistan", "islamabad capital territory",
        "azad jammu", "gilgit", "baltistan"
    ]
    if any(indicator in t for indicator in pakistan_indicators):
        return "PK"
    
    # International locations
    if any(loc in t for loc in ["united states", "usa", " u.s.", "us ", "us,", "us.", "us-", "america", "new york", "ny ", "ny,", "ny.", "ny-", "california", "ca ", "ca,", "ca.", "ca-", "texas", "tx ", "tx,", "tx.", "tx-", "florida", "fl ", "fl,", "fl.", "fl-", "washington", "wa ", "wa,", "wa.", "wa-", "illinois", "il ", "il,", "il.", "il-", "massachusetts", "ma ", "ma,", "ma.", "ma-", "boston", "chicago", "los angeles", "san francisco", "seattle", "austin", "denver"]):
        return "US"
    if any(loc in t for loc in ["united kingdom", "uk", "britain", "england", "london", "manchester", "birmingham"]):
        return "GB"
    if any(loc in t for loc in ["canada", "ca ", "ca,", "ca.", "ca-", "toronto", "vancouver", "montreal"]):
        return "CA"
    if any(loc in t for loc in ["australia", "au ", "au,", "au.", "au-", "sydney", "melbourne"]):
        return "AU"
    if any(loc in t for loc in ["germany", "de ", "de,", "de.", "de-", "berlin", "munich"]):
        return "DE"
    if any(loc in t for loc in ["united arab emirates", "uae", "dubai", "abu dhabi"]):
        return "AE"
    if any(loc in t for loc in ["saudi arabia", "saudi", "riyadh", "jeddah"]):
        return "SA"
    if any(loc in t for loc in ["singapore", "sg "]):
        return "SG"
    if any(loc in t for loc in ["malaysia", "my "]):
        return "MY"
    if any(loc in t for loc in ["remote worldwide", "worldwide", "anywhere", "global"]):
        return "WW"
    
    # Unknown locations must not be assumed to be in Pakistan
    return ""


def _parse_salary(text: Optional[str]) -> tuple[Optional[float], Optional[float], Optional[str], Optional[str]]:
    """Best-effort salary parser. Returns (min, max, currency, period)."""
    if not text:
        return None, None, None, None
    m = _SALARY_RANGE.search(text)
    if not m:
        return None, None, None, None
    cur = (m.group("cur") or "").upper() or None
    if cur == "RS":
        cur = "PKR"
    if cur == "$":
        cur = "USD"
    raw_min = m.group("min").replace(",", "")
    raw_max = (m.group("max") or "").replace(",", "")
    try:
        smin = float(raw_min)
    except ValueError:
        return None, None, cur, None
    smax: Optional[float]
    if raw_max:
        try:
            smax = float(raw_max)
        except ValueError:
            smax = None
    else:
        smax = None
    period = "monthly" if "month" in text.lower() else ("yearly" if "year" in text.lower() or "annual" in text.lower() else None)
    return smin, smax, cur, period


def _safe_str(value: Any, max_len: int = 1000) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    if len(s) > max_len:
        s = s[: max_len - 1] + "…"
    return s


def normalize(raw: RawJob) -> NormalizedJob:
    """Convert a RawJob into a NormalizedJob."""
    title = _safe_str(raw.title, max_len=512) or ""
    company = _safe_str(raw.company_name, max_len=512) or ""
    location = _safe_str(raw.location, max_len=512)

    city = _detect_city(location) or _detect_city(raw.description)
    province = _detect_province(location) or _detect_province(raw.description)

    workplace = _detect_workplace_type(location, raw.workplace_type)
    is_remote = workplace == "remote" or bool(raw.is_remote)
    employment = _detect_employment_type(raw.employment_type)

    # Salary — prefer explicit fields, else parse from text fields
    if raw.salary_min is not None or raw.salary_max is not None:
        smin, smax, scur, speriod = raw.salary_min, raw.salary_max, raw.salary_currency, raw.salary_period
        if smin is None and smax is not None:
            smin = smax
        if smax is None and smin is not None:
            smax = smin
    else:
        smin, smax, scur, speriod = _parse_salary(raw.description) or _parse_salary(raw.title) or (None, None, None, None)

    posted = raw.posted_at
    if posted is not None and posted.tzinfo is None:
        posted = posted.replace(tzinfo=timezone.utc)
    closing = raw.closing_at
    if closing is not None and closing.tzinfo is None:
        closing = closing.replace(tzinfo=timezone.utc)

    content_hash = compute_content_hash(raw)
    normalized_hash = compute_normalized_hash(title, company, city or "", province or "")

    import json
    raw_meta = json.dumps({"extra": raw.extra} if raw.extra else {}, ensure_ascii=False)

    # Determine eligibility: prioritize explicit is_pakistan_eligible=False, 
    # then map eligibility string, then fall back to boolean
    raw_eligibility = raw.eligibility
    is_pak_eligible = raw.is_pakistan_eligible
    
    # If explicitly set to False, use ineligible
    if is_pak_eligible is False and raw_eligibility in (None, "Open to Pakistani citizens"):
        eligibility = "ineligible"
    elif raw_eligibility:
        elig_lower = raw_eligibility.lower()
        if any(kw in elig_lower for kw in ["eligible", "accept", "open to pak", "pakistan accepted", "pakistan welcome", "worldwide", "anywhere", "global"]):
            eligibility = "eligible"
        elif any(kw in elig_lower for kw in ["ineligible", "not eligible", "not accept", "restricted to", "only us", "only usa", "usa only", "us only", "uk only", "eu only", "europe only"]):
            eligibility = "ineligible"
        else:
            # Unknown string, fall back to boolean
            eligibility = "eligible" if is_pak_eligible else "ineligible"
    else:
        eligibility = "eligible" if is_pak_eligible else "ineligible"
    
    eligibility_reason = raw.eligibility_reason

    # Determine country from location, not eligibility
    # Country represents where the job is physically located
    country_default = _detect_country(location) or ""

    return NormalizedJob(
        source=raw.source,
        source_job_id=raw.source_job_id,
        source_url=raw.source_url,
        title=title,
        company_name=company,
        company_url=_safe_str(raw.company_url, max_len=1024),
        description=_safe_str(raw.description, max_len=20000),
        requirements=_safe_str(raw.requirements, max_len=20000),
        responsibilities=_safe_str(raw.responsibilities, max_len=20000),
        skills=_safe_str(raw.skills, max_len=2000),
        employment_type=employment,
        workplace_type=workplace,
        department=_safe_str(raw.department, max_len=255),
        category=_safe_str(raw.category, max_len=255),
        location=location,
        city=city,
        province=province,
        country=country_default,
        is_remote=is_remote,
        eligibility=eligibility,
        eligibility_reason=eligibility_reason,
        salary_min=smin,
        salary_max=smax,
        salary_currency=scur,
        salary_period=speriod,
        experience_min=raw.experience_min,
        experience_max=raw.experience_max,
        education_requirements=_safe_str(raw.education_requirements, max_len=255),
        posted_at=posted,
        closing_at=closing,
        status="active",
        is_active=True,
        raw_source_metadata=raw_meta,
        content_hash=content_hash,
        normalized_hash=normalized_hash,
    )
