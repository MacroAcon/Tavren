import React from 'react';
import { calculateTimeRemaining, calculateExpiryPercentage } from '../../utils/formatters';

interface ExpiryProgressProps {
  grantedAt: string;
  expiresAt: string;
  className?: string;
  showLabel?: boolean;
}

/**
 * A reusable component for displaying consent expiration progress
 */
const ExpiryProgress: React.FC<ExpiryProgressProps> = ({ 
  grantedAt,
  expiresAt,
  className = '',
  showLabel = true
}) => {
  return (
    <div className={`expiry-container ${className}`}>
      {showLabel && <span className="expiry-label">Expires:</span>}
      <span className="expiry-value">{calculateTimeRemaining(expiresAt)}</span>
      <div className="expiry-progress">
        <div 
          className="expiry-bar" 
          style={{ 
            width: `${calculateExpiryPercentage(grantedAt, expiresAt)}%` 
          }}
        ></div>
      </div>
    </div>
  );
};

export default ExpiryProgress; 