/**
 * PlayerTableFilters Component
 *
 * Filter controls for position, team, and unmatched status filtering.
 * Multi-select dropdowns with clear button and active indicator.
 *
 * Accessibility Features:
 * - Form controls with proper labels (FormControl + Select)
 * - ARIA labels for filter groups
 * - aria-live region for active filter count
 * - Checkbox controls with semantic labels
 * - Keyboard navigation support
 * - Color contrast >= 4.5:1
 */

import React, { useCallback, useState, useMemo } from 'react';
import {
  Box,
  Stack,
  FormControl,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel,
  Button,
  Chip,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import ClearIcon from '@mui/icons-material/Clear';
import FilterListIcon from '@mui/icons-material/FilterList';

const POSITIONS = ['QB', 'RB', 'WR', 'TE', 'DST'];

const NFL_TEAMS = [
  'KC', 'LAR', 'SF', 'DEN', 'NYG', 'NYJ', 'TB', 'BUF',
  'DAL', 'PHI', 'WAS', 'CLE', 'BAL', 'PIT', 'TEN', 'JAX',
  'IND', 'HOU', 'MIN', 'GB', 'DET', 'CHI', 'LAC', 'ATL',
  'CAR', 'NO', 'MIA', 'NE', 'SEA', 'OAK', 'ARI',
];

export interface PlayerFilters {
  positions: string[];
  teams: string[];
  unmatchedOnly: boolean;
}

export interface PlayerTableFiltersProps {
  onFilterChange: (filters: PlayerFilters) => void;
}

export const PlayerTableFilters: React.FC<PlayerTableFiltersProps> = React.memo(({
  onFilterChange,
}) => {
  const [filters, setFilters] = useState<PlayerFilters>({
    positions: [],
    teams: [],
    unmatchedOnly: false,
  });

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const handlePositionChange = useCallback(
    (event: any) => {
      const value = event.target.value;
      const newFilters = {
        ...filters,
        positions: Array.isArray(value) ? value : [value],
      };
      setFilters(newFilters);
      onFilterChange(newFilters);
    },
    [filters, onFilterChange]
  );

  const handleTeamChange = useCallback(
    (event: any) => {
      const value = event.target.value;
      const newFilters = {
        ...filters,
        teams: Array.isArray(value) ? value : [value],
      };
      setFilters(newFilters);
      onFilterChange(newFilters);
    },
    [filters, onFilterChange]
  );

  const handleUnmatchedToggle = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const newFilters = {
        ...filters,
        unmatchedOnly: event.target.checked,
      };
      setFilters(newFilters);
      onFilterChange(newFilters);
    },
    [filters, onFilterChange]
  );

  const handleClearAll = useCallback(() => {
    const clearedFilters: PlayerFilters = {
      positions: [],
      teams: [],
      unmatchedOnly: false,
    };
    setFilters(clearedFilters);
    onFilterChange(clearedFilters);
  }, [onFilterChange]);

  const hasActiveFilters =
    filters.positions.length > 0 ||
    filters.teams.length > 0 ||
    filters.unmatchedOnly;

  const activeFilterCount = useMemo(
    () => filters.positions.length + filters.teams.length + (filters.unmatchedOnly ? 1 : 0),
    [filters]
  );

  const filterStatusMessage = useMemo(
    () => `${activeFilterCount} filter(s) applied`,
    [activeFilterCount]
  );

  return (
    <Box
      role="region"
      aria-label="Player Filters"
      aria-live="polite"
      sx={{
        padding: isMobile ? '12px' : '16px',
        backgroundColor: 'rgba(255, 255, 255, 0.02)',
        borderRadius: '8px',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        marginBottom: '20px',
      }}
    >
      <Stack spacing={2}>
        {/* Filters Row */}
        <Stack
          direction={isMobile ? 'column' : 'row'}
          spacing={2}
          sx={{
            alignItems: isMobile ? 'stretch' : 'center',
          }}
          role="group"
          aria-label="Filter controls"
        >
          {/* Position Filter */}
          <FormControl
            size="small"
            sx={{
              minWidth: isMobile ? '100%' : '150px',
              flex: isMobile ? 1 : 'auto',
            }}
          >
            <Select
              multiple
              displayEmpty
              value={filters.positions}
              onChange={handlePositionChange}
              aria-label="Filter by position: quarterback, running back, wide receiver, tight end, or defense"
              renderValue={(selected: any) => {
                if (selected.length === 0) {
                  return <span style={{ color: '#9ca3af' }}>Position</span>;
                }
                return (
                  <Box sx={{ display: 'flex', gap: 0.5 }}>
                    {selected.map((pos: string) => (
                      <Chip
                        key={pos}
                        label={pos}
                        size="small"
                        sx={{
                          backgroundColor: 'rgba(255, 140, 66, 0.2)',
                          color: '#ff8c42',
                          height: '24px',
                        }}
                      />
                    ))}
                  </Box>
                );
              }}
              sx={{
                backgroundColor: 'rgba(255, 255, 255, 0.05)',
                borderRadius: '6px',
                color: '#ffffff',
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'rgba(255, 255, 255, 0.1)',
                },
                '&:hover .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'rgba(255, 255, 255, 0.2)',
                },
                '&:focus-within .MuiOutlinedInput-notchedOutline': {
                  borderColor: '#ff8c42',
                },
              }}
            >
              {POSITIONS.map((pos) => (
                <MenuItem key={pos} value={pos}>
                  <Checkbox
                    checked={filters.positions.includes(pos)}
                    size="small"
                    aria-label={`Select ${pos}`}
                  />
                  {pos}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Team Filter */}
          <FormControl
            size="small"
            sx={{
              minWidth: isMobile ? '100%' : '150px',
              flex: isMobile ? 1 : 'auto',
            }}
          >
            <Select
              multiple
              displayEmpty
              value={filters.teams}
              onChange={handleTeamChange}
              aria-label="Filter by NFL team: select one or more team abbreviations"
              renderValue={(selected: any) => {
                if (selected.length === 0) {
                  return <span style={{ color: '#9ca3af' }}>Team</span>;
                }
                return (
                  <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                    {selected.slice(0, 2).map((team: string) => (
                      <Chip
                        key={team}
                        label={team}
                        size="small"
                        sx={{
                          backgroundColor: 'rgba(255, 140, 66, 0.2)',
                          color: '#ff8c42',
                          height: '24px',
                        }}
                      />
                    ))}
                    {selected.length > 2 && (
                      <Chip
                        label={`+${selected.length - 2}`}
                        size="small"
                        sx={{
                          backgroundColor: 'rgba(255, 140, 66, 0.2)',
                          color: '#ff8c42',
                          height: '24px',
                        }}
                      />
                    )}
                  </Box>
                );
              }}
              sx={{
                backgroundColor: 'rgba(255, 255, 255, 0.05)',
                borderRadius: '6px',
                color: '#ffffff',
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'rgba(255, 255, 255, 0.1)',
                },
                '&:hover .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'rgba(255, 255, 255, 0.2)',
                },
                '&:focus-within .MuiOutlinedInput-notchedOutline': {
                  borderColor: '#ff8c42',
                },
              }}
            >
              {NFL_TEAMS.map((team) => (
                <MenuItem key={team} value={team}>
                  <Checkbox
                    checked={filters.teams.includes(team)}
                    size="small"
                    aria-label={`Select ${team}`}
                  />
                  {team}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Unmatched Only Toggle */}
          <FormControlLabel
            control={
              <Checkbox
                checked={filters.unmatchedOnly}
                onChange={handleUnmatchedToggle}
                aria-label="Show only unmatched players"
                sx={{
                  color: 'rgba(255, 255, 255, 0.5)',
                  '&.Mui-checked': {
                    color: '#ff8c42',
                  },
                }}
              />
            }
            label={
              <span style={{ color: '#e5e7eb', fontSize: '0.9rem' }}>
                Unmatched Only
              </span>
            }
            sx={{
              whiteSpace: 'nowrap',
            }}
          />
        </Stack>

        {/* Active Filters and Clear Button */}
        {hasActiveFilters && (
          <Stack
            direction="row"
            spacing={1}
            sx={{
              alignItems: 'center',
              justifyContent: 'space-between',
              paddingTop: '8px',
              borderTop: '1px solid rgba(255, 255, 255, 0.1)',
            }}
            role="status"
            aria-live="polite"
            aria-atomic="true"
          >
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
              <FilterListIcon
                sx={{
                  color: '#ff8c42',
                  fontSize: '1.2rem',
                }}
                aria-hidden="true"
              />
              <span style={{ color: '#9ca3af', fontSize: '0.85rem' }}>
                {filterStatusMessage}
              </span>
            </Box>

            <Button
              size="small"
              startIcon={<ClearIcon />}
              onClick={handleClearAll}
              aria-label="Clear all filters"
              sx={{
                color: '#ff8c42',
                textTransform: 'none',
                fontSize: '0.85rem',
                fontWeight: 500,
                minHeight: '36px',
                minWidth: isMobile ? '36px' : 'auto',
                '@media (hover: hover)': {
                  '&:hover': {
                    backgroundColor: 'rgba(255, 140, 66, 0.1)',
                  },
                },
              }}
            >
              Clear All
            </Button>
          </Stack>
        )}
      </Stack>
    </Box>
  );
});

PlayerTableFilters.displayName = 'PlayerTableFilters';

export default PlayerTableFilters;
