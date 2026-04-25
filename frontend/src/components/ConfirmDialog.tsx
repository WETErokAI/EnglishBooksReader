import React from 'react';

interface ConfirmDialogProps {
  title: string;
  message: string;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'danger' | 'warning' | 'info';
}

/**
 * Модальное окно подтверждения действий.
 */
export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  title,
  message,
  isOpen,
  onClose,
  onConfirm,
  confirmLabel = 'Подтвердить',
  cancelLabel = 'Отмена',
  variant = 'info',
}) => {
  const [isConfirming, setIsConfirming] = React.useState(false);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape' && !isConfirming) onClose();
  };

  if (!isOpen) return null;

  const variantClasses = {
    danger: 'bg-red-500 hover:bg-red-600',
    warning: 'bg-yellow-500 hover:bg-yellow-600',
    info: 'bg-blue-500 hover:bg-blue-600',
  };

  const handleConfirm = async () => {
    setIsConfirming(true);
    try {
      await onConfirm();
    } finally {
      setIsConfirming(false);
      onClose();
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      onKeyDown={handleKeyDown}
      aria-modal="true"
      role="alertdialog"
    >
      <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md mx-4">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">{title}</h2>
        <p className="text-gray-600 mb-6">{message}</p>

        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            disabled={isConfirming}
            className="px-4 py-2 text-gray-700 bg-gray-200 hover:bg-gray-300 rounded-md transition-colors disabled:opacity-50"
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            disabled={isConfirming}
            className={`px-4 py-2 text-white rounded-md transition-colors disabled:opacity-50 ${variantClasses[variant]} ${isConfirming ? 'animate-pulse' : ''}`}
          >
            {isConfirming ? 'Выполняется...' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
};
