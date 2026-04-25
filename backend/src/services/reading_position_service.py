"""
Сервис для управления позициями чтения.

Сохранение и получение последней позиции чтения для книг.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.repositories.book_repository import BookRepository


class ReadingPositionService:
    """Сервис для сохранения/получения позиции чтения."""

    def __init__(self, db: Session, book_repository: BookRepository):
        """Инициализация сервиса.

        Args:
            db: Сессия базы данных.
            book_repository: Репозиторий книг.
        """
        self.db = db
        self.book_repository = book_repository

    def save_position(
        self,
        book_id: UUID,
        chunk_id: UUID,
        offset: int,
        timestamp: Optional[datetime] = None,
    ) -> bool:
        """Сохранить позицию чтения для книги.

        Args:
            book_id: UUID книги.
            chunk_id: UUID чанка.
            offset: Смещение в чанке (в символах).
            timestamp: Метка времени (по умолчанию текущее время).

        Returns:
            True если позиция сохранена, False если книга не найдена.
        """
        # Проверяем что книга существует
        book = self.book_repository.get_by_id(book_id)
        if not book:
            return False

        # Валидация offset
        if offset < 0:
            offset = 0

        # Создаём данные позиции
        position_data = {
            "chunk_id": str(chunk_id),
            "offset": offset,
            "timestamp": (timestamp or datetime.utcnow()).isoformat(),
        }

        # Обновляем позицию в книге
        self.book_repository.update(book_id, {"last_reading_position": position_data})
        return True

    def get_position(self, book_id: UUID) -> Optional[dict]:
        """Получить последнюю позицию чтения для книги.

        Args:
            book_id: UUID книги.

        Returns:
            Словарь с данными позиции или None если позиция не сохранена.
        """
        book = self.book_repository.get_by_id(book_id)
        if not book:
            return None

        return book.last_reading_position
