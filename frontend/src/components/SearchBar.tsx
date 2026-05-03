/**
 * Компонент SearchBar — поисковая строка с debounce 300ms.
 *
 * При вводе текста debounce предотвращает избыточные запросы к API.
 * Кнопка очистки (✕) появляется при наличии текста.
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

const DEBOUNCE_MS = 300;

export const SearchBar: React.FC<SearchBarProps> = ({
  value,
  onChange,
  placeholder = 'Поиск по названию или автору...',
}) => {
  const [inputValue, setInputValue] = useState(value);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Синхронизация с внешним value (например, при сбросе поиска)
  useEffect(() => {
    setInputValue(value);
  }, [value]);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = e.target.value;
      setInputValue(newValue);

      // Debounce: отправляем значение только через 300ms после последнего ввода
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
      debounceRef.current = setTimeout(() => {
        onChange(newValue);
      }, DEBOUNCE_MS);
    },
    [onChange],
  );

  const handleClear = useCallback(() => {
    setInputValue('');
    onChange('');
  }, [onChange]);

  return (
    <div className="relative flex-1 sm:flex-none">
      <div className="relative">
        {/* Иконка лупы */}
        <svg
          className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>

        <input
          type="text"
          placeholder={placeholder}
          value={inputValue}
          onChange={handleChange}
          className="w-full sm:w-64 lg:w-80 pl-10 pr-8 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm transition-shadow"
          aria-label="Поиск книг"
        />

        {/* Кнопка очистки */}
        {inputValue && (
          <button
            type="button"
            onClick={handleClear}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-0.5 text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="Очистить поиск"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
};
