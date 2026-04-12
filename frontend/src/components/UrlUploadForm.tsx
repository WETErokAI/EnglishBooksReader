/**
 * Компонент формы загрузки книги по ссылке.
 *
 * Функциональность:
 * - Поле ввода URL
 * - Валидация URL
 * - Индикатор загрузки
 * - Обработка ошибок
 */

import { useState, useCallback } from 'react';
import type { UseMutationResult } from '@tanstack/react-query';
import type { BookDTO } from '../types/book';

interface UrlUploadFormProps {
  onUploadSuccess: (data: BookDTO) => void;
  uploadUrlMutation: UseMutationResult<{ data: BookDTO }, Error, { url: string }, unknown>;
}

export default function UrlUploadForm({ onUploadSuccess, uploadUrlMutation }: UrlUploadFormProps) {
  const [url, setUrl] = useState('');
  const [error, setError] = useState<string | null>(null);

  const validateUrl = useCallback((value: string): string | null => {
    if (!value.trim()) {
      return 'Введите ссылку';
    }
    try {
      new URL(value);
    } catch {
      return 'Некорректный URL';
    }
    return null;
  }, []);

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const validationError = validateUrl(url);
    if (validationError) {
      setError(validationError);
      return;
    }

    uploadUrlMutation.mutate(
      { url: url.trim() },
      {
        onSuccess: (response) => {
          onUploadSuccess(response.data);
          setUrl('');
        },
        onError: (err) => {
          setError(err.message || 'Ошибка при загрузке по ссылке');
        },
      }
    );
  }, [url, validateUrl, uploadUrlMutation, onUploadSuccess]);

  const isLoading = uploadUrlMutation.isPending;

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="url-input" className="block text-sm font-medium text-gray-700 mb-1">
          Ссылка на книгу
        </label>
        <input
          id="url-input"
          type="url"
          value={url}
          onChange={(e) => {
            setUrl(e.target.value);
            setError(null);
          }}
          placeholder="https://example.com/books/my-book.epub"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
          disabled={isLoading}
        />
        <p className="mt-1 text-xs text-gray-500">
          Введите прямую ссылку на файл (.epub, .fb2, .txt)
        </p>
      </div>

      {/* Индикатор загрузки */}
      {isLoading && (
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div
            className="bg-blue-600 h-2.5 rounded-full animate-pulse"
            style={{ width: '60%' }}
          />
          <p className="text-sm text-gray-600 mt-1">Скачивание...</p>
        </div>
      )}

      {/* Сообщение об ошибке */}
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Кнопка загрузки */}
      <button
        type="submit"
        disabled={!url.trim() || isLoading}
        className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
      >
        {isLoading ? 'Загрузка...' : 'Загрузить по ссылке'}
      </button>
    </form>
  );
}
