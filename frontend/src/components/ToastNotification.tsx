import React from 'react';

export type ToastVariant = 'success' | 'error' | 'warning' | 'info';

export interface ToastData {
  id: string;
  message: string;
  variant: ToastVariant;
  duration?: number;
}

interface ToastNotificationProps {
  toast: ToastData;
  onClose: (id: string) => void;
}

/**
 * ToastNotification — одно уведомление (тост).
 *
 * Отображается автоматически и закрывается по клику на крестик
 * или по истечении таймера.
 */
export const ToastNotification: React.FC<ToastNotificationProps> = ({
  toast,
  onClose,
}) => {
  React.useEffect(() => {
    const duration = toast.duration ?? 4000;
    const timer = setTimeout(() => onClose(toast.id), duration);
    return () => clearTimeout(timer);
  }, [toast.id, toast.duration, onClose]);

  const variantStyles: Record<ToastVariant, { bg: string; icon: string; text: string }> = {
    success: {
      bg: 'bg-green-50',
      icon: 'text-green-400',
      text: 'text-green-800',
    },
    error: {
      bg: 'bg-red-50',
      icon: 'text-red-400',
      text: 'text-red-800',
    },
    warning: {
      bg: 'bg-yellow-50',
      icon: 'text-yellow-400',
      text: 'text-yellow-800',
    },
    info: {
      bg: 'bg-blue-50',
      icon: 'text-blue-400',
      text: 'text-blue-800',
    },
  };

  const styles = variantStyles[toast.variant];

  const iconPaths: Record<ToastVariant, string> = {
    success: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
    error: 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z',
    warning: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z',
    info: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  };

  return (
    <div
      className={`${styles.bg} border-l-4 border-l-blue-500 rounded-md shadow-md p-4 flex items-start gap-3 animate-slide-in max-w-sm`}
      role="alert"
    >
      {/* Icon */}
      <svg
        className={`w-5 h-5 flex-shrink-0 mt-0.5 ${styles.icon}`}
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d={iconPaths[toast.variant]}
        />
      </svg>

      {/* Message */}
      <p className={`${styles.text} text-sm flex-1`}>{toast.message}</p>

      {/* Close button */}
      <button
        onClick={() => onClose(toast.id)}
        className={`flex-shrink-0 ${styles.text} hover:opacity-70 transition-opacity`}
        aria-label="Закрыть уведомление"
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
    </div>
  );
};

// ==================== ToastContainer ====================

interface ToastContainerProps {
  toasts: ToastData[];
  onClose: (id: string) => void;
}

/**
 * ToastContainer — контейнер для отображения списка уведомлений.
 *
 * Размещается в правом верхнем углу экрана.
 */
export const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, onClose }) => {
  if (toasts.length === 0) return null;

  return (
    <div
      className="fixed top-4 right-4 z-[100] flex flex-col gap-2"
      aria-live="polite"
      aria-atomic="true"
    >
      {toasts.map((toast) => (
        <ToastNotification key={toast.id} toast={toast} onClose={onClose} />
      ))}
    </div>
  );
};
