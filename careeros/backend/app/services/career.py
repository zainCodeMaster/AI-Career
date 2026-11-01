"""Service layer for career profile operations."""

from typing import Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from pydantic import HttpUrl

from app.db.models.career_profile import CareerProfile
from app.db.models.education import Education
from app.db.models.work_experience import WorkExperience
from app.db.models.skill import Skill
from app.db.models.certification import Certification
from app.schemas.career import (
    CareerProfileCreate,
    CareerProfileUpdate,
    EducationCreate,
    EducationUpdate,
    WorkExperienceCreate,
    WorkExperienceUpdate,
    SkillCreate,
    SkillUpdate,
    CertificationCreate,
    CertificationUpdate,
)
from app.services.audit import create_audit_log


def _to_db_value(v: Any) -> Any:
    """Convert Pydantic types to plain Python types for SQLAlchemy binding."""
    if isinstance(v, HttpUrl):
        return str(v)
    return v


def _dump_for_db(data: dict[str, Any]) -> dict[str, Any]:
    """Dump a Pydantic model to a dict with SQLAlchemy-safe values."""
    return {k: _to_db_value(v) for k, v in data.items()}


class CareerProfileService:
    """Service for career profile operations."""

    @staticmethod
    def create_profile(db: Session, user_id: UUID, profile_data: CareerProfileCreate) -> CareerProfile:
        """Create career profile for user."""
        profile = CareerProfile(user_id=user_id, **_dump_for_db(profile_data.model_dump()))
        db.add(profile)
        db.commit()
        db.refresh(profile)
        create_audit_log(
            db,
            event_type="PROFILE_CREATED",
            user_id=user_id,
            details={"profile_id": str(profile.id)},
        )
        return profile

    @staticmethod
    def get_profile(db: Session, user_id: UUID) -> Optional[CareerProfile]:
        """Get career profile for user."""
        return db.query(CareerProfile).filter(CareerProfile.user_id == user_id).first()

    @staticmethod
    def calculate_completeness(db: Session, user_id: UUID) -> int:
        """Calculate career profile completeness score (0-100)."""
        profile = CareerProfileService.get_profile(db, user_id)
        if not profile:
            return 0

        score = 0

        # Profile fields (50 points total)
        if profile.professional_title:
            score += 10
        if profile.summary:
            score += 10
        if profile.location:
            score += 5
        if profile.linkedin_url:
            score += 5
        if profile.github_url:
            score += 5
        if profile.years_of_experience is not None:
            score += 5
        if profile.preferred_job_title:
            score += 5
        if profile.preferred_location:
            score += 5

        # Education (15 points)
        educations = EducationService.get_user_education(db, user_id)
        if educations:
            score += 15

        # Experience (20 points)
        experiences = WorkExperienceService.get_user_work_experience(db, user_id)
        if experiences:
            score += 20

        # Skills (10 points)
        skills = SkillService.get_user_skills(db, user_id)
        if skills:
            score += 10

        return min(score, 100)

    @staticmethod
    def get_profile_with_completeness(db: Session, user_id: UUID) -> Optional[dict]:
        """Get career profile with completeness score."""
        profile = CareerProfileService.get_profile(db, user_id)
        if not profile:
            return None

        score = CareerProfileService.calculate_completeness(db, user_id)

        return {
            "id": str(profile.id),
            "user_id": str(profile.user_id),
            "professional_title": profile.professional_title,
            "summary": profile.summary,
            "phone": profile.phone,
            "location": profile.location,
            "linkedin_url": str(profile.linkedin_url) if profile.linkedin_url else None,
            "github_url": str(profile.github_url) if profile.github_url else None,
            "portfolio_url": str(profile.portfolio_url) if profile.portfolio_url else None,
            "years_of_experience": profile.years_of_experience,
            "preferred_job_title": profile.preferred_job_title,
            "preferred_location": profile.preferred_location,
            "remote_preference": profile.remote_preference,
            "created_at": profile.created_at,
            "updated_at": profile.updated_at,
            "completeness_score": score,
        }

    @staticmethod
    def update_profile(db: Session, user_id: UUID, update_data: CareerProfileUpdate) -> Optional[CareerProfile]:
        """Update career profile."""
        profile = db.query(CareerProfile).filter(CareerProfile.user_id == user_id).first()
        if not profile:
            return None

        update_dict = _dump_for_db(update_data.model_dump(exclude_unset=True))
        for key, value in update_dict.items():
            setattr(profile, key, value)
        db.commit()
        db.refresh(profile)

        create_audit_log(
            db,
            event_type="PROFILE_UPDATED",
            user_id=user_id,
            details={"profile_id": str(profile.id), "fields_updated": list(update_dict.keys())},
        )
        return profile


