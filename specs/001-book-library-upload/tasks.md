# Tasks: Базовая библиотека книг и загрузка файлов

**Input**: Design documents from `/specs/001-book-library-upload/`
**Prerequisites**: plan.md (✅), spec.md (✅), research.md (✅), data-model.md (✅), contracts/api-contracts.md (✅)

**Tests**: TDD подход (тесты до кода) — NON-NEGOTIABLE согласно конституции проекта.

**Organization**: Задачи организованы по user stories (US1, US2, US3) для независимой реализации и тестирования.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Можно выполнять параллельно (разные файлы, нет зависимостей)
- **[Story]**: Какая user story (US1, US2, US3)
- Указаны точные пути к файлам

## Path Conventions

- **Backend**: `backend/src/`, `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Инициализация проекта и базовой структуры

- [ ] T001 [P] Создать структуру директорий backend согласно plan.md: `backend/src/{controllers,services,repositories,models,schemas,utils}`, `backend/tests/{unit,integration}`, `backend/app/`
- [ ] T002 [P] Создать структуру директорий frontend согласно plan.md: `frontend/src/{components,pages,services,hooks,types,utils}`, `frontend/tests/{unit,integration}`
- [ ] T003 Создать `backend/requirements.txt` с зависимостями из quickstart.md (fastapi, uvicorn, sqlalchemy, alembic, psycopg2-binary, lxml, ebooklib, pillow, pytest, и др.)
- [ ] T004 Создать `frontend/package.json` с зависимостями из quickstart.md (react, react-router-dom, @tanstack/react-query, axios, vite, tailwindcss, typescript, vitest)
- [ ] T005 [P] Настроить `backend/app/config.py` для управления конфигурацией через переменные окружения (DATABASE_URL, BOOKS_STORAGE_PATH, COVERS_STORAGE_PATH)
- [ ] T006 [P] Создать `backend/.env.example` с шаблоном конфигурации
- [ ] T007 [P] Создать `frontend/.env.local` с `VITE_API_BASE_URL=http://localhost:8000/api/v1`
- [ ] T008 [P] Настроить Tailwind CSS в frontend (`frontend/tailwind.config.ts`, `frontend/postcss.config.js`)
- [ ] T009 [P] Настроить Vite в frontend (`frontend/vite.config.ts`)
- [ ] T010 Настроить `frontend/tsconfig.json` для TypeScript

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Критическая инфраструктура, необходимая для ВСЕХ user stories

**⚠️ CRITICAL**: Нельзя начинать user stories до завершения этой фазы

- [ ] T011 Инициализировать Alembic для миграций БД: создать `backend/alembic.ini` и `backend/alembic/env.py` с настройкой PostgreSQL
- [ ] T012 Создать модель Book в `backend/src/models/book.py` (SQLAlchemy модель согласно data-model.md: id, title, author, file_path, file_format, file_size, cover_image_path, cover_thumbnail_path, date_added, last_reading_position)
- [ ] T013 Создать модель BookChunk в `backend/src/models/book_chunk.py` (SQLAlchemy модель: id, book_id, chunk_index, content_html, word_count)
- [ ] T014 Создать первую миграцию Alembic для таблиц books и book_chunks
- [ ] T015 [P] Создать Pydantic схемы в `backend/src/schemas/book.py`: BookCreate, BookUpdate, BookDTO, BookListDTO (согласно data-model.md)
- [ ] T016 Создать базовый репозиторий BookRepository в `backend/src/repositories/book_repository.py` с методами: get_all, get_by_id, add, delete, update, check_duplicate, search
- [ ] T017 [P] Настроить CORS middleware в `backend/app/main.py` для подключения frontend (localhost:5173)
- [ ] T018 [P] Создать `backend/app/main.py` с базовым FastAPI приложением и health check endpoint `/health`
- [ ] T019 [P] Создать утилиту валидации файлов в `backend/src/utils/file_validator.py` (проверка формата: txt|epub|fb2, проверка размера ≤50 МБ)
- [ ] T020 Настроить директорию хранения файлов: создать `storage/{books,covers,thumbnails}` и утилиты для генерации путей в `backend/src/utils/storage.py`
- [ ] T021 Создать базовый API клиент в `frontend/src/services/apiClient.ts` (axios instance с baseURL из env)
- [ ] T022 [P] Создать TypeScript типы в `frontend/src/types/book.ts` (BookDTO, BookListDTO, ReadingPosition, ErrorResponse)

