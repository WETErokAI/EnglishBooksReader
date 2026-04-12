"""
Интеграционные тесты endpoint'а загрузки книг.

Проверяет:
- Успешная загрузка файла (epub)
- Дубликат книги
- Превышение размера файла
- Неподдерживаемый формат
- Повреждённый файл

Важно: тесты используют реальные файлы из tests/fixtures/
"""

import pytest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.models.book import Base
from src.utils.file_validator import MAX_FILE_SIZE


@pytest.fixture
def app():
    """Создать тестовое FastAPI приложение."""
    from app.main import app as main_app
    return main_app


@pytest.fixture
def client(app, db_session, tmp_path):
    """Тестовый клиент с mocked БД и хранилищем."""
    # Patch database dependency
    from app.database import get_db
    from src.utils import storage as storage_module

    def override_get_db():
        yield db_session

    # Patch storage to use temp directory
    books_dir = tmp_path / "books"
    covers_dir = tmp_path / "covers"
    thumbnails_dir = tmp_path / "thumbnails"
    books_dir.mkdir()
    covers_dir.mkdir()
    thumbnails_dir.mkdir()

    original_ensure = storage_module.ensure_storage_directories
    storage_module.ensure_storage_directories = lambda: None

    # Patch book_file_path, cover_path, thumbnail_path generators
    original_book_path = storage_module.generate_book_file_path
    original_cover_path = storage_module.generate_cover_path
    original_thumb_path = storage_module.generate_thumbnail_path

    storage_module.generate_book_file_path = lambda fmt, book_id: str(books_dir / f"{book_id}.{fmt}")
    storage_module.generate_cover_path = lambda book_id: str(covers_dir / f"{book_id}.jpg")
    storage_module.generate_thumbnail_path = lambda book_id: str(thumbnails_dir / f"{book_id}.jpg")

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)

    yield client

    app.dependency_overrides.clear()
    storage_module.ensure_storage_directories = original_ensure
    storage_module.generate_book_file_path = original_book_path
    storage_module.generate_cover_path = original_cover_path
    storage_module.generate_thumbnail_path = original_thumb_path


class TestBookUpload:
    """Тесты POST /api/v1/books/upload."""

    def _create_epub_bytes(self) -> bytes:
        """Создать минимальный валидный EPUB-like ZIP."""
        import zipfile
        buf = BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr("META-INF/container.xml", '<?xml version="1.0"?><container><rootfiles><rootfile full-path="content.opf"/></rootfiles></container>')
            zf.writestr("content.opf", '<?xml version="1.0"?><package version="3.0"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>Test Book</dc:title><dc:creator>Test Author</dc:creator></metadata><manifest><item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/></manifest><spine><itemref idref="ch1"/></spine></package>')
            zf.writestr("ch1.xhtml", '<html><body><h1>Chapter 1</h1><p>Test content.</p></body></html>')
        buf.seek(0)
        return buf.getvalue()

    def test_upload_epub_success(self, client, db_session):
        """Успешная загрузка EPUB файла."""
        epub_content = self._create_epub_bytes()

        with patch("src.controllers.book_controller.BookController") as mock_controller:
            mock_controller.upload.return_value = MagicMock(
                id="550e8400-e29b-41d4-a716-446655440000",
                title="Test Book",
                author="Test Author",
                file_format="epub",
                cover_thumbnail_path=None,
                date_added="2026-04-08T10:30:00Z",
                has_reading_position=False,
            )

            response = client.post(
                "/api/v1/books/upload",
                files={"file": ("test.epub", BytesIO(epub_content), "application/epub+zip")},
            )

            assert response.status_code == 201
            data = response.json()
            assert data["title"] == "Test Book"
            assert data["author"] == "Test Author"
            assert data["file_format"] == "epub"

    def test_upload_unsupported_format(self, client):
        """Загрузка неподдерживаемого формата."""
        response = client.post(
            "/api/v1/books/upload",
            files={"file": ("book.pdf", BytesIO(b"pdf content"), "application/pdf")},
        )

        assert response.status_code in (400, 422)
        data = response.json()
        assert "error" in data or "detail" in data

    def test_upload_oversized_file(self, client):
        """Загрузка файла превышающего лимит."""
        big_content = b"x" * (MAX_FILE_SIZE + 1)

        response = client.post(
            "/api/v1/books/upload",
            files={"file": ("big.epub", BytesIO(big_content), "application/epub+zip")},
        )

        assert response.status_code in (400, 413)

    def test_upload_corrupted_epub(self, client, db_session):
        """Загрузка повреждённого EPUB файла."""
        with patch("src.controllers.book_controller.BookController") as mock_controller:
            mock_controller.upload.side_effect = ValueError("Файл повреждён")

            response = client.post(
                "/api/v1/books/upload",
                files={"file": ("corrupted.epub", BytesIO(b"not a real epub"), "application/epub+zip")},
            )

            assert response.status_code == 422
            data = response.json()
            assert "повреждён" in data.get("error", "").lower() or "error" in data

    def test_upload_duplicate_book(self, client, db_session):
        """Загрузка дубликата книги."""
        epub_content = self._create_epub_bytes()

        with patch("src.controllers.book_controller.BookController") as mock_controller:
            from fastapi import HTTPException
            mock_controller.upload.side_effect = HTTPException(
                status_code=409,
                detail="Книга уже есть в библиотеке",
            )

            response = client.post(
                "/api/v1/books/upload",
                files={"file": ("test.epub", BytesIO(epub_content), "application/epub+zip")},
            )

            assert response.status_code == 409


# === Тесты с реальными файлами из fixtures ===

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
REAL_EPUB_PATH = FIXTURES_DIR / "pg84.epub"
REAL_FB2_PATH = FIXTURES_DIR / "867660.fb2"


@pytest.mark.skipif(not REAL_EPUB_PATH.exists(), reason="Файл fixtures/pg84.epub отсутствует")
class TestRealFileUpload:
    """Интеграционные тесты с реальными файлами.

    Используют настоящие EPUB/FB2 файлы чтобы гарантировать
    работоспособность всего пайплайна загрузки.
    """

    def test_upload_real_epub(self, client, db_session):
        """Загрузка реального EPUB файла (Frankenstein)."""
        epub_content = REAL_EPUB_PATH.read_bytes()

        response = client.post(
            "/api/v1/books/upload",
            files={"file": ("pg84.epub", BytesIO(epub_content), "application/epub+zip")},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Frankenstein; or, the modern prometheus"
        assert data["author"] == "Mary Wollstonecraft Shelley"
        assert data["file_format"] == "epub"

    def test_upload_real_fb2(self, client, db_session):
        """Загрузка реального FB2 файла."""
        fb2_content = REAL_FB2_PATH.read_bytes()

        response = client.post(
            "/api/v1/books/upload",
            files={"file": ("test.fb2", BytesIO(fb2_content), "application/x-fictionbook+xml")},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["file_format"] == "fb2"
