/**
 * useWeekMetadata Hook
 *
 * Fetches detailed metadata for a specific week
 *
 * Query Configuration:
 * - Query key: ['week-metadata', weekId]
 * - Fetch: GET /api/weeks/{weekId}/metadata
 * - enabled: !!weekId (only fetch if weekId is provided)
 *
 * @param weekId - The week ID to fetch metadata for (optional)
 * @returns Object containing { data, isLoading, error }
 */

import { useState, useEffect } from 'react';
import { Week, WeekMetadata } from '../store';

export interface WeekMetadataResponse {
  success: boolean;
  week_id: number;
  metadata: WeekMetadata & {
    season: number;
    week_number: number;
    nfl_slate_date: string;
    is_locked: boolean;
    locked_at: string | null;
  };
}

export interface UseWeekMetadataReturn {
  data: (WeekMetadata & {
    season: number;
    week_number: number;
    nfl_slate_date: string;
    is_locked: boolean;
    locked_at: string | null;
  }) | null;
  isLoading: boolean;
  error: string | null;
}

/**
 * Custom hook to fetch detailed week metadata
 *
 * Only fetches when weekId is provided (enabled: !!weekId)
 * Useful for getting detailed metadata for a specific week
 */
export const useWeekMetadata = (weekId?: number): UseWeekMetadataReturn => {
  const [data, setData] = useState<(WeekMetadata & {
    season: number;
    week_number: number;
    nfl_slate_date: string;
    is_locked: boolean;
    locked_at: string | null;
  }) | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Only fetch if weekId is provided (enabled: !!weekId)
    if (!weekId) {
      setData(null);
      setError(null);
      return;
    }

    const fetchMetadata = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const response = await fetch(`/api/weeks/${weekId}/metadata`);

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || `Failed to fetch metadata for week ${weekId}`);
        }

        const result: WeekMetadataResponse = await response.json();

        if (result.success && result.metadata) {
          setData(result.metadata);
        } else {
          throw new Error('Failed to fetch week metadata');
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'An unexpected error occurred';
        setError(errorMessage);
      } finally {
        setIsLoading(false);
      }
    };

    fetchMetadata();
  }, [weekId]);

  return {
    data,
    isLoading,
    error,
  };
};

export default useWeekMetadata;
