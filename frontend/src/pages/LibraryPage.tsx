import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGetBooks, useUpdateBook, useDeleteBook } from '../services/bookApi';
import { ViewToggle, ViewMode } from '../components/ViewToggle';
import { BookGridView } from '../components/BookGridView';
import { BookListView } from '../components/BookListView';
import { RenameDialog } from '../components/RenameDialog';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { SearchBar } from '../components/SearchBar';
import { NoResultsMessage } from '../components/NoResultsMessage';
import type { BookDTO } from '../types/book';

/**
 * Основная страница библиотеки.
 * Отображает список книг с возможностью переключения вида,
 * переименования и удаления.
 */
export const LibraryPage: React.FC = () => {
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [selectedBook, setSelectedBook] = useState<BookDTO | null>(null);

  // Dialog states
  const [isRenameOpen, setIsRenameOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);

  // React Query
  const { data, isLoading, error, refetch } = useGetBooks({
    page,
    page_size: 20,
    search: search || undefined,
  });
  const updateMutation = useUpdateBook();
  const deleteMutation = useDeleteBook();

  const books = data?.books || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / 20);

  // Handlers
  const handleRead = (bookId: string) => {
    navigate(`/books/${bookId}/read`);
  };

  const handleRename = (bookId: string) => {
    const book = books.find((b) => b.id === bookId);
    if (book) {
      setSelectedBook(book);
      setIsRenameOpen(true);
    }
  };

  const handleDelete = (bookId: string) => {
    const book = books.find((b) => b.id === bookId);
    if (book) {
      setSelectedBook(book);
      setIsDeleteOpen(true);
    }
  };

  const handleSaveRename = (newTitle: string, newAuthor: string | null) => {
    if (!selectedBook) return;
    updateMutation.mutate(
      {
        bookId: selectedBook.id,
        data: { title: newTitle, author: newAuthor || undefined },
      },
      {
        onSuccess: () => {
          setIsRenameOpen(false);
          setSelectedBook(null);
        },
      }
    );
  };

  const handleConfirmDelete = async () => {
    if (!selectedBook) return;
    // ConfirmDialog.handleConfirm вызывает onClose() после await
    return deleteMutation.mutateAsync(selectedBook.id, {
      onSuccess: () => {
        // Диалог закроется через ConfirmDialog.onClose()
        setSelectedBook(null);
      },
      onError: (error) => {
        console.error('Delete failed:', error);
        setSelectedBook(null);
      },
    });
  };

  const handleSearchChange = useCallback(
    (newSearch: string) => {
      setSearch(newSearch);
      setPage(1); // Reset to first page on new search
    },
    [],
  );

  const handleClearSearch = useCallback(() => {
    setSearch('');
    setPage(1);
  }, []);

  return (
    <div className="library-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Библиотека</h1>

        <div className="flex items-center gap-4 w-full sm:w-auto">
          {/* Search */}
          <SearchBar value={search} onChange={handleSearchChange} />

          {/* View Toggle */}
          <ViewToggle viewMode={viewMode} onViewModeChange={setViewMode} />
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="text-center py-16">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <p className="text-gray-600 mt-2">Загрузка книг...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
          <p className="text-red-800">Ошибка загрузки книг</p>
          <button
            onClick={() => refetch()}
            className="text-red-600 hover:text-red-800 text-sm mt-1 underline"
          >
            Попробовать снова
          </button>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && books.length === 0 && (
        search ? (
          <NoResultsMessage searchQuery={search} onClear={handleClearSearch} />
        ) : (
          <div className="text-center py-16">
            <p className="text-gray-500 text-lg mb-4">Библиотека пуста</p>
            <button
              onClick={() => navigate('/upload')}
              className="bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded-md transition-colors"
            >
              Загрузить книгу
            </button>
          </div>
        )
      )}

      {/* Books Grid/List */}
      {!isLoading && books.length > 0 && (
        <>
          {viewMode === 'grid' ? (
            <BookGridView
              books={books}
              onRead={handleRead}
              onRename={handleRename}
              onDelete={handleDelete}
            />
          ) : (
            <BookListView
              books={books}
              onRead={handleRead}
              onRename={handleRename}
              onDelete={handleDelete}
            />
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center items-center gap-2 mt-8">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 border rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors"
                aria-label="Previous page"
              >
                ←
              </button>
              <span className="text-sm text-gray-600">
                Страница {page} из {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-3 py-1 border rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors"
                aria-label="Next page"
              >
                →
              </button>
            </div>
          )}
        </>
      )}

      {/* Rename Dialog */}
      {selectedBook && (
        <RenameDialog
          bookTitle={selectedBook.title}
          bookAuthor={selectedBook.author}
          isOpen={isRenameOpen}
          onClose={() => {
            setIsRenameOpen(false);
            setSelectedBook(null);
          }}
          onSave={handleSaveRename}
        />
      )}

      {/* Delete Confirmation Dialog */}
      {selectedBook && (
        <ConfirmDialog
          title="Удалить книгу"
          message={`Вы уверены, что хотите удалить "${selectedBook.title}"?`}
          isOpen={isDeleteOpen}
          onClose={() => {
            setIsDeleteOpen(false);
            setSelectedBook(null);
          }}
          onConfirm={handleConfirmDelete}
          confirmLabel="Удалить"
          variant="danger"
        />
      )}
    </div>
  );
};
