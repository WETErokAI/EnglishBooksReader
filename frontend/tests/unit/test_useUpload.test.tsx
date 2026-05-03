/**
 * Unit-тесты хука useUpload.
 *
 * Проверяет:
 * - Успешная загрузка файла
 * - Ошибка при загрузке
 * - Прогресс загрузки (isPending)
 * - Загрузка по URL
 * - Ошибка загрузки по URL
 */

import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createElement } from 'react';
import { useUpload } from '../../src/hooks/useUpload';

// ===== Mocks =====

const mockUseUploadBook = vi.fn();
const mockUseUploadBookFromUrl = vi.fn();

vi.mock('../../src/services/bookApi', () => ({
  useUploadBook: (...args: any[]) => mockUseUploadBook(...args),
  useUploadBookFromUrl: (...args: any[]) => mockUseUploadBookFromUrl(...args),
}));

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

// Фабрика мутаций с динамическим isPending
function createMutationFactory() {
  let state = {
    isPending: false,
    data: null,
    error: null,
  };

  const mutate = vi.fn((data: any) => {
    state.isPending = true;
    // async simulation
    Promise.resolve(state.data)
      .then(() => {
        state.isPending = false;
      })
      .catch(() => {
        state.isPending = false;
      });
  });

  const mutateAsync = vi.fn(async (data: any) => {
    if (state.error) throw state.error;
    return state.data;
  });

  return {
    getState: () => state,
    mutate,
    mutateAsync,
    getSnapshot: () => ({
      mutate,
      mutateAsync,
      get isPending() {
        return state.isPending;
      },
      get isSuccess() {
        return !state.isPending && state.data !== null;
      },
      get isError() {
        return state.error !== null;
      },
      get data() {
        return state.data;
      },
      get error() {
        return state.error;
      },
    }),
    setState: (partial: Partial<typeof state>) => {
      Object.assign(state, partial);
    },
  };
}

const uploadBookFactory = createMutationFactory();
const uploadUrlFactory = createMutationFactory();

const defaultUploadData = {
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

const defaultUploadUrlData = {
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

describe('useUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    uploadBookFactory.setState({ isPending: false, data: defaultUploadData, error: null });
    uploadUrlFactory.setState({ isPending: false, data: defaultUploadUrlData, error: null });
    mockUseUploadBook.mockImplementation(() => uploadBookFactory.getSnapshot());
    mockUseUploadBookFromUrl.mockImplementation(() => uploadUrlFactory.getSnapshot());
  });

  it('должен успешно загрузить файл', async () => {
    const { result } = renderHook(() => useUpload(), {
      wrapper: createWrapper(),
    });

    const file = new File(['test content'], 'test.epub', { type: 'application/epub+zip' });
    const promise = result.current.uploadMutation.mutateAsync(file);

    await expect(promise).resolves.toEqual(defaultUploadData);
  });

  it('должен обработать ошибку загрузки', async () => {
    const errorMessage = 'Неподдерживаемый формат файла';

    uploadBookFactory.setState({
      isPending: false,
      data: null,
      error: new Error(errorMessage),
    });

    const { result } = renderHook(() => useUpload(), {
      wrapper: createWrapper(),
    });

    const file = new File(['test content'], 'book.pdf', { type: 'application/pdf' });

    await expect(result.current.uploadMutation.mutateAsync(file)).rejects.toThrow(errorMessage);
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

    const file = new File(['test content'], 'test.epub', { type: 'application/epub+zip' });
    act(() => {
      result.current.uploadMutation.mutate(file);
    });

    await waitFor(() => {
      expect(result.current.uploadMutation.isPending).toBe(true);
    });

    await waitFor(() => {
      expect(result.current.uploadMutation.isPending).toBe(false);
    });
  });

  it('должен загрузить по URL', async () => {
    const { result } = renderHook(() => useUpload(), {
      wrapper: createWrapper(),
    });

    await expect(
      result.current.uploadUrlMutation.mutateAsync({ url: 'https://example.com/book.epub' })
    ).resolves.toEqual(defaultUploadUrlData);
  });

  it('должен обработать ошибку загрузки по URL', async () => {
    uploadUrlFactory.setState({
      isPending: false,
      data: null,
      error: new Error('Некорректная или недоступная ссылка'),
    });

    const { result } = renderHook(() => useUpload(), {
      wrapper: createWrapper(),
    });

    await expect(
      result.current.uploadUrlMutation.mutateAsync({ url: 'https://invalid-url/book.epub' })
    ).rejects.toThrow('Некорректная или недоступная ссылка');
  });
});
