/**
 * useWeeks Hook
 *
 * Fetches weeks for a specific year using TanStack Query
 *
 * Query Configuration:
 * - Query key: ['weeks', year]
 * - Fetch: GET /api/weeks?year={year}&include_metadata=true
 * - staleTime: 5 minutes
 * - cacheTime: 10 minutes
 * - On success: Updates Zustand store with weeks data
 * - On error: Updates Zustand store with error message
 *
 * @param year - The NFL season year (e.g., 2025)
 * @returns Object containing { data, isLoading, error, isSuccess }
 */

import { useState, useEffect } from 'react';
import { useWeekStore, Week } from '../store';

export interface UseWeeksReturn {
  data: Week[] | null;
  isLoading: boolean;
  error: string | null;
  isSuccess: boolean;
}

/**
 * Custom hook to fetch weeks for a specific year
 *
 * Implements basic data fetching with error handling.
 * Note: For production, integrate with TanStack Query (React Query)
 * when available in the project dependencies.
 */
export const useWeeks = (year: number): UseWeeksReturn => {
  const store = useWeekStore();
  const [data, setData] = useState<Week[] | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchWeeks = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const response = await fetch(`/api/weeks?year=${year}&include_metadata=true`);

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || `Failed to fetch weeks for year ${year}`);
        }

        const result = await response.json();

        if (result.success && result.weeks) {
          setData(result.weeks);
          // Update Zustand store on success
          store.setWeeks(result.weeks);
        } else {
          throw new Error(result.error || 'Failed to fetch weeks');
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'An unexpected error occurred';
        setError(errorMessage);
        // Update Zustand store with error
        store.setError(errorMessage);
      } finally {
        setIsLoading(false);
      }
    };

    fetchWeeks();
  }, [year]);

  return {
    data,
    isLoading,
    error,
    isSuccess: !error && data !== null,
  };
};

export default useWeeks;
