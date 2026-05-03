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
import tempfile
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
from src.utils.file_validator import validate_upload_file, validate_file_size
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

    async def download_file_from_url(self, url: str) -> UploadFile:
        """Скачать файл книги по HTTP/HTTPS ссылке.

        Args:
            url: HTTP/HTTPS ссылка на файл книги.

        Returns:
            UploadFile с загруженным содержимым.

        Raises:
            HTTPException: При ошибке загрузки файла.
        """
        import httpx

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
            except httpx.HTTPError:
                raise HTTPException(status_code=400, detail="Некорректная или недоступная ссылка")

        content = response.content
        filename = url.split("/")[-1].split("?")[0] or "downloaded_file"

        upload_file = UploadFile(
            filename=filename,
            file=tempfile.SpooledTemporaryFile(),
        )
        await upload_file.write(content)
        await upload_file.seek(0)

        return upload_file

    async def upload_book(self, file: UploadFile) -> BookDTO:
        """Загрузить книгу из файла.

        Args:
            file: Загружаемый файл.

        Returns:
            BookDTO с данными загруженной книги.

        Raises:
            HTTPException: При ошибках валидации, дубликата или обработки.
        """
        # 1. Валидация и чтение файла
        file_format, content = await self._validate_and_read_file(file)
        original_filename = file.filename

        # 2. Временный файл для парсинга
        tmp_path = self._create_temp_file(content, file_format)

        try:
            # 3. Парсинг метаданных и проверка на дубликат
            metadata = self._parse_metadata(tmp_path, file_format)
            self._check_duplicate(metadata)

            # 4. Создание записи книги
            book = await self._create_book_record(metadata, content, file_format, original_filename)

            # 5. Чанкинг контента
            self._chunk_and_save(book, tmp_path, file_format, content)

        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except HTTPException:
            raise
        finally:
            tmp_path.unlink(missing_ok=True)

        return self._to_dto(book)

    async def _validate_and_read_file(self, file: UploadFile) -> tuple[str, bytes]:
        """Валидировать файл и прочитать содержимое.

        Args:
            file: Загружаемый файл.

        Returns:
            Кортеж (формат файла, содержимое в байтах).

        Raises:
            HTTPException: При ошибках валидации.
        """
        file_format = await validate_upload_file(file)
        content = await file.read()
        file_size = len(content)
        validate_file_size(file_size)
        return file_format, content

    def _create_temp_file(self, content: bytes, file_format: str) -> Path:
        """Создать временный файл для парсинга метаданных.

        Args:
            content: Содержимое файла в байтах.
            file_format: Формат файла.

        Returns:
            Путь к временному файлу.
        """
        with tempfile.NamedTemporaryFile(suffix=f".{file_format}", delete=False) as tmp:
            tmp.write(content)
            return Path(tmp.name)

    def _check_duplicate(self, metadata) -> None:
        """Проверить наличие дубликата книги.

        Args:
            metadata: Объект с метаданными книги.

        Raises:
            HTTPException: Если дубликат найден.
        """
        duplicate = self.repository.check_duplicate(metadata.title, metadata.author)
        if duplicate:
            raise HTTPException(
                status_code=409,
                detail="Книга уже есть в библиотеке",
                headers={"X-Existing-Book-Id": str(duplicate.id)},
            )

    async def _create_book_record(self, metadata, content: bytes, file_format: str, original_filename: Optional[str]) -> Book:
        """Создать запись книги в БД.

        Args:
            metadata: Объект с метаданными книги.
            content: Содержимое файла в байтах.
            file_format: Формат файла.
            original_filename: Оригинальное имя файла.

        Returns:
            Сохранённая запись Book.
        """
        book_id = uuid.uuid4()
        book_file_path = generate_book_file_path(book_id, original_filename or "unknown")

        # Сохраняем файл книги
        book_file_path.parent.mkdir(parents=True, exist_ok=True)
        book_file_path.write_bytes(content)

        # Обработка обложки
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

        # Создание записи в БД
        book = Book(
            id=book_id,
            title=metadata.title,
            author=metadata.author,
            file_path=str(book_file_path),
            file_format=file_format,
            file_size=len(content),
            cover_image_path=cover_path_str,
            cover_thumbnail_path=thumbnail_path_str,
            date_added=datetime.utcnow(),
        )
        return self.repository.add(book)

    def _chunk_and_save(self, book: Book, tmp_path: Path, file_format: str, content: bytes) -> None:
        """Выполнить чанкинг контента и сохранить чанки в БД.

        Args:
            book: Созданная запись книги.
            tmp_path: Путь к временному файлу.
            file_format: Формат файла.
            content: Содержимое файла в байтах.
        """
        if file_format not in ("epub", "fb2"):
            logger.info(f"Формат {file_format} — чанкинг пропускается")
            return

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

    def _parse_metadata(self, file_path: Path, file_format: str):
        """Извлечь метаданные из файла.

        Args:
            file_path: Путь к временному файлу.
            file_format: Формат файла.

        Returns:
            BookMetadata с метаданными.

        Raises:
            HTTPException: При ошибке парсинга.
        """
        try:
            if file_format == "epub":
                return EpubParser.parse(file_path)
            elif file_format == "fb2":
                return Fb2Parser.parse(file_path)
            else:  # txt
                return TxtParser.parse(file_path)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Ошибка парсинга файла: {str(e)}")

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
