"""add is_admin to user

Revision ID: bffb59e34693
Revises: eb3667a95720
Create Date: 2026-03-15 23:11:04.468895

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bffb59e34693'
down_revision: Union[str, Sequence[str], None] = 'eb3667a95720'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('is_admin', sa.Integer(), server_default='0', nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'is_admin')
