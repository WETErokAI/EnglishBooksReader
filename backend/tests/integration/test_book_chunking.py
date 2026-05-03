"""
Интеграционный тест создания чанков при загрузке книги.

Проверяет:
1. Загрузка EPUB файла через API
2. Проверка что чанки созданы в БД
3. Проверка что API /books/{id}/chunks возвращает чанки
"""

import pytest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch, MagicMock
from sqlalchemy import text

from fastapi.testclient import TestClient


@pytest.fixture
def app():
    """Создать тестовое FastAPI приложение."""
    from app.main import app as main_app
    return main_app


@pytest.fixture
def client(app, db_session, tmp_path):
    """Тестовый клиент с mocked БД и хранилищем."""
    from app.database import get_db
    from src.utils import storage as storage_module

    def override_get_db():
        yield db_session

    # Патчим storage
    books_dir = tmp_path / "books"
    covers_dir = tmp_path / "covers"
    thumbnails_dir = tmp_path / "thumbnails"
    books_dir.mkdir()
    covers_dir.mkdir()
    thumbnails_dir.mkdir()

    storage_module.ensure_storage_directories = lambda: None
    storage_module.generate_book_file_path = lambda fmt, book_id: str(books_dir / f"{book_id}.{fmt}")
    storage_module.generate_cover_path = lambda book_id: str(covers_dir / f"{book_id}.jpg")
    storage_module.generate_thumbnail_path = lambda book_id: str(thumbnails_dir / f"{book_id}.jpg")

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)

    yield client

    app.dependency_overrides.clear()


def _create_epub_with_multiple_chapters() -> bytes:
    """Создать EPUB с несколькими главами для тестирования чанкинга.

    Структура соответствует валидному EPUB:
    - mimetype: без сжатия (STORED), первый файл в архиве
    - META-INF/container.xml: указывает на content.opf
    - OEBPS/content.opf: манифест и структура книги
    - OEBPS/ch*.xhtml: HTML-главы
    """
    import zipfile

    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_STORED) as zf:
        # mimetype — ОБЯЗАТЕЛЬНО без сжатия (compress_type=0)
        zf.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip")

        zf.writestr("META-INF/container.xml",
            '<?xml version="1.0"?>'
            '<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">'
            '<rootfiles>'
            '<rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>'
            '</rootfiles></container>')
        zf.writestr("OEBPS/content.opf",
            '<?xml version="1.0"?>'
            '<package version="3.0" unique-id="uid" '
            'xmlns="http://www.idpf.org/2007/opf">'
            '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
            '<dc:identifier id="uid">urn:uuid:test</dc:identifier>'
            '<dc:title>Test Book With Chapters</dc:title>'
            '<dc:creator>Test Author</dc:creator>'
            '</metadata>'
            '<manifest>'
            '<item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>'
            '<item id="ch2" href="ch2.xhtml" media-type="application/xhtml+xml"/>'
            '<item id="ch3" href="ch3.xhtml" media-type="application/xhtml+xml"/>'
            '</manifest>'
            '<spine><itemref idref="ch1"/><itemref idref="ch2"/><itemref idref="ch3"/></spine>'
            '</package>')
        zf.writestr("OEBPS/ch1.xhtml",
            '<html xmlns="http://www.w3.org/1999/xhtml">'
            '<head><title>Chapter 1</title></head>'
            '<body><h1>Chapter 1: The Beginning</h1>'
            '<p>This is the first chapter. It contains some content to test chunking.</p>'
            '<p>More content here to make it interesting and longer.</p>'
            '</body></html>')
        zf.writestr("OEBPS/ch2.xhtml",
            '<html xmlns="http://www.w3.org/1999/xhtml">'
            '<head><title>Chapter 2</title></head>'
            '<body><h1>Chapter 2: The Journey</h1>'
            '<p>This is the second chapter. It continues the story.</p>'
            '<p>More content here to test chunking functionality.</p>'
            '</body></html>')
        zf.writestr("OEBPS/ch3.xhtml",
            '<html xmlns="http://www.w3.org/1999/xhtml">'
            '<head><title>Chapter 3</title></head>'
            '<body><h1>Chapter 3: The End</h1>'
            '<p>This is the final chapter. The story comes to an end.</p>'
            '<p>Thank you for reading this test book.</p>'
            '</body></html>')
    buf.seek(0)
    return buf.getvalue()


