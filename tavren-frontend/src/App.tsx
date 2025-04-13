import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { useAuth } from './AuthContext';
import Login from './components/Login';
import AgentExchangeHistory from './components/AgentExchangeHistory';
import AgentExchangeDetail from './components/AgentExchangeDetail';
import ConsentDashboard from './components/ConsentDashboard';
import AgentInteractionInterface from './components/AgentInteractionInterface';
import DataPackageHistory from './components/DataPackageHistory';
import TrustVisualization from './components/TrustVisualization';
import OnboardingFlow from './components/onboarding/OnboardingFlow';

function App() {
  const { isAuthenticated, user, logout } = useAuth();

  // State to track if user has completed onboarding
  const [hasCompletedOnboarding, setHasCompletedOnboarding] = React.useState(() => {
    // Check localStorage to see if user has completed onboarding
    return localStorage.getItem('onboardingCompleted') === 'true';
  });

  const handleOnboardingComplete = () => {
    localStorage.setItem('onboardingCompleted', 'true');
    setHasCompletedOnboarding(true);
  };

  // Default ID for testing or when user is not fully loaded
  const defaultUserId = 'user1';
  const userId = user?.username || defaultUserId;

  return (
    <Router>
      <div className="app-container">
        <header>
          <h1>Tavren Data Management</h1>
          {isAuthenticated && hasCompletedOnboarding && (
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
          ) : !hasCompletedOnboarding ? (
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
      </div>
    </Router>
  );
}

export default App; 