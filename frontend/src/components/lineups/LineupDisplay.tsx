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
 */

import React, { useState } from 'react';
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
} from '@mui/material';
import type { GeneratedLineup } from '../../types/lineup.types';

export interface LineupDisplayProps {
  lineups: GeneratedLineup[];
  isLoading?: boolean;
  onSaveSelected?: (selectedLineups: GeneratedLineup[]) => void;
  isSaving?: boolean;
}

const POSITION_ORDER = ['QB', 'RB', 'RB', 'WR', 'WR', 'WR', 'TE', 'FLEX', 'DST'];

export const LineupDisplay: React.FC<LineupDisplayProps> = ({
  lineups,
  isLoading = false,
  onSaveSelected,
  isSaving = false,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [selectedLineups, setSelectedLineups] = useState<Set<number>>(new Set());

  const handleToggleLineup = (lineupNumber: number) => {
    const newSelected = new Set(selectedLineups);
    if (newSelected.has(lineupNumber)) {
      newSelected.delete(lineupNumber);
    } else {
      newSelected.add(lineupNumber);
    }
    setSelectedLineups(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedLineups.size === lineups.length) {
      setSelectedLineups(new Set());
    } else {
      setSelectedLineups(new Set(lineups.map(l => l.lineup_number)));
    }
  };

  const handleSave = () => {
    if (onSaveSelected && selectedLineups.size > 0) {
      const toSave = lineups.filter(l => selectedLineups.has(l.lineup_number));
      onSaveSelected(toSave);
    }
  };

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
    <Box>
      {/* Selection Controls */}
      <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Stack direction="row" spacing={2} alignItems="center">
          <Checkbox
            checked={selectedLineups.size === lineups.length && lineups.length > 0}
            indeterminate={selectedLineups.size > 0 && selectedLineups.size < lineups.length}
            onChange={handleSelectAll}
            sx={{
              color: '#ff6b35',
              '&.Mui-checked': {
                color: '#ff6b35',
              },
            }}
          />
          <Typography variant="body2" sx={{ color: 'text.secondary' }}>
            {selectedLineups.size} of {lineups.length} selected
          </Typography>
        </Stack>

        {onSaveSelected && selectedLineups.size > 0 && (
          <Button
            variant="contained"
            onClick={handleSave}
            disabled={isSaving}
            size="small"
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

      {/* Lineups Table */}
      <TableContainer
        component={Paper}
        sx={{
          backgroundColor: '#0a0a0a',
          border: '1px solid rgba(255, 107, 53, 0.2)',
          maxHeight: '70vh',
          overflow: 'auto',
        }}
      >
        <Table stickyHeader size="small">
          <TableHead>
            <TableRow>
              <TableCell
                sx={{
                  backgroundColor: '#0a0a0a',
                  color: '#ff6b35',
                  fontWeight: 600,
                  fontSize: '0.75rem',
                  borderBottom: '1px solid rgba(255, 107, 53, 0.2)',
                  position: 'sticky',
                  left: 0,
                  zIndex: 3,
                  minWidth: 100,
                }}
              >
                Lineup
              </TableCell>
              {POSITION_ORDER.map((pos, idx) => (
                <TableCell
                  key={`${pos}-${idx}`}
                  sx={{
                    backgroundColor: '#0a0a0a',
                    color: '#ff6b35',
                    fontWeight: 600,
                    fontSize: '0.75rem',
                    borderBottom: '1px solid rgba(255, 107, 53, 0.2)',
                    textAlign: 'center',
                    minWidth: 150,
                  }}
                >
                  {pos}
                </TableCell>
              ))}
              <TableCell
                sx={{
                  backgroundColor: '#0a0a0a',
                  color: '#ff6b35',
                  fontWeight: 600,
                  fontSize: '0.75rem',
                  borderBottom: '1px solid rgba(255, 107, 53, 0.2)',
                  textAlign: 'center',
                }}
              >
                Salary
              </TableCell>
              <TableCell
                sx={{
                  backgroundColor: '#0a0a0a',
                  color: '#ff6b35',
                  fontWeight: 600,
                  fontSize: '0.75rem',
                  borderBottom: '1px solid rgba(255, 107, 53, 0.2)',
                  textAlign: 'center',
                }}
              >
                Score
              </TableCell>
              <TableCell
                sx={{
                  backgroundColor: '#0a0a0a',
                  color: '#ff6b35',
                  fontWeight: 600,
                  fontSize: '0.75rem',
                  borderBottom: '1px solid rgba(255, 107, 53, 0.2)',
                  textAlign: 'center',
                }}
              >
                Avg Own%
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {lineups.map((lineup) => {
              // Sort players by position order
              const sortedPlayers = [...lineup.players].sort((a, b) => {
                const aIdx = POSITION_ORDER.indexOf(a.position);
                const bIdx = POSITION_ORDER.indexOf(b.position);
                return aIdx - bIdx;
              });

              // Fill in positions (handle FLEX)
              const positionMap: Record<string, GeneratedLineup['players']> = {};
              sortedPlayers.forEach((player) => {
                const pos = player.position;
                if (!positionMap[pos]) {
                  positionMap[pos] = [];
                }
                positionMap[pos].push(player);
              });

              // Build display array
              const displayPlayers: (GeneratedLineup['players'][0] | null)[] = [];
              let flexUsed = false;

              POSITION_ORDER.forEach((pos) => {
                if (pos === 'FLEX') {
                  // Find first unused RB/WR/TE
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

              const isSelected = selectedLineups.has(lineup.lineup_number);
              const salaryViolation = lineup.total_salary > 50000;

              return (
                <TableRow
                  key={lineup.lineup_number}
                  sx={{
                    backgroundColor: isSelected ? 'rgba(255, 107, 53, 0.1)' : 'transparent',
                    '&:hover': {
                      backgroundColor: isSelected ? 'rgba(255, 107, 53, 0.15)' : 'rgba(255, 255, 255, 0.03)',
                    },
                  }}
                >
                  <TableCell
                    sx={{
                      position: 'sticky',
                      left: 0,
                      backgroundColor: isSelected ? 'rgba(255, 107, 53, 0.1)' : '#0a0a0a',
                      borderRight: '1px solid rgba(255, 107, 53, 0.2)',
                      zIndex: 2,
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
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
                      />
                      <Typography variant="caption" sx={{ fontSize: '0.75rem', fontWeight: 600 }}>
                        #{lineup.lineup_number}
                      </Typography>
                    </Box>
                  </TableCell>

                  {displayPlayers.map((player, idx) => (
                    <TableCell
                      key={idx}
                      sx={{
                        fontSize: '0.75rem',
                        color: 'text.primary',
                        textAlign: 'center',
                        borderBottom: '1px solid rgba(255, 107, 53, 0.1)',
                      }}
                    >
                      {player ? (
                        <Box>
                          <Typography variant="caption" sx={{ fontSize: '0.7rem', fontWeight: 600, display: 'block' }}>
                            {player.name}
                          </Typography>
                          <Typography variant="caption" sx={{ fontSize: '0.65rem', color: 'text.secondary' }}>
                            {player.team} | ${(player.salary / 100).toFixed(0)}K
                          </Typography>
                          <Typography variant="caption" sx={{ fontSize: '0.65rem', color: '#ff6b35' }}>
                            {player.smart_score.toFixed(1)}
                          </Typography>
                        </Box>
                      ) : (
                        <Typography variant="caption" sx={{ color: 'text.disabled' }}>
                          -
                        </Typography>
                      )}
                    </TableCell>
                  ))}

                  <TableCell
                    sx={{
                      fontSize: '0.75rem',
                      textAlign: 'center',
                      fontWeight: salaryViolation ? 600 : 'normal',
                      color: salaryViolation ? '#f44336' : 'text.primary',
                    }}
                  >
                    ${(lineup.total_salary / 1000).toFixed(1)}K
                  </TableCell>

                  <TableCell
                    sx={{
                      fontSize: '0.75rem',
                      textAlign: 'center',
                      fontWeight: 600,
                      color: '#ff6b35',
                    }}
                  >
                    {lineup.projected_score.toFixed(1)}
                  </TableCell>

                  <TableCell
                    sx={{
                      fontSize: '0.75rem',
                      textAlign: 'center',
                    }}
                  >
                    {(lineup.avg_ownership * 100).toFixed(1)}%
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default LineupDisplay;

