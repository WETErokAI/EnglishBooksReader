"""
Unit-тесты для BookRepository search method.

Проверяет:
- Совпадения по title
- Совпадения по author
- Без результатов
- Очистка поиска (пустой query)
"""

import pytest
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime

from src.repositories.book_repository import BookRepository
from src.models.book import Book


@pytest.fixture
def repository(db_session):
    """Создать репозиторий с тестовой сессией."""
    return BookRepository(db_session)


@pytest.fixture
def search_books(db_session):
    """Создать тестовые книги для поиска."""
    books = [
        Book(
            id=uuid4(),
            title="Python Programming",
            author="Guido van Rossum",
            file_path="/path/to/python.epub",
            file_format="epub",
            file_size=100000,
            date_added=datetime(2026, 1, 1, 10, 0, 0),
        ),
        Book(
            id=uuid4(),
            title="Python Crash Course",
            author="Eric Matthes",
            file_path="/path/to/crash.epub",
            file_format="epub",
            file_size=120000,
            date_added=datetime(2026, 1, 2, 10, 0, 0),
        ),
        Book(
            id=uuid4(),
            title="Clean Code",
            author="Robert C. Martin",
            file_path="/path/to/cleancode.epub",
            file_format="epub",
            file_size=80000,
            date_added=datetime(2026, 1, 3, 10, 0, 0),
        ),
        Book(
            id=uuid4(),
            title="Design Patterns",
            author="Erich Gamma",
            file_path="/path/to/dp.epub",
            file_format="epub",
            file_size=90000,
            date_added=datetime(2026, 1, 4, 10, 0, 0),
        ),
    ]
    for book in books:
        db_session.add(book)
    db_session.commit()
    return books


class TestBookRepositorySearch:
    """Тесты для метода search."""

    def test_search_by_title_exact_match(self, repository: BookRepository, search_books):
        """Поиск по точному совпадению названия."""
        results = repository.search("Python Programming")
        assert len(results) == 1
        assert results[0].title == "Python Programming"
        assert results[0].author == "Guido van Rossum"

    def test_search_by_title_partial_match(self, repository: BookRepository, search_books):
        """Поиск по частичному совпадению названия."""
        results = repository.search("python")
        assert len(results) == 2
        titles = {book.title for book in results}
        assert "Python Programming" in titles
        assert "Python Crash Course" in titles

    def test_search_by_author(self, repository: BookRepository, search_books):
        """Поиск по автору."""
        results = repository.search("Martin")
        assert len(results) == 1
        assert results[0].title == "Clean Code"
        assert results[0].author == "Robert C. Martin"

    def test_search_no_results(self, repository: BookRepository, search_books):
        """Поиск без результатов."""
        results = repository.search("Machine Learning")
        assert len(results) == 0

    def test_search_empty_query(self, repository: BookRepository, search_books):
        """Поиск с пустым запросом возвращает все книги."""
        results = repository.search("")
        assert len(results) == 4  # Все 4 книги

    def test_search_case_insensitive(self, repository: BookRepository, search_books):
        """Поиск должен быть нечувствителен к регистру."""
        results_upper = repository.search("PYTHON")
        results_lower = repository.search("python")
        assert len(results_upper) == 2
        assert len(results_lower) == 2
        assert set(r.id for r in results_upper) == set(r.id for r in results_lower)

    def test_search_both_title_and_author(self, repository: BookRepository, search_books):
        """Поиск по названию, содержащемуся и в названии, и в авторе."""
        results = repository.search("Clean")
        assert len(results) == 1
        assert results[0].title == "Clean Code"

    def test_search_word_fragment(self, repository: BookRepository, search_books):
        """Поиск по фрагменту слова."""
        results = repository.search("Gram")
        # "Gram" содержится в "Programming" (не в "Patterns")
        assert len(results) == 1
        assert results[0].title == "Python Programming"

    def test_search_respects_limit(self, repository: BookRepository, search_books):
        """Поиск должен соблюдать лимит."""
        results = repository.search("", limit=2)
        assert len(results) == 2

    def test_search_results_ordered_by_date_desc(self, repository: BookRepository, search_books):
        """Результаты поиска должны быть упорядочены по дате добавления (новые первыми)."""
        results = repository.search("")
        assert results[0].date_added > results[-1].date_added
