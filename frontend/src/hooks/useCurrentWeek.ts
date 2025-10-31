/**
 * useCurrentWeek Hook
 *
 * Fetches the current week from the backend and updates state
 *
 * Query Configuration:
 * - Query key: ['current-week']
 * - Fetch: GET /api/current-week
 * - refetchInterval: 60000ms (1 minute)
 * - On success: Calls store.setCurrentWeek() if week changed
 *
 * @returns Object containing { data, isLoading, error }
 */

import { useState, useEffect, useRef } from 'react';
import { useWeekStore, Week } from '../store';

export interface CurrentWeekResponse {
  success: boolean;
  current_week: number;
  current_date: string;
  week_details: Week;
}

export interface UseCurrentWeekReturn {
  data: Week | null;
  isLoading: boolean;
  error: string | null;
}

/**
 * Custom hook to fetch current week
 *
 * Refetches every 60 seconds to detect week changes
 * Updates Zustand store when current week changes
 */
export const useCurrentWeek = (): UseCurrentWeekReturn => {
  const store = useWeekStore();
  const [data, setData] = useState<Week | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const fetchCurrentWeek = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const response = await fetch('/api/current-week');

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Failed to fetch current week');
        }

        const result: CurrentWeekResponse = await response.json();

        if (result.success && result.week_details) {
          setData(result.week_details);

          // Only auto-update if no week is manually selected by the user
          // This prevents overriding user selections
          if (store.currentWeek === null && result.current_week) {
            store.setCurrentWeek(result.current_week);
          }
        } else {
          throw new Error('Failed to fetch current week');
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'An unexpected error occurred';
        setError(errorMessage);
        store.setError(errorMessage);
      } finally {
        setIsLoading(false);
      }
    };

    // Initial fetch
    fetchCurrentWeek();

    // Setup interval for 60-second refetch
    intervalRef.current = setInterval(fetchCurrentWeek, 60000);

    // Cleanup
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [store]);

  return {
    data,
    isLoading,
    error,
  };
};

export default useCurrentWeek;
