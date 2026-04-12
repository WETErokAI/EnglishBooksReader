"""
Сервис парсинга EPUB файлов.

Извлечение метаданных:
- title (название книги)
- author (автор)
- cover (обложка)
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import ebooklib
from ebooklib import epub


@dataclass
class BookMetadata:
    """Метаданные книги."""

    title: str
    author: Optional[str] = None
    cover_data: Optional[bytes] = None


class EpubParser:
    """Парсер EPUB файлов."""

    @staticmethod
    def parse(file_path: Path) -> BookMetadata:
        """Извлечь метаданные из EPUB файла.

        Args:
            file_path: Путь к EPUB файлу.

        Returns:
            BookMetadata с извлечёнными метаданными.

        Raises:
            FileNotFoundError: Если файл не найден.
            ValueError: Если файл повреждён.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Файл не найден: {file_path}")

        try:
            book = epub.read_epub(str(file_path))
        except Exception as e:
            raise ValueError(f"Файл повреждён и не может быть обработан: {e}")

        # Извлекаем метаданные
        titles = book.get_metadata("DC", "title")
        creators = book.get_metadata("DC", "creator")

        # Название
        title = titles[0][0] if titles else file_path.stem

        # Автор
        author = ", ".join([c[0] for c in creators]) if creators else None

        # Обложка
        cover_data = EpubParser._extract_cover(book)

        return BookMetadata(title=title, author=author, cover_data=cover_data)

    @staticmethod
    def _extract_cover(book: epub.EpubBook) -> Optional[bytes]:
        """Извлечь обложку из EPUB книги.

        Args:
            book: Объект EPUB книги.

        Returns:
            Байты обложки или None.
        """
        # Ищем обложку по стандартным ID
        for cover_id in ["cover", "Cover", "cover_image", "cover.jpg", "cover.png"]:
            item = book.get_item_with_id(cover_id)
            if item is not None:
                return item.get_content()

        # Ищем среди items с image/* media-type
        for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
            # Пропускаем маленькие иконки
            content = item.get_content()
            if len(content) > 1000:
                return content

        return None
