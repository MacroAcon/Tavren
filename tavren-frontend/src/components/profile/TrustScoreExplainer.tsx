import React, { useState, useEffect } from 'react';
import apiClient from '../../utils/apiClient';
import './profile.css';

interface TrustScore {
  overall_score: number;
  data_quality_score: number;
  participation_score: number;
  consistency_score: number;
  factors: Record<string, number>;
  last_updated: string;
}

const TrustScoreExplainer: React.FC = () => {
  const [trustScore, setTrustScore] = useState<TrustScore | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTrustScore = async () => {
      try {
        setLoading(true);
        const data = await apiClient.get<TrustScore>('/user/trust-score');
        setTrustScore(data);
        setError(null);
      } catch (err) {
        setError('Failed to load trust score data');
        console.error('Error loading trust score:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchTrustScore();
  }, []);

  // Helper function to convert decimal score to percentage
  const formatScore = (score: number): string => {
    return `${Math.round(score * 100)}%`;
  };

  // Helper function to get CSS class based on score value
  const getScoreClass = (score: number): string => {
    if (score >= 0.85) return 'score-high';
    if (score >= 0.70) return 'score-medium';
    return 'score-low';
  };

  const factorLabels: Record<string, string> = {
    'consent_compliance': 'Consent Compliance',
    'data_freshness': 'Data Freshness',
    'response_rate': 'Response Rate',
    'verification_level': 'Verification Level',
    'review_accuracy': 'Review Accuracy'
  };

  if (loading && !trustScore) {
    return <div className="profile-loading">Loading trust score data...</div>;
  }

  if (error && !trustScore) {
    return <div className="profile-error">Error: {error}</div>;
  }

  if (!trustScore) {
    return <div className="profile-error">Trust score data not available</div>;
  }

  return (
    <div className="profile-section">
      <h2>Your Trust Score</h2>
      
      <div className="trust-score-container">
        <div className="score-overview">
          <div className="main-score">
            <div className={`score-circle ${getScoreClass(trustScore.overall_score)}`}>
              <span className="score-value">{formatScore(trustScore.overall_score)}</span>
            </div>
            <span className="score-label">Overall Trust</span>
          </div>
          
          <div className="score-components">
            <div className="score-component">
              <span className={`component-value ${getScoreClass(trustScore.data_quality_score)}`}>
                {formatScore(trustScore.data_quality_score)}
              </span>
              <span className="component-label">Data Quality</span>
            </div>
            
            <div className="score-component">
              <span className={`component-value ${getScoreClass(trustScore.participation_score)}`}>
                {formatScore(trustScore.participation_score)}
              </span>
              <span className="component-label">Participation</span>
            </div>
            
            <div className="score-component">
              <span className={`component-value ${getScoreClass(trustScore.consistency_score)}`}>
                {formatScore(trustScore.consistency_score)}
              </span>
              <span className="component-label">Consistency</span>
            </div>
          </div>
        </div>
        
        <div className="score-details">
          <h3>Factors Affecting Your Score</h3>
          
          <div className="factors-list">
            {Object.entries(trustScore.factors).map(([key, value]) => (
              <div key={key} className="factor-item">
                <div className="factor-info">
                  <span className="factor-name">{factorLabels[key] || key}</span>
                  <span className={`factor-score ${getScoreClass(value)}`}>
                    {formatScore(value)}
                  </span>
                </div>
                <div className="factor-bar-container">
                  <div 
                    className={`factor-bar ${getScoreClass(value)}`} 
                    style={{ width: `${value * 100}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
          
          <div className="score-info">
            <p>
              <strong>Last updated:</strong> {new Date(trustScore.last_updated).toLocaleDateString()}
            </p>
            <p className="score-explainer">
              Your trust score affects data request prioritization and compensation rates.
              Higher scores lead to more valuable partnership opportunities.
            </p>
          </div>
          
          <h3>How to Improve Your Score</h3>
          <ul className="improvement-tips">
            <li>Maintain consistent data sharing patterns</li>
            <li>Respond promptly to data requests</li>
            <li>Complete your profile verification</li>
            <li>Provide high-quality, accurate data</li>
            <li>Regularly review and update your sharing preferences</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default TrustScoreExplainer; 