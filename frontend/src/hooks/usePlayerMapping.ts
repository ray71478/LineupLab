/**
 * usePlayerMapping Hook
 *
 * Custom hook for managing unmatched player mapping workflow
 * - Manages modal open/close state
 * - Fetches fuzzy match suggestions for unmatched player
 * - Manages selected match from suggestions
 * - Submits mapping to backend via API
 * - Handles loading, error, and success states
 * - Provides callbacks for mapping completion
 *
 * @example
 * const {
 *   isModalOpen,
 *   selectedUnmatchedPlayer,
 *   suggestions,
 *   selectedMatch,
 *   isLoading,
 *   error,
 *   openModal,
 *   closeModal,
 *   selectMatch,
 *   submitMapping,
 *   isSubmitting
 * } = usePlayerMapping(onSuccess);
 */

import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { PlayerResponse, UnmatchedPlayerResponse, MappingPayload } from '../types/player.types';

export interface UsePlayerMappingReturn {
  isModalOpen: boolean;
  selectedUnmatchedPlayer: UnmatchedPlayerResponse | null;
  suggestions: PlayerResponse[];
  selectedMatch: PlayerResponse | null;
  isLoading: boolean;
  isSuggestionsLoading: boolean;
  error: Error | null;
  mappingError: Error | null;
  openModal: (player: UnmatchedPlayerResponse) => void;
  closeModal: () => void;
  selectMatch: (player: PlayerResponse) => void;
  submitMapping: () => Promise<void>;
  isSubmitting: boolean;
}

interface SuggestionsResponse {
  success: boolean;
  unmatched_player?: UnmatchedPlayerResponse;
  suggestions: PlayerResponse[];
}

interface MappingResponse {
  success: boolean;
  message?: string;
  error?: string;
}

/**
 * Fetch fuzzy match suggestions for unmatched player
 */
async function fetchSuggestions(
  unmatchedPlayerId: number,
  limit: number = 5
): Promise<PlayerResponse[]> {
  const response = await fetch(`/api/players/suggestions/${unmatchedPlayerId}?limit=${limit}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch suggestions for player ${unmatchedPlayerId}`);
  }

  const data: SuggestionsResponse = await response.json();

  if (!data.success) {
    throw new Error('Failed to fetch suggestions');
  }

  return data.suggestions || [];
}

/**
 * Submit player mapping to backend
 */
async function submitPlayerMapping(payload: MappingPayload): Promise<MappingResponse> {
  const response = await fetch('/api/unmatched-players/map', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Failed to submit mapping: ${response.statusText}`);
  }

  const data: MappingResponse = await response.json();

  if (!data.success) {
    throw new Error(data.error || 'Failed to map player');
  }

  return data;
}

/**
 * usePlayerMapping Hook
 *
 * Manages the complete player mapping workflow with:
 * - Modal state management
 * - Fuzzy suggestion fetching
 * - Match selection and submission
 * - Error handling and retry logic
 * - Cache invalidation on success
 */
export const usePlayerMapping = (
  onSuccess?: () => void
): UsePlayerMappingReturn => {
  const queryClient = useQueryClient();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedUnmatchedPlayer, setSelectedUnmatchedPlayer] =
    useState<UnmatchedPlayerResponse | null>(null);
  const [selectedMatch, setSelectedMatch] = useState<PlayerResponse | null>(null);

  // Fetch suggestions when unmatched player is selected
  const {
    data: suggestions = [],
    isLoading: isSuggestionsLoading,
    error: suggestionsError,
  } = useQuery({
    queryKey: ['player-suggestions', selectedUnmatchedPlayer?.id],
    queryFn: () => fetchSuggestions(selectedUnmatchedPlayer!.id),
    enabled: selectedUnmatchedPlayer !== null,
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });

  // Submit mapping mutation
  const {
    mutateAsync: submitMappingMutation,
    isPending: isSubmitting,
    error: mappingError,
    reset: resetMappingError,
  } = useMutation({
    mutationFn: (payload: MappingPayload) => submitPlayerMapping(payload),
    onSuccess: async () => {
      // Invalidate relevant caches
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['players'] }),
        queryClient.invalidateQueries({ queryKey: ['unmatched-players'] }),
      ]);

      // Call success callback
      if (onSuccess) {
        onSuccess();
      }
    },
  });

  const openModal = useCallback((player: UnmatchedPlayerResponse) => {
    resetMappingError();
    setSelectedUnmatchedPlayer(player);
    setSelectedMatch(null);
    setIsModalOpen(true);
  }, [resetMappingError]);

  const closeModal = useCallback(() => {
    setIsModalOpen(false);
    setSelectedUnmatchedPlayer(null);
    setSelectedMatch(null);
    resetMappingError();
  }, [resetMappingError]);

  const selectMatch = useCallback((player: PlayerResponse) => {
    setSelectedMatch(player);
  }, []);

  const submitMapping = useCallback(async () => {
    if (!selectedUnmatchedPlayer || !selectedMatch) {
      throw new Error('No player selected for mapping');
    }

    try {
      await submitMappingMutation({
        unmatched_player_id: selectedUnmatchedPlayer.id,
        canonical_player_key: selectedMatch.player_key,
      });

      // Close modal after successful mapping
      closeModal();
    } catch (err) {
      // Error is handled by mutation error state
      throw err;
    }
  }, [selectedUnmatchedPlayer, selectedMatch, submitMappingMutation, closeModal]);

  return {
    isModalOpen,
    selectedUnmatchedPlayer,
    suggestions,
    selectedMatch,
    isLoading: isSuggestionsLoading,
    isSuggestionsLoading,
    error: suggestionsError as Error | null,
    mappingError: mappingError as Error | null,
    openModal,
    closeModal,
    selectMatch,
    submitMapping,
    isSubmitting,
  };
};

export default usePlayerMapping;
