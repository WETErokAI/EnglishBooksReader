/**
 * Unit-тесты компонентов BookListView и BookListRow.
 *
 * Проверяет:
 * - BookListView: рендер списка/таблицы
 * - BookListView: пустой список
 * - BookListRow: рендер строки с обложкой, названием, автором, форматом, датой
 * - BookListRow: обработка кликов (read, rename, delete)
 * - BookListRow: автор по умолчанию "—" когда null
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { BookListView } from '../../src/components/BookListView';
import { BookListRow } from '../../src/components/BookListRow';
import type { BookDTO } from '../../src/types/book';

const createBook = (overrides: Partial<BookDTO> = {}): BookDTO => ({
  id: '550e8400-e29b-41d4-a716-446655440000',
  title: 'The Great Gatsby',
  author: 'F. Scott Fitzgerald',
  file_format: 'epub',
  cover_thumbnail_path: 'cover-123.jpg',
  date_added: '2026-01-01T10:00:00Z',
  ...overrides,
});

describe('BookListView', () => {
  let onRead: ReturnType<typeof vi.fn>;
  let onRename: ReturnType<typeof vi.fn>;
  let onDelete: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    onRead = vi.fn();
    onRename = vi.fn();
    onDelete = vi.fn();
    vi.clearAllMocks();
  });

  // ===== Пустой список =====

  it('должен отобразить сообщение когда нет книг', () => {
    render(
      <BookListView
        books={[]}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    expect(screen.getByText('Нет книг для отображения')).toBeInTheDocument();
  });

  it('не должен рендерить таблицу когда нет книг', () => {
    const { container } = render(
      <BookListView
        books={[]}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    const table = container.querySelector('table');
    expect(table).not.toBeInTheDocument();
  });

  // ===== Список с книгами =====

  it('должен отрендерить таблицу когда есть книги', () => {
    render(
      <BookListView
        books={[createBook()]}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    expect(screen.getByRole('table')).toBeInTheDocument();
  });

  it('должен отрендерить заголовки таблицы', () => {
    render(
      <BookListView
        books={[createBook()]}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    expect(screen.getByText('Обложка')).toBeInTheDocument();
    expect(screen.getByText('Название')).toBeInTheDocument();
    expect(screen.getByText('Автор')).toBeInTheDocument();
    expect(screen.getByText('Формат')).toBeInTheDocument();
    expect(screen.getByText('Дата добавления')).toBeInTheDocument();
    expect(screen.getByText('Действия')).toBeInTheDocument();
  });

  it('должен отрендерить все книги из списка', () => {
    const books = [
      createBook({ id: '1', title: 'Book One' }),
      createBook({ id: '2', title: 'Book Two' }),
      createBook({ id: '3', title: 'Book Three' }),
    ];

    render(
      <BookListView
        books={books}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    expect(screen.getByTitle('Book One')).toBeInTheDocument();
    expect(screen.getByTitle('Book Two')).toBeInTheDocument();
    expect(screen.getByTitle('Book Three')).toBeInTheDocument();
  });

  it('должен передать корректные props в BookListRow для каждой книги', () => {
    const book = createBook({ id: 'test-id-123' });

    render(
      <BookListView
        books={[book]}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    // Кнопка "Читать" должна вызвать onRead с правильным ID
    const readButton = screen.getByLabelText('Читать The Great Gatsby');
    fireEvent.click(readButton);

    expect(onRead).toHaveBeenCalledWith('test-id-123');
  });

  // ===== Разные форматы отображения =====

  it.each([
    ['txt', 'txt'],
    ['epub', 'epub'],
    ['fb2', 'fb2'],
  ])('должен отобразить формат %s в таблице', (format, expected) => {
    render(
      <BookListView
        books={[createBook({ file_format: format as BookDTO['file_format'] })]}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    // Формат в BookListRow рендерится в нижнем регистре
    expect(screen.getByText(expected)).toBeInTheDocument();
  });
});

describe('BookListRow', () => {
  let onRead: ReturnType<typeof vi.fn>;
  let onRename: ReturnType<typeof vi.fn>;
  let onDelete: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    onRead = vi.fn();
    onRename = vi.fn();
    onDelete = vi.fn();
    vi.clearAllMocks();
  });

  // ===== Рендер =====

  it('должен отрендерить название книги в строке', () => {
    render(
      <BookListRow
        book={createBook()}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    expect(screen.getByTitle('The Great Gatsby')).toBeInTheDocument();
  });

  it('должен отрендерить автора в строке', () => {
    render(
      <BookListRow
        book={createBook()}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    expect(screen.getByText('F. Scott Fitzgerald')).toBeInTheDocument();
  });

  it('должен отобразить "—" когда автор null', () => {
    render(
      <BookListRow
        book={createBook({ author: null })}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    expect(screen.getByText('—')).toBeInTheDocument();
  });

  it('должен отрендерить формат файла', () => {
    render(
      <BookListRow
        book={createBook()}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    // Формат в BookListRow рендерится в нижнем регистре
    expect(screen.getByText('epub')).toBeInTheDocument();
  });

  it('должен отрендерить дату добавления', () => {
    render(
      <BookListRow
        book={createBook({ date_added: '2026-01-15T10:00:00Z' })}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    // В jsdom с locale по умолчанию: "15.01.2026"
    expect(screen.getByText('15.01.2026')).toBeInTheDocument();
  });

  it('должен отрендерить обложку', () => {
    render(
      <BookListRow
        book={createBook()}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    const img = screen.getByAltText('The Great Gatsby') as HTMLImageElement;
    expect(img).toBeInTheDocument();
    expect(img.src).toContain('/api/v1/static/covers/cover-123.jpg');
  });

  it('должен использовать default-cover.svg когда cover_thumbnail_path = null', () => {
    render(
      <BookListRow
        book={createBook({ cover_thumbnail_path: null })}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    const img = screen.getByAltText('The Great Gatsby') as HTMLImageElement;
    expect(img.src).toContain('/default-cover.svg');
  });

  // ===== Обработка кликов =====

  it('должен вызвать onRead при клике на кнопку "Читать"', () => {
    render(
      <BookListRow
        book={createBook()}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    const readButton = screen.getByLabelText('Читать The Great Gatsby');
    fireEvent.click(readButton);

    expect(onRead).toHaveBeenCalledWith('550e8400-e29b-41d4-a716-446655440000');
  });

  it('должен вызвать onRename при клике на кнопку переименования', () => {
    render(
      <BookListRow
        book={createBook()}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    const renameButton = screen.getByLabelText('Переименовать The Great Gatsby');
    fireEvent.click(renameButton);

    expect(onRename).toHaveBeenCalledWith('550e8400-e29b-41d4-a716-446655440000');
  });

  it('должен вызвать onDelete при клике на кнопку удаления', () => {
    render(
      <BookListRow
        book={createBook()}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    const deleteButton = screen.getByLabelText('Удалить The Great Gatsby');
    fireEvent.click(deleteButton);

    expect(onDelete).toHaveBeenCalledWith('550e8400-e29b-41d4-a716-446655440000');
  });

  // ===== CSS классы =====

  it('должен содержать CSS класс строки таблицы', () => {
    const { container } = render(
      <BookListRow
        book={createBook()}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    const row = container.querySelector('tr');
    expect(row).toHaveClass('hover:bg-gray-50');
  });

  // ===== Обработка ошибки обложки =====

  it('должен переключить на default-cover.svg при ошибке загрузки обложки', () => {
    const { container } = render(
      <BookListRow
        book={createBook({ cover_thumbnail_path: 'broken.jpg' })}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    const img = screen.getByAltText('The Great Gatsby') as HTMLImageElement;
    expect(img.src).toContain('/api/v1/static/covers/broken.jpg');

    // Симулируем ошибку загрузки изображения
    fireEvent.error(img);

    expect(img.src).toContain('/default-cover.svg');
  });

  // ===== Разные ID =====

  it('должен использовать уникальный key для каждой книги', () => {
    const books = [
      createBook({ id: 'id-1' }),
      createBook({ id: 'id-2' }),
    ];

    render(
      <BookListView
        books={books}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    const rows = screen.getAllByRole('row');
    // Первая строка — заголовок, остальные — книги
    expect(rows).toHaveLength(3);
  });
});
