"""Resume section management service.

Handles creation, updating, ordering, and deletion of resume sections.
"""

from __future__ import annotations

import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.db.models.resume import Resume, ResumeSection

logger = logging.getLogger("app.resume.sections")


class ResumeSectionService:
    """Manage individual sections of a resume."""

    @staticmethod
    def add_section(
        db: Session,
        user_id: UUID | str,
        resume_id: UUID | str,
        section_type: str,
        content: str,
        section_title: Optional[str] = None,
        display_order: int = 0,
        is_custom: bool = False,
    ) -> ResumeSection:
        """Add a new section to a resume."""
        uid = UUID(str(user_id))
        rid = UUID(str(resume_id))

        # Verify ownership
        resume = db.get(Resume, rid)
        if resume is None or resume.user_id != uid:
            raise PermissionError("Resume not found or not owned by user")

        # Shift existing sections to make room for the new one
        if display_order <= 0:
            display_order = _next_display_order(db, rid)

        db.execute(
            update(ResumeSection)
            .where(
                ResumeSection.resume_id == rid,
                ResumeSection.display_order >= display_order,
            )
            .values(display_order=ResumeSection.display_order + 1)
        )

        section = ResumeSection(
            resume_id=rid,
            section_type=section_type,
            section_title=section_title,
            content=content,
            display_order=display_order,
            is_custom=is_custom,
        )
        db.add(section)
        db.flush()

        logger.info(
            "section_added",
            extra={
                "user_id": str(uid),
                "resume_id": str(rid),
                "section_type": section_type,
            },
        )
        return section

    @staticmethod
    def update_section(
        db: Session,
        user_id: UUID | str,
        section_id: UUID | str,
        content: Optional[str] = None,
        section_title: Optional[str] = None,
        display_order: Optional[int] = None,
        is_custom: Optional[bool] = None,
    ) -> Optional[ResumeSection]:
        """Update an existing section."""
        uid = UUID(str(user_id))
        sid = UUID(str(section_id))

        section = db.get(ResumeSection, sid)
        if section is None:
            return None

        # Verify ownership through resume
        resume = db.get(Resume, section.resume_id)
        if resume is None or resume.user_id != uid:
            raise PermissionError("Section not found or not owned by user")

        if content is not None:
            section.content = content
        if section_title is not None:
            section.section_title = section_title
        if display_order is not None:
            section.display_order = display_order
        if is_custom is not None:
            section.is_custom = is_custom

        db.add(section)
        db.flush()
        return section

    @staticmethod
    def get_sections(
        db: Session,
        user_id: UUID | str,
        resume_id: UUID | str,
    ) -> List[ResumeSection]:
        """Get all sections for a resume, ordered by display_order."""
        uid = UUID(str(user_id))
        rid = UUID(str(resume_id))

        # Verify ownership
        resume = db.get(Resume, rid)
        if resume is None or resume.user_id != uid:
            raise PermissionError("Resume not found or not owned by user")

        stmt = (
            select(ResumeSection)
            .where(ResumeSection.resume_id == rid)
            .order_by(ResumeSection.display_order.asc())
        )
        return db.execute(stmt).scalars().all()

    @staticmethod
    def delete_section(
        db: Session,
        user_id: UUID | str,
        section_id: UUID | str,
    ) -> bool:
        """Delete a section and re-order remaining sections."""
        uid = UUID(str(user_id))
        sid = UUID(str(section_id))

        section = db.get(ResumeSection, sid)
        if section is None:
            return False

        # Verify ownership
        resume = db.get(Resume, section.resume_id)
        if resume is None or resume.user_id != uid:
            raise PermissionError("Section not found or not owned by user")

        old_order = section.display_order
        resume_id = section.resume_id

        db.delete(section)

        # Re-order remaining sections
        from sqlalchemy import update as sql_update

        db.execute(
            sql_update(ResumeSection)
            .where(
                ResumeSection.resume_id == resume_id,
                ResumeSection.display_order > old_order,
            )
            .values(display_order=ResumeSection.display_order - 1)
        )
        db.flush()
        return True

    @staticmethod
    def reorder_sections(
        db: Session,
        user_id: UUID | str,
        resume_id: UUID | str,
        section_order: List[str],
    ) -> List[ResumeSection]:
        """Reorder sections by providing their IDs in the desired order."""
        uid = UUID(str(user_id))
        rid = UUID(str(resume_id))

        # Verify ownership
        resume = db.get(Resume, rid)
        if resume is None or resume.user_id != uid:
            raise PermissionError("Resume not found or not owned by user")

        # Verify all section IDs belong to this resume
        for i, section_id_str in enumerate(section_order):
            section_id = UUID(section_id_str)
            section = db.get(ResumeSection, section_id)
            if section is None or section.resume_id != rid:
                raise ValueError(f"Invalid section ID: {section_id_str}")
            section.display_order = i
            db.add(section)

        db.flush()
        return ResumeSectionService.get_sections(db, uid, rid)


def _next_display_order(db: Session, resume_id: UUID) -> int:
    """Get the next display order value for a new section."""
    from sqlalchemy import func

    max_order = db.execute(
        select(func.max(ResumeSection.display_order))
        .where(ResumeSection.resume_id == resume_id)
    ).scalar() or 0
    return max_order + 1
