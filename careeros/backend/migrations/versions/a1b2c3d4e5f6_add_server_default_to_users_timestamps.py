"""Add server_default to users created_at and updated_at

Revision ID: a1b2c3d4e5f6
Revises: 9ec9ba707c89
Create Date: 2026-09-02 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import func


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '9ec9ba707c89'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SQLite does not support ALTER COLUMN SET DEFAULT directly, so use
    # batch mode which recreates the table.
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('created_at',
                              existing_type=sa.DateTime(timezone=True),
                              nullable=False,
                              server_default=func.now())
        batch_op.alter_column('updated_at',
                              existing_type=sa.DateTime(timezone=True),
                              nullable=False,
                              server_default=func.now())


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('updated_at',
                              existing_type=sa.DateTime(timezone=True),
                              nullable=False,
                              server_default=None)
        batch_op.alter_column('created_at',
                              existing_type=sa.DateTime(timezone=True),
                              nullable=False,
                              server_default=None)
