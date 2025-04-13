import React from 'react';

// Mock API endpoint for analytics events
const MOCK_API_ENDPOINT = '/api/analytics';

/**
 * Mock analytics tracking functions
 * These will be replaced with actual analytics integration in production
 */

/**
 * Track a specific event with optional properties
 */
export const trackEvent = (eventName: string, properties?: Record<string, any>): void => {
  console.log(`[Analytics] Tracked event: ${eventName}`, properties);
};

/**
 * Track A/B test variant view 
 */
export const trackVariantView = (testId: string, variant: string): void => {
  console.log(`[Analytics] A/B Test: ${testId}, Variant: ${variant}`);
  // Store the variant to maintain consistency through the journey
  storeVariant(testId, variant);
};

/**
 * Track A/B test variant conversion
 */
export const trackVariantConversion = (testId: string, variant: string, action: string): void => {
  console.log(`[Analytics] A/B Test Conversion: ${testId}, Variant: ${variant}, Action: ${action}`);
};

/**
 * Log a specific conversion event for A/B testing
 * Records which variant led to which action
 */
export const logConversionEvent = (variant: string, action: string, testId: string = 'onboarding-value-proposition'): void => {
  console.log(`[Analytics] Conversion Event: ${testId}, Variant: ${variant}, Action: ${action}`, {
    timestamp: Date.now(),
    testId,
    variant,
    action,
    conversionType: action.includes('_') ? action.split('_')[0] : action,
    source: 'onboarding'
  });
};

/**
 * Get variant from URL param or return null
 */
export const getVariantFromUrl = (paramName: string = 'variant'): string | null => {
  if (typeof window !== 'undefined') {
    const params = new URLSearchParams(window.location.search);
    return params.get(paramName);
  }
  return null;
};

/**
 * Randomly select a variant
 */
export const getRandomVariant = (variants: string[]): string => {
  const randomIndex = Math.floor(Math.random() * variants.length);
  return variants[randomIndex];
};

/**
 * Store the current variant in session storage
 */
export const storeVariant = (testId: string, variant: string): void => {
  if (typeof window !== 'undefined' && window.sessionStorage) {
    window.sessionStorage.setItem(`ab_test_${testId}`, variant);
  }
};

/**
 * Retrieve stored variant from session storage
 */
export const getStoredVariant = (testId: string): string | null => {
  if (typeof window !== 'undefined' && window.sessionStorage) {
    return window.sessionStorage.getItem(`ab_test_${testId}`);
  }
  return null;
}; 