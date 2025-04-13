import React from 'react';
import { getAnonymizationClass } from '../../utils/styleHelpers';

interface AnonymizationIndicatorProps {
  level: string;
  showLabel?: boolean;
  className?: string;
}

/**
 * A reusable component for displaying anonymization levels
 */
const AnonymizationIndicator: React.FC<AnonymizationIndicatorProps> = ({ 
  level, 
  showLabel = true,
  className = ''
}) => {
  return (
    <div className={`anonymization-container ${className}`}>
      {showLabel && <span className="anon-label">Anonymization:</span>}
      <div className={`anon-indicator ${getAnonymizationClass(level)}`}>
        {level}
      </div>
    </div>
  );
};

export default AnonymizationIndicator; 