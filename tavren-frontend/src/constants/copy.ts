/**
 * Application-wide text content
 */

export const TRUST_TIER_DESCRIPTIONS = {
  HIGH: 'Data buyers in this tier have demonstrated exceptional compliance with privacy standards and responsible data use. They follow strict data handling protocols and have a strong history of respecting user consent choices.',
  STANDARD: 'Data buyers in this tier meet expected industry standards for data handling and privacy. They have a good track record but occasionally may have minor compliance issues or user feedback concerns.',
  LOW: 'Data buyers in this tier have significant issues with data handling practices or have repeatedly received negative user feedback. Exercise caution when sharing data with these buyers.',
  UNKNOWN: 'Trust tier information not available.'
};

export const TRUST_TIER_BULLETS = {
  HIGH: [
    'Excellent compliance with data use policies',
    'Robust data security measures',
    'Transparent data practices',
    'Strong history of respecting consent'
  ],
  STANDARD: [
    'Good compliance with data policies',
    'Adequate security protocols',
    'Generally respects consent boundaries',
    'Occasional minor compliance issues'
  ],
  LOW: [
    'History of policy violations',
    'Questionable data handling practices',
    'Multiple user complaints',
    'Limited transparency'
  ]
};

export const ANONYMIZATION_DESCRIPTIONS = {
  NONE: 'No anonymization applied - data includes your full identity.',
  MINIMAL: 'Basic identifiers removed but demographics retained.',
  PARTIAL: 'Most identifying information removed. Only categorical data remains.',
  FULL: 'Complete anonymization - no way to link data back to you.',
  UNKNOWN: 'Anonymization level not specified.'
};

export const CONSENT_EXPLANATION = 'When you accept an offer, you are granting explicit permission for your data to be used for the specific purpose stated. You can revoke this consent at any time.';

export const ERROR_MESSAGES = {
  FETCH_CONSENTS: 'Error loading consent data. Please try again.',
  FETCH_REQUESTS: 'Error loading data requests. Please try again.',
  REVOKE_CONSENT: 'Error revoking consent. Please try again.',
  ACCEPT_REQUEST: 'Error accepting request. Please try again.',
  DECLINE_REQUEST: 'Error declining request. Please try again.',
  FETCH_TRUST_DATA: 'Error loading trust data. Please try again.',
  ACCEPT_COUNTER_OFFER: 'Error accepting counter offer. Please try again.'
};

export const EMPTY_STATES = {
  NO_CONSENTS: 'You currently have no active consent permissions.',
  NO_REQUESTS: 'No pending data requests.',
  NO_HISTORY: 'No data sharing history found.',
  NO_TRUST_DATA: 'No trust data available yet.'
}; 