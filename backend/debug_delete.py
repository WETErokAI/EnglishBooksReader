#!/usr/bin/env python
"""Debug script to test book deletion."""
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from src.models.book import Base, Book
from uuid import uuid4
from datetime import datetime

# Создаём in-memory SQLite
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)


def override_get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# Создаём книгу через сессию
session = Session()
book = Book(
    id=uuid4(),
    title="Test",
    author="Author",
    file_path="/path.epub",
    file_format="epub",
    file_size=100,
    date_added=datetime.utcnow(),
)
session.add(book)
session.commit()
book_id = book.id
print(f"Created book with id: {book_id}")

# Получаем книгу через API
resp = client.get(f"/api/v1/books/{book_id}")
print(f"GET before delete: status={resp.status_code}")

# Удаляем книгу через API
resp = client.delete(f"/api/v1/books/{book_id}")
print(f"DELETE: status={resp.status_code}")

# Проверяем что книга удалена
resp = client.get(f"/api/v1/books/{book_id}")
print(f"GET after delete: status={resp.status_code}")

# Проверяем через сессию напрямую
books_count = session.query(Book).count()
print(f"Books in DB after delete: {books_count}")
