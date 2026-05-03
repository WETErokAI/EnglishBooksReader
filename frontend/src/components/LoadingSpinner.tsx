import React from 'react';

interface LoadingSpinnerProps {
  /** Размер спиннера в пикселях (по умолчанию 24) */
  size?: number;
  /** Текст-подсказка под спиннером (опционально) */
  label?: string;
  /** Размер текста label */
  labelSize?: 'sm' | 'md' | 'lg';
  /** Показывать ли label */
  showLabel?: boolean;
}

/**
 * LoadingSpinner — универсальный индикатор загрузки.
 *
 * Используется для отображения состояния загрузки контента,
 * данных API, чанков книги и т.д.
 */
export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 24,
  label,
  labelSize = 'md',
  showLabel = true,
}) => {
  const labelClass = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  }[labelSize];

  return (
    <div
      className="flex flex-col items-center justify-center gap-2"
      role="status"
      aria-label={label || 'Загрузка'}
    >
      {/* SVG Spinner */}
      <svg
        className="animate-spin text-blue-500"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        style={{ width: size, height: size }}
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>

      {/* Label */}
      {showLabel && label && (
        <span className={`${labelClass} text-gray-500`}>{label}</span>
      )}

      {/* Default label */}
      {showLabel && !label && (
        <span className={`${labelClass} text-gray-500`}>Загрузка...</span>
      )}
    </div>
  );
};
