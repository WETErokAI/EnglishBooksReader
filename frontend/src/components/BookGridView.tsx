import React from 'react';
import { BookDTO } from '../types/book';
import { BookCard } from './BookCard';

interface BookGridViewProps {
  books: BookDTO[];
  onRead: (bookId: string) => void;
  onRename: (bookId: string) => void;
  onDelete: (bookId: string) => void;
}

/**
 * Компонент сетки карточек книг.
 */
export const BookGridView: React.FC<BookGridViewProps> = ({
  books,
  onRead,
  onRename,
  onDelete,
}) => {
  if (books.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        Нет книг для отображения
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
      {books.map((book) => (
        <BookCard
          key={book.id}
          book={book}
          onRead={onRead}
          onRename={onRename}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
};