class EducationService:
    """Service for education operations."""

    @staticmethod
    def create_education(db: Session, user_id: UUID, education_data: EducationCreate) -> Education:
        """Create education record."""
        education = Education(user_id=user_id, **_dump_for_db(education_data.model_dump()))
        db.add(education)
        db.commit()
        db.refresh(education)

        create_audit_log(
            db,
            event_type="EDUCATION_CREATED",
            user_id=user_id,
            details={"education_id": str(education.id), "institution": education.institution},
        )
        return education

    @staticmethod
    def get_education(db: Session, education_id: UUID, user_id: UUID) -> Optional[Education]:
        """Get education record with ownership check."""
        return db.query(Education).filter(
            and_(Education.id == education_id, Education.user_id == user_id)
        ).first()

    @staticmethod
    def get_user_education(db: Session, user_id: UUID) -> list[Education]:
        """Get all education records for user."""
        return db.query(Education).filter(Education.user_id == user_id).order_by(Education.created_at.desc()).all()

    @staticmethod
    def update_education(
        db: Session, education_id: UUID, user_id: UUID, update_data: EducationUpdate
    ) -> Optional[Education]:
        """Update education record with ownership check."""
        education = db.query(Education).filter(
            and_(Education.id == education_id, Education.user_id == user_id)
        ).first()
        if not education:
            return None

        update_dict = _dump_for_db(update_data.model_dump(exclude_unset=True))
        for key, value in update_dict.items():
            setattr(education, key, value)
        db.commit()
        db.refresh(education)

        create_audit_log(
            db,
            event_type="EDUCATION_UPDATED",
            user_id=user_id,
            details={"education_id": str(education.id), "fields_updated": list(update_dict.keys())},
        )
        return education

    @staticmethod
    def delete_education(db: Session, education_id: UUID, user_id: UUID) -> bool:
        """Delete education record with ownership check."""
        education = db.query(Education).filter(
            and_(Education.id == education_id, Education.user_id == user_id)
        ).first()
        if not education:
            return False

        db.delete(education)
        db.commit()

        create_audit_log(
            db,
            event_type="EDUCATION_DELETED",
            user_id=user_id,
            details={"education_id": str(education_id), "institution": education.institution},
        )
        return True


class WorkExperienceService:
    """Service for work experience operations."""

    @staticmethod
    def create_work_experience(db: Session, user_id: UUID, experience_data: WorkExperienceCreate) -> WorkExperience:
        """Create work experience record."""
        experience = WorkExperience(user_id=user_id, **_dump_for_db(experience_data.model_dump()))
        db.add(experience)
        db.commit()
        db.refresh(experience)

        create_audit_log(
            db,
            event_type="WORK_EXPERIENCE_CREATED",
            user_id=user_id,
            details={"experience_id": str(experience.id), "company": experience.company},
        )
        return experience

    @staticmethod
    def get_work_experience(db: Session, experience_id: UUID, user_id: UUID) -> Optional[WorkExperience]:
        """Get work experience record with ownership check."""
        return db.query(WorkExperience).filter(
            and_(WorkExperience.id == experience_id, WorkExperience.user_id == user_id)
        ).first()

    @staticmethod
    def get_user_work_experience(db: Session, user_id: UUID) -> list[WorkExperience]:
        """Get all work experience records for user."""
        return db.query(WorkExperience).filter(WorkExperience.user_id == user_id).order_by(
            WorkExperience.start_date.desc()
        ).all()

    @staticmethod
    def update_work_experience(
        db: Session, experience_id: UUID, user_id: UUID, update_data: WorkExperienceUpdate
    ) -> Optional[WorkExperience]:
        """Update work experience record with ownership check."""
        experience = db.query(WorkExperience).filter(
            and_(WorkExperience.id == experience_id, WorkExperience.user_id == user_id)
        ).first()
        if not experience:
            return None

        update_dict = _dump_for_db(update_data.model_dump(exclude_unset=True))
        for key, value in update_dict.items():
            setattr(experience, key, value)
        db.commit()
        db.refresh(experience)

        create_audit_log(
            db,
            event_type="WORK_EXPERIENCE_UPDATED",
            user_id=user_id,
            details={"experience_id": str(experience.id), "fields_updated": list(update_dict.keys())},
        )
        return experience

    @staticmethod
    def delete_work_experience(db: Session, experience_id: UUID, user_id: UUID) -> bool:
        """Delete work experience record with ownership check."""
        experience = db.query(WorkExperience).filter(
            and_(WorkExperience.id == experience_id, WorkExperience.user_id == user_id)
        ).first()
        if not experience:
            return False

        db.delete(experience)
        db.commit()

        create_audit_log(
            db,
            event_type="WORK_EXPERIENCE_DELETED",
            user_id=user_id,
            details={"experience_id": str(experience_id), "company": experience.company},
        )
        return True


