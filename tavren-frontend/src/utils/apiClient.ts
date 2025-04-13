import axios from 'axios';
import { useAuthStore } from '../stores/authStore';
import { notifyError, notifyWarning } from '../stores/notificationStore';
import { handleApiError, parseApiError, ErrorType } from './errorHandling';

// Define types locally since they might not be exported directly in your axios version
type AxiosInstance = typeof axios;
type AxiosResponse<T = any> = {
  data: T;
  status: number;
  statusText: string;
  headers: any;
  config: any;
};
type AxiosError = {
  isAxiosError: boolean;
  response?: {
    status: number;
    data?: any;
    headers?: any;
  };
  request?: any;
  config?: any;
  message: string;
};
type InternalAxiosRequestConfig = {
  headers: any;
  [key: string]: any;
};

// Use environment variables for base URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
// Get environment for readiness flags
export const API_ENVIRONMENT = import.meta.env.MODE || 'development';

// Create axios instance with default config
const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to attach auth token
axiosInstance.interceptors.request.use(
  (config: any) => {
    const token = useAuthStore.getState().getAccessToken();
    if (token) {
      config.headers = {
        ...config.headers,
        Authorization: `Bearer ${token}`,
      };
    }
    return config;
  },
  (error: any) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle token expiry
axiosInstance.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: any) => {
    const originalRequest = error.config as any & { _retry?: boolean };
    
    // Handle token expiry (401 unauthorized)
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      // Show warning to the user
      notifyWarning('Your session is being refreshed...');
      
      // Try to refresh the token
      const refreshSuccess = await useAuthStore.getState().refreshToken();
      
      // If refresh was successful, retry the original request
      if (refreshSuccess) {
        const token = useAuthStore.getState().getAccessToken();
        originalRequest.headers.Authorization = `Bearer ${token}`;
        return axiosInstance(originalRequest);
      } else {
        // If refresh failed, redirect to login
        notifyWarning('Your session has expired. Please login again.');
        window.location.href = '/login';
      }
    }
    
    // Format error for consistent handling
    return Promise.reject(formatError(error));
  }
);

// Helper to format errors consistently
const formatError = (error: any) => {
  const response = error.response;
  return {
    status: response?.status,
    message: response?.data?.detail || error.message || 'An unknown error occurred',
    data: response?.data,
    original: error,
  };
};

// Log API calls in development mode
const logApiCall = (method: string, url: string, data?: any) => {
  if (import.meta.env.MODE !== 'production') {
    console.log(`🌐 API ${method} ${url}`, data || '');
  }
};

// CRUD helper methods with retry functionality
export const apiClient = {
  // GET request
  get: async <T>(url: string, config?: any, retry = 1): Promise<T> => {
    logApiCall('GET', url);
    try {
      const response = await axiosInstance.get<T>(url, config);
      return response.data;
    } catch (error: any) {
      // Only retry for network errors, not for 4xx or 5xx responses
      if (retry > 0 && (!error.response || error.response.status >= 500)) {
        // Wait before retrying (exponential backoff)
        const waitTime = 1000 * Math.pow(2, 3 - retry);
        await new Promise(resolve => setTimeout(resolve, waitTime));
        return apiClient.get<T>(url, config, retry - 1);
      }
      
      // Use our error handling system
      handleApiError(error, `loading ${url.split('/').pop()}`, { silent: false });
      throw error;
    }
  },
  
  // POST request
  post: async <T>(url: string, data?: any, config?: any, retry = 1): Promise<T> => {
    logApiCall('POST', url, data);
    try {
      const response = await axiosInstance.post<T>(url, data, config);
      return response.data;
    } catch (error: any) {
      if (retry > 0 && (!error.response || error.response.status >= 500)) {
        const waitTime = 1000 * Math.pow(2, 3 - retry);
        await new Promise(resolve => setTimeout(resolve, waitTime));
        return apiClient.post<T>(url, data, config, retry - 1);
      }
      
      handleApiError(error, `saving to ${url.split('/').pop()}`, { silent: false });
      throw error;
    }
  },
  
  // PUT request
  put: async <T>(url: string, data?: any, config?: any, retry = 1): Promise<T> => {
    logApiCall('PUT', url, data);
    try {
      const response = await axiosInstance.put<T>(url, data, config);
      return response.data;
    } catch (error: any) {
      if (retry > 0 && (!error.response || error.response.status >= 500)) {
        const waitTime = 1000 * Math.pow(2, 3 - retry);
        await new Promise(resolve => setTimeout(resolve, waitTime));
        return apiClient.put<T>(url, data, config, retry - 1);
      }
      
      handleApiError(error, `updating ${url.split('/').pop()}`, { silent: false });
      throw error;
    }
  },
  
  // PATCH request
  patch: async <T>(url: string, data?: any, config?: any, retry = 1): Promise<T> => {
    logApiCall('PATCH', url, data);
    try {
      const response = await axiosInstance.patch<T>(url, data, config);
      return response.data;
    } catch (error: any) {
      if (retry > 0 && (!error.response || error.response.status >= 500)) {
        const waitTime = 1000 * Math.pow(2, 3 - retry);
        await new Promise(resolve => setTimeout(resolve, waitTime));
        return apiClient.patch<T>(url, data, config, retry - 1);
      }
      
      handleApiError(error, `updating ${url.split('/').pop()}`, { silent: false });
      throw error;
    }
  },
  
  // DELETE request
  delete: async <T>(url: string, config?: any, retry = 1): Promise<T> => {
    logApiCall('DELETE', url);
    try {
      const response = await axiosInstance.delete<T>(url, config);
      return response.data;
    } catch (error: any) {
      if (retry > 0 && (!error.response || error.response.status >= 500)) {
        const waitTime = 1000 * Math.pow(2, 3 - retry);
        await new Promise(resolve => setTimeout(resolve, waitTime));
        return apiClient.delete<T>(url, config, retry - 1);
      }
      
      handleApiError(error, `deleting ${url.split('/').pop()}`, { silent: false });
      throw error;
    }
  }
};

export default apiClient; 