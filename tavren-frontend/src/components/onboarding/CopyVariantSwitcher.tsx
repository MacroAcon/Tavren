import React, { useEffect, useState } from 'react';
import { 
  trackVariantView, 
  trackVariantConversion, 
  getVariantFromUrl, 
  getRandomVariant,
  storeVariant,
  getStoredVariant,
  logConversionEvent 
} from '../../utils/analytics';
import './copy-variant-switcher.css';

// Constants for the test
const TEST_ID = 'onboarding-value-proposition';
const VARIANTS = ['A', 'B'] as const;

type Variant = typeof VARIANTS[number];

// Variant content
const VARIANT_CONTENT = {
  A: {
    headline: 'Your Data, Your Terms',
    subhead: 'Tavren puts you in control of your digital life. Choose what to share, see how it\'s used, and revoke access anytime—complete transparency with no surprises.',
    cta: 'Take Control Now',
    altHeadline: 'Data Control, Finally In Reach'
  },
  B: {
    headline: 'Earn From Your Digital Life',
    subhead: 'Your online activity creates value every day. Tavren ensures you get your fair share through easy, transparent data sharing that turns your everyday digital habits into real earnings.',
    cta: 'See My Earning Potential',
    altHeadline: 'Data Dividends, Now For Everyone'
  }
};

interface CopyVariantSwitcherProps {
  /**
   * Optional override to force a specific variant
   */
  variantOverride?: Variant;
  
  /**
   * Callback function when CTA button is clicked
   */
  onCtaClick: () => void;
  
  /**
   * Optional class name for styling
   */
  className?: string;
  
  /**
   * Whether to use alt headlines instead of primary headlines
   */
  useAltHeadlines?: boolean;
  
  /**
   * Current step in onboarding - used for conversion tracking
   */
  currentStep?: string;
}

/**
 * A/B testing component for onboarding messaging
 * Switches between Empowerment (A) and Reward (B) messaging
 */
const CopyVariantSwitcher: React.FC<CopyVariantSwitcherProps> = ({
  variantOverride,
  onCtaClick,
  className = '',
  useAltHeadlines = false,
  currentStep = 'introduction'
}) => {
  // Determine which variant to show, with priority:
  // 1. Component prop override
  // 2. Previously stored variant (for journey consistency)
  // 3. URL parameter
  // 4. Random assignment
  const [variant, setVariant] = useState<Variant>('A'); // Default to A until determined
  const [isDebugVisible, setIsDebugVisible] = useState(false);
  
  useEffect(() => {
    // Check for override prop first
    if (variantOverride && VARIANTS.includes(variantOverride)) {
      setVariant(variantOverride);
      return;
    } 
    
    // Check for previously stored variant
    const storedVariant = getStoredVariant(TEST_ID) as Variant;
    if (storedVariant && VARIANTS.includes(storedVariant as Variant)) {
      setVariant(storedVariant as Variant);
      return;
    }
    
    // Check URL parameters
    const urlVariant = getVariantFromUrl() as Variant;
    if (urlVariant && VARIANTS.includes(urlVariant)) {
      setVariant(urlVariant);
      return;
    }
    
    // Randomly assign - convert readonly array to regular array with spread
    setVariant(getRandomVariant([...VARIANTS]) as Variant);
  }, [variantOverride]);
  
  // Track impression when variant is displayed
  useEffect(() => {
    trackVariantView(TEST_ID, variant);
    storeVariant(TEST_ID, variant);
    
    // Set up debug mode with keyboard shortcut (Alt+Shift+D)
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.altKey && e.shiftKey && e.key === 'D') {
        setIsDebugVisible(prev => !prev);
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [variant]);
  
  // Get the content for the current variant
  const variantContent = VARIANT_CONTENT[variant];
  const headline = useAltHeadlines ? variantContent.altHeadline : variantContent.headline;
  
  // Handler for the CTA button
  const handleCtaClick = () => {
    trackVariantConversion(TEST_ID, variant, 'cta_click');
    logConversionEvent(variant, `${currentStep}_continue`);
    onCtaClick();
  };
  
  return (
    <div className={`variant-switcher ${className}`} data-variant={variant}>
      {isDebugVisible && (
        <div className="debug-overlay">
          <p>A/B Test: {TEST_ID}</p>
          <p>Variant: {variant} ({variant === 'A' ? 'Empowerment' : 'Reward'})</p>
          <p>Current Step: {currentStep}</p>
          <small>Press Alt+Shift+D to hide</small>
        </div>
      )}
      
      <h1 className="headline">{headline}</h1>
      <p className="intro-text">{variantContent.subhead}</p>
      <button 
        className="primary-button" 
        onClick={handleCtaClick}
      >
        {variantContent.cta}
      </button>
    </div>
  );
};

export default CopyVariantSwitcher; 