"""Company service for Phase 7 CRM.

Handles company normalization, get_or_create, merge, and user-scoped overlays.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models.crm import Company, UserCompanyLink
from app.services.audit import create_audit_log


def _normalize_name(name: str) -> str:
    """Normalize a company name for deduplication.

    - Lowercase
    - Strip legal suffixes: Inc, Ltd, GmbH, Pvt, Corp, LLC, PLC, AG, SA, SAS
    - Collapse whitespace
    """
    n = name.strip().lower()
    suffixes = [
        r"\binc\.?\b",
        r"\bltd\.?\b",
        r"\bgmbh\b",
        r"\bpvt\.?\b",
        r"\bcorp\.?\b",
        r"\bllc\b",
        r"\bplc\b",
        r"\bag\b",
        r"\bsa\b",
        r"\bsas\b",
        r"\bco\.?\b",
        r"\bcompany\b",
    ]
    for pat in suffixes:
        n = re.sub(pat, "", n, flags=re.IGNORECASE)
    n = re.sub(r"\s+", " ", n).strip()
    return n


def _derive_domain(website: Optional[str], name: str) -> Optional[str]:
    """Derive a registrable domain from a website URL."""
    if not website:
        return None
    w = website.strip().lower()
    w = re.sub(r"^https?://", "", w)
    w = re.sub(r"^www\.", "", w)
    w = w.split("/")[0]
    if "." in w:
        return w
    return None


class CompanyService:
    """Service for company CRUD, normalization, and merge."""

    @staticmethod
    def get(db: Session, company_id: UUID) -> Optional[Company]:
        """Get a company by ID."""
        return db.get(Company, company_id)

    @staticmethod
    def list(db: Session, user_id: Optional[UUID] = None) -> List[Company]:
        """List companies, optionally filtered by user overlay."""
        stmt = select(Company)
        if user_id is not None:
            stmt = stmt.join(UserCompanyLink, Company.id == UserCompanyLink.company_id).where(
                UserCompanyLink.user_id == user_id
            )
        stmt = stmt.order_by(Company.normalized_name)
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_or_create(db: Session, name: str, website: Optional[str] = None, **kwargs) -> Company:
        """Get or create a company by normalized name/domain.

        Normalizes on write. Never silently auto-merges.
        """
        normalized = _normalize_name(name)
        domain = _derive_domain(website, name)
        stmt = select(Company).where(
            or_(
                Company.normalized_name == normalized,
                Company.domain == domain if domain else False,
            )
        )
        existing = db.execute(stmt).scalars().first()
        if existing:
            return existing
        company = Company(
            name=name.strip(),
            normalized_name=normalized,
            canonical_name=name.strip(),
            website=website,
            domain=domain,
            **{key: value for key, value in kwargs.items() if value is not None},
        )
        db.add(company)
        db.flush()
        return company

    @staticmethod
    def create(db: Session, name: str, website: Optional[str] = None, **kwargs) -> Company:
        """Create a new company with normalized name/domain."""
        normalized = _normalize_name(name)
        domain = _derive_domain(website, name)
        company = Company(
            name=name.strip(),
            normalized_name=normalized,
            canonical_name=name.strip(),
            website=website,
            domain=domain,
            **kwargs,
        )
        db.add(company)
        db.flush()
        return company

    @staticmethod
    def update(db: Session, company: Company, **kwargs) -> Company:
        """Update a company and re-normalize if name/website changed."""
        for key, value in kwargs.items():
            if key in ("name", "website") and value:
                normalized = _normalize_name(value) if key == "name" else company.normalized_name
                domain = _derive_domain(value, company.name) if key == "website" else company.domain
                setattr(company, "normalized_name", normalized)
                if key == "name":
                    setattr(company, "name", value.strip())
                    setattr(company, "canonical_name", value.strip())
                if key == "website":
                    setattr(company, "website", value)
                    setattr(company, "domain", domain)
            else:
                setattr(company, key, value)
        company.updated_at = datetime.now(timezone.utc)
        db.flush()
        return company

    @staticmethod
    def merge(
        db: Session,
        source_company_id: UUID,
        target_company_id: UUID,
        merged_by_user_id: UUID,
    ) -> Company:
        """Merge source company into target company.

        Re-points FKs from source to target, then deletes source.
        Records an audit entry.
        """
        source = db.get(Company, source_company_id)
        target = db.get(Company, target_company_id)
        if not source or not target:
            raise ValueError("Source or target company not found")
        if source.id == target.id:
            return target
        from sqlalchemy import update
        from app.db.models.crm import Application, Contact, UserCompanyLink
        for table, fk_col in [
            (Application, "company_id"),
            (Contact, "company_id"),
            (UserCompanyLink, "company_id"),
        ]:
            stmt = update(table).where(fk_col == source_company_id).values(company_id=target_company_id)
            db.execute(stmt)
        create_audit_log(
            db,
            event_type="COMPANY_MERGED",
            user_id=merged_by_user_id,
            details={
                "source_company_id": str(source_company_id),
                "target_company_id": str(target_company_id),
                "source_name": source.name,
                "target_name": target.name,
            },
        )
        db.delete(source)
        db.flush()
        return target

    @staticmethod
    def get_user_link(db: Session, user_id: UUID, company_id: UUID) -> Optional[UserCompanyLink]:
        """Get a user's company link."""
        stmt = select(UserCompanyLink).where(
            UserCompanyLink.user_id == user_id,
            UserCompanyLink.company_id == company_id,
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def create_or_update_user_link(
        db: Session, user_id: UUID, company_id: UUID, **kwargs
    ) -> UserCompanyLink:
        """Create or update a user company link."""
        link = CompanyService.get_user_link(db, user_id, company_id)
        if link:
            for key, value in kwargs.items():
                setattr(link, key, value)
            link.updated_at = datetime.now(timezone.utc)
        else:
            link = UserCompanyLink(user_id=user_id, company_id=company_id, **kwargs)
            db.add(link)
        db.flush()
        return link

    @staticmethod
    def get_user_companies(db: Session, user_id: UUID) -> List[Company]:
        """Get all companies a user has linked."""
        stmt = (
            select(Company)
            .join(UserCompanyLink, Company.id == UserCompanyLink.company_id)
            .where(UserCompanyLink.user_id == user_id)
            .order_by(Company.normalized_name)
        )
        return list(db.execute(stmt).scalars().all())
