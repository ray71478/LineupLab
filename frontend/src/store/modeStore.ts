/**
 * Zustand store for global contest mode state management
 *
 * Manages:
 * - Currently selected contest mode ('main' | 'showdown')
 * - Mode switching between Main Slate and Showdown contests
 *
 * State persists to localStorage via persist middleware for session continuity.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

/**
 * Contest mode type - either main slate or showdown
 */
export type ContestMode = 'main' | 'showdown';

/**
 * State interface with all actions
 */
export interface ModeState {
  // State
  mode: ContestMode;

  // Actions
  setMode: (mode: ContestMode) => void;

  // Helper for testing
  reset?: () => void;
}

/**
 * Create Zustand store with persist middleware
 * Persists to localStorage key: 'mode-store'
 * Version: 1
 */
export const useModeStore = create<ModeState>()(
  persist(
    (set) => ({
      // Initial state
      mode: 'main',

      // Actions
      setMode: (mode: ContestMode) => {
        // Validate mode is one of the allowed values
        if (mode === 'main' || mode === 'showdown') {
          set({ mode });
        } else {
          console.error(`Invalid mode: ${mode}. Must be 'main' or 'showdown'.`);
        }
      },

      // Helper for testing
      reset: () => {
        set({ mode: 'main' });
      },
    }),
    {
      name: 'mode-store', // localStorage key
      version: 1,
    }
  )
);
