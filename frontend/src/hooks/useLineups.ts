/**
 * useLineups Hook
 *
 * Custom hook for managing lineup generation and saving.
 * - Generates optimized lineups with contest mode support
 * - Saves selected lineups
 * - Fetches saved lineups filtered by mode
 * - Manages loading and error states
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type {
  LineupOptimizationRequest,
  LineupOptimizationResponse,
  SaveLineupsRequest,
  SaveLineupsResponse,
  SavedLineup,
  GeneratedLineup,
} from '../types/lineup.types';
import { useMode } from './useMode';

export interface UseLineupsReturn {
  generateLineups: (request: LineupOptimizationRequest) => Promise<GeneratedLineup[]>;
  isGenerating: boolean;
  saveLineups: (request: SaveLineupsRequest) => Promise<SaveLineupsResponse>;
  isSaving: boolean;
  savedLineups: SavedLineup[];
  isLoadingSaved: boolean;
  refetchSaved: () => void;
}

/**
 * Generate optimized lineups
 */
async function generateLineups(request: LineupOptimizationRequest): Promise<GeneratedLineup[]> {
  console.log('Generating lineups with request:', request);
  const response = await fetch('/api/lineups/generate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    console.error('Lineup generation failed:', error);
    throw new Error(error.detail || 'Failed to generate lineups');
  }

  const data: LineupOptimizationResponse = await response.json();
  return data.lineups || [];
}

/**
 * Save selected lineups
 */
async function saveLineups(request: SaveLineupsRequest): Promise<SaveLineupsResponse> {
  const response = await fetch('/api/lineups/save', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to save lineups');
  }

  return await response.json();
}

/**
 * Fetch saved lineups for a week and contest mode
 */
async function fetchSavedLineups(weekId: number, contestMode: string): Promise<SavedLineup[]> {
  const response = await fetch(`/api/lineups/saved/${weekId}?contest_mode=${contestMode}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch saved lineups');
  }

  return await response.json();
}

/**
 * useLineups Hook
 *
 * Manages lineup generation and saving with contest mode awareness
 */
export const useLineups = (weekId: number | null): UseLineupsReturn => {
  const queryClient = useQueryClient();
  const { mode } = useMode();

  // Generate lineups mutation
  const generateMutation = useMutation({
    mutationFn: generateLineups,
    onSuccess: () => {
      // Invalidate saved lineups query to refresh if needed
      if (weekId !== null) {
        queryClient.invalidateQueries({ queryKey: ['saved-lineups', weekId, mode] });
      }
    },
  });

  // Save lineups mutation
  const saveMutation = useMutation({
    mutationFn: saveLineups,
    onSuccess: () => {
      // Refresh saved lineups
      if (weekId !== null) {
        queryClient.invalidateQueries({ queryKey: ['saved-lineups', weekId, mode] });
      }
    },
  });

  // Fetch saved lineups
  const {
    data: savedLineups = [],
    isLoading: isLoadingSaved,
    refetch: refetchSaved,
  } = useQuery({
    queryKey: ['saved-lineups', weekId, mode],
    queryFn: () => fetchSavedLineups(weekId!, mode),
    enabled: weekId !== null,
  });

  return {
    generateLineups: generateMutation.mutateAsync,
    isGenerating: generateMutation.isPending,
    saveLineups: saveMutation.mutateAsync,
    isSaving: saveMutation.isPending,
    savedLineups,
    isLoadingSaved,
    refetchSaved,
  };
};
