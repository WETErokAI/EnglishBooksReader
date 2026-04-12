"""
Unit-тесты сервиса чанкинга книг.

Проверяет:
- Разбиение на чанки по главам
- Fallback на фиксированный размер (~5000 слов)
- Генерация HTML чанков
- word_count корректен
"""

import pytest
from pathlib import Path

from src.services.chunking_service import ChunkingService


class TestChunkingService:
    """Тесты ChunkingService."""

    def test_chunk_by_chapters(self):
        """Разбиение текста по главам (заголовки H1/H2)."""
        content = """
<h1>Chapter 1</h1>
<p>First chapter content with some words.</p>
<h1>Chapter 2</h1>
<p>Second chapter content with different words.</p>
<h1>Chapter 3</h1>
<p>Third chapter content here.</p>
"""
        service = ChunkingService()
        chunks = service.chunk_html_content(content)

        assert len(chunks) == 3
        assert "Chapter 1" in chunks[0]["content_html"]
        assert "Chapter 2" in chunks[1]["content_html"]
        assert "Chapter 3" in chunks[2]["content_html"]
        assert chunks[0]["chunk_index"] == 0
        assert chunks[1]["chunk_index"] == 1
        assert chunks[2]["chunk_index"] == 2

    def test_chunk_fallback_by_word_count(self):
        """Fallback: разбиение по ~5000 слов при отсутствии глав."""
        # Создаём текст > 10000 слов без заголовков
        words = ["word"] * 12000
        content = "<p>" + " ".join(words) + "</p>"

        service = ChunkingService()
        chunks = service.chunk_html_content(content)

        # Должно быть разбито минимум на 2 чанка
        assert len(chunks) >= 2
        # Каждый чанк имеет word_count
        for chunk in chunks:
            assert "word_count" in chunk
            assert "content_html" in chunk
            assert "chunk_index" in chunk

    def test_small_content_no_split(self):
        """Маленький текст (< 5000 слов) не разбивается."""
        content = "<p>A short paragraph with few words.</p>"

        service = ChunkingService()
        chunks = service.chunk_html_content(content)

        assert len(chunks) == 1
        assert chunks[0]["chunk_index"] == 0
        assert chunks[0]["word_count"] > 0

    def test_chunk_word_count(self):
        """word_count корректно считается."""
        content = "<p>One two three four five</p>"

        service = ChunkingService()
        chunks = service.chunk_html_content(content)

        assert len(chunks) == 1
        assert chunks[0]["word_count"] == 5

    def test_chunk_indices_sequential(self):
        """Индексы чанков идут последовательно от 0."""
        content = """
<h1>Ch 1</h1><p>Content one.</p>
<h1>Ch 2</h1><p>Content two.</p>
<h1>Ch 3</h1><p>Content three.</p>
<h1>Ch 4</h1><p>Content four.</p>
"""
        service = ChunkingService()
        chunks = service.chunk_html_content(content)

        for i, chunk in enumerate(chunks):
            assert chunk["chunk_index"] == i

    def test_empty_content(self):
        """Пустой контент вызывает ValueError."""
        service = ChunkingService()

        with pytest.raises(ValueError):
            service.chunk_html_content("")

    def test_whitespace_only_content(self):
        """Только пробелы — пустой контент."""
        service = ChunkingService()

        with pytest.raises(ValueError):
            service.chunk_html_content("   \n\n   ")

    def test_html_tags_stripped_for_word_count(self):
        """HTML теги не считаются словами."""
        content = "<p>Hello world</p><div>Foo bar baz</div>"

        service = ChunkingService()
        chunks = service.chunk_html_content(content)

        assert len(chunks) == 1
        # "Hello world Foo bar baz" = 5 слов
        assert chunks[0]["word_count"] == 5
