"""Pydantic schemas for Phase 6 Resume Engine.

Structured resume management with versioning, import/parsing, ATS analysis, and tailoring.
"""

from __future__ import annotations

import json
from datetime import datetime
from enum import Enum as PyEnum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.jobs import JobSummary


class ResumeTypeResponse(str, PyEnum):
    """Resume type options for API responses."""
    BASE = "base"
    TAILORED = "tailored"
    IMPORTED = "imported"


class ResumeStatusResponse(str, PyEnum):
    """Resume status options for API responses."""
    DRAFT = "draft"
    READY = "ready"
    ARCHIVED = "archived"


class ResumeSectionBase(BaseModel):
    """Base schema for resume sections."""
    
    section_type: str = Field(..., max_length=50)  # summary, skills, experience, etc.
    section_title: Optional[str] = Field(None, max_length=255)
    content: str  # Section content in appropriate format (markdown, JSON, etc.)
    display_order: int = Field(default=0, ge=0)
    is_custom: bool = Field(default=False)


class ResumeSectionCreate(ResumeSectionBase):
    """Schema for creating resume sections."""
    pass


class ResumeSectionUpdate(BaseModel):
    """Schema for updating resume sections."""
    
    section_type: Optional[str] = Field(None, max_length=50)
    section_title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = None
    display_order: Optional[int] = Field(None, ge=0)
    is_custom: Optional[bool] = None


class ResumeSectionResponse(ResumeSectionBase):
    """Schema for resume section responses."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    resume_id: str
    created_at: datetime
    updated_at: datetime


class ResumeBase(BaseModel):
    """Base schema for resumes."""
    
    name: str = Field(..., max_length=255)
    resume_type: ResumeTypeResponse
    status: ResumeStatusResponse = Field(default=ResumeStatusResponse.DRAFT)
    target_job_id: Optional[str] = Field(None, description="Job ID for tailored resumes")
    parent_resume_id: Optional[str] = Field(None, description="Parent resume ID for versioned resumes")
    version_number: int = Field(default=1, ge=1)
    structured_data: Optional[Dict[str, Any]] = Field(None, description="Structured resume data as JSON")
    source_file_name: Optional[str] = Field(None, max_length=255)
    source_file_type: Optional[str] = Field(None, max_length=50)  # pdf, docx, txt
    import_metadata: Optional[Dict[str, Any]] = Field(None)


class ResumeCreate(ResumeBase):
    """Schema for creating resumes."""
    
    @field_validator('target_job_id')
    @classmethod
    def validate_target_job_for_tailored(cls, v, info):
        if info.data.get('resume_type') == ResumeTypeResponse.TAILORED and not v:
            raise ValueError('target_job_id is required for tailored resumes')
        return v
    
    @field_validator('parent_resume_id')
    @classmethod
    def validate_parent_for_versioned(cls, v, info):
        if info.data.get('version_number', 1) > 1 and not v:
            raise ValueError('parent_resume_id is required for versioned resumes (version > 1)')
        return v


class ResumeUpdate(BaseModel):
    """Schema for updating resumes."""
    
    name: Optional[str] = Field(None, max_length=255)
    status: Optional[ResumeStatusResponse] = None
    target_job_id: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    source_file_name: Optional[str] = Field(None, max_length=255)
    source_file_type: Optional[str] = Field(None, max_length=50)
    import_metadata: Optional[Dict[str, Any]] = None


class ResumeResponse(ResumeBase):
    """Schema for resume responses."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    version_number: int
    created_at: datetime
    updated_at: datetime
    
    # Computed flags from resume_type/status
    is_base_resume: bool = False
    is_tailored: bool = False
    is_imported: bool = False
    is_draft: bool = False
    is_ready: bool = False
    is_archived: bool = False
    
    # Relationships (eager loaded when needed)
    target_job: Optional[JobSummary] = None
    parent_resume: Optional['ResumeResponse'] = None
    versions: List['ResumeResponse'] = Field(default_factory=list)
    sections: List[ResumeSectionResponse] = Field(default_factory=list)


