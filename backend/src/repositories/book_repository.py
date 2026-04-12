"""
Репозиторий для работы с книгами.

CRUD операции:
- get_all: получить все книги с пагинацией и поиском
- get_by_id: получить книгу по ID
- add: добавить книгу
- delete: удалить книгу
- update: обновить метаданные
- check_duplicate: проверка на дубликат
- search: поиск по названию и автору
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.models.book import Book


class BookRepository:
    """Репозиторий для CRUD операций с книгами."""

    def __init__(self, db: Session):
        """Инициализация репозитория.

        Args:
            db: Сессия базы данных.
        """
        self.db = db

    def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
    ) -> tuple[list[Book], int]:
        """Получить все книги с пагинацией и опциональным поиском.

        Args:
            skip: Количество пропускаемых записей.
            limit: Максимальное количество записей.
            search: Поисковый запрос для фильтрации.

        Returns:
            Кортеж (список книг, общее количество).
        """
        query = self.db.query(Book)

        if search:
            search_pattern = f"%{search.lower()}%"
            query = query.filter(
                or_(
                    Book.title.ilike(search_pattern),
                    Book.author.ilike(search_pattern),
                )
            )

        total = query.count()
        books = query.order_by(Book.date_added.desc()).offset(skip).limit(limit).all()
        return books, total

    def get_by_id(self, book_id: UUID) -> Optional[Book]:
        """Получить книгу по ID.

        Args:
            book_id: UUID книги.

        Returns:
            Книга или None если не найдена.
        """
        return self.db.query(Book).filter(Book.id == book_id).first()

    def add(self, book: Book) -> Book:
        """Добавить книгу в базу данных.

        Args:
            book: Объект книги для добавления.

        Returns:
            Добавленная книга.
        """
        self.db.add(book)
        self.db.commit()
        self.db.refresh(book)
        return book

    def delete(self, book_id: UUID) -> bool:
        """Удалить книгу по ID.

        Args:
            book_id: UUID книги для удаления.

        Returns:
            True если книга удалена, False если не найдена.
        """
        book = self.get_by_id(book_id)
        if not book:
            return False
        self.db.delete(book)
        self.db.commit()
        return True

    def update(self, book_id: UUID, updates: dict) -> Optional[Book]:
        """Обновить метаданные книги.

        Args:
            book_id: UUID книги.
            updates: Словарь с полями для обновления.

        Returns:
            Обновленная книга или None если не найдена.
        """
        book = self.get_by_id(book_id)
        if not book:
            return None

        for key, value in updates.items():
            if hasattr(book, key) and value is not None:
                setattr(book, key, value)

        self.db.commit()
        self.db.refresh(book)
        return book

    def check_duplicate(self, title: str, author: Optional[str] = None) -> Optional[Book]:
        """Проверить наличие дубликата по названию и автору.

        Args:
            title: Название книги.
            author: Автор книги (опционально).

        Returns:
            Найденная книга-дубликат или None.
        """
        query = self.db.query(Book).filter(
            Book.title.ilike(title.strip().lower())
        )

        if author:
            query = query.filter(Book.author.ilike(author.strip().lower()))
        else:
            query = query.filter(Book.author.is_(None))

        return query.first()

    def search(self, query: str, limit: int = 50) -> list[Book]:
        """Поиск книг по названию и автору.

        Args:
            query: Поисковый запрос.
            limit: Максимальное количество результатов.

        Returns:
            Список найденных книг.
        """
        search_pattern = f"%{query.lower()}%"
        return (
            self.db.query(Book)
            .filter(
                or_(
                    Book.title.ilike(search_pattern),
                    Book.author.ilike(search_pattern),
                )
            )
            .order_by(Book.date_added.desc())
            .limit(limit)
            .all()
        )
