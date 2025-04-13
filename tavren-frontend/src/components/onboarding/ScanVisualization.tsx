import React, { useEffect, useState } from 'react';
import { logConversionEvent, getStoredVariant } from '../../utils/analytics';

interface ScanVisualizationProps {
  onScanComplete: () => void;
  currentStep?: string;
}

const ScanVisualization: React.FC<ScanVisualizationProps> = ({ 
  onScanComplete,
  currentStep = 'scanning'
}) => {
  const [progress, setProgress] = useState(0);

  // Track when the scan visualization is shown
  useEffect(() => {
    const variant = getStoredVariant('onboarding-value-proposition');
    if (variant) {
      logConversionEvent(variant, `${currentStep}_started`);
    }
  }, [currentStep]);
  
  useEffect(() => {
    // Simulate scanning progress with a timer
    const timer = setInterval(() => {
      setProgress(prev => {
        const newProgress = prev + 1;
        
        // Complete the scan when reaching 100%
        if (newProgress >= 100) {
          clearInterval(timer);
          
          // Wait a moment before completing to show 100%
          setTimeout(() => {
            onScanComplete();
          }, 500);
        }
        
        return newProgress > 100 ? 100 : newProgress;
      });
    }, 50);
    
    // Clean up timer on unmount
    return () => clearInterval(timer);
  }, [onScanComplete]);
  
  return (
    <div className="onboarding-container scan-screen">
      <div className="scan-content">
        <h2 className="scan-title">Analyzing Your Digital Footprint</h2>
        
        <div className="scan-visualization">
          <div className="scan-animation">
            {/* Animation elements would go here */}
            <div className="pulse-ripple"></div>
            <div className="scan-beam"></div>
          </div>
        </div>
        
        <div className="scan-progress">
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <div className="progress-text">
            <span className="progress-percentage">{progress}%</span>
            <span className="progress-status">
              {progress < 30 ? 'Detecting trackers...' :
               progress < 60 ? 'Analyzing data collection...' :
               progress < 90 ? 'Calculating value metrics...' :
               'Finalizing results...'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScanVisualization; 