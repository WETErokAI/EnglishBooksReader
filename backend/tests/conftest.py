"""
Pytest fixtures для backend тестов.
"""

import pytest
from sqlalchemy import create_engine, event, String, TypeDecorator, Column
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from uuid import UUID

from src.models.book import Base


class SQLiteUUID(TypeDecorator):
    """Тип UUID для SQLite в тестах (хранит как строку)."""
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return UUID(value)
        return value


@pytest.fixture
def db_session():
    """Создать тестовую сессию БД (SQLite in-memory)."""
    # Заменяем UUID типы на совместимые с SQLite на уровне таблицы
    from src.models.book import Book, BookChunk
    
    # Обновляем типы в таблицах
    Book.__table__.c['id'].type = SQLiteUUID()
    BookChunk.__table__.c['id'].type = SQLiteUUID()
    BookChunk.__table__.c['book_id'].type = SQLiteUUID()
    
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Включаем FOREIGN KEY для SQLite — по умолчанию отключены
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(_dbapi_connection, _connection_record):
        cursor = _dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
