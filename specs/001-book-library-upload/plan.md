# Implementation Plan: Базовая библиотека книг и загрузка файлов

**Branch**: `001-book-library-upload` | **Date**: 2026-04-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-book-library-upload/spec.md`

## Summary

Реализация веб-приложения для локального управления библиотекой книг с поддержкой загрузки файлов (.txt, .epub, .fb2), извлечения метаданных, чтения с динамической подгрузкой чанков и поиска. Backend на Python/FastAPI, frontend на TypeScript/Vite/Tailwind.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: 
  - Backend: FastAPI, Uvicorn, SQLAlchemy (PostgreSQL), lxml (XML parsing для epub/fb2), ebooklib (epub), Pillow (обложки)
  - Frontend: Vite, React, Tailwind CSS, React Query
  - Парсинг больших книг: кастомный чанкер для разбиения на segments
**Storage**: PostgreSQL для метаданных книг и позиций чтения; файлы книг хранятся локально в директории приложения
**Testing**: pytest (backend), Vitest + React Testing Library (frontend), Playwright (E2E)
**Target Platform**: Windows 10 (локальное веб-приложение), браузер Chrome/Edge
**Project Type**: Web-service (frontend + backend)
**Performance Goals**: 
  - Загрузка книги до 50 МБ < 10 сек (локальный файл)
  - Поиск < 1 секунды
  - Рендеринг чанков в режиме чтения < 200ms
**Constraints**: 
  - Локальная работа без облачных зависимостей
  - Макс. размер файла 50 МБ
  - Память: динамическая подгрузка чанков для книг >100 МБ
  - Offline-capable (кроме загрузки по ссылке)
**Scale/Scope**: Один пользователь, локальная библиотека (десятки-сотни книг)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

### Gate 1: Простота (Simplicity)
- ✅ Минимально достаточное решение: FastAPI + React без избыточной абстракции
- ✅ Нет преждевременной оптимизации — чанкинг только для больших книг
- ✅ Data model минималистичен (2 сущности: Book, BookChunk)
- **Status**: PASS ✅

### Gate 2: Feature-ветки (Feature Branches)
- ✅ Ветка `001-book-library-upload` создана
- ✅ Слияние только после ревью и тестов
- **Status**: PASS ✅

### Gate 3: TDD: тесты до кода (NON-NEGOTIABLE)
- ✅ pytest + Vitest определены в Technical Context
- ✅ Quickstart содержит инструкции по TDD workflow
- ✅ Contracts определены ДО реализации (contract-first)
- **Status**: PASS ✅ (resolved from Phase 0)

### Gate 4: Запуск тестов (Run Tests After Changes)
- ✅ pytest и Vitest будут запускаться после каждого изменения
- ✅ Quickstart содержит команды для запуска тестов
- **Status**: PASS ✅

### Gate 5: Документация и стиль кода (Documentation & Code Style)
- ✅ Вся документация на русском языке (spec, research, data-model, quickstart)
- ✅ Docstrings в стиле Google Docstring на русском (будет применяться в коде)
- ✅ Именованные аргументы в функциях (будет применяться в коде)
- **Status**: PASS ✅

### Gate 6: Controller > Service > CRUD
- ✅ Backend структура: Controllers → Services → Repositories
- ✅ Data model чётко разделяет модели и схемы
- ✅ API contracts соответствуют REST принцип
- **Status**: PASS ✅

### Gate 7: Локальность (Local-First)
- ✅ Приложение работает локально на Windows 10
- ✅ PostgreSQL запускается локально
- ✅ Нет облачных зависимостей (кроме загрузки книг по ссылке — это часть функциональности)
- ✅ Файлы хранятся локально в `storage/`
- ✅ Все AI-модели (если будут добавлены) запускаются локально
- **Status**: PASS ✅

### Gate 8: Технологический стек
- ✅ Backend: Python 3.11+ + FastAPI + Uvicorn
- ✅ Frontend: TypeScript + Vite + Tailwind CSS
- ✅ База данных: PostgreSQL
- ✅ Все зависимости совместимы и доступны локально
- **Status**: PASS ✅

**Overall Constitution Check**: ✅ ALL GATES PASS (без нарушений)

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── controllers/          # FastAPI routes (загрузка, библиотека, чтение)
│   ├── services/             # Бизнес-логика (парсинг книг, чанкинг, метаданные)
│   ├── repositories/         # SQLAlchemy CRUD операции
│   ├── models/               # SQLAlchemy модели (Book, Library)
│   ├── schemas/              # Pydantic схемы для request/response
│   └── utils/                # Утилиты (парсинг epub/fb2, валидация файлов)
├── tests/
│   ├── unit/                 # Unit-тесты (services, utils)
│   ├── integration/          # Интеграционные тесты (API endpoints)
│   └── conftest.py           # Fixtures и тестовые данные
└── app/
    ├── main.py               # Точка входа FastAPI
    └── config.py             # Конфигурация приложения

frontend/
├── src/
│   ├── components/           # React компоненты (BookCard, BookList, UploadForm)
│   ├── pages/                # Страницы (LibraryPage, ReaderPage, UploadPage)
│   ├── services/             # API клиенты (books API, upload API)
│   ├── hooks/                # Кастомные React hooks
│   ├── types/                # TypeScript типы
│   └── utils/                # Утилиты (форматирование, валидация)
├── tests/
│   ├── unit/                 # Component unit tests
│   └── integration/          # API integration tests
└── vite.config.ts
```

**Structure Decision**: Выбрана Option 2: Web application (frontend + backend) с чётким разделением ответственности. Backend обеспечивает REST API для управления библиотекой, frontend предоставляет пользовательский интерфейс.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
