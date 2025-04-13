import React, { useState } from 'react';

interface ScanResultsProps {
  onContinue: () => void;
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

const ScanResults: React.FC<ScanResultsProps> = ({ onContinue }) => {
  const [activeTab, setActiveTab] = useState('summary');
  
  const renderRiskIndicator = (risk: string) => {
    const classes = `risk-indicator ${risk}`;
    return <span className={classes}>{risk}</span>;
  };
  
  return (
    <div className="onboarding-container scan-results">
      <div className="results-content">
        <h1 className="results-headline">Your Digital Footprint</h1>
        <p className="results-subtext">
          Here's what we found about your data exposure. 
          Your information is being collected across multiple channels.
        </p>
        
        <div className="tabs">
          <button 
            className={`tab ${activeTab === 'summary' ? 'active' : ''}`}
            onClick={() => setActiveTab('summary')}
          >
            Summary
          </button>
          <button 
            className={`tab ${activeTab === 'trackers' ? 'active' : ''}`}
            onClick={() => setActiveTab('trackers')}
          >
            Trackers
          </button>
          <button 
            className={`tab ${activeTab === 'apps' ? 'active' : ''}`}
            onClick={() => setActiveTab('apps')}
          >
            Apps
          </button>
          <button 
            className={`tab ${activeTab === 'data' ? 'active' : ''}`}
            onClick={() => setActiveTab('data')}
          >
            Data Types
          </button>
        </div>
        
        <div className="tab-content">
          {activeTab === 'summary' && (
            <div className="summary-panel">
              <div className="stats-grid">
                <div className="stat-card">
                  <h3>{mockScanData.trackers.count}</h3>
                  <p>Trackers Identified</p>
                </div>
                <div className="stat-card">
                  <h3>{mockScanData.apps.count}</h3>
                  <p>Apps Accessing Your Data</p>
                </div>
                <div className="stat-card">
                  <h3>{mockScanData.dataCategories.length}</h3>
                  <p>Data Categories Exposed</p>
                </div>
                <div className="stat-card">
                  <h3>$0</h3>
                  <p>Your Current Earnings</p>
                </div>
              </div>
              
              <p className="summary-message">
                Your data is valuable, but you've been giving it away for free.
                With Tavren, you can start earning from your digital footprint while 
                maintaining control over what you share.
              </p>
            </div>
          )}
          
          {activeTab === 'trackers' && (
            <div className="trackers-panel">
              <h3>Tracking Technologies Found: {mockScanData.trackers.count}</h3>
              <div className="category-list">
                {mockScanData.trackers.categories.map((category, index) => (
                  <div key={index} className="category-item">
                    <div className="category-name">{category.name}</div>
                    <div className="category-bar">
                      <div 
                        className="category-fill"
                        style={{ width: `${(category.count / mockScanData.trackers.count) * 100}%` }}
                      ></div>
                    </div>
                    <div className="category-count">{category.count}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {activeTab === 'apps' && (
            <div className="apps-panel">
              <h3>Apps Accessing Your Data: {mockScanData.apps.count}</h3>
              <div className="app-access-list">
                {mockScanData.apps.accessTypes.map((access, index) => (
                  <div key={index} className="app-access-item">
                    <div className="access-type">{access.type}</div>
                    <div className="access-details">
                      <span className="access-count">{access.count} apps</span>
                      <span className="access-frequency">{access.frequency}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {activeTab === 'data' && (
            <div className="data-panel">
              <h3>Your Exposed Data Categories</h3>
              <div className="data-table">
                <div className="data-table-header">
                  <div>Category</div>
                  <div>Privacy Risk</div>
                  <div>Market Value</div>
                </div>
                {mockScanData.dataCategories.map((category, index) => (
                  <div key={index} className="data-table-row">
                    <div>{category.name}</div>
                    <div>{renderRiskIndicator(category.risk)}</div>
                    <div>{renderRiskIndicator(category.value)}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
        
        <button className="primary-button" onClick={onContinue}>
          See Your First Offer
        </button>
      </div>
    </div>
  );
};

export default ScanResults; 