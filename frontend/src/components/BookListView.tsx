import React from 'react';
import { BookDTO } from '../types/book';

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
          {books.map((book) => {
            const coverUrl = book.cover_thumbnail_path
              ? `/api/v1/static/covers/${book.cover_thumbnail_path}`
              : '/default-cover.svg';

            return (
              <tr key={book.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap">
                  <img
                    src={coverUrl}
                    alt={book.title}
                    className="h-12 w-8 object-cover rounded"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = '/default-cover.svg';
                    }}
                  />
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900 truncate max-w-xs" title={book.title}>
                    {book.title}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-500 truncate max-w-xs" title={book.author || ''}>
                    {book.author || '—'}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-xs text-gray-500 uppercase">{book.file_format}</span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm text-gray-500">
                    {new Date(book.date_added).toLocaleDateString()}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right">
                  <div className="inline-flex gap-2">
                    <button
                      onClick={() => onRead(book.id)}
                      className="bg-blue-500 hover:bg-blue-600 text-white py-1 px-3 rounded text-sm transition-colors"
                      aria-label={`Читать ${book.title}`}
                    >
                      Читать
                    </button>
                    <button
                      onClick={() => onRename(book.id)}
                      className="bg-gray-200 hover:bg-gray-300 text-gray-700 py-1 px-2 rounded text-sm transition-colors"
                      aria-label={`Переименовать ${book.title}`}
                    >
                      ✏️
                    </button>
                    <button
                      onClick={() => onDelete(book.id)}
                      className="bg-red-500 hover:bg-red-600 text-white py-1 px-2 rounded text-sm transition-colors"
                      aria-label={`Удалить ${book.title}`}
                    >
                      🗑️
                    </button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
