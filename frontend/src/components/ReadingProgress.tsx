import React from 'react';

interface ReadingProgressProps {
  currentChunk: number;
  totalChunks: number;
  onChunkChange?: (chunkIndex: number) => void;
}

/**
 * Индикатор прогресса чтения.
 * Показывает текущую позицию и позволяет перейти к другому чанку.
 */
export const ReadingProgress: React.FC<ReadingProgressProps> = ({
  currentChunk,
  totalChunks,
  onChunkChange,
}) => {
  if (totalChunks === 0) return null;

  const progress = ((currentChunk + 1) / totalChunks) * 100;

  return (
    <div className="reading-progress w-full" aria-label="Прогресс чтения">
      {/* Progress Bar */}
      <div className="relative w-full h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="absolute top-0 left-0 h-full bg-blue-500 transition-all duration-300"
          style={{ width: `${progress}%` }}
          role="progressbar"
          aria-valuenow={progress}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>

      {/* Info */}
      <div className="flex justify-between items-center mt-1 text-xs text-gray-500">
        <span>
          Глава {currentChunk + 1} из {totalChunks}
        </span>
        <span>{Math.round(progress)}%</span>
      </div>

      {/* Chunk Navigation (если больше 5 чанков) */}
      {totalChunks > 5 && onChunkChange && (
        <div className="flex gap-1 mt-2 overflow-x-auto pb-1">
          {Array.from({ length: totalChunks }, (_, i) => (
            <button
              key={i}
              onClick={() => onChunkChange(i)}
              className={`flex-shrink-0 w-8 h-6 text-xs rounded transition-colors ${
                i === currentChunk
                  ? 'bg-blue-500 text-white'
                  : i < currentChunk
                  ? 'bg-blue-200 text-blue-700 hover:bg-blue-300'
                  : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
              }`}
              aria-label={`Перейти к главе ${i + 1}`}
              aria-current={i === currentChunk ? 'true' : undefined}
            >
              {i + 1}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
