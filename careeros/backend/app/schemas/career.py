"""Pydantic schemas for Phase 2 career profile entities."""

from typing import Optional
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, field_validator


class _UUIDAwareResponse(BaseModel):
    """Coerces UUID attributes to strings for response serialization."""

    @field_validator("*", mode="before")
    @classmethod
    def _coerce_uuid(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v


class CareerProfileBase(BaseModel):
    """Base schema for career profile."""

    professional_title: Optional[str] = Field(None, max_length=255)
    summary: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    location: Optional[str] = Field(None, max_length=255)
    linkedin_url: Optional[HttpUrl] = Field(None, max_length=512)
    github_url: Optional[HttpUrl] = Field(None, max_length=512)
    portfolio_url: Optional[HttpUrl] = Field(None, max_length=512)
    years_of_experience: Optional[int] = None
    preferred_job_title: Optional[str] = Field(None, max_length=255)
    preferred_location: Optional[str] = Field(None, max_length=255)
    remote_preference: Optional[str] = Field(None, max_length=50)


class CareerProfileCreate(CareerProfileBase):
    """Schema for creating career profile."""

    pass


class CareerProfileUpdate(CareerProfileBase):
    """Schema for updating career profile."""

    pass


class CareerProfileResponse(_UUIDAwareResponse, CareerProfileBase):
    """Schema for career profile response."""

    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    completeness_score: Optional[int] = None


class EducationBase(BaseModel):
    """Base schema for education."""

    institution: str = Field(..., max_length=255)
    degree: Optional[str] = Field(None, max_length=100)
    field_of_study: Optional[str] = Field(None, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    grade: Optional[str] = Field(None, max_length=10)
    description: Optional[str] = None


class EducationCreate(EducationBase):
    """Schema for creating education."""

    pass


class EducationUpdate(BaseModel):
    """Schema for updating education."""

    institution: Optional[str] = Field(None, max_length=255)
    degree: Optional[str] = Field(None, max_length=100)
    field_of_study: Optional[str] = Field(None, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    grade: Optional[str] = Field(None, max_length=10)
    description: Optional[str] = None


class EducationResponse(_UUIDAwareResponse, EducationBase):
    """Schema for education response."""

    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime


class WorkExperienceBase(BaseModel):
    """Base schema for work experience."""

    company: str = Field(..., max_length=255)
    job_title: str = Field(..., max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    start_date: date
    end_date: Optional[date] = None
    is_current: bool = False
    description: Optional[str] = None


class WorkExperienceCreate(WorkExperienceBase):
    """Schema for creating work experience."""

    pass


class WorkExperienceUpdate(BaseModel):
    """Schema for updating work experience."""

    company: Optional[str] = Field(None, max_length=255)
    job_title: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None
    description: Optional[str] = None


class WorkExperienceResponse(_UUIDAwareResponse, WorkExperienceBase):
    """Schema for work experience response."""

    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime


class SkillBase(BaseModel):
    """Base schema for skill."""

    name: str = Field(..., max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    proficiency: Optional[str] = Field(None, max_length=50)
    years_of_experience: Optional[int] = None


class SkillCreate(SkillBase):
    """Schema for creating skill."""

    pass


class SkillUpdate(BaseModel):
    """Schema for updating skill."""

    name: Optional[str] = Field(None, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    proficiency: Optional[str] = Field(None, max_length=50)
    years_of_experience: Optional[int] = None


class SkillResponse(_UUIDAwareResponse, SkillBase):
    """Schema for skill response."""

    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime


class CertificationBase(BaseModel):
    """Base schema for certification."""

    name: str = Field(..., max_length=255)
    issuing_organization: Optional[str] = Field(None, max_length=255)
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    credential_id: Optional[str] = Field(None, max_length=255)
    credential_url: Optional[HttpUrl] = Field(None, max_length=512)
    description: Optional[str] = None


class CertificationCreate(CertificationBase):
    """Schema for creating certification."""

    pass


class CertificationUpdate(BaseModel):
    """Schema for updating certification."""

    name: Optional[str] = Field(None, max_length=255)
    issuing_organization: Optional[str] = Field(None, max_length=255)
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    credential_id: Optional[str] = Field(None, max_length=255)
    credential_url: Optional[HttpUrl] = Field(None, max_length=512)
    description: Optional[str] = None


class CertificationResponse(_UUIDAwareResponse, CertificationBase):
    """Schema for certification response."""

    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
