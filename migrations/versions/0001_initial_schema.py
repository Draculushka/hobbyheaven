"""Initial schema

Revision ID: 0001
Revises: 
Create Date: 2026-03-15 13:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Создаем таблицу posts, если ее нет (на случай первого запуска)
    op.create_table(
        'posts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('author', sa.String(), nullable=True),
        sa.Column('image_path', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_posts_id'), 'posts', ['id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_posts_id'), table_name='posts')
    op.drop_table('posts')
