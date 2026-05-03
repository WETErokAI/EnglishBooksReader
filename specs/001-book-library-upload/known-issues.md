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

---

## Проблема 6: Генерация тестовых EPUB-файлов создаёт невалидный архив

**Дата обнаружения**: 2026-04-25
**Файл**: `tests/integration/test_book_chunking.py`
**Симптом**: `ebooklib.epub.EpubException: 'Can not find container file'` или `KeyError: "There is no item named '.' in the archive"` при загрузке тестового EPUB

### Причина

EPUB — это специфичный формат ZIP-архива. При ручной генерации через `zipfile` нужно соблюдать **строгие правила**:

1. **`mimetype` должен быть первым файлом в архиве и НЕ сжат** (`compress_type=0`). Это требование спецификации EPUB 3.0. Стандартный `zf.writestr("mimetype", ...)` сжимает файл по умолчанию.
2. **`content.opf` НЕ должен быть в корне архива** — он должен находиться в поддиректории (обычно `OEBPS/`). Библиотека `ebooklib` ищет `container.xml`, затем по пути из него открывает `content.opf`. Если пути не совпадают — ошибка.
3. **HTML-файлы должны быть в той же директории, что и `content.opf`** — если `content.opf` в `OEBPS/`, то и `.xhtml` файлы тоже должны быть в `OEBPS/`.
4. **`container.xml` должен содержать правильный namespace** — `xmlns="urn:oasis:names:tc:opendocument:xmlns:container"`.
5. **`content.opf` должен содержать правильный namespace пакета** — `xmlns="http://www.idpf.org/2007/opf"`.

### Решение

```python
import zipfile
from io import BytesIO

def _create_epub_with_multiple_chapters() -> bytes:
    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_STORED) as zf:
        # 1. mimetype — ОБЯЗАТЕЛЬНО без сжатия, через ZipInfo
        zf.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip")

        # 2. container.xml указывает на OEBPS/content.opf
        zf.writestr("META-INF/container.xml",
            '<?xml version="1.0"?>'
            '<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">'
            '<rootfiles>'
            '<rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>'
            '</rootfiles></container>')

        # 3. content.opf в поддиректории OEBPS/
        zf.writestr("OEBPS/content.opf",
            '<?xml version="1.0"?>'
            '<package version="3.0" unique-id="uid" '
            'xmlns="http://www.idpf.org/2007/opf">'
            '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
            '<dc:identifier id="uid">urn:uuid:test</dc:identifier>'
            '<dc:title>Test Book</dc:title>'
            '<dc:creator>Test Author</dc:creator>'
            '</metadata>'
            '<manifest>'
            '<item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>'
            '</manifest>'
            '<spine><itemref idref="ch1"/></spine>'
            '</package>')

        # 4. HTML-файлы тоже в OEBPS/
        zf.writestr("OEBPS/ch1.xhtml",
            '<html xmlns="http://www.w3.org/1999/xhtml">'
            '<body><h1>Chapter 1</h1><p>Test content.</p></body></html>')

    buf.seek(0)
    return buf.getvalue()
```

### Как проверить валидность EPUB

```python
import zipfile

# Проверить структуру
zf = zipfile.ZipFile("test.epub")
print(zf.namelist())

# Проверить что mimetype без сжатия
info = zf.getinfo("mimetype")
assert info.compress_type == 0, "mimetype должен быть без сжатия!"

# Закрыть архив
zf.close()
```

### Как избежать повторения

1. Использовать **реальный EPUB** (`tests/fixtures/pg84.epub`) как образец структуры
2. Перед коммитом тестовых EPUB-генераторов проверять валидность через `zipfile`
3. Для production-генерации EPUB использовать библиотеку `ebooklib` вместо ручного ZIP

### Полезные ссылки

- Структура реального EPUB: `backend/tests/fixtures/pg84.epub`
- Спецификация EPUB 3.0: https://www.w3.org/TR/epub-33/
- Open Container Format (OCF): https://www.idpf.org/edition/oebps/ocf/

---

## Проблема 7: SQLAlchemy 2.0 — неверный синтаксис передачи bind-параметров

**Дата обнаружения**: 2026-04-25
**Файл**: `tests/integration/test_book_chunking.py`
**Симптом**: `sqlalchemy.exc.InvalidRequestError: A value is required for bind parameter 'book_id'`

### Причина

В SQLAlchemy 2.0 метод `.scalar()` **не принимает** аргумент `params=`. Параметры должны передаваться во второй аргумент метода `.execute()`:

```python
# ❌ НЕПРАВИЛЬНО — params= игнорируется, bind parameter остаётся без значения
stmt = text("SELECT COUNT(*) FROM book_chunks WHERE book_id = :book_id")
result = db_session.execute(stmt).scalar(params={"book_id": book_id})

# ✅ ПРАВИЛЬНО — параметры во втором аргументе execute()
stmt = text("SELECT COUNT(*) FROM book_chunks WHERE book_id = :book_id")
result = db_session.execute(stmt, {"book_id": book_id}).scalar()
```

### Решение

Всегда передавать параметры как **второй позиционный аргумент** `.execute()`:

```python
# Общий паттерн
db_session.execute(
    text("SQL с :bind_params"),
    {"bind_param": value}
).scalar()  # или .fetchall(), .first() и т.д.
```

### Как избежать повторения

1. При использовании `sqlalchemy.text()` — всегда проверять сигнатуру `.execute()`
2. SQLAlchemy 2.0 изменил API: параметры больше не передаются через `.scalar(params=...)`
3. Документация: https://docs.sqlalchemy.org/en/20/core/connections.html#sqlalchemy.text

---

## Проблема 8: ebooklib — константа ITEM_DOCUMENT удалена в новых версиях

**Дата обнаружения**: 2026-04-25
**Файл**: `src/services/epub_parser.py`
**Симптом**: `AttributeError: module 'ebooklib.epub' has no attribute 'ITEM_DOCUMENT'`

### Причина

В более новых версиях `ebooklib` (после 0.18) константа `ITEM_DOCUMENT` удалена. Метод `book.get_items_of_type(epub.ITEM_DOCUMENT)` больше не работает.

### Решение

Использовать проверку типа вместо константы:

```python
# ❌ НЕПРАВИЛЬНО — ITEM_DOCUMENT удалён
html_items = book.get_items_of_type(epub.ITEM_DOCUMENT)

# ✅ ПРАВИЛЬНО — проверка по классу
html_items = [item for item in book.get_items() if isinstance(item, epub.EpubHtml)]
```

### Как избежать повторения

1. Всегда использовать `isinstance(item, epub.EpubHtml)` вместо `epub.ITEM_DOCUMENT`
2. Проверять версию `ebooklib` при обновлении зависимости
3. При миграции на новую версию — grep по `ITEM_DOCUMENT` для поиска устаревшего кода

### Полезные ссылки

- Changelog ebooklib: https://github.com/aerkalov/ebooklib/releases
- Классы ebooklib: https://github.com/aerkalov/ebooklib/blob/master/ebooklib/epub.py
