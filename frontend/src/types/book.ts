/**
 * TypeScript типы для книг.
 */

/** Формат файла книги */
export type FileFormat = 'txt' | 'epub' | 'fb2';

/** DTO для отображения книги */
export interface BookDTO {
  id: string; // UUID
  title: string;
  author: string | null;
  file_format: FileFormat;
  cover_thumbnail_path: string | null;
  date_added: string; // ISO datetime
  has_reading_position: boolean;
}

/** DTO для списка книг с пагинацией */
export interface BookListDTO {
  books: BookDTO[];
  total: number;
}

/** Позиция чтения */
export interface ReadingPosition {
  chunk_id: string;
  offset: number;
  timestamp: string; // ISO datetime
}

/** Ответ с ошибкой от API */
export interface ErrorResponse {
  detail: string;
}

/** Параметры для получения списка книг */
export interface GetBooksParams {
  skip?: number;
  limit?: number;
  search?: string;
}

/** Данные для обновления книги */
export interface BookUpdate {
  title?: string;
  author?: string;
}
