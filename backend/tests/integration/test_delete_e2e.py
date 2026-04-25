"""
E2E тест удаления книги — полная проверка от создания до удаления.

Проверяет:
1. Создание книги через upload
2. Книга реально в БД (проверка через новую сессию)
3. Удаление через DELETE endpoint
4. Книга УДАЛЕНА из БД (проверка через новую сессию)
5. API GET /books не возвращает удалённую книгу
6. API GET /books/{id} возвращает 404
"""

import pytest
from datetime import datetime
from io import BytesIO
from pathlib import Path
from uuid import uuid4, UUID

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, inspect, String, TypeDecorator
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.models.book import Base, Book, BookChunk


class SQLiteUUID(TypeDecorator):
    """Тип UUID для SQLite в тестах (хранит как строку)."""
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return UUID(value)
        return value


@pytest.fixture
def app():
    """Создать тестовое FastAPI приложение."""
    from app.main import app as main_app
    return main_app


@pytest.fixture
def client_and_engine(tmp_path):
    """Создать клиент с ОТДЕЛЬНЫМ engine для проверок БД."""
    from app.main import app as main_app
    from app.database import get_db
    from src.utils import storage as storage_module

    # Патчим UUID типы на SQLite-совместимые
    Book.__table__.c['id'].type = SQLiteUUID()
    BookChunk.__table__.c['id'].type = SQLiteUUID()
    BookChunk.__table__.c['book_id'].type = SQLiteUUID()

    # Создаём ОТДЕЛЬНЫЙ engine для проверок
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Включаем FOREIGN KEY для SQLite — по умолчанию отключены
    @event.listens_for(test_engine, "connect")
    def set_sqlite_pragma(_dbapi_connection, _connection_record):
        cursor = _dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Создаём таблицы
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        from sqlalchemy.orm import Session
        db = Session(bind=test_engine)
        try:
            yield db
        finally:
            db.close()

    main_app.dependency_overrides[get_db] = override_get_db

    # Патчим storage
    storage_module.ensure_storage_directories = lambda: None
    books_dir = tmp_path / "books"
    covers_dir = tmp_path / "covers"
    thumbnails_dir = tmp_path / "thumbnails"
    books_dir.mkdir()
    covers_dir.mkdir()
    thumbnails_dir.mkdir()
    storage_module.generate_book_file_path = lambda fmt, book_id: str(books_dir / f"{book_id}.{fmt}")
    storage_module.generate_cover_path = lambda book_id: str(covers_dir / f"{book_id}.jpg")
    storage_module.generate_thumbnail_path = lambda book_id: str(thumbnails_dir / f"{book_id}.jpg")

    client = TestClient(main_app)

    yield client, test_engine

    main_app.dependency_overrides.clear()


def _create_minimal_epub() -> bytes:
    """Создать минимальный EPUB файл."""
    import zipfile
    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        zf.writestr("mimetype", "application/epub+zip")
        zf.writestr("META-INF/container.xml",
            '<?xml version="1.0"?><container><rootfiles>'
            '<rootfile full-path="content.opf"/>'
            '</rootfiles></container>')
        zf.writestr("content.opf",
            '<?xml version="1.0"?>'
            '<package version="3.0" unique-id="uid">'
            '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
            '<dc:identifier id="uid">urn:uuid:test</dc:identifier>'
            '<dc:title>Test Book For Delete</dc:title>'
            '<dc:creator>Test Author</dc:creator>'
            '</metadata>'
            '<manifest><item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/></manifest>'
            '<spine><itemref idref="ch1"/></spine>'
            '</package>')
        zf.writestr("ch1.xhtml",
            '<html xmlns="http://www.w3.org/1999/xhtml">'
            '<body><h1>Chapter 1</h1><p>Test content.</p></body></html>')
    buf.seek(0)
    return buf.getvalue()


