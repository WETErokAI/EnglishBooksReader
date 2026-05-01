"""
BookService — бизнес-логика загрузки книг.

Оркестрация процесса:
1. Валидация файла
2. Парсинг метаданных (epub/fb2/txt)
3. Обработка обложки
4. Чанкинг контента
5. Сохранение в БД
6. Проверка на дубликаты
"""

import logging
import uuid
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from src.models.book import Book, BookChunk
from src.schemas.book import BookDTO
from src.repositories.book_repository import BookRepository
from src.utils.file_validator import validate_upload_file, validate_file_size, MAX_FILE_SIZE
from src.utils.storage import generate_book_file_path, generate_cover_path, generate_thumbnail_path
from src.services.epub_parser import EpubParser
from src.services.fb2_parser import Fb2Parser
from src.services.txt_parser import TxtParser
from src.services.cover_processor import CoverProcessor
from src.services.chunking_service import ChunkingService


class BookService:
    """Сервис управления книгами."""

    def __init__(self, db_session: Session):
        """Инициализация сервиса.

        Args:
            db_session: Сессия базы данных.
        """
        self.db = db_session
        self.repository = BookRepository(db_session)
        self.chunking_service = ChunkingService()

    async def upload_book(self, file: UploadFile) -> BookDTO:
        """Загрузить книгу из файла.

        Args:
            file: Загружаемый файл.

        Returns:
            BookDTO с данными загруженной книги.

        Raises:
            HTTPException: При ошибках валидации, дубликата или обработки.
        """
        # 1. Валидация файла
        file_format = await validate_upload_file(file)

        # 2. Чтение содержимого
        content = await file.read()
        file_size = len(content)
        validate_file_size(file_size)

        # 3. Парсинг метаданных
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=f".{file_format}", delete=False) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        try:
            # Парсим метаданные
            metadata = self._parse_metadata(tmp_path, file_format)

            # 4. Проверка на дубликат
            duplicate = self.repository.check_duplicate(metadata.title, metadata.author)
            if duplicate:
                raise HTTPException(
                    status_code=409,
                    detail="Книга уже есть в библиотеке",
                    headers={"X-Existing-Book-Id": str(duplicate.id)},
                )

            # 5. Создание записи книги
            book_id = uuid.uuid4()
            book_file_path = generate_book_file_path(book_id, file.filename or "unknown")

            # Сохраняем файл книги
            book_file_path.parent.mkdir(parents=True, exist_ok=True)
            book_file_path.write_bytes(content)

            # 6. Обработка обложки
            cover_path_str: Optional[str] = None
            thumbnail_path_str: Optional[str] = None

            if metadata.cover_data:
                from app.config import settings
                cover_path = generate_cover_path(book_id)
                thumbnail_path = generate_thumbnail_path(book_id)
                covers_base_path = Path(settings.COVERS_STORAGE_PATH)
                cover_saved, thumb_saved = CoverProcessor.process_cover(
                    metadata.cover_data, cover_path, thumbnail_path, covers_base_path
                )
                cover_path_str = cover_saved
                thumbnail_path_str = thumb_saved

            # 7. Создание записи в БД
            book = Book(
                id=book_id,
                title=metadata.title,
                author=metadata.author,
                file_path=str(book_file_path),
                file_format=file_format,
                file_size=file_size,
                cover_image_path=cover_path_str,
                cover_thumbnail_path=thumbnail_path_str,
                date_added=datetime.utcnow(),
            )
            book = self.repository.add(book)

            # 8. Чанкинг контента (для epub/fb2) — ДО удаления временного файла
            if file_format in ("epub", "fb2"):
                logger.info(f"Начинаю чанкинг для книги {book.id}, формат={file_format}")
                html_content = self._extract_html_content(tmp_path, file_format, content)
                if html_content:
                    logger.info(f"HTML контент извлечён, длина={len(html_content)} символов")
                    try:
                        chunks = self.chunking_service.chunk_html_content(html_content)
                        logger.info(f"Создано чанков: {len(chunks)}")
                        for chunk_data in chunks:
                            chunk = BookChunk(
                                book_id=book.id,
                                chunk_index=chunk_data["chunk_index"],
                                content_html=chunk_data["content_html"],
                                word_count=chunk_data["word_count"],
                            )
                            self.db.add(chunk)
                        self.db.commit()
                        logger.info(f"Чанки сохранены в БД для книги {book.id}")
                    except Exception as e:
                        logger.error(f"Ошибка при сохранении чанков: {e}", exc_info=True)
                        self.db.rollback()
                else:
                    logger.warning(f"HTML контент не извлечён для книги {book.id}, чанки не созданы")
            else:
                logger.info(f"Формат {file_format} — чанкинг пропускается")

        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except HTTPException:
            raise
        finally:
            # Удаляем временный файл после всех операций
            tmp_path.unlink(missing_ok=True)

        return self._to_dto(book)

    def _parse_metadata(self, file_path: Path, file_format: str):
        """Извлечь метаданные из файла.

        Args:
            file_path: Путь к временному файлу.
            file_format: Формат файла.

        Returns:
            BookMetadata с метаданными.
        """
        if file_format == "epub":
            return EpubParser.parse(file_path)
        elif file_format == "fb2":
            return Fb2Parser.parse(file_path)
        else:  # txt
            return TxtParser.parse(file_path)

    def _extract_html_content(self, file_path: Path, file_format: str, content: bytes) -> Optional[str]:
        """Извлечь HTML контент для чанкинга.

        Args:
            file_path: Путь к файлу.
            file_format: Формат файла.
            content: Содержимое файла.

        Returns:
            HTML строка или None.
        """
        if file_format == "epub":
            try:
                from ebooklib import epub
                book = epub.read_epub(str(file_path))
                html_parts = []
                # Фильтруем по типу EpubHtml — надёжно независимо от версии ebooklib
                for item in book.get_items():
                    if isinstance(item, epub.EpubHtml):
                        html_parts.append(item.get_content().decode("utf-8", errors="ignore"))
                logger.info(f"Извлечено {len(html_parts)} HTML-документов из EPUB")
                return "\n".join(html_parts) if html_parts else None
            except Exception as e:
                logger.error(f"Ошибка при чтении EPUB: {e}", exc_info=True)
                return None
        elif file_format == "fb2":
            try:
                return content.decode("utf-8", errors="ignore")
            except Exception:
                return None
        return None

    def _to_dto(self, book: Book) -> BookDTO:
        """Конвертировать модель Book в BookDTO.

        Args:
            book: Объект Book.

        Returns:
            BookDTO для API ответа.
        """
        return BookDTO(
            id=book.id,
            title=book.title,
            author=book.author,
            file_format=book.file_format,
            cover_thumbnail_path=book.cover_thumbnail_path,
            date_added=book.date_added,
        )