class SkillService:
    """Service for skill operations."""

    @staticmethod
    def create_skill(db: Session, user_id: UUID, skill_data: SkillCreate) -> Skill:
        """Create skill record."""
        skill = Skill(user_id=user_id, **_dump_for_db(skill_data.model_dump()))
        db.add(skill)
        db.commit()
        db.refresh(skill)

        create_audit_log(
            db,
            event_type="SKILL_CREATED",
            user_id=user_id,
            details={"skill_id": str(skill.id), "name": skill.name},
        )
        return skill

    @staticmethod
    def get_skill(db: Session, skill_id: UUID, user_id: UUID) -> Optional[Skill]:
        """Get skill record with ownership check."""
        return db.query(Skill).filter(and_(Skill.id == skill_id, Skill.user_id == user_id)).first()

    @staticmethod
    def get_user_skills(db: Session, user_id: UUID) -> list[Skill]:
        """Get all skills for user."""
        return db.query(Skill).filter(Skill.user_id == user_id).order_by(Skill.created_at.desc()).all()

    @staticmethod
    def update_skill(db: Session, skill_id: UUID, user_id: UUID, update_data: SkillUpdate) -> Optional[Skill]:
        """Update skill record with ownership check."""
        skill = db.query(Skill).filter(and_(Skill.id == skill_id, Skill.user_id == user_id)).first()
        if not skill:
            return None

        update_dict = _dump_for_db(update_data.model_dump(exclude_unset=True))
        for key, value in update_dict.items():
            setattr(skill, key, value)
        db.commit()
        db.refresh(skill)

        create_audit_log(
            db,
            event_type="SKILL_UPDATED",
            user_id=user_id,
            details={"skill_id": str(skill.id), "fields_updated": list(update_dict.keys())},
        )
        return skill

    @staticmethod
    def delete_skill(db: Session, skill_id: UUID, user_id: UUID) -> bool:
        """Delete skill record with ownership check."""
        skill = db.query(Skill).filter(and_(Skill.id == skill_id, Skill.user_id == user_id)).first()
        if not skill:
            return False

        db.delete(skill)
        db.commit()

        create_audit_log(
            db,
            event_type="SKILL_DELETED",
            user_id=user_id,
            details={"skill_id": str(skill_id), "name": skill.name},
        )
        return True


class CertificationService:
    """Service for certification operations."""

    @staticmethod
    def create_certification(db: Session, user_id: UUID, certification_data: CertificationCreate) -> Certification:
        """Create certification record."""
        certification = Certification(user_id=user_id, **_dump_for_db(certification_data.model_dump()))
        db.add(certification)
        db.commit()
        db.refresh(certification)

        create_audit_log(
            db,
            event_type="CERTIFICATION_CREATED",
            user_id=user_id,
            details={"certification_id": str(certification.id), "name": certification.name},
        )
        return certification

    @staticmethod
    def get_certification(db: Session, certification_id: UUID, user_id: UUID) -> Optional[Certification]:
        """Get certification record with ownership check."""
        return db.query(Certification).filter(
            and_(Certification.id == certification_id, Certification.user_id == user_id)
        ).first()

    @staticmethod
    def get_user_certifications(db: Session, user_id: UUID) -> list[Certification]:
        """Get all certifications for user."""
        return db.query(Certification).filter(Certification.user_id == user_id).order_by(
            Certification.created_at.desc()
        ).all()

    @staticmethod
    def update_certification(
        db: Session, certification_id: UUID, user_id: UUID, update_data: CertificationUpdate
    ) -> Optional[Certification]:
        """Update certification record with ownership check."""
        certification = db.query(Certification).filter(
            and_(Certification.id == certification_id, Certification.user_id == user_id)
        ).first()
        if not certification:
            return None

        update_dict = _dump_for_db(update_data.model_dump(exclude_unset=True))
        for key, value in update_dict.items():
            setattr(certification, key, value)
        db.commit()
        db.refresh(certification)

        create_audit_log(
            db,
            event_type="CERTIFICATION_UPDATED",
            user_id=user_id,
            details={"certification_id": str(certification.id), "fields_updated": list(update_dict.keys())},
        )
        return certification

    @staticmethod
    def delete_certification(db: Session, certification_id: UUID, user_id: UUID) -> bool:
        """Delete certification record with ownership check."""
        certification = db.query(Certification).filter(
            and_(Certification.id == certification_id, Certification.user_id == user_id)
        ).first()
        if not certification:
            return False

        db.delete(certification)
        db.commit()

        create_audit_log(
            db,
            event_type="CERTIFICATION_DELETED",
            user_id=user_id,
            details={"certification_id": str(certification_id), "name": certification.name},
        )
        return True
