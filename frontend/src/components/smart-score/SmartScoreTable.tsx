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
  Tooltip,
  IconButton,
} from '@mui/material';
import InfoIcon from '@mui/icons-material/Info';
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
import { UsageWarningBadge } from './UsageWarningBadge';
// import { StackPotentialBadge } from './StackPotentialBadge'; // Hidden - not used in Smart Score engine

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
  const [consistencyFilter, setConsistencyFilter] = useState<string>('all'); // 'all', 'low', 'medium', 'high'
  const [valueTrendFilter, setValueTrendFilter] = useState<string>('all'); // 'all', 'up', 'down', 'stable'

  // Memoize showDelta flag
  const showDelta = useMemo(() => scoreDeltas.size > 0, [scoreDeltas.size]);

  // Get unique positions for filter
  const positions = useMemo(() => {
    const unique = Array.from(new Set(players.map(p => p.position))).sort();
    return unique;
  }, [players]);

  // Filter players by position
  const filteredPlayers = useMemo(() => {
    let filtered = players;
    
    // Position filter
    if (positionFilter !== 'all') {
      filtered = filtered.filter(p => p.position === positionFilter);
    }
    
    // Consistency filter
    if (consistencyFilter !== 'all') {
      filtered = filtered.filter(p => {
        if (p.consistency_score === null || p.consistency_score === undefined) return false;
        const cv = p.consistency_score;
        if (consistencyFilter === 'low') return cv < 0.3; // Very consistent
        if (consistencyFilter === 'medium') return cv >= 0.3 && cv < 0.6;
        if (consistencyFilter === 'high') return cv >= 0.6; // Volatile
        return true;
      });
    }
    
    // Value trend filter
    if (valueTrendFilter !== 'all') {
      filtered = filtered.filter(p => p.salary_efficiency_trend === valueTrendFilter);
    }
    
    return filtered;
  }, [players, positionFilter, consistencyFilter, valueTrendFilter]);

  // Helper function to create tooltip header
  const createTooltipHeader = (title: string, tooltipContent: React.ReactNode) => (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
      <Typography variant="body2" component="span">
        {title}
      </Typography>
      <Tooltip
        title={tooltipContent}
        arrow
        placement="top"
      >
        <IconButton
          size="small"
          sx={{
            p: 0,
            minWidth: 16,
            width: 16,
            height: 16,
            color: 'text.secondary',
            '&:hover': {
              color: 'text.primary',
            },
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <InfoIcon sx={{ fontSize: '0.875rem' }} />
        </IconButton>
      </Tooltip>
    </Box>
  );

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
            <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
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
          <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
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
      // Stack column hidden - not useful for Smart Score engine (stacking is a roster construction consideration)
      // {
      //   id: 'stack_potential',
      //   accessorKey: 'stack_partners',
      //   header: 'Stack',
      //   size: 80,
      //   cell: ({ row }) => {
      //     const player = row.original;
      //     // Only show for QB, WR, TE
      //     if (!['QB', 'WR', 'TE'].includes(player.position)) {
      //       return null;
      //     }
      //     return (
      //       <StackPotentialBadge
      //         stackPartners={player.stack_partners}
      //         position={player.position}
      //       />
      //     );
      //   },
      // },
      {
        id: 'salary',
        accessorKey: 'salary',
        header: 'Salary',
        size: 70,
        cell: ({ getValue }) => {
          const salary = getValue() as number;
          // Display as stored in spreadsheet (e.g., 7300 = $7,300)
          return (
            <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
              ${salary?.toLocaleString('en-US') || '-'}
            </Typography>
          );
        },
      },
      {
        id: 'projection',
        accessorKey: 'projection',
        header: 'Proj',
        size: 70,
        cell: ({ getValue }) => (
          <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
            {(getValue() as number)?.toFixed(2) || '-'}
          </Typography>
        ),
      },
      {
        id: 'ownership',
        accessorKey: 'ownership',
        header: 'Own %',
        size: 70,
        cell: ({ getValue }) => {
          const ownership = getValue() as number;
          // Display exactly as stored in spreadsheet (all values are percentages)
          // 0.60 = 0.60%, 16.9 = 16.9%
          if (ownership === null || ownership === undefined) {
            return <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>-</Typography>;
          }
          // Format with appropriate decimal places
          const formatted = ownership % 1 === 0 
            ? ownership.toFixed(0) 
            : ownership.toFixed(1);
          return (
            <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
              {formatted}%
            </Typography>
          );
        },
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
        id: 'implied_team_total',
        accessorKey: 'implied_team_total',
        header: 'ITT',
        size: 60,
        cell: ({ getValue }) => {
          const itt = getValue() as number | null | undefined;
          if (itt === null || itt === undefined) {
            return <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>-</Typography>;
          }
          return (
            <Typography variant="body2" sx={{ fontSize: '0.75rem', fontWeight: 500 }}>
              {itt.toFixed(2)}
            </Typography>
          );
        },
      },
      {
        id: 'over_under',
        accessorKey: 'over_under',
        header: 'O/U',
        size: 60,
        cell: ({ getValue }) => {
          const ou = getValue() as number | null | undefined;
          if (ou === null || ou === undefined) {
            return <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>-</Typography>;
          }
          return (
            <Typography variant="body2" sx={{ fontSize: '0.75rem', fontWeight: 500 }}>
              {ou.toFixed(1)}
            </Typography>
          );
        },
      },
      {
        id: 'consistency_score',
        accessorKey: 'consistency_score',
        header: () => (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Typography variant="body2" component="span">
              Consistency
            </Typography>
            <Tooltip
              title={
                <Box>
                  <Typography variant="caption" component="div" sx={{ fontWeight: 600, mb: 0.5 }}>
                    Coefficient of Variation (CV)
                  </Typography>
                  <Typography variant="caption" component="div" sx={{ fontSize: '0.7rem' }}>
                    Measures scoring consistency over the last 6 games with 20+ snaps.
                  </Typography>
                  <Typography variant="caption" component="div" sx={{ fontSize: '0.7rem', mt: 0.5, fontWeight: 600 }}>
                    Lower is better:
                  </Typography>
                  <Typography variant="caption" component="div" sx={{ fontSize: '0.7rem' }}>
                    • &lt; 0.3 = Very consistent (Green)
                  </Typography>
                  <Typography variant="caption" component="div" sx={{ fontSize: '0.7rem' }}>
                    • 0.3-0.6 = Moderately consistent (Orange)
                  </Typography>
                  <Typography variant="caption" component="div" sx={{ fontSize: '0.7rem' }}>
                    • &gt; 0.6 = Volatile/Inconsistent (Red)
                  </Typography>
                  <Typography variant="caption" component="div" sx={{ fontSize: '0.7rem', mt: 0.5, fontStyle: 'italic' }}>
                    CV = Standard Deviation ÷ Average Points
                  </Typography>
                </Box>
              }
              arrow
              placement="top"
            >
              <IconButton
                size="small"
                sx={{
                  p: 0,
                  minWidth: 16,
                  width: 16,
                  height: 16,
                  color: 'text.secondary',
                  '&:hover': {
                    color: 'text.primary',
                  },
                }}
                onClick={(e) => e.stopPropagation()}
              >
                <InfoIcon sx={{ fontSize: '0.875rem' }} />
              </IconButton>
            </Tooltip>
          </Box>
        ),
        size: 90,
        cell: ({ getValue, row }) => {
          const cv = getValue() as number | null | undefined;
          const player = row.original;
          if (cv === null || cv === undefined) {
            return <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>-</Typography>;
          }
          // Lower CV = more consistent (better)
          // Color code: < 0.3 = green, 0.3-0.6 = yellow, > 0.6 = red
          const getColor = () => {
            if (cv < 0.3) return '#4caf50'; // Green
            if (cv < 0.6) return '#ff9800'; // Orange
            return '#f44336'; // Red
          };
          return (
            <Typography 
              variant="body2" 
              sx={{ 
                fontSize: '0.75rem',
                color: getColor(),
                fontWeight: cv < 0.3 ? 600 : 400,
              }}
            >
              {cv.toFixed(2)}
            </Typography>
          );
        },
      },
      {
        id: 'opponent',
        accessorKey: 'opponent',
        header: 'vs Opp',
        size: 70,
        cell: ({ getValue }) => {
          const opponent = getValue() as string | null | undefined;
          if (!opponent) {
            return <Typography variant="body2" sx={{ fontSize: '0.75rem', color: 'text.secondary' }}>-</Typography>;
          }
          return (
            <Typography 
              variant="body2" 
              sx={{ 
                fontSize: '0.75rem',
                fontWeight: 500,
              }}
            >
              {opponent}
            </Typography>
          );
        },
      },
      {
        id: 'salary_efficiency_trend',
        accessorKey: 'salary_efficiency_trend',
        header: () => createTooltipHeader(
          'Value Trend',
          <Box>
            <Typography variant="caption" component="div" sx={{ fontWeight: 600, mb: 0.5 }}>
              Salary Efficiency Trend
            </Typography>
            <Typography variant="caption" component="div" sx={{ fontSize: '0.7rem' }}>
              Compares value score (points per $1,000 salary) over recent weeks.
            </Typography>
            <Typography variant="caption" component="div" sx={{ fontSize: '0.7rem', mt: 0.5, fontWeight: 600 }}>
              Trend calculation:
            </Typography>
            <Typography variant="caption" component="div" sx={{ fontSize: '0.7rem' }}>
              Compares last 3 weeks vs previous 3 weeks.
            </Typography>
            <Typography variant="caption" component="div" sx={{ fontSize: '0.7rem', mt: 0.5 }}>
              <Box component="span" sx={{ fontWeight: 600 }}>▲</Box> = Trending up (Green) - Recent value &gt; 10% higher
            </Typography>
            <Typography variant="caption" component="div" sx={{ fontSize: '0.7rem' }}>
              <Box component="span" sx={{ fontWeight: 600 }}>→</Box> = Stable (Gray) - Within 10% of previous average
            </Typography>
            <Typography variant="caption" component="div" sx={{ fontSize: '0.7rem' }}>
              <Box component="span" sx={{ fontWeight: 600 }}>▼</Box> = Trending down (Red) - Recent value &lt; 10% of previous
            </Typography>
            <Typography variant="caption" component="div" sx={{ fontSize: '0.7rem', mt: 0.5, fontStyle: 'italic' }}>
              Value Score = (Points ÷ Salary) × 1,000
            </Typography>
          </Box>
        ),
        size: 80,
        cell: ({ getValue }) => {
          const trend = getValue() as 'up' | 'down' | 'stable' | null | undefined;
          if (!trend) {
            return <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>-</Typography>;
          }
          const getIcon = () => {
            if (trend === 'up') return '▲';
            if (trend === 'down') return '▼';
            return '→';
          };
          const getColor = () => {
            if (trend === 'up') return '#4caf50';
            if (trend === 'down') return '#f44336';
            return '#999';
          };
          return (
            <Typography 
              variant="body2" 
              sx={{ 
                fontSize: '0.75rem',
                color: getColor(),
                fontWeight: 600,
              }}
            >
              {getIcon()}
            </Typography>
          );
        },
      },
      {
        id: 'usage_warnings',
        accessorFn: (row) => row.usage_warnings,
        header: () => createTooltipHeader(
          'Usage',
          <Box>
            <Typography variant="caption" component="div" sx={{ fontWeight: 600, mb: 0.5 }}>
              Usage Pattern Warnings
            </Typography>
            <Typography variant="caption" component="div" sx={{ fontSize: '0.7rem' }}>
              Analyzes snaps and touches over last 4 games to detect declining usage.
            </Typography>
            <Typography variant="caption" component="div" sx={{ fontSize: '0.7rem', mt: 0.5 }}>
              <Box component="span" sx={{ fontWeight: 600 }}>Applies to:</Box> RB, WR, TE only (not QB)
            </Typography>
            <Typography variant="caption" component="div" sx={{ fontSize: '0.7rem', mt: 0.5, fontWeight: 600 }}>
              Warning triggers:
            </Typography>
            <Typography variant="caption" component="div" sx={{ fontSize: '0.7rem' }}>
              • Snap count declining 15%+ (last 2 weeks vs weeks 3-4)
            </Typography>
            <Typography variant="caption" component="div" sx={{ fontSize: '0.7rem' }}>
              • Touches declining 15%+ (last 2 weeks vs weeks 3-4)
            </Typography>
            <Typography variant="caption" component="div" sx={{ fontSize: '0.7rem', mt: 0.5 }}>
              Shows warning badge if either trend detected. No badge = stable usage.
            </Typography>
          </Box>
        ),
        size: 70,
        cell: ({ row }) => {
          const player = row.original;
          // Only show usage warnings for RB, WR, TE - not QB
          if (player.position === 'QB') {
            return (
              <Typography variant="body2" sx={{ fontSize: '0.75rem', color: 'text.secondary' }}>
                -
              </Typography>
            );
          }
          return (
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <UsageWarningBadge warnings={player.usage_warnings} />
              {!player.usage_warnings && (
                <Typography variant="body2" sx={{ fontSize: '0.75rem', color: 'text.secondary' }}>
                  -
                </Typography>
              )}
            </Box>
          );
        },
      },
      {
        id: 'games_with_20_plus_snaps',
        accessorKey: 'games_with_20_plus_snaps',
        header: () => createTooltipHeader(
          '20+ Snaps',
          <Box>
            <Typography variant="caption" component="div" sx={{ fontWeight: 600, mb: 0.5 }}>
              Games with 20+ Snaps
            </Typography>
            <Typography variant="caption" component="div" sx={{ fontSize: '0.7rem' }}>
              Count of recent games where player had 20 or more snaps.
            </Typography>
            <Typography variant="caption" component="div" sx={{ fontSize: '0.7rem', mt: 0.5, fontWeight: 600 }}>
              Used for:
            </Typography>
            <Typography variant="caption" component="div" sx={{ fontSize: '0.7rem' }}>
              • W5 Trend Adjustment calculation
            </Typography>
            <Typography variant="caption" component="div" sx={{ fontSize: '0.7rem' }}>
              • Position-specific trend metrics (target share, snap %, etc.)
            </Typography>
            <Typography variant="caption" component="div" sx={{ fontSize: '0.7rem', mt: 0.5 }}>
              <Box component="span" sx={{ fontWeight: 600 }}>Minimum:</Box> 2 games needed for trend calculation
            </Typography>
            <Typography variant="caption" component="div" sx={{ fontSize: '0.7rem' }}>
              <Box component="span" sx={{ fontWeight: 600 }}>Maximum:</Box> Analyzes up to last 4 games
            </Typography>
            <Typography variant="caption" component="div" sx={{ fontSize: '0.7rem', mt: 0.5, fontStyle: 'italic' }}>
              Games with &lt; 20 snaps excluded (incomplete participation)
            </Typography>
          </Box>
        ),
        size: 70,
        cell: ({ getValue }) => (
          <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
            {getValue() !== null && getValue() !== undefined ? String(getValue()) : '-'}
          </Typography>
        ),
      },
      {
        id: 'regression_risk',
        accessorFn: (row) => row.regression_risk,
        header: () => createTooltipHeader(
          'Risk',
          <Box>
            <Typography variant="caption" component="div" sx={{ fontWeight: 600, mb: 0.5 }}>
              Regression Risk (80-20 Rule)
            </Typography>
            <Typography variant="caption" component="div" sx={{ fontSize: '0.7rem' }}>
              Flags WR players who scored exceptionally high last week.
            </Typography>
            <Typography variant="caption" component="div" sx={{ fontSize: '0.7rem', mt: 0.5 }}>
              <Box component="span" sx={{ fontWeight: 600 }}>Applies to:</Box> WR position only
            </Typography>
            <Typography variant="caption" component="div" sx={{ fontSize: '0.7rem', mt: 0.5, fontWeight: 600 }}>
              Rule logic:
            </Typography>
            <Typography variant="caption" component="div" sx={{ fontSize: '0.7rem' }}>
              If WR scored ≥ 20.0 points last week (default threshold), they're flagged for regression risk.
            </Typography>
            <Typography variant="caption" component="div" sx={{ fontSize: '0.7rem', mt: 0.5 }}>
              <Box component="span" sx={{ fontWeight: 600 }}>Why:</Box> High-scoring games are often outliers. Players typically regress toward their average.
            </Typography>
            <Typography variant="caption" component="div" sx={{ fontSize: '0.7rem', mt: 0.5 }}>
              <Box component="span" sx={{ fontWeight: 600 }}>Visual indicator:</Box> Orange "Risk" badge appears when flagged
            </Typography>
            <Typography variant="caption" component="div" sx={{ fontSize: '0.7rem', mt: 0.5, fontStyle: 'italic' }}>
              Note: This is a visual flag only. W6 penalty weight controls actual impact on Smart Score.
            </Typography>
          </Box>
        ),
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
            <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>-</Typography>
          );
        },
      },
      {
        id: 'injury_status',
        accessorKey: 'injury_status',
        header: 'Injury',
        size: 70,
        cell: ({ getValue }) => {
          const status = getValue() as string | null | undefined;
          if (!status) {
            return <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>-</Typography>;
          }
          // Color code injury status
          const getColor = () => {
            switch (status.toUpperCase()) {
              case 'OUT':
                return '#f44336'; // Red
              case 'DOUBTFUL':
                return '#ff9800'; // Orange
              case 'QUESTIONABLE':
                return '#ffc107'; // Yellow/Amber
              case 'PROBABLE':
                return '#4caf50'; // Green
              default:
                return '#e5e7eb'; // Gray
            }
          };
          return (
            <Chip
              label={status}
              size="small"
              sx={{
                height: 20,
                fontSize: '0.65rem',
                fontWeight: 600,
                backgroundColor: getColor(),
                color: '#fff',
                '& .MuiChip-label': {
                  padding: '0 6px',
                },
              }}
            />
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
        backgroundColor: '#0a0a0a',
        border: '1px solid rgba(255, 107, 53, 0.2)',
        borderRadius: 2,
        overflow: 'hidden',
      }}
    >
      {/* Filter Bar */}
      <Box
        sx={{
          p: 1.5,
          borderBottom: '1px solid rgba(255, 107, 53, 0.2)',
          display: 'flex',
          alignItems: 'center',
          gap: 2,
          flexWrap: 'wrap',
        }}
      >
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel sx={{ fontSize: '0.75rem' }}>Position</InputLabel>
          <Select
            value={positionFilter}
            label="Position"
            onChange={(e) => setPositionFilter(e.target.value)}
            sx={{ fontSize: '0.75rem', height: 32 }}
          >
            <MenuItem value="all">All Positions</MenuItem>
            {positions.map((pos) => (
              <MenuItem key={pos} value={pos}>
                {pos}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        
        <FormControl size="small" sx={{ minWidth: 140 }}>
          <InputLabel sx={{ fontSize: '0.75rem' }}>Consistency</InputLabel>
          <Select
            value={consistencyFilter}
            label="Consistency"
            onChange={(e) => setConsistencyFilter(e.target.value)}
            sx={{ fontSize: '0.75rem', height: 32 }}
          >
            <MenuItem value="all">All</MenuItem>
            <MenuItem value="low">Low CV (&lt;0.3)</MenuItem>
            <MenuItem value="medium">Medium (0.3-0.6)</MenuItem>
            <MenuItem value="high">High CV (&gt;0.6)</MenuItem>
          </Select>
        </FormControl>
        
        <FormControl size="small" sx={{ minWidth: 130 }}>
          <InputLabel sx={{ fontSize: '0.75rem' }}>Value Trend</InputLabel>
          <Select
            value={valueTrendFilter}
            label="Value Trend"
            onChange={(e) => setValueTrendFilter(e.target.value)}
            sx={{ fontSize: '0.75rem', height: 32 }}
          >
            <MenuItem value="all">All</MenuItem>
            <MenuItem value="up">Trending Up ▲</MenuItem>
            <MenuItem value="stable">Stable →</MenuItem>
            <MenuItem value="down">Trending Down ▼</MenuItem>
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
              <TableRow
                key={headerGroup.id}
                sx={{
                  backgroundColor: '#1a1a1a',
                }}
              >
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
                          ? 'rgba(255, 107, 53, 0.2)'
                          : '#1a1a1a',
                        borderLeft: isSmartScore ? '2px solid #ff6b35' : 'none',
                        borderRight: isSmartScore ? '2px solid #ff6b35' : 'none',
                        '&:hover': isSortable ? { backgroundColor: isSmartScore ? 'rgba(255, 107, 53, 0.3)' : 'rgba(255, 255, 255, 0.03)' } : {},
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
                        fontSize: '0.75rem',
                        backgroundColor: isSmartScore
                          ? 'rgba(255, 107, 53, 0.08)'
                          : 'inherit',
                        borderLeft: isSmartScore ? '2px solid #ff6b35' : 'none',
                        borderRight: isSmartScore ? '2px solid #ff6b35' : 'none',
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

