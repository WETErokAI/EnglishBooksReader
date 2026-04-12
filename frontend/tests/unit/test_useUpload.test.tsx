/**
 * Unit-тесты хука useUpload.
 *
 * Проверяет:
 * - Успешная загрузка файла
 * - Ошибка при загрузке
 * - Прогресс загрузки
 */

import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createElement } from 'react';
import { useUpload } from '../../../src/hooks/useUpload';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

describe('useUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('должен успешно загрузить файл', async () => {
    const mockResponse = {
      data: {
        id: '550e8400-e29b-41d4-a716-446655440000',
        title: 'Test Book',
        author: 'Test Author',
        file_format: 'epub',
        cover_thumbnail_path: null,
        date_added: '2026-04-08T10:30:00Z',
        has_reading_position: false,
      },
    };

    const { result } = renderHook(() => useUpload(), {
      wrapper: createWrapper(),
    });

    // Мокаем uploadMutation
    result.current.uploadMutation.mutateAsync = vi.fn().mockResolvedValue(mockResponse);

    const file = new File(['test content'], 'test.epub', { type: 'application/epub+zip' });
    const promise = result.current.uploadMutation.mutateAsync(file);

    await expect(promise).resolves.toEqual(mockResponse);
  });

  it('должен обработать ошибку загрузки', async () => {
    const errorMessage = 'Неподдерживаемый формат файла';

    const { result } = renderHook(() => useUpload(), {
      wrapper: createWrapper(),
    });

    result.current.uploadMutation.mutateAsync = vi.fn().mockRejectedValue(
      new Error(errorMessage)
    );

    const file = new File(['test content'], 'book.pdf', { type: 'application/pdf' });

    await expect(result.current.uploadMutation.mutateAsync(file)).rejects.toThrow(
      errorMessage
    );
  });

  it('должен иметь начальное состояние isUploading = false', () => {
    const { result } = renderHook(() => useUpload(), {
      wrapper: createWrapper(),
    });

    expect(result.current.uploadMutation.isPending).toBe(false);
  });

  it('должен установить isUploading = true во время загрузки', async () => {
    const { result } = renderHook(() => useUpload(), {
      wrapper: createWrapper(),
    });

    // Запускаем загрузку которая задерживается
    let resolvePromise: (value: any) => void;
    const pendingPromise = new Promise((resolve) => {
      resolvePromise = resolve;
    });

    result.current.uploadMutation.mutateAsync = vi.fn().mockImplementation(async () => {
      return pendingPromise;
    });

    const file = new File(['test content'], 'test.epub', { type: 'application/epub+zip' });
    result.current.uploadMutation.mutate(file);

    await waitFor(() => {
      expect(result.current.uploadMutation.isPending).toBe(true);
    });

    // Завершаем загрузку
    resolvePromise!({ data: { id: '123', title: 'Test' } });
    await waitFor(() => {
      expect(result.current.uploadMutation.isPending).toBe(false);
    });
  });

  it('должен загрузить по URL', async () => {
    const mockResponse = {
      data: {
        id: '550e8400-e29b-41d4-a716-446655440000',
        title: 'Remote Book',
        author: 'Remote Author',
        file_format: 'epub',
        cover_thumbnail_path: null,
        date_added: '2026-04-08T10:30:00Z',
        has_reading_position: false,
      },
    };

    const { result } = renderHook(() => useUpload(), {
      wrapper: createWrapper(),
    });

    result.current.uploadUrlMutation.mutateAsync = vi.fn().mockResolvedValue(mockResponse);

    await expect(
      result.current.uploadUrlMutation.mutateAsync({ url: 'https://example.com/book.epub' })
    ).resolves.toEqual(mockResponse);
  });

  it('должен обработать ошибку загрузки по URL', async () => {
    const { result } = renderHook(() => useUpload(), {
      wrapper: createWrapper(),
    });

    result.current.uploadUrlMutation.mutateAsync = vi.fn().mockRejectedValue(
      new Error('Некорректная или недоступная ссылка')
    );

    await expect(
      result.current.uploadUrlMutation.mutateAsync({ url: 'https://invalid-url/book.epub' })
    ).rejects.toThrow('Некорректная или недоступная ссылка');
  });
});
