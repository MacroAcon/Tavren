import React from 'react';
import Button from './Button';

interface DialogProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  primaryAction?: {
    label: string;
    onClick: () => void;
    variant?: 'primary' | 'secondary' | 'danger' | 'success';
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

/**
 * A reusable dialog/modal component
 */
const Dialog: React.FC<DialogProps> = ({ 
  isOpen,
  onClose,
  title,
  children,
  primaryAction,
  secondaryAction,
  className = ''
}) => {
  if (!isOpen) return null;

  return (
    <div className="dialog-overlay">
      <div className={`dialog ${className}`}>
        <div className="dialog-header">
          <h2 className="dialog-title">{title}</h2>
          <button className="dialog-close" onClick={onClose}>×</button>
        </div>
        <div className="dialog-content">
          {children}
        </div>
        {(primaryAction || secondaryAction) && (
          <div className="dialog-actions">
            {secondaryAction && (
              <Button 
                variant="outline" 
                onClick={secondaryAction.onClick}
              >
                {secondaryAction.label}
              </Button>
            )}
            {primaryAction && (
              <Button 
                variant={primaryAction.variant || 'primary'} 
                onClick={primaryAction.onClick}
              >
                {primaryAction.label}
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dialog; 