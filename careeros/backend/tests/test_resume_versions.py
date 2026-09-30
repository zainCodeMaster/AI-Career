"""Phase 6 — Resume versioning tests.

Tests for:
- Creating versioned resumes (tailored versions)
- Listing versions of a resume
- Original resume remains unchanged after tailoring
- Version history is correctly maintained
"""

import pytest
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.db.models.jobs import Job
from app.db.models.resume import Resume, ResumeSection, ResumeType
from app.db.models.user import User
from app.core.security import get_password_hash
from app.services.resume.resume_service import ResumeService
from app.services.resume.resume_tailorer import ResumeTailorer


def _create_user(db_session: Session, email: str) -> User:
    """Create a test user."""
    user = User(
        email=email,
        full_name=email.split("@")[0],
        password_hash=get_password_hash("StrongPass123"),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _create_resume(db_session: Session, user: User, name: str = "Test Resume") -> Resume:
    """Create a test resume."""
    resume = Resume(
        user_id=user.id,
        name=name,
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
                    "job_title": "Senior Python Developer",
                    "start_date": "2020-01-01",
                    "end_date": None,
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
        version_number=1,
    )
    db_session.add(resume)
    db_session.commit()
    return resume


def _create_job(db_session: Session) -> Job:
    """Create a test job."""
    job = Job(
        title="Senior Python Developer",
        company_name="Big Tech",
        description="Looking for senior Python developer",
        requirements="python, django, 5+ years experience",
        skills="python, django, postgresql, docker",
        employment_type="full_time",
        experience_min=5,
        education_requirements="Bachelor's degree",
        location="Lahore",
        country="PK",
        source="test",
        source_job_id="versioning-test-job",
        content_hash="hash123",
        normalized_hash="norm123",
    )
    db_session.add(job)
    db_session.commit()
    return job


class TestResumeVersioning:
    """Tests for resume version management."""

    @pytest.fixture
    def test_user_obj(self, db_session):
        """Create a test user."""
        user = User(
            email="versioning@example.com",
            full_name="Versioning User",
            password_hash=get_password_hash("StrongPass123"),
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        return user

    def test_create_base_resume(self, db_session, test_user_obj):
        """Test creating a base resume."""
        resume = _create_resume(db_session, test_user_obj, "Base Resume")
        
        assert resume.resume_type.value == "base"
        assert resume.version_number == 1
        assert resume.parent_resume_id is None
        assert resume.target_job_id is None

    def test_create_tailored_resume(self, db_session, test_user_obj):
        """Test creating a tailored version of a resume."""
        base_resume = _create_resume(db_session, test_user_obj, "Base")
        job = _create_job(db_session)

        # Create tailored version
        tailor = ResumeTailorer()
        result = tailor.tailor_for_job(
            db_session, test_user_obj.id,
            base_resume.id, job.id,
            name="Tailored for Senior Python",
        )

        tailored_resume = result.tailored_resume
        
        assert tailored_resume.resume_type == "tailored"
        assert tailored_resume.parent_resume_id == base_resume.id
        assert tailored_resume.target_job_id == job.id
        assert tailored_resume.version_number == 1

    def test_get_versions_lists_all(self, db_session, test_user_obj):
        """Test getting all versions of a resume."""
        base_resume = _create_resume(db_session, test_user_obj, "Base")
        job = _create_job(db_session)

        # Create a tailored version
        tailor = ResumeTailorer()
        result = tailor.tailor_for_job(
            db_session, test_user_obj.id,
            base_resume.id, job.id,
            name="Tailored Version",
        )

        # Get all versions
        versions = ResumeService.get_versions(db_session, test_user_obj.id, base_resume.id)

        assert len(versions) == 2
        # Base should be version 1
        assert versions[0].version_number == 1
        assert versions[0].id == base_resume.id
        # Tailored should be version 1 of its own, but linked as a version
        assert versions[1].id == result.tailored_resume.id

    def test_original_unchanged_after_tailoring(self, db_session, test_user_obj):
        """Test that the original resume is not modified after tailoring."""
        base_resume = _create_resume(db_session, test_user_obj, "Original")
        original_structured_data = dict(base_resume.structured_data)
        original_updated = base_resume.updated_at

        job = _create_job(db_session)

        # Create tailored version
        tailor = ResumeTailorer()
        result = tailor.tailor_for_job(
            db_session, test_user_obj.id,
            base_resume.id, job.id,
            name="Tailored Copy",
        )

        # Verify original is unchanged
        db_session.expire_all()
        original = db_session.get(Resume, base_resume.id)
        
        assert original.structured_data == original_structured_data
        assert original.name == "Original"
        assert original.resume_type.value == "base"

    def test_tailored_resume_references_correct_job(self, db_session, test_user_obj):
        """Test that tailored resume references the correct target job."""
        base_resume = _create_resume(db_session, test_user_obj, "Base for Job Test")
        job = _create_job(db_session)

        tailor = ResumeTailorer()
        result = tailor.tailor_for_job(
            db_session, test_user_obj.id,
            base_resume.id, job.id,
        )

        assert result.tailored_resume.target_job_id == str(job.id)

    def test_multiple_tailored_versions(self, db_session, test_user_obj):
        """Test creating multiple tailored versions for different jobs."""
        base_resume = _create_resume(db_session, test_user_obj, "Multi Base")
        
        job1 = _create_job(db_session)
        job2 = Job(
            title="Backend Engineer",
            company_name="Startup",
            description="Looking for backend engineer",
            skills="python, postgresql, redis",
            source="test",
            source_job_id="multi-test-job-2",
            content_hash="hash456",
            normalized_hash="norm456",
        )
        db_session.add(job2)
        db_session.commit()

        tailor = ResumeTailorer()

        # Tailor for job 1
        result1 = tailor.tailor_for_job(
            db_session, test_user_obj.id,
            base_resume.id, job1.id,
            name="Tailored for Job 1",
        )

        # Tailor for job 2
        result2 = tailor.tailor_for_job(
            db_session, test_user_obj.id,
            base_resume.id, job2.id,
            name="Tailored for Job 2",
        )

        versions = ResumeService.get_versions(db_session, test_user_obj.id, base_resume.id)
        assert len(versions) == 3  # Base + 2 tailored versions

        # Verify each tailored version references the correct job
        tailored_versions = [v for v in versions if v.resume_type == "tailored"]
        assert len(tailored_versions) == 2

        job_ids = {str(v.target_job_id) for v in tailored_versions}
        assert str(job1.id) in job_ids
        assert str(job2.id) in job_ids

    def test_version_number_increment(self, db_session, test_user_obj):
        """Test that version numbers increment correctly."""
        base_resume = Resume(
            user_id=test_user_obj.id,
            name="Version Test",
            version_number=1,
        )
        db_session.add(base_resume)
        db_session.commit()

        # Create a v2
        v2 = Resume(
            user_id=test_user_obj.id,
            name="Version Test",
            version_number=2,
            parent_resume_id=base_resume.id,
        )
        db_session.add(v2)
        db_session.commit()

        v3 = Resume(
            user_id=test_user_obj.id,
            name="Version Test",
            version_number=3,
            parent_resume_id=base_resume.id,
        )
        db_session.add(v3)
        db_session.commit()

        versions = ResumeService.get_versions(db_session, test_user_obj.id, base_resume.id)
        version_numbers = [v.version_number for v in versions]
        assert version_numbers == [1, 2, 3]
