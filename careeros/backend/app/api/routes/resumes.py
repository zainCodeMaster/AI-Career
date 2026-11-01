"""Phase 6 Resume Engine API routes.

Endpoints for:
- Resume CRUD: create, list, retrieve, update, delete/archive
- Resume sections: manage individual sections
- Resume versions: list versions of a resume
- ATS analysis: analyze resume against a job
- Resume tailoring: create tailored version for a specific job
"""

import io
import json
import logging
from typing import Optional

from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.db.models.jobs import Job
from app.db.models.resume import Resume, ResumeSection, ResumeType, ResumeStatus
from app.db.models.user import User
from app.schemas.resume import (
    ATSAnalysisRequest,
    ATSAnalysisResponse,
    CoverLetterGenerateRequest,
    CoverLetterResponse,
    ResumeCreate,
    ResumeListResponse,
    ResumeResponse,
    ResumeSectionCreate,
    ResumeSectionResponse,
    ResumeSectionUpdate,
    ResumeSummary,
    ResumeTailorRequest,
    ResumeTailorResponse,
    ResumeTextImportRequest,
    ResumeUpdate,
    ResumeVersionResponse,
)
from app.services.audit import create_audit_log
from app.services.resume.ats_analyzer import ATSAnalyzer
from app.services.resume.job_analysis import JobRequirementAnalyzer
from app.services.resume.resume_service import ResumeService
from app.services.resume.resume_tailorer import ResumeTailorer
from app.services.resume.cover_letter import CoverLetterService

logger = logging.getLogger("app.resume.api")

router = APIRouter(prefix="/resumes", tags=["resumes"])


def _get_resume_or_404(
    db: Session, user_id: str, resume_id: str
) -> Resume:
    """Get a resume belonging to the user, or raise 404."""
    resume = ResumeService.get(db, user_id, resume_id)
    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )
    return resume


def _validate_pagination(
    page: int, page_size: int
) -> tuple[int, int]:
    """Validate and clamp pagination parameters."""
    page = max(1, page)
    page_size = max(1, min(100, page_size))
    return page, page_size


# ---------------------------------------------------------------------------
# Resume CRUD
# ---------------------------------------------------------------------------


