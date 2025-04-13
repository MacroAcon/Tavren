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
import MobileNavigation from './components/shared/MobileNavigation';
import OfflineIndicator from './components/shared/OfflineIndicator';
import QAHelper from './components/shared/QAHelper';
import { 
  WalletDashboard, 
  PaymentMethodManagement, 
  TransactionHistory, 
  PayoutSettings 
} from './components/wallet';
import OffersPage from './components/offers/OffersPage';
import OfferDetail from './components/offers/OfferDetail';
import ProfilePage from './components/profile';

// Import from our new stores
import { 
  useAuthStore, 
  useOnboardingStore,
  notifyInfo
} from './stores';

import './components/shared/mobile-navigation.css';

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

  // Define components that are still using mock data
  const mockDataComponents = [
    'Offers Feed',
    'ConsentDashboard',
    'TrustVisualization'
  ];

  // Define API versions for different endpoints
  const apiVersions = {
    'users': '1.0',
    'offers': '1.1',
    'wallet': '1.0',
    'consent': '0.9',
    'trust': '0.8'
  };

  return (
    <Router>
      <div className="app-container">
        {/* Desktop Header - Hidden on mobile */}
        <header className="desktop-header">
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
                <Link to="/wallet">Wallet</Link>
                <Link to="/offers">Offers</Link>
                <Link to="/profile">Profile</Link>
              </nav>
              <button onClick={logout} className="logout-button">
                Logout
              </button>
            </div>
          )}
        </header>

        {/* Mobile Navigation - Shows on small screens */}
        {isAuthenticated && isOnboardingCompleted && (
          <MobileNavigation onLogout={logout} />
        )}

        <main className="main-content">
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
                    <div className="dashboard-card" onClick={() => window.location.href = '/wallet'}>
                      <h3>Your Wallet</h3>
                      <p>Manage earnings, payment methods and payouts</p>
                    </div>
                    <div className="dashboard-card" onClick={() => window.location.href = '/offers'}>
                      <h3>Offer Feed</h3>
                      <p>Browse and accept data-sharing offers</p>
                    </div>
                    <div className="dashboard-card" onClick={() => window.location.href = '/profile'}>
                      <h3>Profile & Preferences</h3>
                      <p>Manage your profile, privacy settings, and preferences</p>
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
              
              {/* Wallet Routes */}
              <Route path="/wallet" element={<WalletDashboard />} />
              <Route path="/wallet/payment-methods" element={<PaymentMethodManagement />} />
              <Route path="/wallet/transactions" element={<TransactionHistory />} />
              <Route path="/wallet/payout-settings" element={<PayoutSettings />} />
              
              {/* Offer Routes */}
              <Route path="/offers" element={<OffersPage />} />
              <Route path="/offers/:offerId" element={<OfferDetail />} />
              
              {/* Profile Routes */}
              <Route path="/profile" element={<ProfilePage />} />
            </Routes>
          )}
        </main>

        {/* Notification System */}
        <NotificationSystem />
        
        {/* Offline Indicator */}
        <OfflineIndicator />
        
        {/* QA Helper - Hidden but available in console */}
        <QAHelper 
          mockDataComponents={mockDataComponents}
          apiVersions={apiVersions}
        />
      </div>
    </Router>
  );
}

export default App; 