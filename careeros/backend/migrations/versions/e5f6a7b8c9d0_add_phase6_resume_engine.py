"""Add Phase 6 Resume Engine tables.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-09-09 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create resumes table
    op.create_table('resumes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('resume_type', sa.String(length=32), nullable=False, server_default='base'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='draft'),
        sa.Column('target_job_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('parent_resume_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('structured_data', sa.JSON(), nullable=True),
        sa.Column('source_file_name', sa.String(length=255), nullable=True),
        sa.Column('source_file_type', sa.String(length=50), nullable=True),
        sa.Column('import_metadata', sa.JSON(), nullable=True),
        sa.Column('ats_score', sa.Integer(), nullable=True),
        sa.Column('ats_breakdown', sa.JSON(), nullable=True),
        sa.Column('ats_analyzed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ats_analyzed_for_job_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['ats_analyzed_for_job_id'], ['jobs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['parent_resume_id'], ['resumes.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['target_job_id'], ['jobs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'name', 'version_number', name='uq_resume_user_name_version'),
    )
    
    # Indexes for resumes
    op.create_index('ix_resumes_user_type', 'resumes', ['user_id', 'resume_type'], unique=False)
    op.create_index('ix_resumes_target_job', 'resumes', ['target_job_id'], unique=False)
    op.create_index('ix_resumes_parent', 'resumes', ['parent_resume_id'], unique=False)
    op.create_index('ix_resumes_ats_analyzed', 'resumes', ['ats_analyzed_for_job_id'], unique=False)
    op.create_index('ix_resumes_status', 'resumes', ['status'], unique=False)
    op.create_index('ix_resumes_resume_type', 'resumes', ['resume_type'], unique=False)

    # Create resume_sections table
    op.create_table('resume_sections',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('section_type', sa.String(length=50), nullable=False),
        sa.Column('section_title', sa.String(length=255), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_custom', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Indexes for resume_sections
    op.create_index('ix_resume_sections_resume_type', 'resume_sections', ['resume_id', 'section_type'], unique=False)
    op.create_index('ix_resume_sections_order', 'resume_sections', ['resume_id', 'display_order'], unique=False)
    op.create_index('ix_resume_sections_section_type', 'resume_sections', ['section_type'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_resume_sections_section_type', table_name='resume_sections')
    op.drop_index('ix_resume_sections_order', table_name='resume_sections')
    op.drop_index('ix_resume_sections_resume_type', table_name='resume_sections')
    op.drop_table('resume_sections')
    
    op.drop_index('ix_resumes_resume_type', table_name='resumes')
    op.drop_index('ix_resumes_status', table_name='resumes')
    op.drop_index('ix_resumes_ats_analyzed', table_name='resumes')
    op.drop_index('ix_resumes_parent', table_name='resumes')
    op.drop_index('ix_resumes_target_job', table_name='resumes')
    op.drop_index('ix_resumes_user_type', table_name='resumes')
    op.drop_table('resumes')
