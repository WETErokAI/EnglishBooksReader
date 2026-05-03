"""Диагностика базы данных: проверка таблиц и данных."""

from sqlalchemy import create_engine, MetaData, text
from app.config import settings
from app.database import engine as db_engine
from src.models.book import Base, ReadingPosition

# 1. Показываем URL
print(f"DATABASE_URL: {settings.DATABASE_URL[:50]}...")

# 2. Создаём таблицы
Base.metadata.create_all(bind=db_engine)
print("Tables after create_all:")

# 3. Отражаем таблицы
m = MetaData()
m.reflect(bind=db_engine)
tables = list(m.tables.keys())
print(f"  {tables}")

# 4. Проверяем reading_positions
if 'reading_positions' in tables:
    with db_engine.connect() as conn:
        result = conn.execute(text('SELECT book_id, chunk_id, "offset" FROM reading_positions'))
        rows = result.fetchall()
        print(f"\nreading_positions rows: {len(rows)}")
        for row in rows:
            print(f"  book_id={row[0]}, chunk_id={row[1]}, offset={row[2]}")
else:
    print("\nWARNING: reading_positions table NOT FOUND!")

# 5. Проверяем books
if 'books' in tables:
    with db_engine.connect() as conn:
        result = conn.execute(text("SELECT id, title FROM books"))
        rows = result.fetchall()
        print(f"\nbooks rows: {len(rows)}")
        for row in rows:
            print(f"  id={row[0]}, title={row[1]}")
else:
    print("\nWARNING: books table NOT FOUND!")

print("\nDone.")
