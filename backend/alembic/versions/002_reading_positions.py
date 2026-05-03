"""Add reading_positions table and update FK cascades

Revision ID: 002_reading_positions
Revises: 001_initial
Create Date: 2026-05-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_reading_positions'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Создать таблицу reading_positions и обновить FK cascade."""
    # Create reading_positions table
    op.create_table(
        'reading_positions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('book_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chunk_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('offset', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_read_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('book_id'),
    )
    op.create_index('idx_reading_position_book_id', 'reading_positions', ['book_id'], unique=True)

    # Update book_chunks FK to use CASCADE delete
    # Drop old FK constraint and recreate with ondelete=CASCADE
    op.drop_constraint('book_chunks_book_id_fkey', 'book_chunks', type_='foreignkey')
    op.create_foreign_key(
        'book_chunks_book_id_fkey',
        'book_chunks',
        'books',
        ['book_id'],
        ['id'],
        ondelete='CASCADE',
    )


def downgrade() -> None:
    """Удалить таблицу reading_positions и восстановить старые FK."""
    # Restore book_chunks FK without CASCADE
    op.drop_constraint('book_chunks_book_id_fkey', 'book_chunks', type_='foreignkey')
    op.create_foreign_key(
        'book_chunks_book_id_fkey',
        'book_chunks',
        'books',
        ['book_id'],
        ['id'],
    )

    op.drop_index('idx_reading_position_book_id', table_name='reading_positions')
    op.drop_table('reading_positions')
