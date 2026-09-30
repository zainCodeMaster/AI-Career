"""Phase 6 — Resume model tests.

Tests for:
- Resume model creation and attributes
- ResumeSection model
- Enum types and defaults
- Relationship setup
"""

import pytest
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.db.models.resume import Resume, ResumeSection, ResumeType, ResumeStatus
from app.db.models.user import User
from app.db.models.jobs import Job
from app.core.security import get_password_hash


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        email="resume_test@example.com",
        full_name="Resume Test User",
        password_hash=get_password_hash("StrongPass123"),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_job(db_session, test_user):
    """Create a test job for resume tailoring tests."""
    job = Job(
        title="Senior Python Developer",
        company_name="Tech Corp",
        description="We're looking for a senior Python developer with Django experience.",
        requirements="5+ years of Python, 3+ years of Django",
        skills="python, django, postgresql, docker",
        employment_type="full_time",
        experience_min=5,
        experience_max=None,
        education_requirements="Bachelor's degree in CS or related",
        location="Lahore, Pakistan",
        country="PK",
        source="test",
        source_job_id="test-job-1",
        content_hash="abc123",
        normalized_hash="def456",
        is_pakistan_eligible=True,
    )
    db_session.add(job)
    db_session.commit()
    return job


# ---------------------------------------------------------------------------
# Resume Model Tests
# ---------------------------------------------------------------------------


class TestResumeModel:
    """Tests for the Resume model."""

    def test_resume_creation(self, db_session, test_user):
        """Test creating a resume with all required fields."""
        resume = Resume(
            user_id=test_user.id,
            name="Software Engineer Resume",
            resume_type=ResumeType.BASE,
            status=ResumeStatus.DRAFT,
            version_number=1,
        )
        db_session.add(resume)
        db_session.commit()

        assert resume.id is not None
        assert resume.user_id == test_user.id
        assert resume.name == "Software Engineer Resume"
        assert resume.resume_type == ResumeType.BASE
        assert resume.status == ResumeStatus.DRAFT
        assert resume.version_number == 1
        assert resume.created_at is not None
        assert resume.updated_at is not None

    def test_resume_defaults(self, db_session, test_user):
        """Test default values for resume fields."""
        resume = Resume(
            user_id=test_user.id,
            name="Default Resume",
        )
        db_session.add(resume)
        db_session.commit()

        assert resume.resume_type == ResumeType.BASE
        assert resume.status == ResumeStatus.DRAFT
        assert resume.version_number == 1
        assert resume.target_job_id is None
        assert resume.parent_resume_id is None

    def test_resume_types(self, db_session, test_user):
        """Test different resume types."""
        for rtype in ResumeType:
            resume = Resume(
                user_id=test_user.id,
                name=f"{rtype.value} Resume",
                resume_type=rtype,
            )
            db_session.add(resume)
        db_session.commit()

        resumes = db_session.query(Resume).filter(Resume.user_id == test_user.id).all()
        assert len(resumes) == len(list(ResumeType))
        for r in resumes:
            assert r.resume_type in list(ResumeType)

    def test_resume_status_values(self, db_session, test_user):
        """Test different resume status values."""
        for status in ResumeStatus:
            resume = Resume(
                user_id=test_user.id,
                name=f"{status.value} Resume",
                status=status,
            )
            db_session.add(resume)
        db_session.commit()

        resumes = db_session.query(Resume).filter(Resume.user_id == test_user.id).all()
        assert len(resumes) == len(list(ResumeStatus))

    def test_resume_versioning(self, db_session, test_user):
        """Test that versions are properly linked."""
        base = Resume(
            user_id=test_user.id,
            name="Base Resume",
            resume_type=ResumeType.BASE,
            version_number=1,
        )
        db_session.add(base)
        db_session.flush()

        tailored = Resume(
            user_id=test_user.id,
            name="Tailored Resume",
            resume_type=ResumeType.TAILORED,
            version_number=1,
            parent_resume_id=base.id,
        )
        db_session.add(tailored)
        db_session.commit()

        assert tailored.parent_resume_id == base.id

    def test_resume_structured_data(self, db_session, test_user):
        """Test storing structured data in JSON column."""
        structured_data = {
            "summary": "Experienced Python developer",
            "skills": [{"name": "Python", "category": "technical"}],
            "experience": [{"company": "Tech Corp", "job_title": "Developer"}],
        }
        resume = Resume(
            user_id=test_user.id,
            name="Structured Resume",
            structured_data=structured_data,
        )
        db_session.add(resume)
        db_session.commit()

        fetched = db_session.get(Resume, resume.id)
        assert fetched.structured_data == structured_data
        assert fetched.structured_data["summary"] == "Experienced Python developer"

    def test_resume_import_metadata(self, db_session, test_user):
        """Test storing import metadata."""
        import_metadata = {
            "import_method": "text",
            "original_text_length": 5000,
            "parsed_sections": ["summary", "skills", "experience"],
        }
        resume = Resume(
            user_id=test_user.id,
            name="Imported Resume",
            resume_type=ResumeType.IMPORTED,
            source_file_name="resume.txt",
            source_file_type="txt",
            import_metadata=import_metadata,
        )
        db_session.add(resume)
        db_session.commit()

        fetched = db_session.get(Resume, resume.id)
        assert fetched.import_metadata == import_metadata
        assert fetched.source_file_name == "resume.txt"

    def test_resume_ats_cache(self, db_session, test_user, test_job):
        """Test storing ATS analysis cache."""
        resume = Resume(
            user_id=test_user.id,
            name="ATS Resume",
            ats_score=85,
            ats_breakdown={"keyword_coverage": 80, "skill_alignment": 90},
            ats_analyzed_for_job_id=test_job.id,
        )
        db_session.add(resume)
        db_session.commit()

        fetched = db_session.get(Resume, resume.id)
        assert fetched.ats_score == 85
        assert fetched.ats_breakdown["keyword_coverage"] == 80
        assert fetched.ats_analyzed_for_job_id == test_job.id

    def test_resume_repr(self, db_session, test_user):
        """Test resume __repr__."""
        resume = Resume(
            user_id=test_user.id,
            name="Test Resume",
        )
        db_session.add(resume)
        db_session.commit()

        repr_str = repr(resume)
        assert "Resume" in repr_str
        assert str(resume.id) in repr_str


