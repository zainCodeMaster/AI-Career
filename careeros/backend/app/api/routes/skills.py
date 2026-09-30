"""Skills API routes."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.db.models.user import User
from app.schemas.career import (
    SkillResponse,
    SkillCreate,
    SkillUpdate,
)
from app.services.career import SkillService

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("", response_model=list[SkillResponse])
def list_skills(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[SkillResponse]:
    """Get all skills for current user."""
    return SkillService.get_user_skills(db, current_user.id)


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
def create_skill(
    skill_data: SkillCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SkillResponse:
    """Create skill record."""
    return SkillService.create_skill(db, current_user.id, skill_data)


@router.get("/{skill_id}", response_model=SkillResponse)
def get_skill(
    skill_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SkillResponse:
    """Get skill record by ID."""
    skill = SkillService.get_skill(db, skill_id, current_user.id)
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    return skill


@router.put("/{skill_id}", response_model=SkillResponse)
def update_skill(
    skill_id: UUID,
    skill_data: SkillUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SkillResponse:
    """Update skill record."""
    skill = SkillService.update_skill(db, skill_id, current_user.id, skill_data)
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    return skill


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_skill(
    skill_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete skill record."""
    deleted = SkillService.delete_skill(db, skill_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
