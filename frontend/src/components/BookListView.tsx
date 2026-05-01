import React from 'react';
import { BookDTO } from '../types/book';
import { BookListRow } from './BookListRow';

interface BookListViewProps {
  books: BookDTO[];
  onRead: (bookId: string) => void;
  onRename: (bookId: string) => void;
  onDelete: (bookId: string) => void;
}

/**
 * Компонент списка книг в виде таблицы.
 */
export const BookListView: React.FC<BookListViewProps> = ({
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
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th
              scope="col"
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
            >
              Обложка
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
            >
              Название
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
            >
              Автор
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
            >
              Формат
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
            >
              Дата добавления
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"
            >
              Действия
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {books.map((book) => (
            <BookListRow
              key={book.id}
              book={book}
              onRead={onRead}
              onRename={onRename}
              onDelete={onDelete}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
};
