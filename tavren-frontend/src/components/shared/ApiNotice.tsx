import React from 'react';
import './api-notice.css';

interface ApiNoticeProps {
  component: string;
  mockData?: boolean;
}

/**
 * A developer-only component that indicates a feature is using mock data
 * and needs real API integration.
 * 
 * This is toggled via a localStorage developer mode setting
 */
const ApiNotice: React.FC<ApiNoticeProps> = ({ component, mockData = true }) => {
  const [isDevMode, setIsDevMode] = React.useState<boolean>(false);

  React.useEffect(() => {
    // Check if developer mode is enabled in localStorage
    const devMode = localStorage.getItem('tavren-dev-mode') === 'true';
    setIsDevMode(devMode);
    
    // Add keyboard shortcut to toggle dev mode (Ctrl+Shift+D)
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'D') {
        const newDevMode = !devMode;
        localStorage.setItem('tavren-dev-mode', String(newDevMode));
        setIsDevMode(newDevMode);
        e.preventDefault();
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);
  
  if (!isDevMode) {
    return null;
  }
  
  return (
    <div className="api-notice">
      <span className="api-notice-badge">DEV</span>
      <div className="api-notice-content">
        <strong>{component}</strong>: 
        {mockData 
          ? ' Using mock data. API integration needed.' 
          : ' Ready for API integration.'
        }
      </div>
    </div>
  );
};

export default ApiNotice; 