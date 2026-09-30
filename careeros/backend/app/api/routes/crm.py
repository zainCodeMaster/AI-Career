"""Phase 7 Career CRM API routes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.db.models.crm import (
    Application,
    ApplicationActivity,
    ApplicationContact,
    ApplicationDocument,
    Company,
    Contact,
    FollowUp,
    Interview,
    Offer,
    Rejection,
    Recommendation,
    UserCompanyLink,
)
from app.db.models.resume import Resume
from app.db.models.crm import ActivityEventType, ActorType, ApplicationStatus, FollowUpStatus
from app.schemas.crm import (
    ActivityFeedResponse,
    AllowedTransitionResponse,
    ApplicationContactResponse,
    ApplicationCreate,
    ApplicationDocumentCreate,
    ApplicationDocumentResponse,
    ApplicationDocumentUpdate,
    ApplicationListResponse,
    ApplicationResponse,
    ApplicationStatsResponse,
    ApplicationTransitionRequest,
    ApplicationTransitionResponse,
    ApplicationUpdate,
    CompanyCreate,
    CompanyResponse,
    CompanyUpdate,
    ContactCreate,
    ContactResponse,
    ContactUpdate,
    FunnelResponse,
    FunnelStageResponse,
    FollowUpCreate,
    FollowUpResponse,
    FollowUpUpdate,
    InterviewCreate,
    InterviewResponse,
    InterviewUpdate,
    OfferCreate,
    OfferResponse,
    OfferUpdate,
    PipelineResponse,
    PipelineStageResponse,
    RecommendationCreate,
    RecommendationResponse,
    RejectionCreate,
    RejectionResponse,
    StateMachineInfoResponse,
    StateTransitionResponse,
    UserCompanyLinkCreate,
    UserCompanyLinkResponse,
    UserCompanyLinkUpdate,
)
from app.services.crm.application_service import ApplicationService
from app.services.crm.company_service import CompanyService
from app.services.crm.dashboard import DashboardService
from app.services.crm.followup_service import FollowUpService
from app.services.crm.interview_service import InterviewService
from app.services.crm.offer_service import OfferService, RejectionService
from app.services.crm.recommendations import RecommendationService
from app.services.crm.state_machine import ApplicationStateMachine
from app.services.crm.timeline_service import TimelineService

router = APIRouter(tags=["crm"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_uuid(value: str) -> UUID:
    try:
        return UUID(value)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid id format")


def _require_owned_record(
    db: Session,
    model: type,
    record_id: UUID,
    user_id: UUID,
    detail: str,
) -> None:
    record = db.get(model, record_id)
    if record is None or record.user_id != user_id:
        raise HTTPException(status_code=404, detail=detail)


def _require_owned_contacts(
    db: Session,
    contact_ids: Optional[List[UUID]],
    user_id: UUID,
) -> None:
    if not contact_ids:
        return
    contacts = (
        db.query(Contact.id)
        .filter(Contact.id.in_(contact_ids), Contact.user_id == user_id)
        .all()
    )
    if len(contacts) != len(set(contact_ids)):
        raise HTTPException(status_code=404, detail="Contact not found")


def _validate_application_references(
    db: Session,
    resume_version_id: Optional[UUID],
    cover_letter_document_id: Optional[UUID],
    primary_contact_id: Optional[UUID],
    user_id: UUID,
) -> None:
    if resume_version_id is not None:
        _require_owned_record(
            db,
            Resume,
            resume_version_id,
            user_id,
            "Resume not found",
        )
    if cover_letter_document_id is not None:
        _require_owned_record(
            db,
            ApplicationDocument,
            cover_letter_document_id,
            user_id,
            "Document not found",
        )
    if primary_contact_id is not None:
        _require_owned_record(
            db,
            Contact,
            primary_contact_id,
            user_id,
            "Contact not found",
        )


def _require_linked_company(
    db: Session,
    company_id: UUID,
    user_id: UUID,
) -> Company:
    company = CompanyService.get(db, company_id)
    if company is None or CompanyService.get_user_link(db, user_id, company.id) is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


def _ensure_company_has_no_other_users(
    db: Session,
    company_ids: List[UUID],
    user_id: UUID,
) -> None:
    has_other_user = db.query(UserCompanyLink.id).filter(
        UserCompanyLink.company_id.in_(company_ids),
        UserCompanyLink.user_id != user_id,
    ).first()
    if has_other_user is None:
        has_other_user = db.query(Application.id).filter(
            Application.company_id.in_(company_ids),
            Application.user_id != user_id,
        ).first()
    if has_other_user is None:
        has_other_user = db.query(Contact.id).filter(
            Contact.company_id.in_(company_ids),
            Contact.user_id != user_id,
        ).first()
    if has_other_user is not None:
        raise HTTPException(
            status_code=409,
            detail="Company is used by another user",
        )


# ---------------------------------------------------------------------------
# State machine helpers
# ---------------------------------------------------------------------------


@router.get("/applications/state-machine", response_model=StateMachineInfoResponse)
def get_state_machine_info(
    status: str = Query(..., description="Current application status"),
    _current_user=Depends(get_current_active_user),
) -> StateMachineInfoResponse:
    try:
        current = ApplicationStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status")
    info = ApplicationStateMachine.get_state_machine_info(current)
    return StateMachineInfoResponse(
        current_status=info.current_status,
        allowed_transitions=[
            StateTransitionResponse(
                from_status=info.current_status,
                to_status=t.to_status,
                allowed=t.allowed,
                reason_required=t.reason_required,
                message=t.message,
            )
            for t in info.allowed_transitions
        ],
        is_terminal=info.is_terminal,
        can_reopen=info.can_reopen,
    )


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------


@router.get("/applications", response_model=ApplicationListResponse)
def list_applications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: Optional[List[str]] = Query(default=None),
    company_id: Optional[UUID] = Query(default=None),
    priority: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None, max_length=200),
    sort_by: str = Query(default="created_at"),
    sort_dir: str = Query(default="desc"),
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ApplicationListResponse:
    items, total = ApplicationService.list(
        db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        status=status,
        company_id=company_id,
        priority=priority,
        source=source,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    return ApplicationListResponse(
        items=[ApplicationResponse.model_validate(app) for app in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/applications", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(
    payload: ApplicationCreate,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ApplicationResponse:
    _validate_application_references(
        db,
        payload.resume_version_id,
        payload.cover_letter_document_id,
        payload.primary_contact_id,
        current_user.id,
    )
    app = ApplicationService.create(
        db,
        user_id=current_user.id,
        name=payload.name,
        job_id=payload.job_id,
        company_id=payload.company_id,
        job_title_snapshot=payload.job_title_snapshot,
        resume_version_id=payload.resume_version_id,
        cover_letter_document_id=payload.cover_letter_document_id,
        primary_contact_id=payload.primary_contact_id,
        priority=payload.priority.value,
        source=payload.source.value,
        application_url=payload.application_url,
        external_application_id=payload.external_application_id,
        notes=payload.notes,
        deadline_at=payload.deadline_at,
    )
    db.flush()
    return ApplicationResponse.model_validate(app)


@router.get("/applications/{application_id}", response_model=ApplicationResponse)
def get_application(
    application_id: str,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ApplicationResponse:
    app = ApplicationService.get(db, _parse_uuid(application_id), current_user.id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return ApplicationResponse.model_validate(app)


@router.patch("/applications/{application_id}", response_model=ApplicationResponse)
def update_application(
    application_id: str,
    payload: ApplicationUpdate,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ApplicationResponse:
    app = ApplicationService.get(db, _parse_uuid(application_id), current_user.id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    data = payload.model_dump(exclude_unset=True)
    if "status" in data:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_STATUS_UPDATE",
                "message": "Direct status modification via PATCH is not allowed. Use POST /applications/{id}/transitions to change status through the state machine.",
            },
        )
    _validate_application_references(
        db,
        data.get("resume_version_id"),
        data.get("cover_letter_document_id"),
        data.get("primary_contact_id"),
        current_user.id,
    )
    app = ApplicationService.update(db, app, **data)
    return ApplicationResponse.model_validate(app)


@router.delete("/applications/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(
    application_id: str,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    app = ApplicationService.get(db, _parse_uuid(application_id), current_user.id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    ApplicationService.delete(db, app)
    return None


@router.post(
    "/applications/{application_id}/transitions",
    response_model=ApplicationTransitionResponse,
)
def transition_application(
    application_id: str,
    payload: ApplicationTransitionRequest,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ApplicationTransitionResponse:
    app = ApplicationService.get(db, _parse_uuid(application_id), current_user.id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    from_status = app.status
    app, error = ApplicationService.transition(
        db,
        application=app,
        to_status=payload.to_status.value,
        user_id=current_user.id,
        reason=payload.reason,
        metadata=payload.metadata,
    )
    if error:
        raise HTTPException(status_code=409, detail={"code": "INVALID_TRANSITION", "message": error})
    db.flush()
    return ApplicationTransitionResponse(
        application_id=app.id,
        from_status=from_status.value,
        to_status=app.status.value,
        transitioned_at=datetime.now(timezone.utc),
        message=None,
    )


@router.get("/applications/{application_id}/timeline", response_model=ActivityFeedResponse)
def get_application_timeline(
    application_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ActivityFeedResponse:
    app = ApplicationService.get(db, _parse_uuid(application_id), current_user.id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    items, total = ApplicationService.get_activity_timeline(
        db, current_user.id, app.id, page=page, page_size=page_size
    )
    return ActivityFeedResponse(items=items, total=total, page=page, page_size=page_size)


@router.post(
    "/applications/{application_id}/documents",
    response_model=ApplicationDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_application_document(
    application_id: str,
    payload: ApplicationDocumentCreate,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ApplicationDocumentResponse:
    app = ApplicationService.get(db, _parse_uuid(application_id), current_user.id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    doc = ApplicationDocument(
        application_id=app.id,
        user_id=current_user.id,
        document_type=payload.document_type,
        file_url=payload.file_url,
        file_name=payload.file_name,
        file_size=payload.file_size,
        mime_type=payload.mime_type,
        document_metadata=payload.document_metadata,
    )
    db.add(doc)
    db.flush()
    event_type = (
        ActivityEventType.COVER_LETTER_ATTACHED
        if payload.document_type == "cover_letter"
        else ActivityEventType.RESUME_ATTACHED
    )
    TimelineService.add_event(
        db,
        application_id=app.id,
        user_id=current_user.id,
        event_type=event_type,
        title=f"Document attached: {payload.document_type}",
        actor_type=ActorType.MANUAL,
        related_entity_type="document",
        related_entity_id=doc.id,
    )
    db.flush()
    return ApplicationDocumentResponse.model_validate(doc)


@router.delete(
    "/applications/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_application_document(
    document_id: str,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    doc = db.query(ApplicationDocument).filter(
        ApplicationDocument.id == _parse_uuid(document_id),
        ApplicationDocument.user_id == current_user.id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.flush()
    return None


@router.post(
    "/applications/{application_id}/contacts",
    response_model=ApplicationContactResponse,
    status_code=status.HTTP_201_CREATED,
)
def link_contact_to_application(
    application_id: str,
    contact_id: UUID = Query(...),
    role: str = Query(default="other", max_length=32),
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ApplicationContactResponse:
    app = ApplicationService.get(db, _parse_uuid(application_id), current_user.id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    contact = db.query(Contact).filter(
        Contact.id == contact_id, Contact.user_id == current_user.id
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    link = ApplicationContact(
        application_id=app.id,
        contact_id=contact.id,
        role=role,
    )
    db.add(link)
    db.flush()
    TimelineService.add_event(
        db,
        application_id=app.id,
        user_id=current_user.id,
        event_type=ActivityEventType.CONTACT_ADDED,
        title=f"Contact added: {contact.name}",
        actor_type=ActorType.MANUAL,
        related_entity_type="contact",
        related_entity_id=contact.id,
    )
    db.flush()
    return ApplicationContactResponse(
        id=link.id,
        application_id=app.id,
        contact=ContactResponse.model_validate(contact),
        role=link.role,
        created_at=link.created_at,
    )


@router.delete(
    "/applications/{application_id}/contacts/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unlink_contact_from_application(
    application_id: str,
    contact_id: str,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    app = ApplicationService.get(db, _parse_uuid(application_id), current_user.id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    contact = db.query(Contact).filter(
        Contact.id == _parse_uuid(contact_id), Contact.user_id == current_user.id
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    link = db.query(ApplicationContact).filter(
        ApplicationContact.application_id == app.id,
        ApplicationContact.contact_id == contact.id,
    ).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    db.delete(link)
    db.flush()
    return None


@router.get("/applications/{application_id}/recommendations", response_model=List[RecommendationResponse])
def get_application_recommendations(
    application_id: str,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[RecommendationResponse]:
    app = ApplicationService.get(db, _parse_uuid(application_id), current_user.id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    recs = ApplicationService.get_recommendations(db, app.id, current_user.id)
    return [RecommendationResponse.model_validate(r) for r in recs]


@router.post(
    "/applications/{application_id}/recommendations",
    response_model=List[RecommendationResponse],
    status_code=status.HTTP_201_CREATED,
)
def regenerate_application_recommendations(
    application_id: str,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[RecommendationResponse]:
    app = ApplicationService.get(db, _parse_uuid(application_id), current_user.id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    recs = ApplicationService.refresh_recommendations(db, app.id, current_user.id)
    return [RecommendationResponse.model_validate(r) for r in recs]


@router.get("/applications/{application_id}/offer", response_model=Optional[OfferResponse])
def get_application_offer(
    application_id: str,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Optional[OfferResponse]:
    app = ApplicationService.get(db, _parse_uuid(application_id), current_user.id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    offer = OfferService.get_by_application(db, app.id, current_user.id)
    if not offer:
        return None
    return OfferResponse.model_validate(offer)


@router.put("/applications/{application_id}/offer", response_model=OfferResponse)
def upsert_application_offer(
    application_id: str,
    payload: OfferUpdate,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> OfferResponse:
    app = ApplicationService.get(db, _parse_uuid(application_id), current_user.id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    existing = OfferService.get_by_application(db, app.id, current_user.id)
    data = payload.model_dump(exclude_unset=True)
    if existing:
        if "status" in data and data["status"] is not None:
            data["status"] = data["status"].value
        offer = OfferService.update(db, existing, **data)
    else:
        create_data = payload.model_dump(exclude_unset=True)
        if "status" in create_data and create_data["status"] is not None:
            create_data["status"] = create_data["status"].value
        offer = OfferService.create(db, user_id=current_user.id, application_id=app.id, **create_data)
    return OfferResponse.model_validate(offer)


# ---------------------------------------------------------------------------
# Companies
# ---------------------------------------------------------------------------


@router.get("/companies", response_model=List[CompanyResponse])
def list_companies(
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[CompanyResponse]:
    companies = CompanyService.get_user_companies(db, current_user.id)
    return [CompanyResponse.model_validate(c) for c in companies]


@router.post("/companies", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def create_company(
    payload: CompanyCreate,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CompanyResponse:
    company = CompanyService.get_or_create(
        db,
        name=payload.name,
        website=payload.website,
        industry=payload.industry,
        location=payload.location,
        size=payload.size,
        description=payload.description,
        logo_url=payload.logo_url,
    )
    CompanyService.create_or_update_user_link(db, user_id=current_user.id, company_id=company.id)
    db.flush()
    return CompanyResponse.model_validate(company)


@router.get("/companies/{company_id}", response_model=CompanyResponse)
def get_company(
    company_id: str,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CompanyResponse:
    company = _require_linked_company(db, _parse_uuid(company_id), current_user.id)
    return CompanyResponse.model_validate(company)


@router.patch("/companies/{company_id}", response_model=CompanyResponse)
def update_company(
    company_id: str,
    payload: CompanyUpdate,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CompanyResponse:
    company = _require_linked_company(db, _parse_uuid(company_id), current_user.id)
    data = payload.model_dump(exclude_unset=True)
    company = CompanyService.update(db, company, **data)
    return CompanyResponse.model_validate(company)


@router.delete("/companies/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(
    company_id: str,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    company = _require_linked_company(db, _parse_uuid(company_id), current_user.id)
    _ensure_company_has_no_other_users(db, [company.id], current_user.id)
    db.delete(company)
    db.flush()
    return None


@router.post("/companies/{company_id}/merge", response_model=CompanyResponse)
def merge_companies(
    company_id: str,
    target_company_id: UUID = Query(...),
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CompanyResponse:
    source = _require_linked_company(db, _parse_uuid(company_id), current_user.id)
    target = _require_linked_company(db, target_company_id, current_user.id)
    if source.id == target.id:
        raise HTTPException(status_code=400, detail="Companies must be different")
    _ensure_company_has_no_other_users(db, [source.id, target.id], current_user.id)
    merged = CompanyService.merge(db, source.id, target.id, merged_by_user_id=current_user.id)
    return CompanyResponse.model_validate(merged)


# ---------------------------------------------------------------------------
# Contacts
# ---------------------------------------------------------------------------


@router.get("/contacts", response_model=List[ContactResponse])
def list_contacts(
    company_id: Optional[UUID] = Query(default=None),
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[ContactResponse]:
    stmt = select(Contact).where(Contact.user_id == current_user.id)
    if company_id:
        stmt = stmt.where(Contact.company_id == company_id)
    contacts = list(db.execute(stmt).scalars().all())
    return [ContactResponse.model_validate(c) for c in contacts]


@router.post("/contacts", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
def create_contact(
    payload: ContactCreate,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ContactResponse:
    if payload.company_id is not None:
        _require_linked_company(db, payload.company_id, current_user.id)
    contact = Contact(
        user_id=current_user.id,
        company_id=payload.company_id,
        name=payload.name,
        title=payload.title,
        email=payload.email,
        linkedin_url=payload.linkedin_url,
        phone=payload.phone,
        notes=payload.notes,
        relationship_status=payload.relationship_status,
    )
    db.add(contact)
    db.flush()
    return ContactResponse.model_validate(contact)


@router.get("/contacts/{contact_id}", response_model=ContactResponse)
def get_contact(
    contact_id: str,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ContactResponse:
    contact = db.query(Contact).filter(
        Contact.id == _parse_uuid(contact_id), Contact.user_id == current_user.id
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return ContactResponse.model_validate(contact)


@router.patch("/contacts/{contact_id}", response_model=ContactResponse)
def update_contact(
    contact_id: str,
    payload: ContactUpdate,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ContactResponse:
    contact = db.query(Contact).filter(
        Contact.id == _parse_uuid(contact_id), Contact.user_id == current_user.id
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        if value is not None:
            setattr(contact, key, value)
    contact.updated_at = datetime.now(timezone.utc)
    db.flush()
    return ContactResponse.model_validate(contact)


@router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(
    contact_id: str,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    contact = db.query(Contact).filter(
        Contact.id == _parse_uuid(contact_id), Contact.user_id == current_user.id
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.delete(contact)
    db.flush()
    return None


# ---------------------------------------------------------------------------
# Interviews
# ---------------------------------------------------------------------------


@router.get("/interviews", response_model=List[InterviewResponse])
def list_interviews(
    application_id: Optional[UUID] = Query(default=None),
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[InterviewResponse]:
    stmt = select(Interview).where(Interview.user_id == current_user.id)
    if application_id:
        stmt = stmt.where(Interview.application_id == application_id)
    interviews = list(db.execute(stmt).scalars().all())
    return [InterviewResponse.model_validate(i) for i in interviews]


@router.post("/interviews", response_model=InterviewResponse, status_code=status.HTTP_201_CREATED)
def create_interview(
    payload: InterviewCreate,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> InterviewResponse:
    app = ApplicationService.get(db, payload.application_id, current_user.id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    _require_owned_contacts(db, payload.interviewer_contact_ids, current_user.id)
    interview = InterviewService.create(
        db,
        user_id=current_user.id,
        application_id=payload.application_id,
        interview_type=payload.interview_type.value,
        scheduled_at=payload.scheduled_at,
        duration_minutes=payload.duration_minutes,
        timezone=payload.timezone,
        location_or_meeting_url=payload.location_or_meeting_url,
        interviewer_contact_ids=[str(c) for c in payload.interviewer_contact_ids] if payload.interviewer_contact_ids else None,
        notes=payload.notes,
        preparation_notes=payload.preparation_notes,
    )
    db.flush()
    return InterviewResponse.model_validate(interview)


@router.get("/interviews/{interview_id}", response_model=InterviewResponse)
def get_interview(
    interview_id: str,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> InterviewResponse:
    interview = InterviewService.get(db, _parse_uuid(interview_id), current_user.id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return InterviewResponse.model_validate(interview)


@router.patch("/interviews/{interview_id}", response_model=InterviewResponse)
def update_interview(
    interview_id: str,
    payload: InterviewUpdate,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> InterviewResponse:
    interview = InterviewService.get(db, _parse_uuid(interview_id), current_user.id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    data = payload.model_dump(exclude_unset=True)
    _require_owned_contacts(db, data.get("interviewer_contact_ids"), current_user.id)
    if "interview_type" in data:
        data["interview_type"] = data["interview_type"].value
    if "status" in data:
        data["status"] = data["status"].value
    if "outcome" in data:
        data["outcome"] = data["outcome"].value
    if "interviewer_contact_ids" in data and data["interviewer_contact_ids"]:
        data["interviewer_contact_ids"] = [str(c) for c in data["interviewer_contact_ids"]]
    interview = InterviewService.update(db, interview, **data)
    return InterviewResponse.model_validate(interview)


@router.delete("/interviews/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_interview(
    interview_id: str,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    interview = InterviewService.get(db, _parse_uuid(interview_id), current_user.id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    InterviewService.delete(db, interview)
    return None


# ---------------------------------------------------------------------------
# Follow-ups
# ---------------------------------------------------------------------------


@router.get("/follow-ups", response_model=List[FollowUpResponse])
def list_follow_ups(
    application_id: Optional[UUID] = Query(default=None),
    status: Optional[str] = Query(default=None),
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[FollowUpResponse]:
    stmt = select(FollowUp).where(FollowUp.user_id == current_user.id)
    if application_id:
        stmt = stmt.where(FollowUp.application_id == application_id)
    if status:
        stmt = stmt.where(FollowUp.status == status)
    follow_ups = list(db.execute(stmt).scalars().all())
    return [FollowUpResponse.model_validate(f) for f in follow_ups]


@router.post("/follow-ups", response_model=FollowUpResponse, status_code=status.HTTP_201_CREATED)
def create_follow_up(
    payload: FollowUpCreate,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> FollowUpResponse:
    if payload.application_id is not None and ApplicationService.get(
        db, payload.application_id, current_user.id
    ) is None:
        raise HTTPException(status_code=404, detail="Application not found")
    if payload.contact_id is not None:
        _require_owned_record(
            db,
            Contact,
            payload.contact_id,
            current_user.id,
            "Contact not found",
        )
    follow_up = FollowUpService.create(
        db,
        user_id=current_user.id,
        application_id=payload.application_id,
        contact_id=payload.contact_id,
        follow_up_type=payload.follow_up_type.value,
        title=payload.title,
        notes=payload.notes,
        due_at=payload.due_at,
        priority=payload.priority,
        reminder_at=payload.reminder_at,
        created_by="manual",
    )
    db.flush()
    return FollowUpResponse.model_validate(follow_up)


@router.get("/follow-ups/{follow_up_id}", response_model=FollowUpResponse)
def get_follow_up(
    follow_up_id: str,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> FollowUpResponse:
    follow_up = FollowUpService.get(db, _parse_uuid(follow_up_id), current_user.id)
    if not follow_up:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    return FollowUpResponse.model_validate(follow_up)


@router.patch("/follow-ups/{follow_up_id}", response_model=FollowUpResponse)
def update_follow_up(
    follow_up_id: str,
    payload: FollowUpUpdate,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> FollowUpResponse:
    follow_up = FollowUpService.get(db, _parse_uuid(follow_up_id), current_user.id)
    if not follow_up:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    data = payload.model_dump(exclude_unset=True)
    if "follow_up_type" in data:
        data["follow_up_type"] = data["follow_up_type"].value
    if "status" in data:
        data["status"] = data["status"].value
    follow_up = FollowUpService.update(db, follow_up, **data)
    return FollowUpResponse.model_validate(follow_up)


@router.delete("/follow-ups/{follow_up_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_follow_up(
    follow_up_id: str,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    follow_up = FollowUpService.get(db, _parse_uuid(follow_up_id), current_user.id)
    if not follow_up:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    FollowUpService.delete(db, follow_up)
    return None


@router.post("/follow-ups/{follow_up_id}/complete", response_model=FollowUpResponse)
def complete_follow_up(
    follow_up_id: str,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> FollowUpResponse:
    follow_up = FollowUpService.get(db, _parse_uuid(follow_up_id), current_user.id)
    if not follow_up:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    follow_up = FollowUpService.complete(db, follow_up)
    return FollowUpResponse.model_validate(follow_up)


# ---------------------------------------------------------------------------
# CRM Dashboard / Pipeline / Analytics
# ---------------------------------------------------------------------------


@router.get("/crm/dashboard", response_model=ApplicationStatsResponse)
def get_crm_dashboard(
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ApplicationStatsResponse:
    stats = DashboardService.get_stats(db, current_user.id)
    return ApplicationStatsResponse(**stats)


@router.get("/crm/pipeline", response_model=PipelineResponse)
def get_crm_pipeline(
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PipelineResponse:
    stages = DashboardService.get_pipeline(db, current_user.id)
    return PipelineResponse(
        stages=[
            PipelineStageResponse(
                status=s["status"],
                label=s["label"],
                count=s["count"],
            )
            for s in stages
        ],
        total=sum(s["count"] for s in stages),
    )


@router.get("/crm/analytics", response_model=FunnelResponse)
def get_crm_analytics(
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> FunnelResponse:
    funnel = DashboardService.get_funnel(db, current_user.id)
    total = sum(s["count"] for s in funnel)
    offers = sum(s["count"] for s in funnel if s["stage"] == "offer")
    accepted = sum(s["count"] for s in funnel if s["stage"] == "accepted")
    rejected = sum(s["count"] for s in funnel if s["stage"] == "rejected")
    return FunnelResponse(
        stages=[FunnelStageResponse(**s) for s in funnel],
        total_applications=total,
        total_offers=offers,
        total_rejections=rejected,
    )


# ---------------------------------------------------------------------------
# Activity feed
# ---------------------------------------------------------------------------


@router.get("/activities", response_model=ActivityFeedResponse)
def list_activities(
    application_id: Optional[UUID] = Query(default=None),
    event_type: Optional[str] = Query(default=None, max_length=64),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ActivityFeedResponse:
    evt_type = ActivityEventType(event_type) if event_type else None
    items, total = TimelineService.list_events(
        db, current_user.id, application_id=application_id, event_type=evt_type, page=page, page_size=page_size
    )
    return ActivityFeedResponse(items=items, total=total, page=page, page_size=page_size)
