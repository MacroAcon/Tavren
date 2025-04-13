import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Login from './components/Login';
import AgentExchangeHistory from './components/AgentExchangeHistory';
import AgentExchangeDetail from './components/AgentExchangeDetail';
import ConsentDashboard from './components/ConsentDashboard';
import AgentInteractionInterface from './components/AgentInteractionInterface';
import DataPackageHistory from './components/DataPackageHistory';
import TrustVisualization from './components/TrustVisualization';
import OnboardingFlow from './components/onboarding/OnboardingFlow';
import NotificationSystem from './components/shared/NotificationSystem';

// Import from our new stores
import { 
  useAuthStore, 
  useOnboardingStore,
  notifyInfo
} from './stores';

function App() {
  // Use auth store instead of AuthContext
  const isAuthenticated = useAuthStore(state => state.isAuthenticated);
  const user = useAuthStore(state => state.user);
  const logout = useAuthStore(state => state.logout);

  // Use onboarding store instead of local state
  const isOnboardingCompleted = useOnboardingStore(state => state.isCompleted);
  const setOnboardingCompleted = useOnboardingStore(state => state.setCompleted);

  // This effect runs once on mount, you could add onboarding completion logic here if needed
  useEffect(() => {
    // Example notification when the app loads
    if (isAuthenticated) {
      notifyInfo('Welcome back to Tavren!');
    }
  }, [isAuthenticated]);

  const handleOnboardingComplete = () => {
    setOnboardingCompleted(true);
    notifyInfo('Onboarding completed successfully!');
  };

  // Default ID for testing or when user is not fully loaded
  const defaultUserId = 'user1';
  const userId = user?.username || defaultUserId;

  return (
    <Router>
      <div className="app-container">
        <header>
          <h1>Tavren Data Management</h1>
          {isAuthenticated && isOnboardingCompleted && (
            <div className="header-controls">
              <nav>
                <Link to="/">Dashboard</Link>
                <Link to="/consent">Consent</Link>
                <Link to="/agent-interactions">Agent Interactions</Link>
                <Link to="/data-packages">Data Packages</Link>
                <Link to="/trust">Trust Visualizer</Link>
                <Link to="/agent-exchanges">Agent Exchanges</Link>
              </nav>
              <button onClick={logout} className="logout-button">
                Logout
              </button>
            </div>
          )}
        </header>

        <main>
          {!isAuthenticated ? (
            <Login />
          ) : !isOnboardingCompleted ? (
            <OnboardingFlow onComplete={handleOnboardingComplete} />
          ) : (
            <Routes>
              <Route path="/" element={
                <div className="welcome-container">
                  <h2>Welcome to Tavren Data Control Center</h2>
                  <p>Your personal data control and visualization dashboard.</p>
                  <div className="dashboard-cards">
                    <div className="dashboard-card" onClick={() => window.location.href = '/consent'}>
                      <h3>Consent Dashboard</h3>
                      <p>Manage your active data consents and permissions</p>
                    </div>
                    <div className="dashboard-card" onClick={() => window.location.href = '/agent-interactions'}>
                      <h3>Agent Interactions</h3>
                      <p>Respond to data requests from AI agents</p>
                    </div>
                    <div className="dashboard-card" onClick={() => window.location.href = '/data-packages'}>
                      <h3>Data Packages</h3>
                      <p>View history of your shared data packages</p>
                    </div>
                    <div className="dashboard-card" onClick={() => window.location.href = '/trust'}>
                      <h3>Trust Visualization</h3>
                      <p>Explore buyer trust metrics and privacy implications</p>
                    </div>
                  </div>
                </div>
              } />
              <Route path="/consent" element={<ConsentDashboard userId={userId} />} />
              <Route path="/agent-interactions" element={<AgentInteractionInterface userId={userId} />} />
              <Route path="/data-packages" element={<DataPackageHistory userId={userId} />} />
              <Route path="/trust" element={<TrustVisualization userId={userId} />} />
              <Route path="/agent-exchanges" element={<AgentExchangeHistory userId={userId} />} />
              <Route path="/agent-exchanges/:exchangeId" element={<AgentExchangeDetail />} />
              <Route path="/onboarding" element={<OnboardingFlow onComplete={handleOnboardingComplete} />} />
            </Routes>
          )}
        </main>

        {/* Notification System */}
        <NotificationSystem />
      </div>
    </Router>
  );
}

export default App; 