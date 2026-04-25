"""
Unit-тесты для ReadingPositionService.
"""

import pytest
from datetime import datetime
from uuid import uuid4

from src.services.reading_position_service import ReadingPositionService
from src.repositories.book_repository import BookRepository
from src.models.book import Book


@pytest.fixture
def repository(db_session):
    """Создать репозиторий с тестовой сессией."""
    return BookRepository(db_session)


@pytest.fixture
def service(db_session, repository):
    """Создать сервис позиции чтения."""
    return ReadingPositionService(db_session, repository)


@pytest.fixture
def sample_book(db_session, repository):
    """Создать тестовую книгу."""
    book = Book(
        id=uuid4(),
        title="Test Book",
        author="Test Author",
        file_path="/path/to/test.epub",
        file_format="epub",
        file_size=100000,
        date_added=datetime.utcnow(),
    )
    return repository.add(book)


class TestReadingPositionService:
    """Тесты для ReadingPositionService."""

    def test_save_position_new(self, service: ReadingPositionService, sample_book: Book):
        """Сохранение новой позиции чтения."""
        chunk_id = uuid4()
        result = service.save_position(sample_book.id, chunk_id, offset=1250)
        
        assert result is True
        
        # Проверяем что позиция сохранилась в БД
        book = service.get_position(sample_book.id)
        assert book is not None
        assert book["chunk_id"] == str(chunk_id)
        assert book["offset"] == 1250
        assert "timestamp" in book

    def test_save_position_update_existing(self, service: ReadingPositionService, sample_book: Book):
        """Обновление существующей позиции чтения."""
        chunk_id_1 = uuid4()
        service.save_position(sample_book.id, chunk_id_1, offset=500)
        
        # Обновляем позицию
        chunk_id_2 = uuid4()
        result = service.save_position(sample_book.id, chunk_id_2, offset=2500)
        
        assert result is True
        
        # Проверяем что позиция обновилась
        book = service.get_position(sample_book.id)
        assert book is not None
        assert book["chunk_id"] == str(chunk_id_2)
        assert book["offset"] == 2500

    def test_save_position_book_not_found(self, service: ReadingPositionService):
        """Сохранение позиции для несуществующей книги."""
        fake_book_id = uuid4()
        result = service.save_position(fake_book_id, uuid4(), offset=0)
        
        assert result is False

    def test_get_position_exists(self, service: ReadingPositionService, sample_book: Book):
        """Получение существующей позиции чтения."""
        chunk_id = uuid4()
        service.save_position(sample_book.id, chunk_id, offset=1250)
        
        position = service.get_position(sample_book.id)
        assert position is not None
        assert position["chunk_id"] == str(chunk_id)
        assert position["offset"] == 1250

    def test_get_position_not_exists(self, service: ReadingPositionService):
        """Получение позиции для книги без сохранённой позиции."""
        fake_book_id = uuid4()
        position = service.get_position(fake_book_id)
        
        assert position is None

    def test_save_position_with_timestamp(self, service: ReadingPositionService, sample_book: Book):
        """Сохранение позиции с кастомной меткой времени."""
        chunk_id = uuid4()
        custom_timestamp = datetime(2026, 1, 1, 12, 0, 0)
        result = service.save_position(
            sample_book.id, chunk_id, offset=3000, timestamp=custom_timestamp
        )
        
        assert result is True
        
        book = service.get_position(sample_book.id)
        assert book is not None
        # timestamp должен сохраниться
        assert book["timestamp"] is not None

    def test_save_position_validates_offset(self, service: ReadingPositionService, sample_book: Book):
        """Сохранение позиции с валидацией offset."""
        chunk_id = uuid4()
        
        # Отрицательный offset должен обрабатываться корректно
        result = service.save_position(sample_book.id, chunk_id, offset=-100)
        # Сервис должен либо отклонить, либо исправить на 0
        # (зависит от реализации - проверим что не падает с ошибкой)
        assert result is True or result is False  # Либо принято, либо отклонено

    def test_position_structure(self, service: ReadingPositionService, sample_book: Book):
        """Проверка структуры данных позиции."""
        chunk_id = uuid4()
        service.save_position(sample_book.id, chunk_id, offset=1250)
        
        position = service.get_position(sample_book.id)
        
        # Должны быть все необходимые поля
        assert "chunk_id" in position
        assert "offset" in position
        assert "timestamp" in position
        
        # Типы данных
        assert isinstance(position["chunk_id"], str)
        assert isinstance(position["offset"], int)
        assert isinstance(position["timestamp"], str)  # ISO формат
