import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import UploadPage from './pages/UploadPage';
import { LibraryPage } from './pages/LibraryPage';
import { ReaderPage } from './pages/ReaderPage';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow">
          <nav className="max-w-7xl mx-auto px-4 py-4 flex items-center gap-6">
            <a href="/" className="text-xl font-bold text-gray-900 hover:text-blue-600 transition">
              English Books Reader
            </a>
            <div className="flex gap-4">
              <a
                href="/upload"
                className="text-sm text-gray-600 hover:text-blue-600 transition"
              >
                Загрузить книгу
              </a>
              <a
                href="/library"
                className="text-sm text-gray-600 hover:text-blue-600 transition"
              >
                Библиотека
              </a>
            </div>
          </nav>
        </header>

        {/* Main content */}
        <main className="max-w-7xl mx-auto px-4 py-6">
          <Routes>
            <Route path="/" element={<Navigate to="/library" replace />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/library" element={<LibraryPage />} />
            <Route path="/books/:bookId/read" element={<ReaderPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
