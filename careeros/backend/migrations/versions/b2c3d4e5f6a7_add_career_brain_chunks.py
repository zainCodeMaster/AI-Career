"""Add career brain chunks table with pgvector

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-03 05:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    # Only create the pgvector extension on PostgreSQL. SQLite (used in tests)
    # does not support extensions but pgvector's Vector type degrades to a
    # JSON column automatically.
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        'career_brain_chunks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('source_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=512), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('embedding_model', sa.String(length=128), nullable=False),
        sa.Column('embedding_dimension', sa.Integer(), nullable=False),
        sa.Column('embedding', Vector(384), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_career_brain_chunks_content_hash'),
        'career_brain_chunks',
        ['content_hash'],
        unique=False,
    )
    op.create_index(
        op.f('ix_career_brain_chunks_source_id'),
        'career_brain_chunks',
        ['source_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_career_brain_chunks_source_type'),
        'career_brain_chunks',
        ['source_type'],
        unique=False,
    )
    op.create_index(
        op.f('ix_career_brain_chunks_user_id'),
        'career_brain_chunks',
        ['user_id'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_career_brain_chunks_user_id'), table_name='career_brain_chunks')
    op.drop_index(op.f('ix_career_brain_chunks_source_type'), table_name='career_brain_chunks')
    op.drop_index(op.f('ix_career_brain_chunks_source_id'), table_name='career_brain_chunks')
    op.drop_index(op.f('ix_career_brain_chunks_content_hash'), table_name='career_brain_chunks')
    op.drop_table('career_brain_chunks')
    # Note: we intentionally do NOT drop the pgvector extension on downgrade
    # to avoid affecting other tables that may use it.