class ResumeSummary(BaseModel):
    """Lightweight resume representation for list views."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    name: str
    resume_type: ResumeTypeResponse
    status: ResumeStatusResponse
    target_job_id: Optional[str] = None
    version_number: int
    is_base_resume: bool
    is_tailored: bool
    is_imported: bool
    created_at: datetime
    updated_at: datetime


class ResumeImportResult(BaseModel):
    """Result of resume import/parsing operation."""
    
    success: bool
    resume_id: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    sections: List[Dict[str, Any]] = []
    errors: List[str] = []
    warnings: List[str] = []
    
    # Parsed content metadata
    detected_file_type: Optional[str] = None
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    skill_matches: List[str] = []  # Skills found that match user's Career Profile
    missing_sections: List[str] = []  # Standard resume sections that were missing


class ResumeTextImportRequest(BaseModel):
    """Request body for importing a resume from plain text."""
    resume_text: str = Field(..., max_length=50000, description="Plain text resume content to parse")


class ATSSectionScoreSchema(BaseModel):
    """Score for a specific section of the resume in ATS analysis."""
    
    section_type: str
    score: int  # 0-100
    matched_count: int
    total_count: int
    matched_items: List[str] = Field(default_factory=list)
    missing_items: List[str] = Field(default_factory=list)


class ATSAnalysisRequest(BaseModel):
    """Request for ATS analysis of a resume against a job."""
    
    resume_id: str
    job_id: str
    include_recommendations: bool = Field(default=True)


class ATSAnalysisResponse(BaseModel):
    """Response from ATS analysis."""
    
    model_config = ConfigDict(from_attributes=True)
    
    resume_id: str
    job_id: str
    overall_score: int = Field(..., ge=0, le=100)  # 0-100 score
    breakdown: Dict[str, int] = Field(...)  # e.g., {"keyword_coverage": 85, "skill_alignment": 78, ...}
    
    # Component scores
    keyword_coverage: ATSSectionScoreSchema
    skill_alignment: ATSSectionScoreSchema
    experience_alignment: ATSSectionScoreSchema
    education_alignment: ATSSectionScoreSchema
    certification_alignment: ATSSectionScoreSchema
    structure_score: ATSSectionScoreSchema
    relevance_score: ATSSectionScoreSchema
    
    # Detailed lists
    matched_keywords: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    matched_requirements: List[str] = Field(default_factory=list)
    missing_requirements: List[str] = Field(default_factory=list)
    
    # Quality signals
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    
    # Metadata
    analyzed_at: datetime
    total_keywords_matched: int = Field(default=0)
    total_keywords_required: int = Field(default=0)


class ResumeTailorRequest(BaseModel):
    """Request to tailor a resume for a specific job."""
    
    base_resume_id: str  # The resume to tailor (usually the base resume)
    target_job_id: str   # The job to tailor for
    name: str = Field(..., max_length=255)  # Name for the tailored resume
    include_ai_suggestions: bool = Field(default=True)  # Whether to use AI for wording improvements
    max_versions_to_keep: int = Field(default=10, ge=1)  # How many tailored versions to retain


class ResumeTailorResponse(BaseModel):
    """Response from resume tailoring operation."""
    
    tailored_resume_id: str
    base_resume_id: str
    target_job_id: str
    tailoring_changes: Dict[str, Any] = Field(...)  # What was changed from base to tailored
    ats_analysis: ATSAnalysisResponse  # ATS score of the tailored resume
    matched_requirements: List[str] = []
    missing_requirements: List[str] = []
    recommendations: List[str] = []
    created_at: datetime


class ResumeVersionResponse(BaseModel):
    """Response for resume version information."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    resume_id: str
    version_number: int
    name: str
    resume_type: ResumeTypeResponse
    status: ResumeStatusResponse
    target_job_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    ats_score: Optional[int] = None
    ats_analyzed_at: Optional[datetime] = None


class ResumeListResponse(BaseModel):
    """Paginated list of resumes."""
    
    items: List[ResumeResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


# Update forward references
ResumeResponse.model_rebuild()