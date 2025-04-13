import React from 'react';
import './state-components.css';

interface LoadingStateProps {
  message?: string;
  className?: string;
}

/**
 * A reusable loading state component
 */
const LoadingState: React.FC<LoadingStateProps> = ({ 
  message = 'Loading...',
  className = ''
}) => {
  return (
    <div className={`loading-container ${className}`}>
      <div className="loading-spinner"></div>
      <p className="loading-message">{message}</p>
    </div>
  );
};

export default LoadingState; 