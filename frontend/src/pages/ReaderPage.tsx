import React, { useEffect, useRef, useCallback, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { List, useDynamicRowHeight } from 'react-window';
import { AutoSizer } from 'react-virtualized-auto-sizer';
import { useGetBook } from '../services/bookApi';
import { useChunkLoader } from '../hooks/useChunkLoader';
import { ReadingProgress } from '../components/ReadingProgress';
import { VirtualChunkRow } from '../components/VirtualChunkRow';

const ESTIMATED_CHUNK_HEIGHT = 600;

/**
 * Страница чтения книги с виртуализированным скроллом.
 *
 * Функциональность:
 * - Виртуализация чанков через react-window v2 List
 * - Переменные высоты чанков через useDynamicRowHeight
 * - В DOM только видимые чанки (+ небольшой буфер)
 * - Навигация между чанками (стрелки, скролл-бар)
 * - IntersectionObserver для определения активного чанка
 *
 * NOTE: Сохранение позиции чтения перенесено на будущую реализацию.
 */
export const ReaderPage: React.FC = () => {
  const { bookId } = useParams<{ bookId: string }>();
  const navigate = useNavigate();
  const listApiRef = useRef<{
    element: HTMLDivElement | null;
    scrollToRow: (config: { align?: 'auto' | 'center' | 'end' | 'start' | 'smart'; behavior?: 'auto' | 'smooth' | 'instant'; index: number }) => void;
  }>({ element: null, scrollToRow: () => {} });
  const chunkRefs = useRef<Map<number, HTMLDivElement>>(new Map());
  const [isKeyboardNavigation, setIsKeyboardNavigation] = useState(false);

  if (!bookId) {
    return (
      <div className="text-center py-16 text-red-600">
        Книга не найдена
      </div>
    );
  }

  const { data: book, isLoading: bookLoading } = useGetBook(bookId);

  const {
    chunks,
    totalChunks,
    isLoading,
    error,
    currentChunkIndex,
    goToChunk,
  } = useChunkLoader({ bookId });

  // Хук для переменных высот строк (react-window v2)
  const rowHeight = useDynamicRowHeight({ defaultRowHeight: ESTIMATED_CHUNK_HEIGHT });

  // Регистрация DOM-элемента чанка
  const registerChunkRef = useCallback((el: HTMLDivElement | null, index: number) => {
    if (el) {
      chunkRefs.current.set(index, el);
    } else {
      chunkRefs.current.delete(index);
    }
  }, []);

  // Intersection Observer для отслеживания видимого чанка
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            const chunkIndex = Number(entry.target.getAttribute('data-chunk-index'));
            if (!isNaN(chunkIndex) && chunkIndex !== currentChunkIndex && !isKeyboardNavigation) {
              goToChunk(chunkIndex);
            }
          }
        }
      },
      { root: null, threshold: 0.3 }
    );

    chunkRefs.current.forEach((el) => {
      if (el.parentNode) {
        observer.observe(el);
      }
    });

    return () => observer.disconnect();
  }, [chunks.length, currentChunkIndex, goToChunk, isKeyboardNavigation]);

  // Наблюдаем за DOM-элементами строк для измерения высоты (react-window v2)
  useEffect(() => {
    const elements = Array.from(chunkRefs.current.values());
    if (elements.length === 0) return;

    const cleanup = rowHeight.observeRowElements(elements);
    return cleanup;
  }, [chunks.length, rowHeight]);

  // Клавиатурная навигация
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        e.preventDefault();
        setIsKeyboardNavigation(true);
        if (currentChunkIndex < totalChunks - 1) {
          const nextIndex = currentChunkIndex + 1;
          goToChunk(nextIndex);
          listApiRef.current?.scrollToRow({ index: nextIndex, align: 'start', behavior: 'smooth' });
        }
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        e.preventDefault();
        setIsKeyboardNavigation(true);
        if (currentChunkIndex > 0) {
          const prevIndex = currentChunkIndex - 1;
          goToChunk(prevIndex);
          listApiRef.current?.scrollToRow({ index: prevIndex, align: 'start', behavior: 'smooth' });
        }
      } else if (e.key === 'Escape') {
        navigate('/library');
      }
    },
    [currentChunkIndex, totalChunks, goToChunk, navigate]
  );

  // Сброс флага клавиатурной навигации
  useEffect(() => {
    if (!isKeyboardNavigation) return;

    const resetId = setTimeout(() => {
      setIsKeyboardNavigation(false);
    }, 600);

    return () => clearTimeout(resetId);
  }, [currentChunkIndex, isKeyboardNavigation]);

  // Row renderer для List
  const renderRow = useCallback(({ index, style, ariaAttributes: _ariaAttributes }: {
    index: number;
    style: React.CSSProperties;
    ariaAttributes: { 'aria-posinset': number; 'aria-setsize': number; role: 'listitem' };
  }) => {
    const chunk = chunks[index];
    if (!chunk) return null;

    return (
      <VirtualChunkRow
        style={style}
        chunkIndex={chunk.chunk_index}
        contentHtml={chunk.content_html}
        isActive={chunk.chunk_index === currentChunkIndex}
        registerRef={registerChunkRef}
      />
    );
  }, [chunks, currentChunkIndex, registerChunkRef]);

  if (bookLoading || isLoading) {
    return (
      <div className="text-center py-16" onKeyDown={handleKeyDown} tabIndex={0}>
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <p className="text-gray-600 mt-2">Загрузка книги...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-16 text-red-600" onKeyDown={handleKeyDown} tabIndex={0}>
        <p className="text-lg">Ошибка загрузки книги</p>
        <button
          onClick={() => navigate('/library')}
          className="mt-4 bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded transition-colors"
        >
          Вернуться в библиотеку
        </button>
      </div>
    );
  }

  return (
    <div className="reader-page h-screen flex flex-col" onKeyDown={handleKeyDown} tabIndex={0}>
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/library')}
            className="text-gray-600 hover:text-gray-900 transition-colors"
            aria-label="Вернуться в библиотеку"
          >
            ← Назад
          </button>
          <div>
            <h1 className="text-lg font-semibold text-gray-900">{book?.title}</h1>
            {book?.author && (
              <p className="text-sm text-gray-500">{book.author}</p>
            )}
          </div>
        </div>
      </header>

      {/* Reading Progress Bar */}
      <div className="flex-shrink-0 bg-white border-b border-gray-200 px-4 py-2">
        <ReadingProgress
          currentChunk={currentChunkIndex}
          totalChunks={totalChunks}
        />
      </div>

      {/* Virtualized Content */}
      <div className="flex-1 overflow-hidden bg-gray-50">
        <AutoSizer
          renderProp={({ width, height }) => (
            <List
              style={{ width, height }}
              rowCount={totalChunks}
              rowHeight={rowHeight}
              listRef={listApiRef}
              rowComponent={renderRow}
              rowProps={{}}
            />
          )}
        />
      </div>
    </div>
  );
};