**Checkpoint**: Foundation готова — можно начинать user stories

---

## Phase 3: User Story 1 — Загрузка книг в библиотеку (Priority: P1) 🎯 MVP

**Goal**: Пользователь может загрузить книгу из локального файла или по ссылке, система извлекает метаданные и обложку, книга появляется в библиотеке

**Independent Test**: Пользователь может загрузить хотя бы одну книгу (.epub) и увидеть её в списке с корректным названием и автором

### Тесты для User Story 1 (TDD — писать ДО кода) ⚠️

> **NOTE: Написать эти тесты ПЕРВЫМИ, убедиться что они ПАДАЮТ перед реализацией**

- [ ] T023 [P] [US1] Unit-тест file_validator в `backend/tests/unit/test_file_validator.py` (валидные форматы, превышение размера, неподдерживаемый формат)
- [ ] T024 [P] [US1] Unit-тест epub parser в `backend/tests/unit/test_epub_parser.py` (извлечение названия, автора, обложки, обработка повреждённых файлов)
- [ ] T025 [P] [US1] Unit-тест fb2 parser в `backend/tests/unit/test_fb2_parser.py` (извлечение названия, автора, обложки, обработка повреждённых файлов)
- [ ] T026 [P] [US1] Unit-тест txt parser в `backend/tests/unit/test_txt_parser.py` (название из filename, нет автора/обложки)
- [ ] T027 [P] [US1] Unit-тест book chunking service в `backend/tests/unit/test_chunking_service.py` (разбиение на чанки по главам, fallback на фиксированный размер)
- [ ] T028 [US1] Интеграционный тест upload endpoint в `backend/tests/integration/test_book_upload.py` (успешная загрузка файла, дубликат, превышение размера, неподдерживаемый формат, повреждённый файл)
- [ ] T029 [P] [US1] Unit-тест useUpload hook в `frontend/tests/unit/test_useUpload.test.tsx` (успешная загрузка, ошибка, прогресс)

### Реализация для User Story 1

#### Backend — Парсеры и сервисы
- [ ] T030 [P] [US1] Создать сервис парсинга EPUB в `backend/src/services/epub_parser.py` (извлечение метаданных: title, author, cover через ebooklib)
- [ ] T031 [P] [US1] Создать сервис парсинга FB2 в `backend/src/services/fb2_parser.py` (извлечение метаданных: title, author, cover через lxml XML parsing)
- [ ] T032 [P] [US1] Создать сервис парсинга TXT в `backend/src/services/txt_parser.py` (название из filename, нет автора/обложки)
- [ ] T033 [US1] Создать сервис обработки изображений в `backend/src/services/cover_processor.py` (извлечение обложки, создание миниатюры 200x300 через Pillow)
- [ ] T034 [US1] Создать сервис чанкинга книг в `backend/src/services/chunking_service.py` (разбиение по главам, fallback на ~5000 слов, генерация HTML chunks)
- [ ] T035 [US1] Создать BookService в `backend/src/services/book_service.py` (бизнес-логика загрузки: валидация → парсинг → чанкинг → сохранение, проверка на дубликаты)

#### Backend — Controllers
- [ ] T036 [US1] Создать BookController в `backend/src/controllers/book_controller.py` с endpoint POST `/api/v1/books/upload` (multipart/form-data upload)
- [ ] T037 [US1] Добавить endpoint POST `/api/v1/books/upload-from-url` в BookController (загрузка по ссылке через httpx)

