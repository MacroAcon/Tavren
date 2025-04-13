import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { useOfferStore, notifySuccess, notifyError } from '../../stores';
import { 
  Offer, 
  OfferType, 
  DataAccessLevel, 
  DataCategory, 
  OfferStatus 
} from '../../types/offers';
import { LoadingState, ErrorState, Dialog } from '../shared';
import './offers.css';

// Helper function to format currency (same as in OfferFeed)
const formatCurrency = (amount: number, currency: string = 'USD') => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  }).format(amount);
};

// Helper to format duration (same as in OfferFeed)
const formatDuration = (value: number, unit: string) => {
  return `${value} ${value === 1 ? unit.slice(0, -1) : unit}`;
};

// Format date function
const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date);
};

// Data Category Badge
const DataCategoryBadge: React.FC<{ category: DataCategory }> = ({ category }) => {
  // Map categories to colors
  const categoryColors: Record<DataCategory, string> = {
    [DataCategory.Demographics]: 'blue',
    [DataCategory.Preferences]: 'purple',
    [DataCategory.Behaviors]: 'teal',
    [DataCategory.Financial]: 'red',
    [DataCategory.Medical]: 'orange',
    [DataCategory.Location]: 'green',
    [DataCategory.Social]: 'pink',
    [DataCategory.Professional]: 'brown'
  };
  
  return (
    <span className={`data-category-badge ${categoryColors[category]}`}>
      {category.charAt(0).toUpperCase() + category.slice(1)}
    </span>
  );
};

// Access Level Indicator with explanation
const AccessLevelIndicator: React.FC<{ level: DataAccessLevel }> = ({ level }) => {
  // Map access levels to descriptions
  const accessLevelDescriptions: Record<DataAccessLevel, string> = {
    [DataAccessLevel.Basic]: 'Limited access to summary data only',
    [DataAccessLevel.Extended]: 'Access to detailed data with some anonymization',
    [DataAccessLevel.Comprehensive]: 'Access to most data with minimal anonymization',
    [DataAccessLevel.Full]: 'Complete access to all data without anonymization'
  };
  
  // Map access levels to colors and bar widths
  const accessLevelConfig: Record<DataAccessLevel, { color: string, width: number }> = {
    [DataAccessLevel.Basic]: { color: 'green', width: 25 },
    [DataAccessLevel.Extended]: { color: 'blue', width: 50 },
    [DataAccessLevel.Comprehensive]: { color: 'orange', width: 75 },
    [DataAccessLevel.Full]: { color: 'red', width: 100 }
  };
  
  const { color, width } = accessLevelConfig[level];
  
  return (
    <div className="access-level-indicator">
      <div className="access-level-label">
        {level.charAt(0).toUpperCase() + level.slice(1)} Access
      </div>
      <div className="access-level-bar">
        <div
          className={`access-level-fill ${color}`}
          style={{ width: `${width}%` }}
        ></div>
      </div>
      <div className="access-level-description">
        {accessLevelDescriptions[level]}
      </div>
    </div>
  );
};

// Trust tier explainer
const TrustTierExplainer: React.FC<{ tier: number }> = ({ tier }) => {
  // Map trust tiers to descriptions
  const trustTierDescriptions: Record<number, string> = {
    1: 'Basic verification only. Use caution when sharing sensitive data.',
    2: 'Verified identity but limited track record. Some protections in place.',
    3: 'Established buyer with good track record. Standard protections.',
    4: 'Trusted buyer with strong data protection practices.',
    5: 'Premium trusted buyer with highest standards of data protection and ethics.'
  };
  
  return (
    <div className="trust-tier-explainer">
      <div className="trust-tier-header">
        <span 
          className={`trust-badge trust-tier-${tier} trust-${tier >= 4 ? 'green' : tier >= 3 ? 'orange' : 'red'}`}
        >
          Trust Tier {tier}
        </span>
      </div>
      <p className="trust-tier-description">
        {trustTierDescriptions[tier]}
      </p>
    </div>
  );
};

