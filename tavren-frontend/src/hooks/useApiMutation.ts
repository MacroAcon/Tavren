import { useState } from 'react';

interface MutationOptions {
  method?: 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  headers?: Record<string, string>;
}

interface MutationResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  mutate: (body: any) => Promise<T | null>;
}

/**
 * Hook for handling API mutations (POST, PUT, PATCH, DELETE)
 */
export function useApiMutation<T>(
  endpoint: string,
  options: MutationOptions = {}
): MutationResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const defaultOptions: MutationOptions = {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  };

  const mutate = async (body: any): Promise<T | null> => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(endpoint, {
        method: defaultOptions.method,
        headers: defaultOptions.headers,
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`);
      }

      const result = await response.json();
      setData(result);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(`Error: ${errorMessage}`);
      console.error('API mutation error:', err);
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { data, loading, error, mutate };
} 