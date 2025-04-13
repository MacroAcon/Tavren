import React, { useState, useEffect } from 'react';

interface ScanVisualizationProps {
  onScanComplete: () => void;
}

const ScanVisualization: React.FC<ScanVisualizationProps> = ({ onScanComplete }) => {
  const [scanProgress, setScanProgress] = useState(0);
  const [scanStage, setScanStage] = useState(0);
  const [fadeIn, setFadeIn] = useState(true);
  
  const scanStages = [
    'Analyzing digital footprint...',
    'Discovering connected apps...',
    'Identifying tracking patterns...',
    'Quantifying data exposure...',
    'Evaluating privacy impact...',
    'Compiling results...'
  ];
  
  useEffect(() => {
    // Simulate a scanning process over 10 seconds
    const scanTimer = setInterval(() => {
      setScanProgress(prev => {
        const newProgress = prev + 1;
        
        // Update the stage based on progress
        if (newProgress % 16 === 0 && newProgress < 96) {
          setFadeIn(false);
          setTimeout(() => {
            setScanStage(s => (s + 1) % scanStages.length);
            setFadeIn(true);
          }, 500);
        }
        
        // Complete scan at 100%
        if (newProgress >= 100) {
          clearInterval(scanTimer);
          setTimeout(onScanComplete, 1000);
          return 100;
        }
        
        return newProgress;
      });
    }, 100); // Update every 100ms
    
    return () => clearInterval(scanTimer);
  }, [onScanComplete, scanStages.length]);
  
  return (
    <div className="onboarding-container scan-visualization">
      <div className="scan-content">
        <div className="scan-visual">
          {/* Animated visualization elements */}
          <div className="scan-ring outer-ring"></div>
          <div className="scan-ring middle-ring"></div>
          <div className="scan-ring inner-ring"></div>
          <div className="scan-beam"></div>
          
          {/* Data points that appear during scan */}
          <div className="data-points">
            {Array.from({ length: 20 }).map((_, i) => (
              <div 
                key={i}
                className="data-point"
                style={{
                  opacity: scanProgress > i * 5 ? 1 : 0,
                  transform: `translate(${Math.sin(i) * 120}px, ${Math.cos(i) * 120}px)`,
                  animationDelay: `${i * 0.1}s`
                }}
              />
            ))}
          </div>
        </div>
        
        <div className="scan-info">
          <h2 className={`scan-stage ${fadeIn ? 'fade-in' : 'fade-out'}`}>
            {scanStages[scanStage]}
          </h2>
          
          <div className="progress-bar-container">
            <div className="progress-bar" style={{ width: `${scanProgress}%` }}></div>
          </div>
          
          <p className="progress-text">{scanProgress}% Complete</p>
        </div>
      </div>
    </div>
  );
};

export default ScanVisualization; 