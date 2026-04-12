"""
Unit-тесты парсера EPUB.

Проверяет:
- Извлечение названия (title)
- Извлечение автора (author)
- Извлечение обложки (cover)
- Обработка повреждённых файлов

Важно: тесты используют реальный EPUB файл из fixtures/pg84.epub
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.services.epub_parser import EpubParser, BookMetadata

# Путь к тестовому файлу — реальный EPUB (pg84: Frankenstein)
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
REAL_EPUB_PATH = FIXTURES_DIR / "pg84.epub"


class TestEpubParser:
    """Тесты EpubParser."""

    def test_extract_title_success(self, tmp_path: Path):
        """Корректное извлечение названия книги."""
        epub_file = tmp_path / "test.epub"
        epub_file.write_bytes(b"fake epub content")

        mock_book = MagicMock()
        mock_book.get_metadata.return_value = {
            "DC": {"title": ["The Great Gatsby"]}
        }

        with patch("src.services.epub_parser.EpubBook.read_epub") as mock_read:
            mock_read.return_value = mock_book
            metadata = EpubParser.parse(epub_file)

        assert metadata.title == "The Great Gatsby"

    def test_extract_author_success(self, tmp_path: Path):
        """Корректное извлечение автора книги."""
        epub_file = tmp_path / "test.epub"
        epub_file.write_bytes(b"fake epub content")

        mock_book = MagicMock()
        mock_book.get_metadata.return_value = {
            "DC": {
                "title": ["Test Book"],
                "creator": ["F. Scott Fitzgerald"],
            }
        }

        with patch("src.services.epub_parser.EpubBook.read_epub") as mock_read:
            mock_read.return_value = mock_book
            metadata = EpubParser.parse(epub_file)

        assert metadata.author == "F. Scott Fitzgerald"

    def test_extract_multiple_authors(self, tmp_path: Path):
        """Извлечение нескольких авторов."""
        epub_file = tmp_path / "test.epub"
        epub_file.write_bytes(b"fake epub content")

        mock_book = MagicMock()
        mock_book.get_metadata.return_value = {
            "DC": {
                "title": ["Test Book"],
                "creator": ["Author One", "Author Two"],
            }
        }

        with patch("src.services.epub_parser.EpubBook.read_epub") as mock_read:
            mock_read.return_value = mock_book
            metadata = EpubParser.parse(epub_file)

        assert metadata.author == "Author One, Author Two"

    def test_missing_title_falls_back_to_filename(self, tmp_path: Path):
        """При отсутствии названия используется имя файла."""
        epub_file = tmp_path / "my_novel.epub"
        epub_file.write_bytes(b"fake epub content")

        mock_book = MagicMock()
        mock_book.get_metadata.return_value = {
            "DC": {"title": []}
        }

        with patch("src.services.epub_parser.EpubBook.read_epub") as mock_read:
            mock_read.return_value = mock_book
            metadata = EpubParser.parse(epub_file)

        assert metadata.title == "my_novel"

    def test_missing_author_is_none(self, tmp_path: Path):
        """При отсутствии автора возвращается None."""
        epub_file = tmp_path / "test.epub"
        epub_file.write_bytes(b"fake epub content")

        mock_book = MagicMock()
        mock_book.get_metadata.return_value = {
            "DC": {"title": ["Test Book"]}
        }

        with patch("src.services.epub_parser.EpubBook.read_epub") as mock_read:
            mock_read.return_value = mock_book
            metadata = EpubParser.parse(epub_file)

        assert metadata.author is None

    def test_extract_cover_image(self, tmp_path: Path):
        """Извлечение обложки из EPUB."""
        epub_file = tmp_path / "test.epub"
        epub_file.write_bytes(b"fake epub content")
        cover_data = b"fake cover image data"

        mock_book = MagicMock()
        mock_book.get_metadata.return_value = {
            "DC": {"title": ["Test Book"]}
        }
        mock_item = MagicMock()
        mock_item.get_content.return_value = cover_data
        mock_book.get_item_with_id.return_value = mock_item

        with patch("src.services.epub_parser.EpubBook.read_epub") as mock_read:
            mock_read.return_value = mock_book
            metadata = EpubParser.parse(epub_file)

        assert metadata.cover_data == cover_data

    def test_no_cover_image(self, tmp_path: Path):
        """EPUB без обложки — cover_data is None."""
        epub_file = tmp_path / "test.epub"
        epub_file.write_bytes(b"fake epub content")

        mock_book = MagicMock()
        mock_book.get_metadata.return_value = {
            "DC": {"title": ["Test Book"]}
        }
        mock_book.get_item_with_id.return_value = None

        with patch("src.services.epub_parser.EpubBook.read_epub") as mock_read:
            mock_read.return_value = mock_book
            metadata = EpubParser.parse(epub_file)

        assert metadata.cover_data is None

    def test_corrupted_epub_file(self, tmp_path: Path):
        """Повреждённый EPUB файл вызывает ValueError."""
        epub_file = tmp_path / "corrupted.epub"
        epub_file.write_bytes(b"not a real epub")

        with patch("src.services.epub_parser.EpubBook.read_epub") as mock_read:
            mock_read.side_effect = Exception("Invalid EPUB file")
            with pytest.raises(ValueError) as exc_info:
                EpubParser.parse(epub_file)

        assert "повреждён" in str(exc_info.value).lower() or "corrupted" in str(exc_info.value).lower()

    def test_nonexistent_file(self):
        """Несуществующий файл вызывает FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            EpubParser.parse(Path("/nonexistent/book.epub"))


@pytest.mark.skipif(not REAL_EPUB_PATH.exists(), reason="Файл fixtures/pg84.epub отсутствует")
class TestEpubParserRealFile:
    """Тесты с реальным EPUB файлом (pg84: Frankenstein by Mary Shelley).

    Эти тесты гарантируют что парсер работает с настоящими EPUB файлами,
    а не только с моками. Файл pg84.epub — это «Франкенштейн» Мэри Шелли
    из проекта Гутенберг.

    Природа известных ошибок:
    - ebooklib.get_metadata(namespace, name) принимает СТРОКУ как второй аргумент,
      НЕ dict. Вызов get_metadata('DC', {}) вызывает TypeError: unhashable type: 'dict'.
      Это НЕочевидно из документации ebooklib.
    """

    def test_real_epub_title(self):
        """Реальный EPUB — корректное извлечение названия."""
        meta = EpubParser.parse(REAL_EPUB_PATH)
        assert meta.title == "Frankenstein; or, the modern prometheus"

    def test_real_epub_author(self):
        """Реальный EPUB — корректное извлечение автора."""
        meta = EpubParser.parse(REAL_EPUB_PATH)
        assert meta.author == "Mary Wollstonecraft Shelley"

    def test_real_epub_has_cover(self):
        """Реальный EPUB — обложка извлечена."""
        meta = EpubParser.parse(REAL_EPUB_PATH)
        assert meta.cover_data is not None
        assert len(meta.cover_data) > 10000  # Реальная обложка > 10KB

