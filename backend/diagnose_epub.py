"""
Диагностический скрипт для проверки работы ebooklib с EPUB файлом.

Запуск:
    python diagnose_epub.py <путь_к_epub_файлу>

Пример:
    python diagnose_epub.py g:\AI\gpt\t\book for test\pg84.epub
"""

import sys
import traceback

def main():
    if len(sys.argv) < 2:
        print("Использование: python diagnose_epub.py <путь_к_epub_файлу>")
        sys.exit(1)

    epub_path = sys.argv[1]
    print(f"Проверяем файл: {epub_path}")
    print("=" * 60)

    # 1. Проверка версии ebooklib
    print("\n[1] Версия ebooklib:")
    try:
        import ebooklib
        version = getattr(ebooklib, '__version__', 'неизвестна')
        print(f"    ebooklib установлен: OK")
        print(f"    Версия: {version}")
    except ImportError:
        print("    ERROR: ebooklib не установлен!")
        sys.exit(1)

    # 2. Проверка доступных констант
    print("\n[2] Доступные константы в ebooklib.epub:")
    import ebooklib.epub as epub
    constants = [x for x in dir(epub) if x.isupper() and not x.startswith('_')]
    print(f"    {constants}")

    # 3. Проверка наличия ITEM_DOCUMENT
    print("\n[3] Проверка ITEM_DOCUMENT:")
    has_item_document = hasattr(epub, 'ITEM_DOCUMENT')
    print(f"    epub.ITEM_DOCUMENT существует: {has_item_document}")
    if not has_item_document:
        print("    WARNING: epub.ITEM_DOCUMENT НЕ НАЙДЕН!")

    # 4. Проверка наличия EpubHtml
    print("\n[4] Проверка EpubHtml:")
    has_epub_html = hasattr(epub, 'EpubHtml')
    print(f"    epub.EpubHtml существует: {has_epub_html}")

    # 5. Попытка прочитать файл
    print("\n[5] Попытка прочитать EPUB файл:")
    try:
        book = epub.read_epub(epub_path)
        print(f"    Файл прочитан: OK")
    except Exception as e:
        print(f"    ERROR при чтении файла: {e}")
        traceback.print_exc()
        sys.exit(1)

    # 6. Проверка get_items
    print("\n[6] get_items():")
    try:
        all_items = list(book.get_items())
        print(f"    Всего items: {len(all_items)}")
        for item in all_items[:5]:
            print(f"      - {type(item).__name__}: {item.file_name}")
    except Exception as e:
        print(f"    ERROR: {e}")
        traceback.print_exc()

    # 7. Проверка get_items_of_type с EpubHtml
    print("\n[7] get_items_of_type(epub.EpubHtml):")
    try:
        html_items = list(book.get_items_of_type(epub.EpubHtml))
        print(f"    HTML items: {len(html_items)}")
        for item in html_items[:5]:
            content = item.get_content()
            print(f"      - {item.get_id()}: {item.file_name}, content_len={len(content)}")
    except Exception as e:
        print(f"    ERROR: {e}")
        traceback.print_exc()

    # 8. Проверка get_items_of_type с несуществующей константой
    print("\n[8] get_items_of_type(epub.ITEM_DOCUMENT) — как было в коде:")
    if has_item_document:
        try:
            doc_items = list(book.get_items_of_type(epub.ITEM_DOCUMENT))
            print(f"    ITEM_DOCUMENT items: {len(doc_items)}")
        except Exception as e:
            print(f"    ERROR: {e}")
    else:
        print("    SKIP: epub.ITEM_DOCUMENT не существует")

    # 9. Проверка типа каждого item
    print("\n[9] Типы всех items:")
    try:
        all_items = list(book.get_items())
        type_counts = {}
        for item in all_items:
            type_name = type(item).__name__
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        for type_name, count in type_counts.items():
            print(f"    {type_name}: {count}")
    except Exception as e:
        print(f"    ERROR: {e}")

    print("\n" + "=" * 60)
    print("Диагностика завершена.")


if __name__ == '__main__':
    main()
