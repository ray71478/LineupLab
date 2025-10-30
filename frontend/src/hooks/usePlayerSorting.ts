/**
 * usePlayerSorting Hook
 *
 * Custom hook for managing table sort state and sorting logic
 * - Manages current sort column and sort direction
 * - Toggles sort direction on repeated column clicks
 * - Provides sorted player list based on current sort state
 * - Supports sorting by all table columns
 *
 * @example
 * const {
 *   sortColumn,
 *   sortDirection,
 *   sortedPlayers,
 *   handleSort
 * } = usePlayerSorting(players);
 */

import { useState, useMemo } from 'react';
import type { PlayerResponse, SortState } from '../types/player.types';

export interface UsePlayerSortingReturn {
  sortColumn: string | null;
  sortDirection: 'asc' | 'desc';
  sortedPlayers: PlayerResponse[];
  handleSort: (columnName: string) => void;
}

/**
 * Compare two values for sorting
 * Handles null/undefined values and different data types
 */
function compareValues(
  a: string | number | undefined | null,
  b: string | number | undefined | null,
  sortDirection: 'asc' | 'desc'
): number {
  // Handle null/undefined
  if (a === null || a === undefined) return 1;
  if (b === null || b === undefined) return -1;

  // Numeric comparison
  if (typeof a === 'number' && typeof b === 'number') {
    return sortDirection === 'asc' ? a - b : b - a;
  }

  // String comparison (case-insensitive)
  const aStr = String(a).toLowerCase();
  const bStr = String(b).toLowerCase();
  return sortDirection === 'asc' ? aStr.localeCompare(bStr) : bStr.localeCompare(aStr);
}

/**
 * Get sort value from player by column name
 */
function getSortValue(
  player: PlayerResponse,
  columnName: string
): string | number | undefined | null {
  switch (columnName) {
    case 'name':
      return player.name;
    case 'team':
      return player.team;
    case 'position':
      return player.position;
    case 'salary':
      return player.salary;
    case 'projection':
      return player.projection;
    case 'ownership':
      return player.ownership;
    case 'ceiling':
      return player.ceiling;
    case 'floor':
      return player.floor;
    case 'source':
      return player.source;
    case 'status':
      return player.status;
    case 'uploaded_at':
      return player.uploaded_at;
    default:
      return undefined;
  }
}

/**
 * usePlayerSorting Hook
 *
 * Manages sort state and provides sorted player list with:
 * - Single-column sorting (not multi-column)
 * - Ascending/descending toggle on column re-click
 * - Smart type handling (numbers, strings, dates)
 * - Null/undefined value handling
 */
export const usePlayerSorting = (players: PlayerResponse[]): UsePlayerSortingReturn => {
  const [sortState, setSortState] = useState<SortState>({
    sortColumn: null,
    sortDirection: 'asc',
  });

  // Apply sorting to players list
  const sortedPlayers = useMemo(() => {
    if (!sortState.sortColumn) {
      return players;
    }

    const sorted = [...players].sort((a, b) => {
      const aValue = getSortValue(a, sortState.sortColumn!);
      const bValue = getSortValue(b, sortState.sortColumn!);
      return compareValues(aValue, bValue, sortState.sortDirection);
    });

    return sorted;
  }, [players, sortState]);

  const handleSort = (columnName: string) => {
    setSortState((prev) => {
      // If clicking the same column, toggle direction
      if (prev.sortColumn === columnName) {
        return {
          sortColumn: columnName,
          sortDirection: prev.sortDirection === 'asc' ? 'desc' : 'asc',
        };
      }

      // If clicking a new column, start with ascending
      return {
        sortColumn: columnName,
        sortDirection: 'asc',
      };
    });
  };

  return {
    sortColumn: sortState.sortColumn,
    sortDirection: sortState.sortDirection,
    sortedPlayers,
    handleSort,
  };
};

export default usePlayerSorting;
