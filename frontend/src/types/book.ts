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
  page?: number;
  page_size?: number;
}

/** Параметры для чанков книги */
export interface BookChunksResponse {
  book_id: string;
  chunks: BookChunkDTO[];
  total_chunks: number;
}

/** DTO для чанка книги */
export interface BookChunkDTO {
  chunk_index: number;
  content_html: string;
  word_count: number;
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
  page?: number;
  page_size?: number;
  search?: string;
}

/** Данные для обновления книги */
export interface BookUpdate {
  title?: string;
  author?: string | undefined;
}
