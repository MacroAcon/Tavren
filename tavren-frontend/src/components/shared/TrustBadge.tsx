import React from 'react';
import { getTrustTierClass, getTrustTierIcon } from '../../utils/styleHelpers';

interface TrustBadgeProps {
  trustTier: string;
  showIcon?: boolean;
  className?: string;
}

/**
 * A reusable badge component for displaying trust tiers
 */
const TrustBadge: React.FC<TrustBadgeProps> = ({ 
  trustTier, 
  showIcon = true,
  className = ''
}) => {
  return (
    <span className={`trust-badge ${getTrustTierClass(trustTier)} ${className}`}>
      {showIcon && <span className="trust-icon">{getTrustTierIcon(trustTier)}</span>}
      {trustTier}
    </span>
  );
};

export default TrustBadge; 