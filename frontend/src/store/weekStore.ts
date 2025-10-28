/**
 * Zustand store for global week state management
 *
 * Manages the currently selected week (1-18) across the entire application.
 * State persists across page navigation and component remounts.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface WeekState {
  currentWeek: number;
  setCurrentWeek: (week: number) => void;
}

export const useWeekStore = create<WeekState>()(
  persist(
    (set) => ({
      currentWeek: 1,
      setCurrentWeek: (week: number) => {
        // Validate week is in range 1-18
        if (week >= 1 && week <= 18) {
          set({ currentWeek: week });
        }
      },
    }),
    {
      name: 'week-store', // localStorage key
      version: 1,
    }
  )
);
