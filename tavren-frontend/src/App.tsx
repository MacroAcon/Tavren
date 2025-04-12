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

function App() {
  const { isAuthenticated, user, logout } = useAuth();

  return (
    <Router>
      <div className="app-container">
        <header>
          <h1>Tavren Data Management</h1>
          {isAuthenticated && (
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
          {isAuthenticated ? (
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
              <Route path="/consent" element={<ConsentDashboard userId={user?.id || 'user1'} />} />
              <Route path="/agent-interactions" element={<AgentInteractionInterface userId={user?.id || 'user1'} />} />
              <Route path="/data-packages" element={<DataPackageHistory userId={user?.id || 'user1'} />} />
              <Route path="/trust" element={<TrustVisualization userId={user?.id || 'user1'} />} />
              <Route path="/agent-exchanges" element={<AgentExchangeHistory userId={user?.id || 'user1'} />} />
              <Route path="/agent-exchanges/:exchangeId" element={<AgentExchangeDetail />} />
            </Routes>
          ) : (
            <Login />
          )}
        </main>
      </div>
    </Router>
  );
}

export default App; 