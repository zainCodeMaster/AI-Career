"""Phase 6 — Job Description Analysis for Resume Engine.

Extends the deterministic job requirements extraction from Phase 5 with richer
analysis for resume tailoring, including:
- Keywords extraction and categorization
- ATS-relevant signals
- Required vs preferred distinctions
- Seniority level classification

IMPORTANT: Job descriptions are external/untrusted content.
All extraction is deterministic and conservative — no hallucination.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from app.db.models.jobs import Job
from app.services.job_requirements import (
    JobRequirements,
    extract_job_requirements,
)
from app.services.job_requirements import _looks_like_skill_token


@dataclass(frozen=True)
class JobKeyword:
    """A keyword extracted from a job description."""

    text: str
    category: str  # "technical", "soft", "industry", "certification", "title"
    required: bool  # True if required, False if preferred


@dataclass(frozen=True)
class JobRequirementAnalysis:
    """Comprehensive analysis of job requirements for resume tailoring.
    
    All fields are derived deterministically from the job's text fields.
    Never invents data — only extracts from existing fields.
    """

    # Core job metadata
    job_id: str
    title: str
    company_name: str
    location: Optional[str]
    
    # Extracted skills and keywords
    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)
    
    # Keywords extracted from all text fields
    keywords: List[JobKeyword] = field(default_factory=list)
    required_keywords: List[str] = field(default_factory=list)
    preferred_keywords: List[str] = field(default_factory=list)
    
    # Experience requirements
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    experience_text: Optional[str] = None
    
    # Education
    education_requirements: Optional[str] = None
    
    # Certifications
    required_certifications: List[str] = field(default_factory=list)
    preferred_certifications: List[str] = field(default_factory=list)
    
    # Employment info
    employment_type: Optional[str] = None
    workplace_type: Optional[str] = None
    is_remote: bool = False
    
    # Seniority classification
    seniority: Optional[str] = None  # "entry", "mid", "senior", "lead", "principal"
    
    # ATS-relevant signals
    required_phrases: List[str] = field(default_factory=list)
    preferred_phrases: List[str] = field(default_factory=list)
    
    # Raw text sources for traceability
    description_preview: Optional[str] = None


class JobRequirementAnalyzer:
    """Analyze a Job record for resume tailoring and ATS matching.
    
    This service extracts structured information from a Job's free-text fields
    using deterministic parsing. It does NOT use LLMs for extraction.
    """

    # Seniority indicators (regex patterns)
    SENIORITY_PATTERNS = {
        "entry": [
            r"\bentry.?level\b", r"\bjunior\b", r"\bnew grad\b", r"\binternship\b", r"\bintern\b",
        ],
        "mid": [
            r"\bmid.?level\b", r"\bmiddle.?level\b", r"\bintermediate\b",
            r"\b\d-?\d+\s*years?\b",
        ],
        "senior": [
            r"\bsenior\b", r"\blead\b", r"\bstaff\b", r"\b\d+\+.*years?\b",
            r"\b5\+.*years?\b", r"\b5-?\d+.*years?\b",
        ],
        "principal": [
            r"\bprincipal\b", r"\barchitect\b",
            r"\b10\+.*years?\b", r"\bsenior staff\b", r"\bprincipal engineer\b",
        ],
    }

    # Known certification keywords
    CERTIFICATION_KEYWORDS = [
        "aws", "azure", "gcp", "google cloud", "amazon web services",
        "pmp", "cpm", "cisa", "cissc", "cissp", "cisa", "ceh",
        "scrum master", "csm", "csp", "safer", "safe",
        "cisco", "ccna", "ccnp", "ccie",
        "oracle", "mysql", "postgresql", "mongodb", "mongodb dba",
        "kubernetes", "cka", "cks",
        "itil", "devops", "docker", "compTIA",
    ]

    @staticmethod
    def analyze(job: Job) -> JobRequirementAnalysis:
        """Analyze a Job record for resume tailoring."""
        # Extract basic job data
        title = job.title or ""
        company = job.company_name or ""
        location = job.location

        # Use existing Phase 5 extraction for skills
        base_reqs = extract_job_requirements(
            skills_text=job.skills,
            requirements_text=job.requirements,
            description_text=job.description,
            experience_min=job.experience_min,
            experience_max=job.experience_max,
            education_requirements=job.education_requirements,
            category=job.category,
        )

        # Extract keywords from all text fields
        keywords = JobRequirementAnalyzer._extract_keywords(
            title=title,
            description=job.description,
            requirements=job.requirements,
            skills=job.skills,
        )
        required_keywords = [
            kw.text for kw in keywords if kw.required and kw.category == "technical"
        ]
        preferred_keywords = [
            kw.text for kw in keywords if not kw.required
        ]

        # Extract experience text from description/requirements
        experience_text = JobRequirementAnalyzer._extract_experience_text(
            job.description, job.requirements
        )

        # Classify seniority
        seniority = JobRequirementAnalyzer._classify_seniority(
            title=title,
            experience_min=job.experience_min,
            experience_text=experience_text,
            description=job.description,
        )

        # Extract certifications
        required_certs, preferred_certs = JobRequirementAnalyzer._extract_certifications(
            job.description, job.requirements, job.skills
        )

        # Extract required/preferred phrases for ATS signals
        required_phrases, preferred_phrases = JobRequirementAnalyzer._extract_phrases(
            job.description, job.requirements
        )

        # Description preview for traceability
        description_preview = job.description[:500] if job.description else None

        return JobRequirementAnalysis(
            job_id=str(job.id),
            title=title,
            company_name=company,
            location=location,
            required_skills=base_reqs.required_skills,
            preferred_skills=base_reqs.optional_skills,
            keywords=keywords,
            required_keywords=required_keywords,
            preferred_keywords=preferred_keywords,
            experience_min=job.experience_min,
            experience_max=job.experience_max,
            experience_text=experience_text,
            education_requirements=job.education_requirements,
            required_certifications=required_certs,
            preferred_certifications=preferred_certs,
            employment_type=job.employment_type,
            workplace_type=job.workplace_type,
            is_remote=job.is_remote,
            seniority=seniority,
            required_phrases=required_phrases,
            preferred_phrases=preferred_phrases,
            description_preview=description_preview,
        )

    @staticmethod
    def analyze_text(
        job_description: str,
        title: str = "",
        company_name: str = "",
        location: Optional[str] = None,
    ) -> JobRequirementAnalysis:
        """Analyze raw job description text (for external JD input).
        
        This method is for analyzing a raw job description string that may
        not have a stored Job record. It performs the same deterministic
        extraction but is more conservative about what it claims to extract.
        """
        # Create a temporary Job for analysis (we won't persist it)
        from app.db.models.jobs import Job as JobModel

        temp_job = JobModel(
            title=title,
            company_name=company_name,
            description=job_description,
            requirements=None,
            skills=None,
            experience_min=None,
            experience_max=None,
            education_requirements=None,
            category=None,
        )
        return JobRequirementAnalyzer.analyze(temp_job)

    @staticmethod
    def _extract_keywords(
        title: str,
        description: Optional[str],
        requirements: Optional[str],
        skills: Optional[str],
    ) -> List[JobKeyword]:
        """Extract keywords from job description fields.
        
        Categorizes keywords as technical, soft, industry, certification, or title.
        """
        keywords: List[JobKeyword] = []
        seen: set[str] = set()

        # Extract from skills field (most structured, all required)
        if skills:
            skill_tokens = re.split(r"[,;\n]", skills)
            for token in skill_tokens:
                token = token.strip()
                if not token or token.lower() in seen:
                    continue
                norm_token = normalize_keyword(token)
                if not norm_token:
                    continue
                seen.add(norm_token.lower())
                category = JobRequirementAnalyzer._categorize_keyword(norm_token)
                keywords.append(JobKeyword(
                    text=norm_token,
                    category=category,
                    required=True,
                ))

        # Extract from requirements text
        if requirements:
            req_keywords = JobRequirementAnalyzer._extract_keywords_from_text(
                requirements, title=title
            )
            for kw, is_required in req_keywords:
                if kw.lower() not in seen:
                    seen.add(kw.lower())
                    keywords.append(JobKeyword(
                        text=kw,
                        category=JobRequirementAnalyzer._categorize_keyword(kw),
                        required=is_required,
                    ))

        # Extract from description (only if we have few keywords from structured fields)
        if description and len(keywords) < 5:
            desc_keywords = JobRequirementAnalyzer._extract_keywords_from_text(
                description, title=title
            )
            for kw, is_required in desc_keywords:
                if kw.lower() not in seen:
                    seen.add(kw.lower())
                    keywords.append(JobKeyword(
                        text=kw,
                        category=JobRequirementAnalyzer._categorize_keyword(kw),
                        required=is_required,
                    ))

        # Always add title as a keyword
        title_keywords = JobRequirementAnalyzer._extract_title_keywords(title)
        for kw in title_keywords:
            if kw.lower() not in seen:
                seen.add(kw.lower())
                keywords.append(JobKeyword(
                    text=kw,
                    category="title",
                    required=True,
                ))

        return keywords

    @staticmethod
    def _extract_keywords_from_text(
        text: str, title: str = ""
    ) -> List[tuple[str, bool]]:
        """Extract keywords from a text blob, distinguishing required vs preferred.
        
        Returns list of (keyword, is_required) tuples.
        """
        results: List[tuple[str, bool]] = []
        seen: set[str] = set()

        # Split into sentences/fragments to detect "required" vs "preferred" signals
        sentences = re.split(r'[.\n]+', text)

        for sentence in sentences:
            # Determine if this sentence contains required or preferred signals
            is_required_context = bool(re.search(
                r'\b(must\s+have|required|essential|mandatory|prerequisite|needed)\b',
                sentence, re.IGNORECASE,
            ))
            is_preferred_context = bool(re.search(
                r'\b(preferred|nice\s+to\s+have|nice\s+to\s+have,|bonus|plus\s+if|would\s+be\s+good)',
                sentence, re.IGNORECASE,
            ))

            # If no signal, default to required (conservative)
            if not is_required_context and not is_preferred_context:
                is_required_context = True

            # Extract skill-like tokens (filter out noise words)
            tokens = re.findall(r'\b[A-Za-z][A-Za-z+#.-]+\b', sentence)
            for token in tokens:
                if not _looks_like_skill_token(token):
                    continue
                norm = normalize_keyword(token)
                if not norm:
                    continue
                if norm.lower() in seen:
                    continue
                seen.add(norm.lower())
                results.append((norm, is_required_context))

        return results

    @staticmethod
    def _extract_title_keywords(title: str) -> List[str]:
        """Extract key terms from a job title."""
        if not title:
            return []
        
        keywords = []
        # Split on common separators
        parts = re.split(r'\s*[\/,&]\s*|\s+and\s+', title.lower())
        for part in parts:
            part = part.strip()
            # Skip generic words
            if part in {"and", "or", "the", "a", "an", "engineer", "developer", "specialist"}:
                continue
            if len(part) > 2:
                keywords.append(part.title())
        return keywords

    @staticmethod
    def _categorize_keyword(keyword: str) -> str:
        """Categorize a keyword based on its content."""
        kw_lower = keyword.lower()

        # Certifications
        cert_patterns = [
            r'\ba(ws|azure|gcp|google cloud|amazon web services)\b',
            r'\b(pmp|cpm|cisa|cissc|cissp|ceh|csm|csp)\b',
            r'\b(cisco|ccna|ccnp|ccie)\b',
            r'\b(itil|compTIA|scrum)\b',
        ]
        for pattern in cert_patterns:
            if re.search(pattern, kw_lower):
                return "certification"

        # Technical skills
        tech_patterns = [
            r'\b(python|java|javascript|typescript|go|rust|ruby|php|kotlin|swift|scala)\b',
            r'\b(react|angular|vue|svelte|next\.?js|nuxt|node|express|django|flask)\b',
            r'\b(aws|azure|gcp|docker|kubernetes|terraform|jenkins)\b',
            r'\b(postgresql|mysql|mongodb|redis|elasticsearch|sqlite)\b',
            r'\b(agile|scrum|kanban)\b',
        ]
        for pattern in tech_patterns:
            if re.search(pattern, kw_lower):
                return "technical"

        # Soft skills
        soft_keywords = {
            "communication", "leadership", "teamwork", "problem solving",
            "project management", "product management", "critical thinking",
            "adaptability", "creativity", "collaboration", "mentoring",
        }
        if kw_lower in soft_keywords:
            return "soft"

        # Industry terms (would need expansion)
        industry_keywords = {
            "fintech", "healthcare", "edtech", "ecommerce", "saa",
        }
        if kw_lower in industry_keywords:
            return "industry"

        return "technical"  # Default to technical

    @staticmethod
    def _extract_experience_text(
        description: Optional[str], requirements: Optional[str]
    ) -> Optional[str]:
        """Extract the experience requirement text from job description."""
        combined = (requirements or "") + " " + (description or "")
        if not combined.strip():
            return None

        # Look for experience patterns
        exp_patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s+)?experience[^.]*(?:in|with|as)?[^.]*',
            r'(\d+-\d+)\s*years?\s*(?:of\s+)?experience[^.]*(?:in|with|as)?[^.]*',
            r'(?:minimum|min\.?)\s*(\d+)\s*years?\s*(?:of\s+)?experience[^.]*(?:in|with|as)?[^.]*',
        ]

        for pattern in exp_patterns:
            match = re.search(pattern, combined, re.IGNORECASE)
            if match:
                return match.group(0).strip()

        return None

    @staticmethod
    def _classify_seniority(
        title: str,
        experience_min: Optional[int],
        experience_text: Optional[str],
        description: Optional[str],
    ) -> Optional[str]:
        """Classify job seniority level."""
        text_to_check = (title or "") + " " + (experience_text or "") + " " + (description or "")

        # Check more specific patterns first (entry before mid to avoid overlap)
        for seniority in ["principal", "senior", "entry", "mid"]:
            patterns = JobRequirementAnalyzer.SENIORITY_PATTERNS[seniority]
            for pattern in patterns:
                if re.search(pattern, text_to_check, re.IGNORECASE):
                    return seniority

        # Use experience_min if available
        if experience_min is not None:
            if experience_min <= 2:
                return "entry"
            elif experience_min <= 5:
                return "mid"
            elif experience_min <= 10:
                return "senior"
            else:
                return "principal"

        return None

    @staticmethod
    def _extract_certifications(
        description: Optional[str],
        requirements: Optional[str],
        skills: Optional[str],
    ) -> tuple[List[str], List[str]]:
        """Extract certification requirements from job text."""
        combined = " ".join(filter(None, [description, requirements, skills]))
        if not combined:
            return [], []

        required_certs = []
        preferred_certs = []
        seen: set[str] = set()

        for cert_kw in JobRequirementAnalyzer.CERTIFICATION_KEYWORDS:
            pattern = re.escape(cert_kw)
            if re.search(pattern, combined, re.IGNORECASE):
                if cert_kw.lower() in seen:
                    continue
                seen.add(cert_kw.lower())
                
                # Check if it's required or preferred
                # Find the sentence containing this certification
                sentences = re.split(r'[.\n]+', combined)
                for sentence in sentences:
                    if re.search(pattern, sentence, re.IGNORECASE):
                        if re.search(r'\b(preferred|nice\s+to\s+have|bonus)\b', sentence, re.IGNORECASE):
                            preferred_certs.append(cert_kw.title())
                        else:
                            required_certs.append(cert_kw.title())
                        break

        return required_certs, preferred_certs

    @staticmethod
    def _extract_phrases(
        description: Optional[str],
        requirements: Optional[str],
    ) -> tuple[List[str], List[str]]:
        """Extract required and preferred phrase signals from job text."""
        required_phrases = []
        preferred_phrases = []

        for text in [requirements, description]:
            if not text:
                continue

            # Look for "X years of experience" patterns
            exp_matches = re.findall(
                r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
                text, re.IGNORECASE,
            )
            for match in exp_matches:
                phrase = f"{match} years of experience"
                if phrase not in required_phrases:
                    required_phrases.append(phrase)

            # Look for "must have" phrases
            must_matches = re.findall(
                r'must\s+have\s+([^.]+?)(?=\.|$)',
                text, re.IGNORECASE,
            )
            for match in must_matches:
                phrase = match.strip()
                if phrase and len(phrase) < 200 and phrase not in required_phrases:
                    required_phrases.append(phrase)

            # Look for "preferred" phrases
            preferred_matches = re.findall(
                r'(?:preferred|nice\s+to\s+have)([^.]+?)(?=\.|$)',
                text, re.IGNORECASE,
            )
            for match in preferred_matches:
                phrase = match.strip()
                if phrase and len(phrase) < 200 and phrase not in preferred_phrases:
                    preferred_phrases.append(phrase)

        return required_phrases, preferred_phrases


def normalize_keyword(token: str) -> str:
    """Normalize a keyword for consistent matching.
    
    Strips extra whitespace, normalizes common variants, and returns
    a canonical form for matching.
    """
    token = token.strip()
    
    # Common normalizations
    replacements = {
        "aws": "AWS",
        "gcp": "GCP",
        "azure": "Azure",
        "api": "API",
        "api's": "APIs",
        "ui": "UI",
        "ux": "UX",
        "ci/cd": "CI/CD",
    }
    
    lower_token = token.lower()
    if lower_token in replacements:
        return replacements[lower_token]
    
    # Strip trailing punctuation
    token = token.rstrip('.,;:!?')
    
    return token
