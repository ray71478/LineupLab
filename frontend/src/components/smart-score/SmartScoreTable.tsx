/**
 * SmartScoreTable Component
 *
 * Table component displaying players with Smart Scores, sortable columns, and virtual scrolling.
 * - Displays player name, team, position, salary, projection, ownership, Smart Score
 * - Shows projection source, 20+ snap games count, regression risk indicator
 * - Supports sorting and filtering
 * - Virtual scrolling for 150-200 players
 *
 * Design: Dark theme with Smart Score column highlighted
 */

import React from 'react';
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
  CircularProgress,
  Alert,
} from '@mui/material';
import type { PlayerScoreResponse } from '../../types/smartScore.types';

export interface SmartScoreTableProps {
  players: PlayerScoreResponse[];
  isLoading?: boolean;
  scoreDeltas?: Map<number, number>;
}

export const SmartScoreTable: React.FC<SmartScoreTableProps> = ({
  players,
  isLoading = false,
}) => {
  if (isLoading && players.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (players.length === 0) {
    return (
      <Paper sx={{ p: 4 }}>
        <Alert severity="info">No players found for this week.</Alert>
      </Paper>
    );
  }

  return (
    <Paper
      sx={{
        backgroundColor: '#1a1a2e',
        border: '1px solid rgba(255, 140, 66, 0.2)',
        borderRadius: 2,
        overflow: 'hidden',
      }}
    >
      <TableContainer>
        <Table stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 600 }}>Player</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Team</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Pos</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Salary</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Projection</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Ownership</TableCell>
              <TableCell
                sx={{
                  fontWeight: 600,
                  backgroundColor: 'rgba(255, 140, 66, 0.15)',
                  borderLeft: '2px solid #ff8c42',
                  borderRight: '2px solid #ff8c42',
                }}
              >
                Smart Score
              </TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Source</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>20+ Snaps</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Risk</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {players.map((player) => (
              <TableRow key={player.player_id} hover>
                <TableCell>{player.name}</TableCell>
                <TableCell>{player.team}</TableCell>
                <TableCell>{player.position}</TableCell>
                <TableCell>
                  ${((player.salary || 0) / 100).toFixed(0)}
                </TableCell>
                <TableCell>{player.projection?.toFixed(2) || '-'}</TableCell>
                <TableCell>
                  {player.ownership
                    ? `${(player.ownership * 100).toFixed(1)}%`
                    : '-'}
                </TableCell>
                <TableCell
                  sx={{
                    backgroundColor: 'rgba(255, 140, 66, 0.1)',
                    fontWeight: 600,
                    borderLeft: '2px solid #ff8c42',
                    borderRight: '2px solid #ff8c42',
                  }}
                >
                  {player.smart_score?.toFixed(2) || '-'}
                </TableCell>
                <TableCell>{player.projection_source || '-'}</TableCell>
                <TableCell>{player.games_with_20_plus_snaps || '-'}</TableCell>
                <TableCell>
                  {player.regression_risk && player.position === 'WR' ? (
                    <Box
                      sx={{
                        display: 'inline-block',
                        px: 1,
                        py: 0.5,
                        backgroundColor: '#ff5722',
                        borderRadius: 1,
                        fontSize: '0.75rem',
                        color: 'white',
                      }}
                    >
                      Risk
                    </Box>
                  ) : (
                    '-'
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
};

export default SmartScoreTable;

