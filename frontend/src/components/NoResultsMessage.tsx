/**
 * Компонент NoResultsMessage — сообщение "Ничего не найдено".
 *
 * Отображается когда поиск не дал результатов.
 * Содержит подсказку для пользователя.
 */

import React from 'react';

interface NoResultsMessageProps {
  searchQuery?: string;
  onClear?: () => void;
}

/**
 * Сообщение "Ничего не найдено" для пустых результатов поиска.
 *
 * @param searchQuery — текущий поисковый запрос (показывается в сообщении)
 * @param onClear — обработчик очистки поиска
 */
export const NoResultsMessage: React.FC<NoResultsMessageProps> = ({
  searchQuery,
  onClear,
}) => {
  return (
    <div className="text-center py-16">
      {/* Иконка лупы с крестиком */}
      <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 mb-4">
        <svg
          className="w-8 h-8 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M10 7l4 4m0-4l-4 4"
          />
        </svg>
      </div>

      <p className="text-gray-600 text-lg font-medium mb-1">Ничего не найдено</p>
      {searchQuery && (
        <p className="text-gray-400 text-sm mb-4">
          Не найдено результатов для &laquo;{searchQuery}&raquo;
        </p>
      )}
      <p className="text-gray-400 text-sm mb-4">
        Попробуйте изменить запрос или загрузите новую книгу
      </p>

      {onClear && (
        <button
          onClick={onClear}
          className="bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded-md transition-colors text-sm"
        >
          Очистить поиск
        </button>
      )}
    </div>
  );
};
