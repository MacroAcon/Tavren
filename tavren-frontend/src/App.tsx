import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { useAuth } from './AuthContext';
import Login from './components/Login';
import AgentExchangeHistory from './components/AgentExchangeHistory';
import AgentExchangeDetail from './components/AgentExchangeDetail';

function App() {
  const { isAuthenticated, user, logout } = useAuth();

  return (
    <Router>
      <div className="app-container">
        <header>
          <h1>Tavren Frontend</h1>
          {isAuthenticated && (
            <div className="header-controls">
              <nav>
                <Link to="/">Dashboard</Link>
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
                  <h2>Welcome, {user?.username}!</h2>
                  <p>You are now logged in to the application.</p>
                  {/* Additional authenticated content will go here */}
                </div>
              } />
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