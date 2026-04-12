"""
Unit-тесты парсера FB2.

Проверяет:
- Извлечение названия (title)
- Извлечение автора (author)
- Извлечение обложки (cover)
- Обработка повреждённых файлов

Важно: тесты используют реальный FB2 файл из fixtures/867660.fb2
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.services.fb2_parser import Fb2Parser, BookMetadata

# Путь к тестовому FB2 файлу
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
REAL_FB2_PATH = FIXTURES_DIR / "867660.fb2"


class TestFb2Parser:
    """Тесты Fb2Parser."""

    def test_extract_title_success(self, tmp_path: Path):
        """Корректное извлечение названия книги."""
        fb2_file = tmp_path / "test.fb2"
        fb2_content = b'<?xml version="1.0"?><FictionBook><description><title-info><book-title>War and Peace</book-title></title-info></description></FictionBook>'
        fb2_file.write_bytes(fb2_content)

        metadata = Fb2Parser.parse(fb2_file)

        assert metadata.title == "War and Peace"

    def test_extract_author_success(self, tmp_path: Path):
        """Корректное извлечение автора книги."""
        fb2_file = tmp_path / "test.fb2"
        fb2_content = b'<?xml version="1.0"?><FictionBook><description><title-info><book-title>Test</book-title><author><first-name>Leo</first-name><last-name>Tolstoy</last-name></author></title-info></description></FictionBook>'
        fb2_file.write_bytes(fb2_content)

        metadata = Fb2Parser.parse(fb2_file)

        assert "Tolstoy" in metadata.author or "Leo" in metadata.author

    def test_missing_title_falls_back_to_filename(self, tmp_path: Path):
        """При отсутствии названия используется имя файла."""
        fb2_file = tmp_path / "my_novel.fb2"
        fb2_content = b'<?xml version="1.0"?><FictionBook><description><title-info></title-info></description></FictionBook>'
        fb2_file.write_bytes(fb2_content)

        metadata = Fb2Parser.parse(fb2_file)

        assert metadata.title == "my_novel"

    def test_missing_author_is_none(self, tmp_path: Path):
        """При отсутствии автора возвращается None."""
        fb2_file = tmp_path / "test.fb2"
        fb2_content = b'<?xml version="1.0"?><FictionBook><description><title-info><book-title>Test Book</book-title></title-info></description></FictionBook>'
        fb2_file.write_bytes(fb2_content)

        metadata = Fb2Parser.parse(fb2_file)

        assert metadata.author is None

    def test_extract_cover_image(self, tmp_path: Path):
        """Извлечение обложки из FB2."""
        fb2_file = tmp_path / "test.fb2"
        # FB2 с binary секцией для обложки
        fb2_content = b'''<?xml version="1.0"?>
<FictionBook>
<description>
<title-info>
<book-title>Test Book</book-title>
<coverpage>
<image href="#cover_image"/>
</coverpage>
</title-info>
</description>
<binary id="cover_image" content-type="image/jpeg">ZmFrZSBpbWFnZQ==</binary>
</FictionBook>'''
        fb2_file.write_bytes(fb2_content)

        metadata = Fb2Parser.parse(fb2_file)

        assert metadata.cover_data is not None

    def test_no_cover_image(self, tmp_path: Path):
        """FB2 без обложки — cover_data is None."""
        fb2_file = tmp_path / "test.fb2"
        fb2_content = b'<?xml version="1.0"?><FictionBook><description><title-info><book-title>Test Book</book-title></title-info></description></FictionBook>'
        fb2_file.write_bytes(fb2_content)

        metadata = Fb2Parser.parse(fb2_file)

        assert metadata.cover_data is None

    def test_corrupted_fb2_file(self, tmp_path: Path):
        """Повреждённый FB2 файл вызывает ValueError."""
        fb2_file = tmp_path / "corrupted.fb2"
        fb2_file.write_bytes(b"not xml at all <<<>>>")

        with pytest.raises(ValueError) as exc_info:
            Fb2Parser.parse(fb2_file)

        assert "повреждён" in str(exc_info.value).lower() or "corrupted" in str(exc_info.value).lower()

    def test_nonexistent_file(self):
        """Несуществующий файл вызывает FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            Fb2Parser.parse(Path("/nonexistent/book.fb2"))


@pytest.mark.skipif(not REAL_FB2_PATH.exists(), reason="Файл fixtures/867660.fb2 отсутствует")
class TestFb2ParserRealFile:
    """Тесты с реальным FB2 файлом.

    Эти тесты гарантируют что парсер работает с настоящими FB2 файлами.
    """

    def test_real_fb2_title(self):
        """Реальный FB2 — корректное извлечение названия."""
        meta = Fb2Parser.parse(REAL_FB2_PATH)
        assert meta.title is not None
        assert len(meta.title) > 0

    def test_real_fb2_metadata_present(self):
        """Реальный FB2 — метаданные извлечены."""
        meta = Fb2Parser.parse(REAL_FB2_PATH)
        # title и author могут быть None в зависимости от файла,
        # но парсер не должен падать
        assert meta is not None
