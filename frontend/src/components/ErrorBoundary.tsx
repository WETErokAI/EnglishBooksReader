import React from 'react';

interface ErrorBoundaryProps {
  fallback?: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/**
 * ErrorBoundary — перехватывает ошибки рендеринга дочерних компонентов.
 *
 * Позволяет показать пользовательский fallback вместо белого экрана
 * при ошибках в дочерних компонентах.
 */
export class ErrorBoundary extends React.Component<React.PropsWithChildren<ErrorBoundaryProps>, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    // Логируем ошибку для последующего анализа
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  handleReset = (): void => {
    this.setState({ hasError: false, error: null });
  };

  render(): React.ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
          <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center">
            {/* Иконка ошибки */}
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100 mb-4">
              <svg
                className="w-8 h-8 text-red-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
                />
              </svg>
            </div>

            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Что-то пошло не так
            </h2>
            <p className="text-gray-600 mb-6">
              Произошла ошибка при рендеринге приложения. Попробуйте обновить
              страницу.
            </p>

            {this.state.error && (
              <details className="mb-6 text-left">
                <summary className="text-sm text-gray-500 cursor-pointer hover:text-gray-700">
                  Подробности ошибки
                </summary>
                <pre className="mt-2 p-3 bg-gray-100 rounded text-xs text-red-600 overflow-auto max-h-40">
                  {this.state.error.message}
                </pre>
              </details>
            )}

            <div className="flex justify-center gap-3">
              <button
                onClick={() => window.location.reload()}
                className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-md transition-colors"
              >
                Обновить страницу
              </button>
              <button
                onClick={this.handleReset}
                className="bg-gray-200 hover:bg-gray-300 text-gray-700 px-6 py-2 rounded-md transition-colors"
              >
                Попробовать снова
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
