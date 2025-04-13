import axios from 'axios';
// Define our own AxiosError type if it's not available from axios
type AxiosError = {
  isAxiosError: boolean;
  response?: {
    status: number;
    data?: any;
  };
};

import { notifyError, notifyWarning, useAuthStore } from '../stores';
import apiClient from './apiClient';

// Error types for better handling
export enum ErrorType {
  NETWORK = 'network',
  AUTH = 'auth',
  VALIDATION = 'validation',
  SERVER = 'server',
  UNKNOWN = 'unknown'
}

// Interface for parsed API errors
export interface ApiError {
  type: ErrorType;
  message: string;
  status?: number;
  data?: any;
  retry?: () => Promise<any>;
}

// Define the notification action interface 
interface NotificationAction {
  label: string;
  onClick: () => void;
}

// Define the notification options that include action
interface NotificationOptions {
  duration?: number;
  action?: NotificationAction;
}

/**
 * Parses an API error into a standardized format
 */
export const parseApiError = (error: any, originalRequest?: () => Promise<any>): ApiError => {
  // If already parsed, return as is
  if (error?.type && Object.values(ErrorType).includes(error.type)) {
    return error as ApiError;
  }

  // Default error
  const apiError: ApiError = {
    type: ErrorType.UNKNOWN,
    message: 'An unexpected error occurred',
    retry: originalRequest
  };

  // Handle axios errors - check for common axios error properties
  if (error && error.isAxiosError) {
    const status = error.response?.status;
    apiError.status = status;
    apiError.data = error.response?.data;

    // Network errors
    if (!error.response) {
      apiError.type = ErrorType.NETWORK;
      apiError.message = 'Network error. Please check your connection and try again.';
    } 
    // Auth errors (401 Unauthorized)
    else if (status === 401) {
      apiError.type = ErrorType.AUTH;
      apiError.message = 'Your session has expired. Please login again.';
    } 
    // Validation errors (400 Bad Request)
    else if (status === 400) {
      apiError.type = ErrorType.VALIDATION;
      apiError.message = error.response.data?.detail || 'Invalid data provided. Please check your inputs.';
    }
    // Forbidden (403)
    else if (status === 403) {
      apiError.type = ErrorType.AUTH;
      apiError.message = 'You do not have permission to perform this action.';
    }
    // Not Found (404)
    else if (status === 404) {
      apiError.type = ErrorType.SERVER;
      apiError.message = 'The requested resource was not found.';
    }
    // Server errors (500+)
    else if (status && status >= 500) {
      apiError.type = ErrorType.SERVER;
      apiError.message = 'Server error. Please try again later.';
    }
  }

  return apiError;
};

/**
 * Determines if an unknown error is an Axios error
 */
function isAxiosError(error: unknown): error is AxiosError {
  return Boolean(error && typeof error === 'object' && 'isAxiosError' in error);
}

/**
 * Handles API errors with appropriate notifications and actions
 */
export const handleApiError = async (
  error: any, 
  context: string = 'operation',
  options: {
    silent?: boolean;
    retryFn?: () => Promise<any>;
    showRetry?: boolean;
  } = {}
): Promise<ApiError> => {
  const { silent = false, retryFn, showRetry = true } = options;
  
  // Parse the error
  const parsedError = parseApiError(error, retryFn);
  
  // Handle based on error type
  switch (parsedError.type) {
    case ErrorType.AUTH:
      // If auth error, log out user and redirect
      if (!silent) {
        notifyWarning(`Session expired. Please login again.`);
      }
      
      // Try to refresh token first
      const authStore = useAuthStore.getState();
      try {
        const refreshed = await authStore.refreshToken();
        if (refreshed && retryFn) {
          return { ...parsedError, retry: retryFn }; // Return with retry function
        }
      } catch (refreshError) {
        // If refresh fails, logout
        authStore.logout();
        window.location.href = '/login';
      }
      break;
    
    case ErrorType.NETWORK:
      if (!silent) {
        if (showRetry && retryFn) {
          // Use a simpler notification without action for now
          notifyWarning(`Network error during ${context}. Please check your connection.`);
          // TODO: Add retry action when notification system supports it
        } else {
          notifyWarning(`Network error during ${context}. Please check your connection.`);
        }
      }
      break;
    
    case ErrorType.VALIDATION:
      if (!silent) {
        notifyError(`Validation error: ${parsedError.message}`);
      }
      break;
    
    case ErrorType.SERVER:
      if (!silent) {
        if (showRetry && retryFn) {
          // Use a simpler notification without action for now
          notifyError(`Server error during ${context}. Please try again later.`);
          // TODO: Add retry action when notification system supports it
        } else {
          notifyError(`Server error during ${context}. Please try again later.`);
        }
      }
      break;
    
    default:
      if (!silent) {
        notifyError(`Error during ${context}: ${parsedError.message}`);
      }
      break;
  }
  
  return parsedError;
};

/**
 * Custom hook for making API calls with automatic error handling
 */
export const useApiWithErrorHandling = () => {
  const callApi = async <T>(
    apiCall: () => Promise<T>,
    context: string = 'API request',
    options: {
      silent?: boolean;
      retries?: number;
      retryDelay?: number;
    } = {}
  ): Promise<T | null> => {
    const { silent = false, retries = 1, retryDelay = 1000 } = options;
    
    let attempts = 0;
    
    while (attempts <= retries) {
      try {
        // If not first attempt, delay before retry
        if (attempts > 0) {
          await new Promise(resolve => setTimeout(resolve, retryDelay));
        }
        
        attempts++;
        return await apiCall();
      } catch (error: unknown) {
        // On last attempt, handle error with notifications
        if (attempts > retries) {
          const retryFn = retries > 0 ? () => callApi(apiCall, context, options) : undefined;
          await handleApiError(error, context, { silent, retryFn });
        }
        
        // If auth error, don't retry (it will be handled by the error handler)
        if (isAxiosError(error) && error.response?.status === 401) {
          break;
        }
      }
    }
    
    return null;
  };
  
  return { callApi };
};

// Note: This function is commented out since the current apiClient doesn't support interceptors.
// When using a full axios instance, this can be enabled.
/*
export const setupApiErrorInterceptors = () => {
  // This requires a full axios instance, not just the simplified API client
  if (typeof apiClient.interceptors === 'undefined') {
    console.warn('API client does not support interceptors');
    return;
  }
  
  apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
      // Handle 401 errors globally
      if (error.response?.status === 401) {
        const authStore = useAuthStore.getState();
        
        // Try to refresh the token
        try {
          const refreshed = await authStore.refreshToken();
          if (refreshed) {
            // Retry the original request with new token
            const originalRequest = error.config;
            return apiClient(originalRequest);
          }
        } catch (refreshError) {
          // If refresh fails, logout
          authStore.logout();
          window.location.href = '/login';
        }
      }
      
      return Promise.reject(error);
    }
  );
};
*/ 