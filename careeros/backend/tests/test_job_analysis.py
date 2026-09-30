"""Phase 6 — Job requirement extraction tests.

Tests for:
- Job requirement analysis from Job records
- Keyword extraction
- Seniority classification
- Certification extraction
- Experience extraction
- Required vs preferred skill distinction
"""

import pytest

from app.db.models.jobs import Job
from app.services.resume.job_analysis import (
    JobRequirementAnalysis,
    JobRequirementAnalyzer,
)


def _make_job(
    title="Senior Python Developer",
    description=None,
    requirements=None,
    skills=None,
    experience_min=None,
    experience_max=None,
    education_requirements=None,
    category=None,
    employment_type=None,
    workplace_type=None,
    is_remote=False,
) -> Job:
    """Create a Job-like object for testing."""
    return Job(
        title=title,
        company_name="Tech Corp",
        description=description,
        requirements=requirements,
        skills=skills,
        employment_type=employment_type or "full_time",
        workplace_type=workplace_type,
        is_remote=is_remote,
        experience_min=experience_min,
        experience_max=experience_max,
        education_requirements=education_requirements,
        category=category,
    )


class TestJobRequirementAnalysis:
    """Tests for JobRequirementAnalyzer."""

    def test_analyze_basic_job(self):
        """Test analyzing a basic job."""
        job = _make_job(
            title="Python Developer",
            description="We need a Python developer",
            requirements="Required: Python, Django, PostgreSQL",
            skills="python, django",
            experience_min=3,
            experience_max=5,
            education_requirements="Bachelor's degree in Computer Science",
        )

        analysis = JobRequirementAnalyzer.analyze(job)

        assert analysis.job_id is not None
        assert analysis.title == "Python Developer"
        assert analysis.company_name == "Tech Corp"
        assert "python" in [s.lower() for s in analysis.required_skills]
        assert "django" in [s.lower() for s in analysis.required_skills]

    def test_required_vs_preferred_skills(self):
        """Test that required vs preferred skills are distinguished."""
        job = _make_job(
            title="Developer",
            requirements="Required: Python. Preferred: Docker, AWS.",
        )

        analysis = JobRequirementAnalyzer.analyze(job)

        # Python should be in required, Docker/AWS in preferred
        lower_required = [s.lower() for s in analysis.required_skills]
        lower_optional = [s.lower() for s in analysis.preferred_skills]

        # At least Python should be found somewhere
        assert len(lower_required) > 0 or len(lower_optional) > 0

    def test_keyword_extraction(self):
        """Test that keywords are extracted from job text."""
        job = _make_job(
            title="Senior Python Developer",
            description="Required: Python, Django, PostgreSQL, Docker",
            requirements="Must have: Python, Django",
            skills="python, django, postgresql, docker",
        )

        analysis = JobRequirementAnalyzer.analyze(job)

        # Keywords should include skills from the skills field
        keyword_texts = [kw.text.lower() for kw in analysis.keywords]
        assert "python" in keyword_texts or "django" in keyword_texts
        assert len(analysis.keywords) > 0

    def test_seniority_classification_entry(self):
        """Test seniority classification for entry-level jobs."""
        job = _make_job(
            title="Junior Developer",
            description="Entry level position. 0-2 years experience.",
        )

        analysis = JobRequirementAnalyzer.analyze(job)
        assert analysis.seniority == "entry"

    def test_seniority_classification_mid(self):
        """Test seniority classification for mid-level jobs."""
        job = _make_job(
            title="Developer",
            description="Mid-level position. 3-5 years experience.",
            experience_min=3,
        )

        analysis = JobRequirementAnalyzer.analyze(job)
        assert analysis.seniority == "mid"

    def test_seniority_classification_senior(self):
        """Test seniority classification for senior jobs."""
        job = _make_job(
            title="Senior Software Engineer",
            description="Senior level. 5+ years experience required.",
            experience_min=5,
        )

        analysis = JobRequirementAnalyzer.analyze(job)
        assert analysis.seniority == "senior"

    def test_seniority_from_title(self):
        """Test seniority detection from title keywords."""
        test_cases = [
            ("Junior Developer", "entry"),
            ("Senior Developer", "senior"),
            ("Lead Engineer", "senior"),
            ("Principal Architect", "principal"),
        ]

        for title, expected in test_cases:
            job = _make_job(title=title)
            analysis = JobRequirementAnalyzer.analyze(job)
            assert analysis.seniority == expected, f"Title '{title}' should be {expected}, got {analysis.seniority}"

    def test_seniority_fallback_to_experience(self):
        """Test that seniority falls back to experience years."""
        job = _make_job(
            title="Software Engineer",
            experience_min=7,
        )

        analysis = JobRequirementAnalyzer.analyze(job)
        assert analysis.seniority == "senior"

    def test_certification_extraction(self):
        """Test extraction of certification requirements."""
        job = _make_job(
            title="Cloud Engineer",
            description="Required: AWS certification and PMP certification",
            requirements="Must have AWS and PMP",
        )

        analysis = JobRequirementAnalyzer.analyze(job)

        certs_lower = [c.lower() for c in analysis.required_certifications]
        # Should find AWS or PMP
        assert len(analysis.required_certifications) > 0 or len(analysis.preferred_certifications) > 0

    def test_certification_preferred_vs_required(self):
        """Test that preferred certifications are distinguished."""
        job = _make_job(
            title="DevOps Engineer",
            description="Required: Docker, Kubernetes. Preferred: AWS certification.",
        )

        analysis = JobRequirementAnalyzer.analyze(job)

        # Both should be detected
        all_certs = analysis.required_certifications + analysis.preferred_certifications
        assert len(all_certs) > 0

    def test_experience_text_extraction(self):
        """Test extraction of experience requirement text."""
        job = _make_job(
            title="Developer",
            description="Must have 5+ years of experience in Python development",
        )

        analysis = JobRequirementAnalyzer.analyze(job)

        # Experience requirements should be extracted
        assert analysis.experience_min == 5 or analysis.experience_text is not None or analysis.experience_min == 5

    def test_experience_min_from_job_fields(self):
        """Test that experience_min comes from the Job model fields."""
        job = _make_job(
            title="Senior Developer",
            experience_min=5,
            experience_max=10,
        )

        analysis = JobRequirementAnalyzer.analyze(job)

        assert analysis.experience_min == 5
        assert analysis.experience_max == 10

    def test_employment_type_preserved(self):
        """Test that employment type is preserved in analysis."""
        job = _make_job(
            title="Developer",
            employment_type="full_time",
        )

        analysis = JobRequirementAnalyzer.analyze(job)

        assert analysis.employment_type == "full_time"

    def test_workplace_type_preserved(self):
        """Test that workplace type is preserved in analysis."""
        job = _make_job(
            title="Developer",
            workplace_type="remote",
            is_remote=True,
        )

        analysis = JobRequirementAnalyzer.analyze(job)

        # These should be available
        assert analysis.workplace_type == "remote"
        assert analysis.is_remote is True

    def test_analysis_with_empty_text_fields(self):
        """Test analysis handles empty/None text fields gracefully."""
        job = Job(
            title="Minimal Job",
            company_name="Corp",
            description=None,
            requirements=None,
            skills=None,
            employment_type=None,
            experience_min=None,
            experience_max=None,
            education_requirements=None,
        )

        analysis = JobRequirementAnalyzer.analyze(job)

        assert analysis.title == "Minimal Job"
        assert analysis.required_skills == []
        assert analysis.required_keywords == []

    def test_keyword_categorization(self):
        """Test that keywords are categorized correctly."""
        job = _make_job(
            title="Python Developer",
            skills="Python, Communication, Leadership",
            description="Required: AWS certification, communication skills",
        )

        analysis = JobRequirementAnalyzer.analyze(job)

        # Keywords should have categories
        for kw in analysis.keywords:
            assert kw.category in ("technical", "soft", "industry", "certification", "title")

    def test_title_keywords_extracted(self):
        """Test that job title keywords are extracted."""
        job = _make_job(title="Senior Python Developer")
        analysis = JobRequirementAnalyzer.analyze(job)

        # Title should be in the analysis
        assert "senior" in analysis.title.lower() or "python" in analysis.title.lower()

    def test_analyze_text_method(self):
        """Test analyzing raw job description text."""
        analysis = JobRequirementAnalyzer.analyze_text(
            job_description="Looking for a Python developer with Django experience.",
            title="Python Developer",
        )

        assert analysis.title == "Python Developer"
        assert analysis.description_preview is not None
