"""
Конфигурация приложения.

Управление переменными окружения для backend.
"""

import os
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения из переменных окружения."""

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/english_books_reader"

    # Storage paths
    BOOKS_STORAGE_PATH: str = "g:\\AI\\gpt\\EnglishBooksReader\\storage\\books"
    COVERS_STORAGE_PATH: str = "g:\\AI\\gpt\\EnglishBooksReader\\storage\\covers"

    # Application
    APP_NAME: str = "English Books Reader"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    @field_validator("BOOKS_STORAGE_PATH", "COVERS_STORAGE_PATH", mode="before")
    @classmethod
    def resolve_path(cls, v: str) -> str:
        """Создать директории если не существуют."""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Глобальный экземпляр настроек
settings = Settings()
