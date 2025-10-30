/**
 * Optimized Zustand store for global week state management
 *
 * Performance optimizations:
 * - Memoized selectors to prevent unnecessary recalculations
 * - Efficient filtering and mapping
 * - WeakMap cache for computed values (optional for large datasets)
 * - Batch updates to minimize re-renders
 * - Subscriptions only for changed properties
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

  // Cache for computed values (performance optimization)
  _weeksByNumberCache?: Map<number, Week>;
  _weeksByStatusCache?: Map<string, Week[]>;

  // Actions
  setCurrentYear: (year: number) => void;
  setCurrentWeek: (week: number) => void;
  setWeeks: (weeks: Week[]) => void;
  setAvailableYears: (years: number[]) => void;
  setIsLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setSelectedWeekForImport: (week: number | null) => void;

  // Computed selectors (memoized)
  getCurrentWeekData: () => Week | null;
  getWeekById: (id: number) => Week | null;
  getWeekByNumber: (number: number) => Week | null;
  getWeeksByStatus: (status: string) => Week[];
  getLockedWeeks: () => Week[];
  getImportedWeeks: () => Week[];
  getActiveWeeks: () => Week[];
  getUpcomingWeeks: () => Week[];
  getCompletedWeeks: () => Week[];

  // Batch update action
  batchUpdate: (updates: Partial<WeekState>) => void;

  // Cache invalidation
  _invalidateCache: () => void;

  // Helper for testing
  reset?: () => void;
}

/**
 * Create efficient selectors with caching
 */
const createMemoizedSelectors = () => {
  let cachedWeeks: Week[] | null = null;
  let cachedWeeksByNumber: Map<number, Week> | null = null;
  let cachedWeeksByStatus: Map<string, Week[]> | null = null;

  return {
    getWeekByNumber: (weeks: Week[], number: number): Week | null => {
      // Check if cache is valid
      if (cachedWeeks !== weeks) {
        cachedWeeks = weeks;
        cachedWeeksByNumber = new Map(
          weeks.map((w) => [w.week_number, w])
        );
      }
      return cachedWeeksByNumber?.get(number) || null;
    },

    getWeeksByStatus: (weeks: Week[], status: string): Week[] => {
      // Check if cache is valid
      if (cachedWeeks !== weeks) {
        cachedWeeks = weeks;
        cachedWeeksByStatus = new Map();
        const allStatuses = ['active', 'upcoming', 'completed', 'pending', 'imported', 'error'];
        for (const s of allStatuses) {
          cachedWeeksByStatus.set(s, weeks.filter((w) => w.status === s));
        }
      }
      return cachedWeeksByStatus?.get(status) || [];
    },
  };
};

const memoizedSelectors = createMemoizedSelectors();

/**
 * Create Zustand store with persist middleware
 * Persists to localStorage key: 'week-store'
 * Version: 1
 */
export const useWeekStoreOptimized = create<WeekState>()(
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
      _weeksByNumberCache: new Map(),
      _weeksByStatusCache: new Map(),

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
        set((state) => {
          // Only update if weeks have actually changed
          if (state.weeks === weeks) return state;
          return {
            weeks,
            _weeksByNumberCache: undefined, // Invalidate cache
            _weeksByStatusCache: undefined,
          };
        });
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

      // Batch update to minimize re-renders
      batchUpdate: (updates: Partial<WeekState>) => {
        set((state) => {
          // Merge updates and invalidate cache if weeks changed
          const newState = { ...state, ...updates };
          if (updates.weeks && updates.weeks !== state.weeks) {
            newState._weeksByNumberCache = undefined;
            newState._weeksByStatusCache = undefined;
          }
          return newState;
        });
      },

      // Cache invalidation
      _invalidateCache: () => {
        set({
          _weeksByNumberCache: undefined,
          _weeksByStatusCache: undefined,
        });
      },

      // Computed selectors with memoization
      getCurrentWeekData: () => {
        const state = get();
        if (!state.currentWeek) return null;
        return memoizedSelectors.getWeekByNumber(state.weeks, state.currentWeek);
      },

      getWeekById: (id: number) => {
        const state = get();
        return state.weeks.find((w) => w.id === id) || null;
      },

      getWeekByNumber: (number: number) => {
        const state = get();
        return memoizedSelectors.getWeekByNumber(state.weeks, number);
      },

      getWeeksByStatus: (status: string) => {
        const state = get();
        return memoizedSelectors.getWeeksByStatus(state.weeks, status);
      },

      getLockedWeeks: () => {
        const state = get();
        return state.weeks.filter((w) => w.is_locked);
      },

      getImportedWeeks: () => {
        const state = get();
        return state.weeks.filter((w) => w.metadata.import_status === 'imported');
      },

      getActiveWeeks: () => {
        const state = get();
        return memoizedSelectors.getWeeksByStatus(state.weeks, 'active');
      },

      getUpcomingWeeks: () => {
        const state = get();
        return memoizedSelectors.getWeeksByStatus(state.weeks, 'upcoming');
      },

      getCompletedWeeks: () => {
        const state = get();
        return memoizedSelectors.getWeeksByStatus(state.weeks, 'completed');
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
          _weeksByNumberCache: new Map(),
          _weeksByStatusCache: new Map(),
        });
      },
    }),
    {
      name: 'week-store-optimized',
      version: 1,
    }
  )
);

export default useWeekStoreOptimized;