# ---------------------------------------------------------------------------
# ResumeSection Model Tests
# ---------------------------------------------------------------------------


class TestResumeSectionModel:
    """Tests for the ResumeSection model."""

    def test_section_creation(self, db_session, test_user):
        """Test creating a resume section."""
        resume = Resume(
            user_id=test_user.id,
            name="Section Resume",
        )
        db_session.add(resume)
        db_session.flush()

        section = ResumeSection(
            resume_id=resume.id,
            section_type="skills",
            section_title="Technical Skills",
            content="Python, Django, PostgreSQL",
            display_order=1,
            is_custom=False,
        )
        db_session.add(section)
        db_session.commit()

        assert section.id is not None
        assert section.resume_id == resume.id
        assert section.section_type == "skills"
        assert section.content == "Python, Django, PostgreSQL"
        assert section.display_order == 1
        assert section.is_custom is False

    def test_section_defaults(self, db_session, test_user):
        """Test default values for section fields."""
        resume = Resume(user_id=test_user.id, name="Defaults Resume")
        db_session.add(resume)
        db_session.flush()

        section = ResumeSection(
            resume_id=resume.id,
            section_type="summary",
            content="Professional summary",
        )
        db_session.add(section)
        db_session.commit()

        assert section.display_order == 0
        assert section.is_custom is False
        assert section.section_title is None

    def test_section_repr(self, db_session, test_user):
        """Test section __repr__."""
        resume = Resume(user_id=test_user.id, name="Repr Resume")
        db_session.add(resume)
        db_session.flush()

        section = ResumeSection(
            resume_id=resume.id,
            section_type="skills",
            content="Python",
            display_order=0,
        )
        db_session.add(section)
        db_session.commit()

        repr_str = repr(section)
        assert "ResumeSection" in repr_str
        assert "skills" in repr_str


# ---------------------------------------------------------------------------
# Unique Constraints
# ---------------------------------------------------------------------------


class TestResumeConstraints:
    """Tests for database constraints."""

    def test_unique_resume_name_version_per_user(self, db_session, test_user):
        """Test that (user_id, name, version_number) is unique."""
        resume1 = Resume(
            user_id=test_user.id,
            name="Dup Name",
            version_number=1,
        )
        db_session.add(resume1)
        db_session.flush()

        resume2 = Resume(
            user_id=test_user.id,
            name="Dup Name",
            version_number=1,  # Same version!
        )
        db_session.add(resume2)

        with pytest.raises(Exception):
            db_session.commit()

    def test_unique_name_version_different_users(self, db_session, test_user):
        """Test that same name+version works for different users."""
        other_user = User(
            email="other@example.com",
            full_name="Other User",
            password_hash=get_password_hash("StrongPass123"),
            is_active=True,
        )
        db_session.add(other_user)
        db_session.flush()

        resume1 = Resume(user_id=test_user.id, name="My Resume", version_number=1)
        resume2 = Resume(user_id=other_user.id, name="My Resume", version_number=1)

        db_session.add(resume1)
        db_session.add(resume2)
        db_session.commit()

        # Both should exist without conflict
        assert resume1.id != resume2.id
