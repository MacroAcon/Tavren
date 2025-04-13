import React, { useState } from 'react';
import './education.css';

interface TrustMetric {
  id: string;
  name: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
  icon: string;
}

interface TrustLevel {
  level: string;
  range: string;
  description: string;
  benefits: string[];
}

const TrustScoreExplainer: React.FC = () => {
  const [expandedSection, setExpandedSection] = useState<string | null>('overview');
  
  // Sample trust metrics that affect buyer trust scores
  const trustMetrics: TrustMetric[] = [
    {
      id: 'data-quality',
      name: 'Data Quality',
      description: 'How complete, accurate, and relevant your provided data is to buyers.',
      impact: 'high',
      icon: '📊'
    },
    {
      id: 'consent-duration',
      name: 'Consent Duration',
      description: 'How long you maintain consent for data use without frequent revocations.',
      impact: 'high',
      icon: '⏱️'
    },
    {
      id: 'response-time',
      name: 'Response Time',
      description: 'How quickly you respond to additional data or verification requests.',
      impact: 'medium',
      icon: '⚡'
    },
    {
      id: 'data-consistency',
      name: 'Data Consistency',
      description: 'Whether your data patterns remain consistent over time, indicating reliability.',
      impact: 'medium',
      icon: '🔄'
    },
    {
      id: 'feedback-compliance',
      name: 'Feedback Compliance',
      description: 'Your rate of compliance with feedback surveys and follow-up requests.',
      impact: 'low',
      icon: '📝'
    },
  ];
  
  // Sample trust levels and their benefits
  const trustLevels: TrustLevel[] = [
    {
      level: 'Bronze',
      range: '0-40',
      description: 'New or occasional data providers with limited history.',
      benefits: [
        'Access to basic data offers',
        'Standard compensation rates',
        'Limited access to premium offers'
      ]
    },
    {
      level: 'Silver',
      range: '41-70',
      description: 'Established data providers with good consistency and quality.',
      benefits: [
        'Access to enhanced data offers',
        '10-15% bonus compensation rates',
        'Priority for new data campaigns',
        'Early access to new data markets'
      ]
    },
    {
      level: 'Gold',
      range: '71-100',
      description: 'Premium data providers with excellent history and comprehensive data.',
      benefits: [
        'Access to all data offers including exclusive high-value opportunities',
        '20-30% bonus compensation rates',
        'First access to premium data campaigns',
        'Reduced verification requirements',
        'VIP support channel access'
      ]
    }
  ];

  const toggleSection = (section: string) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  return (
    <div className="education-container">
      <div className="education-header">
        <div className="education-header-icon">🔒</div>
        <h1 className="education-title">Trust Score Explained</h1>
      </div>
      
      <p className="education-subtitle">
        Your trust score reflects how reliable and valuable your data is to buyers on the Tavren platform.
        Higher scores lead to better offers and increased compensation.
      </p>
      
      <div className="education-section">
        <button 
          className="education-collapse-trigger" 
          onClick={() => toggleSection('overview')}
          aria-expanded={expandedSection === 'overview'}
        >
          <h2 className="education-section-title">
            <span>What is a Trust Score?</span>
            <span style={{ marginLeft: 'auto' }}>
              {expandedSection === 'overview' ? '▼' : '►'}
            </span>
          </h2>
        </button>
        
        {expandedSection === 'overview' && (
          <div className="education-collapse-content">
            <p className="education-section-content">
              Your Trust Score is a numeric value from 0-100 that represents how reliable and valuable your data 
              contributions are to buyers on the platform. Like a credit score for data, it helps buyers 
              identify high-quality data providers and rewards consistent, quality participation.
            </p>
            
            <div className="education-visual">
              <div style={{ padding: '1rem', textAlign: 'center' }}>
                <div style={{ maxWidth: '500px', margin: '0 auto' }}>
                  <div className="trust-score-indicator trust-level-high">
                    <div className="trust-score-indicator-fill" style={{ width: '75%' }}></div>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.5rem' }}>
                    <span>0</span>
                    <span>25</span>
                    <span>50</span>
                    <span>75</span>
                    <span>100</span>
                  </div>
                </div>
                <p><strong>Sample score: 75</strong> - Gold level trust</p>
              </div>
            </div>
          </div>
        )}
      </div>
      
      <div className="education-section">
        <button 
          className="education-collapse-trigger" 
          onClick={() => toggleSection('metrics')}
          aria-expanded={expandedSection === 'metrics'}
        >
          <h2 className="education-section-title">
            <span>What Affects Your Score</span>
            <span style={{ marginLeft: 'auto' }}>
              {expandedSection === 'metrics' ? '▼' : '►'}
            </span>
          </h2>
        </button>
        
        {expandedSection === 'metrics' && (
          <div className="education-collapse-content">
            <p className="education-section-content">
              Several factors influence your trust score. Understanding these metrics can help you 
              maintain a higher score and access better offers.
            </p>
            
            <div className="education-grid">
              {trustMetrics.map(metric => (
                <div key={metric.id} className="education-card">
                  <div className="education-metric">
                    <div className="education-metric-icon">{metric.icon}</div>
                    <div>
                      <h3 className="education-metric-title">{metric.name}</h3>
                      <p className="education-metric-value">Impact: <strong>{metric.impact}</strong></p>
                    </div>
                  </div>
                  <p>{metric.description}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      
      <div className="education-section">
        <button 
          className="education-collapse-trigger" 
          onClick={() => toggleSection('levels')}
          aria-expanded={expandedSection === 'levels'}
        >
          <h2 className="education-section-title">
            <span>Trust Levels & Benefits</span>
            <span style={{ marginLeft: 'auto' }}>
              {expandedSection === 'levels' ? '▼' : '►'}
            </span>
          </h2>
        </button>
        
        {expandedSection === 'levels' && (
          <div className="education-collapse-content">
            <p className="education-section-content">
              Your trust score places you in one of three tiers, each with increasing benefits.
            </p>
            
            <table className="education-table">
              <thead>
                <tr>
                  <th>Level</th>
                  <th>Score Range</th>
                  <th>Description</th>
                  <th>Benefits</th>
                </tr>
              </thead>
              <tbody>
                {trustLevels.map(level => (
                  <tr key={level.level}>
                    <td><strong>{level.level}</strong></td>
                    <td>{level.range}</td>
                    <td>{level.description}</td>
                    <td>
                      <ul style={{ margin: 0, paddingLeft: '1.5rem' }}>
                        {level.benefits.map((benefit, index) => (
                          <li key={index}>{benefit}</li>
                        ))}
                      </ul>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      
      <div className="education-section">
        <button 
          className="education-collapse-trigger" 
          onClick={() => toggleSection('improve')}
          aria-expanded={expandedSection === 'improve'}
        >
          <h2 className="education-section-title">
            <span>How to Improve Your Score</span>
            <span style={{ marginLeft: 'auto' }}>
              {expandedSection === 'improve' ? '▼' : '►'}
            </span>
          </h2>
        </button>
        
        {expandedSection === 'improve' && (
          <div className="education-collapse-content">
            <p className="education-section-content">
              Here are some practical steps you can take to maintain or improve your trust score:
            </p>
            
            <div className="education-card">
              <h3 className="education-card-title">Enable Comprehensive Data Collection</h3>
              <p>The more complete your data profile, the more valuable it is to buyers. Consider enabling more data categories 
                if you're comfortable with the privacy settings.</p>
            </div>
            
            <div className="education-card">
              <h3 className="education-card-title">Maintain Consistent Consent</h3>
              <p>Frequent consent changes or revocations can lower your trust score. Set realistic privacy boundaries 
                that you're comfortable maintaining long-term.</p>
            </div>
            
            <div className="education-card">
              <h3 className="education-card-title">Respond Promptly to Requests</h3>
              <p>When buyers request additional information or verification, responding quickly demonstrates reliability 
                and improves your score.</p>
            </div>
            
            <div className="education-card">
              <h3 className="education-card-title">Complete Feedback Surveys</h3>
              <p>Participation in platform surveys helps improve the system and demonstrates your engagement, positively 
                affecting your score.</p>
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
              <h3 className="education-card-title">How often is my trust score updated?</h3>
              <p>Your trust score is recalculated approximately every 30 days, or after significant activity such as 
                new data contributions or consent changes.</p>
            </div>
            
            <div className="education-card">
              <h3 className="education-card-title">Can my trust score decrease?</h3>
              <p>Yes. Frequent consent revocations, low-quality data, or failure to respond to verification requests 
                can decrease your score over time.</p>
            </div>
            
            <div className="education-card">
              <h3 className="education-card-title">Is my trust score visible to buyers?</h3>
              <p>Buyers see your trust level (Bronze, Silver, Gold) but not your exact numeric score. This helps them 
                identify reliable data sources while protecting your privacy.</p>
            </div>
            
            <div className="education-card">
              <h3 className="education-card-title">How quickly can I improve my trust score?</h3>
              <p>Trust scores typically improve gradually over 3-6 months of consistent positive behavior. New accounts 
                start at a neutral position and build trust over time.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TrustScoreExplainer; 