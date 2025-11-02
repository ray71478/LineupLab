/**
 * Custom hook for easy access to mode store
 *
 * Simplifies component integration by providing a clean interface
 * to the mode store without requiring direct store imports.
 *
 * Usage:
 * ```typescript
 * const { mode, setMode } = useMode();
 *
 * // Read current mode
 * console.log(mode); // 'main' or 'showdown'
 *
 * // Switch modes
 * setMode('showdown');
 * ```
 */

import { useModeStore } from '../store/modeStore';
import type { ContestMode } from '../store/modeStore';

/**
 * Return type for useMode hook
 */
export interface UseModeReturn {
  mode: ContestMode;
  setMode: (mode: ContestMode) => void;
}

/**
 * Hook to access contest mode state and actions
 *
 * @returns Object with mode and setMode function
 */
export const useMode = (): UseModeReturn => {
  const mode = useModeStore((state) => state.mode);
  const setMode = useModeStore((state) => state.setMode);

  return {
    mode,
    setMode,
  };
};
