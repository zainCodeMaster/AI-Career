"""Resume CRUD service.

Handles creation, retrieval, updating, and deletion of resumes with strict
user isolation. All operations are scoped to the authenticated user's UUID.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.resume import Resume, ResumeSection
from app.db.models.user import User
from app.schemas.resume import (
    ResumeCreate,
    ResumeUpdate,
)

logger = logging.getLogger("app.resume")


def _ensure_uuid(value: UUID | str) -> UUID:
    """Coerce a string or UUID to UUID."""
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


class ResumeService:
    """Core resume CRUD operations with strict user isolation."""

    @staticmethod
    def create(
        db: Session,
        user_id: UUID | str,
        resume_in: ResumeCreate,
    ) -> Resume:
        """Create a new resume for the user."""
        uid = _ensure_uuid(user_id)

        if resume_in.resume_type.value == "tailored" and not resume_in.target_job_id:
            raise ValueError("target_job_id is required for tailored resumes")

        # Validate target_job_id belongs to a real job if provided
        if resume_in.target_job_id:
            from app.db.models.jobs import Job

            job = db.get(Job, resume_in.target_job_id)
            if job is None:
                raise ValueError("Target job not found")

        # Validate parent_resume_id belongs to the same user if provided
        if resume_in.parent_resume_id:
            parent = db.get(Resume, resume_in.parent_resume_id)
            if parent is None:
                raise ValueError("Parent resume not found")
            if parent.user_id != uid:
                raise PermissionError("Parent resume does not belong to user")

        # Build structured data dict
        structured_data = resume_in.structured_data or {}
        if resume_in.resume_type.value == "imported" and resume_in.source_file_name:
            structured_data.setdefault("_import_source", resume_in.source_file_name)

        resume = Resume(
            user_id=uid,
            name=resume_in.name,
            resume_type=resume_in.resume_type,
            status=resume_in.status,
            target_job_id=resume_in.target_job_id,
            parent_resume_id=resume_in.parent_resume_id,
            version_number=resume_in.version_number,
            structured_data=structured_data,
            source_file_name=resume_in.source_file_name,
            source_file_type=resume_in.source_file_type,
            import_metadata=resume_in.import_metadata,
        )
        db.add(resume)
        db.flush()

        logger.info(
            "resume_created",
            extra={
                "user_id": str(uid),
                "resume_id": str(resume.id),
                "resume_type": resume.resume_type.value,
            },
        )
        return resume

    @staticmethod
    def get(
        db: Session,
        user_id: UUID | str,
        resume_id: UUID | str,
    ) -> Optional[Resume]:
        """Get a single resume by ID, ensuring user ownership."""
        uid = _ensure_uuid(user_id)
        rid = _ensure_uuid(resume_id)

        stmt = (
            select(Resume)
            .where(Resume.id == rid, Resume.user_id == uid)
            .options(selectinload(Resume.sections))
        )
        result = db.execute(stmt).scalar_one_or_none()
        return result

    @staticmethod
    def list(
        db: Session,
        user_id: UUID | str,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        resume_type: Optional[str] = None,
    ) -> Tuple[List[Resume], int]:
        """List resumes for a user with pagination and optional filters."""
        uid = _ensure_uuid(user_id)
        offset = (page - 1) * page_size

        stmt = (
            select(Resume)
            .where(Resume.user_id == uid)
            .options(selectinload(Resume.sections))
            .order_by(Resume.updated_at.desc())
        )

        if status:
            stmt = stmt.where(Resume.status == status)
        if resume_type:
            stmt = stmt.where(Resume.resume_type == resume_type)

        # Get total count
        count_stmt = select(Resume).where(Resume.user_id == uid)
        if status:
            count_stmt = count_stmt.where(Resume.status == status)
        if resume_type:
            count_stmt = count_stmt.where(Resume.resume_type == resume_type)
        total = db.execute(select(_raw_count(count_stmt))).scalar() or 0

        items = db.execute(stmt.offset(offset).limit(page_size)).scalars().all()
        return items, total

    @staticmethod
    def update(
        db: Session,
        user_id: UUID | str,
        resume_id: UUID | str,
        resume_in: ResumeUpdate,
    ) -> Optional[Resume]:
        """Update a resume, ensuring user ownership."""
        uid = _ensure_uuid(user_id)
        rid = _ensure_uuid(resume_id)

        resume = ResumeService.get(db, uid, rid)
        if resume is None:
            return None

        update_data = resume_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field in ("structured_data", "import_metadata"):
                if value is not None:
                    setattr(resume, field, value)
            elif field:
                setattr(resume, field, value)

        db.add(resume)
        db.flush()

        logger.info(
            "resume_updated",
            extra={
                "user_id": str(uid),
                "resume_id": str(rid),
            },
        )
        return resume

    @staticmethod
    def archive(
        db: Session,
        user_id: UUID | str,
        resume_id: UUID | str,
    ) -> bool:
        """Archive (soft-delete) a resume."""
        uid = _ensure_uuid(user_id)
        rid = _ensure_uuid(resume_id)

        resume = ResumeService.get(db, uid, rid)
        if resume is None:
            return False

        resume.status = "archived"
        db.add(resume)
        db.flush()

        logger.info(
            "resume_archived",
            extra={
                "user_id": str(uid),
                "resume_id": str(rid),
            },
        )
        return True

    @staticmethod
    def delete(
        db: Session,
        user_id: UUID | str,
        resume_id: UUID | str,
    ) -> bool:
        """Permanently delete a resume."""
        uid = _ensure_uuid(user_id)
        rid = _ensure_uuid(resume_id)

        resume = ResumeService.get(db, uid, rid)
        if resume is None:
            return False

        db.delete(resume)
        db.flush()

        logger.info(
            "resume_deleted",
            extra={
                "user_id": str(uid),
                "resume_id": str(rid),
            },
        )
        return True

    @staticmethod
    def get_versions(
        db: Session,
        user_id: UUID | str,
        resume_id: UUID | str,
    ) -> List[Resume]:
        """Get all versions of a resume (including the resume itself)."""
        uid = _ensure_uuid(user_id)
        rid = _ensure_uuid(resume_id)

        # First verify the resume belongs to the user
        resume = ResumeService.get(db, uid, rid)
        if resume is None:
            return []

        # Get all versions (children with this as parent, plus the resume itself)
        stmt = (
            select(Resume)
            .where(
                (Resume.parent_resume_id == rid) |
                (Resume.id == rid)
            )
            .where(Resume.user_id == uid)
            .order_by(Resume.version_number.asc())
            .options(selectinload(Resume.sections))
        )
        return db.execute(stmt).scalars().all()


def _raw_count(stmt):
    """Helper to get a raw count query from a select statement."""
    from sqlalchemy import func

    return stmt.with_only_columns(func.count()).order_by(None).subquery()
