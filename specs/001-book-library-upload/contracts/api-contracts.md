# API Contracts: Библиотека книг

**Date**: 2026-04-08
**Feature**: 001-book-library-upload

## Overview

REST API для управления библиотекой книг. Base URL: `http://localhost:8000/api/v1`

---

## Endpoints

### 1. Загрузить книгу

**POST** `/books/upload`

Загрузка книги из локального файла.

**Request**:
- Content-Type: `multipart/form-data`
- Body:
  - `file` (File): Файл книги (.txt, .epub, .fb2), макс. 50 МБ

**Response 201 Created**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "The Great Gatsby",
  "author": "F. Scott Fitzgerald",
  "file_format": "epub",
  "cover_thumbnail_path": "/static/covers/550e8400.jpg",
  "date_added": "2026-04-08T10:30:00Z",
  "has_reading_position": false
}
```

**Response 400 Bad Request**:
```json
{
  "error": "Неподдерживаемый формат файла. Поддерживаются: .txt, .epub, .fb2"
}
```

**Response 413 Payload Too Large**:
```json
{
  "error": "Превышен максимальный размер файла. Максимум: 50 МБ"
}
```

**Response 409 Conflict** (дубликат):
```json
{
  "error": "Книга уже есть в библиотеке",
  "existing_book_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response 422 Unprocessable Entity** (повреждённый файл):
```json
{
  "error": "Файл повреждён и не может быть обработан"
}
```

---

### 2. Загрузить книгу по ссылке

**POST** `/books/upload-from-url`

Загрузка книги по HTTP/HTTPS ссылке.

**Request**:
- Content-Type: `application/json`
- Body:
```json
{
  "url": "https://example.com/books/great-gatsby.epub"
}
```

**Response 201 Created**: (как выше)

**Response 400 Bad Request**:
```json
{
  "error": "Некорректная или недоступная ссылка"
}
```

**Response 409 Conflict**: (как выше)

---

### 3. Получить список книг

**GET** `/books`

Получение списка всех книг с опциональным поиском.

**Query Parameters**:
- `search` (string, optional): Поисковый запрос по title/author
- `page` (integer, default: 1): Номер страницы
- `page_size` (integer, default: 20): Размер страницы (макс. 100)

**Response 200 OK**:
```json
{
  "books": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "The Great Gatsby",
      "author": "F. Scott Fitzgerald",
      "file_format": "epub",
      "cover_thumbnail_path": "/static/covers/550e8400.jpg",
      "date_added": "2026-04-08T10:30:00Z",
      "has_reading_position": true
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

### 4. Получить книгу по ID

**GET** `/books/{book_id}`

Получение детальной информации о книге.

**Response 200 OK**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "The Great Gatsby",
  "author": "F. Scott Fitzgerald",
  "file_format": "epub",
  "cover_thumbnail_path": "/static/covers/550e8400.jpg",
  "date_added": "2026-04-08T10:30:00Z",
  "has_reading_position": true
}
```

**Response 404 Not Found**:
```json
{
  "error": "Книга не найдена"
}
```

---

### 5. Обновить книгу

**PATCH** `/books/{book_id}`

Обновление метаданных книги (переименование).

**Request**:
- Content-Type: `application/json`
- Body:
```json
{
  "title": "The Great Gatsby (Updated)"
}
```

**Response 200 OK**: (BookDTO)

**Response 404 Not Found**: (как выше)

---

### 6. Удалить книгу

**DELETE** `/books/{book_id}`

Удаление книги из библиотеки (запись в БД, файл не удаляется).

**Response 204 No Content**

**Response 404 Not Found**: (как выше)

---

### 7. Получить чанки книги

**GET** `/books/{book_id}/chunks`

Получение чанков для режима чтения.

**Query Parameters**:
- `from_chunk` (integer): Индекс начального чанка (0-based)
- `to_chunk` (integer): Индекс конечного чанка (inclusive)

**Response 200 OK**:
```json
{
  "book_id": "550e8400-e29b-41d4-a716-446655440000",
  "chunks": [
    {
      "chunk_index": 0,
      "content_html": "<h1>Chapter 1</h1><p>In my younger and more vulnerable years...</p>",
      "word_count": 4500
    }
  ],
  "total_chunks": 15
}
```

---

### 8. Сохранить позицию чтения

**POST** `/books/{book_id}/reading-position`

Сохранение последней позиции чтения.

**Request**:
- Content-Type: `application/json`
- Body:
```json
{
  "chunk_id": "chunk-uuid",
  "offset": 1250,
  "timestamp": "2026-04-08T15:45:00Z"
}
```

**Response 200 OK**:
```json
{
  "success": true
}
```

---

### 9. Получить позицию чтения

**GET** `/books/{book_id}/reading-position`

Получение сохранённой позиции чтения.

**Response 200 OK**:
```json
{
  "chunk_id": "chunk-uuid",
  "offset": 1250,
  "timestamp": "2026-04-08T15:45:00Z"
}
```

**Response 404 Not Found** (нет сохранённой позиции):
```json
{
  "chunk_id": null,
  "offset": 0
}
```

---

## Error Responses

Все ошибки возвращаются в едином формате:

```json
{
  "error": "Человекочитаемое сообщение об ошибке",
  "detail": "Опциональные технические детали (только для dev mode)"
}
```

### HTTP Status Codes

| Code | Значение |
|------|----------|
| 200 | Успешный запрос |
| 201 | Ресурс создан |
| 204 | Успешное удаление |
| 400 | Некорректный запрос (формат, ссылка) |
| 404 | Ресурс не найден |
| 409 | Конфликт (дубликат) |
| 413 | Превышен размер файла |
| 422 | Повреждённый файл |
| 500 | Внутренняя ошибка сервера |
