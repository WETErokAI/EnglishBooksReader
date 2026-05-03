"""
Интеграционные тесты для library endpoints.

Проверяет:
- GET /api/v1/books — получение списка книг
- GET /api/v1/books/{book_id} — получение детальной информации
- PATCH /api/v1/books/{book_id} — переименование книги
- DELETE /api/v1/books/{book_id} — удаление книги
- GET /api/v1/books/{book_id}/chunks — получение чанков
"""

import pytest
from datetime import datetime
from io import BytesIO
from uuid import uuid4
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models.book import Book, BookChunk


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

    # Патчим storage чтобы не создавать реальные директории
    storage_module.ensure_storage_directories = lambda: None

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_books(db_session):
    """Создать несколько тестовых книг."""
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
    ]
    for book in books:
        db_session.add(book)
    db_session.commit()
    return books


@pytest.fixture
def sample_book_with_chunks(db_session):
    """Создать книгу с чанками."""
    book = Book(
        id=uuid4(),
        title="Test Book",
        author="Test Author",
        file_path="/path/to/test.epub",
        file_format="epub",
        file_size=150000,
        date_added=datetime.utcnow(),
    )
    db_session.add(book)
    db_session.flush()

    chunks = [
        BookChunk(
            book_id=book.id,
            chunk_index=0,
            content_html="<h1>Chapter 1</h1><p>Content 1</p>",
            word_count=100,
        ),
        BookChunk(
            book_id=book.id,
            chunk_index=1,
            content_html="<h1>Chapter 2</h1><p>Content 2</p>",
            word_count=150,
        ),
    ]
    for chunk in chunks:
        db_session.add(chunk)
    db_session.commit()
    
    book.chunks = chunks
    return book


class TestGetBooks:
    """Тесты GET /api/v1/books."""

    def test_get_all_books(self, client: TestClient, sample_books):
        """Получение списка всех книг."""
        response = client.get("/api/v1/books")
        
        assert response.status_code == 200
        data = response.json()
        assert "books" in data
        assert "total" in data
        assert data["total"] == 2
        assert len(data["books"]) == 2

    def test_get_books_with_pagination(self, client: TestClient, sample_books):
        """Пагинация при получении книг."""
        response = client.get("/api/v1/books?page=1&page_size=1")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["books"]) == 1
        assert data["total"] == 2
        assert data["page"] == 1

    def test_get_books_with_search(self, client: TestClient, sample_books):
        """Поиск книг по названию."""
        response = client.get("/api/v1/books?search=gatsby")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["books"][0]["title"] == "The Great Gatsby"

    def test_get_books_empty(self, client: TestClient):
        """Получение списка когда нет книг."""
        response = client.get("/api/v1/books")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["books"] == []


