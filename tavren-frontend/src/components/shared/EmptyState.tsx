import React from 'react';
import './state-components.css';

interface EmptyStateProps {
  title: string;
  message: string;
  icon?: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

/**
 * A reusable empty state component for when no data is available
 */
const EmptyState: React.FC<EmptyStateProps> = ({ 
  title,
  message,
  icon = '📭',
  actionLabel = 'Refresh',
  onAction,
  className = ''
}) => {
  return (
    <div className={`empty-state ${className}`}>
      <div className="empty-state-icon">{icon}</div>
      <h3 className="empty-state-title">{title}</h3>
      <p className="empty-state-message">{message}</p>
      {onAction && (
        <button className="btn btn-primary" onClick={onAction}>
          {actionLabel}
        </button>
      )}
    </div>
  );
};

export default EmptyState; 