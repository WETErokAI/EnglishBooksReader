/**
 * Хук для динамической подгрузки чанков книги.
 *
 * Подгружает видимые чанки ± 2 соседних,
 * выгружает невидимые для оптимизации памяти.
 */

import { useEffect, useState, useCallback } from 'react';
import { useGetBookChunks, useGetReadingPosition, useSaveReadingPosition } from '../services/bookApi';
import type { BookChunkDTO } from '../types/book';

interface UseChunkLoaderOptions {
  bookId: string;
  chunkSize?: number; // Размер "окна" видимых чанков (по умолчанию 5)
  neighborCount?: number; // Количество соседних чанков (по умолчанию 2)
}

interface UseChunkLoaderReturn {
  chunks: BookChunkDTO[]; // Загруженные чанки
  totalChunks: number; // Всего чанков в книге
  isLoading: boolean;
  error: Error | null;
  // Позиция чтения
  currentChunkIndex: number;
  // Навигация
  goToChunk: (index: number) => void;
  // Автосохранение позиции
  savePosition: (chunkIndex: number, offset: number) => void;
}

export function useChunkLoader({
  bookId,
  neighborCount = 2,
}: UseChunkLoaderOptions): UseChunkLoaderReturn {
  const [currentChunkIndex, setCurrentChunkIndex] = useState(0);
  const [savedChunks, setSavedChunks] = useState<Map<number, BookChunkDTO>>(new Map());

  // Получаем позицию чтения
  const { data: positionData } = useGetReadingPosition(bookId);

  // Устанавливаем начальную позицию из сохранённой
  useEffect(() => {
    if (positionData?.chunk_id) {
      // chunk_id — это UUID чанка, но у нас есть chunk_index
      // В реальном приложении нужно мапить UUID → chunk_index
      // Для простоты используем offset как chunk_index
      if (positionData.offset >= 0) {
        setCurrentChunkIndex(positionData.offset);
      }
    }
  }, [positionData]);

  // Вычисляем диапазон чанков для загрузки
  const fromChunk = Math.max(0, currentChunkIndex - neighborCount);
  const toChunk = currentChunkIndex + neighborCount;

  // Загружаем чанки
  const { data, isLoading, error } = useGetBookChunks(bookId, {
    from_chunk: fromChunk,
    to_chunk: toChunk,
  });

  // Сохраняем загруженные чанки
  useEffect(() => {
    if (data?.chunks) {
      setSavedChunks((prev) => {
        const next = new Map(prev);
        for (const chunk of data.chunks) {
          next.set(chunk.chunk_index, chunk);
        }
        return next;
      });
    }
  }, [data]);

  // Очищаем старые чанки (за пределами видимости)
  useEffect(() => {
    setSavedChunks((prev) => {
      const next = new Map(prev);
      const minIndex = Math.max(0, currentChunkIndex - neighborCount - 5);
      const maxIndex = currentChunkIndex + neighborCount + 5;

      for (const key of next.keys()) {
        if (key < minIndex || key > maxIndex) {
          next.delete(key);
        }
      }
      return next;
    });
  }, [currentChunkIndex, neighborCount]);

  // Переход к конкретному чанку
  const goToChunk = useCallback((index: number) => {
    setCurrentChunkIndex(index);
  }, []);

  // Сохранение позиции
  const savePositionMutation = useSaveReadingPosition();

  const savePosition = useCallback(
    (chunkIndex: number, offset: number) => {
      savePositionMutation.mutate({
        bookId,
        chunk_id: `chunk-${chunkIndex}`, // Временно используем chunk_index
        offset,
        timestamp: new Date().toISOString(),
      });
    },
    [bookId, savePositionMutation]
  );

  // Собираем чанки в порядке индексов
  const chunks = Array.from(savedChunks.values()).sort(
    (a, b) => a.chunk_index - b.chunk_index
  );

  return {
    chunks,
    totalChunks: data?.total_chunks || 0,
    isLoading,
    error: error instanceof Error ? error : null,
    currentChunkIndex,
    goToChunk,
    savePosition,
  };
}
