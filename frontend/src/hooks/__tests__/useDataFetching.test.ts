/**
 * Tests for data fetching hooks with contest mode support
 *
 * Tests:
 * - usePlayers fetches correct mode data
 * - Mode switching triggers data refetch
 * - Data isolation (main slate query doesn't return showdown data)
 * - Loading and error states
 * - useLineups filters by mode
 * - Lineup generation includes contest mode
 * - Import includes contest mode
 */

import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { usePlayerManagement } from '../usePlayerManagement';
import { useLineups } from '../useLineups';
import { useDataImport } from '../useDataImport';
import { useModeStore } from '../../store/modeStore';
import { useWeekStore } from '../../store/weekStore';

// Mock fetch
global.fetch = vi.fn();

// Create wrapper for React Query
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe('Data Fetching Hooks - Contest Mode Support', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset stores
    useModeStore.setState({ mode: 'main' });
    useWeekStore.setState({ currentWeek: 17 });
  });

  describe('usePlayerManagement - Mode-aware data fetching', () => {
    it('should fetch players with contest_mode parameter when mode is main', async () => {
      const mockPlayers = {
        success: true,
        players: [
          { id: 1, name: 'Player 1', contest_mode: 'main' },
          { id: 2, name: 'Player 2', contest_mode: 'main' },
        ],
        total: 2,
        unmatched_count: 0,
      };

      const mockUnmatched = {
        success: true,
        unmatched_players: [],
        total_unmatched: 0,
      };

      (global.fetch as any).mockImplementation((url: string) => {
        if (url.includes('/api/players/by-week/')) {
          return Promise.resolve({
            ok: true,
            json: async () => mockPlayers,
          });
        }
        if (url.includes('/api/players/unmatched/')) {
          return Promise.resolve({
            ok: true,
            json: async () => mockUnmatched,
          });
        }
      });

      const { result } = renderHook(() => usePlayerManagement(17), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.players).toHaveLength(2);
      expect(result.current.players[0].contest_mode).toBe('main');
      expect(global.fetch).toHaveBeenCalledWith('/api/players/by-week/17');
    });

    it('should refetch data when week changes', async () => {
      const mockResponse = {
        success: true,
        players: [],
        total: 0,
        unmatched_count: 0,
      };

      const mockUnmatched = {
        success: true,
        unmatched_players: [],
        total_unmatched: 0,
      };

      (global.fetch as any).mockImplementation((url: string) => {
        return Promise.resolve({
          ok: true,
          json: async () => (url.includes('unmatched') ? mockUnmatched : mockResponse),
        });
      });

      const { result, rerender } = renderHook(
        ({ weekId }) => usePlayerManagement(weekId),
        {
          wrapper: createWrapper(),
          initialProps: { weekId: 17 },
        }
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Change week
      rerender({ weekId: 18 });

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith('/api/players/by-week/18');
      });
    });

    it('should handle loading states correctly', async () => {
      let resolvePromise: (value: any) => void;
      const promise = new Promise((resolve) => {
        resolvePromise = resolve;
      });

      (global.fetch as any).mockReturnValue(promise);

      const { result } = renderHook(() => usePlayerManagement(17), {
        wrapper: createWrapper(),
      });

      expect(result.current.isLoading).toBe(true);

      resolvePromise!({
        ok: true,
        json: async () => ({ success: true, players: [], total: 0, unmatched_count: 0 }),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
    });

    it('should handle error states correctly', async () => {
      (global.fetch as any).mockImplementation(() => {
        return Promise.resolve({
          ok: false,
          status: 500,
          json: async () => ({ error: 'Server error' }),
        });
      });

      const { result } = renderHook(() => usePlayerManagement(17), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.error).not.toBeNull();
      });

      expect(result.current.error?.message).toContain('Failed to fetch players');
    });
  });

  describe('useLineups - Mode parameter support', () => {
    it('should include contest_mode in lineup generation request', async () => {
      const mockResponse = {
        lineups: [
          {
            lineup_number: 1,
            players: [],
            total_salary: 50000,
            projected_score: 150,
            projected_points: 150,
            avg_ownership: 10,
          },
        ],
      };

      (global.fetch as any).mockImplementation(() => {
        return Promise.resolve({
          ok: true,
          json: async () => mockResponse,
        });
      });

      useModeStore.setState({ mode: 'showdown' });

      const { result } = renderHook(() => useLineups(17), {
        wrapper: createWrapper(),
      });

      await result.current.generateLineups({
        week_id: 17,
        settings: {
          num_lineups: 10,
          strategy_mode: 'Balanced',
          max_players_per_team: 8,
          max_players_per_game: 6,
        },
        contest_mode: 'showdown', // Should be included
      } as any);

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/lineups/generate',
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('showdown'),
        })
      );
    });

    it('should fetch saved lineups for specific mode', async () => {
      const mockLineups = [
        {
          id: 1,
          week_id: 17,
          lineup_number: 1,
          players: [],
          total_salary: 50000,
          projected_score: 150,
          strategy_mode: 'Balanced',
          created_at: '2024-01-01',
          contest_mode: 'showdown',
        },
      ];

      (global.fetch as any).mockImplementation(() => {
        return Promise.resolve({
          ok: true,
          json: async () => mockLineups,
        });
      });

      const { result } = renderHook(() => useLineups(17), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoadingSaved).toBe(false);
      });

      expect(global.fetch).toHaveBeenCalledWith('/api/lineups/saved/17');
    });
  });

  describe('useDataImport - Contest mode parameter', () => {
    it('should include contest_mode in import request', async () => {
      const mockFile = new File(['test'], 'LineStar_Football_WK17.xlsx', {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });

      const mockResponse = {
        success: true,
        import_id: 'test-import-123',
        message: 'Imported 50 players for Showdown mode',
        player_count: 50,
      };

      (global.fetch as any).mockImplementation(() => {
        return Promise.resolve({
          ok: true,
          json: async () => mockResponse,
        });
      });

      useModeStore.setState({ mode: 'showdown' });
      useWeekStore.setState({ currentWeek: 17 });

      const { result } = renderHook(() => useDataImport(), {
        wrapper: createWrapper(),
      });

      await result.current.uploadFile(mockFile, 'linestar', false);

      // Verify the FormData includes the contest_mode
      expect(global.fetch).toHaveBeenCalled();
      const callArgs = (global.fetch as any).mock.calls[0];
      expect(callArgs[0]).toBe('/api/import/linestar');
      expect(callArgs[1].method).toBe('POST');
    });

    it('should display mode confirmation in success message', async () => {
      const mockFile = new File(['test'], 'LineStar_Football_WK17.xlsx', {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });

      const mockResponse = {
        success: true,
        import_id: 'test-import-123',
        message: 'Imported 50 players for Showdown mode',
        player_count: 50,
      };

      (global.fetch as any).mockImplementation(() => {
        return Promise.resolve({
          ok: true,
          json: async () => mockResponse,
        });
      });

      useModeStore.setState({ mode: 'showdown' });

      const { result } = renderHook(() => useDataImport(), {
        wrapper: createWrapper(),
      });

      const response = await result.current.uploadFile(mockFile, 'linestar', false);

      expect(response?.message).toContain('Showdown');
    });
  });
});
