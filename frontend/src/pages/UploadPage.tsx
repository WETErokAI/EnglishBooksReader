/**
 * Страница загрузки книг.
 *
 * Объединяет:
 * - UploadForm (загрузка файла)
 * - UrlUploadForm (загрузка по ссылке)
 * - Уведомления об успехе/ошибке
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUpload } from '../hooks/useUpload';
import UploadForm from '../components/UploadForm';
import UrlUploadForm from '../components/UrlUploadForm';
import type { BookDTO } from '../types/book';

export default function UploadPage() {
  const navigate = useNavigate();
  const { uploadMutation, uploadUrlMutation } = useUpload();
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleUploadSuccess = (book: BookDTO) => {
    setSuccessMessage(`Книга "${book.title}" успешно загружена!`);
    // Автоматический переход в библиотеку через 2 секунды
    setTimeout(() => {
      navigate('/library');
    }, 2000);
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6 py-8">
      <h1 className="text-2xl font-bold text-gray-900">Загрузить книгу</h1>

      {/* Уведомление об успехе */}
      {successMessage && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-sm text-green-700">{successMessage}</p>
          <p className="text-xs text-green-600 mt-1">Переход в библиотеку...</p>
        </div>
      )}

      {/* Вкладки: Файл / Ссылка */}
      <div className="space-y-6">
        {/* Загрузка файла */}
        <section>
          <h2 className="text-lg font-semibold text-gray-800 mb-3">
            Загрузка из файла
          </h2>
          <UploadForm
            uploadMutation={uploadMutation}
            onUploadSuccess={handleUploadSuccess}
          />
        </section>

        <div className="border-t border-gray-200" />

        {/* Загрузка по ссылке */}
        <section>
          <h2 className="text-lg font-semibold text-gray-800 mb-3">
            Загрузка по ссылке
          </h2>
          <UrlUploadForm
            uploadUrlMutation={uploadUrlMutation}
            onUploadSuccess={handleUploadSuccess}
          />
        </section>
      </div>
    </div>
  );
}