#### Frontend — Компоненты загрузки
- [ ] T038 [P] [US1] Создать компонент UploadForm в `frontend/src/components/UploadForm.tsx` (выбор файла, drag-and-drop, индикатор прогресса)
- [ ] T039 [P] [US1] Создать компонент UrlUploadForm в `frontend/src/components/UrlUploadForm.tsx` (ввод URL, валидация)
- [ ] T040 [US1] Создать hook useUpload в `frontend/src/hooks/useUpload.ts` (логика загрузки файла/URL, обработка ошибок, прогресс)
- [ ] T041 [US1] Создать страницу UploadPage в `frontend/src/pages/UploadPage.tsx` (объединяет UploadForm + UrlUploadForm)
- [ ] T042 [US1] Настроить React Query client в `frontend/src/services/bookApi.ts` (mutation для uploadBook, uploadBookFromUrl)

**Checkpoint**: User Story 1 полностью функциональна — можно загрузить книгу и увидеть в БД

---

## Phase 4: User Story 2 — Просмотр и управление библиотекой (Priority: P2)

**Goal**: Пользователь видит список книг в виде карточек/списка, может открыть для чтения, удалить, переименовать

**Independent Test**: При наличии загруженных книг пользователь может увидеть их в списке, открыть для чтения и переименовать

### Тесты для User Story 2 (TDD — писать ДО кода) ⚠️

- [ ] T043 [P] [US2] Unit-тест BookRepository search/duplicate methods в `backend/tests/unit/test_book_repository.py`
- [ ] T044 [P] [US2] Unit-тест reading position service в `backend/tests/unit/test_reading_position_service.py`
- [ ] T045 [US2] Интеграционный тест library endpoints в `backend/tests/integration/test_library_operations.py` (GET список, PATCH rename, DELETE, GET chunks, GET/POST reading position)
- [ ] T046 [P] [US2] Unit-тест BookCard component в `frontend/tests/unit/test_BookCard.test.tsx`
- [ ] T047 [P] [US2] Unit-тест BookList component в `frontend/tests/unit/test_BookList.test.tsx`

### Реализация для User Story 2

#### Backend — Сервисы и Controllers
- [ ] T048 [P] [US2] Создать ReadingPositionService в `backend/src/services/reading_position_service.py` (сохранение/получение позиции чтения)
- [ ] T049 [US2] Добавить endpoint GET `/api/v1/books` в BookController (с пагинацией и поиском)
- [ ] T050 [US2] Добавить endpoint GET `/api/v1/books/{book_id}` в BookController
- [ ] T051 [US2] Добавить endpoint PATCH `/api/v1/books/{book_id}` в BookController (переименование)
- [ ] T052 [US2] Добавить endpoint DELETE `/api/v1/books/{book_id}` в BookController (удаление записи, файл не трогать)
- [ ] T053 [US2] Добавить endpoint GET `/api/v1/books/{book_id}/chunks` в BookController (получение чанков для чтения)
- [ ] T054 [US2] Добавить endpoints POST/GET `/api/v1/books/{book_id}/reading-position` в BookController

#### Frontend — Компоненты библиотеки
- [ ] T055 [P] [US2] Создать компонент BookCard в `frontend/src/components/BookCard.tsx` (отображение книги: обложка, название, автор, кнопки действий)
- [ ] T056 [P] [US2] Создать компонент BookListView в `frontend/src/components/BookListView.tsx` (список книг в виде таблицы)
- [ ] T057 [P] [US2] Создать компонент BookGridView в `frontend/src/components/BookGridView.tsx` (сетка карточек)
- [ ] T058 [US2] Создать компонент ViewToggle в `frontend/src/components/ViewToggle.tsx` (переключение карточки/список)
- [ ] T059 [US2] Создать страницу LibraryPage в `frontend/src/pages/LibraryPage.tsx` (основная страница: ViewToggle + BookGridView/BookListView, загрузка данных через React Query)
- [ ] T060 [US2] Настроить React Query queries в `frontend/src/services/bookApi.ts` (getBooks, getBook, updateBook, deleteBook)
- [ ] T061 [US2] Создать компонент RenameDialog в `frontend/src/components/RenameDialog.tsx` (модальное окно для переименования)
- [ ] T062 [US2] Создать компонент ConfirmDialog в `frontend/src/components/ConfirmDialog.tsx` (подтверждение удаления)

