import React from 'react';

interface IconProps {
  className?: string;
  width?: number;
  height?: number;
  color?: string;
  'aria-hidden'?: boolean;
}

/**
 * PulseIcon - Represents data activity without surveillance connotations
 */
export const PulseIcon: React.FC<IconProps> = ({
  className = '',
  width = 24,
  height = 24,
  color = 'currentColor',
  'aria-hidden': ariaHidden = true
}) => {
  return (
    <svg 
      width={width} 
      height={height} 
      viewBox="0 0 24 24" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden={ariaHidden}
      role="img"
      aria-label="Data activity pulse"
    >
      <path 
        d="M3 12H6L9 3L15 21L18 12H21" 
        stroke={color} 
        strokeWidth="2" 
        strokeLinecap="round" 
        strokeLinejoin="round"
      />
    </svg>
  );
};

/**
 * ShieldIcon - Reinforces privacy and security messaging
 */
export const ShieldIcon: React.FC<IconProps> = ({
  className = '',
  width = 24,
  height = 24,
  color = 'currentColor',
  'aria-hidden': ariaHidden = true
}) => {
  return (
    <svg 
      width={width} 
      height={height} 
      viewBox="0 0 24 24" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden={ariaHidden}
      role="img"
      aria-label="Privacy shield"
    >
      <path 
        d="M12 22C12 22 20 18 20 12V5L12 2L4 5V12C4 18 12 22 12 22Z" 
        stroke={color} 
        strokeWidth="2" 
        strokeLinecap="round" 
        strokeLinejoin="round"
      />
      <path 
        d="M12 16C14.2091 16 16 14.2091 16 12C16 9.79086 14.2091 8 12 8C9.79086 8 8 9.79086 8 12C8 14.2091 9.79086 16 12 16Z" 
        stroke={color} 
        strokeWidth="2" 
        strokeLinecap="round"
      />
    </svg>
  );
};

/**
 * ArrowRightIcon - Used for the call-to-action button
 */
export const ArrowRightIcon: React.FC<IconProps> = ({
  className = '',
  width = 24,
  height = 24,
  color = 'currentColor',
  'aria-hidden': ariaHidden = true
}) => {
  return (
    <svg 
      width={width} 
      height={height} 
      viewBox="0 0 24 24" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden={ariaHidden}
      role="img"
      aria-label="Right arrow"
    >
      <path 
        d="M5 12H19" 
        stroke={color} 
        strokeWidth="2" 
        strokeLinecap="round" 
        strokeLinejoin="round"
      />
      <path 
        d="M12 5L19 12L12 19" 
        stroke={color} 
        strokeWidth="2" 
        strokeLinecap="round" 
        strokeLinejoin="round"
      />
    </svg>
  );
}; 