import React, { useState } from 'react';
import { CopyVariantSwitcher } from './';
import './ab-test-demo.css';

const ABTestDemo: React.FC = () => {
  const [selectedVariant, setSelectedVariant] = useState<'A' | 'B' | undefined>(undefined);
  const [useAltHeadlines, setUseAltHeadlines] = useState(false);
  const [ctaClicked, setCtaClicked] = useState(false);
  
  const handleCtaClick = () => {
    setCtaClicked(true);
    setTimeout(() => setCtaClicked(false), 2000);
  };
  
  const resetDemo = () => {
    setSelectedVariant(undefined);
    setUseAltHeadlines(false);
    setCtaClicked(false);
  };
  
  return (
    <div className="ab-test-demo">
      <div className="demo-controls">
        <h2>A/B Test Controls</h2>
        <div className="control-row">
          <label>
            Variant:
            <select 
              value={selectedVariant || 'random'} 
              onChange={(e) => setSelectedVariant(e.target.value === 'random' ? undefined : e.target.value as 'A' | 'B')}
            >
              <option value="random">Random (50/50)</option>
              <option value="A">A - Empowerment</option>
              <option value="B">B - Reward</option>
            </select>
          </label>
          
          <label>
            <input 
              type="checkbox" 
              checked={useAltHeadlines} 
              onChange={() => setUseAltHeadlines(!useAltHeadlines)} 
            />
            Use Alternative Headlines
          </label>
          
          <button className="secondary-button" onClick={resetDemo}>
            Reset Demo
          </button>
        </div>
        
        <div className="control-info">
          <p>
            <strong>URL Testing:</strong> Append <code>?variant=A</code> or <code>?variant=B</code> to the URL to force a variant.
          </p>
        </div>
      </div>
      
      <div className="demo-preview">
        <h2>Preview</h2>
        <div className="preview-container">
          <CopyVariantSwitcher 
            variantOverride={selectedVariant}
            onCtaClick={handleCtaClick}
            useAltHeadlines={useAltHeadlines}
          />
          
          {ctaClicked && (
            <div className="click-notification">
              CTA clicked! In production, this would advance to the next step.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ABTestDemo; 