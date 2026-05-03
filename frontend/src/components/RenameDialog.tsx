import React, { useState, useEffect } from 'react';

interface RenameDialogProps {
  bookTitle: string;
  bookAuthor: string | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (newTitle: string, newAuthor: string | null) => void;
}

/**
 * Модальное окно для переименования книги.
 */
export const RenameDialog: React.FC<RenameDialogProps> = ({
  bookTitle,
  bookAuthor,
  isOpen,
  onClose,
  onSave,
}) => {
  const [title, setTitle] = useState(bookTitle);
  const [author, setAuthor] = useState(bookAuthor || '');

  useEffect(() => {
    setTitle(bookTitle);
    setAuthor(bookAuthor || '');
  }, [bookTitle, bookAuthor]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    onSave(title.trim(), author.trim() || null);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') onClose();
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      onKeyDown={handleKeyDown}
      aria-modal="true"
      role="dialog"
    >
      <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md mx-4">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Переименовать книгу</h2>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label
              htmlFor="rename-title"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Название *
            </label>
            <input
              id="rename-title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
              autoFocus
            />
          </div>

          <div className="mb-6">
            <label
              htmlFor="rename-author"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Автор
            </label>
            <input
              id="rename-author"
              type="text"
              value={author}
              onChange={(e) => setAuthor(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Необязательно"
            />
          </div>

          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-200 hover:bg-gray-300 rounded-md transition-colors"
            >
              Отмена
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-white bg-blue-500 hover:bg-blue-600 rounded-md transition-colors"
              disabled={!title.trim()}
            >
              Сохранить
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
