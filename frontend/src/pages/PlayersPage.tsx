/**
 * Players Management Page
 *
 * Main page component for player management with:
 * - Unmatched players alert section
 * - Player filtering and search controls
 * - Player table with sorting and virtual scrolling
 * - Player mapping modal workflow
 *
 * Design: Factory.ai inspired (black, white, orange accents)
 *
 * Mobile Responsive:
 * - Adjusted spacing and padding for mobile
 * - Full-width container on mobile
 * - Responsive typography
 *
 * Integrates:
 * - usePlayerManagement hook for data fetching
 * - usePlayerFiltering hook for filter state
 * - usePlayerSorting hook for sort state
 * - usePlayerMapping hook for modal workflow
 */

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  CircularProgress,
  Stack,
  Alert,
  Button,
  Snackbar,
  useTheme,
  useMediaQuery,
  IconButton,
} from '@mui/material';
import HomeIcon from '@mui/icons-material/Home';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { useWeekStore } from '../store/weekStore';
import {
  usePlayerManagement,
  usePlayerFiltering,
  usePlayerSorting,
  usePlayerMapping,
} from '../hooks';
import {
  UnmatchedPlayersSection,
  PlayerTable,
  PlayerTableFilters,
  PlayerSearchBox,
  PlayerMappingModal,
} from '../components/players';
import RefreshIcon from '@mui/icons-material/Refresh';
import type { UnmatchedPlayerResponse, PlayerResponse, PlayerFilters } from '../types/player.types';

