import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { jwtDecode } from 'jwt-decode';

// Define the token structure based on your JWT payload
interface JwtToken {
  sub: string; // username is stored in the 'sub' claim
  exp: number; // expiration timestamp
  // Add other claims your token might have
}

// Define user data structure
export interface User {
  username: string;
  // Add other user properties as needed
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
}

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  tokens: AuthTokens | null;
  login: (tokens: AuthTokens) => void;
  logout: () => void;
  refreshToken: () => Promise<boolean>;
  getAccessToken: () => string | null;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      isAuthenticated: false,
      user: null,
      tokens: null,

      login: (authTokens: AuthTokens) => {
        // Extract user info from the token
        const extractedUser = getUserFromToken(authTokens.access_token);
        
        if (!extractedUser) {
          console.error('Failed to extract user from token');
          return;
        }
        
        // Update state
        set({
          tokens: authTokens,
          user: extractedUser,
          isAuthenticated: true
        });
      },

      logout: () => {
        // Clear state
        set({
          isAuthenticated: false,
          user: null,
          tokens: null
        });
      },

      getAccessToken: () => {
        const state = get();
        return state.tokens?.access_token || null;
      },

      refreshToken: async () => {
        const state = get();
        // Implement token refresh logic based on your backend
        try {
          // Example implementation - adjust based on your API
          const response = await fetch('/api/auth/refresh', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${state.tokens?.access_token}`
            }
          });
          
          if (!response.ok) {
            throw new Error('Token refresh failed');
          }
          
          const newTokens = await response.json();
          get().login(newTokens);
          return true;
        } catch (error) {
          console.error('Error refreshing token:', error);
          // If refresh fails, log the user out
          get().logout();
          return false;
        }
      }
    }),
    {
      name: 'tavren-auth-storage', // name of the item in localStorage
      partialize: (state) => ({ 
        isAuthenticated: state.isAuthenticated, 
        user: state.user, 
        tokens: state.tokens 
      }), // only store these fields
    }
  )
);

// Helper functions

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

// Selector functions for common state access patterns
export const selectIsAuthenticated = (state: AuthState) => state.isAuthenticated;
export const selectUser = (state: AuthState) => state.user;
export const selectUsername = (state: AuthState) => state.user?.username; 