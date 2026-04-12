"""
Сервис парсинга FB2 файлов.

Извлечение метаданных через lxml XML parsing:
- title (название книги)
- author (автор)
- cover (обложка из binary секций)
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import base64

from lxml import etree


@dataclass
class BookMetadata:
    """Метаданные книги."""

    title: str
    author: Optional[str] = None
    cover_data: Optional[bytes] = None


class Fb2Parser:
    """Парсер FB2 файлов."""

    # Namespace FB2
    _NS = {
        "fb": "http://www.gribuser.ru/xml/fictionbook/2.0",
        "xlink": "http://www.w3.org/1999/xlink",
    }

    @staticmethod
    def parse(file_path: Path) -> BookMetadata:
        """Извлечь метаданные из FB2 файла.

        Args:
            file_path: Путь к FB2 файлу.

        Returns:
            BookMetadata с извлечёнными метаданными.

        Raises:
            FileNotFoundError: Если файл не найден.
            ValueError: Если файл повреждён.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Файл не найден: {file_path}")

        try:
            tree = etree.parse(str(file_path))
            root = tree.getroot()
        except etree.XMLSyntaxError as e:
            raise ValueError(f"Файл повреждён и не может быть обработан: {e}")

        # Определяем namespace из root
        ns = Fb2Parser._get_namespace(root)
        ns_map = {"fb": ns} if ns else Fb2Parser._NS

        # Название
        title = Fb2Parser._extract_title(root, ns_map)
        if not title:
            title = file_path.stem

        # Автор
        author = Fb2Parser._extract_author(root, ns_map)

        # Обложка
        cover_data = Fb2Parser._extract_cover(root, tree, ns_map)

        return BookMetadata(title=title, author=author, cover_data=cover_data)

    @staticmethod
    def _get_namespace(root) -> Optional[str]:
        """Определить namespace из root элемента."""
        tag = root.tag
        if tag.startswith("{"):
            return tag.split("}")[0].strip("{")
        return None

    @staticmethod
    def _extract_title(root, ns_map: dict) -> Optional[str]:
        """Извлечь название книги."""
        # Пробуем с namespace
        for path in [
            ".//fb:title-info/fb:book-title",
            ".//fb:book-title",
            ".//title-info/book-title",
            ".//book-title",
        ]:
            try:
                elements = root.xpath(path, namespaces=ns_map)
                if elements:
                    return elements[0].text.strip()
            except etree.XPathEvalError:
                continue

        # Без namespace fallback
        for elem in root.iter():
            if elem.tag.endswith("book-title"):
                return elem.text.strip() if elem.text else None

        return None

    @staticmethod
    def _extract_author(root, ns_map: dict) -> Optional[str]:
        """Извлечь автора книги."""
        authors = []

        for path in [
            ".//fb:title-info/fb:author",
            ".//fb:author",
            ".//title-info/author",
            ".//author",
        ]:
            try:
                author_elements = root.xpath(path, namespaces=ns_map)
                if author_elements:
                    for author_elem in author_elements:
                        parts = []
                        for tag in ["fb:first-name", "fb:middle-name", "fb:last-name",
                                    "first-name", "middle-name", "last-name"]:
                            # Попробуем с namespace и без
                            for prefix in ["fb:", ""]:
                                try:
                                    names = author_elem.xpath(f"{prefix}{tag}", namespaces=ns_map)
                                    if names:
                                        parts.append(names[0].text.strip())
                                        break
                                except etree.XPathEvalError:
                                    continue
                            # Без namespace fallback
                            if not parts:
                                for child in author_elem.iter():
                                    if child.tag.endswith(tag.split(":")[-1]):
                                        if child.text and child.text.strip():
                                            parts.append(child.text.strip())

                        if parts:
                            authors.append(" ".join(parts))
                    break
            except etree.XPathEvalError:
                continue

        return ", ".join(authors) if authors else None

    @staticmethod
    def _extract_cover(root, tree, ns_map: dict) -> Optional[bytes]:
        """Извлечь обложку из FB2."""
        # Ищем ссылку на обложку
        cover_href = None
        for path in [
            ".//fb:title-info/fb:coverpage/fb:image",
            ".//fb:coverpage/fb:image",
            ".//title-info/coverpage/image",
            ".//coverpage/image",
        ]:
            try:
                images = root.xpath(path, namespaces=ns_map)
                if images:
                    href = images[0].get("{http://www.w3.org/1999/xlink}href") or images[0].get("href")
                    if href:
                        cover_href = href.lstrip("#")
                    break
            except (etree.XPathEvalError, KeyError):
                continue

        if not cover_href:
            return None

        # Ищем binary с этим id
        for path in [
            f'//fb:binary[@id="{cover_href}"]',
            f'//binary[@id="{cover_href}"]',
        ]:
            try:
                binaries = root.xpath(path, namespaces=ns_map)
                if not binaries:
                    # Без namespace
                    for elem in root.iter():
                        if elem.tag.endswith("binary") and elem.get("id") == cover_href:
                            data = elem.text
                            if data:
                                return base64.b64decode(data)
                else:
                    data = binaries[0].text
                    if data:
                        return base64.b64decode(data)
            except (etree.XPathEvalError, Exception):
                continue

        return None
