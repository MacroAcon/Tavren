/**
 * Utility functions for consistent styling across components
 */

/**
 * Returns CSS class for trust tier
 */
export const getTrustTierClass = (tier: string): string => {
  switch (tier.toLowerCase()) {
    case 'high':
      return 'trust-high';
    case 'standard':
      return 'trust-standard';
    case 'low':
      return 'trust-low';
    default:
      return 'trust-unknown';
  }
};

/**
 * Returns icon for trust tier
 */
export const getTrustTierIcon = (tier: string): string => {
  switch (tier.toLowerCase()) {
    case 'high':
      return '🛡️';
    case 'standard':
      return '✓';
    case 'low':
      return '⚠️';
    default:
      return '❓';
  }
};

/**
 * Returns description for trust tier
 */
export const getTrustTierDescription = (tier: string): string => {
  switch (tier.toLowerCase()) {
    case 'high':
      return 'Data buyers in this tier have demonstrated exceptional compliance with privacy standards and responsible data use. They follow strict data handling protocols and have a strong history of respecting user consent choices.';
    case 'standard':
      return 'Data buyers in this tier meet expected industry standards for data handling and privacy. They have a good track record but occasionally may have minor compliance issues or user feedback concerns.';
    case 'low':
      return 'Data buyers in this tier have significant issues with data handling practices or have repeatedly received negative user feedback. Exercise caution when sharing data with these buyers.';
    default:
      return 'Trust tier information not available.';
  }
};

/**
 * Returns CSS class for anonymization level
 */
export const getAnonymizationClass = (level: string): string => {
  switch (level.toLowerCase()) {
    case 'none':
      return 'anon-none';
    case 'minimal':
      return 'anon-minimal';
    case 'partial':
      return 'anon-partial';
    case 'full':
      return 'anon-full';
    default:
      return 'anon-unknown';
  }
};

/**
 * Returns description for anonymization level
 */
export const getAnonymizationDescription = (level: string): string => {
  switch (level.toLowerCase()) {
    case 'none':
      return 'No anonymization applied - data includes your full identity.';
    case 'minimal':
      return 'Basic identifiers removed but demographics retained.';
    case 'partial':
      return 'Most identifying information removed. Only categorical data remains.';
    case 'full':
      return 'Complete anonymization - no way to link data back to you.';
    default:
      return 'Anonymization level not specified.';
  }
};

/**
 * Returns icon for data type
 */
export const getDataTypeIcon = (type: string): string => {
  switch (type.toLowerCase()) {
    case 'location':
      return '📍';
    case 'app_usage':
      return '📱';
    case 'browsing_history':
      return '🌐';
    case 'health':
      return '❤️';
    case 'financial':
      return '💰';
    default:
      return '📄';
  }
};

/**
 * Returns color for trust score
 */
export const getTrustScoreColor = (score: number): string => {
  if (score >= 85) return '#4caf50'; // High - green
  if (score >= 70) return '#2196f3'; // Standard - blue
  if (score >= 50) return '#ff9800'; // Caution - orange
  return '#f44336'; // Low - red
}; 