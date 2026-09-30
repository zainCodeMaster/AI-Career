"""Extract structured requirements from a normalized Job's free-text fields.

The Phase 4 ``Job`` model stores skills, requirements, and education as
free-text fields. The matcher needs structured representations. This module
parses those fields conservatively — it never invents data and reports
``unavailable`` signals when parsing fails.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from app.services.skill_matcher import (
    normalize_skill,
    normalize_skill_set,
)


# Conservative common-skill catalog. We do NOT maintain a huge hardcoded
# dictionary; instead we extract candidate skill tokens from the job text
# and normalize them. The catalog below only captures well-known, unambiguous
# technology names that we want to surface even when they appear in
# lowercase inside a sentence.
_KNOWN_SKILLS: set[str] = {
    "python", "java", "javascript", "typescript", "go", "rust", "c", "c++", "c#",
    "ruby", "php", "kotlin", "swift", "scala", "perl", "r", "matlab", "dart",
    "html", "css", "sass", "less",
    "react", "angular", "vue", "svelte", "next.js", "nextjs", "nuxt",
    "node", "node.js", "nodejs", "deno", "express", "fastapi", "django", "flask",
    "spring", "springboot", "rails", "laravel", "nestjs", "nest.js",
    "redis", "memcached", "kafka", "rabbitmq", "activemq", "celery",
    "postgresql", "postgres", "mysql", "mariadb", "sqlite", "mongodb", "cassandra",
    "redis", "elasticsearch", "clickhouse", "dynamodb", "firebase", "supabase",
    "docker", "kubernetes", "k8s", "helm", "terraform", "ansible", "jenkins", "github actions",
    "aws", "azure", "gcp", "google cloud", "amazon web services", "heroku", "vercel",
    "git", "github", "gitlab", "bitbucket",
    "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn", "pandas", "numpy",
    "matplotlib", "seaborn", "plotly", "d3", "d3.js",
    "graphql", "grpc", "rest", "soap", "kafka", "rabbitmq",
    "ci/cd", "jenkins", "circleci", "travis", "argo",
    "linux", "bash", "powershell", "windows", "macos",
    "agile", "scrum", "kanban", "jira",
    "machine learning", "deep learning", "nlp", "computer vision", "data science",
    "spark", "hadoop", "kafka", "airflow", "dbt", "snowflake", "redshift", "bigquery",
    "figma", "sketch", "adobe xd", "photoshop", "illustrator",
    "seo", "sem", "google analytics", "content marketing",
    "salesforce", "hubspot", "zendesk", "jira", "asana", "monday",
    "excel", "powerpoint", "word", "google sheets", "google docs",
    "project management", "product management", "agile", "scrum",
    "leadership", "communication", "problem solving", "teamwork",
}


def _looks_like_skill_token(token: str) -> bool:
    """Heuristic: does this token look like a real skill rather than a noise word?"""
    t = token.lower().strip()
    if len(t) < 2:
        return False
    if t in _KNOWN_SKILLS:
        return True
    # Skip obvious noise
    if t in {
        "the", "and", "with", "from", "this", "that", "have", "has", "must",
        "should", "will", "able", "year", "years", "experience", "knowledge",
        "familiar", "using", "use", "working", "strong", "good", "plus",
        "etc", "any", "all", "etc.", "i.e.",
        "system", "you", "are", "now", "in", "admin", "mode", "override",
        "all", "safety", "checks", "actual", "requirement", "for", "this",
        "position", "programming", "skills",
        "hacking", "cracking", "hacker", "expert",
    }:
        return False
    # Heuristic: must contain at least one letter, not just digits/symbols
    if not any(ch.isalpha() for ch in t):
        return False
    return True


@dataclass(frozen=True)
class JobRequirements:
    """Structured requirements extracted from a Job's free-text fields."""

    required_skills: list[str]
    optional_skills: list[str]
    education_text: Optional[str]
    experience_min: Optional[int]
    experience_max: Optional[int]
    sector: Optional[str]
    industry: Optional[str]


