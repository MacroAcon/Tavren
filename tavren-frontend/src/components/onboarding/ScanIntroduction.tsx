import React from 'react';

interface ScanIntroductionProps {
  onContinue: () => void;
}

const ScanIntroduction: React.FC<ScanIntroductionProps> = ({ onContinue }) => {
  return (
    <div className="onboarding-container introduction-screen">
      <div className="content-wrapper">
        <div className="pulse-animation"></div>
        
        <h1 className="headline">They've been watching. You've been giving.</h1>
        <h2 className="subheadline">Let's change that.</h2>
        
        <p className="intro-text">
          Your data is valuable, but you've been giving it away for free.
          Tavren helps you take back control and get paid for the data you choose to share.
        </p>
        
        <div className="action-area">
          <button 
            className="primary-button" 
            onClick={onContinue}
          >
            Discover Your Digital Footprint
          </button>
          
          <p className="disclaimer">
            We'll analyze your digital presence to show you who's tracking you and what they know.
            Your data remains private and secure throughout this process.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ScanIntroduction; 