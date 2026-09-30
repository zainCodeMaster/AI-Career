"""Phase 6 — Deterministic ATS Analyzer.

Performs a transparent, explainable ATS compatibility analysis that evaluates
how well a resume matches a job description. All scoring is deterministic —
no LLM calls. Every score component is traceable and testable.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.jobs import Job
from app.db.models.resume import Resume
from app.services.resume.job_analysis import (
    JobRequirementAnalysis,
    JobRequirementAnalyzer,
)

logger = logging.getLogger("app.resume.ats")


@dataclass(frozen=True)
class ATSSectionScore:
    """Score for a specific section of the resume."""
    
    section_type: str
    score: int  # 0-100
    matched_count: int
    total_count: int
    matched_items: List[str] = field(default_factory=list)
    missing_items: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ATSAnalysisResult:
    """Complete ATS analysis result.
    
    All fields are deterministically computed from resume content and job requirements.
    """

    resume_id: str
    job_id: str
    overall_score: int  # 0-100, weighted average of component scores
    
    # Component scores
    keyword_coverage: ATSSectionScore
    skill_alignment: ATSSectionScore
    experience_alignment: ATSSectionScore
    education_alignment: ATSSectionScore
    certification_alignment: ATSSectionScore
    structure_score: ATSSectionScore
    relevance_score: ATSSectionScore
    
    # Breakdown percentages (0-100 each)
    breakdown: Dict[str, int]
    
    # Detailed lists
    matched_keywords: List[str] = field(default_factory=list)
    missing_keywords: List[str] = field(default_factory=list)
    matched_skills: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)
    matched_requirements: List[str] = field(default_factory=list)
    missing_requirements: List[str] = field(default_factory=list)
    
    # Quality signals
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Metadata (with defaults for dataclass field ordering)
    analyzed_at: str = ""  # ISO 8601 timestamp
    total_keywords_matched: int = 0
    total_keywords_required: int = 0


class ATSAnalyzer:
    """Deterministic ATS compatibility analyzer.
    
    The analyzer evaluates a resume against a job's requirements using:
    1. Keyword matching (exact and fuzzy)
    2. Skill alignment
    3. Experience level matching
    4. Education/qualification checks
    5. Certification requirements
    6. Resume structure completeness
    7. Section relevance
    
    Scoring weights are configurable but default to industry-standard ATS
    heuristics.
    """

    # Scoring weights (must sum to 1.0)
    WEIGHTS = {
        "keyword_coverage": 0.25,    # How many required keywords are covered
        "skill_alignment": 0.20,     # How many required skills match
        "experience_alignment": 0.15,  # Years of experience match
        "education_alignment": 0.10,   # Education requirements
        "certification_alignment": 0.05,  # Certification requirements
        "structure_score": 0.10,     # Resume structure completeness
        "relevance_score": 0.15,     # Overall relevance of content
    }

    # Required resume sections for a complete score
    REQUIRED_SECTIONS = ["summary", "skills", "experience", "education"]
    OPTIONAL_SECTIONS = ["projects", "certifications", "achievements"]

    @staticmethod
    def analyze(
        db: Session,
        resume: Resume,
        job: Job,
        job_analysis: Optional[JobRequirementAnalysis] = None,
    ) -> ATSAnalysisResult:
        """Analyze a resume against a job for ATS compatibility."""
        if job_analysis is None:
            job_analysis = JobRequirementAnalyzer.analyze(job)

        # Extract resume content
        resume_content = _extract_resume_content(resume)

        # 1. Keyword coverage analysis
        keyword_score = ATSAnalyzer._analyze_keywords(resume_content, job_analysis)

        # 2. Skill alignment analysis
        skill_score = ATSAnalyzer._analyze_skills(resume_content, job_analysis)

        # 3. Experience alignment analysis
        exp_score = ATSAnalyzer._analyze_experience(resume_content, job_analysis)

        # 4. Education alignment analysis
        edu_score = ATSAnalyzer._analyze_education(resume_content, job_analysis)

        # 5. Certification alignment analysis
        cert_score = ATSAnalyzer._analyze_certifications(resume_content, job_analysis)

        # 6. Structure score analysis
        structure_score = ATSAnalyzer._analyze_structure(resume, resume_content)

        # 7. Relevance score analysis
        relevance_score = ATSAnalyzer._analyze_relevance(resume_content, job_analysis)

        # Calculate overall score
        scores = {
            "keyword_coverage": keyword_score.score,
            "skill_alignment": skill_score.score,
            "experience_alignment": exp_score.score,
            "education_alignment": edu_score.score,
            "certification_alignment": cert_score.score,
            "structure_score": structure_score.score,
            "relevance_score": relevance_score.score,
        }

        overall_score = int(sum(
            scores[k] * ATSAnalyzer.WEIGHTS[k] for k in scores
        ))

        # Compile results
        matched_keywords = keyword_score.matched_items
        missing_keywords = keyword_score.missing_items
        matched_skills = skill_score.matched_items
        missing_skills = skill_score.missing_items

        # Compile recommendations
        recommendations = list(ATSAnalyzer._generate_recommendations(
            overall_score, keyword_score, skill_score, exp_score,
            edu_score, cert_score, structure_score, relevance_score,
            job_analysis
        ))

        strengths = ATSAnalyzer._identify_strengths(
            overall_score, keyword_score, skill_score, structure_score
        )
        weaknesses = ATSAnalyzer._identify_weaknesses(
            overall_score, keyword_score, skill_score, structure_score,
            recommendations
        )

        return ATSAnalysisResult(
            resume_id=str(resume.id),
            job_id=str(job.id),
            overall_score=overall_score,
            keyword_coverage=keyword_score,
            skill_alignment=skill_score,
            experience_alignment=exp_score,
            education_alignment=edu_score,
            certification_alignment=cert_score,
            structure_score=structure_score,
            relevance_score=relevance_score,
            breakdown=scores,
            matched_keywords=matched_keywords,
            missing_keywords=missing_keywords,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            matched_requirements=job_analysis.required_skills + job_analysis.required_keywords,
            missing_requirements=missing_skills + missing_keywords,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            analyzed_at=_utcnow_iso(),
            total_keywords_matched=len(matched_keywords),
            total_keywords_required=len(matched_keywords) + len(missing_keywords),
        )

    @staticmethod
    def _analyze_keywords(
        resume_content: Dict,
        job_analysis: JobRequirementAnalysis,
    ) -> ATSSectionScore:
        """Analyze keyword coverage: how many job keywords appear in the resume."""
        all_keywords = set()
        
        # Collect all keywords from the job analysis
        for kw in job_analysis.keywords:
            all_keywords.add(kw.text.lower())
        for kw in job_analysis.required_keywords:
            all_keywords.add(kw.lower())
        
        # Also check required skills
        for skill in job_analysis.required_skills:
            all_keywords.add(skill.lower())
        for skill in job_analysis.preferred_skills:
            all_keywords.add(skill.lower())

        if not all_keywords:
            return ATSSectionScore(
                section_type="keywords",
                score=100,  # No keywords to match
                matched_count=0,
                total_count=0,
            )

        # Get all text from resume content
        resume_text = _get_resume_text(resume_content).lower()

        matched = []
        missing = []
        for kw in all_keywords:
            if kw in resume_text:
                matched.append(kw)
            else:
                missing.append(kw)

        score = int((len(matched) / len(all_keywords)) * 100) if all_keywords else 100

        return ATSSectionScore(
            section_type="keywords",
            score=score,
            matched_count=len(matched),
            total_count=len(all_keywords),
            matched_items=sorted(matched),
            missing_items=sorted(missing),
        )

    @staticmethod
    def _analyze_skills(
        resume_content: Dict,
        job_analysis: JobRequirementAnalysis,
    ) -> ATSSectionScore:
        """Analyze skill alignment between resume and job requirements."""
        required_skills = set(s.lower() for s in job_analysis.required_skills)
        optional_skills = set(s.lower() for s in job_analysis.preferred_skills)

        resume_text = _get_resume_text(resume_content).lower()
        # Handle skills stored as dicts (with "name" key) or strings
        resume_skills = set()
        for s in resume_content.get("skills", []):
            if isinstance(s, dict):
                name = s.get("name", "")
                if name:
                    resume_skills.add(name.lower())
            elif isinstance(s, str):
                resume_skills.add(s.lower())

        matched = []
        missing = []

        for skill in required_skills:
            if skill in resume_skills or skill in resume_text:
                matched.append(skill)
            else:
                missing.append(skill)

        all_skills = required_skills | optional_skills
        score = int((len(matched) / len(required_skills)) * 100) if required_skills else 85

        return ATSSectionScore(
            section_type="skills",
            score=score,
            matched_count=len(matched),
            total_count=len(required_skills),
            matched_items=sorted(matched),
            missing_items=sorted(missing),
        )

    @staticmethod
    def _analyze_experience(
        resume_content: Dict,
        job_analysis: JobRequirementAnalysis,
    ) -> ATSSectionScore:
        """Analyze experience alignment."""
        if job_analysis.experience_min is None and job_analysis.experience_max is None:
            return ATSSectionScore(
                section_type="experience",
                score=85,  # Neutral score when no experience requirement
                matched_count=1,
                total_count=1,
                matched_items=["No specific experience requirement"],
                missing_items=[],
            )

        user_exp_years = _extract_user_experience_years(resume_content)
        required_min = job_analysis.experience_min or 0
        required_max = job_analysis.experience_max or 999

        matched = []
        missing = []
        score = 85  # Default neutral score

        if user_exp_years is not None:
            if user_exp_years >= required_min:
                score = 100
                matched.append(f"User has {user_exp_years}+ years (required: {required_min})")
            else:
                score = max(0, int((user_exp_years / required_min) * 100)) if required_min > 0 else 85
                missing.append(f"Need {required_min} years experience, user has {user_exp_years}")

        # Check for required phrases in experience text
        if job_analysis.required_phrases:
            resume_text = _get_resume_text(resume_content).lower()
            for phrase in job_analysis.required_phrases:
                if phrase.lower() in resume_text:
                    matched.append(phrase)
                else:
                    missing.append(phrase)

        return ATSSectionScore(
            section_type="experience",
            score=score,
            matched_count=len(matched),
            total_count=len(matched) + len(missing),
            matched_items=matched,
            missing_items=missing,
        )

    @staticmethod
    def _analyze_education(
        resume_content: Dict,
        job_analysis: JobRequirementAnalysis,
    ) -> ATSSectionScore:
        """Analyze education alignment."""
        edu_req = job_analysis.education_requirements or ""
        resume_text = _get_resume_text(resume_content).lower()
        
        if not edu_req.strip():
            return ATSSectionScore(
                section_type="education",
                score=85,  # Neutral when no education requirement
                matched_count=1,
                total_count=1,
                matched_items=["No education requirement specified"],
                missing_items=[],
            )

        # Look for education keywords in resume
        matched = []
        missing = []
        
        # Extract key education terms (degree types, institutions)
        edu_keywords = _extract_education_keywords(edu_req)
        resume_edu = resume_content.get("education", [])

        for kw in edu_keywords:
            if kw.lower() in resume_text or any(
                kw.lower() in str(edu).lower() for edu in resume_edu
            ):
                matched.append(kw)
            else:
                missing.append(kw)

        if edu_keywords:
            score = int((len(matched) / len(edu_keywords)) * 100) if matched else 0
        else:
            # If we can't find specific keywords, check if resume has any education
            score = 85 if resume_edu else 50

        return ATSSectionScore(
            section_type="education",
            score=score,
            matched_count=len(matched),
            total_count=len(edu_keywords),
            matched_items=sorted(matched),
            missing_items=sorted(missing),
        )

    @staticmethod
    def _analyze_certifications(
        resume_content: Dict,
        job_analysis: JobRequirementAnalysis,
    ) -> ATSSectionScore:
        """Analyze certification alignment."""
        required_certs = job_analysis.required_certifications
        preferred_certs = job_analysis.preferred_certifications

        all_certs = set(c.lower() for c in required_certs + preferred_certs)
        resume_text = _get_resume_text(resume_content).lower()
        # Handle certifications stored as dicts or strings
        resume_certs = set()
        for c in resume_content.get("certifications", []):
            if isinstance(c, dict):
                name = c.get("name", "")
                if name:
                    resume_certs.add(name.lower())
            elif isinstance(c, str):
                resume_certs.add(c.lower())

        if not all_certs:
            return ATSSectionScore(
                section_type="certifications",
                score=100,
                matched_count=0,
                total_count=0,
                matched_items=[],
                missing_items=[],
            )

        matched = []
        missing = []

        for cert in all_certs:
            if cert in resume_certs or cert in resume_text:
                matched.append(cert)
            else:
                missing.append(cert)

        score = int((len(matched) / len(all_certs)) * 100)

        return ATSSectionScore(
            section_type="certifications",
            score=score,
            matched_count=len(matched),
            total_count=len(all_certs),
            matched_items=sorted(matched),
            missing_items=sorted(missing),
        )

    @staticmethod
    def _analyze_structure(
        resume: Resume,
        resume_content: Dict,
    ) -> ATSSectionScore:
        """Analyze resume structure completeness."""
        sections_present = set()
        sections_content = set(resume_content.keys())

        # Check which sections have meaningful content
        for section in ATSAnalyzer.REQUIRED_SECTIONS:
            if section in sections_content and resume_content.get(section):
                if isinstance(resume_content.get(section), (list, dict)):
                    if resume_content.get(section):
                        sections_present.add(section)
                elif isinstance(resume_content.get(section), str):
                    if resume_content.get(section).strip():
                        sections_present.add(section)

        matched = sorted(sections_present)
        missing = sorted(set(ATSAnalyzer.REQUIRED_SECTIONS) - sections_present)

        # Required sections are worth more
        required_present = len(sections_present & set(ATSAnalyzer.REQUIRED_SECTIONS))
        required_total = len(ATSAnalyzer.REQUIRED_SECTIONS)
        score = int((required_present / required_total) * 100) if required_total > 0 else 100

        # Also check section-level analysis
        for section in resume.sections:
            if section.content.strip():
                sections_present.add(section.section_type)

        return ATSSectionScore(
            section_type="structure",
            score=score,
            matched_count=len(sections_present),
            total_count=len(ATSAnalyzer.REQUIRED_SECTIONS),
            matched_items=matched,
            missing_items=missing,
        )

    @staticmethod
    def _analyze_relevance(
        resume_content: Dict,
        job_analysis: JobRequirementAnalysis,
    ) -> ATSSectionScore:
        """Analyze overall relevance of resume content to the job."""
        resume_text = _get_resume_text(resume_content).lower()
        job_title = (job_analysis.title or "").lower()
        
        matched = []
        missing = []

        # Check if job title keywords appear in resume
        title_words = set(re.findall(r'\b\w+\b', job_title)) - {"and", "or", "the", "a", "an"}
        title_in_resume = any(w in resume_text for w in title_words)
        
        if title_in_resume:
            matched.append("Job title keywords present in resume")
        else:
            missing.append("Job title keywords not prominent in resume")

        # Check seniority alignment
        if job_analysis.seniority:
            seniority_found = job_analysis.seniority.lower() in resume_text
            if seniority_found:
                matched.append(f"Seniority level ({job_analysis.seniority}) reflected in resume")
            else:
                missing.append(f"Seniority level ({job_analysis.seniority}) not clearly stated")

        # Check for required phrases
        for phrase in job_analysis.required_phrases[:5]:  # Limit to top 5
            if phrase.lower() in resume_text:
                matched.append(phrase)
            else:
                missing.append(phrase)

        total = len(matched) + len(missing)
        score = int((len(matched) / total) * 100) if total > 0 else 85

        return ATSSectionScore(
            section_type="relevance",
            score=score,
            matched_count=len(matched),
            total_count=total,
            matched_items=matched,
            missing_items=missing,
        )

    @staticmethod
    def _generate_recommendations(
        overall_score: int,
        keyword_score: ATSSectionScore,
        skill_score: ATSSectionScore,
        exp_score: ATSSectionScore,
        edu_score: ATSSectionScore,
        cert_score: ATSSectionScore,
        structure_score: ATSSectionScore,
        relevance_score: ATSSectionScore,
        job_analysis: JobRequirementAnalysis,
    ) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []

        if keyword_score.missing_items:
            recommendations.append(
                f"Add missing keywords: {', '.join(keyword_score.missing_items[:5])}"
            )
        if skill_score.missing_items:
            recommendations.append(
                f"Add missing skills: {', '.join(skill_score.missing_items[:5])}"
            )
        if structure_score.missing_items:
            recommendations.append(
                f"Add missing sections: {', '.join(structure_score.missing_items)}"
            )
        if exp_score.missing_items:
            recommendations.append(
                f"Address experience gaps: {'; '.join(exp_score.missing_items[:3])}"
            )
        if edu_score.missing_items:
            recommendations.append(
                f"Address education requirements: {', '.join(edu_score.missing_items[:3])}"
            )

        if overall_score >= 80:
            recommendations.append("Resume is well-aligned with this position")
        elif overall_score >= 60:
            recommendations.append("Resume needs significant tailoring for this position")
        else:
            recommendations.append("Major gaps detected — consider if this role is a good fit")

        return recommendations

    @staticmethod
    def _identify_strengths(
        overall_score: int,
        keyword_score: ATSSectionScore,
        skill_score: ATSSectionScore,
        structure_score: ATSSectionScore,
    ) -> List[str]:
        """Identify what the resume does well for this position."""
        strengths = []
        
        if keyword_score.score >= 70:
            strengths.append("Good keyword coverage for this position")
        if skill_score.score >= 80:
            strengths.append("Strong skill alignment with job requirements")
        if structure_score.score >= 90:
            strengths.append("Complete resume structure with all required sections")
        if overall_score >= 80:
            strengths.append("Overall strong match for this position")

        return strengths

    @staticmethod
    def _identify_weaknesses(
        overall_score: int,
        keyword_score: ATSSectionScore,
        skill_score: ATSSectionScore,
        structure_score: ATSSectionScore,
        recommendations: List[str],
    ) -> List[str]:
        """Identify areas for improvement."""
        weaknesses = []
        
        if keyword_score.missing_items:
            weaknesses.append(f"Missing {len(keyword_score.missing_items)} important keywords")
        if skill_score.missing_items:
            weaknesses.append(f"Missing {len(skill_score.missing_items)} required skills")
        if structure_score.missing_items:
            weaknesses.append(f"Missing required resume sections: {', '.join(structure_score.missing_items)}")
        if overall_score < 70:
            weaknesses.append("Overall match score below threshold")

        return weaknesses


def _extract_resume_content(resume: Resume) -> Dict:
    """Extract structured content from a resume for analysis.
    
    Returns a dict with keys matching standard resume sections.
    """
    content = {}
    
    if resume.structured_data:
        # Merge structured_data with section content
        for key, value in resume.structured_data.items():
            if key.startswith('_'):
                continue  # Skip metadata keys
            content[key] = value
    
    # Also extract from sections (more authoritative if present)
    for section in resume.sections:
        if section.section_type and section.content:
            if section.section_type not in content:
                try:
                    content[section.section_type] = section.content
                except Exception:
                    pass

    # Ensure standard sections exist
    for s in ["summary", "skills", "experience", "education", "projects", "certifications", "achievements"]:
        if s not in content:
            content[s] = ""

    return content


def _get_resume_text(content: Dict) -> str:
    """Get all text content from resume content dict."""
    parts = []
    for key, value in content.items():
        if isinstance(value, str) and value:
            parts.append(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    parts.append(" ".join(str(v) for v in item.values()))
        elif isinstance(value, dict):
            parts.append(" ".join(str(v) for v in value.values()))
    return " ".join(parts)


def _extract_user_experience_years(content: Dict) -> Optional[int]:
    """Extract total years of experience from user's resume content."""
    exp_items = content.get("experience", [])
    if not isinstance(exp_items, list):
        return None

    total_months = 0
    for exp in exp_items:
        if isinstance(exp, dict):
            start_date = exp.get("start_date")
            end_date = exp.get("end_date") or exp.get("currently_working", False)
            if start_date and end_date:
                try:
                    from datetime import datetime
                    start = datetime.fromisoformat(start_date) if isinstance(start_date, str) else start_date
                    if end_date is True or end_date == "present" or end_date == "current":
                        from datetime import date
                        end = date.today()
                    elif isinstance(end_date, str):
                        end = datetime.fromisoformat(end_date)
                    else:
                        end = end_date
                    
                    if isinstance(start, datetime):
                        start = start.date()
                    if isinstance(end, datetime):
                        end = end.date()
                    
                    months = (end - start).days // 30
                    total_months += months
                except Exception:
                    continue

    return total_months // 12 if total_months > 0 else None


def _extract_education_keywords(text: str) -> List[str]:
    """Extract education-related keywords from text."""
    keywords = []
    text_lower = text.lower()
    
    # Degree types
    degree_patterns = [
        r"bachelor['\"]?s?\s+(?:of\s+)?(?:science|arts|business|engineering)",
        r"master['\"]?s?\s+(?:of\s+)?(?:science|arts|business|engineering)",
        r"ph\.?d\.?\s*(?:in|of)?",
        r"b\.?sc\.?",
        r"m\.?sc\.?",
        r"mba",
        r"msc",
        r"bba",
        r"bs",
    ]
    
    for pattern in degree_patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            if match not in keywords:
                keywords.append(match)
    
    return keywords


def _utcnow_iso() -> str:
    """Get current UTC time as ISO 8601 string."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
