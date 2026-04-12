# Quickstart Guide: Библиотека книг

**Date**: 2026-04-08
**Feature**: 001-book-library-upload

## Предварительные требования

### Системные требования
- **ОС**: Windows 10
- **Python**: 3.11+
- **Node.js**: 18+ (для frontend)
- **PostgreSQL**: 14+
- **Git**

### Установка зависимостей

#### 1. Backend

```powershell
# Перейти в директорию backend
cd g:\AI\gpt\EnglishBooksReader\backend

# Создать виртуальное окружение
python -m venv .venv
.venv\Scripts\Activate.ps1

# Установить зависимости
pip install -r requirements.txt
```

**requirements.txt**:
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
alembic==1.13.1
psycopg2-binary==2.9.9
python-multipart==0.0.6
lxml==5.1.0
ebooklib==0.18
pillow==10.2.0
pydantic==2.5.3
pytest==7.4.4
pytest-asyncio==0.23.3
factory-boy==3.3.0
httpx==0.26.0  # Для тестирования
```

#### 2. Frontend

```powershell
# Перейти в директорию frontend
cd g:\AI\gpt\EnglishBooksReader\frontend

# Установить зависимости
npm install
```

**Основные зависимости frontend**:
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.0",
    "@tanstack/react-query": "^5.17.0",
    "axios": "^1.6.5"
  },
  "devDependencies": {
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "typescript": "^5.2.2",
    "vite": "^5.0.8",
    "@vitejs/plugin-react": "^4.2.1",
    "tailwindcss": "^3.4.1",
    "vitest": "^1.2.0",
    "@testing-library/react": "^14.1.2"
  }
}
```

#### 3. PostgreSQL

```powershell
# Создать базу данных
createdb -U postgres english_books_reader

# Или через psql
psql -U postgres
CREATE DATABASE english_books_reader;
```

---

## Запуск приложения

### 1. Настройка backend

```powershell
cd g:\AI\gpt\EnglishBooksReader\backend

# Создать файл конфигурации
copy .env.example .env
# Отредактировать .env:
# DATABASE_URL=postgresql://postgres:password@localhost:5432/english_books_reader
# BOOKS_STORAGE_PATH=g:\AI\gpt\EnglishBooksReader\storage\books
# COVERS_STORAGE_PATH=g:\AI\gpt\EnglishBooksReader\storage\covers

# Запустить миграции
alembic upgrade head

# Запустить сервер (development)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend доступен по: `http://localhost:8000`

API Docs (Swagger): `http://localhost:8000/docs`

### 2. Настройка frontend

```powershell
cd g:\AI\gpt\EnglishBooksReader\frontend

# Создать .env.local
echo "VITE_API_BASE_URL=http://localhost:8000/api/v1" > .env.local

# Запустить dev server
npm run dev
```

Frontend доступен по: `http://localhost:5173`

---

## Структура хранилища файлов

```
g:\AI\gpt\EnglishBooksReader\storage\
├── books\              # Исходные файлы книг
│   ├── {book_id}_great_gatsby.epub
│   └── {book_id}_1984.fb2
├── covers\             # Оригиналы обложек
│   ├── {book_id}.jpg
│   └── ...
└── thumbnails\         # Миниатюры для карточек (200x300)
    ├── {book_id}.jpg
    └── ...
```

---

## Запуск тестов

### Backend

```powershell
cd g:\AI\gpt\EnglishBooksReader\backend
pytest                    # Все тесты
pytest tests/unit         # Только unit-тесты
pytest tests/integration  # Только интеграционные тесты
pytest --cov=src         # С покрытием
```

### Frontend

```powershell
cd g:\AI\gpt\EnglishBooksReader\frontend
npm test                  # Запустить Vitest
npm test -- --coverage    # С покрытием
npm run test:ui           # Vitest UI
```

### E2E тесты

```powershell
cd g:\AI\gpt\EnglishBooksReader
npx playwright install    # Первый раз
npx playwright test       # Запустить E2E тесты
```

---

## Типичный workflow разработки

### 1. Создание новой функциональности (TDD)

```powershell
# 1. RED: Написать тест
# Создать backend/tests/test_book_upload.py
pytest tests/test_book_upload.py  # Должен упасть

# 2. GREEN: Написать минимальный код
# Создать backend/src/controllers/book_controller.py
pytest tests/test_book_upload.py  # Должен пройти

# 3. REFACTOR: Улучшить код
pytest tests/test_book_upload.py  # Всё ещё проходит
```

### 2. Проверка всех тестов

```powershell
# Backend
cd backend
pytest

# Frontend (в отдельном терминале)
cd frontend
npm test

# Убедиться, что все тесты проходят перед коммитом
```

---

## Troubleshooting

### PostgreSQL не запускается

```powershell
# Проверить статус
pg_ctl status

# Запустить
pg_ctl start -D "C:\Program Files\PostgreSQL\14\data"
```

### Ошибка миграций

```powershell
# Проверить текущую версию
alembic current

# Откатить последнюю миграцию
alembic downgrade -1

# Применить заново
alembic upgrade head
```

### Frontend не подключается к backend

- Проверить `VITE_API_BASE_URL` в `.env.local`
- Убедиться, что backend запущен на порту 8000
- Проверить CORS настройки в `backend/app/main.py`

---

## Следующие шаги

1. Ознакомиться со спецификацией: `specs/001-book-library-upload/spec.md`
2. Изучить data model: `specs/001-book-library-upload/data-model.md`
3. Посмотреть API контракты: `specs/001-book-library-upload/contracts/api-contracts.md`
4. Начать разработку согласно `tasks.md` (после создания через `/speckit.tasks`)
