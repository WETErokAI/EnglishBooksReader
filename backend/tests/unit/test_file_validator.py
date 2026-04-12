"""
Unit-тесты утилиты валидации файлов.

Проверяет:
- Валидные форматы (txt, epub, fb2)
- Превышение размера файла
- Неподдерживаемый формат
- Отсутствие имени файла
"""

import pytest
from fastapi import UploadFile, HTTPException
from io import BytesIO

from src.utils.file_validator import (
    validate_file_format,
    validate_file_size,
    validate_upload_file,
    MAX_FILE_SIZE,
)


class TestValidateFileFormat:
    """Тесты validate_file_format."""

    @pytest.mark.parametrize(
        "filename, expected_format",
        [
            ("book.epub", "epub"),
            ("book.EPUB", "epub"),
            ("book.Epub", "epub"),
            ("document.txt", "txt"),
            ("document.TXT", "txt"),
            ("library.fb2", "fb2"),
            ("library.FB2", "fb2"),
            ("path/to/book.epub", "epub"),
        ],
    )
    def test_valid_formats(self, filename: str, expected_format: str):
        """Валидные форматы файлов проходят валидацию."""
        result = validate_file_format(filename)
        assert result == expected_format

    @pytest.mark.parametrize(
        "filename",
        [
            "book.pdf",
            "document.docx",
            "library.mobi",
            "archive.zip",
            "image.png",
            "no_extension",
        ],
    )
    def test_unsupported_format(self, filename: str):
        """Неподдерживаемые форматы вызывают HTTPException 400."""
        with pytest.raises(HTTPException) as exc_info:
            validate_file_format(filename)

        assert exc_info.value.status_code == 400
        assert "Неподдерживаемый формат" in str(exc_info.value.detail)


class TestValidateFileSize:
    """Тесты validate_file_size."""

    def test_exact_max_size(self):
        """Файл ровно 50 МБ проходит валидацию."""
        validate_file_size(MAX_FILE_SIZE)  # Не должно вызывать исключение

    def test_under_max_size(self):
        """Файл меньше 50 МБ проходит валидацию."""
        validate_file_size(MAX_FILE_SIZE - 1)
        validate_file_size(1024)
        validate_file_size(1)

    def test_over_max_size(self):
        """Файл больше 50 МБ вызывает HTTPException 400."""
        with pytest.raises(HTTPException) as exc_info:
            validate_file_size(MAX_FILE_SIZE + 1)

        assert exc_info.value.status_code == 400
        assert "превышает" in str(exc_info.value.detail).lower()

    def test_zero_size(self):
        """Файл нулевого размера проходит валидацию."""
        validate_file_size(0)  # Не должно вызывать исключение


class TestValidateUploadFile:
    """Тесты validate_upload_file (async)."""

    @pytest.mark.asyncio
    async def test_valid_epub_file(self):
        """Валидный EPUB файл проходит валидацию."""
        file = UploadFile(
            filename="test.epub",
            file=BytesIO(b"test content"),
            size=1024,
        )
        result = await validate_upload_file(file)
        assert result == "epub"

    @pytest.mark.asyncio
    async def test_valid_txt_file(self):
        """Валидный TXT файл проходит валидацию."""
        file = UploadFile(
            filename="readme.txt",
            file=BytesIO(b"test content"),
            size=512,
        )
        result = await validate_upload_file(file)
        assert result == "txt"

    @pytest.mark.asyncio
    async def test_valid_fb2_file(self):
        """Валидный FB2 файл проходит валидацию."""
        file = UploadFile(
            filename="book.fb2",
            file=BytesIO(b"test content"),
            size=2048,
        )
        result = await validate_upload_file(file)
        assert result == "fb2"

    @pytest.mark.asyncio
    async def test_unsupported_format_upload(self):
        """Неподдерживаемый формат вызывает HTTPException 400."""
        file = UploadFile(
            filename="book.pdf",
            file=BytesIO(b"test content"),
            size=1024,
        )
        with pytest.raises(HTTPException) as exc_info:
            await validate_upload_file(file)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_oversized_file_upload(self):
        """Файл превышающий 50 МБ вызывает HTTPException 400."""
        file = UploadFile(
            filename="big.epub",
            file=BytesIO(b"test content"),
            size=MAX_FILE_SIZE + 1,
        )
        with pytest.raises(HTTPException) as exc_info:
            await validate_upload_file(file)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_missing_filename(self):
        """Отсутствие имени файла вызывает HTTPException 400."""
        file = UploadFile(
            filename=None,
            file=BytesIO(b"test content"),
        )
        with pytest.raises(HTTPException) as exc_info:
            await validate_upload_file(file)

        assert exc_info.value.status_code == 400
        assert "Имя файла не указано" in str(exc_info.value.detail)
