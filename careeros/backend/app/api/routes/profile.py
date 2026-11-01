"""Career profile API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.db.models.user import User
from app.schemas.career import (
    CareerProfileResponse,
    CareerProfileCreate,
    CareerProfileUpdate,
)
from app.services.career import CareerProfileService

router = APIRouter(prefix="/profile", tags=["career-profile"])


@router.get("", response_model=CareerProfileResponse)
def get_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CareerProfileResponse:
    """Get current user's career profile."""
    profile_data = CareerProfileService.get_profile_with_completeness(db, current_user.id)
    if not profile_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile_data


@router.post("", response_model=CareerProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(
    profile_data: CareerProfileCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CareerProfileResponse:
    """Create career profile for current user."""
    existing = CareerProfileService.get_profile(db, current_user.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Profile already exists",
        )
    return CareerProfileService.create_profile(db, current_user.id, profile_data)


@router.put("", response_model=CareerProfileResponse)
def update_profile(
    profile_data: CareerProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CareerProfileResponse:
    """Update current user's career profile."""
    updated_profile = CareerProfileService.update_profile(db, current_user.id, profile_data)
    if not updated_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return updated_profile
