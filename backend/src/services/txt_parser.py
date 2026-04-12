"""
Сервис парсинга TXT файлов.

TXT файлы не содержат метаданных:
- title извлекается из имени файла
- author всегда None
- cover всегда None
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class BookMetadata:
    """Метаданные книги."""

    title: str
    author: Optional[str] = None
    cover_data: Optional[bytes] = None


class TxtParser:
    """Парсер TXT файлов."""

    @staticmethod
    def parse(file_path: Path) -> BookMetadata:
        """Извлечь метаданные из TXT файла.

        Args:
            file_path: Путь к TXT файлу.

        Returns:
            BookMetadata с названием из имени файла.

        Raises:
            FileNotFoundError: Если файл не найден.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Файл не найден: {file_path}")

        # Название из имени файла (без расширения)
        title = file_path.stem

        return BookMetadata(title=title, author=None, cover_data=None)
