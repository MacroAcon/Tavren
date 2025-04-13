import React from 'react';

interface CardProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  className?: string;
  onClick?: () => void;
  selected?: boolean;
}

/**
 * A reusable card component for consistent layout
 */
const Card: React.FC<CardProps> = ({ 
  children,
  title,
  subtitle,
  className = '',
  onClick,
  selected = false
}) => {
  return (
    <div 
      className={`
        card 
        ${onClick ? 'card-clickable' : ''} 
        ${selected ? 'card-selected' : ''} 
        ${className}
      `}
      onClick={onClick}
    >
      {(title || subtitle) && (
        <div className="card-header">
          {title && <h3 className="card-title">{title}</h3>}
          {subtitle && <div className="card-subtitle">{subtitle}</div>}
        </div>
      )}
      <div className="card-content">
        {children}
      </div>
    </div>
  );
};

export default Card; 