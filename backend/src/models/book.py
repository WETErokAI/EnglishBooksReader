"""
SQLAlchemy модели для библиотеки книг.

Сущности:
- Book: книга с метаданными
- BookChunk: чанк контента книги для динамической подгрузки
- ReadingPosition: позиция последнего чтения для книги
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Enum,
    Text,
    ForeignKey,
    Index,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Book(Base):
    """Модель книги с метаданными."""

    __tablename__ = "books"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    author = Column(String(300), nullable=True)
    file_path = Column(String(1000), nullable=False)
    file_format = Column(Enum("txt", "epub", "fb2", name="fileformat"), nullable=False)
    file_size = Column(Integer, nullable=False)
    cover_image_path = Column(String(1000), nullable=True)
    cover_thumbnail_path = Column(String(1000), nullable=True)
    date_added = Column(DateTime, nullable=False, default=datetime.utcnow)

    chunks = relationship(
        "BookChunk",
        back_populates="book",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    reading_position = relationship(
        "ReadingPosition",
        back_populates="book",
        cascade="all, delete-orphan",
        uselist=False,
    )

    __table_args__ = (
        Index("idx_book_title_author", "title", "author"),
    )

    def __repr__(self) -> str:
        return f"<Book(id={self.id}, title='{self.title}', author='{self.author}')>"


class BookChunk(Base):
    """Модель чанка контента книги."""

    __tablename__ = "book_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    book_id = Column(
        UUID(as_uuid=True),
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_index = Column(Integer, nullable=False)
    content_html = Column(Text, nullable=False)
    word_count = Column(Integer, nullable=False)

    book = relationship("Book", back_populates="chunks")

    __table_args__ = (
        Index("idx_chunk_book_index", "book_id", "chunk_index", unique=True),
    )

    def __repr__(self) -> str:
        return f"<BookChunk(id={self.id}, book_id={self.book_id}, index={self.chunk_index})>"


class ReadingPosition(Base):
    """Модель позиции последнего чтения для книги."""

    __tablename__ = "reading_positions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    book_id = Column(
        UUID(as_uuid=True),
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    chunk_id = Column(UUID(as_uuid=True), nullable=False)
    offset = Column(Integer, nullable=False, default=0)
    last_read_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    book = relationship("Book", back_populates="reading_position")

    __table_args__ = (
        Index("idx_reading_position_book_id", "book_id", unique=True),
    )

    def __repr__(self) -> str:
        return f"<ReadingPosition(book_id={self.book_id}, chunk_id={self.chunk_id}, offset={self.offset})>"
