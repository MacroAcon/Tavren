import React, { useState, useEffect } from 'react';
import './agent-interaction.css';

// Define TypeScript interfaces
interface DataRequest {
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

interface AgentCounterOffer {
  originalRequestId: string;
  offerId: string;
  dataType: string;
  purpose: string;
  scope: string;
  accessLevel: string;
  anonymizationLevel: string;
  duration: string;
}

interface AgentInteractionProps {
  userId: string;
}

const AgentInteractionInterface: React.FC<AgentInteractionProps> = ({ userId }) => {
  const [dataRequests, setDataRequests] = useState<DataRequest[]>([]);
  const [selectedRequest, setSelectedRequest] = useState<DataRequest | null>(null);
  const [counterOffers, setCounterOffers] = useState<AgentCounterOffer[]>([]);
  const [showRejectionDialog, setShowRejectionDialog] = useState(false);
  const [rejectionReason, setRejectionReason] = useState('');
  const [rejectionCategory, setRejectionCategory] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch data requests from the API
  useEffect(() => {
    const fetchDataRequests = async () => {
      try {
        setLoading(true);
        // In a real implementation, replace with actual API endpoint
        const response = await fetch(`/api/data-packages/requests?userId=${userId}`);
        
        if (!response.ok) {
          throw new Error('Failed to fetch data requests');
        }
        
        const data = await response.json();
        setDataRequests(data);
        setError(null);
      } catch (err) {
        setError('Error loading data requests. Please try again.');
        console.error('Error fetching data requests:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDataRequests();
  }, [userId]);

  // Helper function to format timestamps
  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  // Handle request selection
  const selectRequest = (request: DataRequest) => {
    setSelectedRequest(request);
    
    // Fetch counter offers if they exist for this request
    fetchCounterOffers(request.id);
  };

  // Fetch counter offers for a request
  const fetchCounterOffers = async (requestId: string) => {
    try {
      // In a real implementation, replace with actual API endpoint
      const response = await fetch(`/api/data-packages/counter-offers?requestId=${requestId}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch counter offers');
      }
      
      const data = await response.json();
      setCounterOffers(data);
    } catch (err) {
      console.error('Error fetching counter offers:', err);
      setCounterOffers([]);
    }
  };

  // Handle accepting a request
  const handleAccept = async (requestId: string) => {
    try {
      // In a real implementation, replace with actual API endpoint
      const response = await fetch(`/api/data-packages/requests/accept`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ requestId }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to accept request');
      }
      
      // Update the request status in the UI
      setDataRequests(dataRequests.map(req => 
        req.id === requestId ? { ...req, status: 'accepted' as const } : req
      ));
      
      if (selectedRequest && selectedRequest.id === requestId) {
        setSelectedRequest({ ...selectedRequest, status: 'accepted' as const });
      }
      
    } catch (err) {
      setError('Error accepting request. Please try again.');
      console.error('Error accepting request:', err);
    }
  };

  // Show rejection dialog
  const openRejectionDialog = () => {
    setShowRejectionDialog(true);
  };

  // Handle rejecting a request
  const handleDecline = async () => {
    if (!selectedRequest) return;
    
    try {
      // In a real implementation, replace with actual API endpoint
      const response = await fetch(`/api/consent/decline`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          offer_id: selectedRequest.id,
          action: 'declined',
          user_reason: rejectionReason,
          reason_category: rejectionCategory
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to decline request');
      }
      
      // Update the request status in the UI
      setDataRequests(dataRequests.map(req => 
        req.id === selectedRequest.id ? { ...req, status: 'declined' as const } : req
      ));
      
      setSelectedRequest({ ...selectedRequest, status: 'declined' as const });
      setShowRejectionDialog(false);
      setRejectionReason('');
      setRejectionCategory('');
      
    } catch (err) {
      setError('Error declining request. Please try again.');
      console.error('Error declining request:', err);
    }
  };

  // Handle accepting a counter offer
  const handleAcceptCounterOffer = async (offerId: string) => {
    try {
      // In a real implementation, replace with actual API endpoint
      const response = await fetch(`/api/data-packages/counter-offers/accept`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ offerId }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to accept counter offer');
      }
      
      // Update the request status in the UI if this was the selected request
      if (selectedRequest) {
        const updatedRequests = dataRequests.map(req => 
          req.id === selectedRequest.id 
            ? { ...req, status: 'accepted' as const } 
            : req
        );
        setDataRequests(updatedRequests);
        setSelectedRequest({ ...selectedRequest, status: 'accepted' as const });
      }
      
    } catch (err) {
      setError('Error accepting counter offer. Please try again.');
      console.error('Error accepting counter offer:', err);
    }
  };

  // Render the request list
  const renderRequestList = () => {
    if (dataRequests.length === 0) {
      return (
        <div className="no-requests">
          <p>No pending data requests.</p>
        </div>
      );
    }

    return (
      <div className="request-list">
        {dataRequests
          .filter(req => req.status === 'pending')
          .map(request => (
            <div
              key={request.id}
              className={`request-item ${selectedRequest?.id === request.id ? 'selected' : ''}`}
              onClick={() => selectRequest(request)}
            >
              <div className="request-header">
                <span className="agent-name">{request.agentName}</span>
                <span className="request-time">{formatTimestamp(request.timestamp)}</span>
              </div>
              <div className="request-brief">
                <p>
                  <span className="data-type">{request.dataType}</span> for 
                  <span className="purpose"> {request.purpose}</span>
                </p>
              </div>
              <div className={`buyer-trust ${getTrustTierClass(request.trustTier)}`}>
                {request.buyerName} ({request.trustTier})
              </div>
            </div>
          ))
        }
      </div>
    );
  };

  // Get trust tier class
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

  // Get anonymization level description
  const getAnonymizationDescription = (level: string): string => {
    switch (level.toLowerCase()) {
      case 'none':
        return 'No anonymization - your data will be shared as-is with full details.';
      case 'minimal':
        return 'Basic anonymization - personal identifiers are removed but correlations remain.';
      case 'partial':
        return 'Moderate anonymization - key identifiers are obfuscated with reduced correlation.';
      case 'full':
        return 'Maximum anonymization - complete obfuscation of all personally identifying information.';
      default:
        return 'Unknown anonymization level.';
    }
  };

  // Render the request details
  const renderRequestDetails = () => {
    if (!selectedRequest) {
      return (
        <div className="select-request-prompt">
          <p>Select a request to view details</p>
        </div>
      );
    }

    return (
      <div className="request-details">
        <h3>{selectedRequest.agentName} wants your data</h3>
        
        <div className="detail-section">
          <h4>Request Details</h4>
          <div className="detail-item">
            <span className="label">Data Type:</span>
            <span className="value">{selectedRequest.dataType}</span>
          </div>
          <div className="detail-item">
            <span className="label">Purpose:</span>
            <span className="value">{selectedRequest.purpose}</span>
          </div>
          <div className="detail-item">
            <span className="label">Scope:</span>
            <span className="value">{selectedRequest.scope}</span>
          </div>
          <div className="detail-item">
            <span className="label">Access Level:</span>
            <span className="value">{selectedRequest.accessLevel}</span>
          </div>
          <div className="detail-item">
            <span className="label">Anonymization:</span>
            <span className="value">{selectedRequest.anonymizationLevel}</span>
            <div className="anon-description">
              {getAnonymizationDescription(selectedRequest.anonymizationLevel)}
            </div>
          </div>
          <div className="detail-item">
            <span className="label">Duration:</span>
            <span className="value">{selectedRequest.duration}</span>
          </div>
        </div>
        
        <div className="detail-section">
          <h4>Buyer Information</h4>
          <div className="detail-item">
            <span className="label">Buyer:</span>
            <span className="value">{selectedRequest.buyerName}</span>
          </div>
          <div className="detail-item">
            <span className="label">Trust Tier:</span>
            <span className={`value ${getTrustTierClass(selectedRequest.trustTier)}`}>
              {selectedRequest.trustTier}
            </span>
          </div>
        </div>
        
        {counterOffers.length > 0 && (
          <div className="counter-offers-section">
            <h4>Alternative Options</h4>
            <div className="counter-offers-list">
              {counterOffers.map(offer => (
                <div key={offer.offerId} className="counter-offer">
                  <h5>Alternative Offer</h5>
                  <div className="detail-item">
                    <span className="label">Anonymization:</span>
                    <span className="value highlight">{offer.anonymizationLevel}</span>
                  </div>
                  <div className="detail-item">
                    <span className="label">Duration:</span>
                    <span className="value highlight">{offer.duration}</span>
                  </div>
                  <div className="detail-item">
                    <span className="label">Scope:</span>
                    <span className="value highlight">{offer.scope}</span>
                  </div>
                  <button 
                    className="accept-counter-offer-button" 
                    onClick={() => handleAcceptCounterOffer(offer.offerId)}
                  >
                    Accept This Alternative
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {selectedRequest.status === 'pending' && (
          <div className="action-buttons">
            <button 
              className="accept-button" 
              onClick={() => handleAccept(selectedRequest.id)}
            >
              Accept Request
            </button>
            <button 
              className="decline-button" 
              onClick={openRejectionDialog}
            >
              Decline Request
            </button>
          </div>
        )}
        
        {selectedRequest.status === 'accepted' && (
          <div className="status-message success">
            You've accepted this request.
          </div>
        )}
        
        {selectedRequest.status === 'declined' && (
          <div className="status-message declined">
            You've declined this request.
          </div>
        )}
      </div>
    );
  };

  // Render the rejection dialog
  const renderRejectionDialog = () => {
    if (!showRejectionDialog) return null;
    
    return (
      <div className="rejection-dialog-overlay">
        <div className="rejection-dialog">
          <h3>Why are you declining this request?</h3>
          
          <div className="reason-category">
            <h4>Select a reason:</h4>
            <div className="reason-options">
              <label>
                <input 
                  type="radio" 
                  name="reason-category" 
                  value="privacy" 
                  checked={rejectionCategory === 'privacy'}
                  onChange={() => setRejectionCategory('privacy')}
                />
                Privacy Concerns
              </label>
              
              <label>
                <input 
                  type="radio" 
                  name="reason-category" 
                  value="trust" 
                  checked={rejectionCategory === 'trust'}
                  onChange={() => setRejectionCategory('trust')}
                />
                Don't Trust Buyer
              </label>
              
              <label>
                <input 
                  type="radio" 
                  name="reason-category" 
                  value="purpose" 
                  checked={rejectionCategory === 'purpose'}
                  onChange={() => setRejectionCategory('purpose')}
                />
                Don't Agree With Purpose
              </label>
              
              <label>
                <input 
                  type="radio" 
                  name="reason-category" 
                  value="complexity" 
                  checked={rejectionCategory === 'complexity'}
                  onChange={() => setRejectionCategory('complexity')}
                />
                Too Complex to Understand
              </label>
              
              <label>
                <input 
                  type="radio" 
                  name="reason-category" 
                  value="other" 
                  checked={rejectionCategory === 'other'}
                  onChange={() => setRejectionCategory('other')}
                />
                Other
              </label>
            </div>
          </div>
          
          <div className="reason-details">
            <h4>Additional details (optional):</h4>
            <textarea 
              value={rejectionReason} 
              onChange={(e) => setRejectionReason(e.target.value)}
              placeholder="Tell us more about why you're declining..."
            />
          </div>
          
          <div className="dialog-buttons">
            <button 
              className="cancel-button"
              onClick={() => setShowRejectionDialog(false)}
            >
              Cancel
            </button>
            <button 
              className="submit-button"
              disabled={!rejectionCategory}
              onClick={handleDecline}
            >
              Submit
            </button>
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return <div className="agent-interaction loading">Loading data requests...</div>;
  }

  if (error) {
    return <div className="agent-interaction error">{error}</div>;
  }

  return (
    <div className="agent-interaction">
      <h2>Data Requests</h2>
      
      <div className="interaction-container">
        <div className="requests-panel">
          {renderRequestList()}
        </div>
        
        <div className="details-panel">
          {renderRequestDetails()}
        </div>
      </div>
      
      {renderRejectionDialog()}
    </div>
  );
};

export default AgentInteractionInterface; 