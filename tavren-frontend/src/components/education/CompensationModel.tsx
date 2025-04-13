import React, { useState } from 'react';
import './education.css';

interface CompensationFactor {
  id: string;
  name: string;
  description: string;
  example: string;
  impact: number; // Percentage impact on compensation
  icon: string;
}

interface DataCategory {
  id: string;
  name: string;
  baseValue: string;
  description: string;
  bonusFactors: string[];
}

const CompensationModel: React.FC = () => {
  const [expandedSection, setExpandedSection] = useState<string | null>('overview');
  const [selectedCategory, setSelectedCategory] = useState<string>('location');
  
  // Sample compensation factors
  const compensationFactors: CompensationFactor[] = [
    {
      id: 'data-uniqueness',
      name: 'Data Uniqueness',
      description: 'How rare or unique your data is compared to what buyers already have access to.',
      example: 'Unusual travel patterns or niche interests can increase value by 15-40%',
      impact: 35,
      icon: '🌟'
    },
    {
      id: 'data-completeness',
      name: 'Data Completeness',
      description: 'How comprehensive your data is across multiple categories and time periods.',
      example: 'Having 6+ months of continuous data can increase value by 20-25%',
      impact: 25,
      icon: '📊'
    },
    {
      id: 'trust-score',
      name: 'Trust Score',
      description: 'Your reliability rating based on data quality and platform participation.',
      example: 'Gold trust level can increase compensation by 20-30%',
      impact: 20,
      icon: '🛡️'
    },
    {
      id: 'market-demand',
      name: 'Market Demand',
      description: 'Current buyer interest in your specific data categories and demographic.',
      example: 'High-demand demographics can see 10-50% higher offers',
      impact: 15,
      icon: '📈'
    },
    {
      id: 'consent-scope',
      name: 'Consent Scope',
      description: 'The breadth of usage rights you grant buyers for your data.',
      example: 'Broader consent options can increase value by 5-15%',
      impact: 5,
      icon: '📝'
    }
  ];
  
  // Sample data categories with base values
  const dataCategories: DataCategory[] = [
    {
      id: 'location',
      name: 'Location Data',
      baseValue: '$2.00-$5.00/month',
      description: 'Geographic data showing movement patterns, visited locations, and dwell times.',
      bonusFactors: [
        'Consistent daily patterns',
        'Regular travel to premium retail locations',
        'Diverse location types (work, home, entertainment)'
      ]
    },
    {
      id: 'browsing',
      name: 'Browsing History',
      baseValue: '$3.00-$7.50/month',
      description: 'Web browsing patterns, search queries, and content engagement metrics.',
      bonusFactors: [
        'Research-oriented browsing',
        'Pre-purchase research patterns',
        'Engagement with specialized content'
      ]
    },
    {
      id: 'purchase',
      name: 'Purchase History',
      baseValue: '$5.00-$12.00/month',
      description: 'Transaction data, purchase categories, frequency, and spending patterns.',
      bonusFactors: [
        'Premium product purchases',
        'Consistent category spending',
        'Early adopter patterns'
      ]
    },
    {
      id: 'app-usage',
      name: 'App Usage',
      baseValue: '$1.50-$4.00/month',
      description: 'App engagement patterns, usage duration, and feature utilization.',
      bonusFactors: [
        'Finance and productivity app usage',
        'Consistent daily app patterns',
        'Engagement with premium app features'
      ]
    },
    {
      id: 'demographic',
      name: 'Demographic Data',
      baseValue: '$1.00-$3.00/month',
      description: 'Basic demographic information combined with lifestyle indicators.',
      bonusFactors: [
        'Niche demographic segments',
        'Lifestyle indicators',
        'Professional information'
      ]
    }
  ];

  const toggleSection = (section: string) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  // Find the currently selected category
  const selectedCategoryData = dataCategories.find(cat => cat.id === selectedCategory);

  return (
    <div className="education-container">
      <div className="education-header">
        <div className="education-header-icon">💰</div>
        <h1 className="education-title">Understanding Your Compensation</h1>
      </div>
      
      <p className="education-subtitle">
        Tavren uses a transparent compensation model that rewards quality data contributions.
        Learn how your rewards are calculated and how to maximize your earnings.
      </p>
      
      <div className="education-section">
        <button 
          className="education-collapse-trigger" 
          onClick={() => toggleSection('overview')}
          aria-expanded={expandedSection === 'overview'}
        >
          <h2 className="education-section-title">
            <span>How Compensation Works</span>
            <span style={{ marginLeft: 'auto' }}>
              {expandedSection === 'overview' ? '▼' : '►'}
            </span>
          </h2>
        </button>
        
        {expandedSection === 'overview' && (
          <div className="education-collapse-content">
            <p className="education-section-content">
              At Tavren, you're paid for the value your data brings to buyers. Unlike other platforms that profit from your 
              data without compensation, we ensure you receive fair payment based on several factors:
            </p>
            
            <div className="education-visual" style={{ padding: '1rem', textAlign: 'center' }}>
              <div style={{ maxWidth: '500px', margin: '0 auto' }}>
                <h3>Your Compensation Formula</h3>
                <div style={{ 
                  padding: '1rem', 
                  backgroundColor: '#f8f9fa', 
                  borderRadius: '8px',
                  fontFamily: 'monospace',
                  margin: '1rem 0'
                }}>
                  Base Value × Data Quality × Trust Score × Market Demand
                </div>
                <p>The result is your monthly compensation for each data category you share.</p>
              </div>
            </div>
            
            <p className="education-section-content">
              Compensation is paid monthly into your Tavren wallet and can be withdrawn to your preferred payment method.
              As your data history grows and your trust score improves, your compensation typically increases over time.
            </p>
          </div>
        )}
      </div>
      
      <div className="education-section">
        <button 
          className="education-collapse-trigger" 
          onClick={() => toggleSection('factors')}
          aria-expanded={expandedSection === 'factors'}
        >
          <h2 className="education-section-title">
            <span>Factors That Affect Your Compensation</span>
            <span style={{ marginLeft: 'auto' }}>
              {expandedSection === 'factors' ? '▼' : '►'}
            </span>
          </h2>
        </button>
        
        {expandedSection === 'factors' && (
          <div className="education-collapse-content">
            <p className="education-section-content">
              Multiple factors influence how much you earn for your data. Understanding these can help you 
              optimize your participation on the platform.
            </p>
            
            <div className="education-grid">
              {compensationFactors.map(factor => (
                <div key={factor.id} className="education-card">
                  <div className="education-metric">
                    <div className="education-metric-icon">{factor.icon}</div>
                    <div>
                      <h3 className="education-metric-title">{factor.name}</h3>
                      <p className="education-metric-value">Impact: <strong>{factor.impact}%</strong></p>
                    </div>
                  </div>
                  <p>{factor.description}</p>
                  <p><strong>Example:</strong> {factor.example}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      
      <div className="education-section">
        <button 
          className="education-collapse-trigger" 
          onClick={() => toggleSection('categories')}
          aria-expanded={expandedSection === 'categories'}
        >
          <h2 className="education-section-title">
            <span>Data Categories & Value</span>
            <span style={{ marginLeft: 'auto' }}>
              {expandedSection === 'categories' ? '▼' : '►'}
            </span>
          </h2>
        </button>
        
        {expandedSection === 'categories' && (
          <div className="education-collapse-content">
            <p className="education-section-content">
              Different types of data have different base values. Select a category below to learn more about its value.
            </p>
            
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', margin: '1rem 0' }}>
              {dataCategories.map(category => (
                <button
                  key={category.id}
                  onClick={() => setSelectedCategory(category.id)}
                  style={{
                    padding: '0.5rem 1rem',
                    border: `1px solid ${selectedCategory === category.id ? 'var(--primary-color)' : 'var(--border-color)'}`,
                    borderRadius: '50px',
                    backgroundColor: selectedCategory === category.id ? 'var(--primary-color)' : 'transparent',
                    color: selectedCategory === category.id ? 'white' : 'var(--text-primary)',
                    cursor: 'pointer',
                    fontSize: '0.9rem'
                  }}
                >
                  {category.name}
                </button>
              ))}
            </div>
            
            {selectedCategoryData && (
              <div className="education-card">
                <h3 className="education-card-title">{selectedCategoryData.name}</h3>
                <p><strong>Base Value:</strong> {selectedCategoryData.baseValue}</p>
                <p>{selectedCategoryData.description}</p>
                <div>
                  <p><strong>Value Boosting Factors:</strong></p>
                  <ul>
                    {selectedCategoryData.bonusFactors.map((factor, index) => (
                      <li key={index}>{factor}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
      
      <div className="education-section">
        <button 
          className="education-collapse-trigger" 
          onClick={() => toggleSection('maximize')}
          aria-expanded={expandedSection === 'maximize'}
        >
          <h2 className="education-section-title">
            <span>How to Maximize Your Earnings</span>
            <span style={{ marginLeft: 'auto' }}>
              {expandedSection === 'maximize' ? '▼' : '►'}
            </span>
          </h2>
        </button>
        
        {expandedSection === 'maximize' && (
          <div className="education-collapse-content">
            <p className="education-section-content">
              Here are actionable strategies to increase your earnings on the Tavren platform:
            </p>
            
            <div className="education-card">
              <h3 className="education-card-title">Enable Multiple Data Categories</h3>
              <p>Users who share data across 3+ categories typically earn 50-100% more than those who share only one category.
                Each additional category not only adds its base value but can reveal valuable patterns across categories.</p>
            </div>
            
            <div className="education-card">
              <h3 className="education-card-title">Build Your Trust Score</h3>
              <p>Reaching and maintaining Gold trust level can increase your compensation by 20-30% across all data categories.
                Focus on consistent participation and high-quality data contributions.</p>
            </div>
            
            <div className="education-card">
              <h3 className="education-card-title">Maintain Continuous Data History</h3>
              <p>Longer data history (6+ months) is more valuable to buyers for trend analysis. Uninterrupted data
                streams can increase your compensation by 15-25% compared to sporadic participation.</p>
            </div>
            
            <div className="education-card">
              <h3 className="education-card-title">Participate in Premium Offers</h3>
              <p>Watch for premium data requests in your dashboard. These targeted offers may pay 2-3× the standard
                rate for specific data types or participation in specialized research.</p>
            </div>
          </div>
        )}
      </div>
      
      <div className="education-section">
        <button 
          className="education-collapse-trigger" 
          onClick={() => toggleSection('faq')}
          aria-expanded={expandedSection === 'faq'}
        >
          <h2 className="education-section-title">
            <span>Frequently Asked Questions</span>
            <span style={{ marginLeft: 'auto' }}>
              {expandedSection === 'faq' ? '▼' : '►'}
            </span>
          </h2>
        </button>
        
        {expandedSection === 'faq' && (
          <div className="education-collapse-content">
            <div className="education-card">
              <h3 className="education-card-title">How often will I be paid?</h3>
              <p>Compensation is calculated monthly and deposited into your Tavren wallet on the 15th of each month.
                You can withdraw to your preferred payment method at any time with no minimum balance requirement.</p>
            </div>
            
            <div className="education-card">
              <h3 className="education-card-title">Why does my compensation amount vary month to month?</h3>
              <p>Compensation fluctuates based on market demand, the volume and quality of data you provide, and
                seasonal factors. Some months may have higher demand for certain data categories than others.</p>
            </div>
            
            <div className="education-card">
              <h3 className="education-card-title">Do I receive compensation for historical data?</h3>
              <p>Yes. When you first join Tavren, you'll receive compensation for any historical data you choose
                to share (typically up to 12 months back). This is calculated at the time of your initial data sync.</p>
            </div>
            
            <div className="education-card">
              <h3 className="education-card-title">Can I negotiate higher rates?</h3>
              <p>While base rates are standardized, users with exceptionally valuable data profiles may receive
                premium offers. These are automatically identified by our system based on unique data characteristics.</p>
            </div>
            
            <div className="education-card">
              <h3 className="education-card-title">What happens to my compensation if I pause data sharing?</h3>
              <p>If you temporarily pause data sharing, you'll continue to receive compensation for any historical
                data that buyers access. However, your ongoing monthly payments will decrease until you resume sharing.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CompensationModel; 