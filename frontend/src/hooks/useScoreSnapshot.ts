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
  snapshot: Map<number, number> | null;
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
  const [snapshot, setSnapshot] = useState<Map<number, number> | null>(null);

  // Create snapshot from current players
  const createSnapshot = useCallback((players: PlayerScoreResponse[]) => {
    const snapshotMap = new Map<number, number>();
    players.forEach((player) => {
      if (player.smart_score !== null && player.smart_score !== undefined) {
        snapshotMap.set(player.player_id, player.smart_score);
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
        const previousScore = snapshot.get(player.player_id);
        const currentScore = player.smart_score;

        if (
          previousScore !== undefined &&
          currentScore !== null &&
          currentScore !== undefined
        ) {
          const delta = currentScore - previousScore;
          deltas.set(player.player_id, delta);
        }
      });

      return deltas;
    },
    [snapshot]
  );

  // Get top 10 biggest changes
  const getTopChanges = useCallback(
    (currentPlayers: PlayerScoreResponse[]): ScoreChange[] => {
      const deltas = calculateDeltas(currentPlayers);
      const changes: ScoreChange[] = [];

      currentPlayers.forEach((player) => {
        const delta = deltas.get(player.player_id);
        const previousScore = snapshot?.get(player.player_id);

        if (delta !== undefined && previousScore !== undefined && player.smart_score !== null && player.smart_score !== undefined) {
          changes.push({
            playerId: player.player_id,
            playerName: player.name,
            previousScore,
            newScore: player.smart_score,
            delta,
            isTopChange: false, // Will be set after sorting
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
        const previousScore = snapshot.get(player.player_id);
        if (previousScore !== undefined) {
          return {
            ...player,
            smart_score: previousScore,
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


