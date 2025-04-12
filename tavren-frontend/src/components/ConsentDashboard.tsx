import React, { useState, useEffect } from 'react';
import './consent-dashboard.css';

// Define TypeScript interfaces for our data
interface ConsentPermission {
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

interface ConsentDashboardProps {
  userId: string;
}

const ConsentDashboard: React.FC<ConsentDashboardProps> = ({ userId }) => {
  const [activeConsents, setActiveConsents] = useState<ConsentPermission[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch active consents from the API
  useEffect(() => {
    const fetchConsents = async () => {
      try {
        setLoading(true);
        // In a real implementation, replace with actual API endpoint
        const response = await fetch(`/api/data-packages/consents/active?userId=${userId}`);
        
        if (!response.ok) {
          throw new Error('Failed to fetch active consents');
        }
        
        const data = await response.json();
        setActiveConsents(data);
        setError(null);
      } catch (err) {
        setError('Error loading consent data. Please try again.');
        console.error('Error fetching consent data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchConsents();
  }, [userId]);

  // Calculate time remaining for a consent
  const calculateTimeRemaining = (expiresAt: string): string => {
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

  // Handle consent revocation
  const handleRevokeConsent = async (consentId: string) => {
    try {
      // In a real implementation, replace with actual API endpoint
      const response = await fetch(`/api/data-packages/consents/revoke`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ consentId }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to revoke consent');
      }
      
      // Remove the revoked consent from the UI
      setActiveConsents(activeConsents.filter(consent => consent.id !== consentId));
    } catch (err) {
      setError('Error revoking consent. Please try again.');
      console.error('Error revoking consent:', err);
    }
  };

  // Get CSS class for anonymization level
  const getAnonymizationClass = (level: string): string => {
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

  // Get icon for data type
  const getDataTypeIcon = (type: string): string => {
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

  // Get class for trust tier
  const getTrustTierClass = (tier: string): string => {
    switch (tier.toLowerCase()) {
      case 'low':
        return 'trust-low';
      case 'standard':
        return 'trust-standard';
      case 'high':
        return 'trust-high';
      default:
        return 'trust-unknown';
    }
  };

  if (loading) {
    return <div className="consent-dashboard loading">Loading active consents...</div>;
  }

  if (error) {
    return <div className="consent-dashboard error">{error}</div>;
  }

  return (
    <div className="consent-dashboard">
      <h2>Active Consent Permissions</h2>
      
      {activeConsents.length === 0 ? (
        <div className="no-consents">
          <p>You currently have no active consent permissions.</p>
        </div>
      ) : (
        <div className="consent-grid">
          {activeConsents.map(consent => (
            <div key={consent.id} className="consent-card">
              <div className="consent-header">
                <span className="data-type-icon">{getDataTypeIcon(consent.dataType)}</span>
                <h3>{consent.dataType}</h3>
                <span className={`trust-badge ${getTrustTierClass(consent.trustTier)}`}>
                  {consent.trustTier}
                </span>
              </div>
              
              <div className="consent-details">
                <p><strong>Purpose:</strong> {consent.purpose}</p>
                <p><strong>Buyer:</strong> {consent.buyerName}</p>
                <p><strong>Granted:</strong> {new Date(consent.grantedAt).toLocaleDateString()}</p>
                
                <div className="expiry-container">
                  <span className="expiry-label">Expires:</span>
                  <span className="expiry-value">{calculateTimeRemaining(consent.expiresAt)}</span>
                  <div className="expiry-progress">
                    <div 
                      className="expiry-bar" 
                      style={{ 
                        width: `${calculateExpiryPercentage(consent.grantedAt, consent.expiresAt)}%` 
                      }}
                    ></div>
                  </div>
                </div>
                
                <div className="anonymization-container">
                  <span className="anon-label">Anonymization:</span>
                  <div className={`anon-indicator ${getAnonymizationClass(consent.anonymizationLevel)}`}>
                    {consent.anonymizationLevel}
                  </div>
                </div>
              </div>
              
              <div className="consent-controls">
                <button 
                  className="revoke-button"
                  onClick={() => handleRevokeConsent(consent.id)}
                >
                  Revoke Consent
                </button>
                <button className="view-details-button">
                  View Details
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Helper function to calculate expiry percentage for progress bar
const calculateExpiryPercentage = (grantedAt: string, expiresAt: string): number => {
  const now = new Date().getTime();
  const granted = new Date(grantedAt).getTime();
  const expires = new Date(expiresAt).getTime();
  
  if (now >= expires) return 0;
  if (granted >= expires) return 100;
  
  const totalDuration = expires - granted;
  const remainingDuration = expires - now;
  
  return Math.round((remainingDuration / totalDuration) * 100);
};

export default ConsentDashboard; 