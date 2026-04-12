# Известные проблемы и решения: EPUB/FB2 загрузка

## Проблема 1: TypeError: unhashable type: 'dict' при парсинге EPUB

**Дата обнаружения**: 2026-04-12
**Файл**: `src/services/epub_parser.py`
**Симптом**: Загрузка EPUB файла вызывает `500 Internal Server Error` с ошибкой `unhashable type: 'dict'`

### Причина

В `ebooklib` метод `book.get_metadata(namespace, name)` принимает **два строковых аргумента**:
```python
# ❌ НЕПРАВИЛЬНО — вызывает TypeError
metadata = book.get_metadata("DC", {})  # dict не может быть ключом

# ✅ ПРАВИЛЬНО — строка как второй аргумент
titles = book.get_metadata("DC", "title")
creators = book.get_metadata("DC", "creator")
```

Метод `get_metadata` использует второй аргумент как ключ для внутреннего dict:
```python
# Внутри ebooklib/epub.py:
def get_metadata(self, namespace, name):
    return self.metadata[namespace].get(name, [])
    # name используется как dict ключ — dict не может быть ключом
```

Это НЕочевидно из документации ebooklib — нет примеров использования `get_metadata`.

### Решение

```python
# src/services/epub_parser.py

# Извлекаем метаданные по одному полю за вызов
titles = book.get_metadata("DC", "title")     # [('Frankenstein', {})]
creators = book.get_metadata("DC", "creator") # [('Mary Shelley', {})]

# Каждый элемент — кортеж (значение, атрибуты)
title = titles[0][0] if titles else file_path.stem
author = ", ".join([c[0] for c in creators]) if creators else None
```

### Как избежать повторения

1. **Тесты с реальными файлами** — добавлены в `tests/fixtures/pg84.epub`
2. **Unit-тесты** — `tests/unit/test_epub_parser.py` содержит `TestEpubParserRealFile`
3. **Интеграционные тесты** — `tests/integration/test_book_upload.py` содержит `TestRealFileUpload`

### Тестовые файлы

Реальные файлы для тестирования находятся в `backend/tests/fixtures/`:
- `pg84.epub` — «Франкенштейн» Мэри Шелли (проект Гутенберг, pg84)
- `867660.fb2` — FB2 файл для тестирования FB2 парсера

---

## Проблема 2: Временный файл удаляется до чанкинга

**Дата обнаружения**: 2026-04-12
**Файл**: `src/services/book_service.py`
**Симптом**: EPUB загружается, но чанки не создаются / ошибка при чтении удалённого файла

### Причина

В `upload_book()` временный файл удалялся (`tmp_path.unlink()`) **до** вызова `_extract_html_content()`. Для EPUB парсер пытается читать файл с диска, который уже удалён.

### Решение

Переместил `tmp_path.unlink()` в блок `finally` после всех операций:

```python
try:
    metadata = self._parse_metadata(tmp_path, file_format)
    # ... создание книги, обработка обложки ...
    # Чанкинг — ДО удаления временного файла
    if file_format in ("epub", "fb2"):
        html_content = self._extract_html_content(tmp_path, file_format, content)
        # ...
finally:
    tmp_path.unlink(missing_ok=True)  # Удаляем ПОСЛЕ всех операций
```

---

## Проблема 3: Alembic migration — AttributeError: 'NoneType' object has no attribute 'dialect'

**Дата обнаружения**: 2026-04-12
**Файл**: `alembic/versions/001_initial.py`
**Симптом**: Миграция падает при создании enum типа

### Причина

`postgresql.ENUM(..., create_type=True).create()` не имеет доступа к connection в контексте alembic.

### Решение

```python
# ❌ НЕПРАВИЛЬНО
fileformat_enum = postgresql.ENUM('txt', 'epub', 'fb2', name='fileformat', create_type=True)
fileformat_enum.create()  # Нет доступа к connection

# ✅ ПРАВИЛЬНО — через SQL
op.execute("CREATE TYPE fileformat AS ENUM ('txt', 'epub', 'fb2')")
```

В downgrade:
```python
# ❌ НЕПРАВИЛЬНО
fileformat_enum.drop()

# ✅ ПРАВИЛЬНО
op.execute("DROP TYPE fileformat")
```

---

## Проблема 4: Отсутствует pydantic-settings в requirements.txt

**Симптом**: `ModuleNotFoundError: No module named 'pydantic_settings'`

### Решение

Добавить в `requirements.txt`:
```
pydantic-settings>=2.0.0
```

Обновить версию pydantic (требуется >= 2.7 для pydantic-settings):
```
pydantic==2.12.5
```

---

## Проблема 5: Alembic ini — KeyError: 'formatters'

**Симптом**: Alembic падает при загрузке конфигурации

### Причина

В `alembic.ini` отсутствовали секции логгеров `[loggers]`, `[handlers]`, `[formatters]`.

### Решение

Добавить в `alembic.ini`:
```ini
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```
