/**
 * Zustand store for global week state management
 *
 * Manages:
 * - Currently selected year (2025-2030)
 * - Currently selected week (1-18)
 * - All weeks for current year with metadata
 * - Available years for season selection
 * - Loading and error states
 * - Selected week for import operations
 *
 * State persists to localStorage via persist middleware.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

/**
 * Week metadata containing import and NFL schedule information
 */
export interface WeekMetadata {
  kickoff_time: string;
  espn_link: string;
  slate_start: string;
  import_status: 'pending' | 'imported' | 'error';
  import_count: number;
  import_timestamp: string | null;
  error_message?: string;
}

/**
 * Week object with all properties
 */
export interface Week {
  id: number;
  season: number;
  week_number: number;
  status: 'active' | 'upcoming' | 'completed';
  status_override: string | null;
  nfl_slate_date: string;
  is_locked: boolean;
  locked_at: string | null;
  metadata: WeekMetadata;
}

/**
 * State interface with all actions and selectors
 */
export interface WeekState {
  // State
  currentYear: number;
  currentWeek: number | null;
  weeks: Week[];
  availableYears: number[];
  isLoading: boolean;
  error: string | null;
  selectedWeekForImport: number | null;

  // Actions
  setCurrentYear: (year: number) => void;
  setCurrentWeek: (week: number) => void;
  setWeeks: (weeks: Week[]) => void;
  setAvailableYears: (years: number[]) => void;
  setIsLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setSelectedWeekForImport: (week: number | null) => void;

  // Computed selectors
  getCurrentWeekData: () => Week | null;
  getWeekById: (id: number) => Week | null;
  getWeekByNumber: (number: number) => Week | null;
  getWeeksByStatus: (status: string) => Week[];
  getLockedWeeks: () => Week[];
  getImportedWeeks: () => Week[];

  // Helper for testing
  reset?: () => void;
}

/**
 * Create Zustand store with persist middleware
 * Persists to localStorage key: 'week-store'
 * Version: 1
 */
export const useWeekStore = create<WeekState>()(
  persist(
    (set, get) => ({
      // Initial state
      currentYear: new Date().getFullYear(),
      currentWeek: null,
      weeks: [],
      availableYears: [2025, 2026, 2027, 2028, 2029, 2030],
      isLoading: false,
      error: null,
      selectedWeekForImport: null,

      // Basic actions
      setCurrentYear: (year: number) => {
        set({ currentYear: year });
      },

      setCurrentWeek: (week: number) => {
        // Validate week is in range 1-18
        if (week >= 1 && week <= 18) {
          set({ currentWeek: week, selectedWeekForImport: week });
        }
      },

      setWeeks: (weeks: Week[]) => {
        set({ weeks });
      },

      setAvailableYears: (years: number[]) => {
        set({ availableYears: years });
      },

      setIsLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },

      setError: (error: string | null) => {
        set({ error });
      },

      setSelectedWeekForImport: (week: number | null) => {
        set({ selectedWeekForImport: week });
      },

      // Computed selectors
      getCurrentWeekData: () => {
        const state = get();
        if (!state.currentWeek) return null;
        return state.weeks.find((w) => w.week_number === state.currentWeek) || null;
      },

      getWeekById: (id: number) => {
        const state = get();
        return state.weeks.find((w) => w.id === id) || null;
      },

      getWeekByNumber: (number: number) => {
        const state = get();
        return state.weeks.find((w) => w.week_number === number) || null;
      },

      getWeeksByStatus: (status: string) => {
        const state = get();
        return state.weeks.filter((w) => w.status === status);
      },

      getLockedWeeks: () => {
        const state = get();
        return state.weeks.filter((w) => w.is_locked);
      },

      getImportedWeeks: () => {
        const state = get();
        return state.weeks.filter((w) => w.metadata.import_status === 'imported');
      },

      // Helper for testing
      reset: () => {
        set({
          currentYear: new Date().getFullYear(),
          currentWeek: null,
          weeks: [],
          availableYears: [2025, 2026, 2027, 2028, 2029, 2030],
          isLoading: false,
          error: null,
          selectedWeekForImport: null,
        });
      },
    }),
    {
      name: 'week-store', // localStorage key
      version: 1,
    }
  )
);
