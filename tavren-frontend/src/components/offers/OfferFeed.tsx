import React, { useEffect, useRef, useCallback } from 'react';
import { useOfferStore } from '../../stores';
import { Offer, OfferType, DataAccessLevel } from '../../types/offers';
import { Card, LoadingState, ErrorState, EmptyState } from '../shared';
import { useApiWithErrorHandling } from '../../utils/errorHandling';
import './offers.css';

// Helper function to format currency
const formatCurrency = (amount: number, currency: string = 'USD') => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  }).format(amount);
};

// Helper to format duration
const formatDuration = (value: number, unit: string) => {
  return `${value} ${value === 1 ? unit.slice(0, -1) : unit}`;
};

// Trust tier badge
const TrustTierBadge: React.FC<{ tier: number }> = ({ tier }) => {
  let color = 'green';
  if (tier < 3) color = 'red';
  else if (tier < 5) color = 'orange';
  
  return (
    <span className={`trust-badge trust-tier-${tier} trust-${color}`}>
      Trust Tier {tier}
    </span>
  );
};

// Offer type badge
const OfferTypeBadge: React.FC<{ type: OfferType }> = ({ type }) => {
  const displayText = {
    [OfferType.OneTime]: 'One-time',
    [OfferType.Subscription]: 'Subscription',
    [OfferType.Limited]: 'Limited Time'
  };
  
  return (
    <span className={`offer-type-badge ${type}`}>
      {displayText[type]}
    </span>
  );
};

// Data access badge
const DataAccessBadge: React.FC<{ level: DataAccessLevel }> = ({ level }) => {
  const displayText = {
    [DataAccessLevel.Basic]: 'Basic',
    [DataAccessLevel.Extended]: 'Extended',
    [DataAccessLevel.Comprehensive]: 'Comprehensive',
    [DataAccessLevel.Full]: 'Full Access'
  };
  
  const color = {
    [DataAccessLevel.Basic]: 'green',
    [DataAccessLevel.Extended]: 'blue',
    [DataAccessLevel.Comprehensive]: 'orange',
    [DataAccessLevel.Full]: 'red'
  };
  
  return (
    <span className={`data-access-badge ${color[level]}`}>
      {displayText[level]}
    </span>
  );
};

// Offer Card component
const OfferCard: React.FC<{ 
  offer: Offer;
  onViewDetails: (offer: Offer) => void;
  onAccept: (offer: Offer) => void;
}> = ({ offer, onViewDetails, onAccept }) => {
  // Get the highest access level requested
  const highestAccessLevel = offer.dataRequests.reduce((highest, request) => {
    const accessLevels = [
      DataAccessLevel.Basic,
      DataAccessLevel.Extended, 
      DataAccessLevel.Comprehensive,
      DataAccessLevel.Full
    ];
    const highestIndex = accessLevels.indexOf(highest);
    const currentIndex = accessLevels.indexOf(request.accessLevel);
    return currentIndex > highestIndex ? request.accessLevel : highest;
  }, DataAccessLevel.Basic);

  return (
    <Card className="offer-card">
      <div className="offer-card-header">
        <div className="offer-badges">
          <OfferTypeBadge type={offer.type} />
          <DataAccessBadge level={highestAccessLevel} />
        </div>
        <h2>{offer.title}</h2>
        <div className="offer-buyer">
          {offer.buyer.logo && (
            <img 
              src={offer.buyer.logo} 
              alt={`${offer.buyer.name} logo`} 
              className="buyer-logo" 
            />
          )}
          <span className="buyer-name">{offer.buyer.name}</span>
          <TrustTierBadge tier={offer.buyer.trustTier} />
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

// Main OfferFeed component
const OfferFeed: React.FC = () => {
  const { 
    offers, 
    loading, 
    error, 
    hasMore,
    fetchOffers,
    nextPage,
    setSelectedOffer 
  } = useOfferStore();
  
  const { callApi } = useApiWithErrorHandling();
  
  // Reference to the sentinel element for infinite scrolling
  const observerRef = useRef<IntersectionObserver | null>(null);
  const sentinelRef = useRef<HTMLDivElement>(null);
  
  // Handle view details click
  const handleViewDetails = useCallback((offer: Offer) => {
    setSelectedOffer(offer);
    window.location.href = `/offers/${offer.id}`;
  }, [setSelectedOffer]);
  
  // Handle accept offer click
  const handleAcceptOffer = useCallback(async (offer: Offer) => {
    // Try to accept the offer with error handling
    const success = await callApi(
      () => useOfferStore.getState().acceptOffer(offer.id),
      'accepting offer',
      { retries: 1 }
    );
    
    if (success) {
      // Navigate to offer details with accept mode
      window.location.href = `/offers/${offer.id}?accept=true`;
    }
  }, [callApi]);
  
  // Handle refresh offers
  const handleRefreshOffers = useCallback(() => {
    fetchOffers(true); // Reset to page 1 and refetch
  }, [fetchOffers]);
  
  // Setup intersection observer for infinite scrolling
  useEffect(() => {
    // Fetch initial offers if none present
    if (offers.length === 0 && !loading && !error) {
      fetchOffers();
    }
    
    // Setup intersection observer for infinite scrolling
    if (sentinelRef.current) {
      observerRef.current = new IntersectionObserver(
        (entries) => {
          if (entries[0].isIntersecting && hasMore && !loading) {
            nextPage();
            fetchOffers();
          }
        },
        { threshold: 0.5 }
      );
      
      observerRef.current.observe(sentinelRef.current);
    }
    
    return () => {
      // Cleanup observer on unmount
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [fetchOffers, hasMore, loading, nextPage, offers.length, error]);
  
  // Handle error state
  if (error && offers.length === 0) {
    return <ErrorState 
      message={`Failed to load offers: ${error}`}
      onRetry={handleRefreshOffers}
    />;
  }
  
  return (
    <div className="offer-feed">
      {offers.length === 0 && !loading ? (
        <EmptyState
          title="No Offers Available"
          message="Try changing your filters or check back later for new offers."
          icon="🔍"
          actionLabel="Refresh Offers"
          onAction={handleRefreshOffers}
        />
      ) : (
        <>
          <div className="offer-grid">
            {offers.map(offer => (
              <OfferCard 
                key={offer.id}
                offer={offer}
                onViewDetails={handleViewDetails}
                onAccept={handleAcceptOffer}
              />
            ))}
          </div>
          
          {loading && <LoadingState message="Loading more offers..." />}
          
          {/* Sentinel element for infinite scrolling */}
          <div ref={sentinelRef} className="sentinel"></div>
        </>
      )}
    </div>
  );
};

export default OfferFeed; 