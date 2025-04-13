import React from 'react';
import { getDataTypeIcon } from '../../utils/styleHelpers';

interface DataTypeIndicatorProps {
  dataType: string;
  showLabel?: boolean;
  className?: string;
}

/**
 * A reusable component for displaying data types with icons
 */
const DataTypeIndicator: React.FC<DataTypeIndicatorProps> = ({ 
  dataType, 
  showLabel = true,
  className = ''
}) => {
  return (
    <span className={`data-type-indicator ${className}`}>
      <span className="data-type-icon">{getDataTypeIcon(dataType)}</span>
      {showLabel && <span className="data-type-label">{dataType}</span>}
    </span>
  );
};

export default DataTypeIndicator; 