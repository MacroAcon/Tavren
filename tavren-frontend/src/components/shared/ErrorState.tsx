import React from 'react';

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
  className?: string;
}

/**
 * A reusable error state component
 */
const ErrorState: React.FC<ErrorStateProps> = ({ 
  message,
  onRetry,
  className = ''
}) => {
  return (
    <div className={`error-container ${className}`}>
      <div className="error-icon">⚠️</div>
      <p className="error-message">{message}</p>
      {onRetry && (
        <button className="retry-button" onClick={onRetry}>
          Try Again
        </button>
      )}
    </div>
  );
};

export default ErrorState; 