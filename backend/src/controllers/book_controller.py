"""
BookController — FastAPI endpoints для управления книгами.

Endpoints:
- POST /api/v1/books/upload — загрузка файла
- POST /api/v1/books/upload-from-url — загрузка по ссылке
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from src.services.book_service import BookService
from src.schemas.book import BookDTO

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