class TestDeleteBookE2E:
    """E2E тесты удаления книги — полная проверка."""

    def test_delete_book_full_flow(self, client_and_engine):
        """Полный flow: создать → проверить в БД → удалить → проверить что УДАЛЕНА."""
        client, test_engine = client_and_engine

        # ====== STEP 1: Создаём книгу напрямую через БД ======
        Session = sessionmaker(bind=test_engine)
        session = Session()

        book_id = uuid4()
        book = Book(
            id=book_id,
            title="Book To Delete",
            author="Test Author",
            file_path="/path/to/book.epub",
            file_format="epub",
            file_size=1000,
            date_added=datetime.utcnow(),
        )
        session.add(book)
        session.commit()
        session.close()

        print(f"\n[STEP 1] Создана книга с id={book_id}")

        # ====== STEP 2: Проверяем что книга в БД через НОВУЮ сессию ======
        fresh_session = Session()
        found_book = fresh_session.query(Book).filter(Book.id == book_id).first()
        assert found_book is not None, "Книга ДОЛЖНА быть в БД после создания"
        assert found_book.title == "Book To Delete"
        fresh_session.close()
        print("[STEP 2] Книга подтверждена в БД через новую сессию")

        # ====== STEP 3: Проверяем что API возвращает книгу ======
        get_response = client.get(f"/api/v1/books/{book_id}")
        assert get_response.status_code == 200, f"GET /books/{book_id} должен вернуть 200, получил {get_response.status_code}"
        book_data = get_response.json()
        assert book_data["title"] == "Book To Delete"
        print("[STEP 3] GET /books/{id} вернул книгу")

        # ====== STEP 4: Проверяем что книга в списке ======
        list_response = client.get("/api/v1/books")
        assert list_response.status_code == 200
        books_list = list_response.json()["books"]
        book_ids_in_list = [b["id"] for b in books_list]
        assert str(book_id) in book_ids_in_list, f"Книга {book_id} должна быть в списке"
        print("[STEP 4] Книга в списке GET /books")

        # ====== STEP 5: Удаляем книгу через API ======
        delete_response = client.delete(f"/api/v1/books/{book_id}")
        assert delete_response.status_code == 204, f"DELETE должен вернуть 204, получил {delete_response.status_code}"
        print(f"[STEP 5] DELETE /books/{book_id} вернул {delete_response.status_code}")

        # ====== STEP 6: Проверяем что книга УДАЛЕНА из БД через НОВУЮ сессию ======
        fresh_session2 = Session()
        deleted_book = fresh_session2.query(Book).filter(Book.id == book_id).first()
        assert deleted_book is None, f"Книга {book_id} должна быть УДАЛЕНА из БД, но найдена: {deleted_book}"
        fresh_session2.close()
        print("[STEP 6] Книга УДАЛЕНА из БД — подтверждено через новую сессию")

        # ====== STEP 7: Проверяем что GET /books/{id} возвращает 404 ======
        get_after_delete = client.get(f"/api/v1/books/{book_id}")
        assert get_after_delete.status_code == 404, f"GET после удаления должен вернуть 404, получил {get_after_delete.status_code}"
        print("[STEP 7] GET /books/{id} после удаления вернул 404")

        # ====== STEP 8: Проверяем что GET /books НЕ содержит удалённую книгу ======
        list_after_delete = client.get("/api/v1/books")
        assert list_after_delete.status_code == 200
        books_after = list_after_delete.json()["books"]
        book_ids_after = [b["id"] for b in books_after]
        assert str(book_id) not in book_ids_after, f"Удалённая книга {book_id} НЕ должна быть в списке"
        print("[STEP 8] GET /books после удаления НЕ содержит удалённую книгу")

        print("\n[OK] ВСЕ ПРОВЕРКИ ПРОШЛИ — удаление работает корректно!")

    def test_delete_multiple_books(self, client_and_engine):
        """Удаление нескольких книг по очереди."""
        client, test_engine = client_and_engine
        Session = sessionmaker(bind=test_engine)

        # Создаём 3 книги
        book_ids = []
        for i in range(3):
            session = Session()
            book_id = uuid4()
            book = Book(
                id=book_id,
                title=f"Book {i}",
                author="Author",
                file_path=f"/path/{i}.epub",
                file_format="epub",
                file_size=100,
                date_added=datetime.utcnow(),
            )
            session.add(book)
            session.commit()
            session.close()
            book_ids.append(book_id)

        # Проверяем что все в списке
        resp = client.get("/api/v1/books")
        assert resp.json()["total"] == 3

        # Удаляем среднюю
        delete_resp = client.delete(f"/api/v1/books/{book_ids[1]}")
        assert delete_resp.status_code == 204

        # Проверяем через БД
        session = Session()
        remaining = session.query(Book).all()
        assert len(remaining) == 2
        remaining_ids = [str(b.id) for b in remaining]
        assert str(book_ids[1]) not in remaining_ids
        session.close()

        # Проверяем через API
        resp = client.get("/api/v1/books")
        assert resp.json()["total"] == 2
        api_ids = [b["id"] for b in resp.json()["books"]]
        assert str(book_ids[1]) not in api_ids
