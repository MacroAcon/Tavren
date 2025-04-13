import React from 'react';
import { useAuthStore } from '../../stores';
import { API_ENVIRONMENT } from '../../utils/apiClient';
import './api-notice.css';

interface ApiNoticeProps {
  component: string;
  mockData?: boolean;
  apiVersion?: string;
}

/**
 * A developer-only component that indicates feature status:
 * - If it's using mock data or real API
 * - Current auth status
 * - API environment (dev/prod)
 * 
 * This is toggled via a localStorage developer mode setting
 * or using the keyboard shortcut Ctrl+Shift+D
 */
const ApiNotice: React.FC<ApiNoticeProps> = ({ 
  component, 
  mockData = true,
  apiVersion
}) => {
  const [isDevMode, setIsDevMode] = React.useState<boolean>(false);
  const isAuthenticated = useAuthStore(state => state.isAuthenticated);
  const user = useAuthStore(state => state.user);
  
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
        console.log(`Developer Mode: ${newDevMode ? 'ON' : 'OFF'}`);
        logDevInfo();
        e.preventDefault();
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);
  
  // Log development info to console
  const logDevInfo = () => {
    console.group('🔍 Tavren Debug Info');
    console.log(`Component: ${component}`);
    console.log(`Mock Data: ${mockData ? 'YES ⚠️' : 'NO ✅'}`);
    console.log(`Auth Status: ${isAuthenticated ? 'Authenticated ✅' : 'Not Authenticated ⚠️'}`);
    console.log(`User: ${user ? user.username : 'None'}`);
    console.log(`API Environment: ${API_ENVIRONMENT.toUpperCase()}`);
    console.log(`API Version: ${apiVersion || 'Not specified'}`);
    console.groupEnd();
  };
  
  if (!isDevMode) {
    return null;
  }
  
  return (
    <div className="api-notice">
      <span className="api-notice-badge">DEV</span>
      <div className="api-notice-content">
        <div><strong>{component}</strong></div>
        <div className="api-notice-details">
          <div className={mockData ? 'status-warning' : 'status-success'}>
            {mockData ? '⚠️ Mock Data' : '✅ Real API'}
          </div>
          <div className={isAuthenticated ? 'status-success' : 'status-warning'}>
            {isAuthenticated ? '✅ Auth OK' : '⚠️ No Auth'}
          </div>
          <div className="api-env">
            ENV: {API_ENVIRONMENT}
          </div>
          {apiVersion && <div className="api-version">v{apiVersion}</div>}
        </div>
      </div>
      <button 
        onClick={logDevInfo} 
        className="api-notice-info-btn" 
        title="Log debug info to console"
      >
        ℹ️
      </button>
    </div>
  );
};

export default ApiNotice; 