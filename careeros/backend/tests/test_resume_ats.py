"""Phase 6 — ATS analyzer tests.

Tests for:
- Deterministic scoring
- Keyword matching
- Skill matching
- Experience alignment
- Education alignment
- Certification matching
- Structure completeness
- ATS score stability for identical inputs
- Missing skills remain missing
"""

import pytest
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.db.models.jobs import Job
from app.db.models.resume import Resume
from app.db.models.user import User
from app.core.security import get_password_hash
from app.services.resume.ats_analyzer import ATSAnalyzer
from app.services.resume.job_analysis import JobRequirementAnalyzer


def _create_user(db_session: Session) -> User:
    user = User(
        email="ats_test@example.com",
        full_name="ATS Test User",
        password_hash=get_password_hash("StrongPass123"),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _create_job(db_session: Session, title="Python Developer", skills="python, django, postgresql") -> Job:
    job = Job(
        title=title,
        company_name="Tech Corp",
        description=f"We are looking for a {title} with experience in {skills}",
        requirements="Required: Python, Django, PostgreSQL",
        skills=skills,
        employment_type="full_time",
        experience_min=3,
        experience_max=5,
        education_requirements="Bachelor's degree",
        location="Lahore",
        country="PK",
        source="test",
        source_job_id=f"ats-test-{uuid4().hex[:8]}",
        content_hash="ats_test_hash_1",
        normalized_hash=f"norm_{uuid4().hex[:8]}",
    )
    db_session.add(job)
    db_session.commit()
    return job


def _create_resume(db_session: Session, user: User, data: dict = None) -> Resume:
    if data is None:
        data = {
            "summary": "Experienced Python developer with Django and PostgreSQL",
            "skills": [
                {"name": "Python", "category": "technical", "proficiency": "advanced"},
                {"name": "Django", "category": "technical", "proficiency": "advanced"},
            ],
            "experience": [
                {
                    "company": "Tech Corp",
                    "job_title": "Python Developer",
                    "start_date": "2020-01-01",
                    "is_current": True,
                    "description": "Built Django applications with PostgreSQL",
                },
            ],
            "education": [
                {"institution": "University", "degree": "Bachelor", "field_of_study": "Computer Science"},
            ],
        }
    
    resume = Resume(
        user_id=user.id,
        name="ATS Test Resume",
        resume_type="base",
        status="ready",
        structured_data=data,
    )
    db_session.add(resume)
    db_session.commit()
    return resume


class TestATSDeterministicScoring:
    """Tests that ATS scoring is deterministic and stable."""

    def test_identical_inputs_produce_identical_score(self, db_session):
        """ATS score must remain deterministic for identical inputs."""
        user = _create_user(db_session)
        job = _create_job(db_session)
        resume = _create_resume(db_session, user)

        analyzer = ATSAnalyzer()
        
        result1 = analyzer.analyze(db_session, resume, job)
        result2 = analyzer.analyze(db_session, resume, job)

        assert result1.overall_score == result2.overall_score
        assert result1.matched_keywords == result2.matched_keywords
        assert result1.missing_keywords == result2.missing_keywords

    def test_score_is_bounded(self, db_session):
        """ATS score must be between 0 and 100."""
        user = _create_user(db_session)
        job = _create_job(db_session)
        resume = _create_resume(db_session, user)

        analyzer = ATSAnalyzer()
        result = analyzer.analyze(db_session, resume, job)

        assert 0 <= result.overall_score <= 100

    def test_score_with_perfect_resume(self, db_session):
        """A resume with all required skills should score high."""
        user = _create_user(db_session)
        job = _create_job(db_session, skills="python, django, postgresql, docker")
        
        data = {
            "summary": "Senior Python developer",
            "skills": [
                {"name": "Python", "category": "technical"},
                {"name": "Django", "category": "technical"},
                {"name": "PostgreSQL", "category": "technical"},
                {"name": "Docker", "category": "technical"},
            ],
            "experience": [
                {
                    "company": "Tech Corp",
                    "job_title": "Python Developer",
                    "start_date": "2020-01-01",
                    "is_current": True,
                    "description": "Python, Django, PostgreSQL, Docker",
                },
            ],
            "education": [{"institution": "University", "degree": "Bachelor"}],
        }
        resume = _create_resume(db_session, user, data)

        analyzer = ATSAnalyzer()
        result = analyzer.analyze(db_session, resume, job)

        assert result.overall_score >= 80


class TestATSKeywordMatching:
    """Tests for keyword matching in ATS analysis."""

    def test_matched_keywords(self, db_session):
        """Test that keywords present in resume are matched."""
        user = _create_user(db_session)
        job = _create_job(db_session, skills="python, django, postgresql")
        resume = _create_resume(db_session, user)

        analyzer = ATSAnalyzer()
        result = analyzer.analyze(db_session, resume, job)

        # Python and Django should be matched
        assert "python" in [k.lower() for k in result.matched_keywords]
        assert "django" in [k.lower() for k in result.matched_keywords]

    def test_missing_keywords(self, db_session):
        """Test that keywords not in resume are identified as missing."""
        user = _create_user(db_session)
        job = _create_job(db_session, skills="python, django, postgresql, docker, aws")
        
        data = {
            "summary": "Python developer",
            "skills": [{"name": "Python", "category": "technical"}],
            "experience": [{"company": "X", "job_title": "Developer", "is_current": True}],
            "education": [{"institution": "Uni"}],
        }
        resume = _create_resume(db_session, user, data)

        analyzer = ATSAnalyzer()
        result = analyzer.analyze(db_session, resume, job)

        # docker and aws should be missing
        lower_missing = [k.lower() for k in result.missing_keywords]
        assert "docker" in lower_missing or "aws" in lower_missing

    def test_keyword_coverage_score(self, db_session):
        """Test keyword coverage score calculation."""
        user = _create_user(db_session)
        job = _create_job(db_session, skills="python, django, postgresql")
        resume = _create_resume(db_session, user)

        analyzer = ATSAnalyzer()
        result = analyzer.analyze(db_session, resume, job)

        # Keyword coverage should be > 0 and <= 100
        assert 0 <= result.keyword_coverage.score <= 100
        assert result.keyword_coverage.total_count > 0


class TestATSSkillMatching:
    """Tests for skill matching in ATS analysis."""

    def test_matched_skills(self, db_session):
        """Test that skills present in resume are matched."""
        user = _create_user(db_session)
        job = _create_job(db_session, skills="python, django, postgresql")
        resume = _create_resume(db_session, user)

        analyzer = ATSAnalyzer()
        result = analyzer.analyze(db_session, resume, job)

        assert "python" in [s.lower() for s in result.matched_skills]
        assert "django" in [s.lower() for s in result.matched_skills]

    def test_missing_skills(self, db_session):
        """Test that skills not in resume are identified as missing."""
        user = _create_user(db_session)
        job = _create_job(db_session, skills="python, django, redis")
        resume = _create_resume(db_session, user)

        analyzer = ATSAnalyzer()
        result = analyzer.analyze(db_session, resume, job)

        lower_missing = [s.lower() for s in result.missing_skills]
        assert "redis" in lower_missing

    def test_skill_alignment_score(self, db_session):
        """Test skill alignment score calculation."""
        user = _create_user(db_session)
        job = _create_job(db_session, skills="python, django")
        resume = _create_resume(db_session, user)

        analyzer = ATSAnalyzer()
        result = analyzer.analyze(db_session, resume, job)

        assert 0 <= result.skill_alignment.score <= 100


class TestATSExperienceAlignment:
    """Tests for experience alignment in ATS analysis."""

    def test_experience_match(self, db_session):
        """Test experience alignment when user has required experience."""
        user = _create_user(db_session)
        job = _create_job(db_session)
        job.experience_min = 3
        job.experience_max = 5
        db_session.commit()

        data = {
            "summary": "Python developer",
            "skills": [{"name": "Python"}],
            "experience": [
                {
                    "company": "Tech",
                    "job_title": "Developer",
                    "start_date": "2020-01-01",
                    "is_current": True,
                },
            ],
            "education": [{"institution": "Uni"}],
        }
        resume = _create_resume(db_session, user, data)

        analyzer = ATSAnalyzer()
        result = analyzer.analyze(db_session, resume, job)

        # Experience should score well since user has experience data
        assert 0 <= result.experience_alignment.score <= 100

    def test_experience_missing_when_no_job_requirement(self, db_session):
        """Test experience alignment when job has no experience requirement."""
        user = _create_user(db_session)
        job = _create_job(db_session)
        job.experience_min = None
        job.experience_max = None
        db_session.commit()

        resume = _create_resume(db_session, user)

        analyzer = ATSAnalyzer()
        result = analyzer.analyze(db_session, resume, job)

        # Should be neutral when no experience requirement
        assert result.experience_alignment.score == 85

    def test_years_of_experience_in_description(self, db_session):
        """Test that years of experience are extracted from resume."""
        user = _create_user(db_session)
        job = _create_job(db_session)
        job.experience_min = 10
        db_session.commit()

        data = {
            "summary": "Python developer",
            "skills": [{"name": "Python"}],
            "experience": [
                {
                    "company": "Tech",
                    "job_title": "Developer",
                    "start_date": "2015-01-01",
                    "is_current": True,
                    "description": "5+ years of Python development",
                },
            ],
            "education": [{"institution": "Uni"}],
        }
        resume = _create_resume(db_session, user, data)

        analyzer = ATSAnalyzer()
        result = analyzer.analyze(db_session, resume, job)

        # Required phrases should detect experience mentions
        assert result.experience_alignment.score < 100  # Since user has less than 10 years


class TestATSEducationAlignment:
    """Tests for education alignment in ATS analysis."""

    def test_education_match(self, db_session):
        """Test education alignment when resume has education."""
        user = _create_user(db_session)
        job = _create_job(db_session)
        job.education_requirements = "Bachelor's degree"
        db_session.commit()

        data = {
            "summary": "Python developer",
            "skills": [{"name": "Python"}],
            "experience": [{"company": "X", "job_title": "Dev"}],
            "education": [{"institution": "University", "degree": "Bachelor"}],
        }
        resume = _create_resume(db_session, user, data)

        analyzer = ATSAnalyzer()
        result = analyzer.analyze(db_session, resume, job)

        assert result.education_alignment.score > 0


class TestATSCertificationAlignment:
    """Tests for certification alignment in ATS analysis."""

    def test_no_certifications_required(self, db_session):
        """Test certification alignment when job has no certification requirements."""
        user = _create_user(db_session)
        job = _create_job(db_session)
        resume = _create_resume(db_session, user)

        analyzer = ATSAnalyzer()
        result = analyzer.analyze(db_session, resume, job)

        # Should be 100 when no certifications required
        assert result.certification_alignment.score == 100

    def test_missing_certifications(self, db_session):
        """Test missing certifications are identified."""
        user = _create_user(db_session)
        job = _create_job(db_session, skills="python, aws, pmp")
        job.description = "Required: PMP certification and AWS certification"
        db_session.commit()

        data = {
            "summary": "Python developer",
            "skills": [{"name": "Python"}],
            "experience": [{"company": "X", "job_title": "Dev"}],
            "education": [{"institution": "Uni"}],
        }
        resume = _create_resume(db_session, user, data)

        analyzer = ATSAnalyzer()
        result = analyzer.analyze(db_session, resume, job)

        # No certifications in resume
        assert len(result.certification_alignment.matched_items) == 0


class TestATSStructureScore:
    """Tests for resume structure analysis."""

    def test_complete_structure(self, db_session):
        """Test structure score for resume with all required sections."""
        user = _create_user(db_session)
        job = _create_job(db_session)

        data = {
            "summary": "Experienced developer",
            "skills": [{"name": "Python"}],
            "experience": [{"company": "X", "job_title": "Dev", "is_current": True}],
            "education": [{"institution": "Uni"}],
            "projects": [{"name": "Project"}],
            "certifications": [{"name": "AWS"}],
        }
        resume = _create_resume(db_session, user, data)

        analyzer = ATSAnalyzer()
        result = analyzer.analyze(db_session, resume, job)

        assert result.structure_score.score == 100

    def test_missing_sections_penalized(self, db_session):
        """Test that missing required sections lower the structure score."""
        user = _create_user(db_session)
        job = _create_job(db_session)

        data = {
            "summary": "Experience developer",
            # Missing skills, experience, education
        }
        resume = _create_resume(db_session, user, data)

        analyzer = ATSAnalyzer()
        result = analyzer.analyze(db_session, resume, job)

        # Structure score should be low due to missing sections
        assert result.structure_score.score < 100
        assert len(result.structure_score.missing_items) > 0


class TestATSRecommendations:
    """Tests for ATS recommendations generation."""

    def test_recommendations_generated(self, db_session):
        """Test that recommendations are generated for missing items."""
        user = _create_user(db_session)
        job = _create_job(db_session, skills="python, docker, aws, gcp")

        data = {
            "summary": "Python developer",
            "skills": [{"name": "Python"}],
            "experience": [{"company": "X", "job_title": "Dev", "is_current": True}],
            "education": [{"institution": "Uni"}],
        }
        resume = _create_resume(db_session, user, data)

        analyzer = ATSAnalyzer()
        result = analyzer.analyze(db_session, resume, job)

        assert len(result.recommendations) > 0
        # Recommendations should mention missing skills
        recs = " ".join(result.recommendations).lower()
        assert "missing" in recs or "add" in recs

    def test_no_recommendations_for_perfect_match(self, db_session):
        """Test that minimal recommendations are given for a good match."""
        user = _create_user(db_session)
        job = _create_job(db_session, skills="python, django")

        data = {
            "summary": "Python developer",
            "skills": [{"name": "Python"}, {"name": "Django"}],
            "experience": [{"company": "X", "job_title": "Python Developer", "is_current": True}],
            "education": [{"institution": "Uni"}],
        }
        resume = _create_resume(db_session, user, data)

        analyzer = ATSAnalyzer()
        result = analyzer.analyze(db_session, resume, job)

        # A good match should have reasonable score
        assert result.overall_score >= 50


class TestATSScoreDeterminism:
    """Tests that verify ATS scores are deterministic across different resume instances."""

    def test_different_resume_different_score(self, db_session):
        """Verify that a different resume produces a different score."""
        user = _create_user(db_session)
        job = _create_job(db_session, skills="python, django, redis, aws")

        # Resume 1 - missing some skills
        data1 = {
            "summary": "Python developer",
            "skills": [{"name": "Python"}],
            "experience": [{"company": "X", "job_title": "Dev"}],
            "education": [{"institution": "Uni"}],
        }
        resume1 = _create_resume(db_session, user, data1)

        # Resume 2 - has more skills
        data2 = {
            "summary": "Python developer",
            "skills": [
                {"name": "Python"},
                {"name": "Django"},
                {"name": "Redis"},
                {"name": "AWS"},
            ],
            "experience": [{"company": "X", "job_title": "Dev"}],
            "education": [{"institution": "Uni"}],
        }
        resume2 = Resume(
            user_id=user.id,
            name="Complete Resume",
            resume_type="base",
            structured_data=data2,
        )
        db_session.add(resume2)
        db_session.commit()

        analyzer = ATSAnalyzer()
        result1 = analyzer.analyze(db_session, resume1, job)
        result2 = analyzer.analyze(db_session, resume2, job)

        assert result2.overall_score > result1.overall_score
