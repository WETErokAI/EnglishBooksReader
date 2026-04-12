/**
 * API сервис для книг.
 *
 * React Query мутации и запросы:
 * - uploadBook: мутация загрузки файла
 * - uploadBookFromUrl: мутация загрузки по URL
 */

import { useMutation } from '@tanstack/react-query';
import apiClient from '../services/apiClient';
import type { BookDTO } from '../types/book';

// ===== Upload File Mutation =====

interface UploadFileResponse {
  data: BookDTO;
}

async function uploadBookFile(file: File): Promise<UploadFileResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<BookDTO>('/books/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return { data: response.data };
}

export function useUploadBook() {
  return useMutation({
    mutationFn: uploadBookFile,
  });
}

// ===== Upload from URL Mutation =====

interface UploadUrlParams {
  url: string;
}

async function uploadBookFromUrl(params: UploadUrlParams): Promise<UploadFileResponse> {
  const response = await apiClient.post<BookDTO>('/books/upload-from-url', null, {
    params: { url: params.url },
  });

  return { data: response.data };
}

export function useUploadBookFromUrl() {
  return useMutation({
    mutationFn: uploadBookFromUrl,
  });
}
