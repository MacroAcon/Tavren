import React, { useState } from 'react';
import { useAuthStore, notifySuccess, notifyError } from '../stores';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const login = useAuthStore(state => state.login);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Basic validation
    if (!username || !password) {
      notifyError('Please enter both username and password');
      return;
    }
    
    setIsLoading(true);
    
    try {
      // Send login request to the API
      const response = await fetch('/api/auth/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          'username': username,
          'password': password,
        }),
      });
      
      if (!response.ok) {
        notifyError('Failed to log in. Please check your credentials.');
        setIsLoading(false);
        return;
      }
      
      // Parse the response to get the tokens
      const tokens = await response.json();
      
      // Use the login function from the auth store
      login(tokens);
      
      // Notify successful login
      notifySuccess(`Welcome, ${username}!`);
      
    } catch (err) {
      console.error('Login error:', err);
      notifyError('An error occurred during login. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <h2>Log In</h2>
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="username">Username</label>
          <input
            type="text"
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Enter your username"
            disabled={isLoading}
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter your password"
            disabled={isLoading}
          />
        </div>
        
        <button type="submit" className="login-button" disabled={isLoading}>
          {isLoading ? 'Logging in...' : 'Log In'}
        </button>
      </form>
    </div>
  );
};

export default Login; 