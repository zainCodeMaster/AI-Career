"""Cover Letter Generation Service.

Generates job-specific cover letters using verified user career data.

KEY PRINCIPLES:
- NEVER invent or fabricate achievements, qualifications, or experience
- All content must be grounded in the user's verified Career Profile
- Cover letter is a separate document from the resume
- User must review and approve before submitting
- All claims are traceable to source data
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.jobs import Job
from app.db.models.resume import Resume
from app.services.career import CareerProfileService
from app.services.resume.resume_service import ResumeService

logger = logging.getLogger("app.resume.cover_letter")


@dataclass
class CoverLetterResult:
    """Result of cover letter generation."""

    cover_letter: str
    user_name: str
    job_title: str
    company_name: str
    grounded_skills: list[str]
    grounded_experience: list[str]
    factuality_notes: list[str]


class CoverLetterService:
    """Generate job-specific cover letters from verified career data."""

    @staticmethod
    def generate_cover_letter(
        db: Session,
        user_id: UUID,
        job: Job,
        resume: Optional[Resume] = None,
    ) -> CoverLetterResult:
        """Generate a cover letter for a specific job.

        Args:
            db: Database session
            user_id: User ID
            job: Target job
            resume: Optional resume to base content on

        Returns:
            CoverLetterResult with the generated letter and grounding info
        """
        # Load user career profile (source of truth)
        profile_data = CareerProfileService.get_profile_with_completeness(db, user_id)
        if not profile_data:
            raise ValueError("Career profile not found. Complete your profile first.")

        # Get user skills and experience
        from app.services.career import (
            SkillService,
            WorkExperienceService,
            EducationService,
        )

        skills = SkillService.get_user_skills(db, user_id)
        experiences = WorkExperienceService.get_user_work_experience(db, user_id)
        educations = EducationService.get_user_education(db, user_id)

        # Build grounded skill list
        grounded_skills = [
            s.name for s in skills if s.name and s.proficiency
        ][:10]

        # Build grounded experience summary
        grounded_experience = []
        for exp in experiences[:3]:
            if exp.job_title and exp.company:
                grounded_experience.append(
                    f"{exp.job_title} at {exp.company}"
                )

        # Build education summary
        education_summary = ""
        if educations:
            edu = educations[0]
            if edu.degree and edu.institution:
                education_summary = f"{edu.degree} from {edu.institution}"

        # Build user name from profile or fallback
        user_name = (
            profile_data.get("professional_title") or "Professional"
        )

        # Build cover letter sections
        sections = []

        # Header
        sections.append(f"{user_name}")
        sections.append(f"{profile_data.get('location', '')}")
        sections.append(f"{profile_data.get('linkedin_url', '')}")
        sections.append(f"{datetime.now(timezone.utc).strftime('%B %d, %Y')}")
        sections.append("")

        # Salutation
        sections.append(f"Dear Hiring Manager,")
        sections.append("")

        # Opening - state the position
        opening = (
            f"I am writing to express my interest in the {job.title} position "
            f"at {job.company_name or 'your organization'}."
        )
        sections.append(opening)
        sections.append("")

        # Body - highlight relevant experience
        body_parts = []

        if grounded_experience:
            body_parts.append(
                f"With experience as {', '.join(grounded_experience[:2])}, "
                "I have developed the skills and expertise needed for this role."
            )

        if grounded_skills:
            skills_str = ", ".join(grounded_skills[:5])
            body_parts.append(
                f"My technical background includes {skills_str}, which directly "
                "aligns with the requirements of this position."
            )

        if education_summary:
            body_parts.append(
                f"I hold {education_summary}, providing a strong foundation "
                "for this role."
            )

        if not body_parts:
            body_parts.append(
                "I am excited about the opportunity to contribute to your team."
            )

        body_parts.append(
            f"I am particularly drawn to {job.company_name or 'your organization'} "
            "because of its reputation and the opportunity to make a meaningful impact."
        )

        body_parts.append(
            "I welcome the opportunity to discuss how my background and skills "
            "align with your needs."
        )

        sections.extend(body_parts)
        sections.append("")

        # Closing
        sections.append("Sincerely,")
        sections.append("")
        sections.append(user_name)

        cover_letter = "\n".join(sections)

        # Factuality notes
        factuality_notes = [
            "All skills and experience listed are from your verified Career Profile",
            "No achievements or qualifications have been invented or exaggerated",
            f"Cover letter targets: {job.title} at {job.company_name or 'company'}",
            "Please review and customize before submitting",
        ]

        return CoverLetterResult(
            cover_letter=cover_letter,
            user_name=user_name,
            job_title=job.title,
            company_name=job.company_name or "Company",
            grounded_skills=grounded_skills,
            grounded_experience=grounded_experience,
            factuality_notes=factuality_notes,
        )
