"""Work Experience API routes."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import get_current_active_user
from app.db.models.user import User
from app.schemas.career import (
    WorkExperienceResponse,
    WorkExperienceCreate,
    WorkExperienceUpdate,
)
from app.services.career import WorkExperienceService

router = APIRouter(prefix="/experience", tags=["work-experience"])


@router.get("", response_model=list[WorkExperienceResponse])
def list_work_experience(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[WorkExperienceResponse]:
    """Get all work experience records for current user."""
    return WorkExperienceService.get_user_work_experience(db, current_user.id)


@router.post("", response_model=WorkExperienceResponse, status_code=status.HTTP_201_CREATED)
def create_work_experience(
    experience_data: WorkExperienceCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> WorkExperienceResponse:
    """Create work experience record."""
    return WorkExperienceService.create_work_experience(db, current_user.id, experience_data)


@router.get("/{experience_id}", response_model=WorkExperienceResponse)
def get_work_experience(
    experience_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> WorkExperienceResponse:
    """Get work experience record by ID."""
    experience = WorkExperienceService.get_work_experience(db, experience_id, current_user.id)
    if not experience:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work experience record not found")
    return experience


@router.put("/{experience_id}", response_model=WorkExperienceResponse)
def update_work_experience(
    experience_id: UUID,
    experience_data: WorkExperienceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> WorkExperienceResponse:
    """Update work experience record."""
    experience = WorkExperienceService.update_work_experience(
        db, experience_id, current_user.id, experience_data
    )
    if not experience:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work experience record not found")
    return experience


@router.delete("/{experience_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_work_experience(
    experience_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete work experience record."""
    deleted = WorkExperienceService.delete_work_experience(db, experience_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work experience record not found")
