import React, { useEffect, useState } from 'react';
import { PulseIcon, ShieldIcon, ArrowRightIcon } from './icons';
import './your-data-at-work.css';
import { DataImpactData, DataImpactMetric, getRandomDataImpact } from '../../mock/dataImpactService';

interface YourDataAtWorkProps {
  /**
   * Optional override for the widget headline
   */
  headline?: string;
  
  /**
   * Optional override for the widget subtext
   */
  subtext?: string;
  
  /**
   * Optional array of metrics to display
   */
  metrics?: DataImpactMetric[];
  
  /**
   * Optional privacy reminder text
   */
  privacyReminder?: string;
  
  /**
   * Optional call-to-action text
   */
  ctaText?: string;
  
  /**
   * Function to call when CTA button is clicked
   */
  onCtaClick?: () => void;
  
  /**
   * CSS class name for custom styling
   */
  className?: string;
}

/**
 * YourDataAtWork Component
 * 
 * Displays how user data contributes to collective value with privacy reassurance.
 * Mobile-first responsive design with accessible elements.
 */
const YourDataAtWork: React.FC<YourDataAtWorkProps> = ({
  headline,
  subtext,
  metrics,
  privacyReminder,
  ctaText = 'See My Impact',
  onCtaClick,
  className = ''
}) => {
  const [impactData, setImpactData] = useState<DataImpactData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  // Fetch mock data on component mount
  useEffect(() => {
    // Simulate API call delay
    const timer = setTimeout(() => {
      setImpactData(getRandomDataImpact());
      setIsLoading(false);
    }, 500);
    
    return () => clearTimeout(timer);
  }, []);
  
  // Show loading state while data is being fetched
  if (isLoading) {
    return (
      <div className={`data-at-work-card ${className}`} aria-busy="true">
        <div className="loading-container">
          <div className="loading-spinner" aria-hidden="true"></div>
          <p className="loading-message">Loading your impact data...</p>
        </div>
      </div>
    );
  }
  
  // Early return if data couldn't be loaded
  if (!impactData) {
    return (
      <div className={`data-at-work-card ${className}`}>
        <p className="impact-subtext">Unable to load your impact data. Please try again later.</p>
      </div>
    );
  }
  
  // Use props if provided, otherwise use fetched data
  const displayHeadline = headline || impactData.headline;
  const displaySubtext = subtext || impactData.subtext;
  const displayMetrics = metrics || impactData.metrics;
  const displayPrivacyReminder = privacyReminder || impactData.privacyReminder;
  
  return (
    <div className={`data-at-work-card ${className}`}>
      <div className="impact-header">
        <div className="pulse-icon-container" aria-hidden={true}>
          <PulseIcon />
        </div>
        <h2>{displayHeadline}</h2>
      </div>
      
      <p className="impact-subtext">{displaySubtext}</p>
      
      <div className="metrics-container">
        {displayMetrics.map((metric, index) => (
          <div key={index} className="metric-block">
            <span className="metric-value">{metric.value}</span>
            <span className="metric-label">{metric.label}</span>
          </div>
        ))}
      </div>
      
      <div className="privacy-reminder" role="note">
        <ShieldIcon aria-hidden={true} />
        <p>{displayPrivacyReminder}</p>
      </div>
      
      <button
        className="impact-cta"
        onClick={onCtaClick}
        aria-label={`${ctaText} - View details about how your data is making an impact`}
      >
        <span>{ctaText}</span>
        <ArrowRightIcon aria-hidden={true} />
      </button>
    </div>
  );
};

export default YourDataAtWork; 