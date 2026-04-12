import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import UploadPage from './pages/UploadPage';

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
            <Route path="/" element={<Navigate to="/upload" replace />} />
            <Route path="/upload" element={<UploadPage />} />
            {/* Маршруты для библиотеки и чтения будут добавлены в Phase 4 */}
            <Route path="/library" element={
              <div className="text-center py-16">
                <h2 className="text-2xl font-bold text-gray-900 mb-2">Библиотека</h2>
                <p className="text-gray-600">Будет реализована в Phase 4</p>
              </div>
            } />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
