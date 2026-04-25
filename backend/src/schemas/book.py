"""
Pydantic схемы для книг.

Схемы:
- BookCreate: для загрузки книги
- BookUpdate: для обновления метаданных
- BookDTO: для отображения одной книги
- BookListDTO: для отображения списка книг с пагинацией
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class BookCreate(BaseModel):
    """Схема для загрузки книги.

    File upload обрабатывается через FastAPI UploadFile,
    поэтому эта схема пуста — валидация происходит в сервисе.
    """

    pass


class BookUpdate(BaseModel):
    """Схема для обновления метаданных книги."""

    title: Optional[str] = Field(None, max_length=500)
    author: Optional[str] = Field(None, max_length=300)


class BookDTO(BaseModel):
    """DTO для отображения книги."""

    id: UUID
    title: str
    author: Optional[str]
    file_format: str
    cover_thumbnail_path: Optional[str]
    date_added: datetime
    has_reading_position: bool

    model_config = ConfigDict(from_attributes=True)


class BookListDTO(BaseModel):
    """Схема для списка книг с пагинацией."""

    books: list[BookDTO]
    total: int
    page: int = 1
    page_size: int = 20


class BookChunkDTO(BaseModel):
    """DTO для отображения чанка книги."""

    chunk_index: int
    content_html: str
    word_count: int

    model_config = ConfigDict(from_attributes=True)


class BookChunksResponse(BaseModel):
    """Схема для ответа с чанками книги."""

    book_id: UUID
    chunks: list[BookChunkDTO]
    total_chunks: int


class ReadingPositionSave(BaseModel):
    """Схема для сохранения позиции чтения."""

    chunk_id: UUID
    offset: int = Field(ge=0)
    timestamp: datetime


class ReadingPositionResponse(BaseModel):
    """Схема для ответа с позицией чтения."""

    chunk_id: Optional[UUID] = None
    offset: int = 0
    timestamp: Optional[str] = None


class ReadingPositionSuccessResponse(BaseModel):
    """Схема для успешного сохранения позиции."""

    success: bool = True
