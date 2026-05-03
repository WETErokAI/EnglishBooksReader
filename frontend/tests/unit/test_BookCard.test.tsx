/**
 * Unit-тесты компонента BookCard.
 *
 * Проверяет:
 * - Рендер обложки, названия, автора, формата
 * - Fallback на default-cover.svg при ошибке загрузки обложки
 * - Отображение автора только когда он есть
 * - Обработка кликов (read, rename, delete)
 * - Состояние загрузки обложки (placeholder)
 * - Разные форматы файлов
 * - ARIA labels
 * - CSS классы
 */

import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { BookCard } from '../../src/components/BookCard';
import type { BookDTO } from '../../src/types/book';

// После каждого теста — очистка DOM
afterEach(cleanup);

const createBook = (overrides: Partial<BookDTO> = {}): BookDTO => ({
  id: '550e8400-e29b-41d4-a716-446655440000',
  title: 'The Great Gatsby',
  author: 'F. Scott Fitzgerald',
  file_format: 'epub',
  cover_thumbnail_path: 'cover-123.jpg',
  date_added: '2026-01-01T10:00:00Z',
  ...overrides,
});

describe('BookCard', () => {
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

  it('должен отрендерить название книги', () => {
    const { container } = render(
      <BookCard
        book={createBook()}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    const h3 = container.querySelector('h3');
    expect(h3?.textContent).toBe('The Great Gatsby');
  });

  it('должен отрендерить автора', () => {
    const { container } = render(
      <BookCard
        book={createBook()}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    const p = container.querySelector('.book-author');
    expect(p?.textContent).toBe('F. Scott Fitzgerald');
  });

  it('должен отрендерить формат файла', () => {
    const { container } = render(
      <BookCard
        book={createBook()}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    const p = container.querySelector('.book-format');
    expect(p?.textContent).toBe('epub');
  });

  it('должен отрендерить обложку с правильным src', () => {
    const { container } = render(
      <BookCard
        book={createBook()}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    const img = container.querySelector('img') as HTMLImageElement;
    expect(img.src).toContain('/api/v1/static/covers/cover-123.jpg');
  });

  // ===== Обработка кликов =====

  it('должен вызвать onRead при клике на кнопку "Читать"', () => {
    const { container } = render(
      <BookCard
        book={createBook()}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    const readButton = container.querySelector('.btn-read') as HTMLButtonElement;
    fireEvent.click(readButton);

    expect(onRead).toHaveBeenCalledWith('550e8400-e29b-41d4-a716-446655440000');
  });

  it('должен вызвать onRename при клике на кнопку переименования', () => {
    const { container } = render(
      <BookCard
        book={createBook()}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    const renameButton = container.querySelector('.btn-rename') as HTMLButtonElement;
    fireEvent.click(renameButton);

    expect(onRename).toHaveBeenCalledWith('550e8400-e29b-41d4-a716-446655440000');
  });

  it('должен вызвать onDelete при клике на кнопку удаления', () => {
    const { container } = render(
      <BookCard
        book={createBook()}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    const deleteButton = container.querySelector('.btn-delete') as HTMLButtonElement;
    fireEvent.click(deleteButton);

    expect(onDelete).toHaveBeenCalledWith('550e8400-e29b-41d4-a716-446655440000');
  });

  // ===== Автор null =====

  it('не должен отображать автора когда author = null', () => {
    const { container } = render(
      <BookCard
        book={createBook({ author: null })}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    const authorEl = container.querySelector('.book-author');
    expect(authorEl).not.toBeInTheDocument();
  });

  // ===== Обложка =====

  it('должен использовать default-cover.svg когда cover_thumbnail_path = null', () => {
    const { container } = render(
      <BookCard
        book={createBook({ cover_thumbnail_path: null })}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    const img = container.querySelector('img') as HTMLImageElement;
    expect(img.src).toContain('/default-cover.svg');
  });

  it('должен переключить на default-cover.svg при ошибке загрузки обложки', () => {
    const { container } = render(
      <BookCard
        book={createBook({ cover_thumbnail_path: 'broken-cover.jpg' })}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    const img = container.querySelector('img') as HTMLImageElement;
    expect(img.src).toContain('/api/v1/static/covers/broken-cover.jpg');

    // Симулируем ошибку загрузки изображения
    fireEvent.error(img);

    // После ошибки src должен измениться на default-cover
    expect(img.src).toContain('/default-cover.svg');
  });

  // ===== Пустое название (edge case) =====

  it('должен отрендерить книгу с пустым названием', () => {
    const { container } = render(
      <BookCard
        book={createBook({ title: '' })}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    const img = container.querySelector('img') as HTMLImageElement;
    expect(img).toBeInTheDocument();
  });

  // ===== Разные форматы =====

  it.each([
    ['txt', 'txt'],
    ['epub', 'epub'],
    ['fb2', 'fb2'],
  ])('должен отобразить формат %s', (format, expected) => {
    const { container, unmount } = render(
      <BookCard
        book={createBook({ file_format: format as BookDTO['file_format'] })}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    const p = container.querySelector('.book-format');
    expect(p?.textContent).toBe(expected);

    unmount();
  });

  // ===== ARIA labels =====

  it('должен содержать правильные aria-label у кнопок действий', () => {
    const { container } = render(
      <BookCard
        book={createBook()}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    const readBtn = container.querySelector('.btn-read') as HTMLButtonElement;
    const renameBtn = container.querySelector('.btn-rename') as HTMLButtonElement;
    const deleteBtn = container.querySelector('.btn-delete') as HTMLButtonElement;

    expect(readBtn?.ariaLabel).toBe('Читать The Great Gatsby');
    expect(renameBtn?.ariaLabel).toBe('Переименовать The Great Gatsby');
    expect(deleteBtn?.ariaLabel).toBe('Удалить The Great Gatsby');
  });

  // ===== CSS классы =====

  it('должен содержать базовые CSS классы карточки', () => {
    const { container } = render(
      <BookCard
        book={createBook()}
        onRead={onRead}
        onRename={onRename}
        onDelete={onDelete}
      />
    );

    const card = container.firstChild as HTMLElement;
    expect(card).toHaveClass('book-card');
    expect(card).toHaveClass('bg-white');
    expect(card).toHaveClass('rounded-lg');
    expect(card).toHaveClass('shadow-md');
  });
});
