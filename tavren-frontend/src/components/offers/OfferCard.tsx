import React from 'react';
import { Offer, DataAccessLevel } from '../../types/offers';
import Card from '../shared/Card';

interface OfferCardProps {
  offer: Offer;
  onViewDetails: (offer: Offer) => void;
  onAccept: (offer: Offer) => void;
}

// Helper functions
const formatCurrency = (amount: number, currency: string) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2
  }).format(amount);
};

const formatDuration = (value: number, unit: string) => {
  return `${value} ${unit}${value !== 1 ? 's' : ''}`;
};

const OfferCard: React.FC<OfferCardProps> = ({ offer, onViewDetails, onAccept }) => {
  // Determine badge colors based on offer type
  const getBadgeClass = () => {
    switch (offer.type) {
      case 'one_time':
        return 'one_time';
      case 'subscription':
        return 'subscription';
      case 'limited':
        return 'limited';
      default:
        return '';
    }
  };

  // Determine data access badge color based on risk level
  const getDataAccessClass = () => {
    // Calculate a risk level based on the data categories and access levels
    const dataImpact = calculateDataImpact(offer);
    switch (dataImpact) {
      case 'low':
        return 'green';
      case 'medium':
        return 'blue';
      case 'high':
        return 'orange';
      case 'critical':
        return 'red';
      default:
        return 'blue';
    }
  };

  // Calculate a data impact/risk level based on the data requests
  const calculateDataImpact = (offer: Offer): 'low' | 'medium' | 'high' | 'critical' => {
    // Check for sensitive data categories
    const hasMedical = offer.dataRequests.some(req => req.category === 'medical');
    const hasFinancial = offer.dataRequests.some(req => req.category === 'financial');
    const hasLocation = offer.dataRequests.some(req => req.category === 'location');
    
    // Check for comprehensive or full access levels
    const hasFullAccess = offer.dataRequests.some(
      req => req.accessLevel === 'comprehensive' || req.accessLevel === 'full'
    );
    
    if ((hasMedical || hasFinancial) && hasFullAccess) {
      return 'critical';
    } else if (hasMedical || hasFinancial || (hasLocation && hasFullAccess)) {
      return 'high';
    } else if (hasLocation || hasFullAccess) {
      return 'medium';
    } else {
      return 'low';
    }
  };

  // Determine trust badge class based on buyer's trust tier
  const getTrustClass = () => {
    const trustTier = offer.buyer.trustTier || 3; // Default to middle trust tier
    if (trustTier >= 4) {
      return 'trust-green';
    } else if (trustTier >= 2) {
      return 'trust-orange';
    } else {
      return 'trust-red';
    }
  };

  // Handle touch feedback for mobile
  const handleCardPress = () => {
    onViewDetails(offer);
  };

  return (
    <Card className="offer-card">
      <div className="offer-card-header">
        <div className="offer-badges">
          <span className={`offer-type-badge ${getBadgeClass()}`}>
            {offer.type === 'one_time' ? 'One-time' : 
             offer.type === 'subscription' ? 'Subscription' : 'Limited Time'}
          </span>
          <span className={`data-access-badge ${getDataAccessClass()}`}>
            {calculateDataImpact(offer).charAt(0).toUpperCase() + calculateDataImpact(offer).slice(1)} Impact
          </span>
        </div>
        
        <h2>{offer.title}</h2>
        
        <div className="offer-buyer">
          <img 
            src={offer.buyer.logo || '/placeholder-logo.svg'} 
            alt={`${offer.buyer.name} logo`}
            className="buyer-logo"
          />
          <span className="buyer-name">{offer.buyer.name}</span>
          <span className={`trust-badge ${getTrustClass()}`}>
            {offer.buyer.trustTier >= 4 ? 'High' : 
             offer.buyer.trustTier >= 2 ? 'Medium' : 'Low'} Trust
          </span>
        </div>
      </div>
      
      <div className="offer-card-body">
        <p className="offer-description">{offer.description}</p>
        
        <div className="offer-details">
          <div className="detail-item">
            <span className="detail-label">Payout:</span>
            <span className="detail-value payout-amount">
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
            <span className="detail-label">Data Access:</span>
            <span className="detail-value">
              {offer.dataRequests.length} data categories
            </span>
          </div>
        </div>
        
        <div className="offer-tags">
          {offer.tags.map(tag => (
            <span key={tag} className="offer-tag">#{tag}</span>
          ))}
        </div>
        
        {offer.matchScore !== undefined && (
          <div className="match-score">
            <div className="match-score-bar">
              <div 
                className="match-score-fill" 
                style={{ width: `${offer.matchScore}%` }}
              ></div>
            </div>
            <span>{offer.matchScore}% Match</span>
          </div>
        )}
      </div>
      
      <div className="offer-card-actions">
        <button className="secondary-button" onClick={() => onViewDetails(offer)}>
          View Details
        </button>
        <button className="primary-button" onClick={() => onAccept(offer)}>
          Accept Offer
        </button>
      </div>
    </Card>
  );
};

export default OfferCard; 