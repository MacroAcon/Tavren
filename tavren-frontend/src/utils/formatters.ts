/**
 * Utility functions for formatting data throughout the application
 */

import { PayoutCurrency } from '../types/wallet';

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

/**
 * Format a number as currency based on the provided currency code
 * @param amount The amount to format
 * @param currency The currency code (default: USD)
 * @returns Formatted currency string
 */
export const formatCurrency = (amount: number, currency: PayoutCurrency = PayoutCurrency.USD): string => {
  // Define currency formats
  const currencyFormats: Record<PayoutCurrency, { locale: string, code: string }> = {
    [PayoutCurrency.USD]: { locale: 'en-US', code: 'USD' },
    [PayoutCurrency.EUR]: { locale: 'de-DE', code: 'EUR' },
    [PayoutCurrency.GBP]: { locale: 'en-GB', code: 'GBP' },
    [PayoutCurrency.CAD]: { locale: 'en-CA', code: 'CAD' },
    [PayoutCurrency.AUD]: { locale: 'en-AU', code: 'AUD' }
  };

  const { locale, code } = currencyFormats[currency] || currencyFormats[PayoutCurrency.USD];

  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: code,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amount);
};

/**
 * Format a date string to a readable date format
 * @param dateString ISO date string
 * @param includeTime Whether to include the time
 * @returns Formatted date string
 */
export const formatDate = (dateString: string, includeTime = false): string => {
  const date = new Date(dateString);
  
  const options: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    ...(includeTime ? { hour: '2-digit', minute: '2-digit' } : {})
  };
  
  return date.toLocaleDateString(undefined, options);
};

/**
 * Format a date to show how long ago it was
 * @param dateString ISO date string
 * @returns Relative time string (e.g., "2 hours ago")
 */
export const formatRelativeTime = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  
  // Convert to seconds
  const diffSec = Math.floor(diffMs / 1000);
  
  if (diffSec < 60) {
    return diffSec === 1 ? '1 second ago' : `${diffSec} seconds ago`;
  }
  
  // Convert to minutes
  const diffMin = Math.floor(diffSec / 60);
  
  if (diffMin < 60) {
    return diffMin === 1 ? '1 minute ago' : `${diffMin} minutes ago`;
  }
  
  // Convert to hours
  const diffHour = Math.floor(diffMin / 60);
  
  if (diffHour < 24) {
    return diffHour === 1 ? '1 hour ago' : `${diffHour} hours ago`;
  }
  
  // Convert to days
  const diffDay = Math.floor(diffHour / 24);
  
  if (diffDay < 30) {
    return diffDay === 1 ? '1 day ago' : `${diffDay} days ago`;
  }
  
  // Convert to months
  const diffMonth = Math.floor(diffDay / 30);
  
  if (diffMonth < 12) {
    return diffMonth === 1 ? '1 month ago' : `${diffMonth} months ago`;
  }
  
  // Convert to years
  const diffYear = Math.floor(diffMonth / 12);
  
  return diffYear === 1 ? '1 year ago' : `${diffYear} years ago`;
}; 