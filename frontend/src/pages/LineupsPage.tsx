/**
 * Lineups Page
 *
 * Main page for lineup optimizer:
 * - Configuration panel for optimization settings
 * - Generate button
 * - Display generated lineups
 * - Save selected lineups
 *
 * Design: Dark theme with orange accents
 */

import React, { useState, useEffect } from 'react';
import {
  Container,
  Box,
  Typography,
  Stack,
  Button,
  Grid,
  Alert,
  CircularProgress,
  useTheme,
  useMediaQuery,
  Chip,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useWeekStore } from '../store/weekStore';
import { useLineups } from '../hooks/useLineups';
import { useWeightProfile } from '../hooks';
import type { OptimizationSettings, GeneratedLineup } from '../types/lineup.types';
import type { PlayerScoreResponse } from '../types/smartScore.types';

const LineupConfigurationPanel = React.lazy(() =>
  import('../components/lineups/LineupConfigurationPanel').then((m) => ({
    default: m.LineupConfigurationPanel,
  }))
);
const LineupDisplay = React.lazy(() =>
  import('../components/lineups/LineupDisplay').then((m) => ({
    default: m.LineupDisplay,
  }))
);
const LineupGenerationProgress = React.lazy(() =>
  import('../components/lineups/LineupGenerationProgress')
);

const DEFAULT_SETTINGS: OptimizationSettings = {
  num_lineups: 10,
  strategy_mode: 'Tournament',  // Default to Tournament mode (ceiling + ownership leverage)
  max_players_per_team: 4,
  max_players_per_game: 5,
  stacking_rules: {
    qb_wr_stack_enabled: true,  // Default ON for tournaments
    bring_back_enabled: true,    // Default ON for tournaments
  },
};

export const LineupsPage: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const isTablet = useMediaQuery(theme.breakpoints.between('md', 'lg'));
  const navigate = useNavigate();

  const currentWeekNumber = useWeekStore((state) => state.currentWeek);
  const getCurrentWeekData = useWeekStore((state) => state.getCurrentWeekData);
  const currentWeek = getCurrentWeekData();

  const weekId = currentWeek?.id ?? null;
  const { profiles, currentProfile } = useWeightProfile();
  const { generateLineups, isGenerating, saveLineups, isSaving } = useLineups(weekId);

  const [settings, setSettings] = useState<OptimizationSettings>(DEFAULT_SETTINGS);
  const [generatedLineups, setGeneratedLineups] = useState<GeneratedLineup[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [selectedPlayers, setSelectedPlayers] = useState<PlayerScoreResponse[] | null>(null);

  // Load selected players from sessionStorage on mount
  useEffect(() => {
    const stored = sessionStorage.getItem('selectedPlayers');
    if (stored) {
      try {
        const players = JSON.parse(stored) as PlayerScoreResponse[];
        setSelectedPlayers(players);
        // Clear sessionStorage after loading to avoid stale data
        sessionStorage.removeItem('selectedPlayers');
      } catch (err) {
        console.error('Failed to parse selected players:', err);
      }
    }
  }, []);

  const handleGenerate = async () => {
    if (!weekId) {
      setError('Please select a week first');
      return;
    }

    setError(null);
    try {
      const request: LineupOptimizationRequest = {
        week_id: weekId,
        settings,
      };

      // Only include selected_player_ids if players were actually selected
      if (selectedPlayers && selectedPlayers.length > 0) {
        request.selected_player_ids = selectedPlayers.map((p) => p.player_id);
      }

      const lineups = await generateLineups(request);
      setGeneratedLineups(lineups);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate lineups');
      setGeneratedLineups([]);
    }
  };

  const handleSaveSelected = async (selectedLineups: GeneratedLineup[]) => {
    if (!weekId) {
      setError('Please select a week first');
      return;
    }

    setError(null);
    try {
      await saveLineups({
        week_id: weekId,
        lineups: selectedLineups,
        weight_profile_id: currentProfile?.id,
        strategy_mode: settings.strategy_mode,
      });
      // Clear selected lineups after saving
      setGeneratedLineups([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save lineups');
    }
  };

  if (!weekId) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ py: 4 }}>
          <Typography variant="h4" sx={{ fontWeight: 600, mb: 2 }}>
            Lineup Generator
          </Typography>
          <Alert severity="info">Please select a week to generate lineups.</Alert>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl">
      <Box sx={{ py: { xs: 2, md: 4 } }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4" sx={{ fontWeight: 600, color: '#ff6b35' }}>
            Lineup Generator
          </Typography>
          {selectedPlayers && selectedPlayers.length > 0 && (
            <Chip
              label={`${selectedPlayers.length} players selected`}
              sx={{
                backgroundColor: '#ff6b35',
                color: '#fff',
                fontWeight: 600,
              }}
              onDelete={() => {
                setSelectedPlayers(null);
                navigate('/player-selection');
              }}
            />
          )}
        </Box>

        {selectedPlayers && selectedPlayers.length > 0 && (
          <Alert severity="info" sx={{ mb: 2 }}>
            Using {selectedPlayers.length} selected players for optimization. 
            <Button
              size="small"
              onClick={() => navigate('/player-selection')}
              sx={{ ml: 1, color: '#ff6b35' }}
            >
              Change Selection
            </Button>
          </Alert>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Progress Indicator */}
        {isGenerating && (
          <React.Suspense fallback={<CircularProgress />}>
            <LineupGenerationProgress 
              isGenerating={isGenerating}
              numLineups={settings.num_lineups}
              numPlayers={selectedPlayers?.length || undefined}
            />
          </React.Suspense>
        )}

        {/* Configuration Panel - Stacked vertically on top */}
        <Box sx={{ mb: 3 }}>
          <Box sx={{ mb: 2 }}>
            <React.Suspense fallback={<CircularProgress />}>
              <LineupConfigurationPanel settings={settings} onSettingsChange={setSettings} />
            </React.Suspense>
          </Box>

          {/* Generate Button */}
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              onClick={handleGenerate}
              disabled={isGenerating || (selectedPlayers !== null && selectedPlayers.length === 0)}
              sx={{
                backgroundColor: '#ff6b35',
                py: 1.5,
                px: 4,
                fontSize: '0.875rem',
                fontWeight: 600,
                '&:hover': {
                  backgroundColor: '#e55a25',
                },
                '&:disabled': {
                  backgroundColor: '#666',
                },
              }}
            >
              {isGenerating ? (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CircularProgress size={16} sx={{ color: '#fff' }} />
                  Generating...
                </Box>
              ) : (
                'Generate Lineups'
              )}
            </Button>
            {selectedPlayers === null && (
              <Button
                variant="outlined"
                onClick={() => navigate('/player-selection')}
                sx={{
                  borderColor: '#ff6b35',
                  color: '#ff6b35',
                  '&:hover': {
                    borderColor: '#ff6b35',
                    backgroundColor: 'rgba(255, 107, 53, 0.1)',
                  },
                }}
              >
                Select Players First
              </Button>
            )}
          </Box>
        </Box>

        {/* Lineups Display - Full width below */}
        <Box>
          <React.Suspense fallback={<CircularProgress />}>
            <LineupDisplay
              lineups={generatedLineups}
              isLoading={isGenerating}
              onSaveSelected={handleSaveSelected}
              isSaving={isSaving}
            />
          </React.Suspense>
        </Box>
      </Box>
    </Container>
  );
};

export default LineupsPage;