#### Frontend — Reader Page
- [ ] T063 [US2] Создать страницу ReaderPage в `frontend/src/pages/ReaderPage.tsx` (режим чтения: загрузка чанков, вертикальная прокрутка, сохранение позиции)
- [ ] T064 [US2] Создать hook useChunkLoader в `frontend/src/hooks/useChunkLoader.ts` (динамическая подгрузка видимых чанков ± 2 соседних, выгрузка невидимых)
- [ ] T065 [US2] Создать компонент ReadingProgress в `frontend/src/components/ReadingProgress.tsx` (индикатор прогресса чтения)

**Checkpoint**: User Stories 1 AND 2 работают независимо

---

## Phase 5: User Story 3 — Поиск по библиотеке (Priority: P3)

**Goal**: Пользователь может искать книги по названию и имени автора, получать отфильтрованные результаты

**Independent Test**: При наличии нескольких книг пользователь может ввести часть названия/автора и увидеть отфильтрованный список

### Тесты для User Story 3 (TDD — писать ДО кода) ⚠️

- [ ] T066 [P] [US3] Unit-тест BookRepository search method в `backend/tests/unit/test_book_repository_search.py` (совпадения по title, author, без результатов, очистка поиска)
- [ ] T067 [US3] Интеграционный тест search endpoint в `backend/tests/integration/test_book_search.py` (параметр search, пагинация с поиском)

### Реализация для User Story 3

#### Backend
- [ ] T068 [US3] Реализовать метод search в BookRepository (`backend/src/repositories/book_repository.py`) — SQL запрос с ILIKE по title и author, индексация для производительности

#### Frontend
- [ ] T069 [P] [US3] Создать компонент SearchBar в `frontend/src/components/SearchBar.tsx` (поисковая строка с debounce 300ms)
- [ ] T070 [P] [US3] Создать компонент NoResultsMessage в `frontend/src/components/NoResultsMessage.tsx` (сообщение "Ничего не найдено")
- [ ] T071 [US3] Интегрировать SearchBar в LibraryPage в `frontend/src/pages/LibraryPage.tsx` (фильтрация через React Query с параметром search)
- [ ] T072 [US3] Обновить React Query query в `frontend/src/services/bookApi.ts` (getBooks с параметром search)

**Checkpoint**: Все user stories работают независимо

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Улучшения, затрагивающие несколько user stories

- [ ] T073 [P] Создать компонент ErrorBoundary в `frontend/src/components/ErrorBoundary.tsx` (обработка ошибок рендеринга)
- [ ] T074 [P] Создать компонент LoadingSpinner в `frontend/src/components/LoadingSpinner.tsx` (индикатор загрузки)
- [ ] T075 [P] Создать компонент ToastNotification в `frontend/src/components/ToastNotification.tsx` (уведомления об ошибках/успехе)
- [ ] T076 Настроить React Router в `frontend/src/App.tsx` (маршруты: /, /upload, /books/:id/read)
- [ ] T077 Добавить placeholder image для книг без обложки в `frontend/public/default-cover.svg`
- [ ] T078 [P] Написать E2E тесты в `tests/e2e/test_upload_and_read_flow.spec.ts` (Playwright: загрузка → просмотр → чтение)
- [ ] T079 [P] Написать E2E тесты в `tests/e2e/test_library_management.spec.ts` (Playwright: переименование, удаление, поиск)
- [ ] T080 Задокументировать API в `backend/README.md` (ссылки на contracts, примеры использования)
- [ ] T081 Запустить quickstart.md validation — проверить, что приложение запускается согласно инструкции
- [ ] T082 Финальный запуск всех тестов: `cd backend && pytest` + `cd frontend && npm test`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Нет зависимостей — можно начинать сразу
- **Foundational (Phase 2)**: Зависит от Setup — БЛОКИРУЕТ все user stories
- **User Stories (Phase 3+)**: Все зависят от завершения Foundational
  - User stories могут идти параллельно (если есть ресурсы)
  - Или последовательно в порядке приоритета: P1 → P2 → P3
- **Polish (Final Phase)**: Зависит от завершения всех нужных user stories

### User Story Dependencies

```
Phase 1: Setup ──→ Phase 2: Foundational ──┬──→ Phase 3: US1 (P1) ──┬──→ Phase 6: Polish
                                            ├──→ Phase 4: US2 (P2) ──┤
                                            └──→ Phase 5: US3 (P3) ──┘
```

