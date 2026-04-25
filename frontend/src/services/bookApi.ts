/**
 * API сервис для книг.
 *
 * React Query мутации и запросы:
 * - uploadBook: мутация загрузки файла
 * - uploadBookFromUrl: мутация загрузки по URL
 * - getBooks: query для получения списка книг
 * - getBook: query для получения одной книги
 * - updateBook: мутация обновления книги
 * - deleteBook: мутация удаления книги
 * - getBookChunks: query для получения чанков
 * - saveReadingPosition: мутация сохранения позиции
 * - getReadingPosition: query для получения позиции
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import apiClient from '../services/apiClient';
import type {
  BookDTO,
  BookListDTO,
  BookUpdate,
  BookChunksResponse,
  ReadingPosition,
  GetBooksParams,
} from '../types/book';

// ===== Get Books Query =====

async function fetchBooks(params: GetBooksParams = {}): Promise<BookListDTO> {
  const { page = 1, page_size = 20, search } = params;
  const response = await apiClient.get<BookListDTO>('/books', {
    params: { page, page_size, search },
  });
  return response.data;
}

export function useGetBooks(params: GetBooksParams = {}) {
  return useQuery({
    queryKey: ['books', params],
    queryFn: () => fetchBooks(params),
  });
}

// ===== Get Book Query =====

async function fetchBook(bookId: string): Promise<BookDTO> {
  const response = await apiClient.get<BookDTO>(`/books/${bookId}`);
  return response.data;
}

export function useGetBook(bookId: string | null) {
  return useQuery({
    queryKey: ['book', bookId],
    queryFn: () => fetchBook(bookId!),
    enabled: !!bookId,
  });
}

// ===== Update Book Mutation =====

async function updateBookApi(params: { bookId: string; data: BookUpdate }): Promise<BookDTO> {
  const response = await apiClient.patch<BookDTO>(`/books/${params.bookId}`, params.data);
  return response.data;
}

export function useUpdateBook() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateBookApi,
    onSuccess: (_data, variables) => {
      // Инвалидируем списки и конкретную книгу
      queryClient.invalidateQueries({ queryKey: ['books'] });
      queryClient.invalidateQueries({ queryKey: ['book', variables.bookId] });
    },
  });
}

// ===== Delete Book Mutation =====

async function deleteBookApi(bookId: string): Promise<void> {
  console.log(`[deleteBookApi] Deleting book: ${bookId}`);
  const response = await apiClient.delete(`/books/${bookId}`);
  console.log(`[deleteBookApi] Delete response status: ${response.status}`);
}

export function useDeleteBook() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteBookApi,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['books'] });
    },
  });
}

// ===== Get Book Chunks Query =====

async function fetchBookChunks(
  bookId: string,
  range?: { from_chunk?: number; to_chunk?: number }
): Promise<BookChunksResponse> {
  const response = await apiClient.get<BookChunksResponse>(`/books/${bookId}/chunks`, {
    params: range,
  });
  return response.data;
}

export function useGetBookChunks(bookId: string, range?: { from_chunk?: number; to_chunk?: number }) {
  return useQuery({
    queryKey: ['book-chunks', bookId, range],
    queryFn: () => fetchBookChunks(bookId, range),
    enabled: !!bookId,
  });
}

// ===== Save Reading Position Mutation =====

interface SavePositionParams {
  bookId: string;
  chunk_id: string;
  offset: number;
  timestamp: string;
}

async function saveReadingPositionApi(params: SavePositionParams): Promise<void> {
  const { bookId, ...data } = params;
  await apiClient.post(`/books/${bookId}/reading-position`, data);
}

export function useSaveReadingPosition() {
  return useMutation({
    mutationFn: saveReadingPositionApi,
  });
}

// ===== Get Reading Position Query =====

async function fetchReadingPosition(bookId: string): Promise<ReadingPosition> {
  const response = await apiClient.get<ReadingPosition>(`/books/${bookId}/reading-position`);
  return response.data;
}

export function useGetReadingPosition(bookId: string | null) {
  return useQuery({
    queryKey: ['reading-position', bookId],
    queryFn: () => fetchReadingPosition(bookId!),
    enabled: !!bookId,
  });
}

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
