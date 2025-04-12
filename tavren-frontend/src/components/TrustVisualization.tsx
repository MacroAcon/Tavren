import React, { useState, useEffect } from 'react';
import './trust-visualization.css';

// Define TypeScript interfaces
interface TrustData {
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

interface BuyerSummaryStats {
  totalBuyers: number;
  highTrustCount: number;
  standardTrustCount: number;
  lowTrustCount: number;
  averageTrustScore: number;
}

interface TrustVisualizationProps {
  userId: string;
}

const TrustVisualization: React.FC<TrustVisualizationProps> = ({ userId }) => {
  const [trustData, setTrustData] = useState<TrustData[]>([]);
  const [summaryStats, setSummaryStats] = useState<BuyerSummaryStats | null>(null);
  const [selectedBuyer, setSelectedBuyer] = useState<TrustData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch trust data from the API
  useEffect(() => {
    const fetchTrustData = async () => {
      try {
        setLoading(true);
        // In a real implementation, replace with actual API endpoint
        const response = await fetch(`/api/dashboard/buyer-trust?userId=${userId}`);
        
        if (!response.ok) {
          throw new Error('Failed to fetch trust data');
        }
        
        const data = await response.json();
        setTrustData(data.buyers);
        setSummaryStats(data.summary);
        setError(null);
      } catch (err) {
        setError('Error loading trust data. Please try again.');
        console.error('Error fetching trust data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchTrustData();
  }, [userId]);

  // Get color for trust score
  const getTrustScoreColor = (score: number): string => {
    if (score >= 85) return '#4caf50'; // High - green
    if (score >= 70) return '#2196f3'; // Standard - blue
    if (score >= 50) return '#ff9800'; // Caution - orange
    return '#f44336'; // Low - red
  };

  // Get description for trust tier
  const getTrustTierDescription = (tier: string): string => {
    switch (tier.toLowerCase()) {
      case 'high':
        return 'Data buyers in this tier have demonstrated exceptional compliance with privacy standards and responsible data use. They follow strict data handling protocols and have a strong history of respecting user consent choices.';
      case 'standard':
        return 'Data buyers in this tier meet expected industry standards for data handling and privacy. They have a good track record but occasionally may have minor compliance issues or user feedback concerns.';
      case 'low':
        return 'Data buyers in this tier have significant issues with data handling practices or have repeatedly received negative user feedback. Exercise caution when sharing data with these buyers.';
      default:
        return 'Trust tier information not available.';
    }
  };

  // Get icon for trust tier
  const getTrustTierIcon = (tier: string): string => {
    switch (tier.toLowerCase()) {
      case 'high':
        return '🛡️';
      case 'standard':
        return '✓';
      case 'low':
        return '⚠️';
      default:
        return '❓';
    }
  };

  // Handle buyer selection
  const handleSelectBuyer = (buyer: TrustData) => {
    setSelectedBuyer(buyer);
  };

  // Format percentage
  const formatPercentage = (value: number): string => {
    return `${Math.round(value)}%`;
  };

  // Render the trust tier explanation
  const renderTrustTierExplanation = () => {
    return (
      <div className="trust-tier-explanation">
        <h3>Understanding Trust Tiers</h3>
        
        <div className="trust-tiers">
          <div className="trust-tier high">
            <div className="tier-header">
              <span className="tier-icon">🛡️</span>
              <h4>High Trust</h4>
            </div>
            <p className="tier-score">Trust Score: 85-100</p>
            <div className="tier-details">
              <p>The highest level of trust, indicating:</p>
              <ul>
                <li>Excellent compliance with data use policies</li>
                <li>Robust data security measures</li>
                <li>Transparent data practices</li>
                <li>Strong history of respecting consent</li>
              </ul>
              <div className="privacy-implications">
                <p><strong>Privacy Implications:</strong> Minimal risk of data misuse. These buyers demonstrably handle your data with the highest care.</p>
              </div>
            </div>
          </div>
          
          <div className="trust-tier standard">
            <div className="tier-header">
              <span className="tier-icon">✓</span>
              <h4>Standard Trust</h4>
            </div>
            <p className="tier-score">Trust Score: 70-84</p>
            <div className="tier-details">
              <p>Meets baseline trust expectations, indicating:</p>
              <ul>
                <li>Good compliance with data policies</li>
                <li>Adequate security protocols</li>
                <li>Generally respects consent boundaries</li>
                <li>Occasional minor compliance issues</li>
              </ul>
              <div className="privacy-implications">
                <p><strong>Privacy Implications:</strong> Low to moderate risk. These buyers generally handle data responsibly but may have occasional issues.</p>
              </div>
            </div>
          </div>
          
          <div className="trust-tier low">
            <div className="tier-header">
              <span className="tier-icon">⚠️</span>
              <h4>Low Trust</h4>
            </div>
            <p className="tier-score">Trust Score: 0-69</p>
            <div className="tier-details">
              <p>Below expected trust standards, indicating:</p>
              <ul>
                <li>History of policy violations</li>
                <li>Questionable data handling practices</li>
                <li>Multiple user complaints</li>
                <li>Limited transparency</li>
              </ul>
              <div className="privacy-implications">
                <p><strong>Privacy Implications:</strong> Higher risk of data misuse. Exercise caution when sharing data with these buyers.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Render the trust summary
  const renderTrustSummary = () => {
    if (!summaryStats) return null;
    
    return (
      <div className="trust-summary">
        <h3>Buyer Trust Overview</h3>
        
        <div className="summary-stats">
          <div className="summary-stat">
            <span className="stat-value">{summaryStats.totalBuyers}</span>
            <span className="stat-label">Total Data Buyers</span>
          </div>
          
          <div className="summary-stat high">
            <span className="stat-value">{summaryStats.highTrustCount}</span>
            <span className="stat-label">High Trust</span>
          </div>
          
          <div className="summary-stat standard">
            <span className="stat-value">{summaryStats.standardTrustCount}</span>
            <span className="stat-label">Standard Trust</span>
          </div>
          
          <div className="summary-stat low">
            <span className="stat-value">{summaryStats.lowTrustCount}</span>
            <span className="stat-label">Low Trust</span>
          </div>
        </div>
        
        <div className="average-trust">
          <div className="trust-meter">
            <div className="trust-meter-label">Average Trust Score</div>
            <div className="trust-meter-bar">
              <div 
                className="trust-meter-fill" 
                style={{ 
                  width: `${summaryStats.averageTrustScore}%`,
                  backgroundColor: getTrustScoreColor(summaryStats.averageTrustScore)
                }}
              ></div>
            </div>
            <div className="trust-meter-value">{Math.round(summaryStats.averageTrustScore)}</div>
          </div>
        </div>
      </div>
    );
  };

  // Render the buyer list
  const renderBuyerList = () => {
    if (trustData.length === 0) {
      return (
        <div className="no-buyers">
          <p>No data buyers found.</p>
        </div>
      );
    }

    return (
      <div className="buyer-list">
        <h3>Data Buyers</h3>
        
        <div className="buyer-items">
          {trustData.map(buyer => (
            <div 
              key={buyer.buyerId}
              className={`buyer-item ${selectedBuyer?.buyerId === buyer.buyerId ? 'selected' : ''} ${buyer.trustTier.toLowerCase()}`}
              onClick={() => handleSelectBuyer(buyer)}
            >
              <div className="buyer-header">
                <span className="trust-icon">{getTrustTierIcon(buyer.trustTier)}</span>
                <span className="buyer-name">{buyer.buyerName}</span>
              </div>
              
              <div className="trust-score-container">
                <div className="trust-score-bar">
                  <div 
                    className="trust-score-fill" 
                    style={{ 
                      width: `${buyer.trustScore}%`,
                      backgroundColor: getTrustScoreColor(buyer.trustScore)
                    }}
                  ></div>
                </div>
                <div className="trust-score-value">{Math.round(buyer.trustScore)}</div>
              </div>
              
              <div className="buyer-tier">
                {buyer.trustTier} Trust
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Render the buyer details
  const renderBuyerDetails = () => {
    if (!selectedBuyer) {
      return (
        <div className="select-buyer-prompt">
          <p>Select a data buyer to view details</p>
        </div>
      );
    }

    const totalDeclines = Object.values(selectedBuyer.reasonStats).reduce((a, b) => a + b, 0);
    
    return (
      <div className="buyer-details">
        <h3>{selectedBuyer.buyerName}</h3>
        
        <div className="detail-section">
          <h4>Trust Rating</h4>
          
          <div className="trust-score-detail">
            <div className="score-label">Trust Score:</div>
            <div className="score-meter">
              <div 
                className="score-fill" 
                style={{ 
                  width: `${selectedBuyer.trustScore}%`,
                  backgroundColor: getTrustScoreColor(selectedBuyer.trustScore)
                }}
              ></div>
            </div>
            <div className="score-value">{Math.round(selectedBuyer.trustScore)}</div>
          </div>
          
          <div className="trust-badge-container">
            <div className={`trust-badge ${selectedBuyer.trustTier.toLowerCase()}`}>
              {selectedBuyer.trustTier} Trust
            </div>
            <p className="trust-description">
              {getTrustTierDescription(selectedBuyer.trustTier)}
            </p>
          </div>
        </div>
        
        <div className="detail-section">
          <h4>Performance Metrics</h4>
          
          <div className="metric-row">
            <div className="metric-label">Privacy Grade:</div>
            <div className={`metric-value grade-${selectedBuyer.privacyGrade.toLowerCase()}`}>
              {selectedBuyer.privacyGrade}
            </div>
          </div>
          
          <div className="metric-row">
            <div className="metric-label">Data Use Compliance:</div>
            <div className="metric-meter">
              <div className="meter-track">
                <div 
                  className="meter-fill" 
                  style={{ width: formatPercentage(selectedBuyer.dataUseCompliance) }}
                ></div>
              </div>
              <div className="meter-value">{formatPercentage(selectedBuyer.dataUseCompliance)}</div>
            </div>
          </div>
          
          <div className="metric-row">
            <div className="metric-label">Data Retention:</div>
            <div className="metric-meter">
              <div className="meter-track">
                <div 
                  className="meter-fill" 
                  style={{ width: formatPercentage(selectedBuyer.dataRetentionScore) }}
                ></div>
              </div>
              <div className="meter-value">{formatPercentage(selectedBuyer.dataRetentionScore)}</div>
            </div>
          </div>
          
          <div className="metric-row">
            <div className="metric-label">Consent Adherence:</div>
            <div className="metric-meter">
              <div className="meter-track">
                <div 
                  className="meter-fill" 
                  style={{ width: formatPercentage(selectedBuyer.consentFollowScore) }}
                ></div>
              </div>
              <div className="meter-value">{formatPercentage(selectedBuyer.consentFollowScore)}</div>
            </div>
          </div>
        </div>
        
        <div className="detail-section">
          <h4>User Feedback</h4>
          
          <div className="feedback-summary">
            <div className="decline-stat">
              <div className="decline-count">{selectedBuyer.declineCount}</div>
              <div className="decline-label">Declined Requests</div>
            </div>
            
            <div className="interaction-rate">
              <div className="rate-label">Decline Rate:</div>
              <div className="rate-value">
                {formatPercentage(selectedBuyer.declineCount / selectedBuyer.totalInteractions * 100)}
              </div>
            </div>
          </div>
          
          {totalDeclines > 0 && (
            <div className="decline-reasons">
              <h5>Reasons for Declining</h5>
              
              <div className="reason-bars">
                {Object.entries(selectedBuyer.reasonStats).map(([reason, count]) => {
                  const percentage = (count / totalDeclines) * 100;
                  if (percentage === 0) return null;
                  
                  return (
                    <div key={reason} className="reason-bar-container">
                      <div className="reason-label">{reason}:</div>
                      <div className="reason-bar">
                        <div 
                          className={`reason-fill ${reason}`}
                          style={{ width: `${percentage}%` }}
                        ></div>
                      </div>
                      <div className="reason-percentage">{formatPercentage(percentage)}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  if (loading) {
    return <div className="trust-visualization loading">Loading trust data...</div>;
  }

  if (error) {
    return <div className="trust-visualization error">{error}</div>;
  }

  return (
    <div className="trust-visualization">
      <h2>Data Buyer Trust</h2>
      
      {renderTrustSummary()}
      
      <div className="trust-container">
        <div className="buyers-panel">
          {renderBuyerList()}
        </div>
        
        <div className="details-panel">
          {renderBuyerDetails()}
        </div>
      </div>
      
      {renderTrustTierExplanation()}
    </div>
  );
};

export default TrustVisualization; 