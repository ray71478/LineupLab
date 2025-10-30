/**
 * SmartScoreTable Component
 *
 * Table component displaying players with Smart Scores, sortable columns, and filtering.
 * - Displays player name, team, position, salary, projection, ownership, Smart Score
 * - Shows projection source, 20+ snap games count, regression risk indicator
 * - Supports sorting by all columns
 * - Position filtering
 * - Compact table design for better space utilization
 * - Optimized with React.memo for performance
 *
 * Design: Dark theme with Smart Score column highlighted, compact rows
 */

import React, { useMemo, useState } from 'react';
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
  Chip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  SortingState,
  ColumnDef,
  flexRender,
} from '@tanstack/react-table';
import type { PlayerScoreResponse } from '../../types/smartScore.types';
import { ScoreDeltaIndicator } from './ScoreDeltaIndicator';
import { RegressionRiskBadge } from './RegressionRiskBadge';
import { MissingDataIndicator } from './MissingDataIndicator';

export interface SmartScoreTableProps {
  players: PlayerScoreResponse[];
  isLoading?: boolean;
  scoreDeltas?: Map<number, number>;
}

export const SmartScoreTable: React.FC<SmartScoreTableProps> = React.memo(({
  players,
  isLoading = false,
  scoreDeltas = new Map(),
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [sorting, setSorting] = useState<SortingState>([
    { id: 'smart_score', desc: true }, // Default sort by Smart Score descending
  ]);
  const [positionFilter, setPositionFilter] = useState<string>('all');

  // Memoize showDelta flag
  const showDelta = useMemo(() => scoreDeltas.size > 0, [scoreDeltas.size]);

  // Get unique positions for filter
  const positions = useMemo(() => {
    const unique = Array.from(new Set(players.map(p => p.position))).sort();
    return unique;
  }, [players]);

  // Filter players by position
  const filteredPlayers = useMemo(() => {
    if (positionFilter === 'all') return players;
    return players.filter(p => p.position === positionFilter);
  }, [players, positionFilter]);

  // Column definitions
  const columns = useMemo<ColumnDef<PlayerScoreResponse>[]>(
    () => [
      {
        id: 'name',
        accessorKey: 'name',
        header: 'Player',
        size: 150,
        cell: ({ row }) => (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Typography variant="body2" sx={{ fontSize: '0.875rem' }}>
              {row.original.name}
            </Typography>
            <MissingDataIndicator
              missingDataIndicators={row.original.score_breakdown?.missing_data_indicators}
            />
          </Box>
        ),
      },
      {
        id: 'team',
        accessorKey: 'team',
        header: 'Team',
        size: 60,
        cell: ({ getValue }) => (
          <Typography variant="body2" sx={{ fontSize: '0.875rem' }}>
            {getValue() as string}
          </Typography>
        ),
      },
      {
        id: 'position',
        accessorKey: 'position',
        header: 'Pos',
        size: 50,
        cell: ({ getValue }) => (
          <Chip
            label={getValue() as string}
            size="small"
            sx={{
              height: 20,
              fontSize: '0.7rem',
              fontWeight: 600,
            }}
          />
        ),
      },
      {
        id: 'salary',
        accessorKey: 'salary',
        header: 'Salary',
        size: 70,
        cell: ({ getValue }) => (
          <Typography variant="body2" sx={{ fontSize: '0.875rem' }}>
            ${(((getValue() as number) || 0) / 100).toFixed(0)}
          </Typography>
        ),
      },
      {
        id: 'projection',
        accessorKey: 'projection',
        header: 'Proj',
        size: 70,
        cell: ({ getValue }) => (
          <Typography variant="body2" sx={{ fontSize: '0.875rem' }}>
            {(getValue() as number)?.toFixed(2) || '-'}
          </Typography>
        ),
      },
      {
        id: 'ownership',
        accessorKey: 'ownership',
        header: 'Own %',
        size: 70,
        cell: ({ getValue }) => (
          <Typography variant="body2" sx={{ fontSize: '0.875rem' }}>
            {(getValue() as number)
              ? `${((getValue() as number) * 100).toFixed(1)}%`
              : '-'}
          </Typography>
        ),
      },
      {
        id: 'smart_score',
        accessorKey: 'smart_score',
        header: 'Smart Score',
        size: 100,
        cell: ({ row }) => {
          const player = row.original;
          const scoreDelta = scoreDeltas.get(player.player_id);
          return (
            <ScoreDeltaIndicator
              score={player.smart_score}
              delta={scoreDelta}
              showDelta={showDelta}
            />
          );
        },
      },
      {
        id: 'projection_source',
        accessorKey: 'projection_source',
        header: 'Source',
        size: 70,
        cell: ({ getValue }) => (
          <Typography variant="body2" sx={{ fontSize: '0.875rem' }}>
            {getValue() as string || '-'}
          </Typography>
        ),
      },
      {
        id: 'games_with_20_plus_snaps',
        accessorKey: 'games_with_20_plus_snaps',
        header: '20+ Snaps',
        size: 70,
        cell: ({ getValue }) => (
          <Typography variant="body2" sx={{ fontSize: '0.875rem' }}>
            {getValue() !== null && getValue() !== undefined ? String(getValue()) : '-'}
          </Typography>
        ),
      },
      {
        id: 'regression_risk',
        accessorFn: (row) => row.regression_risk,
        header: 'Risk',
        size: 60,
        cell: ({ row }) => {
          const player = row.original;
          return player.regression_risk && player.position === 'WR' ? (
            <RegressionRiskBadge
              regressionRisk={player.regression_risk}
              position={player.position}
              hasHistoricalData={
                player.games_with_20_plus_snaps !== null &&
                player.games_with_20_plus_snaps !== undefined
              }
            />
          ) : (
            <Typography variant="body2" sx={{ fontSize: '0.875rem' }}>-</Typography>
          );
        },
      },
    ],
    [scoreDeltas, showDelta]
  );

  // Initialize table
  const table = useReactTable({
    data: filteredPlayers,
    columns,
    state: {
      sorting,
    },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

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
      {/* Filter Bar */}
      <Box
        sx={{
          p: 1.5,
          borderBottom: '1px solid rgba(255, 140, 66, 0.1)',
          display: 'flex',
          alignItems: 'center',
          gap: 2,
          flexWrap: 'wrap',
        }}
      >
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel sx={{ fontSize: '0.875rem' }}>Position</InputLabel>
          <Select
            value={positionFilter}
            label="Position"
            onChange={(e) => setPositionFilter(e.target.value)}
            sx={{ fontSize: '0.875rem', height: 32 }}
          >
            <MenuItem value="all">All Positions</MenuItem>
            {positions.map((pos) => (
              <MenuItem key={pos} value={pos}>
                {pos}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <Typography variant="body2" sx={{ color: 'text.secondary', ml: 'auto' }}>
          Showing {filteredPlayers.length} of {players.length} players
        </Typography>
      </Box>

      <TableContainer sx={{ maxHeight: { xs: '60vh', md: '70vh' }, overflowX: 'auto' }}>
        <Table stickyHeader size="small" sx={{ '& .MuiTableCell-root': { py: 0.75 } }}>
          <TableHead>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  const isSortable = header.column.getCanSort();
                  const isSorted = header.column.getIsSorted();
                  const isSmartScore = header.id === 'smart_score';

                  return (
                    <TableCell
                      key={header.id}
                      sx={{
                        fontWeight: 600,
                        fontSize: '0.8rem',
                        cursor: isSortable ? 'pointer' : 'default',
                        userSelect: 'none',
                        backgroundColor: isSmartScore
                          ? 'rgba(255, 140, 66, 0.15)'
                          : 'inherit',
                        borderLeft: isSmartScore ? '2px solid #ff8c42' : 'none',
                        borderRight: isSmartScore ? '2px solid #ff8c42' : 'none',
                        '&:hover': isSortable ? { backgroundColor: 'rgba(255, 255, 255, 0.05)' } : {},
                      }}
                      onClick={header.column.getToggleSortingHandler()}
                    >
                      <Box
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 0.5,
                        }}
                      >
                        {flexRender(header.column.columnDef.header, header.getContext())}
                        {isSortable && (
                          <Box
                            component="span"
                            sx={{
                              fontSize: '0.7rem',
                              opacity: isSorted ? 1 : 0.3,
                              transition: 'opacity 0.2s',
                            }}
                          >
                            {isSorted === 'asc' ? '▲' : isSorted === 'desc' ? '▼' : '⇅'}
                          </Box>
                        )}
                      </Box>
                    </TableCell>
                  );
                })}
              </TableRow>
            ))}
          </TableHead>
          <TableBody>
            {table.getRowModel().rows.map((row) => (
              <TableRow
                key={row.id}
                hover
                sx={{
                  '& .MuiTableCell-root': {
                    borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                  },
                  '&:nth-of-type(even)': {
                    backgroundColor: 'rgba(255, 255, 255, 0.02)',
                  },
                }}
              >
                {row.getVisibleCells().map((cell) => {
                  const isSmartScore = cell.column.id === 'smart_score';
                  return (
                    <TableCell
                      key={cell.id}
                      sx={{
                        fontSize: '0.875rem',
                        backgroundColor: isSmartScore
                          ? 'rgba(255, 140, 66, 0.1)'
                          : 'inherit',
                        borderLeft: isSmartScore ? '2px solid #ff8c42' : 'none',
                        borderRight: isSmartScore ? '2px solid #ff8c42' : 'none',
                        fontWeight: isSmartScore ? 600 : 'normal',
                      }}
                    >
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  );
                })}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
});

SmartScoreTable.displayName = 'SmartScoreTable';

export default SmartScoreTable;

