"""rename_post_to_hobby_add_tags

Revision ID: eb3667a95720
Revises: 0001
Create Date: 2026-03-15 14:08:03.435363

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'eb3667a95720'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Переименовываем таблицу posts в hobbies
    op.rename_table('posts', 'hobbies')
    
    # Переименовываем индексы и ограничения (Alembic обычно делает это автоматически при rename_table в некоторых диалектах, но лучше явно)
    # В PostgreSQL индексы при переименовании таблицы сохраняются, но их имена могут остаться старыми.
    op.execute("ALTER INDEX ix_posts_id RENAME TO ix_hobbies_id")
    op.execute("ALTER TABLE hobbies RENAME CONSTRAINT posts_pkey TO hobbies_pkey")

    # Создаем таблицу tags
    op.create_table('tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_tags_id'), 'tags', ['id'], unique=False)

    # Создаем таблицу связи hobby_tags
    op.create_table('hobby_tags',
        sa.Column('hobby_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['hobby_id'], ['hobbies.id'], ),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ),
        sa.PrimaryKeyConstraint('hobby_id', 'tag_id')
    )


def downgrade() -> None:
    op.drop_table('hobby_tags')
    op.drop_index(op.f('ix_tags_id'), table_name='tags')
    op.drop_table('tags')
    
    op.execute("ALTER INDEX ix_hobbies_id RENAME TO ix_posts_id")
    op.execute("ALTER TABLE hobbies RENAME CONSTRAINT hobbies_pkey TO posts_pkey")
    op.rename_table('hobbies', 'posts')
