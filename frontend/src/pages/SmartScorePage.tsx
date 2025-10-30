/**
 * Smart Score Page
 *
 * Main page component for Smart Score Engine with:
 * - Weight adjustment panel (sidebar)
 * - Player table with Smart Scores
 * - Recalculation workflow
 * - Profile management
 *
 * Design: Factory.ai inspired (black, white, orange accents)
 *
 * Mobile Responsive:
 * - Stacked layout on mobile
 * - Collapsible weight panel
 * - Full-width table
 */

import React, { useEffect, useState } from 'react';
import {
  Container,
  Box,
  Typography,
  CircularProgress,
  Stack,
  Alert,
  useTheme,
  useMediaQuery,
  Grid,
} from '@mui/material';
import { useWeekStore } from '../store/weekStore';
import { useSmartScore, useWeightProfile, useScoreSnapshot } from '../hooks';
import type { PlayerScoreResponse, WeightProfile, ScoreConfig } from '../types/smartScore.types';

// Placeholder components - will be created next
const WeightAdjustmentPanel = React.lazy(() => import('../components/smart-score/WeightAdjustmentPanel').then(m => ({ default: m.WeightAdjustmentPanel })));
const SmartScoreTable = React.lazy(() => import('../components/smart-score/SmartScoreTable').then(m => ({ default: m.SmartScoreTable })));
const SnapshotModal = React.lazy(() => import('../components/smart-score/SnapshotModal').then(m => ({ default: m.SnapshotModal })));

export const SmartScorePage: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const isTablet = useMediaQuery(theme.breakpoints.between('md', 'lg'));

  const currentWeekNumber = useWeekStore((state) => state.currentWeek);
  const getCurrentWeekData = useWeekStore((state) => state.getCurrentWeekData);
  const currentWeek = getCurrentWeekData();

  // Weight profile management
  const {
    currentWeights,
    currentConfig,
    isLoading: profilesLoading,
    error: profilesError,
    loadDefaultProfile,
    updateWeights,
    updateConfig,
  } = useWeightProfile();

  // Smart Score data
  const weekId = currentWeek?.id ?? null;
  const {
    players,
    isLoading: scoresLoading,
    error: scoresError,
    calculateScores,
    isCalculating,
  } = useSmartScore(weekId);

  const [localPlayers, setLocalPlayers] = useState<PlayerScoreResponse[]>([]);
  const [isInitialized, setIsInitialized] = useState(false);
  const [showSnapshotModal, setShowSnapshotModal] = useState(false);

  // Snapshot management
  const {
    createSnapshot,
    keepChanges,
    revert,
    calculateDeltas,
    getTopChanges,
    hasSnapshot,
  } = useScoreSnapshot();

  // Calculate scores when week or weights change
  useEffect(() => {
    if (weekId && currentWeights && !isInitialized) {
      const initialCalculation = async () => {
        try {
          const calculatedPlayers = await calculateScores(weekId, currentWeights, currentConfig);
          setLocalPlayers(calculatedPlayers);
          setIsInitialized(true);
        } catch (err) {
          console.error('Failed to calculate initial scores:', err);
        }
      };
      initialCalculation();
    }
  }, [weekId, currentWeights, currentConfig, isInitialized, calculateScores]);

  // Update local players when players from hook change
  useEffect(() => {
    if (players.length > 0) {
      setLocalPlayers(players);
    }
  }, [players]);

  const handleApply = async () => {
    if (!weekId) return;

    try {
      // Store previous scores before recalculation
      if (localPlayers.length > 0) {
        createSnapshot(localPlayers);
      }

      // Calculate new scores
      const calculatedPlayers = await calculateScores(weekId, currentWeights, currentConfig);
      setLocalPlayers(calculatedPlayers);

      // Show snapshot modal if there are changes
      const changes = getTopChanges(calculatedPlayers);
      if (changes.length > 0) {
        setShowSnapshotModal(true);
      }
    } catch (err) {
      console.error('Failed to calculate scores:', err);
    }
  };

  const handleKeepChanges = () => {
    keepChanges();
    setShowSnapshotModal(false);
  };

  const handleRevert = () => {
    const revertedPlayers = revert(localPlayers);
    setLocalPlayers(revertedPlayers);
    setShowSnapshotModal(false);
  };

  const handleCloseSnapshotModal = () => {
    setShowSnapshotModal(false);
  };

  const handleReset = async () => {
    try {
      await loadDefaultProfile();
      setIsInitialized(false);
    } catch (err) {
      console.error('Failed to load default profile:', err);
    }
  };

  const handleWeightsChange = (weights: WeightProfile) => {
    updateWeights(weights);
  };

  const handleConfigChange = (config: ScoreConfig) => {
    updateConfig(config);
  };

  const isLoading = scoresLoading || profilesLoading || isCalculating;
  const error = scoresError || profilesError;

  if (!currentWeek) {
    return (
      <Container maxWidth="xl">
        <Box sx={{ py: 4 }}>
          <Alert severity="info">
            Please select a week to view Smart Scores.
          </Alert>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: { xs: 2, md: 4 } }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
          Smart Score Engine
        </Typography>
        <Typography variant="body2" sx={{ color: 'text.secondary' }}>
          Week {currentWeek.week_number} - {currentWeek.season}
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error.message || 'An error occurred while loading Smart Scores'}
        </Alert>
      )}

      {isLoading && !isInitialized ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Grid container spacing={3}>
          {/* Weight Adjustment Panel */}
          <Grid item xs={12} md={4} lg={3}>
            <Box
              sx={{
                position: { md: 'sticky' },
                top: { md: 24 },
                maxHeight: { md: 'calc(100vh - 48px)' },
                overflowY: { md: 'auto' },
              }}
            >
              <React.Suspense fallback={<CircularProgress />}>
                <WeightAdjustmentPanel
                  weights={currentWeights}
                  config={currentConfig}
                  onApply={handleApply}
                  onReset={handleReset}
                  onWeightsChange={handleWeightsChange}
                  onConfigChange={handleConfigChange}
                  isCalculating={isCalculating}
                />
              </React.Suspense>
            </Box>
          </Grid>

          {/* Smart Score Table */}
          <Grid item xs={12} md={8} lg={9}>
            <React.Suspense fallback={<CircularProgress />}>
              <SmartScoreTable
                players={localPlayers}
                isLoading={isLoading}
                scoreDeltas={hasSnapshot ? calculateDeltas(localPlayers) : new Map()}
              />
            </React.Suspense>
          </Grid>
        </Grid>
      )}

      {/* Snapshot Modal */}
      {showSnapshotModal && (
        <React.Suspense fallback={null}>
          <SnapshotModal
            open={showSnapshotModal}
            changes={getTopChanges(localPlayers)}
            onKeepChanges={handleKeepChanges}
            onRevert={handleRevert}
            onClose={handleCloseSnapshotModal}
          />
        </React.Suspense>
      )}
    </Container>
  );
};

export default SmartScorePage;
