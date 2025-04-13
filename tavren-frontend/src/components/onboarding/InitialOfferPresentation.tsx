import React, { useState } from 'react';

interface InitialOfferPresentationProps {
  onComplete: () => void;
}

// Mock offer data
const mockOffer = {
  id: 'offer-123',
  title: 'App Usage Insights',
  description: 'Share 3 days of anonymized app usage data to help improve mobile experiences.',
  compensation: 0.75,
  duration: '3 days',
  dataCategories: [
    { name: 'App Usage Patterns', description: 'Which apps you use and for how long' },
    { name: 'App Launch Frequency', description: 'How often you open specific applications' },
    { name: 'Time of Day Usage', description: 'When during the day you use different apps' }
  ],
  privacyImpact: 'low',
  buyer: {
    name: 'AppInsights Research',
    trustScore: 4.2,
    transactions: 15420,
    description: 'Market research firm specializing in mobile user experience optimization'
  }
};

const InitialOfferPresentation: React.FC<InitialOfferPresentationProps> = ({ onComplete }) => {
  const [expanded, setExpanded] = useState<string | null>(null);
  const [offerAccepted, setOfferAccepted] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  
  const toggleExpand = (section: string) => {
    if (expanded === section) {
      setExpanded(null);
    } else {
      setExpanded(section);
    }
  };
  
  const handleAccept = () => {
    setOfferAccepted(true);
    setShowConfirmation(true);
    // In a real implementation, you would send this acceptance to your API
  };
  
  const handleComplete = () => {
    onComplete();
  };
  
  return (
    <div className="onboarding-container offer-presentation">
      <div className="offer-content">
        {!showConfirmation ? (
          <>
            <div className="offer-header">
              <h1>Your First Data Opportunity</h1>
              <p className="offer-subtext">
                Here's a chance to earn from your data while maintaining your privacy.
              </p>
            </div>
            
            <div className="offer-card">
              <div className="offer-title-row">
                <h2>{mockOffer.title}</h2>
                <div className="offer-value">${mockOffer.compensation.toFixed(2)}</div>
              </div>
              
              <p className="offer-description">{mockOffer.description}</p>
              
              <div className="offer-details">
                <div className="offer-detail">
                  <span className="detail-label">Duration:</span>
                  <span className="detail-value">{mockOffer.duration}</span>
                </div>
                <div className="offer-detail">
                  <span className="detail-label">Privacy Impact:</span>
                  <span className={`detail-value privacy-${mockOffer.privacyImpact}`}>
                    {mockOffer.privacyImpact.toUpperCase()}
                  </span>
                </div>
              </div>
              
              <div className="collapsible-section">
                <div 
                  className="section-header"
                  onClick={() => toggleExpand('data')}
                >
                  <h3>Data Requested</h3>
                  <span className={`expand-icon ${expanded === 'data' ? 'expanded' : ''}`}>▼</span>
                </div>
                
                {expanded === 'data' && (
                  <div className="section-content">
                    <ul className="data-list">
                      {mockOffer.dataCategories.map((category, index) => (
                        <li key={index} className="data-item">
                          <span className="data-name">{category.name}</span>
                          <span className="data-description">{category.description}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
              
              <div className="collapsible-section">
                <div 
                  className="section-header"
                  onClick={() => toggleExpand('buyer')}
                >
                  <h3>About the Buyer</h3>
                  <span className={`expand-icon ${expanded === 'buyer' ? 'expanded' : ''}`}>▼</span>
                </div>
                
                {expanded === 'buyer' && (
                  <div className="section-content">
                    <div className="buyer-info">
                      <div className="buyer-header">
                        <h4>{mockOffer.buyer.name}</h4>
                        <div className="trust-score">
                          <span className="score-value">{mockOffer.buyer.trustScore}</span>/5
                        </div>
                      </div>
                      <p className="buyer-description">{mockOffer.buyer.description}</p>
                      <div className="transaction-count">
                        {mockOffer.buyer.transactions.toLocaleString()} successful transactions
                      </div>
                    </div>
                  </div>
                )}
              </div>
              
              <div className="offer-controls">
                <button 
                  className="secondary-button"
                  onClick={() => onComplete()}
                >
                  Skip for Now
                </button>
                <button 
                  className="primary-button accept-button"
                  onClick={handleAccept}
                >
                  Accept Offer
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="confirmation-screen">
            <div className="confirmation-icon">✓</div>
            <h1>Offer Accepted!</h1>
            <p className="confirmation-message">
              You've just started your journey to taking control of your data and getting 
              compensated for it. We'll begin collecting the agreed-upon data for the next 3 days.
            </p>
            <div className="earnings-summary">
              <h3>Your Earnings</h3>
              <div className="earnings-value">${mockOffer.compensation.toFixed(2)}</div>
              <p>Will be added to your wallet after the collection period</p>
            </div>
            <button 
              className="primary-button"
              onClick={handleComplete}
            >
              Continue to Dashboard
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default InitialOfferPresentation; 