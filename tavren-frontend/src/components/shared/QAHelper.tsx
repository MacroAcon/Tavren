import React, { useEffect } from 'react';
import { useAuthStore } from '../../stores';
import { API_ENVIRONMENT } from '../../utils/apiClient';

interface QAHelperProps {
  mockDataComponents?: string[];
  apiVersions?: Record<string, string>;
}

/**
 * Developer helper component that logs readiness information to the console
 * and provides a global window object for QA testing.
 * 
 * This component doesn't render anything visible in the UI.
 */
const QAHelper: React.FC<QAHelperProps> = ({ 
  mockDataComponents = [],
  apiVersions = {}
}) => {
  const isAuthenticated = useAuthStore(state => state.isAuthenticated);
  const user = useAuthStore(state => state.user);
  
  useEffect(() => {
    // Create a global object for QA testing
    const qaHelper = {
      isMockData: mockDataComponents.length > 0,
      mockDataComponents,
      isAuthenticated,
      user,
      apiEnvironment: API_ENVIRONMENT,
      apiVersions,
      getDevelopmentInfo: () => {
        console.group('🔍 Tavren QA Helper Info');
        console.log(`Auth Status: ${isAuthenticated ? 'Authenticated ✅' : 'Not Authenticated ⚠️'}`);
        console.log(`User: ${user ? user.username : 'None'}`);
        console.log(`API Environment: ${API_ENVIRONMENT.toUpperCase()}`);
        
        if (mockDataComponents.length > 0) {
          console.log('⚠️ Components still using mock data:');
          mockDataComponents.forEach(component => console.log(`  - ${component}`));
        } else {
          console.log('✅ All components using real API data');
        }
        
        if (Object.keys(apiVersions).length > 0) {
          console.log('API Versions:');
          Object.entries(apiVersions).forEach(([key, version]) => {
            console.log(`  - ${key}: v${version}`);
          });
        }
        
        console.groupEnd();
        return true;
      }
    };
    
    // Add to window for easy console access
    (window as any).__TAVREN_QA__ = qaHelper;
    
    // Log on mount in development
    if (import.meta.env.DEV) {
      qaHelper.getDevelopmentInfo();
      console.log('ℹ️ QA Helper available at window.__TAVREN_QA__');
    }
    
    return () => {
      // Cleanup
      if ((window as any).__TAVREN_QA__) {
        delete (window as any).__TAVREN_QA__;
      }
    };
  }, [isAuthenticated, user, mockDataComponents, apiVersions]);
  
  // This component doesn't render anything
  return null;
};

export default QAHelper; 