// OfferDetail Component
const OfferDetail: React.FC = () => {
  const { offerId } = useParams<{ offerId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  
  // Check if we're in "accept" mode from the URL
  const showAcceptDialog = new URLSearchParams(location.search).get('accept') === 'true';
  
  const { 
    fetchOfferById,
    selectedOffer,
    loading,
    error
  } = useOfferStore();
  
  // Local state for accept dialog
  const [isAcceptDialogOpen, setIsAcceptDialogOpen] = useState(showAcceptDialog);
  const [acceptInProgress, setAcceptInProgress] = useState(false);
  
  // Fetch offer details when component mounts
  useEffect(() => {
    if (offerId) {
      fetchOfferById(offerId);
    }
  }, [offerId, fetchOfferById]);
  
  // Handle back button click
  const handleBackClick = useCallback(() => {
    navigate('/offers');
  }, [navigate]);
  
  // Handle accept offer
  const handleAcceptOffer = useCallback(() => {
    setIsAcceptDialogOpen(true);
  }, []);
  
  // Handle dialog confirmation
  const handleConfirmAccept = useCallback(() => {
    if (!selectedOffer) return;
    
    setAcceptInProgress(true);
    
    // Simulate API call to accept offer
    setTimeout(() => {
      setAcceptInProgress(false);
      setIsAcceptDialogOpen(false);
      notifySuccess(`You've accepted the offer: ${selectedOffer.title}`);
      
      // Redirect to dashboard or some confirmation page
      navigate('/offers?accepted=true');
    }, 1500);
  }, [selectedOffer, navigate]);
  
  // Handle dialog close
  const handleCloseDialog = useCallback(() => {
    setIsAcceptDialogOpen(false);
    
    // Also remove the accept=true from URL if present
    if (showAcceptDialog) {
      navigate(location.pathname, { replace: true });
    }
  }, [navigate, location.pathname, showAcceptDialog]);
  
  // Handle reject offer
  const handleRejectOffer = useCallback(() => {
    if (!selectedOffer) return;
    
    // Simulate API call to reject offer
    setTimeout(() => {
      notifyError(`You've rejected the offer: ${selectedOffer.title}`);
      navigate('/offers?rejected=true');
    }, 500);
  }, [selectedOffer, navigate]);
  
  // Show loading state
  if (loading) {
    return <LoadingState />;
  }
  
  // Show error state
  if (error || !selectedOffer) {
    return <ErrorState message={error || 'Offer not found'} />;
  }
  
  const offer = selectedOffer;
  
  return (
    <div className="offer-detail">
      <button className="back-button" onClick={handleBackClick}>
        ← Back to Offers
      </button>
      
      <div className="offer-detail-header">
        <div className="offer-badges">
          <span className={`offer-type-badge ${offer.type}`}>
            {offer.type === OfferType.OneTime ? 'One-time' : 
             offer.type === OfferType.Subscription ? 'Subscription' : 'Limited Time'}
          </span>
          <span className={`offer-status-badge ${offer.status.toLowerCase()}`}>
            {offer.status}
          </span>
        </div>
        
        <h1>{offer.title}</h1>
        
        <div className="offer-buyer-details">
          {offer.buyer.logo && (
            <img 
              src={offer.buyer.logo} 
              alt={`${offer.buyer.name} logo`} 
              className="buyer-logo-large" 
            />
          )}
          <div className="buyer-info">
            <h3>{offer.buyer.name}</h3>
            <p>{offer.buyer.industry || 'Data Partner'}</p>
            <TrustTierExplainer tier={offer.buyer.trustTier} />
          </div>
        </div>
      </div>
      
      <div className="offer-detail-body">
        <div className="offer-detail-section">
          <h2>Offer Details</h2>
          
          <div className="offer-detail-grid">
            <div className="detail-item">
              <span className="detail-label">Payout:</span>
              <span className="detail-value payout-amount-large">
                {formatCurrency(offer.payout.amount, offer.payout.currency)}
              </span>
            </div>
            
            <div className="detail-item">
              <span className="detail-label">Duration:</span>
              <span className="detail-value">
                {formatDuration(offer.duration.value, offer.duration.unit)}
              </span>
            </div>
            
            <div className="detail-item">
              <span className="detail-label">Created:</span>
              <span className="detail-value">
                {formatDate(offer.createdAt)}
              </span>
            </div>
            
            <div className="detail-item">
              <span className="detail-label">Expires:</span>
              <span className="detail-value">
                {formatDate(offer.expiresAt)}
              </span>
            </div>
          </div>
        </div>
        
        <div className="offer-detail-section">
          <h2>Description</h2>
          <p className="offer-description-full">{offer.description}</p>
          
          <div className="offer-tags">
            {offer.tags.map(tag => (
              <span key={tag} className="offer-tag">#{tag}</span>
            ))}
          </div>
        </div>
        
        <div className="offer-detail-section">
          <h2>Data Requested</h2>
          
          <div className="data-requests-list">
            {offer.dataRequests.map((request, index) => (
              <div key={index} className="data-request-item">
                <div className="data-request-header">
                  <DataCategoryBadge category={request.category} />
                  {request.required ? (
                    <span className="required-badge">Required</span>
                  ) : (
                    <span className="optional-badge">Optional</span>
                  )}
                </div>
                
                <p className="data-request-description">
                  {request.description}
                </p>
                
                <AccessLevelIndicator level={request.accessLevel} />
              </div>
            ))}
          </div>
        </div>
      </div>
      
      <div className="offer-detail-actions">
        <button 
          className="secondary-button"
          onClick={handleRejectOffer}
        >
          Reject Offer
        </button>
        <button 
          className="primary-button"
          onClick={handleAcceptOffer}
        >
          Accept Offer
        </button>
      </div>
      
      {/* Accept Confirmation Dialog */}
      <Dialog 
        isOpen={isAcceptDialogOpen}
        onClose={handleCloseDialog}
        title="Accept Offer"
      >
        <div className="accept-dialog-content">
          <p>
            You're about to accept the following offer:
          </p>
          <h3>{offer.title}</h3>
          <p>
            <strong>Payout:</strong> {formatCurrency(offer.payout.amount, offer.payout.currency)}
          </p>
          <p>
            <strong>Duration:</strong> {formatDuration(offer.duration.value, offer.duration.unit)}
          </p>
          <p>
            <strong>Data Categories:</strong> {offer.dataRequests.map(req => 
              req.category.charAt(0).toUpperCase() + req.category.slice(1)
            ).join(', ')}
          </p>
          <p>
            Are you sure you want to proceed?
          </p>
          
          <div className="dialog-actions">
            <button 
              className="secondary-button"
              onClick={handleCloseDialog}
              disabled={acceptInProgress}
            >
              Cancel
            </button>
            <button 
              className="primary-button"
              onClick={handleConfirmAccept}
              disabled={acceptInProgress}
            >
              {acceptInProgress ? 'Processing...' : 'Confirm'}
            </button>
          </div>
        </div>
      </Dialog>
    </div>
  );
};

export default OfferDetail; 