@router.get("", response_model=ResumeListResponse)
def list_resumes(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    resume_type: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ResumeListResponse:
    """List resumes for the authenticated user with pagination."""
    page, page_size = _validate_pagination(page, page_size)

    items, total = ResumeService.list(
        db, current_user.id, page=page, page_size=page_size,
        status=status_filter, resume_type=resume_type,
    )

    has_next = page * page_size < total
    has_prev = page > 1

    responses = [_resume_to_response(db, r) for r in items]

    return ResumeListResponse(
        items=responses,
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next,
        has_prev=has_prev,
    )


@router.post("", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
def create_resume(
    resume_data: ResumeCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ResumeResponse:
    """Create a new resume."""
    try:
        resume = ResumeService.create(db, current_user.id, resume_data)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    create_audit_log(
        db,
        event_type="RESUME_CREATED",
        user_id=current_user.id,
        details={
            "resume_id": str(resume.id),
            "resume_type": resume.resume_type,
            "name": resume.name,
        },
    )

    return _resume_to_response(db, resume)


@router.get("/{resume_id}", response_model=ResumeResponse)
def get_resume(
    resume_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ResumeResponse:
    """Get a specific resume by ID."""
    resume = _get_resume_or_404(db, current_user.id, resume_id)
    return _resume_to_response(db, resume)


@router.get("/{resume_id}/export", response_class=Response)
def export_resume(
    resume_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Response:
    """Export an owned resume as a deterministic plain-text document."""
    resume = _get_resume_or_404(db, current_user.id, resume_id)
    lines = [resume.name, "=" * len(resume.name), ""]
    if resume.structured_data:
        lines.append(json.dumps(resume.structured_data, indent=2, ensure_ascii=True))
    for section in sorted(resume.sections, key=lambda item: item.display_order):
        lines.extend(
            [
                "",
                section.section_title or section.section_type.replace("_", " ").title(),
                "-" * 40,
                section.content,
            ]
        )
    content = "\n".join(lines).strip() + "\n"
    filename = f"{resume.name.strip() or 'resume'}.txt".replace("/", "_").replace("\\", "_")
    return Response(
        content=content,
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.put("/{resume_id}", response_model=ResumeResponse)
def update_resume(
    resume_id: str,
    resume_data: ResumeUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ResumeResponse:
    """Update a resume."""
    try:
        resume = ResumeService.update(db, current_user.id, resume_id, resume_data)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )

    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )

    create_audit_log(
        db,
        event_type="RESUME_UPDATED",
        user_id=current_user.id,
        details={"resume_id": str(resume_id)},
    )

    return _resume_to_response(db, resume)


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(
    resume_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Permanently delete a resume."""
    deleted = ResumeService.delete(db, current_user.id, resume_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )

    create_audit_log(
        db,
        event_type="RESUME_DELETED",
        user_id=current_user.id,
        details={"resume_id": str(resume_id)},
    )


# ---------------------------------------------------------------------------
# Resume Sections
# ---------------------------------------------------------------------------


@router.get("/{resume_id}/sections", response_model=list[ResumeSectionResponse])
def list_sections(
    resume_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[ResumeSectionResponse]:
    """List all sections of a resume."""
    _get_resume_or_404(db, current_user.id, resume_id)
    
    # Verify ownership again for the section service
    from app.services.resume.section_service import ResumeSectionService
    sections = ResumeSectionService.get_sections(db, current_user.id, resume_id)
    return [_section_to_response(s) for s in sections]


@router.post("/{resume_id}/sections", response_model=ResumeSectionResponse, status_code=status.HTTP_201_CREATED)
def create_section(
    resume_id: str,
    section_data: ResumeSectionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ResumeSectionResponse:
    """Add a new section to a resume."""
    from app.services.resume.section_service import ResumeSectionService
    try:
        section = ResumeSectionService.add_section(
            db, current_user.id, resume_id,
            section_type=section_data.section_type,
            content=section_data.content,
            section_title=section_data.section_title,
            display_order=section_data.display_order,
            is_custom=section_data.is_custom,
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )

    create_audit_log(
        db,
        event_type="RESUME_SECTION_ADDED",
        user_id=current_user.id,
        details={
            "resume_id": resume_id,
            "section_type": section_data.section_type,
        },
    )

    return _section_to_response(section)


@router.put("/sections/{section_id}", response_model=ResumeSectionResponse)
def update_section(
    section_id: str,
    section_data: ResumeSectionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ResumeSectionResponse:
    """Update a resume section."""
    from app.services.resume.section_service import ResumeSectionService
    try:
        section = ResumeSectionService.update_section(
            db, current_user.id, section_id,
            content=section_data.content,
            section_title=section_data.section_title,
            display_order=section_data.display_order,
            is_custom=section_data.is_custom,
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )

    if section is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found",
        )

    return _section_to_response(section)


@router.delete("/sections/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_section(
    section_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a resume section."""
    from app.services.resume.section_service import ResumeSectionService
    try:
        deleted = ResumeSectionService.delete_section(db, current_user.id, section_id)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found",
        )


# ---------------------------------------------------------------------------
# Resume Versions
# ---------------------------------------------------------------------------


@router.get("/{resume_id}/versions", response_model=list[ResumeVersionResponse])
def list_versions(
    resume_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[ResumeVersionResponse]:
    """List all versions of a resume."""
    _get_resume_or_404(db, current_user.id, resume_id)

    tailorer = ResumeTailorer()
    versions = tailorer.get_resume_versions(db, current_user.id, resume_id)
    return [_version_to_response(v) for v in versions]


# ---------------------------------------------------------------------------
# ATS Analysis
# ---------------------------------------------------------------------------


@router.post("/ats/analyze", response_model=ATSAnalysisResponse)
def analyze_resume_ats(
    analysis_request: ATSAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ATSAnalysisResponse:
    """Analyze a resume against a job for ATS compatibility.
    
    This performs a deterministic analysis — no LLM calls.
    """
    resume = _get_resume_or_404(db, current_user.id, analysis_request.resume_id)

    job = db.get(Job, analysis_request.job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    from app.services.resume.job_analysis import JobRequirementAnalyzer
    job_analysis = JobRequirementAnalyzer.analyze(job)

    analyzer = ATSAnalyzer()
    result = analyzer.analyze(db, resume, job, job_analysis)

    create_audit_log(
        db,
        event_type="ATS_ANALYSIS_EXECUTED",
        user_id=current_user.id,
        details={
            "resume_id": analysis_request.resume_id,
            "job_id": analysis_request.job_id,
            "score": result.overall_score,
        },
    )

    return _ats_result_to_response(result)


# ---------------------------------------------------------------------------
# Resume Tailoring
# ---------------------------------------------------------------------------


@router.post("/tailor", response_model=ResumeTailorResponse, status_code=status.HTTP_201_CREATED)
def tailor_resume(
    request: ResumeTailorRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ResumeTailorResponse:
    """Create a tailored version of a resume for a specific job."""
    tailorer = ResumeTailorer()
    try:
        result = tailorer.tailor_for_job(
            db, current_user.id,
            request.base_resume_id, request.target_job_id,
            name=request.name,
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    create_audit_log(
        db,
        event_type="RESUME_TAILORED",
        user_id=current_user.id,
        details={
            "base_resume_id": request.base_resume_id,
            "tailored_resume_id": str(result.tailored_resume.id),
            "job_id": request.target_job_id,
            "ats_score": result.ats_analysis.overall_score,
        },
    )

    return ResumeTailorResponse(
        tailored_resume_id=str(result.tailored_resume.id),
        base_resume_id=request.base_resume_id,
        target_job_id=request.target_job_id,
        tailoring_changes=result.tailoring_changes,
        ats_analysis=_ats_result_to_response(result.ats_analysis),
        matched_requirements=result.matched_requirements,
        missing_requirements=result.missing_requirements,
        recommendations=result.recommendations,
        created_at=result.tailored_resume.created_at,
    )


# ---------------------------------------------------------------------------
# Cover Letter Generation
# ---------------------------------------------------------------------------


@router.post("/cover-letter/generate", response_model=CoverLetterResponse)
def generate_cover_letter(
    request: CoverLetterGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CoverLetterResponse:
    """Generate a job-specific cover letter from verified career data.
    
    The cover letter is grounded in the user's Career Profile — no achievements
    or qualifications are invented. User should review before submitting.
    """
    # Verify the job exists
    job = db.get(Job, request.job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Optional resume reference
    resume = None
    if request.resume_id:
        resume = _get_resume_or_404(db, current_user.id, request.resume_id)

    result = CoverLetterService.generate_cover_letter(
        db, current_user.id, job, resume
    )

    create_audit_log(
        db,
        event_type="COVER_LETTER_GENERATED",
        user_id=current_user.id,
        details={
            "job_id": str(request.job_id),
            "resume_id": request.resume_id,
        },
    )

    return CoverLetterResponse(
        cover_letter=result.cover_letter,
        user_name=result.user_name,
        job_title=result.job_title,
        company_name=result.company_name,
        grounded_skills=result.grounded_skills,
        grounded_experience=result.grounded_experience,
        factuality_notes=result.factuality_notes,
        generated_at=datetime.now(timezone.utc),
    )


@router.get("/cover-letter/export")
def export_cover_letter(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Export a cover letter as plain text."""
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    resume = None  # No resume passed for export - regenerate
    result = CoverLetterService.generate_cover_letter(
        db, current_user.id, job, resume
    )

    filename = f"cover_letter_{job.title.replace(' ', '_').lower()}_{job.company_name or 'company'}.txt".replace("/", "_").replace("\\", "_")

    return Response(
        content=result.cover_letter,
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )




# ---------------------------------------------------------------------------
# Resume Import
# ---------------------------------------------------------------------------


@router.post("/{resume_id}/import/text", response_model=ResumeResponse)
def import_resume_from_text(
    resume_id: str,
    request: ResumeTextImportRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ResumeResponse:
    """Import a resume from plain text by parsing it into structured sections.
    
    This is a basic text parser that splits text into resume sections using
    common section headers. It does NOT use LLMs.
    """
    resume = _get_resume_or_404(db, current_user.id, resume_id)

    from app.services.resume.resume_parser import ResumeTextParser
    parser = ResumeTextParser()
    structured_data = parser.parse(request.resume_text)

    # Store as import metadata
    import_metadata = resume.import_metadata or {}
    import_metadata["import_method"] = "text"
    import_metadata["original_text_length"] = len(request.resume_text)
    import_metadata["parsed_sections"] = list(structured_data.keys())

    resume.structured_data = structured_data
    resume.import_metadata = import_metadata
    resume.source_file_type = "txt"
    db.add(resume)
    db.flush()

    create_audit_log(
        db,
        event_type="RESUME_IMPORTED",
        user_id=current_user.id,
        details={
            "resume_id": str(resume_id),
            "import_method": "text",
            "text_length": len(request.resume_text),
        },
    )

    return _resume_to_response(db, resume)


@router.post("/{resume_id}/import/file", response_model=ResumeResponse)
async def import_resume_file(
    resume_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ResumeResponse:
    """Import a resume from an uploaded file (PDF, DOCX, or TXT)."""
    resume = _get_resume_or_404(db, current_user.id, resume_id)

    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided",
        )

    file_ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    allowed_extensions = {"pdf", "docx", "txt"}
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '.{file_ext}' not supported. Allowed: {', '.join(allowed_extensions)}",
        )

    # Read file content
    content = await file.read()
    
    # Validate file size (max 10MB)
    max_size = 10 * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {max_size // (1024 * 1024)}MB",
        )

    # Check for path traversal
    import os
    safe_filename = os.path.basename(file.filename)
    if safe_filename != file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename: path traversal detected",
        )

    # Parse file content
    structured_data: dict = {}
    import_metadata: dict = {
        "import_method": "file",
        "original_filename": safe_filename,
        "file_size": len(content),
        "detected_file_type": file_ext,
    }

    if file_ext == "txt":
        try:
            text = content.decode("utf-8")
            from app.services.resume.resume_parser import ResumeTextParser
            parser = ResumeTextParser()
            structured_data = parser.parse(text)
            import_metadata["text_length"] = len(text)
            import_metadata["parsed_sections"] = list(structured_data.keys())
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not decode text file. Please ensure it's UTF-8 encoded.",
            )

    elif file_ext == "pdf":
        try:
            # Try to use pdfplumber if available, fall back to basic extraction
            import pdfplumber
            
            text_parts = []
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page in pdf.pages:
                    text_parts.append(page.extract_text() or "")
            text = "\n".join(text_parts)
            
            from app.services.resume.resume_parser import ResumeTextParser
            parser = ResumeTextParser()
            structured_data = parser.parse(text)
            import_metadata["text_length"] = len(text)
            import_metadata["page_count"] = len(pdf.pages)
            import_metadata["parsed_sections"] = list(structured_data.keys())
        except ImportError:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="PDF import requires the 'pdfplumber' package. Please install it or use TXT format.",
            )
        except Exception as e:
            logger.warning(f"PDF parsing failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not parse PDF file: {str(e)}",
            )

    elif file_ext == "docx":
        try:
            from docx import Document as DocxDocument
            
            doc = DocxDocument(io.BytesIO(content))
            text = "\n".join(para.text for para in doc.paragraphs if para.text.strip())
            
            from app.services.resume.resume_parser import ResumeTextParser
            parser = ResumeTextParser()
            structured_data = parser.parse(text)
            import_metadata["text_length"] = len(text)
            import_metadata["parsed_sections"] = list(structured_data.keys())
        except ImportError:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="DOCX import requires the 'python-docx' package. Please install it or use TXT format.",
            )
        except Exception as e:
            logger.warning(f"DOCX parsing failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not parse DOCX file: {str(e)}",
            )

    # Store parsed data
    if structured_data or import_metadata["import_method"] == "file":
        resume.structured_data = structured_data if structured_data else (resume.structured_data or {})
        resume.import_metadata = (resume.import_metadata or {}) | import_metadata
        resume.source_file_name = safe_filename
        resume.source_file_type = file_ext
        resume.resume_type = "imported" if not resume.structured_data else resume.resume_type
        db.add(resume)
        db.flush()

    create_audit_log(
        db,
        event_type="RESUME_IMPORTED",
        user_id=current_user.id,
        details={
            "resume_id": str(resume_id),
            "import_method": "file",
            "file_type": file_ext,
            "file_size": len(content),
        },
    )

    return _resume_to_response(db, resume)


# ---------------------------------------------------------------------------
# Build resume from profile
# ---------------------------------------------------------------------------


@router.post("/build-from-profile", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
def build_resume_from_profile(
    name: str = Query(default="My Resume", max_length=255),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ResumeResponse:
    """Create a base resume from the user's verified Career Profile data."""
    from app.services.resume.resume_builder import ResumeBuilder

    resume = ResumeBuilder.create_base_resume(db, current_user.id, name=name)

    create_audit_log(
        db,
        event_type="RESUME_BUILT_FROM_PROFILE",
        user_id=current_user.id,
        details={
            "resume_id": str(resume_id := resume.id),
            "name": name,
        },
    )

    db.commit()
    return _resume_to_response(db, resume)


# ---------------------------------------------------------------------------
# Response helpers
# ---------------------------------------------------------------------------


def _resume_to_response(db: Session, resume: Resume) -> ResumeResponse:
    """Convert a Resume model to the response schema."""
    from app.schemas.resume import ResumeSectionResponse

    sections = [
        ResumeSectionResponse.model_validate(s)
        for s in resume.sections
    ]

    # Compute convenience flags
    is_base_resume = resume.resume_type.value == "base"
    is_tailored = resume.resume_type.value == "tailored"
    is_imported = resume.resume_type.value == "imported"
    is_draft = resume.status.value == "draft"
    is_ready = resume.status.value == "ready"
    is_archived = resume.status.value == "archived"

    # Handle target_job if present
    target_job = None
    if resume.target_job_id:
        job = db.get(Job, resume.target_job_id)
        if job:
            target_job = JobSummary.model_validate(job)

    # Handle parent_resume if present
    parent_resume = None
    if resume.parent_resume_id:
        parent = db.get(Resume, resume.parent_resume_id)
        if parent and parent.user_id == resume.user_id:
            parent_resume = ResumeResponse.model_validate(_resume_mini(parent, db))

    return ResumeResponse(
        id=str(resume.id),
        user_id=str(resume.user_id),
        name=resume.name,
        resume_type=ResumeTypeResponse(resume.resume_type.value),
        status=ResumeStatusResponse(resume.status.value),
        target_job_id=str(resume.target_job_id) if resume.target_job_id else None,
        parent_resume_id=str(resume.parent_resume_id) if resume.parent_resume_id else None,
        version_number=resume.version_number,
        structured_data=resume.structured_data,
        source_file_name=resume.source_file_name,
        source_file_type=resume.source_file_type,
        import_metadata=resume.import_metadata,
        ats_score=resume.ats_score,
        ats_breakdown=resume.ats_breakdown,
        ats_analyzed_at=resume.ats_analyzed_at,
        ats_analyzed_for_job_id=str(resume.ats_analyzed_for_job_id) if resume.ats_analyzed_for_job_id else None,
        created_at=resume.created_at,
        updated_at=resume.updated_at,
        is_base_resume=is_base_resume,
        is_tailored=is_tailored,
        is_imported=is_imported,
        is_draft=is_draft,
        is_ready=is_ready,
        is_archived=is_archived,
        target_job=target_job,
        parent_resume=parent_resume,
        versions=[],  # Filled separately if needed
        sections=sections,
    )


def _resume_mini(resume: Resume, db: Session) -> ResumeResponse:
    """Create a minimal ResumeResponse for parent_resume."""
    return ResumeResponse(
        id=str(resume.id),
        user_id=str(resume.user_id),
        name=resume.name,
        resume_type=ResumeTypeResponse(resume.resume_type.value),
        status=ResumeStatusResponse(resume.status.value),
        target_job_id=str(resume.target_job_id) if resume.target_job_id else None,
        parent_resume_id=str(resume.parent_resume_id) if resume.parent_resume_id else None,
        version_number=resume.version_number,
        structured_data=resume.structured_data,
        source_file_name=resume.source_file_name,
        source_file_type=resume.source_file_type,
        import_metadata=resume.import_metadata,
        ats_score=resume.ats_score,
        ats_breakdown=resume.ats_breakdown,
        ats_analyzed_at=resume.ats_analyzed_at,
        ats_analyzed_for_job_id=str(resume.ats_analyzed_for_job_id) if resume.ats_analyzed_for_job_id else None,
        created_at=resume.created_at,
        updated_at=resume.updated_at,
        is_base_resume=resume.resume_type.value == "base",
        is_tailored=resume.resume_type.value == "tailored",
        is_imported=resume.resume_type.value == "imported",
        is_draft=resume.status.value == "draft",
        is_ready=resume.status.value == "ready",
        is_archived=resume.status.value == "archived",
        sections=[],
        versions=[],
    )


def _section_to_response(section: ResumeSection) -> ResumeSectionResponse:
    """Convert a ResumeSection model to the response schema."""
    from app.schemas.resume import ResumeSectionResponse
    
    return ResumeSectionResponse(
        id=str(section.id),
        resume_id=str(section.resume_id),
        section_type=section.section_type,
        section_title=section.section_title,
        content=section.content,
        display_order=section.display_order,
        is_custom=section.is_custom,
        created_at=section.created_at,
        updated_at=section.updated_at,
    )


def _version_to_response(resume: Resume) -> ResumeVersionResponse:
    """Convert a Resume model to a version response."""
    return ResumeVersionResponse(
        id=str(resume.id),
        resume_id=str(resume.parent_resume_id or resume.id),
        version_number=resume.version_number,
        name=resume.name,
        resume_type=ResumeTypeResponse(resume.resume_type.value),
        status=ResumeStatusResponse(resume.status.value),
        target_job_id=str(resume.target_job_id) if resume.target_job_id else None,
        created_at=resume.created_at,
        updated_at=resume.updated_at,
        ats_score=resume.ats_score,
        ats_analyzed_at=resume.ats_analyzed_at,
    )


def _ats_result_to_response(result) -> ATSAnalysisResponse:
    """Convert ATSAnalysisResult to ATSAnalysisResponse."""
    from app.schemas.resume import ATSSectionScoreSchema
    
    def _section_to_schema(s):
        return ATSSectionScoreSchema(
            section_type=s.section_type,
            score=s.score,
            matched_count=s.matched_count,
            total_count=s.total_count,
            matched_items=s.matched_items,
            missing_items=s.missing_items,
        )
    
    return ATSAnalysisResponse(
        resume_id=result.resume_id,
        job_id=result.job_id,
        overall_score=result.overall_score,
        keyword_coverage=_section_to_schema(result.keyword_coverage),
        skill_alignment=_section_to_schema(result.skill_alignment),
        experience_alignment=_section_to_schema(result.experience_alignment),
        education_alignment=_section_to_schema(result.education_alignment),
        certification_alignment=_section_to_schema(result.certification_alignment),
        structure_score=_section_to_schema(result.structure_score),
        relevance_score=_section_to_schema(result.relevance_score),
        breakdown=result.breakdown,
        matched_keywords=result.matched_keywords,
        missing_keywords=result.missing_keywords,
        matched_skills=result.matched_skills,
        missing_skills=result.missing_skills,
        matched_requirements=result.matched_requirements,
        missing_requirements=result.missing_requirements,
        strengths=result.strengths,
        weaknesses=result.weaknesses,
        recommendations=result.recommendations,
        analyzed_at=result.analyzed_at,
        total_keywords_matched=result.total_keywords_matched,
        total_keywords_required=result.total_keywords_required,
    )


# Import here to avoid circular imports
from app.schemas.jobs import JobSummary
from app.schemas.resume import (
    ATSSectionScoreSchema,
    ResumeTypeResponse,
    ResumeStatusResponse,
)