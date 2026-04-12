"""
FastAPI приложение.

Точка входа для backend сервера.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from src.models.book import Base
from src.utils.storage import ensure_storage_directories
from src.controllers.book_controller import router as books_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle приложения: инициализация при запуске."""
    # Создаем таблицы в БД если не существуют
    Base.metadata.create_all(bind=engine)
    # Создаем директории хранилища
    ensure_storage_directories()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS middleware для frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Регистрируем роутер книг
app.include_router(books_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    """Health check endpoint.

    Returns:
        Статус приложения.
    """
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
