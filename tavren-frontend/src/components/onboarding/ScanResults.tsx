import React, { useEffect } from 'react';
import { useOnboardingStore } from '../../stores';
import { logConversionEvent, getStoredVariant } from '../../utils/analytics';

interface ScanResultsProps {
  onContinue: () => void;
  currentStep?: string;
}

// Mock data for the scan results
const mockScanData = {
  trackers: {
    count: 37,
    categories: [
      { name: 'Social Media', count: 12 },
      { name: 'Advertising', count: 15 },
      { name: 'Analytics', count: 7 },
      { name: 'Content Delivery', count: 3 }
    ]
  },
  apps: {
    count: 11,
    accessTypes: [
      { type: 'Location', count: 8, frequency: 'weekly' },
      { type: 'Contacts', count: 5, frequency: 'monthly' },
      { type: 'Photos', count: 6, frequency: 'daily' },
      { type: 'Microphone', count: 3, frequency: 'rarely' }
    ]
  },
  dataCategories: [
    { name: 'Personal Identifiers', risk: 'high', value: 'high' },
    { name: 'Location History', risk: 'medium', value: 'high' },
    { name: 'Browsing History', risk: 'medium', value: 'medium' },
    { name: 'Purchase History', risk: 'low', value: 'high' },
    { name: 'Social Connections', risk: 'medium', value: 'medium' }
  ]
};

const ScanResults: React.FC<ScanResultsProps> = ({ 
  onContinue,
  currentStep = 'results'
}) => {
  const scanResults = useOnboardingStore(state => state.scanResults);
  
  // Log when the results are viewed
  useEffect(() => {
    const variant = getStoredVariant('onboarding-value-proposition');
    if (variant) {
      logConversionEvent(variant, `${currentStep}_viewed`);
    }
  }, [currentStep]);
  
  // Default values if results aren't available
  const trackerCount = scanResults?.trackerCount || 32;
  const appCount = scanResults?.appCount || 8;
  const dataCategories = scanResults?.dataCategories || 4;
  
  const renderRiskIndicator = (risk: string) => {
    const classes = `risk-indicator ${risk}`;
    return <span className={classes}>{risk}</span>;
  };
  
  return (
    <div className="onboarding-container results-screen">
      <div className="results-content">
        <h1 className="headline">Your Digital Footprint</h1>
        
        <div className="results-summary">
          <div className="result-card">
            <span className="result-value">{trackerCount}</span>
            <span className="result-label">Trackers Active</span>
          </div>
          
          <div className="result-card">
            <span className="result-value">{appCount}</span>
            <span className="result-label">Connected Apps</span>
          </div>
          
          <div className="result-card">
            <span className="result-value">{dataCategories}</span>
            <span className="result-label">Data Categories</span>
          </div>
        </div>
        
        <div className="insights-container">
          <h2 className="insights-title">What This Means For You</h2>
          
          <div className="insight-item">
            <div className="insight-icon">
              <svg viewBox="0 0 24 24" width="24" height="24">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" 
                  fill="none" stroke="currentColor" strokeWidth="2" />
              </svg>
            </div>
            <div className="insight-content">
              <h3>Data Collection</h3>
              <p>Your personal data is being collected by {trackerCount} different services as you browse online.</p>
            </div>
          </div>
          
          <div className="insight-item">
            <div className="insight-icon">
              <svg viewBox="0 0 24 24" width="24" height="24">
                <path d="M12 22a10 10 0 100-20 10 10 0 000 20z" 
                  fill="none" stroke="currentColor" strokeWidth="2" />
                <path d="M12 8v4l3 3" 
                  fill="none" stroke="currentColor" strokeWidth="2" />
              </svg>
            </div>
            <div className="insight-content">
              <h3>Time Spent</h3>
              <p>You spend approximately 6 hours per day using digital services that collect and monetize your data.</p>
            </div>
          </div>
          
          <div className="insight-item">
            <div className="insight-icon">
              <svg viewBox="0 0 24 24" width="24" height="24">
                <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" 
                  fill="none" stroke="currentColor" strokeWidth="2" />
              </svg>
            </div>
            <div className="insight-content">
              <h3>Value Creation</h3>
              <p>Your data helps create an estimated $1,257 in value per year, while you receive $0 in return.</p>
            </div>
          </div>
        </div>
        
        <div className="cta-container">
          <p className="pre-cta-text">
            With Tavren, you can take control of your digital footprint and earn from the value you create online.
          </p>
          
          <button className="primary-button" onClick={onContinue}>
            See My First Earnings Opportunity
          </button>
        </div>
      </div>
    </div>
  );
};

export default ScanResults; 