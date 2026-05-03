# English Books Reader — Backend API

REST API для управления локальной библиотекой книг. Поддерживает загрузку файлов (.txt, .epub, .fb2), извлечение метаданных, чтение с динамической подгрузкой чанков и поиск по библиотеке.

## Запуск

```powershell
cd backend

# Активировать conda окружение
conda activate english-books-reader

# Настроить конфигурацию
copy .env.example .env
# Отредактировать .env:
# DATABASE_URL=postgresql://postgres:password@localhost:5432/english_books_reader
# BOOKS_STORAGE_PATH=g:\AI\gpt\EnglishBooksReader\storage\books
# COVERS_STORAGE_PATH=g:\AI\gpt\EnglishBooksReader\storage\covers

# Применить миграции
alembic upgrade head

# Запустить сервер
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Сервер доступен по: **http://localhost:8000**

Swagger UI: **http://localhost:8000/docs**

ReDoc: **http://localhost:8000/redoc**

---

## Структура

```
backend/
├── src/
│   ├── controllers/          # FastAPI роуты (API endpoints)
│   ├── services/             # Бизнес-логика
│   ├── repositories/         # CRUD операции с БД
│   ├── models/               # SQLAlchemy модели
│   ├── schemas/              # Pydantic схемы (request/response)
│   └── utils/                # Утилиты
├── tests/
│   ├── unit/                 # Unit-тесты
│   └── integration/          # Интеграционные тесты
├── app/
│   ├── main.py               # Точка входа FastAPI
│   └── config.py             # Конфигурация
├── alembic/                  # Миграции БД
├── alembic.ini               # Конфигурация Alembic
└── requirements.txt          # Зависимости
```

---

## API Endpoints

### Health Check

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/api/v1/health` | Проверка работоспособности |

**Response**:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

---

### Книги (Books)

| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/api/v1/books/upload` | Загрузить книгу (multipart/form-data) |
| `POST` | `/api/v1/books/upload-from-url` | Загрузить книгу по URL |
| `GET` | `/api/v1/books` | Получить список книг (с пагинацией и поиском) |
| `GET` | `/api/v1/books/{book_id}` | Получить книгу по ID |
| `PATCH` | `/api/v1/books/{book_id}` | Обновить метаданные книги (переименование) |
| `DELETE` | `/api/v1/books/{book_id}` | Удалить запись о книге |
| `GET` | `/api/v1/books/{book_id}/chunks` | Получить чанки книги для чтения |

---

#### POST `/api/v1/books/upload`

Загрузка книги из локального файла.

**Content-Type**: `multipart/form-data`

**Parameters**:

| Параметр | Тип | Обязательный | Описание |
|----------|-----|:------------:|----------|
| `file` | File | Да | Файл книги (.txt, .epub, .fb2) |

**Поддерживаемые форматы**: `.txt`, `.epub`, `.fb2`

**Максимальный размер**: 50 МБ

**Успешный ответ** (`201 Created`):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "The Great Gatsby",
  "author": "F. Scott Fitzgerald",
  "file_format": "epub",
  "file_size": 245678,
  "cover_thumbnail_path": "/storage/thumbnails/550e8400-e29b-41d4-a716-446655440000.jpg",
  "date_added": "2026-04-08T10:00:00Z"
}
```

**Ошибки**:

| Код | Описание |
|-----|----------|
| `400` | Неподдерживаемый формат или повреждённый файл |
| `400` | Превышен максимальный размер (50 МБ) |
| `409` | Книга с таким названием уже существует |

---

#### POST `/api/v1/books/upload-from-url`

Загрузка книги по HTTP-ссылке.

**Content-Type**: `application/json`

**Request Body**:
```json
{
  "url": "https://example.com/book.epub"
}
```

**Успешный ответ** (`201 Created`): аналогичен `/upload`

---

#### GET `/api/v1/books`

Получить список книг.