- **User Story 1 (P1)**: Можно начинать после Foundational — нет зависимостей от других stories
- **User Story 2 (P2)**: Можно начинать после Foundational — интегрируется с US1, но тестируется независимо
- **User Story 3 (P3)**: Можно начинать после Foundational — использует components из US2 (LibraryPage)

### Within Each User Story

1. Тесты ДО КОДА (Red-Green-Refactor)
2. Модели → Сервисы → Endpoints/Компоненты
3. Ядро реализации → Интеграция
4. Story завершена → Переход к следующей

### Parallel Opportunities

- Все Setup задачи с [P] — параллельно (T001-T010)
- Все Foundational задачи с [P] — параллельно (T015, T017-T019)
- US1 тесты T023-T027 — параллельно (разные файлы)
- US1 парсеры T030-T032 — параллельно (разные форматы)
- US2 компоненты T055-T057 — параллельно (разные компоненты)
- US3 компоненты T069-T070 — параллельно

---

## Parallel Example: User Story 1

```bash
# Запустить все тесты для US1 параллельно:
Task: "Unit-тест file_validator в backend/tests/unit/test_file_validator.py"
Task: "Unit-тест epub parser в backend/tests/unit/test_epub_parser.py"
Task: "Unit-тест fb2 parser в backend/tests/unit/test_fb2_parser.py"
Task: "Unit-тест txt parser в backend/tests/unit/test_txt_parser.py"
Task: "Unit-тест chunking service в backend/tests/unit/test_chunking_service.py"

# Запустить парсеры параллельно:
Task: "Сервис парсинга EPUB в backend/src/services/epub_parser.py"
Task: "Сервис парсинга FB2 в backend/src/services/fb2_parser.py"
Task: "Сервис парсинга TXT в backend/src/services/txt_parser.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Завершить Phase 1: Setup
2. Завершить Phase 2: Foundational (CRITICAL — блокирует всё)
3. Завершить Phase 3: User Story 1
4. **СТОП и ВАЛИДАЦИЯ**: Протестировать US1 — загрузить .epub файл, увидеть в списке
5. Deploy/demo если готово

### Incremental Delivery

1. Setup + Foundational → Foundation готова
2. Добавить US1 → Протестировать → Deploy/Demo (MVP! 🎯)
3. Добавить US2 → Протестировать → Deploy/Demo
4. Добавить US3 → Протестировать → Deploy/Demo
5. Каждая story добавляет ценность, не ломая предыдущие

### Parallel Team Strategy

С несколькими разработчиками:

1. Команда завершает Setup + Foundational вместе
2. После Foundational:
   - Разработчик A: User Story 1
   - Разработчик B: User Story 2
   - Разработчик C: User Story 3
3. Stories завершаются и интегрируются независимо

---

## Summary

**Всего задач**: 82

**По фазам**:
- Phase 1 (Setup): 10 задач
- Phase 2 (Foundational): 12 задач
- Phase 3 (US1): 20 задач (7 тестов + 13 реализации)
- Phase 4 (US2): 23 задач (5 тестов + 18 реализации)
- Phase 5 (US3): 7 задач (2 теста + 5 реализации)
- Phase 6 (Polish): 10 задач

**Параллельные возможности**: 25+ задач с标记 [P] можно выполнять параллельно

**Independent Test Criteria**:
- US1: Загрузить .epub → увидеть в списке с названием и автором
- US2: Открыть библиотеку → увидеть карточки → открыть книгу → переименовать → удалить
- US3: Ввести поисковый запрос → увидеть отфильтрованные результаты

**MVP Scope**: Phase 1 + Phase 2 + Phase 3 (US1) = 42 задачи

---

## Notes

- [P] задачи = разные файлы, нет зависимостей — можно параллелить
- [Story] label связывает задачу с user story для трассировки
- Каждая user story独立 завершаема и тестируема
- Тесты писать ДО кода (TDD: Red-Green-Refactor)
- Commit после каждой задачи или логической группы
- Остановиться на любом checkpoint для валидации story
- Избегать: размытых задач, конфликтов файлов, cross-story зависимостей
