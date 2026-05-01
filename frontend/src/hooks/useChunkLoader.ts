/**
 * Хук для загрузки чанков книги.
 *
 * Функциональность:
 * - Загружает ВСЕ чанки сразу
 * - Показывает все чанки в DOM (скролл-бар рассчитывается по всей книге)
 * - IntersectionObserver отслеживает текущий чанк для прогресса
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { useGetBookChunks } from '../services/bookApi';
import type { BookChunkDTO } from '../types/book';

interface UseChunkLoaderOptions {
  bookId: string;
}

interface UseChunkLoaderReturn {
  chunks: BookChunkDTO[]; // Загруженные чанки
  totalChunks: number; // Всего чанков в книге
  isLoading: boolean;
  error: Error | null;
  // Позиция чтения
  currentChunkIndex: number;
  scrollOffset: number; // Скролл внутри текущего чанка
  // Навигация
  goToChunk: (index: number) => void;
  getChunkIdByIndex: (index: number) => string | null;
}

export function useChunkLoader({
  bookId,
}: UseChunkLoaderOptions): UseChunkLoaderReturn {
  const [currentChunkIndex, setCurrentChunkIndex] = useState(0);
  const [scrollOffset, setScrollOffset] = useState(0);
  const [savedChunks, setSavedChunks] = useState<Map<number, BookChunkDTO>>(new Map());

  // Mapping chunk_index → chunk_id (UUID чанка)
  const chunkIdMappingRef = useRef<Map<number, string>>(new Map());

  // Сброс маппинга чанков и состояния при смене bookId
  useEffect(() => {
    console.log('[ChunkLoader] 🔄 Сброс chunkIdMappingRef при смене bookId:', bookId);
    chunkIdMappingRef.current = new Map();
    setSavedChunks(new Map());
    setCurrentChunkIndex(0);
    setScrollOffset(0);
  }, [bookId]);

  // Загружаем ВСЕ чанки сразу
  const { data, isLoading, error } = useGetBookChunks(bookId, {
    from_chunk: 0,
    to_chunk: 999999, // Загружаем все чанки
  });

  // Сохраняем загруженные чанки и строим chunk_id маппинг
  useEffect(() => {
    if (!data?.chunks) return;

    setSavedChunks((prev) => {
      const next = new Map(prev);

      // Слияние новых чанков и построение маппинга
      for (const chunk of data.chunks) {
        next.set(chunk.chunk_index, chunk);
        chunkIdMappingRef.current.set(chunk.chunk_index, chunk.id);
      }

      return next;
    });
  }, [data]);

  // Переход к конкретному чанку
  const goToChunk = useCallback((index: number) => {
    setCurrentChunkIndex(index);
    setScrollOffset(0); // Сбрасываем скролл при переходе к новому чанку
  }, []);

  // Получение chunk_id по chunk_index
  const getChunkIdByIndex = useCallback((index: number): string | null => {
    return chunkIdMappingRef.current.get(index) || null;
  }, []);

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
    scrollOffset,
    goToChunk,
    getChunkIdByIndex,
  };
}
