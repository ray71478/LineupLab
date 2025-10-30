/**
 * usePlayerManagement Hook
 *
 * Custom hook for centralized player data management with React Query
 * - Fetches player and unmatched player data for a specific week
 * - Implements caching with 5-minute stale time
 * - Provides cache invalidation on mapping
 * - Manages loading, error, and data states
 *
 * @example
 * const {
 *   players,
 *   unmatchedPlayers,
 *   isLoading,
 *   error,
 *   refetch,
 *   invalidateCache
 * } = usePlayerManagement(weekId);
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import type { PlayerResponse, UnmatchedPlayerResponse } from '../types/player.types';

export interface UsePlayerManagementReturn {
  players: PlayerResponse[];
  unmatchedPlayers: UnmatchedPlayerResponse[];
  isLoading: boolean;
  isBackgroundLoading: boolean;
  error: Error | null;
  refetch: () => void;
  invalidateCache: () => Promise<void>;
}

interface PlayersResponse {
  success: boolean;
  players: PlayerResponse[];
  total: number;
  unmatched_count: number;
}

interface UnmatchedPlayersResponse {
  success: boolean;
  unmatched_players: UnmatchedPlayerResponse[];
  total_unmatched: number;
}

/**
 * Fetch players for a specific week
 */
async function fetchPlayersByWeek(weekId: number): Promise<PlayerResponse[]> {
  const response = await fetch(`/api/players/by-week/${weekId}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch players for week ${weekId}`);
  }

  const data: PlayersResponse = await response.json();

  if (!data.success) {
    throw new Error('Failed to fetch players');
  }

  return data.players || [];
}

/**
 * Fetch unmatched players for a specific week
 */
async function fetchUnmatchedPlayers(
  weekId: number
): Promise<UnmatchedPlayerResponse[]> {
  const response = await fetch(`/api/players/unmatched/${weekId}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch unmatched players for week ${weekId}`);
  }

  const data: UnmatchedPlayersResponse = await response.json();

  if (!data.success) {
    throw new Error('Failed to fetch unmatched players');
  }

  return data.unmatched_players || [];
}

/**
 * usePlayerManagement Hook
 *
 * Manages player data fetching with:
 * - React Query for server state management
 * - 5-minute stale time for caching
 * - Automatic refetching when week changes
 * - Manual cache invalidation on mapping
 */
export const usePlayerManagement = (
  weekId: number | null
): UsePlayerManagementReturn => {
  const queryClient = useQueryClient();

  // Fetch all players
  const {
    data: players = [],
    isLoading: isLoadingPlayers,
    isFetching: isFetchingPlayers,
    error: playersError,
    refetch: refetchPlayers,
  } = useQuery({
    queryKey: ['players', weekId],
    queryFn: () => fetchPlayersByWeek(weekId!),
    enabled: weekId !== null,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });

  // Fetch unmatched players
  const {
    data: unmatchedPlayers = [],
    isLoading: isLoadingUnmatched,
    isFetching: isFetchingUnmatched,
    error: unmatchedError,
    refetch: refetchUnmatched,
  } = useQuery({
    queryKey: ['unmatched-players', weekId],
    queryFn: () => fetchUnmatchedPlayers(weekId!),
    enabled: weekId !== null,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });

  const isLoading = isLoadingPlayers || isLoadingUnmatched;
  const isBackgroundLoading = isFetchingPlayers || isFetchingUnmatched;
  const error = playersError || unmatchedError;

  const refetch = () => {
    refetchPlayers();
    refetchUnmatched();
  };

  const invalidateCache = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['players', weekId] }),
      queryClient.invalidateQueries({ queryKey: ['unmatched-players', weekId] }),
    ]);
  };

  return {
    players,
    unmatchedPlayers,
    isLoading,
    isBackgroundLoading,
    error: error as Error | null,
    refetch,
    invalidateCache,
  };
};

export default usePlayerManagement;
