import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useOfferStore, useAuthStore } from '../../stores';
import { Offer, OfferType } from '../../types/offers';
import { Card, LoadingState } from '../shared';
import './offers.css';

// Helper function to format currency (same as in other components)
const formatCurrency = (amount: number, currency: string = 'USD') => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  }).format(amount);
};

// Simplified offer card specifically for recommendations
const RecommendedOfferCard: React.FC<{ offer: Offer }> = ({ offer }) => {
  return (
    <Card className="recommended-offer-card">
      <div className="recommendation-header">
        <h3>{offer.title}</h3>
        <div className="match-score">
          <div className="match-score-bar">
            <div 
              className="match-score-fill" 
              style={{ width: `${offer.matchScore || 0}%` }}
            ></div>
          </div>
          <span>{offer.matchScore || 0}% Match</span>
        </div>
      </div>
      
      <div className="recommendation-body">
        <p className="recommendation-description">
          {offer.description.length > 120 
            ? `${offer.description.substring(0, 120)}...` 
            : offer.description
          }
        </p>
        
        <div className="recommendation-details">
          <div className="detail-item">
            <span className="detail-label">From:</span>
            <span className="detail-value">{offer.buyer.name}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Payout:</span>
            <span className="detail-value payout-amount">
              {formatCurrency(offer.payout.amount, offer.payout.currency)}
            </span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Type:</span>
            <span className="detail-value">
              {offer.type === OfferType.OneTime ? 'One-time' : 
               offer.type === OfferType.Subscription ? 'Subscription' : 'Limited'}
            </span>
          </div>
        </div>
      </div>
      
      <Link to={`/offers/${offer.id}`} className="recommendation-link">
        View Details
      </Link>
    </Card>
  );
};

// Main OfferRecommendations component
const OfferRecommendations: React.FC<{ 
  count?: number;
  title?: string;
  showViewAll?: boolean;
}> = ({ 
  count = 3, 
  title = "Recommended For You", 
  showViewAll = true 
}) => {
  const [recommendations, setRecommendations] = useState<Offer[]>([]);
  const [loading, setLoading] = useState(true);
  const { fetchRecommendedOffers } = useOfferStore();
  const user = useAuthStore(state => state.user);
  
  useEffect(() => {
    const loadRecommendations = async () => {
      setLoading(true);
      try {
        // Use username or a default id
        const userId = user?.username || 'default';
        const offers = await fetchRecommendedOffers(userId, count);
        setRecommendations(offers);
      } catch (error) {
        console.error('Failed to load recommendations:', error);
      } finally {
        setLoading(false);
      }
    };
    
    loadRecommendations();
  }, [count, fetchRecommendedOffers, user]);
  
  if (loading) {
    return <LoadingState />;
  }
  
  if (recommendations.length === 0) {
    return null; // Don't show anything if no recommendations
  }
  
  return (
    <div className="offer-recommendations">
      <div className="recommendations-header">
        <h2>{title}</h2>
        {showViewAll && (
          <Link to="/offers" className="view-all-link">
            View All Offers
          </Link>
        )}
      </div>
      
      <div className="recommendations-grid">
        {recommendations.map(offer => (
          <RecommendedOfferCard key={offer.id} offer={offer} />
        ))}
      </div>
    </div>
  );
};

export default OfferRecommendations; 