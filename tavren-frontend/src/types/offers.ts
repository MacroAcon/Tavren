/**
 * Offer Types for Data-Sharing Marketplace
 */

export enum OfferType {
  OneTime = 'one_time',
  Subscription = 'subscription',
  Limited = 'limited'
}

export enum OfferStatus {
  Active = 'active',
  Expired = 'expired',
  Accepted = 'accepted',
  Rejected = 'rejected',
  Pending = 'pending'
}

export enum DataAccessLevel {
  Basic = 'basic',
  Extended = 'extended',
  Comprehensive = 'comprehensive',
  Full = 'full'
}

export enum DataCategory {
  Demographics = 'demographics',
  Preferences = 'preferences',
  Behaviors = 'behaviors',
  Financial = 'financial',
  Medical = 'medical',
  Location = 'location',
  Social = 'social',
  Professional = 'professional'
}

export interface DataRequest {
  category: DataCategory;
  accessLevel: DataAccessLevel;
  description: string;
  required: boolean;
}

export interface Buyer {
  id: string;
  name: string;
  trustTier: number; // 1-5 rating
  description: string;
  logo?: string;
  industry?: string;
}

export interface Offer {
  id: string;
  title: string;
  description: string;
  type: OfferType;
  status: OfferStatus;
  payout: {
    amount: number;
    currency: string;
  };
  duration: {
    value: number;
    unit: 'days' | 'weeks' | 'months' | 'years';
  };
  expiresAt: string;
  createdAt: string;
  buyer: Buyer;
  dataRequests: DataRequest[];
  tags: string[];
  matchScore?: number; // How well this matches user preferences (0-100)
}

export interface OfferFilters {
  types?: OfferType[];
  minPayout?: number;
  maxPayout?: number;
  dataCategories?: DataCategory[];
  minTrustTier?: number;
  search?: string;
  tags?: string[];
}

export interface OfferFeedState {
  offers: Offer[];
  selectedOffer: Offer | null;
  filters: OfferFilters;
  rejectedOfferIds: string[];
  loading: boolean;
  error: string | null;
  page: number;
  hasMore: boolean;
} 