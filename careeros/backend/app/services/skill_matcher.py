"""Skill normalization and matching.

Provides a deterministic, language-agnostic skill string normalizer and a
``SkillMatcher`` that compares a user's skill set against a job's required
and preferred skills. Skill matching is the most heavily weighted signal in
the overall match score, so the normalizer must be both conservative (to
avoid false positives) and forgiving of common variations (to avoid false
negatives).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

# Allow letters, digits, whitespace, and a small set of meaningful separators
# (+, #, ., -). Everything else (parens, commas, slashes between unrelated
# technologies) is treated as a word boundary.
_TOKEN_SPLIT = re.compile(r"[^A-Za-z0-9+#.\-]+")
# Strip common version qualifiers like "v3", "2.0", "13+".
_VERSION_TOKEN = re.compile(r"^v?\d+(\.\d+)*$")
# Common abbreviations / canonical forms. Conservative: only applied when
# the normalized token matches the key. This is intentionally small and
# maintainable; large dictionaries of synonyms tend to introduce
# false-positive matches.
_ABBREVIATIONS: dict[str, str] = {
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "k8s": "kubernetes",
    "aws": "amazonwebservices",
    "gcp": "googlecloudplatform",
    "az": "azure",
    "ms": "microsoft",
    "pg": "postgresql",
    "postgres": "postgresql",
    "psql": "postgresql",
    "mongo": "mongodb",
    "nosql": "nosql",
    "ml": "machinelearning",
    "ai": "artificialintelligence",
    "nlp": "naturallanguageprocessing",
    "cv": "computervision",
    "dl": "deeplearning",
    "ux": "user experience",
    "ui": "user interface",
    "qa": "quality assurance",
    "fe": "frontend",
    "be": "backend",
    "fs": "fullstack",
    "rest": "rest",
    "graphql": "graphql",
    "http": "http",
    "sql": "sql",
    "nosql": "nosql",
    "oop": "objectorientedprogramming",
    "tdd": "testdrivendevelopment",
}

# Common multi-word tech aliases. Keys are the full lowercase phrase, values
# are the canonical compact form. We match on the phrase being present as a
# contiguous substring of the source skill string.
_PHRASE_CANONICAL: dict[str, str] = {
    "amazon web services": "amazonwebservices",
    "google cloud platform": "googlecloudplatform",
    "microsoft azure": "azure",
    "machine learning": "machinelearning",
    "artificial intelligence": "artificialintelligence",
    "natural language processing": "naturallanguageprocessing",
    "computer vision": "computervision",
    "deep learning": "deeplearning",
    "react js": "reactjs",
    "reactjs": "reactjs",
    "node js": "nodejs",
    "nodejs": "nodejs",
    "next js": "nextjs",
    "nextjs": "nextjs",
    "vue js": "vuejs",
    "vuejs": "vuejs",
    "fast api": "fastapi",
    "spring boot": "springboot",
    "objective c": "objectivec",
    "google cloud": "googlecloudplatform",
    "ci cd": "cici",
    "ci/cd": "cici",
    "amazon s3": "amazons3",
    "aws s3": "amazons3",
    "google sheets": "googlesheets",
    "power bi": "powerbi",
    "data science": "datascience",
}


def normalize_skill(skill: str | None) -> str:
    """Normalize a skill string into a canonical token suitable for comparison.

    - lowercases
    - strips punctuation
    - collapses whitespace
    - applies common multi-word aliases (e.g. ``"Amazon Web Services"`` → ``amazonwebservices``)
    - drops pure version tokens ("v3", "2.0")
    - applies abbreviation expansion ("JS" → ``javascript``)
    - returns an empty string for empty/None input
    """
    if not skill:
        return ""
    text = skill.strip().lower()
    if not text:
        return ""

    # Apply phrase canonicalization before token-splitting so multi-word
    # aliases are captured as a single unit.
    for phrase, canonical in _PHRASE_CANONICAL.items():
        if phrase in text:
            text = text.replace(phrase, canonical)

    # Tokenize on non-alphanumeric boundaries.
    raw_tokens = [t for t in _TOKEN_SPLIT.split(text) if t]
    tokens: list[str] = []
    for tok in raw_tokens:
        # Drop version qualifiers.
        if _VERSION_TOKEN.match(tok):
            continue
        # Drop single-character tokens (too noisy to be a reliable signal).
        if len(tok) <= 1:
            continue
        # Apply abbreviation mapping if the token is exactly an abbrev.
        canonical = _ABBREVIATIONS.get(tok, tok)
        tokens.append(canonical)

    # Build a compact canonical representation by joining tokens. This keeps
    # ordering stable for deterministic comparison and avoids false positives
    # from word-boundary differences ("python3" vs "python 3").
    return "".join(tokens)


def normalize_skill_set(skills: Iterable[str | None]) -> set[str]:
    """Normalize a collection of skill strings into a set of canonical tokens.

    Empty strings are dropped. This set is the canonical user-skill or
    job-skill representation used by the matcher.
    """
    return {s for s in (normalize_skill(x) for x in skills) if s}


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SkillMatchResult:
    """Outcome of comparing user skills against a job's skills."""

    matched: list[str] = field(default_factory=list)  # canonical tokens that matched
    missing: list[str] = field(default_factory=list)  # canonical tokens that did not match
    matched_required: list[str] = field(default_factory=list)  # subset of `matched` that were required
    missing_required: list[str] = field(default_factory=list)  # subset of `missing` that were required
    matched_optional: list[str] = field(default_factory=list)
    missing_optional: list[str] = field(default_factory=list)
    # 0.0–1.0; reflects the proportion of required+optional job skills that
    # the user satisfies, weighted toward required skills.
    score: float = 0.0
    # True if the user has no skills to compare against (signal unavailable).
    no_user_skills: bool = False
    # True if the job has no required/optional skills to match against.
    no_job_skills: bool = False


class SkillMatcher:
    """Deterministic skill matcher.

    Compares a set of normalized user skills against normalized job required
    and optional skills. The score combines required and optional match
    ratios, with required skills weighted more heavily.
    """

    @staticmethod
    def match(
        user_skills: Iterable[str | None],
        job_required_skills: Iterable[str | None] = (),
        job_optional_skills: Iterable[str | None] = (),
    ) -> SkillMatchResult:
        user = normalize_skill_set(user_skills)
        required = normalize_skill_set(job_required_skills)
        optional = normalize_skill_set(job_optional_skills)

        if not user and (required or optional):
            return SkillMatchResult(no_user_skills=True, no_job_skills=not (required or optional))
        if not required and not optional:
            return SkillMatchResult(no_job_skills=True)
        if not user:
            return SkillMatchResult(no_user_skills=True)

        matched_required = sorted(required & user)
        missing_required = sorted(required - user)
        matched_optional = sorted(optional & user)
        missing_optional = sorted(optional - user)

        # Required skills are weighted 3x vs optional. Score is bounded [0, 1].
        required_weight = 3.0
        optional_weight = 1.0
        total_weight = required_weight * len(required) + optional_weight * len(optional)
        if total_weight == 0:
            score = 0.0
        else:
            earned = required_weight * len(matched_required) + optional_weight * len(matched_optional)
            score = min(1.0, earned / total_weight)

        return SkillMatchResult(
            matched=matched_required + matched_optional,
            missing=missing_required + missing_optional,
            matched_required=matched_required,
            missing_required=missing_required,
            matched_optional=matched_optional,
            missing_optional=missing_optional,
            score=score,
        )
