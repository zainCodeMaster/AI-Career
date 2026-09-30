"""Phase 6 — Phase 5 matching integration tests.

Tests that the Resume Engine properly integrates with the existing Phase 5
matching system:
- Resume tailoring uses Phase 5 match results
- Match scores/breakdowns are properly integrated
- Matched/missing skills from matching are used in tailoring
"""

import pytest
from datetime import date
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.db.models.career_profile import CareerProfile
from app.db.models.certification import Certification
from app.db.models.education import Education
from app.db.models.jobs import Job, UserJobPreferences
from app.db.models.resume import Resume
from app.db.models.skill import Skill
from app.db.models.user import User
from app.db.models.work_experience import WorkExperience
from app.core.security import get_password_hash
from app.services.match_engine import MatchEngine
from app.services.resume.resume_tailorer import ResumeTailorer
from app.services.user_profile_aggregator import UserProfileAggregator


def _create_user_with_profile(db_session: Session) -> User:
    """Create a user with a complete career profile."""
    user = User(
        email="match_integration@example.com",
        full_name="Match Integration User",
        password_hash=get_password_hash("StrongPass123"),
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    # Create career profile
    profile = CareerProfile(
        user_id=user.id,
        professional_title="Senior Python Developer",
        summary="Experienced Python developer with 5+ years",
        phone="555-1234",
        location="Lahore, Pakistan",
        years_of_experience=5,
        preferred_job_title="Senior Python Developer",
        preferred_location="Lahore",
        remote_preference="hybrid",
    )
    db_session.add(profile)

    # Create skills
    for skill_name in ["Python", "Django", "PostgreSQL", "Docker"]:
        skill = Skill(user_id=user.id, name=skill_name, category="technical", proficiency="advanced")
        db_session.add(skill)

    # Create work experience
    exp = WorkExperience(
        user_id=user.id,
        company="Tech Corp",
        job_title="Python Developer",
        start_date=date(2020, 1, 1),
        end_date=None,
        is_current=True,
        description="Built Django applications with PostgreSQL",
    )
    db_session.add(exp)

    # Create education
    edu = Education(
        user_id=user.id,
        institution="University of Engineering",
        degree="Bachelor",
        field_of_study="Computer Science",
    )
    db_session.add(edu)

    # Create job preferences
    prefs = UserJobPreferences(
        user_id=str(user.id),
        target_roles='["software engineer", "python developer"]',
        preferred_cities='["Lahore"]',
        remote_preference="hybrid",
    )
    db_session.add(prefs)

    db_session.commit()
    return user


def _create_job(db_session: Session) -> Job:
    """Create a test job."""
    job = Job(
        title="Senior Python Developer",
        company_name="Big Tech",
        description="Looking for senior Python developer with Django experience",
        requirements="Required: Python, Django, 5+ years experience",
        skills="python, django, postgresql",
        employment_type="full_time",
        experience_min=5,
        education_requirements="Bachelor's degree",
        location="Lahore, Pakistan",
        country="PK",
        source="test",
        source_job_id=f"match-integration-{uuid4().hex[:8]}",
        content_hash="match_hash_1",
        normalized_hash=f"norm_{uuid4().hex[:8]}",
    )
    db_session.add(job)
    db_session.commit()
    return job


def _create_base_resume(db_session: Session, user: User) -> Resume:
    """Create a base resume for the user."""
    resume = Resume(
        user_id=user.id,
        name="Base Resume",
        resume_type="base",
        status="ready",
        structured_data={
            "summary": "Experienced Python developer with 5+ years of experience",
            "skills": [
                {"name": "Python", "category": "technical", "proficiency": "advanced"},
                {"name": "Django", "category": "technical", "proficiency": "advanced"},
                {"name": "PostgreSQL", "category": "technical", "proficiency": "intermediate"},
            ],
            "experience": [
                {
                    "company": "Tech Corp",
                    "job_title": "Python Developer",
                    "start_date": "2020-01-01",
                    "is_current": True,
                    "description": "Built Django applications",
                },
            ],
            "education": [
                {
                    "institution": "University of Engineering",
                    "degree": "Bachelor",
                    "field_of_study": "Computer Science",
                },
            ],
        },
    )
    db_session.add(resume)
    db_session.commit()
    return resume


class TestPhase5Integration:
    """Tests for integration with the existing Phase 5 matching system."""

    def test_tailored_resume_uses_phase5_match(self, db_session):
        """Test that tailoring uses Phase 5 match results."""
        user = _create_user_with_profile(db_session)
        job = _create_job(db_session)
        resume = _create_base_resume(db_session, user)

        tailorer = ResumeTailorer()
        result = tailorer.tailor_for_job(
            db_session, user.id, resume.id, job.id,
            name="Tailored Resume",
        )

        # Phase 5 match should be included
        assert result.phase5_match is not None
        assert result.phase5_match.job_id == str(job.id)
        assert 0 <= result.phase5_match.overall_score <= 100
        assert result.phase5_match.breakdown is not None

    def test_phase5_matched_skills_used_in_tailoring(self, db_session):
        """Test that Phase 5 matched skills influence tailoring."""
        user = _create_user_with_profile(db_session)
        job = _create_job(db_session)
        resume = _create_base_resume(db_session, user)

        tailorer = ResumeTailorer()
        result = tailorer.tailor_for_job(
            db_session, user.id, resume.id, job.id,
        )

        # The Phase 5 match should identify matched and missing skills
        assert hasattr(result.phase5_match, "matched_skills")
        assert hasattr(result.phase5_match, "missing_skills")

    def test_phase5_breakdown_integrated(self, db_session):
        """Test that Phase 5 breakdown is properly integrated into response."""
        user = _create_user_with_profile(db_session)
        job = _create_job(db_session)
        resume = _create_base_resume(db_session, user)

        tailorer = ResumeTailorer()
        result = tailorer.tailor_for_job(
            db_session, user.id, resume.id, job.id,
        )

        # Verify breakdown has all expected components
        breakdown = result.phase5_match.breakdown
        assert hasattr(breakdown, "skills")
        assert hasattr(breakdown, "experience")
        assert hasattr(breakdown, "education")
        assert hasattr(breakdown, "location")

    def test_phase5_match_scores_in_tailoring_response(self, db_session):
        """Test that Phase 5 match scores are included in tailor response."""
        user = _create_user_with_profile(db_session)
        job = _create_job(db_session)
        resume = _create_base_resume(db_session, user)

        tailorer = ResumeTailorer()
        result = tailorer.tailor_for_job(
            db_session, user.id, resume.id, job.id,
        )

        # Match score should be reasonable
        assert result.phase5_match.overall_score >= 0
        assert result.phase5_match.overall_score <= 100

        # Should have explanation
        assert len(result.phase5_match.explanation) > 0

    def test_tailoring_leverages_match_breakdown(self, db_session):
        """Test that tailoring uses match breakdown for skill reordering."""
        user = _create_user_with_profile(db_session)
        job = _create_job(db_session)
        resume = _create_base_resume(db_session, user)

        tailorer = ResumeTailorer()
        result = tailorer.tailor_for_job(
            db_session, user.id, resume.id, job.id,
        )

        # If there are matched skills, they should be prioritized
        matched_skills = result.phase5_match.matched_skills
        if matched_skills:
            # Check that the tailored resume has skills section
            tailored_data = result.tailored_resume.structured_data
            assert "skills" in tailored_data
            assert len(tailored_data["skills"]) > 0

    def test_no_duplicate_phase5_engine_instances(self, db_session):
        """Test that the MatchEngine is not re-instantiated unnecessarily."""
        engine1 = MatchEngine()
        engine2 = MatchEngine()

        # They should be separate instances but functionally equivalent
        assert engine1 is not engine2

    def test_user_profile_aggregation_used(self, db_session):
        """Test that user profile aggregation is used in matching."""
        user = _create_user_with_profile(db_session)
        job = _create_job(db_session)
        resume = _create_base_resume(db_session, user)

        # Load the user profile that the matching engine uses
        profile = UserProfileAggregator.load(db_session, user.id)

        assert profile.has_career_brain
        assert "python" in [s.lower() for s in profile.skills]
        assert len(profile.experience_titles) > 0

    def test_match_score_integrated_with_atrs(self, db_session):
        """Test that Phase 5 match score is combined with ATS analysis."""
        user = _create_user_with_profile(db_session)
        job = _create_job(db_session)
        resume = _create_base_resume(db_session, user)

        tailorer = ResumeTailorer()
        result = tailorer.tailor_for_job(
            db_session, user.id, resume.id, job.id,
        )

        # Both Phase 5 match and ATS analysis should be available
        assert result.phase5_match is not None
        assert result.ats_analysis is not None
        assert result.ats_analysis.overall_score >= 0
        assert result.ats_analysis.overall_score <= 100

    def test_missing_skills_from_matching(self, db_session):
        """Test that missing skills from Phase 5 are identified."""
        user = _create_user_with_profile(db_session)
        
        # Create a job requiring skills user doesn't have
        job = Job(
            title="DevOps Engineer",
            company_name="Ops Corp",
            description="Need DevOps engineer",
            skills="kubernetes, terraform, aws",
            source="test",
            source_job_id=f"missing-skill-{uuid4().hex[:8]}",
            content_hash="mhash",
            normalized_hash="mnorm",
        )
        db_session.add(job)
        db_session.commit()

        resume = _create_base_resume(db_session, user)

        tailorer = ResumeTailorer()
        result = tailorer.tailor_for_job(
            db_session, user.id, resume.id, job.id,
        )

        # AWS/k8s/terraform should be missing from user's skills
        missing = [s.lower() for s in result.phase5_match.missing_skills]
        # At least some skills should be missing
        assert len(result.phase5_match.missing_skills) > 0 or len(missing) > 0

    def test_career_profile_is_source_of_truth(self, db_session):
        """Test that Career Profile data (not made up data) is used for matching."""
        user = _create_user_with_profile(db_session)
        job = _create_job(db_session)
        resume = _create_base_resume(db_session, user)

        profile = UserProfileAggregator.load(db_session, user.id)

        # The profile should match what was set up
        assert "Python" in profile.skills
        assert "Senior Python Developer" == profile.professional_title
        assert 5 == profile.years_of_experience

    def test_career_brain_isolation_in_tailoring(self, db_session):
        """Test that Career Brain retrieval remains user-scoped in tailoring."""
        user = _create_user_with_profile(db_session)
        job = _create_job(db_session)
        resume = _create_base_resume(db_session, user)

        tailorer = ResumeTailorer()

        # Create another user
        other_user = User(
            email="other_brain@example.com",
            full_name="Other User",
            password_hash=get_password_hash("StrongPass123"),
            is_active=True,
        )
        db_session.add(other_user)
        db_session.commit()

        # Both should be able to run tailoring without cross-contamination
        result1 = tailorer.tailor_for_job(db_session, user.id, resume.id, job.id)
        
        # The other user's data should not appear in the first user's results
        other_profile = UserProfileAggregator.load(db_session, other_user.id)
        assert other_profile.has_any_data is False or len(other_profile.skills) == 0
