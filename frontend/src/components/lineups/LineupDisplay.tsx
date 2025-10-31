/**
 * LineupDisplay Component
 *
 * Displays generated lineups in a table format:
 * - Shows all lineups side-by-side
 * - Displays position, player name, team, salary, Smart Score, ownership
 * - Calculates totals (salary, Smart Score, avg ownership)
 * - Allows selection of lineups to save
 * - Highlights salary cap violations (shouldn't happen)
 *
 * Design: Dark theme with compact table layout
 * Mobile: Card-based layout for better UX on small screens
 * Accessibility: ARIA labels, keyboard navigation, screen reader support
 * Performance: Memoized components and optimized rendering
 */

import React, { useState, useMemo, useCallback } from 'react';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Checkbox,
  Chip,
  useTheme,
  useMediaQuery,
  Stack,
  Button,
  CircularProgress,
  Card,
  CardContent,
  Grid,
  Tooltip,
  Divider,
} from '@mui/material';
import type { GeneratedLineup } from '../../types/lineup.types';

export interface LineupDisplayProps {
  lineups: GeneratedLineup[];
  isLoading?: boolean;
  onSaveSelected?: (selectedLineups: GeneratedLineup[]) => void;
  isSaving?: boolean;
}

const POSITION_ORDER = ['QB', 'RB', 'RB', 'WR', 'WR', 'WR', 'TE', 'FLEX', 'DST'];

