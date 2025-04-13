import { useState } from 'react';
import { useAuthStore, AuthTokens } from '../stores/authStore';
import apiClient from '../utils/apiClient';

interface LoginCredentials {
  username: string;
  password: string;
}

interface UseLoginReturn {
  login: (credentials: LoginCredentials) => Promise<boolean>;
  logout: () => void;
  isLoading: boolean;
  error: string | null;
}

/**
 * Hook for managing user authentication
 * @returns Authentication utilities and state
 */
export const useLogin = (): UseLoginReturn => {
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const { login: storeLogin, logout: storeLogout } = useAuthStore();

  const login = async (credentials: LoginCredentials): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Format the request body for backend compatibility
      // FastAPI expects OAuth2 format for login
      const formData = new URLSearchParams();
      formData.append('username', credentials.username);
      formData.append('password', credentials.password);
      
      // Call the login endpoint
      const response = await apiClient.post<AuthTokens>('/auth/token', formData.toString(), {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      
      // Store the tokens in auth store
      storeLogin(response);
      
      setIsLoading(false);
      return true;
    } catch (err: any) {
      setIsLoading(false);
      setError(err.message || 'Login failed. Please check your credentials.');
      return false;
    }
  };

  const logout = () => {
    storeLogout();
  };

  return { login, logout, isLoading, error };
};

export default useLogin; 