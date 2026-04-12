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
