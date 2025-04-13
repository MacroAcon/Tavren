import React, { useState, useEffect } from 'react';
import apiClient from '../../utils/apiClient';
import './profile.css';

interface CompensationBreakdown {
  base_rate: number;
  quality_multiplier: number;
  participation_bonus: number;
  total_rate: number;
  estimated_monthly: number;
  historical_average: number;
}

const CompensationModel: React.FC = () => {
  const [compensation, setCompensation] = useState<CompensationBreakdown | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCompensationData = async () => {
      try {
        setLoading(true);
        const data = await apiClient.get<CompensationBreakdown>('/user/compensation-breakdown');
        setCompensation(data);
        setError(null);
      } catch (err) {
        setError('Failed to load compensation data');
        console.error('Error loading compensation data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchCompensationData();
  }, []);

  // Helper function to format currency values
  const formatCurrency = (value: number): string => {
    return `$${value.toFixed(2)}`;
  };

  // Helper function to format percentage values
  const formatPercentage = (value: number): string => {
    return `${Math.round((value - 1) * 100)}%`;
  };

  if (loading && !compensation) {
    return <div className="profile-loading">Loading compensation data...</div>;
  }

  if (error && !compensation) {
    return <div className="profile-error">Error: {error}</div>;
  }

  if (!compensation) {
    return <div className="profile-error">Compensation data not available</div>;
  }

  return (
    <div className="profile-section">
      <h2>Your Compensation Model</h2>
      
      <div className="compensation-container">
        <div className="compensation-summary">
          <div className="compensation-card">
            <h3>Effective Rate</h3>
            <div className="rate-value">{formatCurrency(compensation.total_rate)}</div>
            <div className="rate-label">per validated data point</div>
          </div>
          
          <div className="compensation-card">
            <h3>Estimated Monthly</h3>
            <div className="rate-value">{formatCurrency(compensation.estimated_monthly)}</div>
            <div className="rate-label">based on current activity</div>
          </div>
          
          <div className="compensation-card">
            <h3>Historical Average</h3>
            <div className="rate-value">{formatCurrency(compensation.historical_average)}</div>
            <div className="rate-label">3-month average</div>
          </div>
        </div>
        
        <div className="compensation-breakdown">
          <h3>How Your Rate Is Calculated</h3>
          
          <div className="calculation-table">
            <div className="calculation-row">
              <div className="calc-label">Base Rate</div>
              <div className="calc-value">{formatCurrency(compensation.base_rate)}</div>
              <div className="calc-description">
                Standard payment per data point
              </div>
            </div>
            
            <div className="calculation-row">
              <div className="calc-label">Quality Bonus</div>
              <div className="calc-value">+{formatPercentage(compensation.quality_multiplier)}</div>
              <div className="calc-description">
                Based on your data quality score
              </div>
            </div>
            
            <div className="calculation-row">
              <div className="calc-label">Participation Bonus</div>
              <div className="calc-value">+{formatCurrency(compensation.participation_bonus)}</div>
              <div className="calc-description">
                Reward for consistent participation
              </div>
            </div>
            
            <div className="calculation-row total-row">
              <div className="calc-label">Total Rate</div>
              <div className="calc-value">{formatCurrency(compensation.total_rate)}</div>
              <div className="calc-description">
                Your effective payment rate
              </div>
            </div>
          </div>
          
          <div className="compensation-info">
            <h3>Maximize Your Earnings</h3>
            <ul className="compensation-tips">
              <li>
                <strong>Improve data quality</strong> - Provide accurate, complete information
              </li>
              <li>
                <strong>Participate consistently</strong> - Regular engagement increases your bonus rate
              </li>
              <li>
                <strong>Complete verification</strong> - Verified accounts earn higher base rates
              </li>
              <li>
                <strong>Set detailed preferences</strong> - More specific consent settings lead to better matching
              </li>
              <li>
                <strong>Respond promptly</strong> - Quick responses to data requests improve your participation score
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CompensationModel; 