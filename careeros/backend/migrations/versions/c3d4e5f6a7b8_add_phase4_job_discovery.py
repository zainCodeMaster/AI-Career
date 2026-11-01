"""Add Phase 4 job discovery tables

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-09-03 06:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'job_sources',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('integration_method', sa.String(length=50), nullable=False),
        sa.Column('base_url', sa.String(length=512), nullable=True),
        sa.Column('country', sa.String(length=2), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_success_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_failure_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('consecutive_failures', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_jobs_discovered', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index('ix_job_sources_category', 'job_sources', ['category'], unique=False)

    op.create_table(
        'jobs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('source', sa.String(length=64), nullable=False),
        sa.Column('source_job_id', sa.String(length=512), nullable=False),
        sa.Column('source_url', sa.String(length=1024), nullable=True),
        sa.Column('raw_source_metadata', sa.Text(), nullable=True),
        sa.Column('title', sa.String(length=512), nullable=False),
        sa.Column('company_name', sa.String(length=512), nullable=False),
        sa.Column('company_url', sa.String(length=1024), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('requirements', sa.Text(), nullable=True),
        sa.Column('responsibilities', sa.Text(), nullable=True),
        sa.Column('skills', sa.Text(), nullable=True),
        sa.Column('employment_type', sa.String(length=50), nullable=True),
        sa.Column('workplace_type', sa.String(length=50), nullable=True),
        sa.Column('department', sa.String(length=255), nullable=True),
        sa.Column('category', sa.String(length=255), nullable=True),
        sa.Column('location', sa.String(length=512), nullable=True),
        sa.Column('city', sa.String(length=255), nullable=True),
        sa.Column('province', sa.String(length=100), nullable=True),
        sa.Column('country', sa.String(length=2), nullable=False),
        sa.Column('is_remote', sa.Boolean(), nullable=False),
        sa.Column('is_pakistan_eligible', sa.Boolean(), nullable=False),
        sa.Column('salary_min', sa.Float(), nullable=True),
        sa.Column('salary_max', sa.Float(), nullable=True),
        sa.Column('salary_currency', sa.String(length=8), nullable=True),
        sa.Column('salary_period', sa.String(length=32), nullable=True),
        sa.Column('experience_min', sa.Integer(), nullable=True),
        sa.Column('experience_max', sa.Integer(), nullable=True),
        sa.Column('education_requirements', sa.String(length=255), nullable=True),
        sa.Column('posted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closing_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('discovered_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('eligibility', sa.Text(), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('normalized_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source', 'source_job_id', name='uq_jobs_source_job_id'),
    )
    op.create_index('ix_jobs_source', 'jobs', ['source'], unique=False)
    op.create_index('ix_jobs_title', 'jobs', ['title'], unique=False)
    op.create_index('ix_jobs_company_name', 'jobs', ['company_name'], unique=False)
    op.create_index('ix_jobs_employment_type', 'jobs', ['employment_type'], unique=False)
    op.create_index('ix_jobs_workplace_type', 'jobs', ['workplace_type'], unique=False)
    op.create_index('ix_jobs_city', 'jobs', ['city'], unique=False)
    op.create_index('ix_jobs_province', 'jobs', ['province'], unique=False)
    op.create_index('ix_jobs_country', 'jobs', ['country'], unique=False)
    op.create_index('ix_jobs_is_pakistan_eligible', 'jobs', ['is_pakistan_eligible'], unique=False)
    op.create_index('ix_jobs_category', 'jobs', ['category'], unique=False)
    op.create_index('ix_jobs_posted_at', 'jobs', ['posted_at'], unique=False)
    op.create_index('ix_jobs_closing_at', 'jobs', ['closing_at'], unique=False)
    op.create_index('ix_jobs_status', 'jobs', ['status'], unique=False)
    op.create_index('ix_jobs_is_active', 'jobs', ['is_active'], unique=False)
    op.create_index('ix_jobs_content_hash', 'jobs', ['content_hash'], unique=False)
    op.create_index('ix_jobs_normalized_hash', 'jobs', ['normalized_hash'], unique=False)
    op.create_index('ix_jobs_company_title', 'jobs', ['company_name', 'title'], unique=False)
    op.create_index('ix_jobs_active_posted', 'jobs', ['is_active', 'posted_at'], unique=False)

    op.create_table(
        'job_discovery_runs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('source_id', sa.String(length=64), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('jobs_found', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('jobs_created', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('jobs_updated', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('jobs_skipped', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('jobs_expired', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['source_id'], ['job_sources.id'], ),
    )
    op.create_index('ix_job_discovery_runs_source_id', 'job_discovery_runs', ['source_id'], unique=False)
    op.create_index('ix_job_discovery_runs_status', 'job_discovery_runs', ['status'], unique=False)

    op.create_table(
        'user_saved_jobs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('job_id', sa.String(length=36), nullable=False),
        sa.Column('saved_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.UniqueConstraint('user_id', 'job_id', name='uq_user_saved_jobs_user_job'),
    )
    op.create_index('ix_user_saved_jobs_user_id', 'user_saved_jobs', ['user_id'], unique=False)
    op.create_index('ix_user_saved_jobs_job_id', 'user_saved_jobs', ['job_id'], unique=False)

    op.create_table(
        'user_job_preferences',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('target_roles', sa.Text(), nullable=True),
        sa.Column('preferred_cities', sa.Text(), nullable=True),
        sa.Column('preferred_provinces', sa.Text(), nullable=True),
        sa.Column('remote_preference', sa.String(length=32), nullable=True),
        sa.Column('employment_types', sa.Text(), nullable=True),
        sa.Column('experience_level', sa.String(length=32), nullable=True),
        sa.Column('min_salary', sa.Float(), nullable=True),
        sa.Column('salary_currency', sa.String(length=8), nullable=True),
        sa.Column('sector_preference', sa.String(length=32), nullable=True),
        sa.Column('selected_industries', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index('ix_user_job_preferences_user_id', 'user_job_preferences', ['user_id'], unique=False)

    # Seed default source registry (disabled by default; operators opt-in).
    seed_sources = [
        # Government
        ("pk_fpsc", "FPSC — Federal Public Service Commission", "government", "government_fpsc", "public_page", "https://www.fpsc.gov.pk/", "PK"),
        ("pk_ppsc", "PPSC — Punjab Public Service Commission", "government", "government_ppsc", "public_page", "https://www.ppsc.gop.pk/", "PK"),
        ("pk_spsc", "SPSC — Sindh Public Service Commission", "government", "government_spsc", "public_page", "https://www.spsc.gov.pk/", "PK"),
        ("pk_kppsc", "KPPSC — Khyber Pakhtunkhwa Public Service Commission", "government", "government_kppsc", "public_page", "https://www.kppsc.gov.pk/", "PK"),
        ("pk_bpsc", "BPSC — Balochistan Public Service Commission", "government", "government_bpsc", "public_page", "https://www.bpsc.gob.pk/", "PK"),
        ("pk_nts", "NTS — National Testing Service", "government", "government_nts", "public_page", "https://www.nts.org.pk/", "PK"),
        ("pk_pts", "Pakistan Testing Service", "government", "government_pts", "public_page", "https://pts.org.pk/", "PK"),
        ("pk_ots", "OTS — Open Testing Service", "government", "government_ots", "public_page", "https://ots.org.pk/", "PK"),
        ("pk_njp", "National Jobs Portal", "government", "national_jobs_portal", "public_page", "https://njp.gov.pk/", "PK"),
        ("pk_punjab_jobs", "Punjab Jobs Online", "government", "punjab_jobs", "public_page", "https://jobs.punjab.gov.pk/", "PK"),
        # Private boards
        ("pk_rozee", "Rozee.pk", "private_board", "rozee_pk", "public_page", "https://www.rozee.pk/", "PK"),
        ("pk_mustakbil", "Mustakbil.com", "private_board", "mustakbil", "public_page", "https://www.mustakbil.com/", "PK"),
        ("pk_brightspyre", "BrightSpyre", "private_board", "brightspyre", "public_page", "https://www.brightspyre.com/", "PK"),
        ("linkedin_pk", "LinkedIn — Pakistan", "private_board", "linkedin", "unsupported", "https://www.linkedin.com/jobs/", "PK"),
        ("indeed_pk", "Indeed — Pakistan", "private_board", "indeed", "unsupported", "https://pk.indeed.com/", "PK"),
        # International remote sources
        ("remote_ok", "Remote OK", "remote", "remote_api", "api", "https://remoteok.com/", "WW"),
        ("himalayas", "Himalayas", "remote", "himalayas_api", "api", "https://himalayas.app/", "WW"),
        # Remote (generic/legacy)
        ("remote_generic", "Generic Remote Jobs (Pakistan-eligible)", "remote", "remote_aggregator", "unsupported", "", ""),
        # Company career pages (examples — operator adds more)
        ("company_template", "Company Career Page Template", "company_career", "company_page", "public_page", "", "PK"),
    ]
    for sid, name, cat, st, method, url, country in seed_sources:
        op.execute(
            sa.text(
                "INSERT INTO job_sources (id, name, category, source_type, integration_method, base_url, country, enabled, is_active, notes, consecutive_failures, total_jobs_discovered, created_at, updated_at) "
                "VALUES (:id, :name, :cat, :st, :method, :url, :country, 0, 1, :notes, 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            ).bindparams(
                id=sid,
                name=name,
                cat=cat,
                st=st,
                method=method,
                url=url,
                country=country,
                notes="Seeded by Phase 4 migration. Disabled by default — operator must enable after configuring integration.",
            )
        )


def downgrade() -> None:
    op.drop_index('ix_user_job_preferences_user_id', table_name='user_job_preferences')
    op.drop_table('user_job_preferences')
    op.drop_index('ix_user_saved_jobs_job_id', table_name='user_saved_jobs')
    op.drop_index('ix_user_saved_jobs_user_id', table_name='user_saved_jobs')
    op.drop_table('user_saved_jobs')
    op.drop_index('ix_job_discovery_runs_status', table_name='job_discovery_runs')
    op.drop_index('ix_job_discovery_runs_source_id', table_name='job_discovery_runs')
    op.drop_table('job_discovery_runs')
    op.drop_index('ix_jobs_active_posted', table_name='jobs')
    op.drop_index('ix_jobs_company_title', table_name='jobs')
    op.drop_index('ix_jobs_normalized_hash', table_name='jobs')
    op.drop_index('ix_jobs_content_hash', table_name='jobs')
    op.drop_index('ix_jobs_is_active', table_name='jobs')
    op.drop_index('ix_jobs_status', table_name='jobs')
    op.drop_index('ix_jobs_closing_at', table_name='jobs')
    op.drop_index('ix_jobs_posted_at', table_name='jobs')
    op.drop_index('ix_jobs_category', table_name='jobs')
    op.drop_index('ix_jobs_is_pakistan_eligible', table_name='jobs')
    op.drop_index('ix_jobs_country', table_name='jobs')
    op.drop_index('ix_jobs_province', table_name='jobs')
    op.drop_index('ix_jobs_city', table_name='jobs')
    op.drop_index('ix_jobs_workplace_type', table_name='jobs')
    op.drop_index('ix_jobs_employment_type', table_name='jobs')
    op.drop_index('ix_jobs_company_name', table_name='jobs')
    op.drop_index('ix_jobs_title', table_name='jobs')
    op.drop_index('ix_jobs_source', table_name='jobs')
    op.drop_table('jobs')
    op.drop_index('ix_job_sources_category', table_name='job_sources')
    op.drop_table('job_sources')
