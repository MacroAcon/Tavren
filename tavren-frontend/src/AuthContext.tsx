import React, { createContext, useState, useContext, ReactNode, useEffect } from 'react';
import jwtDecode from 'jwt-decode'; // Add this dependency with: npm install jwt-decode

// Define the token structure based on your JWT payload
interface JwtToken {
  sub: string; // username is stored in the 'sub' claim
  exp: number; // expiration timestamp
  // Add other claims your token might have
}

// Define user data structure
interface User {
  username: string;
  // Add other user properties
}

interface AuthTokens {
  access_token: string;
  token_type: string;
}

interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  login: (tokens: AuthTokens) => void;
  logout: () => void;
  refreshToken: () => Promise<boolean>;
  getAccessToken: () => string | null;
}

const TOKEN_STORAGE_KEY = 'tavren_auth_tokens';
const USER_STORAGE_KEY = 'tavren_user';

// Create context with undefined default
const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [user, setUser] = useState<User | null>(null);
  const [tokens, setTokens] = useState<AuthTokens | null>(null);

  // Load authentication state from localStorage on mount
  useEffect(() => {
    const storedTokens = localStorage.getItem(TOKEN_STORAGE_KEY);
    const storedUser = localStorage.getItem(USER_STORAGE_KEY);
    
    if (storedTokens && storedUser) {
      const parsedTokens = JSON.parse(storedTokens) as AuthTokens;
      const parsedUser = JSON.parse(storedUser) as User;
      
      // Validate token before restoring session
      if (isTokenValid(parsedTokens.access_token)) {
        setTokens(parsedTokens);
        setUser(parsedUser);
        setIsAuthenticated(true);
      } else {
        // Token is invalid or expired, clear storage
        localStorage.removeItem(TOKEN_STORAGE_KEY);
        localStorage.removeItem(USER_STORAGE_KEY);
      }
    }
  }, []);

  // Check if token is about to expire and set up auto refresh
  useEffect(() => {
    if (!tokens?.access_token) return;
    
    try {
      const decoded = jwtDecode<JwtToken>(tokens.access_token);
      const expiresIn = decoded.exp * 1000 - Date.now(); // Convert to milliseconds
      
      // If token expires in less than 5 minutes (300000ms), refresh it
      if (expiresIn < 300000 && expiresIn > 0) {
        const timeoutId = setTimeout(() => {
          refreshToken();
        }, Math.max(0, expiresIn - 60000)); // Refresh 1 minute before expiry
        
        return () => clearTimeout(timeoutId);
      }
      
      // If token is already expired, try to refresh immediately
      if (expiresIn <= 0) {
        refreshToken();
      }
    } catch (error) {
      console.error('Error decoding token:', error);
      // Token is invalid, log the user out
      logout();
    }
  }, [tokens]);

  // Validate token
  const isTokenValid = (token: string): boolean => {
    if (!token) return false;
    
    try {
      const decoded = jwtDecode<JwtToken>(token);
      // Check if token is expired
      return decoded.exp * 1000 > Date.now(); // Convert to milliseconds
    } catch (error) {
      console.error('Error validating token:', error);
      return false;
    }
  };

  // Extract user info from token
  const getUserFromToken = (token: string): User | null => {
    try {
      const decoded = jwtDecode<JwtToken>(token);
      return {
        username: decoded.sub,
        // Add other user properties as needed
      };
    } catch (error) {
      console.error('Error extracting user from token:', error);
      return null;
    }
  };

  const login = (authTokens: AuthTokens) => {
    // Extract user info from the token
    const extractedUser = getUserFromToken(authTokens.access_token);
    
    if (!extractedUser) {
      console.error('Failed to extract user from token');
      return;
    }
    
    // Save to state
    setTokens(authTokens);
    setUser(extractedUser);
    setIsAuthenticated(true);
    
    // Persist to localStorage
    localStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify(authTokens));
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(extractedUser));
  };

  const logout = () => {
    // Clear state
    setIsAuthenticated(false);
    setUser(null);
    setTokens(null);
    
    // Clear localStorage
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    localStorage.removeItem(USER_STORAGE_KEY);
  };

  const getAccessToken = (): string | null => {
    return tokens?.access_token || null;
  };

  const refreshToken = async (): Promise<boolean> => {
    // Implement token refresh logic based on your backend
    try {
      // Example implementation - adjust based on your API
      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${tokens?.access_token}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Token refresh failed');
      }
      
      const newTokens = await response.json();
      login(newTokens);
      return true;
    } catch (error) {
      console.error('Error refreshing token:', error);
      // If refresh fails, log the user out
      logout();
      return false;
    }
  };

  return (
    <AuthContext.Provider value={{ 
      isAuthenticated, 
      user, 
      login, 
      logout, 
      refreshToken,
      getAccessToken
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}; 