"""Fix eligibility schema - remove is_pakistan_eligible, add eligibility index.

Revision ID: fix_eligibility_schema
Revises: b7c8d9e0f1a2
Create Date: 2026-10-31 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "fix_eligibility_schema"
down_revision: Union[str, Sequence[str], None] = "b7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add index on eligibility column
    op.create_index('ix_jobs_eligibility', 'jobs', ['eligibility'], unique=False)


def downgrade() -> None:
    # Remove the eligibility index
    op.drop_index('ix_jobs_eligibility', table_name='jobs')