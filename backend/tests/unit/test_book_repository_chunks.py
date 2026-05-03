"""
Unit-тесты для BookRepository.get_chunks метода.
"""

import pytest
from sqlalchemy.orm import Session
from uuid import uuid4

from src.repositories.book_repository import BookRepository
from src.models.book import Book, BookChunk


@pytest.fixture
def repository(db_session):
    """Создать репозиторий с тестовой сессией."""
    return BookRepository(db_session)


@pytest.fixture
def book_with_chunks(db_session):
    """Создать книгу с чанками."""
    book_id = uuid4()
    book = Book(
        id=book_id,
        title="Test Book",
        author="Test Author",
        file_path="/path/to/test.epub",
        file_format="epub",
        file_size=100000,
    )
    db_session.add(book)
    db_session.flush()

    chunks = [
        BookChunk(book_id=book_id, chunk_index=0, content_html="<p>Chunk 0</p>", word_count=100),
        BookChunk(book_id=book_id, chunk_index=1, content_html="<p>Chunk 1</p>", word_count=150),
        BookChunk(book_id=book_id, chunk_index=2, content_html="<p>Chunk 2</p>", word_count=200),
        BookChunk(book_id=book_id, chunk_index=3, content_html="<p>Chunk 3</p>", word_count=120),
        BookChunk(book_id=book_id, chunk_index=4, content_html="<p>Chunk 4</p>", word_count=180),
    ]
    for chunk in chunks:
        db_session.add(chunk)
    db_session.commit()

    return book_id


class TestBookRepositoryGetChunks:
    """Тесты для метода get_chunks."""

    def test_get_chunks_all(self, repository: BookRepository, book_with_chunks):
        """Получить все чанки книги без фильтрации."""
        chunks = repository.get_chunks(book_with_chunks)
        assert len(chunks) == 5
        indices = [c.chunk_index for c in chunks]
        assert indices == [0, 1, 2, 3, 4]

    def test_get_chunks_sorted_by_index(self, repository: BookRepository, book_with_chunks):
        """Чанки должны быть отсортированы по индексу."""
        chunks = repository.get_chunks(book_with_chunks)
        for i in range(len(chunks) - 1):
            assert chunks[i].chunk_index < chunks[i + 1].chunk_index

    def test_get_chunks_from_index(self, repository: BookRepository, book_with_chunks):
        """Получить чанки начиная с определённого индекса."""
        chunks = repository.get_chunks(book_with_chunks, from_index=2)
        assert len(chunks) == 3
        indices = [c.chunk_index for c in chunks]
        assert indices == [2, 3, 4]

    def test_get_chunks_to_index(self, repository: BookRepository, book_with_chunks):
        """Получить чанки до определённого индекса."""
        chunks = repository.get_chunks(book_with_chunks, to_index=2)
        assert len(chunks) == 3
        indices = [c.chunk_index for c in chunks]
        assert indices == [0, 1, 2]

    def test_get_chunks_from_and_to(self, repository: BookRepository, book_with_chunks):
        """Получить чанки в диапазоне индексов."""
        chunks = repository.get_chunks(book_with_chunks, from_index=1, to_index=3)
        assert len(chunks) == 3
        indices = [c.chunk_index for c in chunks]
        assert indices == [1, 2, 3]

    def test_get_chunks_single_chunk(self, repository: BookRepository, book_with_chunks):
        """Получить один чанк."""
        chunks = repository.get_chunks(book_with_chunks, from_index=2, to_index=2)
        assert len(chunks) == 1
        assert chunks[0].chunk_index == 2

    def test_get_chunks_empty_range(self, repository: BookRepository, book_with_chunks):
        """Получить чанки для несуществующего диапазона."""
        chunks = repository.get_chunks(book_with_chunks, from_index=10, to_index=20)
        assert len(chunks) == 0

    def test_get_chunks_nonexistent_book(self, repository: BookRepository):
        """Получить чанки для несуществующей книги."""
        fake_id = uuid4()
        chunks = repository.get_chunks(fake_id)
        assert len(chunks) == 0

    def test_get_chunks_content_integrity(self, repository: BookRepository, book_with_chunks):
        """Проверить целостность содержимого чанков."""
        chunks = repository.get_chunks(book_with_chunks)
        expected_contents = [
            "<p>Chunk 0</p>",
            "<p>Chunk 1</p>",
            "<p>Chunk 2</p>",
            "<p>Chunk 3</p>",
            "<p>Chunk 4</p>",
        ]
        for i, chunk in enumerate(chunks):
            assert chunk.content_html == expected_contents[i]
            assert chunk.word_count == [100, 150, 200, 120, 180][i]
