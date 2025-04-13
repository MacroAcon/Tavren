import React from 'react';
import './consent-dashboard.css';
import { ConsentPermission } from '../types/common';
import { useApiData } from '../hooks/useApiData';
import { useApiMutation } from '../hooks/useApiMutation';
import { EMPTY_STATES, ERROR_MESSAGES } from '../constants/copy';

// Import all shared components from index
import {
  Card,
  LoadingState,
  ErrorState,
  DataTypeIndicator,
  TrustBadge,
  ExpiryProgress,
  AnonymizationIndicator,
  Button
} from './shared';

interface ConsentDashboardProps {
  userId: string;
}

const ConsentDashboard: React.FC<ConsentDashboardProps> = ({ userId }) => {
  // Use shared hook for fetching data
  const { 
    data: activeConsents, 
    loading, 
    error, 
    refetch 
  } = useApiData<ConsentPermission[]>(
    `/api/data-packages/consents/active?userId=${userId}`,
    [userId]
  );

  // Use shared hook for mutations
  const { 
    mutate: revokeConsent, 
    error: revokeError 
  } = useApiMutation<{ success: boolean }>('/api/data-packages/consents/revoke');

  // Handle consent revocation
  const handleRevokeConsent = async (consentId: string) => {
    await revokeConsent({ consentId });
    refetch();
  };

  if (loading) {
    return <LoadingState message="Loading active consents..." className="consent-dashboard" />;
  }

  if (error || revokeError) {
    return (
      <ErrorState 
        message={revokeError || ERROR_MESSAGES.FETCH_CONSENTS} 
        onRetry={refetch}
        className="consent-dashboard" 
      />
    );
  }

  return (
    <div className="consent-dashboard">
      <h2>Active Consent Permissions</h2>
      
      {!activeConsents || activeConsents.length === 0 ? (
        <div className="no-consents">
          <p>{EMPTY_STATES.NO_CONSENTS}</p>
        </div>
      ) : (
        <div className="consent-grid">
          {activeConsents.map(consent => (
            <Card 
              key={consent.id} 
              className="consent-card"
            >
              <div className="consent-header">
                <DataTypeIndicator dataType={consent.dataType} />
                <TrustBadge trustTier={consent.trustTier} />
              </div>
              
              <div className="consent-details">
                <p><strong>Purpose:</strong> {consent.purpose}</p>
                <p><strong>Buyer:</strong> {consent.buyerName}</p>
                <p><strong>Granted:</strong> {new Date(consent.grantedAt).toLocaleDateString()}</p>
                
                <ExpiryProgress 
                  grantedAt={consent.grantedAt} 
                  expiresAt={consent.expiresAt} 
                />
                
                <AnonymizationIndicator level={consent.anonymizationLevel} />
              </div>
              
              <div className="consent-controls">
                <Button 
                  variant="danger"
                  onClick={() => handleRevokeConsent(consent.id)}
                  className="revoke-button"
                >
                  Revoke Consent
                </Button>
                <Button 
                  variant="outline"
                  className="view-details-button"
                >
                  View Details
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default ConsentDashboard; 