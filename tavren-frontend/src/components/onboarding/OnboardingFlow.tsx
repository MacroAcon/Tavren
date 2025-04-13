import React, { useEffect, useState } from 'react';
import ScanIntroduction from './ScanIntroduction';
import ScanVisualization from './ScanVisualization';
import ScanResults from './ScanResults';
import InitialOfferPresentation from './InitialOfferPresentation';
import './onboarding.css';
import { getStoredVariant, logConversionEvent } from '../../utils/analytics';

// Import from our new stores
import { useOnboardingStore, OnboardingStep } from '../../stores';

interface OnboardingFlowProps {
  onComplete: () => void;
}

// Step names for analytics tracking
const STEP_NAMES = [
  'introduction',
  'scanning',
  'results',
  'offer',
  'complete'
];

const OnboardingFlow: React.FC<OnboardingFlowProps> = ({ onComplete }) => {
  // Use the onboarding store instead of local state
  const currentStep = useOnboardingStore(state => state.currentStep);
  const nextStep = useOnboardingStore(state => state.nextStep);
  const goToStep = useOnboardingStore(state => state.goToStep);
  const setScanResults = useOnboardingStore(state => state.setScanResults);
  
  // Get the stored variant for conversion tracking
  const [activeVariant, setActiveVariant] = useState<string | null>(null);
  
  // Get the variant when the component mounts
  useEffect(() => {
    const variant = getStoredVariant('onboarding-value-proposition');
    setActiveVariant(variant);
  }, []);
  
  const handleNextStep = () => {
    // Track conversion for the current step
    if (activeVariant) {
      logConversionEvent(
        activeVariant, 
        `${STEP_NAMES[currentStep]}_complete`
      );
    }
    
    // If we're at the last step, call the onComplete prop
    if (currentStep === OnboardingStep.Offer) {
      // Track completion of entire flow
      if (activeVariant) {
        logConversionEvent(activeVariant, 'onboarding_complete');
      }
      onComplete();
    } else {
      nextStep();
    }
  };
  
  // Simulated scan results from our mock data
  const saveScanResults = () => {
    setScanResults({
      trackerCount: 37,
      appCount: 11,
      dataCategories: 5
    });
    
    // Track scan completion
    if (activeVariant) {
      logConversionEvent(activeVariant, 'scan_complete');
    }
    
    // Move to the next step after saving results
    nextStep();
  };
  
  const renderCurrentStep = () => {
    switch (currentStep) {
      case OnboardingStep.Introduction:
        return <ScanIntroduction 
                 onContinue={nextStep} 
                 currentStep={STEP_NAMES[currentStep]}
               />;
      
      case OnboardingStep.Scanning:
        return <ScanVisualization 
                 onScanComplete={saveScanResults} 
                 currentStep={STEP_NAMES[currentStep]}
               />;
      
      case OnboardingStep.Results:
        return <ScanResults 
                 onContinue={handleNextStep} 
                 currentStep={STEP_NAMES[currentStep]}
               />;
      
      case OnboardingStep.Offer:
        return <InitialOfferPresentation 
                 onComplete={handleNextStep} 
                 currentStep={STEP_NAMES[currentStep]}
               />;
      
      default:
        return null;
    }
  };
  
  return (
    <div className="onboarding-flow">
      {renderCurrentStep()}
    </div>
  );
};

export default OnboardingFlow; 