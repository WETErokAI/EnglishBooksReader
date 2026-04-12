"""Create books and book_chunks tables

Revision ID: 001_initial
Revises: 
Create Date: 2026-04-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Создать таблицы books и book_chunks."""
    # Create fileformat enum (create_type=True создаст enum автоматически в create_table)
    fileformat_enum = postgresql.ENUM('txt', 'epub', 'fb2', name='fileformat', create_type=False)

    # Создаём enum вручную через SQL
    op.execute("CREATE TYPE fileformat AS ENUM ('txt', 'epub', 'fb2')")

    # Create books table
    op.create_table(
        'books',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('author', sa.String(300), nullable=True),
        sa.Column('file_path', sa.String(1000), nullable=False),
        sa.Column('file_format', fileformat_enum, nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('cover_image_path', sa.String(1000), nullable=True),
        sa.Column('cover_thumbnail_path', sa.String(1000), nullable=True),
        sa.Column('date_added', sa.DateTime(), nullable=False),
        sa.Column('last_reading_position', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_book_title_author', 'books', ['title', 'author'])

    # Create book_chunks table
    op.create_table(
        'book_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('book_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content_html', sa.Text(), nullable=False),
        sa.Column('word_count', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_chunk_book_index', 'book_chunks', ['book_id', 'chunk_index'], unique=True)


def downgrade() -> None:
    """Удалить таблицы books и book_chunks."""
    op.drop_index('idx_chunk_book_index', table_name='book_chunks')
    op.drop_table('book_chunks')
    op.drop_index('idx_book_title_author', table_name='books')
    op.drop_table('books')

    # Drop fileformat enum
    op.execute("DROP TYPE fileformat")
