"""Phase 4 — Job Discovery database models.

Normalized global Job model + per-source configuration/health, discovery
run logs, and user-scoped SavedJob and JobPreferences.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Source configuration / health
# ---------------------------------------------------------------------------


class JobSource(Base):
    """Configuration and health for a single job source.

    Sources are global (not user-scoped). Each source represents a specific
    integration with a Pakistan job board, government portal, company career
    page, or remote aggregator.
    """

    __tablename__ = "job_sources"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # government | private_board | company_career | remote | feed
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # api | feed | public_page | browser | unsupported
    integration_method: Mapped[str] = mapped_column(String(50), nullable=False)
    base_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    country: Mapped[str] = mapped_column(String(2), nullable=False, default="PK")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Operator-visible note about what this source actually does and why.
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Health
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_success_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_failure_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    consecutive_failures: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_jobs_discovered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    def __repr__(self) -> str:
        return f"<JobSource(id={self.id}, name={self.name}, enabled={self.enabled})>"


# ---------------------------------------------------------------------------
# Normalized Job
# ---------------------------------------------------------------------------


class Job(Base):
    """A normalized job listing.

    Jobs are global. User-specific state (saved, applied) lives in separate
    user-scoped tables that FK to this table.
    """

    __tablename__ = "jobs"

    id: Mapped[UUID] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )

    # Source provenance
    source: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_job_id: Mapped[str] = mapped_column(String(512), nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    raw_source_metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Core fields
    title: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    company_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requirements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    responsibilities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    skills: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Job characteristics
    employment_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    workplace_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    department: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    # Location
    location: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    province: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    country: Mapped[str] = mapped_column(String(2), nullable=False, default="PK", index=True)
    is_remote: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Deprecated: use eligibility field instead (kept for backward compatibility)
    is_pakistan_eligible: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )

    # Compensation
    salary_min: Mapped[Optional[float]] = mapped_column(nullable=True)
    salary_max: Mapped[Optional[float]] = mapped_column(nullable=True)
    salary_currency: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    salary_period: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    # Experience / education
    experience_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    experience_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    education_requirements: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Lifecycle / status
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    closing_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    # Eligibility / provenance
    # Single canonical three-state eligibility: eligible | ineligible | unknown
    eligibility: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, index=True,
        # "eligible" | "ineligible" | "unknown"
    )
    eligibility_reason: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        # Human-readable reason for eligibility status
    )

    # Hashes for deduplication
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    normalized_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    __table_args__ = (
        # A given (source, source_job_id) is globally unique — same listing
        # from the same source must not produce duplicates.
        UniqueConstraint("source", "source_job_id", name="uq_jobs_source_job_id"),
        Index("ix_jobs_company_title", "company_name", "title"),
        Index("ix_jobs_active_posted", "is_active", "posted_at"),
    )

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, title={self.title[:30]}, source={self.source})>"


# ---------------------------------------------------------------------------
# Discovery run logs
# ---------------------------------------------------------------------------


class JobDiscoveryRun(Base):
    """A single execution of a job source (or the full discovery engine)."""

    __tablename__ = "job_discovery_runs"

    id: Mapped[UUID] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    source_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("job_sources.id"), nullable=True, index=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running", index=True)
    # running | success | partial | failed
    jobs_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    jobs_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    jobs_updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    jobs_skipped: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    jobs_expired: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<JobDiscoveryRun(id={self.id}, status={self.status}, found={self.jobs_found})>"


# ---------------------------------------------------------------------------
# User-scoped: saved jobs
# ---------------------------------------------------------------------------


class UserSavedJob(Base):
    """A user-scoped bookmark of a global Job."""

    __tablename__ = "user_saved_jobs"

    id: Mapped[UUID] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    user_id: Mapped[UUID] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    job_id: Mapped[UUID] = mapped_column(
        String(36), ForeignKey("jobs.id"), nullable=False, index=True
    )
    saved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="uq_user_saved_jobs_user_job"),
    )


# ---------------------------------------------------------------------------
# User-scoped: job preferences (used by Phase 5 matching)
# ---------------------------------------------------------------------------


class UserJobPreferences(Base):
    """User's job discovery preferences. One row per user."""

    __tablename__ = "user_job_preferences"

    id: Mapped[UUID] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
        index=True,
    )
    target_roles: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list
    preferred_cities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list
    preferred_provinces: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list
    remote_preference: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    # "remote_only" | "hybrid_ok" | "onsite_ok" | "any"
    employment_types: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list
    experience_level: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    # "entry" | "mid" | "senior" | "executive" | "any"
    min_salary: Mapped[Optional[float]] = mapped_column(nullable=True)
    salary_currency: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    sector_preference: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    # "government" | "private" | "remote" | "any"
    selected_industries: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )


# ---------------------------------------------------------------------------
# Cross-source provenance
# ---------------------------------------------------------------------------


class JobExternalReference(Base):
    """Tracks which sources have reported a given canonical Job.

    A single canonical Job may originate from one source but be
    re-observed by other sources. This table preserves provenance
    for deduplication and expiry tracking.
    """

    __tablename__ = "job_external_references"

    id: Mapped[UUID] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    job_id: Mapped[UUID] = mapped_column(
        String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source_job_id: Mapped[str] = mapped_column(String(512), nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    __table_args__ = (
        UniqueConstraint("source_id", "source_job_id", name="uq_job_refs_source_job_id"),
    )

    def __repr__(self) -> str:
        return f"<JobExternalReference(job_id={self.job_id}, source={self.source_id})>"
