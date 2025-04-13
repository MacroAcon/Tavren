import React from 'react';
import { Card, Button } from '../shared';
import { 
  TrustScoreExplainer, 
  CompensationModel, 
  LearnMoreButton, 
  EducationalTooltip, 
  EducationalCard, 
  EducationalMinibanner 
} from './index';
import './education.css';

/**
 * Demo component showing how the education components can be integrated
 * This is for development/demonstration purposes
 */
const EducationDemo: React.FC = () => {
  return (
    <div className="education-container">
      <div className="education-header">
        <div className="education-header-icon">📚</div>
        <h1 className="education-title">Education Components Demo</h1>
      </div>
      
      <p className="education-subtitle">
        This page demonstrates how the educational components can be integrated into the Tavren application.
      </p>
      
      {/* Demo of standalone components */}
      <div className="education-section">
        <h2 className="education-section-title">Standalone Components</h2>
        <p className="education-section-content">
          These components can be accessed directly via routes or from a Help menu:
        </p>
        
        <div className="education-grid">
          <Card>
            <h3>Trust Score Explainer</h3>
            <p>Full page explaining trust scores and their impact</p>
            <Button variant="primary" onClick={() => {}} className="button-small">
              View Component
            </Button>
          </Card>
          
          <Card>
            <h3>Compensation Model</h3>
            <p>Full page explaining how compensation works</p>
            <Button variant="primary" onClick={() => {}} className="button-small">
              View Component
            </Button>
          </Card>
        </div>
      </div>
      
      {/* Demo of integration approaches */}
      <div className="education-section">
        <h2 className="education-section-title">Integration Options</h2>
        <p className="education-section-content">
          These helper components make it easy to add educational content to existing screens:
        </p>
        
        {/* Demo of banners */}
        <h3>Educational Banners</h3>
        <p>Display at key moments or in relevant sections:</p>
        
        <EducationalMinibanner topic="trust-score" />
        <EducationalMinibanner topic="compensation" />
        
        {/* Demo of cards */}
        <h3>Educational Cards</h3>
        <p>Embed in related content areas:</p>
        
        <div className="education-grid">
          <EducationalCard topic="trust-score" />
          <EducationalCard topic="compensation" />
        </div>
        
        {/* Demo of learn more buttons */}
        <h3>Learn More Buttons</h3>
        <p>Add to any interface element:</p>
        
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', margin: '1rem 0' }}>
          <LearnMoreButton topic="trust-score" />
          <LearnMoreButton topic="compensation" buttonText="Understand Compensation" variant="primary" />
          <LearnMoreButton topic="trust-score" buttonText="Trust Score Info" variant="secondary" size="large" />
        </div>
        
        {/* Demo of tooltips */}
        <h3>Educational Tooltips</h3>
        <p>Add to terms or concepts that need explanation:
          <EducationalTooltip topic="trust-score">Trust Score</EducationalTooltip>
          calculations affect your
          <EducationalTooltip topic="compensation">compensation</EducationalTooltip>
           rates.
        </p>
      </div>
      
      {/* Demo of contextual integration */}
      <div className="education-section">
        <h2 className="education-section-title">Contextual Integration</h2>
        <p className="education-section-content">
          Examples of how education components can be integrated into different app flows:
        </p>
        
        <div className="education-card">
          <h3 className="education-card-title">From Consent Settings → Privacy Guides</h3>
          <p>When viewing consent settings, add a banner explaining privacy implications.</p>
          <div style={{ border: '1px solid var(--border-color)', padding: '1rem', borderRadius: '8px', margin: '1rem 0' }}>
            <h4>Consent Management (Mockup)</h4>
            <div>
              <label>
                <input type="checkbox" checked readOnly /> Allow location data collection
              </label>
              <EducationalTooltip topic="trust-score">Why this matters</EducationalTooltip>
            </div>
            <div style={{ marginTop: '1rem' }}>
              <LearnMoreButton topic="trust-score" buttonText="Learn about trust & privacy" />
            </div>
          </div>
        </div>
        
        <div className="education-card">
          <h3 className="education-card-title">From Offer Details → Trust Score & Data Type</h3>
          <p>When viewing offer details, explain related trust factors and data categories.</p>
          <div style={{ border: '1px solid var(--border-color)', padding: '1rem', borderRadius: '8px', margin: '1rem 0' }}>
            <h4>Premium Offer (Mockup)</h4>
            <p><strong>Compensation:</strong> $12.50/month</p>
            <p><strong>Required Trust Level:</strong> Silver or higher <EducationalTooltip topic="trust-score">?</EducationalTooltip></p>
            <div style={{ marginTop: '1rem' }}>
              <LearnMoreButton topic="compensation" buttonText="How compensation works" />
            </div>
          </div>
        </div>
        
        <div className="education-card">
          <h3 className="education-card-title">From Wallet → Compensation Model</h3>
          <p>When viewing wallet or receiving first payment, explain compensation factors.</p>
          <div style={{ border: '1px solid var(--border-color)', padding: '1rem', borderRadius: '8px', margin: '1rem 0' }}>
            <h4>Your Wallet (Mockup)</h4>
            <p><strong>Current Balance:</strong> $37.25</p>
            <p><strong>This Month's Earnings:</strong> $15.75 <EducationalTooltip topic="compensation">How calculated?</EducationalTooltip></p>
            <EducationalMinibanner topic="compensation" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default EducationDemo; 