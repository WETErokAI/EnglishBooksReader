"""
Unit-тесты для BookRepository: search и check_duplicate методы.
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
def sample_books(db_session):
    """Создать тестовые книги."""
    books = [
        Book(
            id=uuid4(),
            title="The Great Gatsby",
            author="F. Scott Fitzgerald",
            file_path="/path/to/gatsby.epub",
            file_format="epub",
            file_size=100000,
            date_added=datetime(2026, 1, 1, 10, 0, 0),
        ),
        Book(
            id=uuid4(),
            title="1984",
            author="George Orwell",
            file_path="/path/to/1984.epub",
            file_format="epub",
            file_size=120000,
            date_added=datetime(2026, 1, 2, 10, 0, 0),
        ),
        Book(
            id=uuid4(),
            title="Animal Farm",
            author="George Orwell",
            file_path="/path/to/animal_farm.epub",
            file_format="epub",
            file_size=80000,
            date_added=datetime(2026, 1, 3, 10, 0, 0),
        ),
        Book(
            id=uuid4(),
            title="To Kill a Mockingbird",
            author=None,  # Книга без автора
            file_path="/path/to/mockingbird.epub",
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

    def test_search_by_title_exact_match(self, repository: BookRepository, sample_books):
        """Поиск по точному совпадению названия."""
        results = repository.search("The Great Gatsby")
        assert len(results) == 1
        assert results[0].title == "The Great Gatsby"
        assert results[0].author == "F. Scott Fitzgerald"

    def test_search_by_title_partial_match(self, repository: BookRepository, sample_books):
        """Поиск по частичному совпадению названия."""
        results = repository.search("gatsby")
        assert len(results) == 1
        assert results[0].title == "The Great Gatsby"

    def test_search_by_author(self, repository: BookRepository, sample_books):
        """Поиск по автору."""
        results = repository.search("George Orwell")
        assert len(results) == 2
        # Должны быть обе книги автора
        titles = {book.title for book in results}
        assert "1984" in titles
        assert "Animal Farm" in titles

    def test_search_case_insensitive(self, repository: BookRepository, sample_books):
        """Поиск должен быть нечувствителен к регистру."""
        results_upper = repository.search("GATSBY")
        results_lower = repository.search("gatsby")
        assert len(results_upper) == 1
        assert len(results_lower) == 1
        assert results_upper[0].id == results_lower[0].id

    def test_search_no_results(self, repository: BookRepository, sample_books):
        """Поиск без результатов."""
        results = repository.search("Harry Potter")
        assert len(results) == 0

    def test_search_empty_query(self, repository: BookRepository, sample_books):
        """Поиск с пустым запросом возвращает все книги."""
        results = repository.search("")
        assert len(results) == 4  # Все 4 книги

    def test_search_respects_limit(self, repository: BookRepository, sample_books):
        """Поиск должен соблюдать лимит."""
        results = repository.search("", limit=2)
        assert len(results) == 2

    def test_search_partial_author(self, repository: BookRepository, sample_books):
        """Поиск по частичному имени автора."""
        results = repository.search("Fitzgerald")
        assert len(results) == 1
        assert results[0].title == "The Great Gatsby"

    def test_search_with_null_author(self, repository: BookRepository, sample_books):
        """Поиск книги с NULL автором."""
        results = repository.search("To Kill a Mockingbird")
        assert len(results) == 1
        assert results[0].title == "To Kill a Mockingbird"
        assert results[0].author is None


class TestBookRepositoryCheckDuplicate:
    """Тесты для метода check_duplicate."""

    def test_check_duplicate_exact_match(self, repository: BookRepository, sample_books):
        """Проверка дубликата по точному совпадению."""
        duplicate = repository.check_duplicate("The Great Gatsby", "F. Scott Fitzgerald")
        assert duplicate is not None
        assert duplicate.title == "The Great Gatsby"

    def test_check_duplicate_case_insensitive(self, repository: BookRepository, sample_books):
        """Проверка дубликата без учета регистра."""
        duplicate = repository.check_duplicate("the great gatsby", "f. scott fitzgerald")
        assert duplicate is not None
        assert duplicate.title == "The Great Gatsby"

    def test_check_duplicate_with_whitespace(self, repository: BookRepository, sample_books):
        """Проверка дубликата с лишними пробелами."""
        duplicate = repository.check_duplicate("  The Great Gatsby  ", "  F. Scott Fitzgerald  ")
        assert duplicate is not None
        assert duplicate.title == "The Great Gatsby"

    def test_check_duplicate_no_duplicate(self, repository: BookRepository, sample_books):
        """Проверка когда дубликата нет."""
        duplicate = repository.check_duplicate("Harry Potter", "J.K. Rowling")
        assert duplicate is None

    def test_check_duplicate_title_only_no_author(self, repository: BookRepository, sample_books):
        """Проверка дубликата только по названию (без автора)."""
        duplicate = repository.check_duplicate("To Kill a Mockingbird")
        assert duplicate is not None
        assert duplicate.title == "To Kill a Mockingbird"

    def test_check_duplicate_different_author(self, repository: BookRepository, sample_books):
        """Проверка что разные авторы не считаются дубликатом."""
        duplicate = repository.check_duplicate("The Great Gatsby", "George Orwell")
        assert duplicate is None

    def test_check_duplicate_same_author_different_title(
        self, repository: BookRepository, sample_books
    ):
        """Проверка что один автор с разными названиями не дубликат."""
        duplicate = repository.check_duplicate("Animal Farm", "F. Scott Fitzgerald")
        assert duplicate is None

    def test_check_duplicate_null_author_in_db(self, repository: BookRepository, sample_books):
        """Проверка дубликата с NULL автором в БД."""
        # Должно найти книгу с NULL author
        duplicate = repository.check_duplicate("To Kill a Mockingbird")
        assert duplicate is not None
        assert duplicate.title == "To Kill a Mockingbird"
        
        # Если передать author=None, должно искать книги с NULL author
        duplicate_with_none = repository.check_duplicate("To Kill a Mockingbird", author=None)
        assert duplicate_with_none is not None

    def test_check_duplicate_with_empty_string_author(self, repository: BookRepository, sample_books):
        """Проверка что пустая строка автора ведет себя как None."""
        # Пустая строка в Python является falsy, поэтому check_duplicate
        # будет искать книги с NULL author
        duplicate = repository.check_duplicate("To Kill a Mockingbird", "")
        assert duplicate is not None
        assert duplicate.title == "To Kill a Mockingbird"
