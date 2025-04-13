/**
 * Common TypeScript interfaces used throughout the application
 */

export interface ConsentPermission {
  id: string;
  dataType: string;
  purpose: string;
  grantedAt: string;
  expiresAt: string;
  anonymizationLevel: string;
  buyerId: string;
  buyerName: string;
  trustTier: string;
}

export interface DataRequest {
  id: string;
  agentId: string;
  agentName: string;
  timestamp: string;
  dataType: string;
  purpose: string;
  scope: string;
  accessLevel: string;
  anonymizationLevel: string;
  duration: string;
  status: 'pending' | 'accepted' | 'declined' | 'counteroffered';
  buyerId: string;
  buyerName: string;
  trustTier: string;
}

export interface AgentCounterOffer {
  originalRequestId: string;
  offerId: string;
  dataType: string;
  purpose: string;
  scope: string;
  accessLevel: string;
  anonymizationLevel: string;
  duration: string;
}

export interface TrustData {
  buyerId: string;
  buyerName: string;
  trustScore: number;
  trustTier: string;
  privacyGrade: string;
  dataUseCompliance: number;
  dataRetentionScore: number;
  consentFollowScore: number;
  declineCount: number;
  totalInteractions: number;
  reasonStats: {
    privacy: number;
    trust: number;
    purpose: number;
    complexity: number;
    other: number;
  };
}

export interface BuyerSummaryStats {
  totalBuyers: number;
  highTrustCount: number;
  standardTrustCount: number;
  lowTrustCount: number;
  averageTrustScore: number;
} 