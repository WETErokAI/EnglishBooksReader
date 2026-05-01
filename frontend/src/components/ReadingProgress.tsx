import React from 'react';

interface ReadingProgressProps {
  currentChunk: number;
  totalChunks: number;
}

/**
 * Индикатор прогресса чтения.
 * Показывает полосу прогресса без элементов навигации.
 */
export const ReadingProgress: React.FC<ReadingProgressProps> = ({
  currentChunk,
  totalChunks,
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
    </div>
  );
};
