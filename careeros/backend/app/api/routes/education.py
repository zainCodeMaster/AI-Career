"""Education API routes."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import get_current_active_user
from app.db.models.user import User
from app.schemas.career import (
    EducationResponse,
    EducationCreate,
    EducationUpdate,
)
from app.services.career import EducationService

router = APIRouter(prefix="/education", tags=["education"])


@router.get("", response_model=list[EducationResponse])
def list_education(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[EducationResponse]:
    """Get all education records for current user."""
    return EducationService.get_user_education(db, current_user.id)


@router.post("", response_model=EducationResponse, status_code=status.HTTP_201_CREATED)
def create_education(
    education_data: EducationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> EducationResponse:
    """Create education record."""
    return EducationService.create_education(db, current_user.id, education_data)


@router.get("/{education_id}", response_model=EducationResponse)
def get_education(
    education_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> EducationResponse:
    """Get education record by ID."""
    education = EducationService.get_education(db, education_id, current_user.id)
    if not education:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Education record not found")
    return education


@router.put("/{education_id}", response_model=EducationResponse)
def update_education(
    education_id: UUID,
    education_data: EducationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> EducationResponse:
    """Update education record."""
    education = EducationService.update_education(db, education_id, current_user.id, education_data)
    if not education:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Education record not found")
    return education


@router.delete("/{education_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_education(
    education_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete education record."""
    deleted = EducationService.delete_education(db, education_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Education record not found")
