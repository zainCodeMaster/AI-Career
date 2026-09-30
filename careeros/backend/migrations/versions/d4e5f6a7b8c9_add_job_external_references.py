"""Add job_external_references table for cross-source provenance tracking.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-09-08 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'job_external_references',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('job_id', sa.String(length=36), nullable=False),
        sa.Column('source_id', sa.String(length=64), nullable=False),
        sa.Column('source_job_id', sa.String(length=512), nullable=False),
        sa.Column('source_url', sa.String(length=1024), nullable=True),
        sa.Column('first_seen_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_job_external_refs_job_id', 'job_external_references', ['job_id'], unique=False)
    op.create_index('ix_job_external_refs_source', 'job_external_references', ['source_id', 'source_job_id'], unique=True)

    # Update JobSource integration_method column to be more descriptive for new sources
    # The column already exists with sufficient length (String(50))


def downgrade() -> None:
    op.drop_index('ix_job_external_refs_source', table_name='job_external_references')
    op.drop_index('ix_job_external_refs_job_id', table_name='job_external_references')
    op.drop_table('job_external_references')
