"""
Утилиты для управления хранилищем файлов.

Генерация путей для:
- Файлов книг
- Обложек
- Миниатюр
"""

import uuid
from pathlib import Path

from app.config import settings


def generate_book_file_path(book_id: uuid.UUID, original_filename: str) -> Path:
    """Сгенерировать путь для файла книги.

    Args:
        book_id: UUID книги.
        original_filename: Оригинальное имя файла.

    Returns:
        Полный путь к файлу книги.
    """
    storage_path = Path(settings.BOOKS_STORAGE_PATH)
    extension = Path(original_filename).suffix.lower()
    filename = f"{book_id}{extension}"
    return storage_path / filename


def generate_cover_path(book_id: uuid.UUID, extension: str = ".jpg") -> Path:
    """Сгенерировать путь для файла обложки.

    Args:
        book_id: UUID книги.
        extension: Расширение файла изображения.

    Returns:
        Полный путь к файлу обложки.
    """
    storage_path = Path(settings.COVERS_STORAGE_PATH) / "covers"
    storage_path.mkdir(parents=True, exist_ok=True)
    filename = f"{book_id}{extension}"
    return storage_path / filename


def generate_thumbnail_path(book_id: uuid.UUID, extension: str = ".jpg") -> Path:
    """Сгенерировать путь для миниатюры обложки.

    Args:
        book_id: UUID книги.
        extension: Расширение файла изображения.

    Returns:
        Полный путь к файлу миниатюры.
    """
    storage_path = Path(settings.COVERS_STORAGE_PATH) / "thumbnails"
    storage_path.mkdir(parents=True, exist_ok=True)
    filename = f"{book_id}{extension}"
    return storage_path / filename


def ensure_storage_directories() -> None:
    """Создать все необходимые директории хранилища."""
    directories = [
        Path(settings.BOOKS_STORAGE_PATH),
        Path(settings.COVERS_STORAGE_PATH) / "covers",
        Path(settings.COVERS_STORAGE_PATH) / "thumbnails",
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
