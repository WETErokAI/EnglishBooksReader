/**
 * Хук для загрузки книг.
 *
 * Предоставляет:
 * - uploadMutation: мутация для загрузки файла
 * - uploadUrlMutation: мутация для загрузки по URL
 */

import { useUploadBook, useUploadBookFromUrl } from '../services/bookApi';

export function useUpload() {
  const uploadMutation = useUploadBook();
  const uploadUrlMutation = useUploadBookFromUrl();

  return {
    uploadMutation,
    uploadUrlMutation,
  };
}
