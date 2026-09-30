"""Career document builder.

Converts Phase 2 career data (profile, education, experience, skills, certifications)
into a normalized list of plain-text career documents. Each document has a stable
identity (source_type + source_id) and is owned by exactly one user.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.certification import Certification
from app.db.models.education import Education
from app.db.models.skill import Skill
from app.db.models.work_experience import WorkExperience


@dataclass(frozen=True)
class CareerDocument:
    """A normalized career document ready for chunking and embedding."""

    source_type: str  # "profile" | "education" | "experience" | "skill" | "certification"
    source_id: str
    title: str
    content: str

    def stable_id(self) -> str:
        """A stable string identity for deduplication."""
        return f"{self.source_type}:{self.source_id}"


def _format_education(edu: Education) -> CareerDocument:
    parts: list[str] = [f"Education at {edu.institution}"]
    if edu.degree:
        parts.append(f"Degree: {edu.degree}")
    if edu.field_of_study:
        parts.append(f"Field of study: {edu.field_of_study}")
    if edu.start_date or edu.end_date:
        start = edu.start_date.isoformat() if edu.start_date else "unknown"
        end = edu.end_date.isoformat() if edu.end_date else "present"
        parts.append(f"Period: {start} to {end}")
    if edu.grade:
        parts.append(f"Grade: {edu.grade}")
    if edu.description:
        parts.append(f"Description: {edu.description}")
    return CareerDocument(
        source_type="education",
        source_id=str(edu.id),
        title=f"{edu.degree or 'Education'} at {edu.institution}" if edu.degree else f"Education at {edu.institution}",
        content=". ".join(parts),
    )


def _format_experience(we: WorkExperience) -> CareerDocument:
    parts: list[str] = [f"Worked as {we.job_title} at {we.company}"]
    if we.location:
        parts.append(f"Location: {we.location}")
    end = "present" if we.is_current else (we.end_date.isoformat() if we.end_date else "unknown")
    start = we.start_date.isoformat() if we.start_date else "unknown"
    parts.append(f"Period: {start} to {end}")
    if we.description:
        parts.append(f"Description: {we.description}")
    return CareerDocument(
        source_type="experience",
        source_id=str(we.id),
        title=f"{we.job_title} at {we.company}",
        content=". ".join(parts),
    )


def _format_skill(skill: Skill) -> CareerDocument:
    parts: list[str] = [f"Skill: {skill.name}"]
    if skill.category:
        parts.append(f"Category: {skill.category}")
    if skill.proficiency:
        parts.append(f"Proficiency: {skill.proficiency}")
    if skill.years_of_experience is not None:
        parts.append(f"Years of experience: {skill.years_of_experience}")
    return CareerDocument(
        source_type="skill",
        source_id=str(skill.id),
        title=skill.name,
        content=". ".join(parts),
    )


def _format_certification(cert: Certification) -> CareerDocument:
    parts: list[str] = [f"Certification: {cert.name}"]
    if cert.issuing_organization:
        parts.append(f"Issued by: {cert.issuing_organization}")
    if cert.issue_date:
        parts.append(f"Issue date: {cert.issue_date.isoformat()}")
    if cert.expiry_date:
        parts.append(f"Expiry date: {cert.expiry_date.isoformat()}")
    if cert.credential_id:
        parts.append(f"Credential ID: {cert.credential_id}")
    if cert.description:
        parts.append(f"Description: {cert.description}")
    return CareerDocument(
        source_type="certification",
        source_id=str(cert.id),
        title=cert.name,
        content=". ".join(parts),
    )


def _format_profile(profile) -> CareerDocument:
    """Format a CareerProfile into a document. Profile has no single 'title' row;
    we summarize its fields."""
    parts: list[str] = []
    if profile.professional_title:
        parts.append(f"Professional title: {profile.professional_title}")
    if profile.summary:
        parts.append(f"Summary: {profile.summary}")
    if profile.years_of_experience is not None:
        parts.append(f"Years of experience: {profile.years_of_experience}")
    if profile.preferred_job_title:
        parts.append(f"Preferred job title: {profile.preferred_job_title}")
    if profile.preferred_location:
        parts.append(f"Preferred location: {profile.preferred_location}")
    if profile.remote_preference:
        parts.append(f"Remote preference: {profile.remote_preference}")
    if profile.phone:
        parts.append(f"Phone: {profile.phone}")
    if profile.location:
        parts.append(f"Location: {profile.location}")
    if profile.linkedin_url:
        parts.append(f"LinkedIn: {profile.linkedin_url}")
    if profile.github_url:
        parts.append(f"GitHub: {profile.github_url}")
    if profile.portfolio_url:
        parts.append(f"Portfolio: {profile.portfolio_url}")

    if not parts:
        parts.append("Career profile exists but is empty.")

    title = profile.professional_title or "Career Profile"
    return CareerDocument(
        source_type="profile",
        source_id=str(profile.id),
        title=title,
        content=". ".join(parts),
    )


class CareerDocumentBuilder:
    """Build normalized career documents for a single user from the database."""

    def build(
        self,
        db: Session,
        user_id: UUID,
        profile=None,
        education: Iterable[Education] | None = None,
        experience: Iterable[WorkExperience] | None = None,
        skills: Iterable[Skill] | None = None,
        certifications: Iterable[Certification] | None = None,
    ) -> list[CareerDocument]:
        """Return all career documents for the given user.

        If a collection is None, it is queried from the database filtered by
        the given user_id. The caller is responsible for ensuring the data
        already belongs to that user; the builder does not perform ownership
        filtering on pre-loaded data.
        """
        docs: list[CareerDocument] = []

        if profile is not None:
            docs.append(_format_profile(profile))
        else:
            from app.db.models.career_profile import CareerProfile
            loaded_profile = (
                db.query(CareerProfile)
                .filter(CareerProfile.user_id == user_id)
                .first()
            )
            if loaded_profile is not None:
                docs.append(_format_profile(loaded_profile))

        for edu in (education if education is not None else db.query(Education).filter(Education.user_id == user_id).all()):
            docs.append(_format_education(edu))

        for we in (experience if experience is not None else db.query(WorkExperience).filter(WorkExperience.user_id == user_id).all()):
            docs.append(_format_experience(we))

        for skill in (skills if skills is not None else db.query(Skill).filter(Skill.user_id == user_id).all()):
            docs.append(_format_skill(skill))

        for cert in (certifications if certifications is not None else db.query(Certification).filter(Certification.user_id == user_id).all()):
            docs.append(_format_certification(cert))

        return docs
