"""
Утилита валидации файлов.

Проверка:
- Поддерживаемые форматы: txt, epub, fb2
- Максимальный размер: 50 МБ (52,428,800 байт)
"""

from pathlib import Path

from fastapi import UploadFile, HTTPException

# Поддерживаемые форматы
SUPPORTED_FORMATS = {"txt", "epub", "fb2"}

# Максимальный размер файла: 50 МБ
MAX_FILE_SIZE = 50 * 1024 * 1024  # 52,428,800 байт


def validate_file_format(filename: str) -> str:
    """Проверить формат файла.

    Args:
        filename: Имя файла с расширением.

    Returns:
        Нормализованный формат файла (lowercase).

    Raises:
        HTTPException: Если формат не поддерживается.
    """
    file_extension = Path(filename).suffix.lstrip(".").lower()
    if file_extension not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый формат файла: {file_extension}. "
                   f"Поддерживаемые форматы: {', '.join(sorted(SUPPORTED_FORMATS))}",
        )
    return file_extension


def validate_file_size(file_size: int) -> None:
    """Проверить размер файла.

    Args:
        file_size: Размер файла в байтах.

    Raises:
        HTTPException: Если размер превышает 50 МБ.
    """
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Размер файла превышает допустимый лимит (50 МБ). "
                   f"Текущий размер: {file_size / (1024 * 1024):.2f} МБ",
        )


async def validate_upload_file(file: UploadFile) -> str:
    """Полная валидация загружаемого файла.

    Args:
        file: Загружаемый файл из FastAPI.

    Returns:
        Нормализованный формат файла.

    Raises:
        HTTPException: Если валидация не прошла.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Имя файла не указано")

    # Проверяем формат
    file_format = validate_file_format(file.filename)

    # Проверяем размер (если известен)
    if file.size is not None:
        validate_file_size(file.size)

    return file_format
