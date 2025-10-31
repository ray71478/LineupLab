/**
 * useScoreSnapshot Hook
 *
 * Custom hook for managing snapshot comparison logic (before/after scores, deltas).
 * - Stores previous scores before recalculation
 * - Calculates deltas (new - previous)
 * - Identifies top 10 biggest changes
 * - Manages Keep Changes and Revert functions
 *
 * @example
 * const {
 *   snapshot,
 *   createSnapshot,
 *   keepChanges,
 *   revert,
 *   clearSnapshot,
 *   calculateDeltas,
 *   getTopChanges
 * } = useScoreSnapshot();
 */

import { useState, useCallback } from 'react';
import type { PlayerScoreResponse, ScoreChange } from '../types/smartScore.types';

export interface UseScoreSnapshotReturn {
  snapshot: Map<number, PlayerScoreResponse> | null;
  calculateDeltas: (currentPlayers: PlayerScoreResponse[]) => Map<number, number>;
  getTopChanges: (currentPlayers: PlayerScoreResponse[]) => ScoreChange[];
  createSnapshot: (players: PlayerScoreResponse[]) => void;
  keepChanges: () => void;
  revert: (previousPlayers: PlayerScoreResponse[]) => PlayerScoreResponse[];
  clearSnapshot: () => void;
  hasSnapshot: boolean;
}

/**
 * useScoreSnapshot Hook
 *
 * Manages snapshot comparison logic for before/after score changes
 */
export const useScoreSnapshot = (): UseScoreSnapshotReturn => {
  const [snapshot, setSnapshot] = useState<Map<number, PlayerScoreResponse> | null>(null);

  // Create snapshot from current players (store full player data for factor breakdown)
  const createSnapshot = useCallback((players: PlayerScoreResponse[]) => {
    const snapshotMap = new Map<number, PlayerScoreResponse>();
    players.forEach((player) => {
      if (player.smart_score !== null && player.smart_score !== undefined) {
        snapshotMap.set(player.player_id, { ...player });
      }
    });
    setSnapshot(snapshotMap);
  }, []);

  // Calculate deltas (new - previous)
  const calculateDeltas = useCallback(
    (currentPlayers: PlayerScoreResponse[]): Map<number, number> => {
      if (!snapshot) return new Map();

      const deltas = new Map<number, number>();
      currentPlayers.forEach((player) => {
        const previousPlayer = snapshot.get(player.player_id);
        const currentScore = player.smart_score;

        if (
          previousPlayer &&
          previousPlayer.smart_score !== null &&
          previousPlayer.smart_score !== undefined &&
          currentScore !== null &&
          currentScore !== undefined
        ) {
          const delta = currentScore - previousPlayer.smart_score;
          deltas.set(player.player_id, delta);
        }
      });

      return deltas;
    },
    [snapshot]
  );

  // Get top 10 biggest changes with factor breakdown
  const getTopChanges = useCallback(
    (currentPlayers: PlayerScoreResponse[]): ScoreChange[] => {
      const deltas = calculateDeltas(currentPlayers);
      const changes: ScoreChange[] = [];

      currentPlayers.forEach((player) => {
        const delta = deltas.get(player.player_id);
        const previousPlayer = snapshot?.get(player.player_id);

        if (
          delta !== undefined &&
          previousPlayer &&
          previousPlayer.smart_score !== null &&
          previousPlayer.smart_score !== undefined &&
          player.smart_score !== null &&
          player.smart_score !== undefined
        ) {
          // Calculate factor-level changes
          const factorChanges: ScoreChange['factorChanges'] = {};
          const previousBreakdown = previousPlayer.score_breakdown;
          const currentBreakdown = player.score_breakdown;

          if (previousBreakdown && currentBreakdown) {
            const factors = ['W1', 'W2', 'W3', 'W4', 'W5', 'W6', 'W7', 'W8'] as const;
            factors.forEach((factor) => {
              const prevKey = `${factor}_value` as keyof typeof previousBreakdown;
              const currKey = `${factor}_value` as keyof typeof currentBreakdown;
              const prevValue = previousBreakdown[prevKey] as number | undefined;
              const currValue = currentBreakdown[currKey] as number | undefined;

              if (prevValue !== undefined && currValue !== undefined && prevValue !== currValue) {
                factorChanges[factor] = {
                  previous: prevValue,
                  current: currValue,
                  delta: currValue - prevValue,
                };
              }
            });
          }

          changes.push({
            playerId: player.player_id,
            playerName: player.name,
            previousScore: previousPlayer.smart_score,
            newScore: player.smart_score,
            delta,
            isTopChange: false, // Will be set after sorting
            factorChanges: Object.keys(factorChanges).length > 0 ? factorChanges : undefined,
            playerData: {
              ownership: player.ownership,
              projection: player.projection,
              salary: player.salary,
              position: player.position,
            },
          });
        }
      });

      // Sort by absolute delta (descending)
      changes.sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta));

      // Mark top 10
      const top10 = changes.slice(0, 10);
      top10.forEach((change) => {
        change.isTopChange = true;
      });

      return changes;
    },
    [snapshot, calculateDeltas]
  );

  // Keep changes (apply new scores, clear snapshot)
  const keepChanges = useCallback(() => {
    setSnapshot(null);
  }, []);

  // Revert to previous scores
  const revert = useCallback(
    (previousPlayers: PlayerScoreResponse[]): PlayerScoreResponse[] => {
      if (!snapshot) return previousPlayers;

      return previousPlayers.map((player) => {
        const previousPlayer = snapshot.get(player.player_id);
        if (previousPlayer && previousPlayer.smart_score !== undefined) {
          return {
            ...player,
            smart_score: previousPlayer.smart_score,
            score_breakdown: previousPlayer.score_breakdown,
          };
        }
        return player;
      });
    },
    [snapshot]
  );

  // Clear snapshot
  const clearSnapshot = useCallback(() => {
    setSnapshot(null);
  }, []);

  return {
    snapshot,
    calculateDeltas,
    getTopChanges,
    createSnapshot,
    keepChanges,
    revert,
    clearSnapshot,
    hasSnapshot: snapshot !== null,
  };
};