def _create_minimal_epub() -> bytes:
    """Создать минимальный валидный EPUB файл.

    Структура соответствует валидному EPUB:
    - mimetype: без сжатия (STORED)
    - content.opf в поддиректории OEBPS
    """
    import zipfile

    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_STORED) as zf:
        # mimetype — ОБЯЗАТЕЛЬНО без сжатия (compress_type=0)
        zf.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip")

        zf.writestr("META-INF/container.xml",
            '<?xml version="1.0"?>'
            '<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">'
            '<rootfiles>'
            '<rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>'
            '</rootfiles></container>')
        zf.writestr("OEBPS/content.opf",
            '<?xml version="1.0"?>'
            '<package version="3.0" unique-id="uid" '
            'xmlns="http://www.idpf.org/2007/opf">'
            '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
            '<dc:identifier id="uid">urn:uuid:test</dc:identifier>'
            '<dc:title>Test Book</dc:title>'
            '<dc:creator>Test Author</dc:creator>'
            '</metadata>'
            '<manifest><item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/></manifest>'
            '<spine><itemref idref="ch1"/></spine>'
            '</package>')
        zf.writestr("OEBPS/ch1.xhtml",
            '<html xmlns="http://www.w3.org/1999/xhtml">'
            '<body><h1>Chapter 1</h1><p>Test content.</p></body></html>')
    buf.seek(0)
    return buf.getvalue()


class TestBookChunkingOnUpload:
    """Тесты создания чанков при загрузке книги."""

    def test_upload_epub_creates_chunks(self, client, db_session, tmp_path):
        """Загрузка EPUB должна создать чанки в БД."""
        epub_content = _create_epub_with_multiple_chapters()

        response = client.post(
            "/api/v1/books/upload",
            files={"file": ("test_chapters.epub", BytesIO(epub_content), "application/epub+zip")},
        )

        assert response.status_code == 201
        data = response.json()
        book_id = data["id"]

        # Проверяем что чанки созданы в БД
        chunks_count = db_session.execute(
            text("SELECT COUNT(*) FROM book_chunks WHERE book_id = :book_id"),
            {"book_id": book_id}
        ).scalar()

        assert chunks_count > 0, f"Ожидалось > 0 чанков, но получено {chunks_count}"
        print(f"Создано чанков: {chunks_count}")

    def test_upload_epub_chunks_retrievable_via_api(self, client, db_session, tmp_path):
        """Чанки должны быть доступны через API /books/{id}/chunks."""
        epub_content = _create_epub_with_multiple_chapters()

        # Загружаем книгу
        upload_response = client.post(
            "/api/v1/books/upload",
            files={"file": ("test_chapters.epub", BytesIO(epub_content), "application/epub+zip")},
        )

        assert upload_response.status_code == 201
        book_id = upload_response.json()["id"]

        # Получаем чанки через API
        chunks_response = client.get(f"/api/v1/books/{book_id}/chunks")
        assert chunks_response.status_code == 200
        chunks_data = chunks_response.json()

        assert chunks_data["total_chunks"] > 0, "Ожидалось > 0 чанков в API ответе"
        assert len(chunks_data["chunks"]) == chunks_data["total_chunks"]
        print(f"API вернул {chunks_data['total_chunks']} чанков")

    def test_upload_minimal_epub_creates_at_least_one_chunk(self, client, db_session, tmp_path):
        """Минимальный EPUB должен создать хотя бы один чанк."""
        epub_content = _create_minimal_epub()

        response = client.post(
            "/api/v1/books/upload",
            files={"file": ("test_minimal.epub", BytesIO(epub_content), "application/epub+zip")},
        )

        assert response.status_code == 201
        data = response.json()
        book_id = data["id"]

        # Проверяем что чанки созданы в БД
        chunks_count = db_session.execute(
            text("SELECT COUNT(*) FROM book_chunks WHERE book_id = :book_id"),
            {"book_id": book_id}
        ).scalar()

        assert chunks_count >= 1, f"Ожидалось >= 1 чанк, но получено {chunks_count}"
        print(f"Создано чанков для минимального EPUB: {chunks_count}")

    def test_upload_epub_chunk_content_not_empty(self, client, db_session, tmp_path):
        """Содержимое чанков не должно быть пустым."""
        epub_content = _create_epub_with_multiple_chapters()

        response = client.post(
            "/api/v1/books/upload",
            files={"file": ("test_content.epub", BytesIO(epub_content), "application/epub+zip")},
        )

        assert response.status_code == 201
        book_id = response.json()["id"]

        # Получаем чанки через API
        chunks_response = client.get(f"/api/v1/books/{book_id}/chunks")
        assert chunks_response.status_code == 200
        chunks_data = chunks_response.json()

        # Проверяем что у каждого чанка есть content_html
        for chunk in chunks_data["chunks"]:
            assert chunk["content_html"], f"Чанк {chunk['chunk_index']} имеет пустой content_html"
            assert chunk["word_count"] > 0, f"Чанк {chunk['chunk_index']} имеет word_count=0"

        print(f"Все {len(chunks_data['chunks'])} чанков содержат контент")
