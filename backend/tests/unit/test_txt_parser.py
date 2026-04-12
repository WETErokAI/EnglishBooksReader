"""
Unit-тесты парсера TXT.

Проверяет:
- Название из имени файла
- Отсутствие автора
- Отсутствие обложки
"""

import pytest
from pathlib import Path

from src.services.txt_parser import TxtParser, BookMetadata


class TestTxtParser:
    """Тесты TxtParser."""

    def test_title_from_filename(self, tmp_path: Path):
        """Название книги извлекается из имени файла."""
        txt_file = tmp_path / "adventure_story.txt"
        txt_file.write_text("Some text content here")

        metadata = TxtParser.parse(txt_file)

        assert metadata.title == "adventure_story"

    def test_author_is_none(self, tmp_path: Path):
        """TXT файлы не имеют автора — возвращается None."""
        txt_file = tmp_path / "readme.txt"
        txt_file.write_text("Content")

        metadata = TxtParser.parse(txt_file)

        assert metadata.author is None

    def test_cover_data_is_none(self, tmp_path: Path):
        """TXT файлы не имеют обложки — cover_data is None."""
        txt_file = tmp_path / "notes.txt"
        txt_file.write_text("Some notes")

        metadata = TxtParser.parse(txt_file)

        assert metadata.cover_data is None

    def test_empty_txt_file(self, tmp_path: Path):
        """Пустой TXT файл — название из filename, остальное None."""
        txt_file = tmp_path / "empty.txt"
        txt_file.write_text("")

        metadata = TxtParser.parse(txt_file)

        assert metadata.title == "empty"
        assert metadata.author is None
        assert metadata.cover_data is None

    def test_filename_with_special_chars(self, tmp_path: Path):
        """Имя файла с символами-разделителями корректно обрабатывается."""
        txt_file = tmp_path / "my--book__title.txt"
        txt_file.write_text("Content")

        metadata = TxtParser.parse(txt_file)

        assert metadata.title == "my--book__title"

    def test_nonexistent_file(self):
        """Несуществующий файл вызывает FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            TxtParser.parse(Path("/nonexistent/file.txt"))
