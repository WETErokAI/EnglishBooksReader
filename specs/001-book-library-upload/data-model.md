# Data Model: Библиотека книг

**Date**: 2026-04-08
**Feature**: 001-book-library-upload

## Entities

### Book (Книга)

Представляет одну загруженную книгу в библиотеке.

**Fields**:

| Поле | Тип | Описание | Validation |
|------|-----|----------|------------|
| `id` | UUID | Уникальный идентификатор книги | Primary key, auto-generated |
| `title` | String(500) | Название книги | Required, max 500 chars |
| `author` | String(300) | Автор книги (если извлечён) | Nullable, max 300 chars |
| `file_path` | String(1000) | Абсолютный путь к файлу на диске | Required, valid file path |
| `file_format` | Enum | Формат файла | Required, один из: `txt`, `epub`, `fb2` |
| `file_size` | Integer | Размер файла в байтах | Required, > 0, <= 50 MB (52,428,800 bytes) |
| `cover_image_path` | String(1000) | Путь к файлу обложки (если извлечена) | Nullable, valid image path |
| `cover_thumbnail_path` | String(1000) | Путь к миниатюре обложки для карточек | Nullable, valid image path |
| `date_added` | DateTime | Дата и время добавления в библиотеку | Required, auto-set on create |
| `chunks` | Relationship | Коллекция чанков книги (one-to-many) | Lazy loaded |
| `is_duplicate` | Boolean | Флаг дубликата (для валидации) | Computed field, not persisted |

**Validation Rules**:
- `file_path` должен существовать на момент создания
- `file_size` <= 50 МБ (52,428,800 байт)
- `file_format` ∈ {`txt`, `epub`, `fb2`}
- `title` не может быть пустым (fallback на filename)
- Уникальность: `(title, author)` комбинация должна быть уникальной (если author NULL, то только `title`)

**State Transitions**:
- `Created` → `Reading` (при открытии книги)
- `Reading` → `Reading` (обновление позиции)
- `Created/Reading` → `Deleted` (мягкое удаление для восстановления файла)

**Indexes**:
- Index на `(title, author)` для быстрого поиска дубликатов
- Full-text index на `title` и `author` для поиска по библиотеке

---

### ReadingPosition (Позиция чтения)

Хранит позицию последнего чтения для конкретной книги. Вынесена в отдельную таблицу, чтобы избежать постоянных перезаписей записей `Book` при каждом обновлении позиции чтения. В проекте один пользователь, поэтому таблица не содержит `user_id`.

**Fields**:

| Поле | Тип | Описание | Validation |
|------|-----|----------|------------|
| `id` | UUID | Уникальный идентификатор записи | Primary key, auto-generated |
| `book_id` | UUID | Внешний ключ на Book | Required, foreign key, unique |
| `chunk_id` | UUID | Идентификатор последнего прочитанного чанка | Required |
| `offset` | Integer | Смещение внутри чанка (позиция в тексте) | Required, >= 0 |
| `last_read_at` | DateTime | Время последнего обновления позиции | Required, auto-set on update |

**Validation Rules**:
- `book_id` должен быть уникальным — одна позиция на книгу
- `offset` не может быть отрицательным
- `last_read_at` обновляется при каждом вызове `save_position`

**Relationships**:
- One-to-one с `Book` (одна позиция на одну книгу)
- Индекс по `book_id` для быстрого поиска

---

### BookChunk (Чанк книги)

Представляет часть контента книги для динамической подгрузки в режиме чтения.

**Fields**:

| Поле | Тип | Описание | Validation |
|------|-----|----------|------------|
| `id` | UUID | Уникальный идентификатор чанка | Primary key, auto-generated |
| `book_id` | UUID | Внешний ключ на Book | Required, foreign key |
| `chunk_index` | Integer | Порядковый номер чанка (0-based) | Required, >= 0 |
| `content_html` | Text | HTML контент чанка | Required, valid HTML |
| `word_count` | Integer | Количество слов в чанке | Computed, для оптимизации |

**Validation Rules**:
- `chunk_index` должен быть уникальным в рамках одной книги
- `content_html` не может быть пустым
- Оптимальный размер: ~5000 слов (не жёсткое ограничение)

**Relationships**:
- Many-to-one с `Book` (множество чанков у одной книги)
- Индекс по `(book_id, chunk_index)` для последовательного чтения

---

### Library (Библиотека)

Коллекция всех книг пользователя. Не отдельная таблица, а view/aggregation над `Book`.

**Operations**:
- `get_all()` → List[Book]: Получить все книги
- `search(query: str)` → List[Book]: Поиск по title/author
- `get_by_id(id: UUID)` → Book: Получить книгу по ID
- `add(book: Book)` → Book: Добавить книгу
- `delete(id: UUID)` → void: Удалить книгу (физически удалить запись, но не файл)
- `update(id: UUID, updates: dict)` → Book: Обновить метаданные книги
- `check_duplicate(title: str, author: Optional[str])` → Optional[Book]: Проверка на дубликат

---

## Database Schema (SQLAlchemy Models)

```python
# backend/src/models/book.py

class Book(Base):
    __tablename__ = "books"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(500), nullable=False)
    author = Column(String(300), nullable=True)
    file_path = Column(String(1000), nullable=False)
    file_format = Column(Enum("txt", "epub", "fb2", name="fileformat"), nullable=False)
    file_size = Column(Integer, nullable=False)
    cover_image_path = Column(String(1000), nullable=True)
    cover_thumbnail_path = Column(String(1000), nullable=True)
    date_added = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_reading_position = Column(JSON, nullable=True)
    
    chunks = relationship("BookChunk", back_populates="book", lazy="selectin")
    
    __table_args__ = (
        Index("idx_book_title_author", "title", "author"),
    )


class BookChunk(Base):
    __tablename__ = "book_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content_html = Column(Text, nullable=False)
    word_count = Column(Integer, nullable=False)
    
    book = relationship("Book", back_populates="chunks")
    
    __table_args__ = (
        Index("idx_chunk_book_index", "book_id", "chunk_index", unique=True),
    )
```

---

## Validation Flow

```
Upload Request
    ↓
1. Validate file format (txt|epub|fb2)
    ↓
2. Validate file size (≤ 50 MB)
    ↓
3. Check for duplicate (title + author)
    ↓
4. Extract metadata (title, author, cover)
    ↓
5. Chunk book content
    ↓
6. Save to database (Book + BookChunks)
    ↓
7. Return BookDTO
```

---

## API DTOs (Pydantic Schemas)

```python
# backend/src/schemas/book.py

class BookCreate(BaseModel):
    """Схема для загрузки книги"""
    # File upload обрабатывается через FastAPI UploadFile
    pass


class BookUpdate(BaseModel):
    """Схема для обновления метаданных"""
    title: Optional[str] = Field(None, max_length=500)
    author: Optional[str] = Field(None, max_length=300)


class BookDTO(BaseModel):
    """DTO для отображения книги"""
    id: UUID
    title: str
    author: Optional[str]
    file_format: str
    cover_thumbnail_path: Optional[str]
    date_added: datetime
    has_reading_position: bool
    
    class Config:
        from_attributes = True


class BookListDTO(BaseModel):
    """Схема для списка книг с пагинацией"""
    books: List[BookDTO]
    total: int
```
