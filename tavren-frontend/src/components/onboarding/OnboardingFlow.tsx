import React from 'react';
import ScanIntroduction from './ScanIntroduction';
import ScanVisualization from './ScanVisualization';
import ScanResults from './ScanResults';
import InitialOfferPresentation from './InitialOfferPresentation';
import './onboarding.css';

// Import from our new stores
import { useOnboardingStore, OnboardingStep } from '../../stores';

interface OnboardingFlowProps {
  onComplete: () => void;
}

const OnboardingFlow: React.FC<OnboardingFlowProps> = ({ onComplete }) => {
  // Use the onboarding store instead of local state
  const currentStep = useOnboardingStore(state => state.currentStep);
  const nextStep = useOnboardingStore(state => state.nextStep);
  const goToStep = useOnboardingStore(state => state.goToStep);
  const setScanResults = useOnboardingStore(state => state.setScanResults);
  
  const handleNextStep = () => {
    // If we're at the last step, call the onComplete prop
    if (currentStep === OnboardingStep.Offer) {
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
    
    // Move to the next step after saving results
    nextStep();
  };
  
  const renderCurrentStep = () => {
    switch (currentStep) {
      case OnboardingStep.Introduction:
        return <ScanIntroduction onContinue={nextStep} />;
      
      case OnboardingStep.Scanning:
        return <ScanVisualization onScanComplete={saveScanResults} />;
      
      case OnboardingStep.Results:
        return <ScanResults onContinue={handleNextStep} />;
      
      case OnboardingStep.Offer:
        return <InitialOfferPresentation onComplete={handleNextStep} />;
      
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