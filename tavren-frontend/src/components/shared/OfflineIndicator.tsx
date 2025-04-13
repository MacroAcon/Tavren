import React, { useEffect, useState } from 'react';
import './offline-indicator.css';

const OfflineIndicator: React.FC = () => {
  const [isOffline, setIsOffline] = useState<boolean>(!navigator.onLine);

  useEffect(() => {
    // Event listeners for online/offline status
    const handleOffline = () => setIsOffline(true);
    const handleOnline = () => setIsOffline(false);

    window.addEventListener('offline', handleOffline);
    window.addEventListener('online', handleOnline);

    // Clean up event listeners
    return () => {
      window.removeEventListener('offline', handleOffline);
      window.removeEventListener('online', handleOnline);
    };
  }, []);

  if (!isOffline) {
    return null;
  }

  return (
    <div className="offline-indicator">
      <div className="offline-content">
        <span className="offline-icon">📶</span>
        <span className="offline-text">You're offline. Some features may be limited.</span>
      </div>
    </div>
  );
};

export default OfflineIndicator; 