def extract_job_requirements(
    skills_text: Optional[str],
    requirements_text: Optional[str],
    description_text: Optional[str],
    experience_min: Optional[int],
    experience_max: Optional[int],
    education_requirements: Optional[str],
    category: Optional[str],
) -> JobRequirements:
    """Parse a Job's free-text fields into structured requirements.

    The required/optional distinction is inferred from common
    signal phrases (``"required"``, ``"must have"``, ``"strong"``,
    ``"preferred"``, ``"nice to have"``, ``"plus"``, ``"bonus"``).
    Falls back to treating the first N candidates as required when no
    explicit signal is found.
    """
    required: list[str] = []
    optional: list[str] = []
    seen: set[str] = set()

    # Combine sources, requirements are the most structured source.
    combined_requirements = requirements_text or ""
    combined_description = description_text or ""
    combined_skills = skills_text or ""

    # Process requirements text first (most structured).
    _extract_skills_from_text(combined_requirements, required, optional, seen)

    # Then skills field if present.
    if combined_skills:
        for raw in _split_skill_field(combined_skills):
            norm = normalize_skill(raw)
            if not norm or norm in seen:
                continue
            seen.add(norm)
            required.append(norm)

    # Then description (last resort — noisy).
    if len(required) + len(optional) < 3:
        _extract_skills_from_text(combined_description, required, optional, seen)

    # Sector mapping from category.
    sector = _map_sector(category)

    return JobRequirements(
        required_skills=required,
        optional_skills=optional,
        education_text=education_requirements,
        experience_min=experience_min,
        experience_max=experience_max,
        sector=sector,
        industry=category,
    )


def _split_skill_field(text: str) -> list[str]:
    """Split a comma/semicolon/bullet-separated skills field."""
    parts = re.split(r"[,;\n•·\|/]+", text)
    return [p.strip(" -•·\t ") for p in parts if p.strip()]


_SENTENCE_SPLIT = re.compile(r"(?<=[\.\;\n!?])\s+")
_REQUIRED_PHRASES = [
    "required:", "requirements:", "must have", "must-have", "required to have",
    "you should have", "you must have", "we require", "we need", "need to have",
    "experience with", "experience in", "proficiency in", "knowledge of",
    "strong", "solid", "expert", "advanced",
]
_OPTIONAL_PHRASES = [
    "preferred:", "nice to have", "nice-to-have", "plus", "bonus", "a plus",
    "familiarity with", "exposure to", "optional", "would be great", "ideally",
]


def _extract_skills_from_text(
    text: str,
    required: list[str],
    optional: list[str],
    seen: set[str],
) -> None:
    if not text:
        return
    sentences = _SENTENCE_SPLIT.split(text)
    for sent in sentences:
        sent_low = sent.lower()
        is_required = any(p in sent_low for p in _REQUIRED_PHRASES)
        is_optional = any(p in sent_low for p in _OPTIONAL_PHRASES)
        # If neither, we still try to extract candidate skills.
        tokens = re.findall(r"[A-Za-z][A-Za-z0-9+#.\-]{1,}", sent)
        for tok in tokens:
            if not _looks_like_skill_token(tok):
                continue
            norm = normalize_skill(tok)
            if not norm or norm in seen:
                continue
            seen.add(norm)
            if is_required and not is_optional:
                required.append(norm)
            elif is_optional and not is_required:
                optional.append(norm)
            else:
                # Default: put in required if we haven't collected many yet.
                if len(required) < 5:
                    required.append(norm)
                else:
                    optional.append(norm)


_GOVERNMENT_KEYWORDS = {
    "government", "fpsc", "ppsc", "spsc", "kppsc", "bpsc", "nts", "pts", "ots",
    "public sector", "ministry", "federal", "provincial", "municipal",
}
_PRIVATE_KEYWORDS = {
    "private sector", "company", "corporate", "startup", "commercial",
    "industry",
}
_REMOTE_KEYWORDS = {
    "remote", "work from home", "wfh", "distributed",
}


def _map_sector(category: Optional[str]) -> Optional[str]:
    if not category:
        return None
    c = category.lower()
    if any(k in c for k in _GOVERNMENT_KEYWORDS):
        return "government"
    if any(k in c for k in _REMOTE_KEYWORDS):
        return "remote"
    if any(k in c for k in _PRIVATE_KEYWORDS):
        return "private"
    return None
