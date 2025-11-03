/**
 * Player Selection Page
 *
 * Allows users to select players for lineup optimization:
 * - Filter by Smart Score percentile (exclude bottom X%)
 * - Filter by minimum ITT (Implied Team Total)
 * - Filter by 3.5X value (ceiling >= salary/1000 * 3.5)
 * - Select all players meeting filters
 * - Select individual players
 * - Review and approve selected players
 * - Send to lineup creation page
 *
 * Mode-aware: Supports both Main Slate and Showdown contest modes
 * - Loads players based on active contest mode
 * - Clears selections when mode changes
 * - Displays mode in page header
 *
 * Design: Dark theme with orange accents
 */

import React, { useState, useMemo, useEffect, useRef } from 'react';
import {
  Container,
  Box,
  Typography,
  Stack,
  Button,
  TextField,
  Paper,
  Alert,
  CircularProgress,
  useTheme,
  useMediaQuery,
  Checkbox,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  FormControlLabel,
  Switch,
  Snackbar,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import { useWeekStore } from '../store/weekStore';
import { useSmartScore, useWeightProfile } from '../hooks';
import { useMode } from '../hooks/useMode';
import type { PlayerScoreResponse } from '../types/smartScore.types';

export const PlayerSelectionPage: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const navigate = useNavigate();

  const currentWeekNumber = useWeekStore((state) => state.currentWeek);
  const getCurrentWeekData = useWeekStore((state) => state.getCurrentWeekData);
  const currentWeek = getCurrentWeekData();
  const { mode } = useMode();

  const weekId = currentWeek?.id ?? null;
  const { currentWeights, currentConfig } = useWeightProfile();
  const { calculateScores, isCalculating } = useSmartScore(weekId);

  const [players, setPlayers] = useState<PlayerScoreResponse[]>([]);
  const [selectedPlayerIds, setSelectedPlayerIds] = useState<Set<number>>(new Set());
  // Mode-aware default filters: Showdown needs more lenient filters
  const [excludeBottomPercentile, setExcludeBottomPercentile] = useState<number>(
    mode === 'showdown' ? 1 : 15
  );
  const [minITT, setMinITT] = useState<number>(
    mode === 'showdown' ? 0.5 : 18.5
  );
  const [meets35XValue, setMeets35XValue] = useState<boolean>(
    mode === 'showdown' ? false : true
  );
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showModeChangeToast, setShowModeChangeToast] = useState(false);

  // Track previous mode to detect changes
  const previousMode = useRef<string | null>(null);

  // Initialize filters based on mode on mount
  useEffect(() => {
    // Set initial filters based on current mode
    setExcludeBottomPercentile(mode === 'showdown' ? 1 : 15);
    setMinITT(mode === 'showdown' ? 0.5 : 18.5);
    setMeets35XValue(mode === 'showdown' ? false : true);
    previousMode.current = mode;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Run only on mount

  // Load players with Smart Scores
  useEffect(() => {
    if (!weekId || !currentWeights || !currentConfig) return;

    let cancelled = false;

    const loadPlayers = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const calculatedPlayers = await calculateScores(weekId, currentWeights, currentConfig);
        if (!cancelled) {
          setPlayers(calculatedPlayers);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load players');
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    loadPlayers();

    // Cleanup function to prevent state updates if component unmounts
    return () => {
      cancelled = true;
    };
    // Note: We intentionally exclude calculateScores from dependencies to prevent infinite loops
    // The function reference changes on every render, but the actual calculation logic doesn't
    // We include mode to trigger refetch when mode changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [weekId, mode, JSON.stringify(currentWeights), JSON.stringify(currentConfig)]);

  // Clear player selections when mode changes
  useEffect(() => {
    // Skip on initial mount (when previousMode is null)
    if (previousMode.current === null) {
      previousMode.current = mode;
      return;
    }

    // Mode has changed - clear selections and reset filters to mode-appropriate defaults
    if (previousMode.current !== mode) {
      if (selectedPlayerIds.size > 0) {
        setSelectedPlayerIds(new Set());
        setShowModeChangeToast(true);
      }
      
      // Reset filters to mode-appropriate defaults
      setExcludeBottomPercentile(mode === 'showdown' ? 1 : 15);
      setMinITT(mode === 'showdown' ? 0.5 : 18.5);
      setMeets35XValue(mode === 'showdown' ? false : true);

      // Update previous mode reference
      previousMode.current = mode;
    }
  }, [mode, selectedPlayerIds.size]);

  // Filter players by percentile, ITT, and 3.5X value
  const filteredPlayers = useMemo(() => {
    let filtered = [...players];

    // Filter by Smart Score percentile (exclude bottom X%)
    if (excludeBottomPercentile > 0 && excludeBottomPercentile < 100) {
      // Filter out players with no Smart Score first
      const playersWithScores = filtered.filter(
        (p) => p.smart_score !== null && p.smart_score !== undefined
      );

      if (playersWithScores.length > 0) {
        // Sort by Smart Score (descending)
        const sorted = [...playersWithScores].sort(
          (a, b) => (b.smart_score || 0) - (a.smart_score || 0)
        );

        // Calculate how many to exclude from bottom
        const excludeCount = Math.floor(
          sorted.length * (excludeBottomPercentile / 100)
        );

        // Take top (100 - excludeBottomPercentile)%
        if (excludeCount > 0 && excludeCount < sorted.length) {
          const topPlayers = sorted.slice(0, sorted.length - excludeCount);
          const topPlayerIds = new Set(topPlayers.map((p) => p.player_id));
          filtered = filtered.filter((p) => topPlayerIds.has(p.player_id));
        }
      }
    }

    // Filter by minimum ITT
    if (minITT > 0) {
      filtered = filtered.filter(
        (p) =>
          p.implied_team_total !== null &&
          p.implied_team_total !== undefined &&
          p.implied_team_total >= minITT
      );
    }

    // Filter by 3.5X value (ceiling >= salary/1000 * 3.5)
    if (meets35XValue) {
      filtered = filtered.filter((p) => {
        if (!p.ceiling || p.salary <= 0) return false;
        const threePointFiveX = (p.salary / 1000) * 3.5;
        return p.ceiling >= threePointFiveX;
      });
    }

    return filtered;
  }, [players, excludeBottomPercentile, minITT, meets35XValue]);

  // Select all players meeting filters
  const handleSelectAll = () => {
    const newSelection = new Set(selectedPlayerIds);
    filteredPlayers.forEach((player) => {
      newSelection.add(player.player_id);
    });
    setSelectedPlayerIds(newSelection);
  };

  // Deselect all players
  const handleDeselectAll = () => {
    setSelectedPlayerIds(new Set());
  };

  // Toggle individual player selection
  const handleTogglePlayer = (playerId: number) => {
    const newSelection = new Set(selectedPlayerIds);
    if (newSelection.has(playerId)) {
      newSelection.delete(playerId);
    } else {
      newSelection.add(playerId);
    }
    setSelectedPlayerIds(newSelection);
  };

  // Get selected players - MUST use filteredPlayers to respect threshold
  const selectedPlayers = useMemo(() => {
    return filteredPlayers.filter((p) => selectedPlayerIds.has(p.player_id));
  }, [filteredPlayers, selectedPlayerIds]);

  // Navigate to lineup page with selected players
  const handleApproveAndSend = () => {
    if (selectedPlayers.length === 0) {
      setError('Please select at least one player');
      return;
    }

    // Store selected players in sessionStorage for the lineup page
    sessionStorage.setItem('selectedPlayers', JSON.stringify(selectedPlayers));
    navigate('/lineups');
  };

  // Get selection summary
  const selectionSummary = useMemo(() => {
    const byPosition: Record<string, number> = {};
    selectedPlayers.forEach((p) => {
      byPosition[p.position] = (byPosition[p.position] || 0) + 1;
    });
    return byPosition;
  }, [selectedPlayers]);

  // Get mode display name
  const modeDisplayName = mode === 'showdown' ? 'Showdown' : 'Main Slate';

  if (!weekId) {
    return (
      <Container maxWidth="xl">
        <Box sx={{ py: 4 }}>
          <Alert severity="info">Please select a week to select players.</Alert>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: { xs: 2, md: 4 } }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, mb: 1, color: '#ff6b35' }}>
          Select Players for Lineup Optimization
        </Typography>
        <Typography variant="body2" sx={{ color: 'text.secondary' }}>
          {modeDisplayName} - Week {currentWeek?.week_number} - {currentWeek?.season}
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Selection Controls */}
      <Paper
        sx={{
          p: 2,
          mb: 3,
          backgroundColor: '#0a0a0a',
          border: '1px solid rgba(255, 107, 53, 0.2)',
          borderRadius: 2,
        }}
      >
        <Stack spacing={2} direction={{ xs: 'column', md: 'row' }} alignItems="center">
          <TextField
            label="Exclude Bottom %"
            type="number"
            value={excludeBottomPercentile}
            onChange={(e) => setExcludeBottomPercentile(Math.max(0, Math.min(100, parseFloat(e.target.value) || 0)))}
            placeholder="0"
            inputProps={{ min: 0, max: 100, step: 1 }}
            size="small"
            sx={{
              flex: { xs: 1, md: '0 0 150px' },
              '& .MuiInputBase-input': {
                fontSize: '0.875rem',
              },
            }}
            helperText="Exclude bottom X% by Smart Score"
          />

          <TextField
            label="Min ITT"
            type="number"
            value={minITT}
            onChange={(e) => setMinITT(Math.max(0, parseFloat(e.target.value) || 0))}
            placeholder="0"
            inputProps={{ min: 0, step: 0.5 }}
            size="small"
            sx={{
              flex: { xs: 1, md: '0 0 120px' },
              '& .MuiInputBase-input': {
                fontSize: '0.875rem',
              },
            }}
            helperText="Minimum Implied Team Total"
          />

          <FormControlLabel
            control={
              <Switch
                checked={meets35XValue}
                onChange={(e) => setMeets35XValue(e.target.checked)}
                size="small"
                sx={{
                  '& .MuiSwitch-switchBase.Mui-checked': {
                    color: '#ff6b35',
                  },
                  '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                    backgroundColor: '#ff6b35',
                  },
                }}
              />
            }
            label={
              <Typography variant="caption" sx={{ fontSize: '0.75rem' }}>
                3.5X ≤ Ceiling
              </Typography>
            }
            sx={{ ml: 1 }}
          />

          <Button
            variant="outlined"
            onClick={handleSelectAll}
            disabled={filteredPlayers.length === 0}
            sx={{
              borderColor: '#ff6b35',
              color: '#ff6b35',
              '&:hover': {
                borderColor: '#ff6b35',
                backgroundColor: 'rgba(255, 107, 53, 0.1)',
              },
            }}
          >
            Select All ({filteredPlayers.length})
          </Button>

          <Button
            variant="outlined"
            onClick={handleDeselectAll}
            disabled={selectedPlayerIds.size === 0}
            sx={{
              borderColor: '#666',
              color: 'text.secondary',
              '&:hover': {
                borderColor: '#999',
                backgroundColor: 'rgba(255, 255, 255, 0.05)',
              },
            }}
          >
            Deselect All
          </Button>

          <Box sx={{ flex: 1 }} />

          <Chip
            label={`${selectedPlayerIds.size} selected`}
            sx={{
              backgroundColor: '#ff6b35',
              color: '#fff',
              fontWeight: 600,
            }}
          />
        </Stack>

        {/* Selection Summary */}
        {selectedPlayerIds.size > 0 && (
          <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid rgba(255, 255, 255, 0.1)' }}>
            <Typography variant="caption" sx={{ color: 'text.secondary', mb: 1, display: 'block' }}>
              Selection Summary:
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap">
              {Object.entries(selectionSummary).map(([position, count]) => (
                <Chip
                  key={position}
                  label={`${position}: ${count}`}
                  size="small"
                  sx={{
                    backgroundColor: 'rgba(255, 107, 53, 0.2)',
                    color: '#ff6b35',
                  }}
                />
              ))}
            </Stack>
          </Box>
        )}
      </Paper>

      {/* Players Table with Selection */}
      {isLoading || isCalculating ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress sx={{ color: '#ff6b35' }} />
        </Box>
      ) : (
        <Box sx={{ position: 'relative' }}>
          {/* Add checkbox column to existing table */}
          <TableContainer
            component={Paper}
            sx={{
              backgroundColor: '#0a0a0a',
              border: '1px solid rgba(255, 107, 53, 0.2)',
              borderRadius: 2,
              maxHeight: '60vh',
              overflow: 'auto',
            }}
          >
            <Table stickyHeader size="small">
              <TableHead>
                <TableRow>
                  <TableCell
                    sx={{
                      backgroundColor: '#0a0a0a',
                      borderBottom: '1px solid rgba(255, 107, 53, 0.2)',
                      width: 50,
                    }}
                  >
                    <Checkbox
                      checked={filteredPlayers.length > 0 && filteredPlayers.every((p) => selectedPlayerIds.has(p.player_id))}
                      indeterminate={
                        filteredPlayers.some((p) => selectedPlayerIds.has(p.player_id)) &&
                        !filteredPlayers.every((p) => selectedPlayerIds.has(p.player_id))
                      }
                      onChange={(e) => {
                        if (e.target.checked) {
                          handleSelectAll();
                        } else {
                          handleDeselectAll();
                        }
                      }}
                      sx={{
                        color: '#ff6b35',
                        '&.Mui-checked': {
                          color: '#ff6b35',
                        },
                      }}
                    />
                  </TableCell>
                  <TableCell sx={{ backgroundColor: '#0a0a0a', borderBottom: '1px solid rgba(255, 107, 53, 0.2)', fontWeight: 600 }}>
                    Name
                  </TableCell>
                  <TableCell sx={{ backgroundColor: '#0a0a0a', borderBottom: '1px solid rgba(255, 107, 53, 0.2)', fontWeight: 600 }}>
                    Position
                  </TableCell>
                  <TableCell sx={{ backgroundColor: '#0a0a0a', borderBottom: '1px solid rgba(255, 107, 53, 0.2)', fontWeight: 600 }}>
                    Team
                  </TableCell>
                  <TableCell
                    align="right"
                    sx={{ backgroundColor: '#0a0a0a', borderBottom: '1px solid rgba(255, 107, 53, 0.2)', fontWeight: 600 }}
                  >
                    Salary
                  </TableCell>
                  <TableCell
                    align="right"
                    sx={{ backgroundColor: '#0a0a0a', borderBottom: '1px solid rgba(255, 107, 53, 0.2)', fontWeight: 600 }}
                  >
                    Smart Score
                  </TableCell>
                  <TableCell
                    align="right"
                    sx={{ backgroundColor: '#0a0a0a', borderBottom: '1px solid rgba(255, 107, 53, 0.2)', fontWeight: 600 }}
                  >
                    ITT
                  </TableCell>
                  <TableCell
                    align="right"
                    sx={{ backgroundColor: '#0a0a0a', borderBottom: '1px solid rgba(255, 107, 53, 0.2)', fontWeight: 600 }}
                  >
                    Ceiling
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredPlayers.map((player) => {
                  const isSelected = selectedPlayerIds.has(player.player_id);
                  return (
                    <TableRow
                      key={player.player_id}
                      hover
                      onClick={() => handleTogglePlayer(player.player_id)}
                      sx={{
                        cursor: 'pointer',
                        backgroundColor: isSelected ? 'rgba(255, 107, 53, 0.1)' : 'inherit',
                        '&:hover': {
                          backgroundColor: isSelected ? 'rgba(255, 107, 53, 0.15)' : 'rgba(255, 255, 255, 0.05)',
                        },
                      }}
                    >
                      <TableCell>
                        <Checkbox
                          checked={isSelected}
                          onChange={() => handleTogglePlayer(player.player_id)}
                          onClick={(e) => e.stopPropagation()}
                          sx={{
                            color: '#ff6b35',
                            '&.Mui-checked': {
                              color: '#ff6b35',
                            },
                          }}
                        />
                      </TableCell>
                      <TableCell>{player.name}</TableCell>
                      <TableCell>
                        <Chip
                          label={player.position}
                          size="small"
                          sx={{
                            backgroundColor: 'rgba(255, 107, 53, 0.2)',
                            color: '#ff6b35',
                            fontSize: '0.7rem',
                          }}
                        />
                      </TableCell>
                      <TableCell>{player.team}</TableCell>
                      <TableCell align="right">${((player.salary || 0) / 1000).toFixed(1)}K</TableCell>
                      <TableCell align="right">
                        <Typography
                          sx={{
                            color: '#ff6b35',
                            fontWeight: 600,
                            fontSize: '0.875rem',
                          }}
                        >
                          {player.smart_score?.toFixed(1) || '-'}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography
                          sx={{
                            color: 'text.secondary',
                            fontSize: '0.875rem',
                          }}
                        >
                          {player.implied_team_total?.toFixed(1) || '-'}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography
                          sx={{
                            color: 'text.secondary',
                            fontSize: '0.875rem',
                          }}
                        >
                          {player.ceiling?.toFixed(1) || '-'}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}

      {/* Action Buttons */}
      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
        <Button
          variant="outlined"
          onClick={() => navigate('/smart-score')}
          sx={{
            borderColor: '#666',
            color: 'text.secondary',
            '&:hover': {
              borderColor: '#999',
            },
          }}
        >
          Back to Smart Scores
        </Button>

        <Button
          variant="contained"
          onClick={handleApproveAndSend}
          disabled={selectedPlayerIds.size === 0}
          startIcon={<CheckCircleIcon />}
          endIcon={<ArrowForwardIcon />}
          sx={{
            backgroundColor: '#ff6b35',
            py: 1.5,
            px: 4,
            fontSize: '1rem',
            fontWeight: 600,
            '&:hover': {
              backgroundColor: '#e55a25',
            },
            '&:disabled': {
              backgroundColor: '#666',
            },
          }}
        >
          Approve & Send to Lineups ({selectedPlayerIds.size} players)
        </Button>
      </Box>

      {/* Mode Change Toast Notification */}
      <Snackbar
        open={showModeChangeToast}
        autoHideDuration={4000}
        onClose={() => setShowModeChangeToast(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setShowModeChangeToast(false)}
          severity="info"
          sx={{
            backgroundColor: '#1a1a1a',
            border: '1px solid rgba(255, 107, 53, 0.3)',
            '& .MuiAlert-icon': {
              color: '#ff6b35',
            },
          }}
        >
          Mode changed. Player selections cleared.
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default PlayerSelectionPage;
