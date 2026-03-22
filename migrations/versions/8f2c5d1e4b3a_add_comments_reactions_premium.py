"""add_comments_reactions_premium

Revision ID: 8f2c5d1e4b3a
Revises: 714815d2aa28
Create Date: 2026-03-22 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f2c5d1e4b3a'
down_revision: Union[str, Sequence[str], None] = '714815d2aa28'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_premium column to users
    op.add_column('users', sa.Column('is_premium', sa.Boolean(), server_default='0', nullable=False))
    
    # Create comments table
    op.create_table('comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('hobby_id', sa.Integer(), nullable=False),
        sa.Column('persona_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['hobby_id'], ['hobbies.id'], ),
        sa.ForeignKeyConstraint(['persona_id'], ['personas.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_comments_id'), 'comments', ['id'], unique=False)
    op.create_index(op.f('ix_comments_hobby_id'), 'comments', ['hobby_id'], unique=False)
    op.create_index(op.f('ix_comments_persona_id'), 'comments', ['persona_id'], unique=False)
    op.create_index(op.f('ix_comments_created_at'), 'comments', ['created_at'], unique=False)

    # Create reactions table
    op.create_table('reactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('hobby_id', sa.Integer(), nullable=False),
        sa.Column('persona_id', sa.Integer(), nullable=False),
        sa.Column('emoji_type', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['hobby_id'], ['hobbies.id'], ),
        sa.ForeignKeyConstraint(['persona_id'], ['personas.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reactions_id'), 'reactions', ['id'], unique=False)
    op.create_index(op.f('ix_reactions_hobby_id'), 'reactions', ['hobby_id'], unique=False)
    op.create_index(op.f('ix_reactions_persona_id'), 'reactions', ['persona_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_reactions_persona_id'), table_name='reactions')
    op.drop_index(op.f('ix_reactions_hobby_id'), table_name='reactions')
    op.drop_index(op.f('ix_reactions_id'), table_name='reactions')
    op.drop_table('reactions')

    op.drop_index(op.f('ix_comments_created_at'), table_name='comments')
    op.drop_index(op.f('ix_comments_persona_id'), table_name='comments')
    op.drop_index(op.f('ix_comments_hobby_id'), table_name='comments')
    op.drop_index(op.f('ix_comments_id'), table_name='comments')
    op.drop_table('comments')

    op.drop_column('users', 'is_premium')