**Query Parameters**:

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|:------------:|----------|
| `page` | int | 1 | Номер страницы |
| `page_size` | int | 20 | Количество книг на странице |
| `search` | str | — | Поиск по названию и автору |

**Успешный ответ** (`200 OK`):
```json
{
  "books": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "The Great Gatsby",
      "author": "F. Scott Fitzgerald",
      "file_format": "epub",
      "cover_thumbnail_path": "/storage/thumbnails/550e8400-e29b-41d4-a716-446655440000.jpg",
      "date_added": "2026-04-08T10:00:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

---

#### GET `/api/v1/books/{book_id}`

Получить детальную информацию о книге.

**Path Parameters**:

| Параметр | Тип | Описание |
|----------|-----|----------|
| `book_id` | UUID | ID книги |

**Успешный ответ** (`200 OK`): аналогичен элементу массива из `GET /books`

**Ошибки**:

| Код | Описание |
|-----|----------|
| `404` | Книга не найдена |

---

#### PATCH `/api/v1/books/{book_id}`

Обновить метаданные книги (переименование).

**Content-Type**: `application/json`

**Request Body**:
```json
{
  "title": "Новое название книги"
}
```

**Успешный ответ** (`200 OK`): обновлённый объект книги

---

#### DELETE `/api/v1/books/{book_id}`

Удалить запись о книге.

**Успешный ответ** (`204 No Content`)

---

#### GET `/api/v1/books/{book_id}/chunks`

Получить чанки книги для режима чтения.

**Query Parameters**:

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|:------------:|----------|
| `from_chunk` | int | 0 | Индекс первого чанка |
| `to_chunk` | int | — | Индекс последнего чанка |
| `count` | int | 3 | Количество чанков |

**Успешный ответ** (`200 OK`):
```json
{
  "chunks": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "chunk_index": 0,
      "content_html": "<h1>Глава 1</h1><p>...</p>",
      "word_count": 4523
    }
  ],
  "total_chunks": 15,
  "book_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## Ошибки

Все ошибки возвращаются в统一ном формате:

```json
{
  "detail": "Описание ошибки"
}
```

| Код | Описание |
|-----|----------|
| `400` | Неверный запрос (формат, размер, повреждённый файл) |
| `404` | Ресурс не найден |
| `409` | Конфликт (дубликат книги) |
| `422` | Ошибка валидации Pydantic |
| `500` | Внутренняя ошибка сервера |

---

## Тестирование

```powershell
# Все тесты
pytest

# Только unit
pytest tests/unit

# Только интеграционные
pytest tests/integration

# С покрытием
pytest --cov=src --cov-report=html
```

---

## Переменные окружения

| Переменная | По умолчанию | Описание |
|------------|-------------|----------|
| `DATABASE_URL` | `postgresql://postgres:password@localhost:5432/english_books_reader` | Строка подключения к PostgreSQL |
| `BOOKS_STORAGE_PATH` | `storage/books` | Директория хранения файлов книг |
| `COVERS_STORAGE_PATH` | `storage/covers` | Директория хранения оригиналов обложек |
| `THUMBNAILS_STORAGE_PATH` | `storage/thumbnails` | Директория хранения миниатюр обложек |
| `MAX_FILE_SIZE` | `52428800` | Максимальный размер файла в байтах (50 МБ) |

---

## Зависимости

| Пакет | Версия | Назначение |
|-------|--------|------------|
| fastapi | 0.109.0 | Web framework |
| uvicorn | 0.27.0 | ASGI сервер |
| sqlalchemy | 2.0.25 | ORM |
| alembic | 1.13.1 | Миграции БД |
| psycopg2-binary | 2.9.9 | PostgreSQL драйвер |
| lxml | 5.1.0 | Парсинг XML/FB2 |
| ebooklib | 0.18 | Парсинг EPUB |
| pillow | 10.2.0 | Обработка изображений |
| pydantic | 2.5.3 | Валидация данных |
| httpx | 0.26.0 | HTTP клиент для загрузки по URL |
| pytest | 7.4.4 | Фреймворк тестирования |
