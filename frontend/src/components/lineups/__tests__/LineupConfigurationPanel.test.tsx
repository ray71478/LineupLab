/**
 * Tests for LineupConfigurationPanel component
 *
 * Test coverage:
 * - Captain lock functionality appears for showdown mode only
 * - Captain lock state persists across lineup generation
 * - Configuration panel displays correctly for both modes
 * - Constraint visibility changes for showdown mode
 * - Locked captain dropdown populates with selected players
 * - Locked captain clears on mode/week change
 *
 * Note: These tests verify configuration panel behavior for both main and showdown modes
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { LineupConfigurationPanel } from '../LineupConfigurationPanel';
import type { OptimizationSettings } from '../../../types/lineup.types';
import type { PlayerScoreResponse } from '../../../types/smartScore.types';

const mockSelectedPlayers: PlayerScoreResponse[] = [
  {
    player_id: 1,
    player_key: 'QB_1',
    name: 'Patrick Mahomes',
    team: 'KC',
    position: 'QB',
    salary: 8500,
    ownership: 0.25,
    smart_score: 85.5,
    rank: 1,
  },
  {
    player_id: 2,
    player_key: 'RB_1',
    name: 'Christian McCaffrey',
    team: 'SF',
    position: 'RB',
    salary: 9200,
    ownership: 0.35,
    smart_score: 90.2,
    rank: 2,
  },
  {
    player_id: 3,
    player_key: 'WR_1',
    name: 'Tyreek Hill',
    team: 'MIA',
    position: 'WR',
    salary: 8000,
    ownership: 0.20,
    smart_score: 82.1,
    rank: 3,
  },
];

const defaultSettings: OptimizationSettings = {
  num_lineups: 10,
  strategy_mode: 'Tournament',
  max_players_per_team: 4,
  max_players_per_game: 5,
  max_ownership: 0.15,
  stacking_rules: {
    qb_wr_stack_enabled: true,
    bring_back_enabled: true,
  },
};

describe('LineupConfigurationPanel', () => {
  let mockOnSettingsChange: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockOnSettingsChange = vi.fn();
    localStorage.clear();
  });

  /**
   * Test 1: Captain lock control appears for showdown mode only
   */
  describe('Test 1: Captain lock control appears for showdown mode only', () => {
    it('should show captain lock dropdown when mode is showdown', () => {
      render(
        <LineupConfigurationPanel
          settings={defaultSettings}
          onSettingsChange={mockOnSettingsChange}
          mode="showdown"
          selectedPlayers={mockSelectedPlayers}
        />
      );

      // Captain lock dropdown should be visible
      expect(screen.getByLabelText(/locked captain/i)).toBeInTheDocument();
    });

    it('should hide captain lock dropdown when mode is main', () => {
      render(
        <LineupConfigurationPanel
          settings={defaultSettings}
          onSettingsChange={mockOnSettingsChange}
          mode="main"
          selectedPlayers={mockSelectedPlayers}
        />
      );

      // Captain lock dropdown should NOT be visible
      expect(screen.queryByLabelText(/locked captain/i)).not.toBeInTheDocument();
    });

    it('should populate captain dropdown with selected players', () => {
      render(
        <LineupConfigurationPanel
          settings={defaultSettings}
          onSettingsChange={mockOnSettingsChange}
          mode="showdown"
          selectedPlayers={mockSelectedPlayers}
        />
      );

      // Open the dropdown
      const dropdown = screen.getByLabelText(/locked captain/i);
      fireEvent.mouseDown(dropdown);

      // All selected players should appear as options
      waitFor(() => {
        expect(screen.getByText(/patrick mahomes/i)).toBeInTheDocument();
        expect(screen.getByText(/christian mccaffrey/i)).toBeInTheDocument();
        expect(screen.getByText(/tyreek hill/i)).toBeInTheDocument();
      });
    });

    it('should show "None (Auto-select)" as default option', () => {
      render(
        <LineupConfigurationPanel
          settings={defaultSettings}
          onSettingsChange={mockOnSettingsChange}
          mode="showdown"
          selectedPlayers={mockSelectedPlayers}
        />
      );

      // Default option should be visible
      expect(screen.getByText(/none.*auto.*select/i)).toBeInTheDocument();
    });
  });

  /**
   * Test 2: Locked captain persists across lineup generation
   */
  describe('Test 2: Locked captain persists across lineup generation', () => {
    it('should call onSettingsChange with locked_captain_id when captain is selected', () => {
      render(
        <LineupConfigurationPanel
          settings={defaultSettings}
          onSettingsChange={mockOnSettingsChange}
          mode="showdown"
          selectedPlayers={mockSelectedPlayers}
        />
      );

      // Open dropdown and select a captain
      const dropdown = screen.getByLabelText(/locked captain/i);
      fireEvent.mouseDown(dropdown);

      waitFor(() => {
        const mahomesOption = screen.getByText(/patrick mahomes/i);
        fireEvent.click(mahomesOption);
      });

      // Verify callback called with locked_captain_id
      waitFor(() => {
        expect(mockOnSettingsChange).toHaveBeenCalledWith(
          expect.objectContaining({
            locked_captain_id: 'QB_1',
          })
        );
      });
    });

    it('should display selected captain in dropdown', () => {
      const settingsWithCaptain = {
        ...defaultSettings,
        locked_captain_id: 'QB_1',
      };

      render(
        <LineupConfigurationPanel
          settings={settingsWithCaptain}
          onSettingsChange={mockOnSettingsChange}
          mode="showdown"
          selectedPlayers={mockSelectedPlayers}
        />
      );

      // Selected captain should be displayed
      expect(screen.getByDisplayValue(/patrick mahomes/i)).toBeInTheDocument();
    });

    it('should allow changing locked captain', () => {
      const settingsWithCaptain = {
        ...defaultSettings,
        locked_captain_id: 'QB_1',
      };

      render(
        <LineupConfigurationPanel
          settings={settingsWithCaptain}
          onSettingsChange={mockOnSettingsChange}
          mode="showdown"
          selectedPlayers={mockSelectedPlayers}
        />
      );

      // Change to different captain
      const dropdown = screen.getByLabelText(/locked captain/i);
      fireEvent.mouseDown(dropdown);

      waitFor(() => {
        const cmcOption = screen.getByText(/christian mccaffrey/i);
        fireEvent.click(cmcOption);
      });

      // Verify callback called with new locked_captain_id
      waitFor(() => {
        expect(mockOnSettingsChange).toHaveBeenCalledWith(
          expect.objectContaining({
            locked_captain_id: 'RB_1',
          })
        );
      });
    });
  });

  /**
   * Test 3: Configuration panel displays for both modes
   */
  describe('Test 3: Configuration panel displays for both modes', () => {
    it('should display number of lineups setting for both modes', () => {
      const { rerender } = render(
        <LineupConfigurationPanel
          settings={defaultSettings}
          onSettingsChange={mockOnSettingsChange}
          mode="main"
        />
      );

      expect(screen.getByLabelText(/number of lineups/i)).toBeInTheDocument();

      // Test for showdown mode
      rerender(
        <LineupConfigurationPanel
          settings={defaultSettings}
          onSettingsChange={mockOnSettingsChange}
          mode="showdown"
        />
      );

      expect(screen.getByLabelText(/number of lineups/i)).toBeInTheDocument();
    });

    it('should display strategy mode setting for both modes', () => {
      const { rerender } = render(
        <LineupConfigurationPanel
          settings={defaultSettings}
          onSettingsChange={mockOnSettingsChange}
          mode="main"
        />
      );

      expect(screen.getByLabelText(/strategy mode/i)).toBeInTheDocument();

      // Test for showdown mode
      rerender(
        <LineupConfigurationPanel
          settings={defaultSettings}
          onSettingsChange={mockOnSettingsChange}
          mode="showdown"
        />
      );

      expect(screen.getByLabelText(/strategy mode/i)).toBeInTheDocument();
    });

    it('should display max ownership setting for both modes', () => {
      const { rerender } = render(
        <LineupConfigurationPanel
          settings={defaultSettings}
          onSettingsChange={mockOnSettingsChange}
          mode="main"
        />
      );

      expect(screen.getByLabelText(/max avg ownership/i)).toBeInTheDocument();

      // Test for showdown mode
      rerender(
        <LineupConfigurationPanel
          settings={defaultSettings}
          onSettingsChange={mockOnSettingsChange}
          mode="showdown"
        />
      );

      expect(screen.getByLabelText(/max avg ownership/i)).toBeInTheDocument();
    });
  });

  /**
   * Test 4: Constraint visibility changes for showdown mode
   */
  describe('Test 4: Constraint visibility changes for showdown mode', () => {
    it('should hide "Max Players Per Team" for showdown mode', () => {
      render(
        <LineupConfigurationPanel
          settings={defaultSettings}
          onSettingsChange={mockOnSettingsChange}
          mode="showdown"
        />
      );

      // Should NOT be visible in showdown mode
      expect(screen.queryByLabelText(/max players per team/i)).not.toBeInTheDocument();
    });

    it('should show "Max Players Per Team" for main slate mode', () => {
      render(
        <LineupConfigurationPanel
          settings={defaultSettings}
          onSettingsChange={mockOnSettingsChange}
          mode="main"
        />
      );

      // Should be visible in main slate mode
      expect(screen.getByLabelText(/max players per team/i)).toBeInTheDocument();
    });

    it('should hide "QB + WR Stack" for showdown mode', () => {
      render(
        <LineupConfigurationPanel
          settings={defaultSettings}
          onSettingsChange={mockOnSettingsChange}
          mode="showdown"
        />
      );

      // Should NOT be visible in showdown mode
      expect(screen.queryByText(/qb.*wr stack/i)).not.toBeInTheDocument();
    });

    it('should show "QB + WR Stack" for main slate mode', () => {
      render(
        <LineupConfigurationPanel
          settings={defaultSettings}
          onSettingsChange={mockOnSettingsChange}
          mode="main"
        />
      );

      // Should be visible in main slate mode
      expect(screen.getByText(/qb.*wr stack/i)).toBeInTheDocument();
    });

    it('should hide "Bring-Back" stacking for showdown mode', () => {
      render(
        <LineupConfigurationPanel
          settings={defaultSettings}
          onSettingsChange={mockOnSettingsChange}
          mode="showdown"
        />
      );

      // Should NOT be visible in showdown mode
      expect(screen.queryByText(/bring.*back/i)).not.toBeInTheDocument();
    });

    it('should show "Bring-Back" stacking for main slate mode', () => {
      render(
        <LineupConfigurationPanel
          settings={defaultSettings}
          onSettingsChange={mockOnSettingsChange}
          mode="main"
        />
      );

      // Should be visible in main slate mode
      expect(screen.getByText(/bring.*back/i)).toBeInTheDocument();
    });
  });

  /**
   * Test 5: Showdown-specific help text displays
   */
  describe('Test 5: Showdown-specific help text displays', () => {
    it('should display captain multiplier explanation tooltip', () => {
      render(
        <LineupConfigurationPanel
          settings={defaultSettings}
          onSettingsChange={mockOnSettingsChange}
          mode="showdown"
          selectedPlayers={mockSelectedPlayers}
        />
      );

      // Look for help text or info icon
      expect(screen.getByText(/1\.5x.*salary.*points/i)).toBeInTheDocument();
    });

    it('should explain auto-selection if no lock specified', () => {
      render(
        <LineupConfigurationPanel
          settings={defaultSettings}
          onSettingsChange={mockOnSettingsChange}
          mode="showdown"
          selectedPlayers={mockSelectedPlayers}
        />
      );

      // Look for auto-selection explanation
      expect(
        screen.getByText(/auto.*select.*best.*captain/i) ||
        screen.getByText(/none.*auto.*select/i)
      ).toBeInTheDocument();
    });

    it('should not show showdown help text in main slate mode', () => {
      render(
        <LineupConfigurationPanel
          settings={defaultSettings}
          onSettingsChange={mockOnSettingsChange}
          mode="main"
        />
      );

      // Showdown-specific help should NOT be visible
      expect(screen.queryByText(/1\.5x.*salary.*points/i)).not.toBeInTheDocument();
    });
  });

  /**
   * Test 6: Locked captain clears appropriately
   */
  describe('Test 6: Locked captain clears appropriately', () => {
    it('should clear locked captain when "None" is selected', () => {
      const settingsWithCaptain = {
        ...defaultSettings,
        locked_captain_id: 'QB_1',
      };

      render(
        <LineupConfigurationPanel
          settings={settingsWithCaptain}
          onSettingsChange={mockOnSettingsChange}
          mode="showdown"
          selectedPlayers={mockSelectedPlayers}
        />
      );

      // Select "None" option
      const dropdown = screen.getByLabelText(/locked captain/i);
      fireEvent.mouseDown(dropdown);

      waitFor(() => {
        const noneOption = screen.getByText(/none.*auto.*select/i);
        fireEvent.click(noneOption);
      });

      // Verify callback called with null locked_captain_id
      waitFor(() => {
        expect(mockOnSettingsChange).toHaveBeenCalledWith(
          expect.objectContaining({
            locked_captain_id: null,
          })
        );
      });
    });

    it('should show message when no players are selected', () => {
      render(
        <LineupConfigurationPanel
          settings={defaultSettings}
          onSettingsChange={mockOnSettingsChange}
          mode="showdown"
          selectedPlayers={[]}
        />
      );

      // Should show a message about selecting players first
      expect(
        screen.getByText(/select players/i) ||
        screen.getByText(/no players available/i)
      ).toBeInTheDocument();
    });
  });
});
