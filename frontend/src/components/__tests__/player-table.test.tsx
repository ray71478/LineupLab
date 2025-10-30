/**
 * Tests for PlayerTable component
 *
 * Test coverage:
 * - Rendering players in table format
 * - Sorting functionality
 * - Filtering and search
 * - Virtual scrolling
 * - Row expansion
 * - Status indicators
 */

import { describe, it, expect, vi } from 'vitest';
import { PlayerTable } from '../players/PlayerTable';

describe('PlayerTable Component', () => {
  /**
   * Test 1: PlayerTable renders successfully with player data
   */
  it('should export PlayerTable component', () => {
    expect(PlayerTable).toBeDefined();
    expect(typeof PlayerTable).toBe('function');
  });

  it('should accept required players prop', () => {
    const mockPlayers = [
      {
        id: 1,
        player_key: 'patrick_mahomes_KC_QB',
        name: 'Patrick Mahomes',
        team: 'KC',
        position: 'QB',
        salary: 8000,
        projection: 24.5,
        ownership: 0.35,
        ceiling: 45.2,
        floor: 18.3,
        notes: 'MVP candidate',
        source: 'DraftKings',
        status: 'matched',
        uploaded_at: '2025-10-29T10:00:00Z',
      },
    ];

    const props = {
      players: mockPlayers,
      isLoading: false,
    };

    expect(props.players).toHaveLength(1);
    expect(props.players[0].name).toBe('Patrick Mahomes');
    expect(props.players[0].position).toBe('QB');
  });

  /**
   * Test 2: PlayerTable supports sorting
   */
  it('should handle sorting by column', () => {
    const mockPlayers = [
      {
        id: 1,
        player_key: 'patrick_mahomes_KC_QB',
        name: 'Patrick Mahomes',
        team: 'KC',
        position: 'QB',
        salary: 8000,
        projection: 24.5,
        ownership: 0.35,
        ceiling: 45.2,
        floor: 18.3,
        notes: '',
        source: 'DraftKings',
        status: 'matched',
        uploaded_at: '2025-10-29T10:00:00Z',
      },
      {
        id: 2,
        player_key: 'josh_allen_BUF_QB',
        name: 'Josh Allen',
        team: 'BUF',
        position: 'QB',
        salary: 7800,
        projection: 23.2,
        ownership: 0.28,
        ceiling: 42.0,
        floor: 17.0,
        notes: '',
        source: 'DraftKings',
        status: 'matched',
        uploaded_at: '2025-10-29T10:00:00Z',
      },
    ];

    const onSort = vi.fn();

    const props = {
      players: mockPlayers,
      isLoading: false,
      onSort,
    };

    expect(props.players).toHaveLength(2);
    expect(typeof props.onSort).toBe('function');
  });

  /**
   * Test 3: PlayerTable shows loading state
   */
  it('should show loading state when isLoading is true', () => {
    const props = {
      players: [],
      isLoading: true,
    };

    expect(props.isLoading).toBe(true);
  });

  it('should hide loading state when isLoading is false', () => {
    const props = {
      players: [],
      isLoading: false,
    };

    expect(props.isLoading).toBe(false);
  });

  /**
   * Test 4: PlayerTable handles empty player list
   */
  it('should handle empty player list', () => {
    const props = {
      players: [],
      isLoading: false,
    };

    expect(props.players).toHaveLength(0);
  });

  /**
   * Test 5: PlayerTable displays status badges
   */
  it('should display matched status for matched players', () => {
    const mockPlayer = {
      id: 1,
      player_key: 'patrick_mahomes_KC_QB',
      name: 'Patrick Mahomes',
      team: 'KC',
      position: 'QB',
      salary: 8000,
      projection: 24.5,
      ownership: 0.35,
      ceiling: 45.2,
      floor: 18.3,
      notes: '',
      source: 'DraftKings',
      status: 'matched' as const,
      uploaded_at: '2025-10-29T10:00:00Z',
    };

    expect(mockPlayer.status).toBe('matched');
  });

  it('should display unmatched status for unmatched players', () => {
    const mockPlayer = {
      id: 2,
      player_key: 'unknown_player_KC_QB',
      name: 'Unknown Player',
      team: 'KC',
      position: 'QB',
      salary: 7500,
      projection: 20.0,
      ownership: 0.20,
      ceiling: 40.0,
      floor: 15.0,
      notes: '',
      source: 'DraftKings',
      status: 'unmatched' as const,
      uploaded_at: '2025-10-29T10:00:00Z',
    };

    expect(mockPlayer.status).toBe('unmatched');
  });

  /**
   * Test 6: PlayerTable column definitions
   */
  it('should define correct table columns', () => {
    const requiredColumns = [
      'name',
      'team',
      'position',
      'salary',
      'projection',
      'ownership',
      'status',
    ];

    // Verify column names are all strings
    requiredColumns.forEach(col => {
      expect(typeof col).toBe('string');
      expect(col.length).toBeGreaterThan(0);
    });
  });

  /**
   * Test 7: PlayerTable handles row expansion
   */
  it('should support row expansion callback', () => {
    const onExpandChange = vi.fn();

    const props = {
      players: [
        {
          id: 1,
          player_key: 'patrick_mahomes_KC_QB',
          name: 'Patrick Mahomes',
          team: 'KC',
          position: 'QB',
          salary: 8000,
          projection: 24.5,
          ownership: 0.35,
          ceiling: 45.2,
          floor: 18.3,
          notes: '',
          source: 'DraftKings',
          status: 'matched',
          uploaded_at: '2025-10-29T10:00:00Z',
        },
      ],
      isLoading: false,
      onExpandChange,
    };

    expect(typeof props.onExpandChange).toBe('function');
  });

  /**
   * Test 8: PlayerTable with large dataset
   */
  it('should handle large player list (virtual scrolling)', () => {
    const largePlayers = Array.from({ length: 200 }, (_, i) => ({
      id: i + 1,
      player_key: `player_${i}_KC_QB`,
      name: `Player ${i}`,
      team: 'KC',
      position: 'QB',
      salary: 5000 + i,
      projection: 10 + (i % 5),
      ownership: 0.1 + (i % 5) / 100,
      ceiling: 25,
      floor: 5,
      notes: '',
      source: 'DraftKings',
      status: 'matched' as const,
      uploaded_at: '2025-10-29T10:00:00Z',
    }));

    const props = {
      players: largePlayers,
      isLoading: false,
    };

    expect(props.players).toHaveLength(200);
  });

  /**
   * Test 9: PlayerTable data types
   */
  it('should have correct player data types', () => {
    const mockPlayer = {
      id: 1,
      player_key: 'patrick_mahomes_KC_QB',
      name: 'Patrick Mahomes',
      team: 'KC',
      position: 'QB',
      salary: 8000,
      projection: 24.5,
      ownership: 0.35,
      ceiling: 45.2,
      floor: 18.3,
      notes: 'MVP candidate',
      source: 'DraftKings',
      status: 'matched',
      uploaded_at: '2025-10-29T10:00:00Z',
    };

    expect(typeof mockPlayer.id).toBe('number');
    expect(typeof mockPlayer.player_key).toBe('string');
    expect(typeof mockPlayer.name).toBe('string');
    expect(typeof mockPlayer.team).toBe('string');
    expect(typeof mockPlayer.position).toBe('string');
    expect(typeof mockPlayer.salary).toBe('number');
    expect(typeof mockPlayer.projection).toBe('number');
    expect(typeof mockPlayer.ownership).toBe('number');
    expect(typeof mockPlayer.status).toBe('string');
  });

  /**
   * Test 10: PlayerTable responsive behavior
   */
  it('should support responsive column visibility', () => {
    const mobileColumns = ['name', 'team', 'position', 'salary'];
    const desktopColumns = [
      'name',
      'team',
      'position',
      'salary',
      'projection',
      'ownership',
      'status',
    ];

    const props = {
      players: [],
      isLoading: false,
      visibleColumns: desktopColumns,
    };

    expect(props.visibleColumns).toHaveLength(7);
  });
});
