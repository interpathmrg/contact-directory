import React from 'react';
import LoadingSpinner from './LoadingSpinner';

interface Props {
  isOpen: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  isLoading?: boolean;
  danger?: boolean;
}

export default function ConfirmDialog({
  isOpen, title, message, confirmLabel = 'Confirmar',
  onConfirm, onCancel, isLoading = false, danger = false,
}: Props) {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40" onClick={onCancel} />
      <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
        <p className="text-sm text-gray-600 mb-6">{message}</p>
        <div className="flex justify-end gap-3">
          <button onClick={onCancel} disabled={isLoading} className="btn-secondary">
            Cancelar
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className={danger ? 'btn-danger' : 'btn-primary'}
          >
            {isLoading ? <LoadingSpinner size="sm" /> : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