export const PlayersPage: React.FC = () => {
  const navigate = useNavigate();
  const currentWeekNumber = useWeekStore((state) => state.currentWeek);
  const getCurrentWeekData = useWeekStore((state) => state.getCurrentWeekData);
  const weeks = useWeekStore((state) => state.weeks);
  const currentWeek = getCurrentWeekData();
  const [showSuccessNotification, setShowSuccessNotification] = useState(false);
  const [notificationMessage, setNotificationMessage] = useState('');
  const [showErrorNotification, setShowErrorNotification] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  // Debug: log week state
  useEffect(() => {
    if (currentWeek) {
      console.log('PlayersPage: currentWeek =', currentWeek);
    }
  }, [currentWeek]);

  // Fetch player data
  const weekId = currentWeek?.id ?? null;
  const {
    players,
    unmatchedPlayers,
    isLoading,
    error: fetchError,
    refetch,
    invalidateCache,
  } = usePlayerManagement(weekId);

  // Manage filters
  const {
    filteredPlayers,
    setPositionFilter,
    setTeamFilter,
    setUnmatchedOnly,
    setSearchQuery,
    clearAllFilters,
    hasActiveFilters,
  } = usePlayerFiltering(players);

  // Manage sorting
  const {
    sortedPlayers,
  } = usePlayerSorting(filteredPlayers);

  // Manage mapping modal and workflow
  const {
    isModalOpen,
    selectedUnmatchedPlayer,
    suggestions,
    selectedMatch,
    isSuggestionsLoading,
    mappingError: submitError,
    openModal,
    closeModal,
    submitMapping,
  } = usePlayerMapping(async () => {
    // On successful mapping:
    // 1. Show success notification
    setNotificationMessage('Player mapped successfully!');
    setShowSuccessNotification(true);

    // 2. Invalidate cache to refresh data
    await invalidateCache();
  });

  // Set page title
  useEffect(() => {
    document.title = 'Player Management - Lineup Lab';
  }, []);

  // Refresh data when week changes
  useEffect(() => {
    if (currentWeekNumber) {
      refetch();
    }
  }, [currentWeekNumber, refetch]);

  // Handle error retry
  const handleRetry = () => {
    refetch();
  };

  // Handle mapping confirmation with selected match
  const handleMappingConfirm = async () => {
    if (!selectedMatch) {
      setErrorMessage('Please select a player to map');
      setShowErrorNotification(true);
      return;
    }

    try {
      await submitMapping();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Failed to map player');
      setShowErrorNotification(true);
    }
  };

  // Handle week not selected
  if (!currentWeek) {
    return (
      <Container maxWidth="lg" sx={{ py: { xs: 4, sm: 6 } }}>
        <Box sx={{ textAlign: 'center' }}>
          <Alert
            severity="info"
            sx={{
              backgroundColor: 'rgba(255, 107, 53, 0.1)',
              borderColor: 'rgba(255, 107, 53, 0.3)',
              color: '#ffffff',
            }}
          >
            Please select a week to view players
          </Alert>
        </Box>
      </Container>
    );
  }

  // Handle loading state
  if (isLoading) {
    return (
      <Container maxWidth="lg">
        <Box
          sx={{
            py: { xs: 6, sm: 8 },
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '60vh',
          }}
        >
          <Stack alignItems="center" spacing={2}>
            <CircularProgress sx={{ color: '#ff6b35' }} />
            <Typography color="text.secondary" sx={{ fontSize: isMobile ? '0.9rem' : '1rem' }}>
              Loading players...
            </Typography>
          </Stack>
        </Box>
      </Container>
    );
  }

  // Handle error state
  if (fetchError) {
    return (
      <Container maxWidth="lg" sx={{ py: { xs: 4, sm: 6 } }}>
        <Box>
          <Alert
            severity="error"
            sx={{
              fontSize: isMobile ? '0.85rem' : '0.95rem',
            }}
          >
            <Typography
              variant="subtitle2"
              sx={{ fontWeight: 600, mb: 1, fontSize: 'inherit' }}
            >
              Failed to load players
            </Typography>
            <Typography variant="body2" sx={{ mb: 2, color: 'inherit', fontSize: 'inherit' }}>
              {fetchError instanceof Error ? fetchError.message : 'An error occurred while fetching player data'}
            </Typography>
            <Button
              variant="contained"
              size={isMobile ? 'small' : 'medium'}
              startIcon={<RefreshIcon />}
              onClick={handleRetry}
              sx={{
                mt: 1,
                minHeight: isMobile ? '40px' : 'auto',
              }}
            >
              Retry
            </Button>
          </Alert>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: { xs: 4, sm: 6 } }}>
      <Box>
        {/* Page Header */}
        <Box sx={{ mb: { xs: 5, sm: 6 } }}>
          <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 3 }}>
            <IconButton
              onClick={() => navigate('/')}
              sx={{
                color: '#ff6b35',
                border: '1px solid rgba(255, 107, 53, 0.2)',
                borderRadius: '10px',
                width: 40,
                height: 40,
                '&:hover': {
                  backgroundColor: 'rgba(255, 107, 53, 0.1)',
                  borderColor: '#ff6b35',
                },
              }}
              aria-label="Back to home"
            >
              <ArrowBackIcon fontSize="small" />
            </IconButton>
            <Button
              startIcon={<HomeIcon />}
              onClick={() => navigate('/')}
              sx={{
                color: '#ff6b35',
                textTransform: 'none',
                fontWeight: 500,
                fontSize: '0.9375rem',
                borderRadius: '10px',
                px: 2,
                '&:hover': {
                  backgroundColor: 'rgba(255, 107, 53, 0.08)',
                },
              }}
            >
              Home
            </Button>
          </Stack>
          <Typography
            variant="h2"
            sx={{
              fontWeight: 700,
              mb: 2,
              fontSize: { xs: '2rem', sm: '2.5rem', md: '3rem' },
              color: '#ffffff',
              letterSpacing: '-0.02em',
              lineHeight: 1.2,
            }}
          >
            Player Management
          </Typography>
          <Typography
            variant="body1"
            color="text.secondary"
            sx={{
              fontSize: { xs: '0.9375rem', sm: '1rem', md: '1.0625rem' },
              fontWeight: 300,
              lineHeight: 1.6,
            }}
          >
            Week {currentWeek.week_number} - {currentWeek.season} Season • {players.length} total players
          </Typography>
        </Box>

        {/* Unmatched Players Section */}
        {unmatchedPlayers.length > 0 && (
          <Box sx={{ mb: { xs: 3, sm: 4 } }}>
            <UnmatchedPlayersSection
              players={unmatchedPlayers as any[]}
              count={unmatchedPlayers.length}
              onFixClick={(player: UnmatchedPlayerResponse) => openModal(player)}
              isLoading={false}
            />
          </Box>
        )}

        {/* Filter and Search Controls */}
        <Box sx={{ mb: { xs: 3, sm: 4 } }}>
          <Stack spacing={isMobile ? 2 : 2.5}>
            {/* Search Box */}
            <Box>
              <PlayerSearchBox
                onSearch={setSearchQuery}
                placeholder="Search by player name..."
              />
            </Box>

            {/* Filters */}
            <Box>
              <PlayerTableFilters
                onFilterChange={(newFilters: PlayerFilters) => {
                  setPositionFilter(newFilters.positions || []);
                  setTeamFilter(newFilters.teams || []);
                  setUnmatchedOnly(newFilters.unmatchedOnly || false);
                }}
              />
            </Box>

            {/* Active filters indicator and clear button */}
            {hasActiveFilters && (
              <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  size={isMobile ? 'small' : 'medium'}
                  variant="text"
                  onClick={clearAllFilters}
                  sx={{
                    minHeight: isMobile ? '40px' : 'auto',
                  }}
                >
                  Clear Filters
                </Button>
              </Box>
            )}
          </Stack>
        </Box>

        {/* Player Table */}
        <Box sx={{ mb: { xs: 3, sm: 4 }, overflow: 'hidden' }}>
          <PlayerTable
            players={sortedPlayers as any[]}
            isLoading={isLoading}
          />
        </Box>

        {/* Empty State */}
        {!isLoading && sortedPlayers.length === 0 && (
          <Box sx={{ py: { xs: 4, sm: 6 }, textAlign: 'center' }}>
            <Typography
              color="text.secondary"
              sx={{ mb: 2, fontSize: isMobile ? '0.9rem' : '1rem' }}
            >
              {hasActiveFilters ? 'No players match your filters' : 'No players found for this week'}
            </Typography>
            {hasActiveFilters && (
              <Button
                variant="text"
                onClick={clearAllFilters}
                sx={{
                  minHeight: isMobile ? '40px' : 'auto',
                }}
              >
                Clear Filters
              </Button>
            )}
          </Box>
        )}

        {/* Player Mapping Modal */}
        {selectedUnmatchedPlayer && (
          <PlayerMappingModal
            open={isModalOpen}
            unmatchedPlayer={{
              id: selectedUnmatchedPlayer.id,
              imported_name: selectedUnmatchedPlayer.imported_name,
              team: selectedUnmatchedPlayer.team,
              position: selectedUnmatchedPlayer.position,
              salary: selectedUnmatchedPlayer.salary ?? undefined,
            }}
            suggestions={suggestions.map((s: PlayerResponse) => ({
              id: s.id,
              player_key: s.player_key,
              name: s.name,
              team: s.team,
              position: s.position,
              salary: s.salary,
              similarity_score: s.similarity_score ?? 0,
            }))}
            onClose={closeModal}
            onConfirm={handleMappingConfirm}
            isFetching={isSuggestionsLoading}
            error={submitError}
          />
        )}

        {/* Success Notification */}
        <Snackbar
          open={showSuccessNotification}
          autoHideDuration={3000}
          onClose={() => setShowSuccessNotification(false)}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        >
          <Alert severity="success" sx={{ minWidth: isMobile ? 'calc(100vw - 32px)' : 'auto' }}>
            {notificationMessage}
          </Alert>
        </Snackbar>

        {/* Error Notification */}
        <Snackbar
          open={showErrorNotification}
          autoHideDuration={4000}
          onClose={() => setShowErrorNotification(false)}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        >
          <Alert severity="error" sx={{ minWidth: isMobile ? 'calc(100vw - 32px)' : 'auto' }}>
            {errorMessage}
          </Alert>
        </Snackbar>
      </Box>
    </Container>
  );
};

export default PlayersPage;
