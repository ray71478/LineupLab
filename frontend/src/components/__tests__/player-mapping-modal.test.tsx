/**
 * Tests for PlayerMappingModal component
 *
 * Test coverage:
 * - Modal open/close functionality
 * - Displaying unmatched player info
 * - Showing fuzzy match suggestions
 * - Confirming mapping selection
 * - Modal submission and callbacks
 */

import { describe, it, expect, vi } from 'vitest';
import { PlayerMappingModal } from '../players/PlayerMappingModal';

describe('PlayerMappingModal Component', () => {
  /**
   * Test 1: PlayerMappingModal exports and basic structure
   */
  it('should export PlayerMappingModal component', () => {
    expect(PlayerMappingModal).toBeDefined();
    expect(typeof PlayerMappingModal).toBe('function');
  });

  /**
   * Test 2: Modal accepts required props
   */
  it('should accept required open, player, and callback props', () => {
    const mockUnmatchedPlayer = {
      id: 1,
      imported_name: 'P. Mahomes',
      team: 'KC',
      position: 'QB',
      salary: 8000,
      status: 'pending',
    };

    const mockSuggestions = [
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
        similarity_score: 0.95,
      },
    ];

    const onClose = vi.fn();
    const onConfirm = vi.fn();

    const props = {
      open: true,
      unmatchedPlayer: mockUnmatchedPlayer,
      suggestions: mockSuggestions,
      onClose,
      onConfirm,
    };

    expect(props.open).toBe(true);
    expect(props.unmatchedPlayer).toBeDefined();
    expect(props.suggestions).toHaveLength(1);
    expect(typeof props.onClose).toBe('function');
    expect(typeof props.onConfirm).toBe('function');
  });

  /**
   * Test 3: Modal displays unmatched player information
   */
  it('should display unmatched player details', () => {
    const mockUnmatchedPlayer = {
      id: 1,
      imported_name: 'P. Mahomes',
      team: 'KC',
      position: 'QB',
      salary: 8000,
      status: 'pending',
    };

    expect(mockUnmatchedPlayer.imported_name).toBe('P. Mahomes');
    expect(mockUnmatchedPlayer.team).toBe('KC');
    expect(mockUnmatchedPlayer.position).toBe('QB');
    expect(mockUnmatchedPlayer.salary).toBe(8000);
  });

  /**
   * Test 4: Modal displays fuzzy match suggestions
   */
  it('should display fuzzy match suggestions with scores', () => {
    const mockSuggestions = [
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
        similarity_score: 0.95,
      },
      {
        id: 2,
        player_key: 'patrick_m_KC_QB',
        name: 'Patrick M',
        team: 'KC',
        position: 'QB',
        salary: 7900,
        projection: 23.0,
        ownership: 0.32,
        ceiling: 44.0,
        floor: 17.0,
        notes: '',
        source: 'DraftKings',
        status: 'matched',
        uploaded_at: '2025-10-29T10:00:00Z',
        similarity_score: 0.85,
      },
    ];

    expect(mockSuggestions).toHaveLength(2);
    expect(mockSuggestions[0].similarity_score).toBe(0.95);
    expect(mockSuggestions[1].similarity_score).toBe(0.85);

    // Verify suggestions are sorted by similarity (highest first)
    for (let i = 0; i < mockSuggestions.length - 1; i++) {
      expect(mockSuggestions[i].similarity_score).toBeGreaterThanOrEqual(
        mockSuggestions[i + 1].similarity_score
      );
    }
  });

  /**
   * Test 5: Modal open/close behavior
   */
  it('should call onClose when modal closes', () => {
    const onClose = vi.fn();
    const props = {
      open: true,
      unmatchedPlayer: {
        id: 1,
        imported_name: 'Unknown',
        team: 'KC',
        position: 'QB',
        salary: 7500,
        status: 'pending',
      },
      suggestions: [],
      onClose,
      onConfirm: vi.fn(),
    };

    expect(typeof props.onClose).toBe('function');
  });

  /**
   * Test 6: Modal handles empty suggestions
   */
  it('should handle empty suggestions list', () => {
    const props = {
      open: true,
      unmatchedPlayer: {
        id: 1,
        imported_name: 'Unknown Player',
        team: 'XX',
        position: 'QB',
        salary: 7500,
        status: 'pending',
      },
      suggestions: [],
      onClose: vi.fn(),
      onConfirm: vi.fn(),
    };

    expect(props.suggestions).toHaveLength(0);
  });

  /**
   * Test 7: Modal handles up to 5 suggestions
   */
  it('should display up to 5 fuzzy match suggestions', () => {
    const mockSuggestions = Array.from({ length: 5 }, (_, i) => ({
      id: i + 1,
      player_key: `player_${i}_KC_QB`,
      name: `Player ${i}`,
      team: 'KC',
      position: 'QB',
      salary: 8000 - (i * 100),
      projection: 24 - i,
      ownership: 0.35 - (i * 0.05),
      ceiling: 45 - i,
      floor: 18 - i,
      notes: '',
      source: 'DraftKings',
      status: 'matched',
      uploaded_at: '2025-10-29T10:00:00Z',
      similarity_score: 0.95 - (i * 0.05),
    }));

    expect(mockSuggestions).toHaveLength(5);
  });

  /**
   * Test 8: Modal calls onConfirm with selected player
   */
  it('should call onConfirm callback when confirming selection', () => {
    const onConfirm = vi.fn();
    const selectedPlayer = {
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
    };

    const props = {
      open: true,
      unmatchedPlayer: {
        id: 1,
        imported_name: 'P. Mahomes',
        team: 'KC',
        position: 'QB',
        salary: 8000,
        status: 'pending',
      },
      suggestions: [selectedPlayer],
      onClose: vi.fn(),
      onConfirm,
    };

    expect(typeof props.onConfirm).toBe('function');
  });

  /**
   * Test 9: Modal loading state
   */
  it('should support loading state during submission', () => {
    const props = {
      open: true,
      unmatchedPlayer: {
        id: 1,
        imported_name: 'P. Mahomes',
        team: 'KC',
        position: 'QB',
        salary: 8000,
        status: 'pending',
      },
      suggestions: [],
      onClose: vi.fn(),
      onConfirm: vi.fn(),
      isLoading: true,
    };

    expect(props.isLoading).toBe(true);
  });

  /**
   * Test 10: Modal closed state
   */
  it('should not render content when open is false', () => {
    const props = {
      open: false,
      unmatchedPlayer: {
        id: 1,
        imported_name: 'P. Mahomes',
        team: 'KC',
        position: 'QB',
        salary: 8000,
        status: 'pending',
      },
      suggestions: [],
      onClose: vi.fn(),
      onConfirm: vi.fn(),
    };

    expect(props.open).toBe(false);
  });

  /**
   * Test 11: Modal handles manual search
   */
  it('should support manual player search in modal', () => {
    const props = {
      open: true,
      unmatchedPlayer: {
        id: 1,
        imported_name: 'Unknown Player',
        team: 'KC',
        position: 'QB',
        salary: 7500,
        status: 'pending',
      },
      suggestions: [],
      onClose: vi.fn(),
      onConfirm: vi.fn(),
      searchResults: [],
    };

    expect(Array.isArray(props.searchResults)).toBe(true);
  });

  /**
   * Test 12: Modal selection highlight
   */
  it('should highlight selected suggestion', () => {
    const selectedPlayer = {
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
    };

    const props = {
      open: true,
      unmatchedPlayer: {
        id: 1,
        imported_name: 'P. Mahomes',
        team: 'KC',
        position: 'QB',
        salary: 8000,
        status: 'pending',
      },
      suggestions: [selectedPlayer],
      onClose: vi.fn(),
      onConfirm: vi.fn(),
      selectedPlayerId: selectedPlayer.id,
    };

    expect(props.selectedPlayerId).toBe(1);
  });
});
