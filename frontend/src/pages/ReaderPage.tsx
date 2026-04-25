import React, { useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useGetBook } from '../services/bookApi';
import { useChunkLoader } from '../hooks/useChunkLoader';
import { ReadingProgress } from '../components/ReadingProgress';

/**
 * Страница чтения книги.
 * Загружает чанки динамически, позволяет читать с вертикальной прокруткой
 * и сохраняет позицию чтения.
 */
export const ReaderPage: React.FC = () => {
  const { bookId } = useParams<{ bookId: string }>();
  const navigate = useNavigate();
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const chunkRefs = useRef<Map<number, HTMLDivElement>>(new Map());

  if (!bookId) {
    return (
      <div className="text-center py-16 text-red-600">
        Книга не найдена
      </div>
    );
  }

  // Загружаем информацию о книге
  const { data: book, isLoading: bookLoading } = useGetBook(bookId);

  // Загружаем чанки
  const {
    chunks,
    totalChunks,
    isLoading,
    error,
    currentChunkIndex,
    goToChunk,
    savePosition,
  } = useChunkLoader({ bookId });

  // Автосохранение позиции при изменении чанка
  useEffect(() => {
    if (totalChunks > 0) {
      savePosition(currentChunkIndex, 0);
    }
  }, [currentChunkIndex, totalChunks, savePosition]);

  // Обработка видимости чанков через Intersection Observer
  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) return;

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            const chunkIndex = Number(entry.target.getAttribute('data-chunk-index'));
            if (!isNaN(chunkIndex) && chunkIndex !== currentChunkIndex) {
              goToChunk(chunkIndex);
            }
          }
        }
      },
      { root: container, threshold: 0.5 }
    );

    // Наблюдаем за всеми чанками
    chunkRefs.current.forEach((el) => {
      if (el.parentNode) {
        observer.observe(el);
      }
    });

    return () => observer.disconnect();
  }, [chunks, currentChunkIndex, goToChunk]);

  // Обработка клавиш навигации
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        e.preventDefault();
        if (currentChunkIndex < totalChunks - 1) {
          goToChunk(currentChunkIndex + 1);
        }
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        e.preventDefault();
        if (currentChunkIndex > 0) {
          goToChunk(currentChunkIndex - 1);
        }
      } else if (e.key === 'Escape') {
        navigate('/library');
      }
    },
    [currentChunkIndex, totalChunks, goToChunk, navigate]
  );

  // Прокрутка к текущему чанку
  useEffect(() => {
    const chunkEl = chunkRefs.current.get(currentChunkIndex);
    if (chunkEl && scrollContainerRef.current) {
      chunkEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [currentChunkIndex]);

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

        {/* Progress indicator */}
        <div className="text-sm text-gray-500">
          Глава {currentChunkIndex + 1} / {totalChunks}
        </div>
      </header>

      {/* Reading Progress Bar */}
      <div className="flex-shrink-0 bg-white border-b border-gray-200 px-4 py-2">
        <ReadingProgress
          currentChunk={currentChunkIndex}
          totalChunks={totalChunks}
          onChunkChange={goToChunk}
        />
      </div>

      {/* Content */}
      <div
        ref={scrollContainerRef}
        className="flex-1 overflow-y-auto bg-gray-50 px-4 py-6"
      >
        <div className="max-w-3xl mx-auto space-y-6">
          {chunks.map((chunk) => (
            <div
              key={chunk.chunk_index}
              ref={(el) => {
                if (el) {
                  chunkRefs.current.set(chunk.chunk_index, el);
                }
              }}
              data-chunk-index={chunk.chunk_index}
              className="bg-white rounded-lg shadow-sm p-8 prose prose-lg max-w-none"
              dangerouslySetInnerHTML={{ __html: chunk.content_html }}
            />
          ))}

          {/* Loading indicator для подгрузки */}
          {isLoading && (
            <div className="text-center py-4">
              <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
