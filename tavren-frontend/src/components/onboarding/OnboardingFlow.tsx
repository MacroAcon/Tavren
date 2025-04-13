import React, { useState } from 'react';
import ScanIntroduction from './ScanIntroduction';
import ScanVisualization from './ScanVisualization';
import ScanResults from './ScanResults';
import InitialOfferPresentation from './InitialOfferPresentation';
import './onboarding.css';

enum OnboardingStep {
  Introduction = 0,
  Scanning = 1,
  Results = 2,
  Offer = 3,
  Complete = 4
}

interface OnboardingFlowProps {
  onComplete: () => void;
}

const OnboardingFlow: React.FC<OnboardingFlowProps> = ({ onComplete }) => {
  const [currentStep, setCurrentStep] = useState<OnboardingStep>(OnboardingStep.Introduction);
  
  const handleNextStep = () => {
    setCurrentStep(prev => prev + 1);
    
    // If we're at the last step, call the onComplete prop
    if (currentStep === OnboardingStep.Offer) {
      onComplete();
    }
  };
  
  const renderCurrentStep = () => {
    switch (currentStep) {
      case OnboardingStep.Introduction:
        return <ScanIntroduction onContinue={handleNextStep} />;
      
      case OnboardingStep.Scanning:
        return <ScanVisualization onScanComplete={handleNextStep} />;
      
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