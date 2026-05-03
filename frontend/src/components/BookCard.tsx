import React, { useState } from 'react';
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
  const [coverLoaded, setCoverLoaded] = useState(false);
  const [coverError, setCoverError] = useState(false);

  const coverUrl = book.cover_thumbnail_path
    ? `/api/v1/static/covers/${book.cover_thumbnail_path}`
    : '/default-cover.svg';

  const handleRead = () => onRead(book.id);
  const handleRename = () => onRename(book.id);
  const handleDelete = () => onDelete(book.id);

  const handleImageLoad = () => {
    setCoverLoaded(true);
  };

  const handleImageError = () => {
    setCoverError(true);
    setCoverLoaded(true);
  };

  return (
    <div className="book-card bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
      {/* Обложка */}
      <div className="book-cover w-full aspect-[3/4] bg-gray-200 flex items-center justify-center overflow-hidden">
        {!coverLoaded && (
          <div className="absolute inset-0 bg-gray-200 animate-pulse flex items-center justify-center">
            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
        )}
        <img
          src={coverError ? '/default-cover.svg' : coverUrl}
          alt={book.title}
          className={`w-full h-full object-cover transition-opacity duration-300 ${coverLoaded ? 'opacity-100' : 'opacity-0'}`}
          loading="lazy"
          onLoad={handleImageLoad}
          onError={handleImageError}
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