export const LineupDisplay: React.FC<LineupDisplayProps> = React.memo(({
  lineups,
  isLoading = false,
  onSaveSelected,
  isSaving = false,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const isTablet = useMediaQuery(theme.breakpoints.between('md', 'lg'));
  const [selectedLineups, setSelectedLineups] = useState<Set<number>>(new Set());

  const handleToggleLineup = useCallback((lineupNumber: number) => {
    setSelectedLineups((prev) => {
      const newSelected = new Set(prev);
      if (newSelected.has(lineupNumber)) {
        newSelected.delete(lineupNumber);
      } else {
        newSelected.add(lineupNumber);
      }
      return newSelected;
    });
  }, []);

  const handleSelectAll = useCallback(() => {
    setSelectedLineups((prev) => {
      if (prev.size === lineups.length) {
        return new Set();
      } else {
        return new Set(lineups.map(l => l.lineup_number));
      }
    });
  }, [lineups]);

  const handleSave = useCallback(() => {
    if (onSaveSelected && selectedLineups.size > 0) {
      const toSave = lineups.filter(l => selectedLineups.has(l.lineup_number));
      onSaveSelected(toSave);
    }
  }, [onSaveSelected, selectedLineups, lineups]);

  const handleKeyDown = useCallback((event: React.KeyboardEvent, lineupNumber: number) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleToggleLineup(lineupNumber);
    }
  }, [handleToggleLineup]);

  // Memoize processed lineup data for performance - MUST be called before any early returns
  const processedLineups = useMemo(() => {
    return lineups.map((lineup) => {
      const sortedPlayers = [...lineup.players].sort((a, b) => {
        const aIdx = POSITION_ORDER.indexOf(a.position);
        const bIdx = POSITION_ORDER.indexOf(b.position);
        return aIdx - bIdx;
      });

      const positionMap: Record<string, GeneratedLineup['players']> = {};
      sortedPlayers.forEach((player) => {
        const pos = player.position;
        if (!positionMap[pos]) {
          positionMap[pos] = [];
        }
        positionMap[pos].push(player);
      });

      const displayPlayers: (GeneratedLineup['players'][0] | null)[] = [];
      POSITION_ORDER.forEach((pos) => {
        if (pos === 'FLEX') {
          const flexPlayer = sortedPlayers.find(
            (p) => (p.position === 'RB' || p.position === 'WR' || p.position === 'TE') &&
              !displayPlayers.some((dp) => dp && dp.player_key === p.player_key)
          );
          displayPlayers.push(flexPlayer || null);
        } else {
          const playersAtPos = positionMap[pos] || [];
          const player = playersAtPos.find(
            (p) => !displayPlayers.some((dp) => dp && dp.player_key === p.player_key)
          );
          displayPlayers.push(player || null);
        }
      });

      return {
        ...lineup,
        displayPlayers,
        salaryViolation: lineup.total_salary > 50000,
      };
    });
  }, [lineups]);

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress sx={{ color: '#ff6b35' }} />
      </Box>
    );
  }

  if (lineups.length === 0) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center', backgroundColor: '#0a0a0a' }}>
        <Typography variant="body1" sx={{ color: 'text.secondary' }}>
          No lineups generated. Click "Generate Lineups" to create optimized lineups.
        </Typography>
      </Paper>
    );
  }

  return (
    <Box role="region" aria-label="Generated lineups">
      {/* Selection Controls */}
      <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
        <Stack direction="row" spacing={2} alignItems="center">
          <Checkbox
            checked={selectedLineups.size === lineups.length && lineups.length > 0}
            indeterminate={selectedLineups.size > 0 && selectedLineups.size < lineups.length}
            onChange={handleSelectAll}
            aria-label="Select all lineups"
            sx={{
              color: '#ff6b35',
              '&.Mui-checked': {
                color: '#ff6b35',
              },
            }}
          />
          <Typography variant="body2" sx={{ color: 'text.secondary' }} aria-live="polite">
            {selectedLineups.size} of {lineups.length} selected
          </Typography>
        </Stack>

        {onSaveSelected && selectedLineups.size > 0 && (
          <Button
            variant="contained"
            onClick={handleSave}
            disabled={isSaving}
            size="small"
            aria-label={`Save ${selectedLineups.size} lineup${selectedLineups.size > 1 ? 's' : ''}`}
            sx={{
              backgroundColor: '#ff6b35',
              '&:hover': {
                backgroundColor: '#e55a25',
              },
            }}
          >
            {isSaving ? 'Saving...' : `Save ${selectedLineups.size} Lineup${selectedLineups.size > 1 ? 's' : ''}`}
          </Button>
        )}
      </Box>

      {/* Mobile Card Layout */}
      {isMobile ? (
        <Grid container spacing={2}>
          {processedLineups.map((lineup, displayIndex) => {
            const isSelected = selectedLineups.has(lineup.lineup_number);
            const isBaseline = lineup.lineup_number < 0;
            // For baselines, use special labels. For regular lineups, use sequential display numbers (1-10)
            const regularLineupsBeforeThis = processedLineups.slice(0, displayIndex).filter(l => l.lineup_number >= 0).length;
            const displayNumber = isBaseline ? lineup.lineup_number : regularLineupsBeforeThis + 1;
            const baselineLabel = lineup.lineup_number === -1 ? '⭐ Best Score' : lineup.lineup_number === -2 ? '🎯 Best Proj' : `Lineup #${displayNumber}`;
            
            return (
              <Grid item xs={12} key={lineup.lineup_number}>
                <Card
                  sx={{
                    backgroundColor: isBaseline
                      ? 'rgba(76, 175, 80, 0.1)'
                      : isSelected ? 'rgba(255, 107, 53, 0.1)' : '#0a0a0a',
                    border: `1px solid ${isBaseline ? '#4caf50' : isSelected ? '#ff6b35' : 'rgba(255, 107, 53, 0.2)'}`,
                    borderLeft: isBaseline ? '4px solid #4caf50' : undefined,
                    cursor: isBaseline ? 'default' : 'pointer',
                    '&:hover': {
                      borderColor: isBaseline ? '#4caf50' : '#ff6b35',
                      backgroundColor: isBaseline
                        ? 'rgba(76, 175, 80, 0.15)'
                        : isSelected ? 'rgba(255, 107, 53, 0.15)' : 'rgba(255, 255, 255, 0.03)',
                    },
                  }}
                  onClick={!isBaseline ? () => handleToggleLineup(lineup.lineup_number) : undefined}
                  onKeyDown={!isBaseline ? (e) => handleKeyDown(e, lineup.lineup_number) : undefined}
                  role={!isBaseline ? "button" : undefined}
                  tabIndex={!isBaseline ? 0 : undefined}
                  aria-label={baselineLabel}
                  aria-pressed={!isBaseline ? isSelected : undefined}
                >
                  <CardContent sx={{ p: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {!isBaseline && (
                          <Checkbox
                            checked={isSelected}
                            onChange={() => handleToggleLineup(lineup.lineup_number)}
                            size="small"
                            sx={{
                              color: '#ff6b35',
                              '&.Mui-checked': {
                                color: '#ff6b35',
                              },
                            }}
                            onClick={(e) => e.stopPropagation()}
                          />
                        )}
                        <Typography 
                          variant="h6" 
                          sx={{ 
                            fontSize: '1rem', 
                            fontWeight: 600, 
                            color: isBaseline ? '#4caf50' : '#ff6b35' 
                          }}
                        >
                          {baselineLabel}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
                        <Chip
                          label={`Score: ${lineup.projected_score.toFixed(1)}`}
                          size="small"
                          sx={{
                            backgroundColor: '#ff6b35',
                            color: '#fff',
                            fontWeight: 600,
                            fontSize: '0.7rem',
                          }}
                        />
                        <Chip
                          label={`Proj: ${(lineup.projected_points ?? 0).toFixed(1)}`}
                          size="small"
                          sx={{
                            backgroundColor: '#4caf50',
                            color: '#fff',
                            fontWeight: 600,
                            fontSize: '0.7rem',
                          }}
                        />
                        <Chip
                          label={lineup.salaryViolation ? `$${(lineup.total_salary / 1000).toFixed(1)}K` : `$${(lineup.total_salary / 1000).toFixed(1)}K`}
                          size="small"
                          sx={{
                            backgroundColor: lineup.salaryViolation ? '#f44336' : 'rgba(255, 255, 255, 0.1)',
                            color: lineup.salaryViolation ? '#fff' : 'text.primary',
                            fontWeight: 600,
                            fontSize: '0.7rem',
                          }}
                        />
                      </Box>
                    </Box>
                    <Divider sx={{ borderColor: 'rgba(255, 107, 53, 0.2)', mb: 1.5 }} />
                    <Grid container spacing={1}>
                      {lineup.displayPlayers.map((player, idx) => (
                        <Grid item xs={6} sm={4} key={idx}>
                          <Box
                            sx={{
                              p: 1,
                              backgroundColor: 'rgba(255, 255, 255, 0.02)',
                              borderRadius: 1,
                              border: '1px solid rgba(255, 107, 53, 0.1)',
                            }}
                          >
                            <Typography variant="caption" sx={{ fontSize: '0.65rem', color: '#ff6b35', fontWeight: 600, display: 'block' }}>
                              {POSITION_ORDER[idx]}
                            </Typography>
                            {player ? (
                              <>
                                <Tooltip title={player.name} arrow>
                                  <Typography
                                    variant="caption"
                                    sx={{
                                      fontSize: '0.7rem',
                                      fontWeight: 600,
                                      display: 'block',
                                      overflow: 'hidden',
                                      textOverflow: 'ellipsis',
                                      whiteSpace: 'nowrap',
                                    }}
                                  >
                                    {player.name}
                                  </Typography>
                                </Tooltip>
                                <Typography variant="caption" sx={{ fontSize: '0.65rem', color: 'text.secondary' }}>
                                  {player.team} · ${(player.salary / 100).toFixed(0)}K
                                </Typography>
                                <Box sx={{ display: 'flex', gap: 0.75, alignItems: 'center', justifyContent: 'center' }}>
                                  <Typography variant="caption" sx={{ fontSize: '0.65rem', color: '#ff6b35', fontWeight: 600 }}>
                                    {player.smart_score.toFixed(1)}
                                  </Typography>
                                  <Typography variant="caption" sx={{ fontSize: '0.65rem', color: '#4caf50', fontWeight: 600 }}>
                                    {player.projection ? player.projection.toFixed(1) : '-'}
                                  </Typography>
                                </Box>
                              </>
                            ) : (
                              <Typography variant="caption" sx={{ color: 'text.disabled', fontSize: '0.65rem' }}>
                                -
                              </Typography>
                            )}
                          </Box>
                        </Grid>
                      ))}
                    </Grid>
                    <Box sx={{ mt: 1.5, display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'text.secondary' }}>
                      <span>Ownership: {(lineup.avg_ownership * 100).toFixed(1)}%</span>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      ) : (
        /* Desktop Table Layout */
        <TableContainer
          component={Paper}
          sx={{
            backgroundColor: '#0a0a0a',
            border: '1px solid rgba(255, 107, 53, 0.2)',
            maxHeight: '70vh',
            overflow: 'auto',
            '&::-webkit-scrollbar': {
              height: '8px',
              width: '8px',
            },
            '&::-webkit-scrollbar-track': {
              backgroundColor: '#1a1a1a',
            },
            '&::-webkit-scrollbar-thumb': {
              backgroundColor: '#ff6b35',
              borderRadius: '4px',
            },
          }}
          role="table"
          aria-label="Generated lineups table"
        >
          <Table stickyHeader size="small" sx={{ tableLayout: 'auto' }}>
            <TableHead>
              <TableRow>
                <TableCell
                  sx={{
                    backgroundColor: '#0a0a0a',
                    color: '#ff6b35',
                    fontWeight: 600,
                    fontSize: '0.7rem',
                    borderBottom: '1px solid rgba(255, 107, 53, 0.2)',
                    position: 'sticky',
                    left: 0,
                    zIndex: 3,
                    minWidth: 70,
                    maxWidth: 70,
                    padding: '8px 4px',
                  }}
                  scope="col"
                >
                  #
                </TableCell>
                {POSITION_ORDER.map((pos, idx) => (
                  <TableCell
                    key={`${pos}-${idx}`}
                    sx={{
                      backgroundColor: '#0a0a0a',
                      color: '#ff6b35',
                      fontWeight: 600,
                      fontSize: '0.7rem',
                      borderBottom: '1px solid rgba(255, 107, 53, 0.2)',
                      textAlign: 'center',
                      minWidth: 110,
                      maxWidth: 110,
                      padding: '8px 4px',
                    }}
                    scope="col"
                  >
                    {pos}
                  </TableCell>
                ))}
                <TableCell
                  sx={{
                    backgroundColor: '#0a0a0a',
                    color: '#ff6b35',
                    fontWeight: 600,
                    fontSize: '0.7rem',
                    borderBottom: '1px solid rgba(255, 107, 53, 0.2)',
                    textAlign: 'center',
                    minWidth: 70,
                    maxWidth: 70,
                    padding: '8px 4px',
                  }}
                  scope="col"
                >
                  $
                </TableCell>
                <TableCell
                  sx={{
                    backgroundColor: '#0a0a0a',
                    color: '#ff6b35',
                    fontWeight: 600,
                    fontSize: '0.7rem',
                    borderBottom: '1px solid rgba(255, 107, 53, 0.2)',
                    textAlign: 'center',
                    minWidth: 65,
                    maxWidth: 65,
                    padding: '8px 4px',
                  }}
                  scope="col"
                >
                  Score
                </TableCell>
                <TableCell
                  sx={{
                    backgroundColor: '#0a0a0a',
                    color: '#ff6b35',
                    fontWeight: 600,
                    fontSize: '0.7rem',
                    borderBottom: '1px solid rgba(255, 107, 53, 0.2)',
                    textAlign: 'center',
                    minWidth: 65,
                    maxWidth: 65,
                    padding: '8px 4px',
                  }}
                  scope="col"
                >
                  Proj
                </TableCell>
                <TableCell
                  sx={{
                    backgroundColor: '#0a0a0a',
                    color: '#ff6b35',
                    fontWeight: 600,
                    fontSize: '0.7rem',
                    borderBottom: '1px solid rgba(255, 107, 53, 0.2)',
                    textAlign: 'center',
                    minWidth: 65,
                    maxWidth: 65,
                    padding: '8px 4px',
                  }}
                  scope="col"
                >
                  Own%
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {processedLineups.map((lineup, displayIndex) => {
                const isSelected = selectedLineups.has(lineup.lineup_number);
                const isBaseline = lineup.lineup_number < 0;
                // For baselines, use special labels. For regular lineups, use sequential display numbers (1-10)
                const regularLineupsBeforeThis = processedLineups.slice(0, displayIndex).filter(l => l.lineup_number >= 0).length;
                const displayNumber = isBaseline ? lineup.lineup_number : regularLineupsBeforeThis + 1;
                const baselineLabel = lineup.lineup_number === -1 ? '⭐ Best Score' : lineup.lineup_number === -2 ? '🎯 Best Proj' : displayNumber.toString();
                
                return (
                  <TableRow
                    key={lineup.lineup_number}
                    sx={{
                      backgroundColor: isBaseline 
                        ? 'rgba(76, 175, 80, 0.1)' // Green tint for baselines
                        : isSelected ? 'rgba(255, 107, 53, 0.1)' : 'transparent',
                      borderLeft: isBaseline ? '3px solid #4caf50' : 'none',
                      '&:hover': {
                        backgroundColor: isBaseline
                          ? 'rgba(76, 175, 80, 0.15)'
                          : isSelected ? 'rgba(255, 107, 53, 0.15)' : 'rgba(255, 255, 255, 0.03)',
                      },
                    }}
                    role="row"
                    aria-selected={isSelected}
                  >
                    <TableCell
                      sx={{
                        position: 'sticky',
                        left: 0,
                        backgroundColor: isBaseline
                          ? 'rgba(76, 175, 80, 0.1)'
                          : isSelected ? 'rgba(255, 107, 53, 0.1)' : '#0a0a0a',
                        borderRight: '1px solid rgba(255, 107, 53, 0.2)',
                        zIndex: 2,
                        padding: '6px 4px',
                        maxWidth: 70,
                      }}
                      role="gridcell"
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        {!isBaseline && (
                          <Checkbox
                            checked={isSelected}
                            onChange={() => handleToggleLineup(lineup.lineup_number)}
                            size="small"
                            aria-label={`Select lineup ${lineup.lineup_number}`}
                            sx={{
                              color: '#ff6b35',
                              padding: '2px',
                              '&.Mui-checked': {
                                color: '#ff6b35',
                              },
                            }}
                          />
                        )}
                        <Tooltip title={isBaseline ? 'Baseline (unconstrained optimization)' : `Lineup ${lineup.lineup_number}`} arrow>
                          <Typography 
                            variant="caption" 
                            sx={{ 
                              fontSize: isBaseline ? '0.65rem' : '0.7rem', 
                              fontWeight: 600, 
                              lineHeight: 1,
                              color: isBaseline ? '#4caf50' : 'inherit',
                            }}
                          >
                            {baselineLabel}
                          </Typography>
                        </Tooltip>
                      </Box>
                    </TableCell>

                    {lineup.displayPlayers.map((player, idx) => (
                      <TableCell
                        key={idx}
                        sx={{
                          fontSize: '0.65rem',
                          color: 'text.primary',
                          textAlign: 'center',
                          borderBottom: '1px solid rgba(255, 107, 53, 0.1)',
                          padding: '6px 4px',
                          maxWidth: 110,
                        }}
                        role="gridcell"
                      >
                        {player ? (
                          <Tooltip title={`${player.name} - ${player.team} - Smart Score: ${player.smart_score.toFixed(1)} - Proj: ${player.projection ? player.projection.toFixed(1) : 'N/A'}`} arrow>
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.25 }}>
                              <Typography 
                                variant="caption" 
                                sx={{ 
                                  fontSize: '0.65rem', 
                                  fontWeight: 600, 
                                  display: 'block',
                                  lineHeight: 1.2,
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  whiteSpace: 'nowrap',
                                  color: 'text.primary',
                                }}
                              >
                                {player.name}
                              </Typography>
                              <Typography 
                                variant="caption" 
                                sx={{ 
                                  fontSize: '0.6rem', 
                                  color: 'text.secondary',
                                  lineHeight: 1.2,
                                }}
                              >
                                {player.team} · ${(player.salary / 100).toFixed(0)}K
                              </Typography>
                              <Box sx={{ display: 'flex', gap: 0.75, alignItems: 'center', justifyContent: 'center' }}>
                                <Typography 
                                  variant="caption" 
                                  sx={{ 
                                    fontSize: '0.6rem', 
                                    color: '#ff6b35',
                                    fontWeight: 600,
                                    lineHeight: 1.2,
                                  }}
                                >
                                  {player.smart_score.toFixed(1)}
                                </Typography>
                                <Typography 
                                  variant="caption" 
                                  sx={{ 
                                    fontSize: '0.6rem', 
                                    color: '#4caf50',
                                    fontWeight: 600,
                                    lineHeight: 1.2,
                                  }}
                                >
                                  {player.projection ? player.projection.toFixed(1) : '-'}
                                </Typography>
                              </Box>
                            </Box>
                          </Tooltip>
                        ) : (
                          <Typography variant="caption" sx={{ color: 'text.disabled', fontSize: '0.65rem' }}>
                            -
                          </Typography>
                        )}
                      </TableCell>
                    ))}

                    <TableCell
                      sx={{
                        fontSize: '0.7rem',
                        textAlign: 'center',
                        fontWeight: lineup.salaryViolation ? 600 : 'normal',
                        color: lineup.salaryViolation ? '#f44336' : 'text.primary',
                        padding: '6px 4px',
                        maxWidth: 70,
                      }}
                      role="gridcell"
                      aria-label={`Total salary: $${(lineup.total_salary / 1000).toFixed(1)}K`}
                    >
                      <Tooltip title={lineup.salaryViolation ? 'Salary cap violation!' : 'Total salary'} arrow>
                        <Box sx={{ color: 'inherit' }}>
                          ${(lineup.total_salary / 1000).toFixed(1)}K
                        </Box>
                      </Tooltip>
                    </TableCell>

                    <TableCell
                      sx={{
                        fontSize: '0.7rem',
                        textAlign: 'center',
                        fontWeight: 600,
                        color: '#ff6b35',
                        padding: '6px 4px',
                        maxWidth: 65,
                      }}
                      role="gridcell"
                    >
                      <Tooltip title="Smart Score" arrow>
                        <Box sx={{ color: '#ff6b35' }}>
                          {lineup.projected_score.toFixed(1)}
                        </Box>
                      </Tooltip>
                    </TableCell>

                    <TableCell
                      sx={{
                        fontSize: '0.7rem',
                        textAlign: 'center',
                        fontWeight: 600,
                        color: '#4caf50',
                        padding: '6px 4px',
                        maxWidth: 65,
                      }}
                      role="gridcell"
                    >
                      <Tooltip title="Projected fantasy points" arrow>
                        <Box sx={{ color: '#4caf50' }}>
                          {(lineup.projected_points ?? 0).toFixed(1)}
                        </Box>
                      </Tooltip>
                    </TableCell>

                    <TableCell
                      sx={{
                        fontSize: '0.7rem',
                        textAlign: 'center',
                        padding: '6px 4px',
                        maxWidth: 65,
                      }}
                      role="gridcell"
                    >
                      <Tooltip title="Average ownership percentage" arrow>
                        <Box>
                          {(lineup.avg_ownership * 100).toFixed(1)}%
                        </Box>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
});

LineupDisplay.displayName = 'LineupDisplay';

export default LineupDisplay;