class TestGetBook:
    """Тесты GET /api/v1/books/{book_id}."""

    def test_get_book_by_id(self, client: TestClient, sample_books):
        """Получение книги по ID."""
        book = sample_books[0]
        response = client.get(f"/api/v1/books/{book.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(book.id)
        assert data["title"] == book.title
        assert data["author"] == book.author

    def test_get_book_not_found(self, client: TestClient):
        """Получение несуществующей книги."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/books/{fake_id}")
        
        assert response.status_code == 404


class TestUpdateBook:
    """Тесты PATCH /api/v1/books/{book_id}."""

    def test_rename_book(self, client: TestClient, sample_books):
        """Переименование книги."""
        book = sample_books[0]
        response = client.patch(
            f"/api/v1/books/{book.id}",
            json={"title": "The Great Gatsby (Renamed)"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "The Great Gatsby (Renamed)"
        assert data["author"] == book.author  # Автор не изменился

    def test_update_author(self, client: TestClient, sample_books):
        """Обновление автора книги."""
        book = sample_books[0]
        response = client.patch(
            f"/api/v1/books/{book.id}",
            json={"author": "Francis Scott Fitzgerald"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["author"] == "Francis Scott Fitzgerald"

    def test_update_book_not_found(self, client: TestClient):
        """Обновление несуществующей книги."""
        fake_id = uuid4()
        response = client.patch(
            f"/api/v1/books/{fake_id}",
            json={"title": "New Title"},
        )
        
        assert response.status_code == 404


class TestDeleteBook:
    """Тесты DELETE /api/v1/books/{book_id}."""

    def test_delete_book(self, client: TestClient, sample_books, db_session):
        """Удаление книги."""
        book = sample_books[0]
        response = client.delete(f"/api/v1/books/{book.id}")

        assert response.status_code == 204

        # Проверяем что книга действительно удалена через API
        get_response = client.get(f"/api/v1/books/{book.id}")
        assert get_response.status_code == 404

        # Проверяем через БД (новая сессия видит изменения после commit)
        from sqlalchemy.orm import Session
        from app.database import SessionLocal
        fresh_session = SessionLocal()
        try:
            from src.models.book import Book
            deleted_book = fresh_session.query(Book).filter(Book.id == book.id).first()
            assert deleted_book is None, "Книга должна быть удалена из БД"
        finally:
            fresh_session.close()

    def test_delete_book_verifies_list_updated(self, client: TestClient, sample_books):
        """После удаления книга исчезает из списка."""
        book = sample_books[0]

        # Получаем список до удаления
        response_before = client.get("/api/v1/books")
        assert response_before.status_code == 200
        data_before = response_before.json()
        assert data_before["total"] == 2

        # Удаляем книгу
        delete_response = client.delete(f"/api/v1/books/{book.id}")
        assert delete_response.status_code == 204

        # Получаем список после удаления
        response_after = client.get("/api/v1/books")
        assert response_after.status_code == 200
        data_after = response_after.json()
        assert data_after["total"] == 1
        book_ids = [b["id"] for b in data_after["books"]]
        assert str(book.id) not in book_ids, "Удалённая книга не должна быть в списке"

    def test_delete_book_via_list_flow(self, client: TestClient, sample_books):
        """Тест полного flow удаления как в frontend: получить список → удалить → получить список."""
        # Step 1: Получаем список книг (как useGetBooks)
        list_response = client.get("/api/v1/books")
        assert list_response.status_code == 200
        books_data = list_response.json()["books"]
        assert len(books_data) == 2

        # Step 2: Берём ID первой книги из списка (как BookCard получает book.id)
        book_id_from_list = books_data[0]["id"]

        # Step 3: Удаляем книгу по этому ID (как deleteBookApi)
        delete_response = client.delete(f"/api/v1/books/{book_id_from_list}")
        assert delete_response.status_code == 204

        # Step 4: Получаем обновлённый список (как invalidateQueries → refetch)
        updated_list_response = client.get("/api/v1/books")
        assert updated_list_response.status_code == 200
        updated_books = updated_list_response.json()["books"]
        assert len(updated_books) == 1

        # Step 5: Проверяем что удалённая книга не в списке
        remaining_ids = [b["id"] for b in updated_books]
        assert book_id_from_list not in remaining_ids

    def test_delete_book_not_found(self, client: TestClient):
        """Удаление несуществующей книги."""
        fake_id = uuid4()
        response = client.delete(f"/api/v1/books/{fake_id}")

        assert response.status_code == 404


class TestDeleteBookWithChunks:
    """Тесты удаления книги с чанками — проверка cascade delete."""

    def test_delete_book_with_chunks_cascade(self, client: TestClient, sample_book_with_chunks):
        """Удаление книги удаляет и все связанные чанки (cascade)."""
        book = sample_book_with_chunks

        # Проверяем что chunks есть
        assert len(book.chunks) == 2

        # Удаляем книгу
        delete_response = client.delete(f"/api/v1/books/{book.id}")
        assert delete_response.status_code == 204

        # Проверяем через БД что chunks удалены
        from sqlalchemy.orm import Session as ORMSession
        from app.database import SessionLocal
        fresh_session = SessionLocal()
        try:
            from src.models.book import Book, BookChunk
            remaining_book = fresh_session.query(Book).filter(Book.id == book.id).first()
            assert remaining_book is None, "Книга должна быть удалена"
            remaining_chunks = (
                fresh_session.query(BookChunk)
                .filter(BookChunk.book_id == book.id)
                .all()
            )
            assert len(remaining_chunks) == 0, f"Чанки должны быть удалены, осталось: {len(remaining_chunks)}"
        finally:
            fresh_session.close()

    def test_delete_book_with_chunks_api_verified(self, client: TestClient, sample_book_with_chunks):
        """Удаление книги с чанками: проверка через API."""
        book = sample_book_with_chunks

        # Проверяем что чанки доступны через API
        chunks_response = client.get(f"/api/v1/books/{book.id}/chunks")
        assert chunks_response.status_code == 200
        assert chunks_response.json()["total_chunks"] == 2

        # Удаляем книгу
        delete_response = client.delete(f"/api/v1/books/{book.id}")
        assert delete_response.status_code == 204

        # Проверяем что чанки недоступны
        chunks_after = client.get(f"/api/v1/books/{book.id}/chunks")
        assert chunks_after.status_code == 404

        # Проверяем что книга недоступна
        book_after = client.get(f"/api/v1/books/{book.id}")
        assert book_after.status_code == 404


class TestBookChunks:
    """Тесты GET /api/v1/books/{book_id}/chunks."""

    def test_get_all_chunks(self, client: TestClient, sample_book_with_chunks):
        """Получение всех чанков книги."""
        book = sample_book_with_chunks
        response = client.get(f"/api/v1/books/{book.id}/chunks")
        
        assert response.status_code == 200
        data = response.json()
        assert "chunks" in data
        assert "total_chunks" in data
        assert data["total_chunks"] == 2
        assert len(data["chunks"]) == 2

    def test_get_chunks_with_range(self, client: TestClient, sample_book_with_chunks):
        """Получение чанков в диапазоне."""
        book = sample_book_with_chunks
        response = client.get(f"/api/v1/books/{book.id}/chunks?from_chunk=0&to_chunk=0")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["chunks"]) == 1
        assert data["chunks"][0]["chunk_index"] == 0

    def test_get_chunks_book_not_found(self, client: TestClient):
        """Получение чанков для несуществующей книги."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/books/{fake_id}/chunks")
        
        assert response.status_code == 404
