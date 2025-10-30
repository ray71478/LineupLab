/**
 * PlayerManagementPage Component
 *
 * Main page for player management, orchestrating all child components.
 * Handles data fetching, filtering, sorting, and modal interactions.
 */

import React, { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Stack,
  Typography,
  Alert,
  Button,
  CircularProgress,
  useTheme,
  useMediaQuery,
  Breadcrumbs,
  Link,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import HomeIcon from '@mui/icons-material/Home';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import RefreshIcon from '@mui/icons-material/Refresh';
import UnmatchedPlayersSection from '../components/players/UnmatchedPlayersSection';
import PlayerTableFilters, {
  PlayerFilters,
} from '../components/players/PlayerTableFilters';
import PlayerSearchBox from '../components/players/PlayerSearchBox';
import PlayerTable from '../components/players/PlayerTable';
import PlayerMappingModal from '../components/players/PlayerMappingModal';
import { useWeekStore } from '../store/weekStore';

export interface PlayerData {
  id: number;
  player_key: string;
  name: string;
  team: string;
  position: string;
  salary: number;
  projection?: number;
  ownership?: number;
  notes?: string;
  source?: string;
  uploaded_at?: string;
  status: 'matched' | 'unmatched';
  ceiling?: number;
  floor?: number;
}

export interface UnmatchedPlayer {
  id: number;
  imported_name: string;
  team: string;
  position: string;
  salary?: number;
  similarity_score?: number;
}

export interface PlayerSuggestion {
  id?: number;
  player_key: string;
  name: string;
  team: string;
  position: string;
  salary?: number;
  similarity_score: number;
}

export const PlayerManagementPage: React.FC = () => {
  // State Management
  const { currentWeek, weeks } = useWeekStore();
  const [players, setPlayers] = useState<PlayerData[]>([]);
  const [unmatchedPlayers, setUnmatchedPlayers] = useState<UnmatchedPlayer[]>([]);
  const [filteredPlayers, setFilteredPlayers] = useState<PlayerData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRetrying, setIsRetrying] = useState(false);

  // Filter State
  const [filters, setFilters] = useState<PlayerFilters>({
    positions: [],
    teams: [],
    unmatchedOnly: false,
  });
  const [searchQuery, setSearchQuery] = useState('');

  // Modal State
  const [selectedUnmatchedPlayer, setSelectedUnmatchedPlayer] =
    useState<UnmatchedPlayer | undefined>();
  const [modalOpen, setModalOpen] = useState(false);
  const [suggestions, setSuggestions] = useState<PlayerSuggestion[]>([]);
  const [isFetchingSuggestions, setIsFetchingSuggestions] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);

  // Responsive Design
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const navigate = useNavigate();

  // Current week data
  const currentWeekData = weeks.find((w) => w.week_number === currentWeek);

  // Fetch players data
  const fetchPlayers = useCallback(async () => {
    if (!currentWeek) {
      setError('No week selected');
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      // Simulate API call - in real implementation, call actual API
      const mockPlayers: PlayerData[] = [
        {
          id: 1,
          player_key: 'patrick_mahomes_KC_QB',
          name: 'Patrick Mahomes',
          team: 'KC',
          position: 'QB',
          salary: 8000,
          projection: 24.5,
          ownership: 0.35,
          status: 'matched',
          ceiling: 45.2,
          floor: 18.3,
          notes: 'MVP candidate',
          source: 'DraftKings',
          uploaded_at: new Date().toISOString(),
        },
        {
          id: 2,
          player_key: 'travis_kelce_KC_TE',
          name: 'Travis Kelce',
          team: 'KC',
          position: 'TE',
          salary: 7500,
          projection: 18.2,
          ownership: 0.28,
          status: 'matched',
          ceiling: 35.1,
          floor: 12.5,
          notes: 'Team leader',
          source: 'DraftKings',
          uploaded_at: new Date().toISOString(),
        },
        {
          id: 3,
          player_key: 'unmatched_player_1',
          name: 'T. Mahomes',
          team: 'KC',
          position: 'QB',
          salary: 7900,
          projection: undefined,
          ownership: undefined,
          status: 'unmatched',
          notes: 'Partial match',
          source: 'LineStar',
          uploaded_at: new Date().toISOString(),
        },
      ];

      const unmatchedMock: UnmatchedPlayer[] = mockPlayers
        .filter((p) => p.status === 'unmatched')
        .map((p) => ({
          id: p.id,
          imported_name: p.name,
          team: p.team,
          position: p.position,
          salary: p.salary,
          similarity_score: undefined,
        }));

      setPlayers(mockPlayers);
      setUnmatchedPlayers(unmatchedMock);
      setFilteredPlayers(mockPlayers);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch players');
    } finally {
      setIsLoading(false);
    }
  }, [currentWeek]);

  // Apply filters and search
  useEffect(() => {
    let filtered = players;

    // Apply position filter
    if (filters.positions.length > 0) {
      filtered = filtered.filter((p) =>
        filters.positions.includes(p.position)
      );
    }

    // Apply team filter
    if (filters.teams.length > 0) {
      filtered = filtered.filter((p) => filters.teams.includes(p.team));
    }

    // Apply unmatched filter
    if (filters.unmatchedOnly) {
      filtered = filtered.filter((p) => p.status === 'unmatched');
    }

    // Apply search
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter((p) =>
        p.name.toLowerCase().includes(query) ||
        p.player_key.toLowerCase().includes(query)
      );
    }

    setFilteredPlayers(filtered);
  }, [players, filters, searchQuery]);

  // Fetch players on mount and week change
  useEffect(() => {
    fetchPlayers();
  }, [currentWeek, fetchPlayers]);

  // Handle opening mapping modal
  const handleFixClick = useCallback(async (playerId: number) => {
    const unmatched = unmatchedPlayers.find((p) => p.id === playerId);
    if (!unmatched) return;

    setSelectedUnmatchedPlayer(unmatched);
    setModalOpen(true);
    setModalError(null);

    // Fetch suggestions
    try {
      setIsFetchingSuggestions(true);
      // Mock suggestions - in real implementation, call actual API
      const mockSuggestions: PlayerSuggestion[] = [
        {
          player_key: 'patrick_mahomes_KC_QB',
          name: 'Patrick Mahomes',
          team: 'KC',
          position: 'QB',
          salary: 8000,
          similarity_score: 0.95,
        },
      ];
      setSuggestions(mockSuggestions);
    } catch (err) {
      setModalError(
        err instanceof Error ? err.message : 'Failed to fetch suggestions'
      );
    } finally {
      setIsFetchingSuggestions(false);
    }
  }, [unmatchedPlayers]);

  // Handle confirming mapping
  const handleConfirmMapping = useCallback(
    async (selectedPlayer: PlayerSuggestion) => {
      if (!selectedUnmatchedPlayer) return;

      try {
        // In real implementation, call mapping API
        // await mapPlayerAPI(selectedUnmatchedPlayer.id, selectedPlayer.player_key);

        // Update state
        setUnmatchedPlayers((prev) =>
          prev.filter((p) => p.id !== selectedUnmatchedPlayer.id)
        );

        setPlayers((prev) =>
          prev.map((p) =>
            p.id === selectedUnmatchedPlayer.id
              ? { ...p, status: 'matched' as const }
              : p
          )
        );

        setModalOpen(false);
      } catch (err) {
        setModalError(
          err instanceof Error ? err.message : 'Failed to confirm mapping'
        );
        throw err;
      }
    },
    [selectedUnmatchedPlayer]
  );

  const handleRetry = useCallback(() => {
    setIsRetrying(true);
    fetchPlayers().finally(() => setIsRetrying(false));
  }, [fetchPlayers]);

  return (
    <Box
      sx={{
        padding: isMobile ? '16px' : '24px',
        backgroundColor: '#0a0a0a',
        minHeight: '100vh',
      }}
    >
      <Stack spacing={3}>
        {/* Breadcrumb Navigation */}
        <Breadcrumbs
          sx={{
            color: '#e5e7eb',
            fontSize: '0.85rem',
            '& .MuiBreadcrumbs-separator': {
              color: '#9ca3af',
            },
          }}
        >
          <Link
            onClick={() => navigate('/')}
            sx={{
              color: '#ff8c42',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 0.5,
              textDecoration: 'none',
              '&:hover': {
                textDecoration: 'underline',
              },
            }}
          >
            <HomeIcon sx={{ fontSize: '1rem' }} />
            Home
          </Link>
          <Typography sx={{ color: '#e5e7eb' }}>Players</Typography>
        </Breadcrumbs>

        {/* Page Header */}
        <Stack spacing={1}>
          <Typography
            variant="h4"
            sx={{
              color: '#ffffff',
              fontWeight: 700,
              fontSize: isMobile ? '1.75rem' : '2rem',
              letterSpacing: '-0.5px',
            }}
          >
            Player Management
          </Typography>
          {currentWeekData && (
            <Typography
              variant="body2"
              sx={{
                color: '#9ca3af',
                fontSize: '0.9rem',
              }}
            >
              Week {currentWeekData.week_number} of {currentWeekData.season}
              {currentWeekData.status === 'active' && (
                <span style={{ marginLeft: '8px', color: '#ff8c42' }}>
                  (Active)
                </span>
              )}
            </Typography>
          )}
        </Stack>

        {/* Error State */}
        {error && (
          <Alert
            severity="error"
            icon={<ErrorOutlineIcon />}
            action={
              <Button
                color="inherit"
                size="small"
                onClick={handleRetry}
                disabled={isRetrying}
                startIcon={<RefreshIcon />}
                sx={{
                  textTransform: 'none',
                }}
              >
                {isRetrying ? 'Retrying...' : 'Retry'}
              </Button>
            }
            sx={{
              backgroundColor: 'rgba(244, 67, 54, 0.1)',
              color: '#ff5722',
              borderColor: '#ff5722',
              borderRadius: '8px',
            }}
          >
            {error}
          </Alert>
        )}

        {/* Loading State */}
        {isLoading && (
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              minHeight: '400px',
              gap: 2,
            }}
          >
            <CircularProgress sx={{ color: '#ff8c42' }} size={40} />
            <Typography
              variant="body2"
              sx={{
                color: '#9ca3af',
              }}
            >
              Loading player data...
            </Typography>
          </Box>
        )}

        {/* Content */}
        {!isLoading && (
          <>
            {/* Unmatched Players Section */}
            <UnmatchedPlayersSection
              players={unmatchedPlayers}
              onFixClick={handleFixClick}
              isLoading={false}
            />

            {/* Filter and Search Controls */}
            <Stack spacing={2}>
              <PlayerSearchBox
                onSearch={setSearchQuery}
                placeholder="Search players by name..."
              />
              <PlayerTableFilters onFilterChange={setFilters} />
            </Stack>

            {/* Player Table */}
            <PlayerTable
              players={filteredPlayers}
              isLoading={false}
            />

            {/* Results Summary */}
            <Box
              sx={{
                padding: '12px 16px',
                backgroundColor: 'rgba(255, 255, 255, 0.02)',
                borderRadius: '6px',
                border: '1px solid rgba(255, 255, 255, 0.1)',
              }}
            >
              <Typography
                variant="caption"
                sx={{
                  color: '#9ca3af',
                  fontSize: '0.8rem',
                }}
              >
                Showing {filteredPlayers.length} of {players.length} players
                {unmatchedPlayers.length > 0 && (
                  <>
                    {' '}
                    ({unmatchedPlayers.length} unmatched)
                  </>
                )}
              </Typography>
            </Box>
          </>
        )}
      </Stack>

      {/* Player Mapping Modal */}
      <PlayerMappingModal
        open={modalOpen}
        unmatchedPlayer={selectedUnmatchedPlayer}
        suggestions={suggestions}
        onClose={() => setModalOpen(false)}
        onConfirm={handleConfirmMapping}
        isFetching={isFetchingSuggestions}
        error={modalError}
      />
    </Box>
  );
};

export default PlayerManagementPage;
