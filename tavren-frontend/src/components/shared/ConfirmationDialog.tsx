import React, { useEffect, useRef } from 'react';
import './shared-components.css';

export interface ConfirmationDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  onConfirm: () => void;
  onCancel: () => void;
  variant?: 'danger' | 'warning' | 'info' | 'success';
}

const ConfirmationDialog: React.FC<ConfirmationDialogProps> = ({
  isOpen,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  onConfirm,
  onCancel,
  variant = 'danger',
}) => {
  const dialogRef = useRef<HTMLDivElement>(null);

  // Handle clicking outside the dialog
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dialogRef.current && !dialogRef.current.contains(event.target as Node)) {
        onCancel();
      }
    };

    // Handle escape key press
    const handleEscKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onCancel();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleEscKey);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscKey);
    };
  }, [isOpen, onCancel]);

  // Handle focus trap
  useEffect(() => {
    if (isOpen && dialogRef.current) {
      const focusableElements = dialogRef.current.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      
      const firstElement = focusableElements[0] as HTMLElement;
      const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;
      
      const handleTabKey = (e: KeyboardEvent) => {
        if (e.key === 'Tab') {
          if (e.shiftKey && document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
          } else if (!e.shiftKey && document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
          }
        }
      };
      
      firstElement?.focus();
      document.addEventListener('keydown', handleTabKey);
      
      return () => {
        document.removeEventListener('keydown', handleTabKey);
      };
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="confirmation-dialog-overlay">
      <div 
        ref={dialogRef}
        className={`confirmation-dialog ${variant}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby="dialog-title"
      >
        <div className="confirmation-dialog-header">
          <h2 id="dialog-title" className="confirmation-dialog-title">{title}</h2>
          <button 
            className="confirmation-dialog-close" 
            onClick={onCancel}
            aria-label="Close"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="confirmation-dialog-content">
          <p>{message}</p>
        </div>
        <div className="confirmation-dialog-actions">
          <button 
            className="confirmation-dialog-cancel-btn" 
            onClick={onCancel}
          >
            {cancelText}
          </button>
          <button 
            className={`confirmation-dialog-confirm-btn ${variant}`} 
            onClick={onConfirm}
            autoFocus
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

// Custom hook for managing confirmation dialogs
export const useConfirmationDialog = () => {
  const [dialogState, setDialogState] = React.useState<{
    isOpen: boolean;
    title: string;
    message: string;
    confirmText?: string;
    cancelText?: string;
    onConfirm: () => void;
    variant?: 'danger' | 'warning' | 'info' | 'success';
  }>({
    isOpen: false,
    title: '',
    message: '',
    onConfirm: () => {},
  });

  const openConfirmDialog = ({
    title,
    message,
    confirmText,
    cancelText,
    onConfirm,
    variant = 'danger',
  }: {
    title: string;
    message: string;
    confirmText?: string;
    cancelText?: string;
    onConfirm: () => void;
    variant?: 'danger' | 'warning' | 'info' | 'success';
  }) => {
    setDialogState({
      isOpen: true,
      title,
      message,
      confirmText,
      cancelText,
      onConfirm,
      variant,
    });
  };

  const closeConfirmDialog = () => {
    setDialogState((prevState) => ({
      ...prevState,
      isOpen: false,
    }));
  };

  // Render prop to use in components
  const ConfirmationDialogComponent = () => (
    <ConfirmationDialog
      isOpen={dialogState.isOpen}
      title={dialogState.title}
      message={dialogState.message}
      confirmText={dialogState.confirmText}
      cancelText={dialogState.cancelText}
      onConfirm={() => {
        dialogState.onConfirm();
        closeConfirmDialog();
      }}
      onCancel={closeConfirmDialog}
      variant={dialogState.variant}
    />
  );

  return {
    openConfirmDialog,
    closeConfirmDialog,
    ConfirmationDialog: ConfirmationDialogComponent,
  };
};

export default ConfirmationDialog; 