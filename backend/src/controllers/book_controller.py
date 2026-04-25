"""
BookController — FastAPI endpoints для управления книгами.

Endpoints:
- POST /api/v1/books/upload — загрузка файла
- POST /api/v1/books/upload-from-url — загрузка по ссылке
- GET /api/v1/books — список книг с пагинацией и поиском
- GET /api/v1/books/{book_id} — детальная информация
- PATCH /api/v1/books/{book_id} — переименование
- DELETE /api/v1/books/{book_id} — удаление
- GET /api/v1/books/{book_id}/chunks — получение чанков
- POST /api/v1/books/{book_id}/reading-position — сохранение позиции
- GET /api/v1/books/{book_id}/reading-position — получение позиции
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from src.services.book_service import BookService
from src.services.reading_position_service import ReadingPositionService
from src.repositories.book_repository import BookRepository
from src.schemas.book import (
    BookDTO,
    BookListDTO,
    BookUpdate,
    BookChunksResponse,
    BookChunkDTO,
    ReadingPositionSave,
    ReadingPositionResponse,
    ReadingPositionSuccessResponse,
)

router = APIRouter(prefix="/books", tags=["books"])


@router.post(
    "/upload",
    response_model=BookDTO,
    status_code=201,
    summary="Загрузить книгу из файла",
    responses={
        400: {"description": "Неподдерживаемый формат или превышен размер"},
        409: {"description": "Книга уже есть в библиотеке"},
        422: {"description": "Файл повреждён"},
    },
)
async def upload_book(
    file: UploadFile = File(..., description="Файл книги (.txt, .epub, .fb2), макс. 50 МБ"),
    db: Session = Depends(get_db),
) -> BookDTO:
    """Загрузить книгу из локального файла.

    Args:
        file: Загружаемый файл книги.
        db: Сессия базы данных.

    Returns:
        BookDTO с данными загруженной книги.

    Raises:
        HTTPException: При ошибках валидации, дубликата или обработки.
    """
    service = BookService(db)
    try:
        return await service.upload_book(file)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {str(e)}")


@router.post(
    "/upload-from-url",
    response_model=BookDTO,
    status_code=201,
    summary="Загрузить книгу по ссылке",
    responses={
        400: {"description": "Некорректная или недоступная ссылка"},
        409: {"description": "Книга уже есть в библиотеке"},
    },
)
async def upload_book_from_url(
    url: str = Query(..., description="HTTP/HTTPS ссылка на файл книги"),
    db: Session = Depends(get_db),
) -> BookDTO:
    """Загрузить книгу по HTTP/HTTPS ссылке.

    Args:
        url: Ссылка на файл книги.
        db: Сессия базы данных.

    Returns:
        BookDTO с данными загруженной книги.

    Raises:
        HTTPException: При ошибках загрузки или дубликата.
    """
    import httpx
    import tempfile
    from pathlib import Path
    from fastapi import UploadFile

    # Скачиваем файл
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
        except httpx.HTTPError:
            raise HTTPException(status_code=400, detail="Некорректная или недоступная ссылка")

    content = response.content
    filename = url.split("/")[-1].split("?")[0] or "downloaded_file"

    # Создаём UploadFile
    upload_file = UploadFile(
        filename=filename,
        file=tempfile.SpooledTemporaryFile(),
    )
    await upload_file.write(content)
    await upload_file.seek(0)

    service = BookService(db)
    try:
        return await service.upload_book(upload_file)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get(
    "",
    response_model=BookListDTO,
    summary="Получить список книг",
)
def get_books(
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    search: Optional[str] = Query(None, description="Поисковый запрос"),
    db: Session = Depends(get_db),
) -> BookListDTO:
    """Получить список книг с пагинацией и опциональным поиском.

    Args:
        page: Номер страницы.
        page_size: Размер страницы.
        search: Поисковый запрос.
        db: Сессия базы данных.

    Returns:
        BookListDTO со списком книг.
    """
    repository = BookRepository(db)
    skip = (page - 1) * page_size
    books, total = repository.get_all(skip=skip, limit=page_size, search=search)

    return BookListDTO(
        books=[BookDTO.model_validate(b) for b in books],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{book_id}",
    response_model=BookDTO,
    summary="Получить книгу по ID",
    responses={404: {"description": "Книга не найдена"}},
)
def get_book(
    book_id: UUID,
    db: Session = Depends(get_db),
) -> BookDTO:
    """Получить детальную информацию о книге.

    Args:
        book_id: UUID книги.
        db: Сессия базы данных.

    Returns:
        BookDTO с данными книги.

    Raises:
        HTTPException: Если книга не найдена.
    """
    repository = BookRepository(db)
    book = repository.get_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")

    return BookDTO.model_validate(book)


@router.patch(
    "/{book_id}",
    response_model=BookDTO,
    summary="Обновить метаданные книги",
    responses={404: {"description": "Книга не найдена"}},
)
def update_book(
    book_id: UUID,
    updates: BookUpdate,
    db: Session = Depends(get_db),
) -> BookDTO:
    """Обновить метаданные книги (переименование).

    Args:
        book_id: UUID книги.
        updates: Данные для обновления.
        db: Сессия базы данных.

    Returns:
        BookDTO с обновлёнными данными.

    Raises:
        HTTPException: Если книга не найдена.
    """
    repository = BookRepository(db)
    update_dict = updates.model_dump(exclude_unset=True)

    book = repository.update(book_id, update_dict)
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")

    return BookDTO.model_validate(book)


@router.delete(
    "/{book_id}",
    status_code=204,
    summary="Удалить книгу",
    responses={404: {"description": "Книга не найдена"}},
)
def delete_book(
    book_id: UUID,
    db: Session = Depends(get_db),
):
    """Удалить книгу из библиотеки.

    Args:
        book_id: UUID книги.
        db: Сессия базы данных.

    Raises:
        HTTPException: Если книга не найдена.
    """
    repository = BookRepository(db)
    success = repository.delete(book_id)
    if not success:
        raise HTTPException(status_code=404, detail="Книга не найдена")


@router.get(
    "/{book_id}/chunks",
    response_model=BookChunksResponse,
    summary="Получить чанки книги",
    responses={404: {"description": "Книга не найдена"}},
)
def get_book_chunks(
    book_id: UUID,
    from_chunk: Optional[int] = Query(None, ge=0, description="Начальный индекс чанка"),
    to_chunk: Optional[int] = Query(None, ge=0, description="Конечный индекс чанка"),
    db: Session = Depends(get_db),
) -> BookChunksResponse:
    """Получить чанки книги для режима чтения.

    Args:
        book_id: UUID книги.
        from_chunk: Индекс начального чанка.
        to_chunk: Индекс конечного чанка.
        db: Сессия базы данных.

    Returns:
        BookChunksResponse с чанками.

    Raises:
        HTTPException: Если книга не найдена.
    """
    from src.models.book import Book

    repository = BookRepository(db)
    book = repository.get_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")

    # Загружаем чанки с опциональным диапазоном
    query = db.query(Book).filter(Book.id == book_id)
    chunks = book.chunks

    if from_chunk is not None and to_chunk is not None:
        chunks = [c for c in chunks if from_chunk <= c.chunk_index <= to_chunk]
    elif from_chunk is not None:
        chunks = [c for c in chunks if c.chunk_index >= from_chunk]
    elif to_chunk is not None:
        chunks = [c for c in chunks if c.chunk_index <= to_chunk]

    return BookChunksResponse(
        book_id=book_id,
        chunks=[BookChunkDTO.model_validate(c) for c in chunks],
        total_chunks=len(book.chunks),
    )


@router.post(
    "/{book_id}/reading-position",
    response_model=ReadingPositionSuccessResponse,
    summary="Сохранить позицию чтения",
    responses={404: {"description": "Книга не найдена"}},
)
def save_reading_position(
    book_id: UUID,
    position: ReadingPositionSave,
    db: Session = Depends(get_db),
) -> ReadingPositionSuccessResponse:
    """Сохранить позицию чтения для книги.

    Args:
        book_id: UUID книги.
        position: Данные позиции чтения.
        db: Сессия базы данных.

    Returns:
        ReadingPositionSuccessResponse.

    Raises:
        HTTPException: Если книга не найдена.
    """
    repository = BookRepository(db)
    service = ReadingPositionService(db, repository)

    success = service.save_position(book_id, position.chunk_id, position.offset, position.timestamp)
    if not success:
        raise HTTPException(status_code=404, detail="Книга не найдена")

    return ReadingPositionSuccessResponse()


@router.get(
    "/{book_id}/reading-position",
    response_model=ReadingPositionResponse,
    summary="Получить позицию чтения",
)
def get_reading_position(
    book_id: UUID,
    db: Session = Depends(get_db),
) -> ReadingPositionResponse:
    """Получить сохранённую позицию чтения.

    Args:
        book_id: UUID книги.
        db: Сессия базы данных.

    Returns:
        ReadingPositionResponse с данными позиции.
    """
    repository = BookRepository(db)
    service = ReadingPositionService(db, repository)

    position = service.get_position(book_id)
    if not position:
        return ReadingPositionResponse(chunk_id=None, offset=0)

    return ReadingPositionResponse(
        chunk_id=UUID(position["chunk_id"]),
        offset=position["offset"],
        timestamp=position["timestamp"],
    )
