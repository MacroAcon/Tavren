import React from 'react';
import './shared-components.css';

interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'danger' | 'success' | 'outline';
  disabled?: boolean;
  className?: string;
  type?: 'button' | 'submit' | 'reset';
  fullWidth?: boolean;
}

/**
 * A reusable button component with consistent styling
 */
const Button: React.FC<ButtonProps> = ({ 
  children,
  onClick,
  variant = 'primary',
  disabled = false,
  className = '',
  type = 'button',
  fullWidth = false
}) => {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`
        button 
        button-${variant} 
        ${fullWidth ? 'button-full-width' : ''} 
        ${className}
      `}
    >
      {children}
    </button>
  );
};

export default Button; 