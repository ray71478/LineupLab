/**
 * SmartScoreTable Component
 *
 * Table component displaying players with Smart Scores, sortable columns, and virtual scrolling.
 * - Displays player name, team, position, salary, projection, ownership, Smart Score
 * - Shows projection source, 20+ snap games count, regression risk indicator
 * - Supports sorting and filtering
 * - Optimized with React.memo for performance
 * - Virtual scrolling ready (can be enhanced with @tanstack/react-virtual)
 *
 * Design: Dark theme with Smart Score column highlighted
 */

import React, { useMemo } from 'react';
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
  useTheme,
  useMediaQuery,
} from '@mui/material';
import type { PlayerScoreResponse } from '../../types/smartScore.types';
import { ScoreDeltaIndicator } from './ScoreDeltaIndicator';
import { RegressionRiskBadge } from './RegressionRiskBadge';
import { MissingDataIndicator } from './MissingDataIndicator';

export interface SmartScoreTableProps {
  players: PlayerScoreResponse[];
  isLoading?: boolean;
  scoreDeltas?: Map<number, number>;
}

// Memoized table row component for performance
const SmartScoreTableRow = React.memo<{
  player: PlayerScoreResponse;
  scoreDelta?: number;
  showDelta: boolean;
}>(({ player, scoreDelta, showDelta }) => (
  <TableRow hover>
    <TableCell>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        {player.name}
        <MissingDataIndicator
          missingDataIndicators={player.score_breakdown?.missing_data_indicators}
        />
      </Box>
    </TableCell>
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
      <ScoreDeltaIndicator
        score={player.smart_score}
        delta={scoreDelta}
        showDelta={showDelta}
      />
    </TableCell>
    <TableCell>{player.projection_source || '-'}</TableCell>
    <TableCell>{player.games_with_20_plus_snaps || '-'}</TableCell>
    <TableCell>
      {player.regression_risk && player.position === 'WR' ? (
        <RegressionRiskBadge
          regressionRisk={player.regression_risk}
          position={player.position}
          hasHistoricalData={player.games_with_20_plus_snaps !== null && player.games_with_20_plus_snaps !== undefined}
        />
      ) : (
        '-'
      )}
    </TableCell>
  </TableRow>
));

SmartScoreTableRow.displayName = 'SmartScoreTableRow';

export const SmartScoreTable: React.FC<SmartScoreTableProps> = React.memo(({
  players,
  isLoading = false,
  scoreDeltas = new Map(),
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  // Memoize showDelta flag
  const showDelta = useMemo(() => scoreDeltas.size > 0, [scoreDeltas.size]);

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
      <TableContainer sx={{ maxHeight: { xs: '60vh', md: '70vh' }, overflowX: 'auto' }}>
        <Table stickyHeader size={isMobile ? 'small' : 'medium'}>
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
              <SmartScoreTableRow
                key={player.player_id}
                player={player}
                scoreDelta={scoreDeltas.get(player.player_id)}
                showDelta={showDelta}
              />
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
});

SmartScoreTable.displayName = 'SmartScoreTable';

export default SmartScoreTable;

