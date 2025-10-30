/**
 * useImportIntegration Hook
 *
 * Handles integration between Data Import System and Week Management.
 * When an import completes successfully:
 * 1. Locks the week via PUT /api/weeks/{week_id}/lock
 * 2. Updates the Zustand store with the locked week
 * 3. Shows visual feedback (green checkmark)
 *
 * Also handles import status updates:
 * 1. Updates import status via PUT /api/weeks/{id}/import-status
 * 2. Refreshes week data with new import status
 */

import { useState, useCallback } from 'react';
import { useWeekStore } from '../store/weekStore';

export interface UseImportIntegrationReturn {
  isLocking: boolean;
  error: string | null;
  lockWeekAfterImport: (
    weekId: number,
    importId: string,
    playerCount: number
  ) => Promise<boolean>;
  updateImportStatus: (
    weekId: number,
    status: 'pending' | 'imported' | 'error',
    importCount?: number,
    importTimestamp?: string,
    errorMessage?: string
  ) => Promise<boolean>;
  clearError: () => void;
}

/**
 * useImportIntegration Hook
 *
 * Provides functions to:
 * 1. Lock a week after successful import completion
 * 2. Update import status in week metadata
 * 3. Refresh week data in Zustand store
 */
export const useImportIntegration = (): UseImportIntegrationReturn => {
  const [isLocking, setIsLocking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { currentYear, weeks, setWeeks, getWeekById } = useWeekStore();

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  /**
   * Lock a week after successful import.
   * Called by Data Import System when import completes.
   */
  const lockWeekAfterImport = useCallback(
    async (
      weekId: number,
      importId: string,
      playerCount: number
    ): Promise<boolean> => {
      try {
        setIsLocking(true);
        clearError();

        // Call PUT /api/weeks/{week_id}/lock
        const response = await fetch(`/api/weeks/${weekId}/lock`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            import_id: importId,
            player_count: playerCount,
          }),
        });

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.detail || `Failed to lock week: ${response.status}`);
        }

        const data = await response.json();

        if (!data.success || !data.week) {
          throw new Error('Invalid response from server');
        }

        // Update Zustand store with locked week
        const updatedWeek = data.week;
        const updatedWeeks = weeks.map((w) =>
          w.id === weekId ? updatedWeek : w
        );
        setWeeks(updatedWeeks);

        setIsLocking(false);
        return true;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'An unexpected error occurred';
        setError(errorMessage);
        setIsLocking(false);
        return false;
      }
    },
    [weeks, setWeeks, clearError]
  );

  /**
   * Update import status in week metadata.
   * Called when import status changes (pending/imported/error).
   */
  const updateImportStatus = useCallback(
    async (
      weekId: number,
      status: 'pending' | 'imported' | 'error',
      importCount?: number,
      importTimestamp?: string,
      errorMessage?: string
    ): Promise<boolean> => {
      try {
        setIsLocking(true);
        clearError();

        // Call PUT /api/weeks/{week_id}/import-status
        const response = await fetch(`/api/weeks/${weekId}/import-status`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            status,
            import_count: importCount ?? 0,
            import_timestamp: importTimestamp,
            error_message: errorMessage,
          }),
        });

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.detail || `Failed to update status: ${response.status}`);
        }

        const data = await response.json();

        if (!data.success || !data.week) {
          throw new Error('Invalid response from server');
        }

        // Update Zustand store with updated week
        const updatedWeek = data.week;
        const updatedWeeks = weeks.map((w) =>
          w.id === weekId ? updatedWeek : w
        );
        setWeeks(updatedWeeks);

        setIsLocking(false);
        return true;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'An unexpected error occurred';
        setError(errorMessage);
        setIsLocking(false);
        return false;
      }
    },
    [weeks, setWeeks, clearError]
  );

  return {
    isLocking,
    error,
    lockWeekAfterImport,
    updateImportStatus,
    clearError,
  };
};

export default useImportIntegration;
