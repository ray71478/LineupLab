/**
 * Player Selection Page
 *
 * Allows users to select players for lineup optimization:
 * - Filter by Smart Score threshold
 * - Select all players >= threshold
 * - Select individual players
 * - Review and approve selected players
 * - Send to lineup creation page
 *
 * Design: Dark theme with orange accents
 */

import React, { useState, useMemo, useEffect } from 'react';
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
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import { useWeekStore } from '../store/weekStore';
import { useSmartScore, useWeightProfile } from '../hooks';
import type { PlayerScoreResponse } from '../types/smartScore.types';

export const PlayerSelectionPage: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const navigate = useNavigate();

  const currentWeekNumber = useWeekStore((state) => state.currentWeek);
  const getCurrentWeekData = useWeekStore((state) => state.getCurrentWeekData);
  const currentWeek = getCurrentWeekData();

  const weekId = currentWeek?.id ?? null;
  const { currentWeights, currentConfig } = useWeightProfile();
  const { calculateScores, isCalculating } = useSmartScore(weekId);

  const [players, setPlayers] = useState<PlayerScoreResponse[]>([]);
  const [selectedPlayerIds, setSelectedPlayerIds] = useState<Set<number>>(new Set());
  const [smartScoreThreshold, setSmartScoreThreshold] = useState<number>(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load players with Smart Scores
  useEffect(() => {
    if (!weekId || !currentWeights || !currentConfig) return;

    const loadPlayers = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const calculatedPlayers = await calculateScores(weekId, currentWeights, currentConfig);
        setPlayers(calculatedPlayers);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load players');
      } finally {
        setIsLoading(false);
      }
    };

    loadPlayers();
  }, [weekId, currentWeights, currentConfig, calculateScores]);

  // Filter players by threshold
  const filteredPlayers = useMemo(() => {
    if (smartScoreThreshold <= 0) return players;
    return players.filter(
      (p) => p.smart_score !== null && p.smart_score !== undefined && p.smart_score >= smartScoreThreshold
    );
  }, [players, smartScoreThreshold]);

  // Select all players meeting threshold
  const handleSelectAll = () => {
    const newSelection = new Set(selectedPlayerIds);
    filteredPlayers.forEach((player) => {
      if (player.smart_score !== null && player.smart_score !== undefined) {
        newSelection.add(player.player_id);
      }
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

  // Get selected players
  const selectedPlayers = useMemo(() => {
    return players.filter((p) => selectedPlayerIds.has(p.player_id));
  }, [players, selectedPlayerIds]);

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
          Week {currentWeek?.week_number} - {currentWeek?.season}
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
            label="Smart Score Threshold"
            type="number"
            value={smartScoreThreshold}
            onChange={(e) => setSmartScoreThreshold(parseFloat(e.target.value) || 0)}
            placeholder="0 (no filter)"
            size="small"
            sx={{
              flex: { xs: 1, md: '0 0 200px' },
              '& .MuiInputBase-input': {
                fontSize: '0.875rem',
              },
            }}
            helperText="Select all players >= this threshold"
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
    </Container>
  );
};

export default PlayerSelectionPage;

