/**
 * useSmartScore Hook
 *
 * Custom hook for managing Smart Score data fetching, calculation, and state.
 * - Fetches player data with React Query
 * - Triggers Smart Score calculation
 * - Manages loading and error states
 * - Caches scores with 5 minute stale time
 * - Invalidates cache on weight changes
 *
 * @example
 * const {
 *   players,
 *   isLoading,
 *   error,
 *   calculateScores,
 *   isCalculating,
 *   refetch
 * } = useSmartScore(weekId);
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type {
  PlayerScoreResponse,
  CalculateScoreRequest,
  CalculateScoreResponse,
  WeightProfile,
  ScoreConfig,
} from '../types/smartScore.types';

export interface UseSmartScoreReturn {
  players: PlayerScoreResponse[];
  isLoading: boolean;
  error: Error | null;
  calculateScores: (weekId: number, weights: WeightProfile, config: ScoreConfig) => Promise<PlayerScoreResponse[]>;
  isCalculating: boolean;
  refetch: () => void;
  invalidateCache: () => Promise<void>;
}

/**
 * Fetch players with Smart Scores for a week
 * Note: This assumes players are already calculated. For recalculation, use calculateScores mutation.
 */
async function fetchPlayersWithScores(weekId: number): Promise<PlayerScoreResponse[]> {
  // For now, fetch players from the players endpoint
  // In a real implementation, you might want a dedicated endpoint for Smart Score players
  const response = await fetch(`/api/players/by-week/${weekId}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch players for week ${weekId}`);
  }

  const data = await response.json();
  return data.players || [];
}

/**
 * Calculate Smart Scores for all players in a week
 */
async function calculateScores(request: CalculateScoreRequest): Promise<PlayerScoreResponse[]> {
  const response = await fetch('/api/smart-score/calculate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to calculate Smart Scores');
  }

  const data: CalculateScoreResponse = await response.json();

  if (!data.success) {
    throw new Error('Failed to calculate Smart Scores');
  }

  return data.players || [];
}

/**
 * useSmartScore Hook
 *
 * Manages Smart Score calculation and player data fetching
 */
export const useSmartScore = (
  weekId: number | null
): UseSmartScoreReturn => {
  const queryClient = useQueryClient();

  // Fetch players (initial load)
  const {
    data: players = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['smart-scores', weekId],
    queryFn: () => fetchPlayersWithScores(weekId!),
    enabled: weekId !== null,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Calculate scores mutation
  const calculateMutation = useMutation({
    mutationFn: calculateScores,
    onSuccess: (data, variables) => {
      // Update cache with calculated scores
      queryClient.setQueryData(['smart-scores', variables.week_id], data);
      // Also invalidate to trigger refetch
      queryClient.invalidateQueries({ queryKey: ['smart-scores', variables.week_id] });
    },
  });

  const calculateScoresFn = async (
    weekId: number,
    weights: WeightProfile,
    config: ScoreConfig
  ): Promise<PlayerScoreResponse[]> => {
    return await calculateMutation.mutateAsync({
      week_id: weekId,
      weights,
      config,
    });
  };

  const invalidateCache = async () => {
    await queryClient.invalidateQueries({ queryKey: ['smart-scores', weekId] });
  };

  return {
    players,
    isLoading: isLoading || calculateMutation.isPending,
    error: (error || calculateMutation.error) as Error | null,
    calculateScores: calculateScoresFn,
    isCalculating: calculateMutation.isPending,
    refetch: () => {
      if (weekId !== null) {
        refetch();
      }
    },
    invalidateCache,
  };
};

