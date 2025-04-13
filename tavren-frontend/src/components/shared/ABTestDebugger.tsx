import React, { useEffect, useState } from 'react';
import { getStoredVariant } from '../../utils/analytics';
import './ab-test-debugger.css';

interface ABTestDebuggerProps {
  /**
   * The test ID to debug
   */
  testId?: string;
}

/**
 * A floating debugger component that shows A/B test information
 * Only visible in development builds and when toggled with Alt+Shift+D
 */
const ABTestDebugger: React.FC<ABTestDebuggerProps> = ({
  testId = 'onboarding-value-proposition'
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [variant, setVariant] = useState<string | null>(null);
  const [logs, setLogs] = useState<any[]>([]);
  
  useEffect(() => {
    // Get the stored variant
    const storedVariant = getStoredVariant(testId);
    setVariant(storedVariant);
    
    // Set up keyboard listener
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.altKey && e.shiftKey && e.key === 'D') {
        setIsVisible(prev => !prev);
      }
    };
    
    // Check if we're in development mode
    // We'll assume we're in development by default for this mock version
    const isDev = true; // In a real app with proper build config this would use process.env.NODE_ENV
    
    if (isDev) {
      window.addEventListener('keydown', handleKeyDown);
    }
    
    // Clean up
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [testId]);
  
  // Listen to console logs to capture analytics events
  useEffect(() => {
    if (!isVisible) return;
    
    const originalConsoleLog = console.log;
    const logEntries: any[] = [];
    
    // Override console.log to capture analytics events
    console.log = function(...args) {
      originalConsoleLog.apply(console, args);
      
      // Check if this is an analytics log
      if (typeof args[0] === 'string' && args[0].includes('[Analytics]')) {
        logEntries.push(args);
        setLogs([...logEntries]);
      }
    };
    
    // Restore console.log on cleanup
    return () => {
      console.log = originalConsoleLog;
    };
  }, [isVisible]);
  
  if (!isVisible) return null;
  
  return (
    <div className="ab-test-debugger">
      <div className="debugger-header">
        <h3>A/B Test Debugger</h3>
        <button onClick={() => setIsVisible(false)}>Close</button>
      </div>
      
      <div className="debugger-content">
        <div className="test-info">
          <p><strong>Test ID:</strong> {testId}</p>
          <p><strong>Active Variant:</strong> {variant || 'None'}</p>
        </div>
        
        <div className="event-logs">
          <h4>Event Log</h4>
          {logs.length === 0 ? (
            <p className="no-logs">No analytics events captured yet.</p>
          ) : (
            <ul>
              {logs.map((log, index) => (
                <li key={index}>
                  <code>{log[0]}</code>
                  <pre>{JSON.stringify(log[1], null, 2)}</pre>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
      
      <div className="debugger-footer">
        <small>Press Alt+Shift+D to toggle debugger • Development Mode</small>
      </div>
    </div>
  );
};

export default ABTestDebugger; 