# Research: Базовая библиотека книг и загрузка файлов

**Date**: 2026-04-08
**Feature**: 001-book-library-upload

## Resolution of NEEDS CLARIFICATION

### 1. TDD Process Confirmation
**Decision**: Строгий TDD цикл (Red-Green-Refactor) будет применяться для всей разработки
**Rationale**: Конституция проекта требует TDD как NON-NEGOTIABLE (Principle III). Все тесты пишутся ДО кода.
**Alternatives considered**: 
- Test-after подход — отклонён, т.к. нарушает конституцию
- Гибридный подход — отклонён по той же причине

---

## Technology Research

### 2. EPUB Parsing Library
**Decision**: Использовать `ebooklib` для парсинга EPUB файлов
**Rationale**: 
- Поддерживает извлечение метаданных (название, автор, обложка)
- Работает с EPUB2 и EPUB3
- Активно поддерживается, хорошая документация
- Легковесный по сравнению с альтернативами
**Alternatives considered**:
- `epubfile` — менее функциональный
- Кастомный ZIP+XML парсер — излишне сложный, ebooklib уже решает задачу

### 3. FB2 Parsing Library
**Decision**: Использовать кастомный XML парсер на базе `lxml` для FB2
**Rationale**:
- FB2 — это XML формат, `lxml` обеспечивает быстрый парсинг
- Прямой контроль над извлечением метаданных и контента
- `lxml` уже в зависимостях для работы с XML
**Alternatives considered**:
- `fb2-utils` — не активно поддерживается
- `remarshal` — требует дополнительных зависимостей

### 4. Image Processing (обложки)
**Decision**: Использовать `Pillow` для обработки обложек
**Rationale**:
- Стандарт де-факто для работы с изображениями в Python
- Поддержка конвертации в base64 для отправки на frontend
- Resize и оптимизация для отображения в карточках
**Alternatives considered**:
- `opencv-python` — избыточен для простой обработки обложек
- `wand` (ImageMagick) — требует установки ImageMagick на систему

### 5. Chunking Strategy для больших книг
**Decision**: Разбиение на чанки по главам/разделам (если доступны), иначе по фиксированному количеству параграфов (~5000 слов на чанк)
**Rationale**:
- Естественные границы (главы) обеспечивают лучший UX при чтении
- Fallback на фиксированный размер гарантирует работу с книгами без глав
- 5000 слов ≈ 30-40 КБ текста — оптимально для быстрой подгрузки
- Frontend загружает видимые чанки ± 2 соседних
**Alternatives considered**:
- Фиксированный размер по символам — может разрывать предложения
- Динамический размер по viewport — сложно предсказать нагрузку
- Постраничное разбиение — не подходит для вертикальной прокрутки

### 6. PostgreSQL vs SQLite для локального хранения
**Decision**: Использовать PostgreSQL как указано в конституции
**Rationale**:
- Конституция требует PostgreSQL (технологический стек)
- Лучшая поддержка полнотекстового поиска для поиска по библиотеке
- Масштабируемость при росте функциональности
**Alternatives considered**:
- SQLite — проще для локальной работы, но нарушает конституцию
- Файловое хранилище (JSON) — не подходит для поиска и транзакций

### 7. React State Management
**Decision**: Использовать React Query (TanStack Query) для серверного состояния + Context API для глобального UI состояния
**Rationale**:
- React Query автоматизирует кэширование, синхронизацию и refetch
- Проще в освоении чем Redux/Zustand для данного scope
- Context API достаточно для UI состояния (тема, вид отображения)
**Alternatives considered**:
- Redux Toolkit — избыточен для данного объёма состояния
- Zustand — хорош, но React Query лучше подходит для API данных
- SWR — менее функционален чем React Query

### 8. File Upload Strategy (большие файлы до 50 МБ)
**Decision**: Прямая загрузка через multipart/form-data с прогресс-баром на frontend, стриминговая обработка на backend
**Rationale**:
- Multipart стандарт для файловых загрузок
- Прогресс-бар улучшает UX для больших файлов
- Стриминг на backend предотвращает превышение памяти
**Alternatives considered**:
- Chunked upload — избыточен для 50 МБ
- Base64 encoding — увеличивает размер на 33%

### 9. Дедупликация книг
**Decision**: Сравнение по normalized название + normalized автор (если автор извлечён)
**Rationale**:
- Нормализация (lowercase, trim, удаление лишних пробелов) предотвращает ложные дубликаты
- Соответствует требованиям спецификации (название И автор)
**Alternatives considered**:
- Хэширование контента — слишком строгое, не учитывает разные издания
- Fuzzy matching — может давать ложные срабатывания

---

## Best Practices Summary

### Backend
- FastAPI с async endpoints для I/O операций (парсинг файлов)
- Background tasks для длительных операций (парсинг больших книг)
- SQLAlchemy ORM для работы с PostgreSQL
- Alembic для миграций БД
- Pydantic для валидации схем

### Frontend
- React с функциональными компонентами и hooks
- TypeScript для типизации
- Tailwind CSS для стилизации
- React Query для API запросов
- React Router для навигации

### Testing
- Backend: pytest с async support, factory_boy для fixtures
- Frontend: Vitest + React Testing Library
- E2E: Playwright для критических пользовательских сценариев

### Performance
- Ленивая подгрузка чанков в reader
- Виртуализация списка книг при большом количестве (>50)
- Кэширование метаданных на backend
- Индексация PostgreSQL для поиска по названию/автору
