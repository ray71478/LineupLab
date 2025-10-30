/**
 * usePlayerFiltering Hook
 *
 * Custom hook for managing player filter state and filtering logic
 * - Manages position, team, unmatched-only, and search filters
 * - Applies filters to player list with AND logic (all filters must match)
 * - Provides filter state and state-setting functions
 * - Supports chaining multiple filters together
 *
 * @example
 * const {
 *   filters,
 *   filteredPlayers,
 *   setPositionFilter,
 *   setTeamFilter,
 *   setUnmatchedOnly,
 *   setSearchQuery,
 *   clearAllFilters,
 *   hasActiveFilters
 * } = usePlayerFiltering(players);
 */

import { useState, useMemo } from 'react';
import type { PlayerResponse, PlayerFilters } from '../types/player.types';

export interface UsePlayerFilteringReturn {
  filters: PlayerFilters;
  filteredPlayers: PlayerResponse[];
  setPositionFilter: (positions: string[]) => void;
  setTeamFilter: (teams: string[]) => void;
  setUnmatchedOnly: (value: boolean) => void;
  setSearchQuery: (query: string) => void;
  clearAllFilters: () => void;
  hasActiveFilters: boolean;
}

/**
 * Check if player matches all active filters
 */
function playerMatchesFilters(
  player: PlayerResponse,
  filters: PlayerFilters
): boolean {
  // Position filter (AND logic - player must match one of selected positions)
  if (filters.positions.length > 0) {
    if (!filters.positions.includes(player.position)) {
      return false;
    }
  }

  // Team filter (AND logic - player must match one of selected teams)
  if (filters.teams.length > 0) {
    if (!filters.teams.includes(player.team)) {
      return false;
    }
  }

  // Unmatched-only filter
  if (filters.unmatchedOnly) {
    if (player.status !== 'unmatched') {
      return false;
    }
  }

  // Search query (case-insensitive partial match on player name)
  if (filters.searchQuery.trim().length > 0) {
    const query = filters.searchQuery.toLowerCase();
    if (!player.name.toLowerCase().includes(query)) {
      return false;
    }
  }

  return true;
}

/**
 * usePlayerFiltering Hook
 *
 * Manages filter state and applies filters to player list with:
 * - Multi-select position and team filters
 * - Unmatched-only toggle
 * - Name search with case-insensitive partial matching
 * - Chainable filters (AND logic)
 */
export const usePlayerFiltering = (
  players: PlayerResponse[]
): UsePlayerFilteringReturn => {
  const [filters, setFilters] = useState<PlayerFilters>({
    positions: [],
    teams: [],
    unmatchedOnly: false,
    searchQuery: '',
  });

  // Apply filters to players list
  const filteredPlayers = useMemo(() => {
    return players.filter((player) => playerMatchesFilters(player, filters));
  }, [players, filters]);

  // Check if any filters are active
  const hasActiveFilters = useMemo(() => {
    return (
      filters.positions.length > 0 ||
      filters.teams.length > 0 ||
      filters.unmatchedOnly ||
      filters.searchQuery.trim().length > 0
    );
  }, [filters]);

  const setPositionFilter = (positions: string[]) => {
    setFilters((prev) => ({
      ...prev,
      positions,
    }));
  };

  const setTeamFilter = (teams: string[]) => {
    setFilters((prev) => ({
      ...prev,
      teams,
    }));
  };

  const setUnmatchedOnly = (value: boolean) => {
    setFilters((prev) => ({
      ...prev,
      unmatchedOnly: value,
    }));
  };

  const setSearchQuery = (query: string) => {
    setFilters((prev) => ({
      ...prev,
      searchQuery: query,
    }));
  };

  const clearAllFilters = () => {
    setFilters({
      positions: [],
      teams: [],
      unmatchedOnly: false,
      searchQuery: '',
    });
  };

  return {
    filters,
    filteredPlayers,
    setPositionFilter,
    setTeamFilter,
    setUnmatchedOnly,
    setSearchQuery,
    clearAllFilters,
    hasActiveFilters,
  };
};

export default usePlayerFiltering;
