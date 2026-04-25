import React from 'react';
import { BookDTO } from '../types/book';

interface BookCardProps {
  book: BookDTO;
  onRead: (bookId: string) => void;
  onRename: (bookId: string) => void;
  onDelete: (bookId: string) => void;
}

/**
 * Компонент карточки книги.
 * Отображает обложку, название, автора и кнопки действий.
 */
export const BookCard: React.FC<BookCardProps> = ({
  book,
  onRead,
  onRename,
  onDelete,
}) => {
  const coverUrl = book.cover_thumbnail_path
    ? `/api/v1/static/covers/${book.cover_thumbnail_path}`
    : '/default-cover.svg';

  const handleRead = () => onRead(book.id);
  const handleRename = () => onRename(book.id);
  const handleDelete = () => onDelete(book.id);

  return (
    <div className="book-card bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
      {/* Обложка */}
      <div className="book-cover w-full h-48 bg-gray-200 flex items-center justify-center">
        <img
          src={coverUrl}
          alt={book.title}
          className="w-full h-full object-cover"
          onError={(e) => {
            (e.target as HTMLImageElement).src = '/default-cover.svg';
          }}
        />
      </div>

      {/* Информация о книге */}
      <div className="book-info p-4">
        <h3 className="book-title text-lg font-semibold text-gray-800 truncate" title={book.title}>
          {book.title}
        </h3>
        {book.author && (
          <p className="book-author text-sm text-gray-600 mt-1 truncate" title={book.author}>
            {book.author}
          </p>
        )}
        <p className="book-format text-xs text-gray-500 mt-2 uppercase">{book.file_format}</p>

        {/* Кнопки действий */}
        <div className="book-actions mt-3 flex gap-2">
          <button
            onClick={handleRead}
            className="btn-read flex-1 bg-blue-500 hover:bg-blue-600 text-white py-2 px-3 rounded text-sm transition-colors"
            aria-label={`Читать ${book.title}`}
          >
            Читать
          </button>
          <button
            onClick={handleRename}
            className="btn-rename bg-gray-200 hover:bg-gray-300 text-gray-700 py-2 px-3 rounded text-sm transition-colors"
            aria-label={`Переименовать ${book.title}`}
          >
            ✏️
          </button>
          <button
            onClick={handleDelete}
            className="btn-delete bg-red-500 hover:bg-red-600 text-white py-2 px-3 rounded text-sm transition-colors"
            aria-label={`Удалить ${book.title}`}
          >
            🗑️
          </button>
        </div>
      </div>
    </div>
  );
};
