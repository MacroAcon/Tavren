import React from 'react';
import { useAuth } from './AuthContext';
import Login from './components/Login';

function App() {
  const { isAuthenticated, user, logout } = useAuth();

  return (
    <div className="app-container">
      <header>
        <h1>Tavren Frontend</h1>
        {isAuthenticated && (
          <button onClick={logout} className="logout-button">
            Logout
          </button>
        )}
      </header>

      <main>
        {isAuthenticated ? (
          <div className="welcome-container">
            <h2>Welcome, {user?.username}!</h2>
            <p>You are now logged in to the application.</p>
            {/* Additional authenticated content will go here */}
          </div>
        ) : (
          <Login />
        )}
      </main>
    </div>
  );
}

export default App; 