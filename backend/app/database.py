"""
Подключение к базе данных SQLAlchemy.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Получить сессию базы данных.

    Используется как FastAPI dependency для injection сессии БД.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
