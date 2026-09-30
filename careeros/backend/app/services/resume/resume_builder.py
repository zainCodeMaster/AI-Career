"""Resume Builder service.

Builds structured resume data from the user's verified Career Profile.
This is the "base resume" that can then be tailored for specific jobs.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.career_profile import CareerProfile
from app.db.models.certification import Certification
from app.db.models.education import Education
from app.db.models.jobs import Job
from app.db.models.resume import Resume, ResumeSection
from app.db.models.skill import Skill
from app.db.models.work_experience import WorkExperience

logger = logging.getLogger("app.resume.builder")


class ResumeBuilder:
    """Build a structured resume from the user's verified Career Profile data."""

    @staticmethod
    def build_from_profile(
        db: Session,
        user_id: UUID | str,
    ) -> Dict[str, Any]:
        """Build structured resume data from the user's Career Profile.
        
        This method loads the user's verified career data and structures it
        into a resume format. It does NOT invent any data.
        """
        uid = UUID(str(user_id))

        # Load all career data
        profile = db.query(CareerProfile).filter(CareerProfile.user_id == uid).first()
        skills = db.query(Skill).filter(Skill.user_id == uid).all()
        experiences = db.query(WorkExperience).filter(WorkExperience.user_id == uid).all()
        educations = db.query(Education).filter(Education.user_id == uid).all()
        certifications = db.query(Certification).filter(Certification.user_id == uid).all()

        structured: Dict[str, Any] = {}

        # Summary / Professional Summary
        if profile and profile.summary:
            structured["summary"] = profile.summary.strip()
        elif profile and profile.professional_title:
            structured["summary"] = f"Professional {profile.professional_title}"
            if profile.years_of_experience:
                structured["summary"] += f" with {profile.years_of_experience}+ years of experience"
        else:
            structured["summary"] = ""

        # Contact info (reference, not duplicated)
        contact = {}
        if profile:
            if profile.phone:
                contact["phone"] = profile.phone
            if profile.location:
                contact["location"] = profile.location
            if profile.linkedin_url:
                contact["linkedin"] = str(profile.linkedin_url)
            if profile.github_url:
                contact["github"] = str(profile.github_url)
            if profile.portfolio_url:
                contact["portfolio"] = str(profile.portfolio_url)
        structured["contact"] = contact

        # Professional Title
        if profile and profile.professional_title:
            structured["professional_title"] = profile.professional_title.strip()

        # Target Role (from preferences)
        from app.db.models.jobs import UserJobPreferences
        prefs = db.query(UserJobPreferences).filter(UserJobPreferences.user_id == str(uid)).first()
        if prefs and prefs.target_roles:
            try:
                target_roles = json.loads(prefs.target_roles)
                structured["target_role"] = ", ".join(target_roles) if target_roles else None
            except (json.JSONDecodeError, TypeError):
                structured["target_role"] = None
        else:
            structured["target_role"] = None

        # Skills
        structured["skills"] = [
            {
                "name": s.name,
                "category": s.category or "technical",
                "proficiency": s.proficiency or "intermediate",
                "years_of_experience": s.years_of_experience,
            }
            for s in skills
            if s.name
        ]

        # Experience
        structured["experience"] = [
            {
                "company": e.company,
                "job_title": e.job_title,
                "location": e.location or None,
                "start_date": e.start_date.isoformat() if e.start_date else None,
                "end_date": e.end_date.isoformat() if e.end_date else None,
                "is_current": e.is_current,
                "description": e.description.strip() if e.description else None,
            }
            for e in experiences
        ]

        # Education
        structured["education"] = [
            {
                "institution": e.institution,
                "degree": e.degree or None,
                "field_of_study": e.field_of_study or None,
                "start_date": e.start_date.isoformat() if e.start_date else None,
                "end_date": e.end_date.isoformat() if e.end_date else None,
                "grade": e.grade or None,
                "description": e.description.strip() if e.description else None,
            }
            for e in educations
        ]

        # Certifications
        structured["certifications"] = [
            {
                "name": c.name,
                "issuing_organization": c.issuing_organization or None,
                "issue_date": c.issue_date.isoformat() if c.issue_date else None,
                "expiry_date": c.expiry_date.isoformat() if c.expiry_date else None,
                "credential_id": c.credential_id or None,
                "credential_url": str(c.credential_url) if c.credential_url else None,
                "description": c.description.strip() if c.description else None,
            }
            for c in certifications
        ]

        # Default empty sections
        structured["projects"] = []
        structured["achievements"] = []
        structured.setdefault("custom_sections", {})

        return structured

    @staticmethod
    def create_base_resume(
        db: Session,
        user_id: UUID | str,
        name: str = "My Resume",
    ) -> Resume:
        """Create a base resume from the user's Career Profile.
        
        Returns a Resume object (not yet committed to DB).
        """
        uid = UUID(str(user_id))
        structured_data = ResumeBuilder.build_from_profile(db, uid)

        resume = Resume(
            user_id=uid,
            name=name,
            resume_type="base",
            status="draft",
            version_number=1,
            structured_data=structured_data,
        )
        db.add(resume)
        db.flush()

        # Create sections from structured data
        section_order = ["summary", "skills", "experience", "education", "projects", "certifications"]
        for order, section_type in enumerate(section_order):
            content = structured_data.get(section_type)
            if content:
                if isinstance(content, (dict, list)):
                    content_json = json.dumps(content)
                else:
                    content_json = str(content)
                
                section = ResumeSection(
                    resume_id=resume.id,
                    section_type=section_type,
                    section_title=None,
                    content=content_json,
                    display_order=order,
                    is_custom=False,
                )
                db.add(section)

        db.flush()
        logger.info(
            "base_resume_created",
            extra={"user_id": str(uid), "resume_id": str(resume.id)},
        )
        return resume