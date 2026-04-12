"""
Сервис чанкинга книг.

Разбиение HTML контента на чанки:
- По главам (H1/H2 заголовки)
- Fallback на фиксированный размер (~5000 слов)
"""

import re
from typing import Optional

# Целевой размер чанка в словах
TARGET_CHUNK_SIZE = 5000


class ChunkingService:
    """Сервис разбиения текста на чанки."""

    def chunk_html_content(self, content: str) -> list[dict]:
        """Разбить HTML контент на чанки.

        Args:
            content: HTML строка с контентом книги.

        Returns:
            Список чанков с полями chunk_index, content_html, word_count.

        Raises:
            ValueError: Если контент пустой или только пробелы.
        """
        if not content or not content.strip():
            raise ValueError("Контент пустой")

        # Пробуем разбить по главам
        chunks = self._chunk_by_chapters(content)

        if not chunks:
            # Fallback: разбиение по размеру
            chunks = self._chunk_by_word_count(content)

        return chunks

    def _chunk_by_chapters(self, content: str) -> list[dict]:
        """Разбить текст по главам (H1/H2 заголовки).

        Args:
            content: HTML контент.

        Returns:
            Список чанков или пустой список если нет глав.
        """
        # Ищем H1 или H2 заголовки
        chapter_pattern = re.compile(r"<h[12][^>]*>.*?</h[12]>", re.IGNORECASE | re.DOTALL)
        matches = list(chapter_pattern.finditer(content))

        if len(matches) < 2:
            # Меньше 2 глав — не разбиваем
            if matches:
                # Одна глава — возвращаем как один чанк
                word_count = self._count_words(content)
                return [{"chunk_index": 0, "content_html": content, "word_count": word_count}]
            return []

        chunks = []
        for i, match in enumerate(matches):
            # Берём контент от текущего заголовка до следующего
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            chapter_content = content[start:end].strip()

            if chapter_content:
                word_count = self._count_words(chapter_content)
                chunks.append({
                    "chunk_index": i,
                    "content_html": chapter_content,
                    "word_count": word_count,
                })

        return chunks

    def _chunk_by_word_count(self, content: str) -> list[dict]:
        """Разбить текст по целевому размеру слов.

        Args:
            content: HTML контент.

        Returns:
            Список чанков.
        """
        total_words = self._count_words(content)

        if total_words <= TARGET_CHUNK_SIZE:
            return [{"chunk_index": 0, "content_html": content, "word_count": total_words}]

        # Простое разбиение по тегам <p>
        paragraphs = re.split(r"(</p>)", content)
        chunks = []
        current_html = ""
        current_words = 0
        chunk_index = 0

        for i, part in enumerate(paragraphs):
            if not part.strip():
                continue

            part_words = self._count_words(part)

            if current_words + part_words > TARGET_CHUNK_SIZE and current_html:
                # Завершаем текущий чанк
                chunks.append({
                    "chunk_index": chunk_index,
                    "content_html": current_html.strip(),
                    "word_count": current_words,
                })
                chunk_index += 1
                current_html = part
                current_words = part_words
            else:
                current_html += part
                current_words += part_words

        # Добавляем последний чанк
        if current_html.strip():
            chunks.append({
                "chunk_index": chunk_index,
                "content_html": current_html.strip(),
                "word_count": current_words,
            })

        return chunks

    @staticmethod
    def _count_words(html: str) -> int:
        """Посчитать слова в HTML строке (без тегов).

        Args:
            html: HTML строка.

        Returns:
            Количество слов.
        """
        # Удаляем HTML теги
        text = re.sub(r"<[^>]+>", "", html)
        # Считаем слова
        return len(text.split())
