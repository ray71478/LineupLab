/**
 * useWeekSelection Hook
 *
 * Comprehensive hook that combines useWeeks, useCurrentWeek, and weekStore
 * Handles:
 * - Year selection and week fetching
 * - Week selection with localStorage persistence
 * - Managing loading and error states
 * - Syncing with Zustand store
 *
 * @returns Object with weeks, currentWeek, currentYear, handlers, and states
 */

import { useWeekStore, Week } from '../store';
import useWeeks from './useWeeks';
import useCurrentWeek from './useCurrentWeek';

export interface UseWeekSelectionReturn {
  weeks: Week[];
  currentWeek: number | null;
  currentYear: number;
  selectedWeekForImport: number | null;
  onYearChange: (year: number) => void;
  onWeekChange: (week: number) => void;
  isLoading: boolean;
  error: string | null;
  isSuccess: boolean;
}

/**
 * Custom hook combining all week management functionality
 *
 * Manages:
 * - Year selection (2025-2030)
 * - Week data fetching for selected year
 * - Current week detection
 * - localStorage persistence
 * - Zustand store synchronization
 */
export const useWeekSelection = (): UseWeekSelectionReturn => {
  const store = useWeekStore();

  // Fetch weeks for current year
  const weeksQuery = useWeeks(store.currentYear);

  // Fetch current week (updates every 60 seconds)
  const currentWeekQuery = useCurrentWeek();

  const handleYearChange = (year: number) => {
    store.setCurrentYear(year);
    store.setIsLoading(true);
  };

  const handleWeekChange = (week: number) => {
    if (week >= 1 && week <= 18) {
      store.setCurrentWeek(week);
    }
  };

  // Combine loading states
  const isLoading = weeksQuery.isLoading || currentWeekQuery.isLoading;

  // Use error from whichever query has one, prioritize weeksQuery
  const error = weeksQuery.error || currentWeekQuery.error;

  // Update store loading state
  if (weeksQuery.isSuccess && error === null) {
    store.setIsLoading(false);
  }

  return {
    weeks: store.weeks,
    currentWeek: store.currentWeek,
    currentYear: store.currentYear,
    selectedWeekForImport: store.selectedWeekForImport,
    onYearChange: handleYearChange,
    onWeekChange: handleWeekChange,
    isLoading,
    error: error || store.error,
    isSuccess: weeksQuery.isSuccess && !error,
  };
};

export default useWeekSelection;
