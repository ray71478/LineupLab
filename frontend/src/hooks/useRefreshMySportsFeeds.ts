/**
 * Hook for triggering manual MySportsFeeds API refresh.
 *
 * Provides functionality to refresh Vegas lines, injuries, and defensive stats
 * from the MySportsFeeds API on-demand from the UI.
 */

import { useState, useCallback } from 'react';

export interface RefreshStats {
  fetched: number;
  stored: number;
  errors: number;
}

export interface RefreshResult {
  success: boolean;
  start_time?: string;
  end_time?: string;
  duration_seconds?: number;
  injuries?: RefreshStats;
  games?: RefreshStats;
  team_stats?: RefreshStats;
  gamelogs?: RefreshStats;
  espn_opponents?: {
    checked: number;
    updated: number;
    errors: number;
  };
  errors?: string[];
  error?: string;
  message?: string;
}

export interface UseRefreshMySportsFeedsReturn {
  isLoading: boolean;
  error: string | null;
  success: boolean;
  result: RefreshResult | null;
  refresh: () => Promise<RefreshResult | null>;
  reset: () => void;
}

export const useRefreshMySportsFeeds = (): UseRefreshMySportsFeedsReturn => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [result, setResult] = useState<RefreshResult | null>(null);

  const refresh = useCallback(async (): Promise<RefreshResult | null> => {
    // Reset states
    setIsLoading(true);
    setError(null);
    setSuccess(false);
    setResult(null);

    try {
      const response = await fetch('/api/refresh/mysportsfeeds', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data: RefreshResult = await response.json();

      if (!response.ok) {
        // Handle error response
        const errorMessage = data.error || data.message || 'Unknown error during refresh';
        setError(errorMessage);
        setSuccess(false);
        setResult(data);
        return data;
      }

      // Success
      if (data.success) {
        setSuccess(true);
        setError(null);
        setResult(data);
        return data;
      } else {
        // API returned success:false
        const errorMessage = data.error || data.message || 'Refresh failed';
        setError(errorMessage);
        setSuccess(false);
        setResult(data);
        return data;
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Network error during refresh';
      setError(errorMessage);
      setSuccess(false);
      setResult(null);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setIsLoading(false);
    setError(null);
    setSuccess(false);
    setResult(null);
  }, []);

  return {
    isLoading,
    error,
    success,
    result,
    refresh,
    reset,
  };
};
