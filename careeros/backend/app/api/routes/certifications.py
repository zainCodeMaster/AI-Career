"""Certifications API routes."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.db.models.user import User
from app.schemas.career import (
    CertificationResponse,
    CertificationCreate,
    CertificationUpdate,
)
from app.services.career import CertificationService

router = APIRouter(prefix="/certifications", tags=["certifications"])


@router.get("", response_model=list[CertificationResponse])
def list_certifications(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[CertificationResponse]:
    """Get all certifications for current user."""
    return CertificationService.get_user_certifications(db, current_user.id)


@router.post("", response_model=CertificationResponse, status_code=status.HTTP_201_CREATED)
def create_certification(
    certification_data: CertificationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CertificationResponse:
    """Create certification record."""
    return CertificationService.create_certification(db, current_user.id, certification_data)


@router.get("/{certification_id}", response_model=CertificationResponse)
def get_certification(
    certification_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CertificationResponse:
    """Get certification record by ID."""
    certification = CertificationService.get_certification(db, certification_id, current_user.id)
    if not certification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certification not found")
    return certification


@router.put("/{certification_id}", response_model=CertificationResponse)
def update_certification(
    certification_id: UUID,
    certification_data: CertificationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CertificationResponse:
    """Update certification record."""
    certification = CertificationService.update_certification(
        db, certification_id, current_user.id, certification_data
    )
    if not certification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certification not found")
    return certification


@router.delete("/{certification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_certification(
    certification_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete certification record."""
    deleted = CertificationService.delete_certification(db, certification_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certification not found")
