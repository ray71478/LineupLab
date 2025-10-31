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
    profiles,
    currentWeights,
    currentConfig,
    currentProfile,
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

  const [previousProfileId, setPreviousProfileId] = useState<number | null>(null);
  const [localPlayers, setLocalPlayers] = useState<PlayerScoreResponse[]>([]);
  const [isInitialized, setIsInitialized] = useState(false);
  const [showSnapshotModal, setShowSnapshotModal] = useState(false);
  const [isCalculatingInitial, setIsCalculatingInitial] = useState(false);
  const [defaultProfileLoadAttempted, setDefaultProfileLoadAttempted] = useState(false);

  // Snapshot management
  const {
    createSnapshot,
    keepChanges,
    revert,
    calculateDeltas,
    getTopChanges,
    hasSnapshot,
  } = useScoreSnapshot();

  // Auto-apply when profile changes (but not on initial load)
  useEffect(() => {
    // Only auto-apply if:
    // 1. We have a weekId
    // 2. We have a currentProfile
    // 3. The profile actually changed (not initial load)
    // 4. We're already initialized (scores have been calculated at least once)
    if (
      weekId &&
      currentProfile &&
      currentProfile.id !== previousProfileId &&
      previousProfileId !== null &&
      isInitialized
    ) {
      // Store previous scores before recalculation
      if (localPlayers.length > 0) {
        createSnapshot(localPlayers);
      }

      // Recalculate with new profile weights
      const applyProfile = async () => {
        try {
          // Use weights/config from the profile directly to ensure we have the latest values
          const profileWeights = currentProfile.weights;
          const profileConfig = currentProfile.config;
          const calculatedPlayers = await calculateScores(weekId, profileWeights, profileConfig);
          setLocalPlayers(calculatedPlayers);
        } catch (err) {
          console.error('Failed to calculate scores after profile change:', err);
        }
      };

      applyProfile();
    }

    // Update previous profile ID (track even on initial load to set baseline)
    if (currentProfile) {
      setPreviousProfileId(currentProfile.id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentProfile?.id, weekId, isInitialized]); // Only depend on profile ID, not full profile object

  // Reset initialization when week changes
  useEffect(() => {
    if (weekId) {
      setIsInitialized(false);
      setIsCalculatingInitial(false);
      setPreviousProfileId(null); // Reset profile tracking when week changes
      // Don't reset defaultProfileLoadAttempted - it's per session, not per week
    }
  }, [weekId]);

  // Listen for data refresh completion and recalculate Smart Scores
  useEffect(() => {
    const handleRefreshComplete = async (event: CustomEvent) => {
      // Only recalculate if we're already initialized (scores calculated at least once)
      if (weekId && currentWeights && currentConfig && isInitialized) {
        try {
          // Store previous scores before recalculation
          if (localPlayers.length > 0) {
            createSnapshot(localPlayers);
          }
          
          // Recalculate with updated opponent data from refresh
          const calculatedPlayers = await calculateScores(weekId, currentWeights, currentConfig);
          setLocalPlayers(calculatedPlayers);
          console.log('Smart Scores recalculated after data refresh');
        } catch (err) {
          console.error('Failed to recalculate scores after refresh:', err);
        }
      }
    };

    window.addEventListener('dataRefreshComplete', handleRefreshComplete as EventListener);

    return () => {
      window.removeEventListener('dataRefreshComplete', handleRefreshComplete as EventListener);
    };
  }, [weekId, currentWeights, currentConfig, isInitialized, localPlayers, calculateScores, createSnapshot]);

  // Track when default profile load attempt has completed
  useEffect(() => {
    // When currentProfile is set, it means the default profile load attempt has completed successfully
    // When profilesLoading becomes false AND currentProfile is still null, the default profile
    // load attempt has completed but failed (falling back to DEFAULT_WEIGHTS)
    if (currentProfile !== null) {
      setDefaultProfileLoadAttempted(true);
    } else if (!profilesLoading && !defaultProfileLoadAttempted) {
      // Profiles have loaded, but default profile hasn't loaded yet - wait a bit more
      // Give the default profile useEffect time to complete (it runs independently)
      const timeout = setTimeout(() => {
        setDefaultProfileLoadAttempted(true);
      }, 100); // Small delay to allow default profile useEffect to complete
      return () => clearTimeout(timeout);
    }
  }, [currentProfile, profilesLoading, defaultProfileLoadAttempted]);

  // Calculate scores when week or weights change
  // Wait for default profile to load before calculating initial scores
  // This ensures scores are calculated with the default profile weights, not hardcoded defaults
  useEffect(() => {
    // Only calculate initial scores if:
    // 1. We have a weekId
    // 2. We have currentWeights
    // 3. Default profile load attempt has completed (currentProfile set OR profiles loaded)
    // 4. We haven't initialized yet
    // 5. We're not already calculating
    //
    // The key: Wait for the default profile load attempt to complete before calculating.
    // This ensures we use the loaded default profile weights, not the hardcoded DEFAULT_WEIGHTS.
    const shouldCalculate = 
      weekId &&
      currentWeights &&
      defaultProfileLoadAttempted &&
      !isInitialized &&
      !isCalculatingInitial;
    
    if (shouldCalculate) {
      setIsCalculatingInitial(true);
      const initialCalculation = async () => {
        try {
          const calculatedPlayers = await calculateScores(weekId, currentWeights, currentConfig);
          setLocalPlayers(calculatedPlayers);
          setIsInitialized(true);
        } catch (err) {
          console.error('Failed to calculate initial scores:', err);
        } finally {
          setIsCalculatingInitial(false);
        }
      };
      initialCalculation();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [weekId, currentWeights, currentConfig, isInitialized, profilesLoading, currentProfile, defaultProfileLoadAttempted]); // isCalculatingInitial is intentionally excluded - it's a guard, not a trigger

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

      // Snapshot modal disabled - user prefers to see changes directly in table
      // Snapshot is still created for delta tracking in the table
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
      setIsCalculatingInitial(false);
      setDefaultProfileLoadAttempted(false); // Reset flag to allow recalculation with new default profile
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
