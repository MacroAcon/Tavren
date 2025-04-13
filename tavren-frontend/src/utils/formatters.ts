/**
 * Utility functions for formatting data throughout the application
 */

/**
 * Formats a timestamp to a locale string
 */
export const formatTimestamp = (timestamp: string): string => {
  const date = new Date(timestamp);
  return date.toLocaleString();
};

/**
 * Formats a value as a percentage
 */
export const formatPercentage = (value: number): string => {
  return `${Math.round(value)}%`;
};

/**
 * Calculates the time remaining until an expiry date
 */
export const calculateTimeRemaining = (expiresAt: string): string => {
  const now = new Date();
  const expiry = new Date(expiresAt);
  const diffMs = expiry.getTime() - now.getTime();
  
  if (diffMs <= 0) return 'Expired';
  
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  const diffHours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  
  if (diffDays > 0) {
    return `${diffDays}d ${diffHours}h remaining`;
  }
  return `${diffHours}h remaining`;
};

/**
 * Calculate expiry percentage for progress bars
 */
export const calculateExpiryPercentage = (grantedAt: string, expiresAt: string): number => {
  const now = new Date().getTime();
  const granted = new Date(grantedAt).getTime();
  const expires = new Date(expiresAt).getTime();
  
  if (now >= expires) return 0;
  if (granted >= expires) return 100;
  
  const totalDuration = expires - granted;
  const remainingDuration = expires - now;
  
  return Math.round((remainingDuration / totalDuration) * 100);
}; 