import React from 'react';
import CopyVariantSwitcher from './CopyVariantSwitcher';
import { getVariantFromUrl } from '../../utils/analytics';

interface ScanIntroductionProps {
  onContinue: () => void;
  currentStep?: string;
}

const ScanIntroduction: React.FC<ScanIntroductionProps> = ({ 
  onContinue,
  currentStep = 'introduction'
}) => {
  // Check for variant override from URL
  const urlVariant = getVariantFromUrl();
  
  return (
    <div className="onboarding-container introduction-screen">
      <div className="content-wrapper">
        <div className="pulse-animation"></div>
        
        {/* A/B testing component for onboarding copy */}
        <CopyVariantSwitcher
          onCtaClick={onContinue}
          variantOverride={urlVariant as 'A' | 'B' | undefined}
          currentStep={currentStep}
        />
        
        <p className="disclaimer">
          We'll analyze your digital presence to show you who's tracking you and what they know.
          Your data remains private and secure throughout this process.
        </p>
      </div>
    </div>
  );
};

export default ScanIntroduction; 