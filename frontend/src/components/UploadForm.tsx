/**
 * Компонент формы загрузки файла.
 *
 * Функциональность:
 * - Выбор файла через кнопку
 * - Drag-and-drop область
 * - Индикатор прогресса загрузки
 * - Валидация формата и размера
 */

import { useState, useCallback, useRef } from 'react';
import type { UseMutationResult } from '@tanstack/react-query';
import type { BookDTO } from '../types/book';

interface UploadFormProps {
  onUploadSuccess: (data: BookDTO) => void;
  uploadMutation: UseMutationResult<{ data: BookDTO }, Error, File, unknown>;
}

const SUPPORTED_FORMATS = ['.txt', '.epub', '.fb2'];
const MAX_SIZE_MB = 50;

export default function UploadForm({ onUploadSuccess, uploadMutation }: UploadFormProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = useCallback((file: File): string | null => {
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!SUPPORTED_FORMATS.includes(extension)) {
      return `Неподдерживаемый формат. Поддерживаются: ${SUPPORTED_FORMATS.join(', ')}`;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      return `Файл слишком большой. Максимум: ${MAX_SIZE_MB} МБ`;
    }
    return null;
  }, []);

  const handleFileSelect = useCallback((file: File) => {
    setError(null);
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      setSelectedFile(null);
      return;
    }
    setSelectedFile(file);
  }, [validateFile]);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  }, [handleFileSelect]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) {
      handleFileSelect(file);
    }
  }, [handleFileSelect]);

  const handleUpload = useCallback(() => {
    if (!selectedFile) return;
    uploadMutation.mutate(selectedFile, {
      onSuccess: (response) => {
        onUploadSuccess(response.data);
        setSelectedFile(null);
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      },
      onError: (err) => {
        setError(err.message || 'Ошибка при загрузке файла');
      },
    });
  }, [selectedFile, uploadMutation, onUploadSuccess]);

  const isUploading = uploadMutation.isPending;

  return (
    <div className="space-y-4">
      {/* Drag-and-drop область */}
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          isDragOver
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="space-y-2">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            stroke="currentColor"
            fill="none"
            viewBox="0 0 48 48"
            aria-hidden="true"
          >
            <path
              d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <div className="text-sm text-gray-600">
            <label
              htmlFor="file-upload"
              className="cursor-pointer text-blue-600 hover:text-blue-500"
            >
              <span>Выберите файл</span>
              <input
                ref={fileInputRef}
                id="file-upload"
                type="file"
                className="sr-only"
                accept=".txt,.epub,.fb2"
                onChange={handleInputChange}
                disabled={isUploading}
              />
            </label>
            <span> или перетащите сюда</span>
          </div>
          <p className="text-xs text-gray-500">
            Поддерживаемые форматы: {SUPPORTED_FORMATS.join(', ')} (макс. {MAX_SIZE_MB} МБ)
          </p>
        </div>
      </div>

      {/* Выбранный файл */}
      {selectedFile && (
        <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
          <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span className="text-sm text-gray-700 flex-1 truncate">{selectedFile.name}</span>
          <span className="text-xs text-gray-500">
            {(selectedFile.size / (1024 * 1024)).toFixed(2)} МБ
          </span>
        </div>
      )}

      {/* Индикатор прогресса */}
      {isUploading && (
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div
            className="bg-blue-600 h-2.5 rounded-full animate-pulse"
            style={{ width: '60%' }}
          />
          <p className="text-sm text-gray-600 mt-1">Загрузка...</p>
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
        type="button"
        onClick={handleUpload}
        disabled={!selectedFile || isUploading}
        className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
      >
        {isUploading ? 'Загрузка...' : 'Загрузить книгу'}
      </button>
    </div>
  );
}
