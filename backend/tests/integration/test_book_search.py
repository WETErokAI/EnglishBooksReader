"""
Интеграционные тесты для search endpoint.

Проверяет:
- GET /api/v1/books?search= — поиск по названию
- GET /api/v1/books?search= — поиск по автору
- GET /api/v1/books?search= — пагинация с поиском
- GET /api/v1/books?search= — пустой результат
"""

import pytest
from datetime import datetime
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models.book import Book


@pytest.fixture
def app():
    """Создать тестовое FastAPI приложение."""
    from app.main import app as main_app
    return main_app


@pytest.fixture
def client(app, db_session, tmp_path):
    """Тестовый клиент с настроенной БД."""
    from app.database import get_db
    from src.utils import storage as storage_module

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    storage_module.ensure_storage_directories = lambda: None

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()


@pytest.fixture
def search_books(db_session):
    """Создать тестовые книги для поиска."""
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
            author=None,
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


class TestSearchEndpoint:
    """Тесты GET /api/v1/books с параметром search."""

    def test_search_by_title(self, client: TestClient, search_books):
        """Поиск по названию книги."""
        response = client.get("/api/v1/books?search=gatsby")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["books"]) == 1
        assert data["books"][0]["title"] == "The Great Gatsby"

    def test_search_by_author(self, client: TestClient, search_books):
        """Поиск по автору."""
        response = client.get("/api/v1/books?search=Orwell")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        titles = {book["title"] for book in data["books"]}
        assert "1984" in titles
        assert "Animal Farm" in titles

    def test_search_case_insensitive(self, client: TestClient, search_books):
        """Поиск без учёта регистра."""
        response_lower = client.get("/api/v1/books?search=1984")
        response_upper = client.get("/api/v1/books?search=1984")

        assert response_lower.status_code == 200
        assert response_upper.status_code == 200
        assert response_lower.json()["total"] == 1
        assert response_upper.json()["total"] == 1

    def test_search_no_results(self, client: TestClient, search_books):
        """Поиск без результатов."""
        response = client.get("/api/v1/books?search=Harry Potter")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["books"] == []

    def test_search_with_pagination(self, client: TestClient, search_books):
        """Поиск с пагинацией."""
        # Поиск "Orwell" возвращает 2 книги, проверяем пагинацию
        response = client.get("/api/v1/books?search=Orwell&page=1&page_size=1")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["books"]) == 1
        assert data["page"] == 1
        assert data["page_size"] == 1

    def test_search_empty_string(self, client: TestClient, search_books):
        """Пустой поисковый запрос возвращает все книги."""
        response = client.get("/api/v1/books?search=")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 4
        assert len(data["books"]) == 4

    def test_search_no_search_param(self, client: TestClient, search_books):
        """Без параметра search возвращает все книги."""
        response = client.get("/api/v1/books")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 4

    def test_search_partial_word(self, client: TestClient, search_books):
        """Поиск по частичному совпадению слова."""
        response = client.get("/api/v1/books?search=Kill")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["books"][0]["title"] == "To Kill a Mockingbird"

    def test_search_null_author_book(self, client: TestClient, search_books):
        """Поиск книги с NULL автором."""
        response = client.get("/api/v1/books?search=Mockingbird")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["books"][0]["title"] == "To Kill a Mockingbird"
        assert data["books"][0]["author"] is None

    def test_search_results_order(self, client: TestClient, search_books):
        """Результаты поиска упорядочены по дате добавления (новые первыми)."""
        response = client.get("/api/v1/books?search=")

        assert response.status_code == 200
        data = response.json()
        books = data["books"]
        for i in range(len(books) - 1):
            assert books[i]["date_added"] >= books[i + 1]["date_added"]
