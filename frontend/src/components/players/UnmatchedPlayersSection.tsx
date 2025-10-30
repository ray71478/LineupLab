/**
 * UnmatchedPlayersSection Component
 *
 * Displays unmatched players in an alert box with grid of cards.
 * Hides section when no unmatched players exist.
 *
 * Accessibility Features:
 * - ARIA live region to announce unmatched player count
 * - Semantic alert structure with role="region"
 * - aria-label for dynamic count
 * - Card grid with proper ARIA attributes
 */

import React, { useMemo } from 'react';
import {
  Box,
  Typography,
  Grid,
  Stack,
  Alert,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import WarningIcon from '@mui/icons-material/Warning';
import UnmatchedPlayerCard from './UnmatchedPlayerCard';

export interface UnmatchedPlayer {
  id: number;
  imported_name: string;
  team: string;
  position: string;
  salary?: number;
  similarity_score?: number;
}

export interface UnmatchedPlayersSectionProps {
  players: UnmatchedPlayer[];
  onFixClick: (playerId: number) => void;
  isLoading?: boolean;
}

export const UnmatchedPlayersSection: React.FC<UnmatchedPlayersSectionProps> = React.memo(({
  players,
  onFixClick,
  isLoading = false,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm')); // < 600px
  const isTablet = useMediaQuery(theme.breakpoints.down('md')); // < 960px

  const alertMessage = useMemo(
    () => players.length === 1
      ? '1 Player Needs Mapping'
      : `${players.length} Players Need Mapping`,
    [players.length]
  );

  // Hide section if no unmatched players
  if (players.length === 0 && !isLoading) {
    return null;
  }

  return (
    <Box
      role="region"
      aria-label="Unmatched Players Section"
      aria-live="polite"
      aria-atomic="true"
      sx={{
        marginBottom: '32px',
        animation: 'fadeIn 0.3s ease-in-out',
        '@keyframes fadeIn': {
          from: {
            opacity: 0,
            transform: 'translateY(-10px)',
          },
          to: {
            opacity: 1,
            transform: 'translateY(0)',
          },
        },
      }}
    >
      {/* Alert Box with Count */}
      <Alert
        severity="warning"
        icon={<WarningIcon sx={{ fontSize: '1.5rem' }} />}
        sx={{
          backgroundColor: 'rgba(255, 87, 34, 0.1)',
          border: '2px solid #ff5722',
          borderRadius: '8px',
          padding: '16px 20px',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: isMobile ? 'wrap' : 'nowrap',
          gap: 2,
        }}
        role="alert"
      >
        <Stack spacing={0.5}>
          <Typography
            variant="subtitle1"
            sx={{
              fontWeight: 600,
              color: '#ffffff',
              fontSize: isMobile ? '0.95rem' : '1.1rem',
            }}
            id="unmatched-count"
          >
            {alertMessage}
          </Typography>
          <Typography
            variant="caption"
            sx={{
              color: '#e5e7eb',
              fontSize: '0.8rem',
            }}
          >
            These players could not be automatically matched and require manual review.
          </Typography>
        </Stack>
      </Alert>

      {/* Cards Grid */}
      <Grid
        container
        spacing={2}
        sx={{
          width: '100%',
        }}
        role="list"
        aria-labelledby="unmatched-count"
      >
        {players.map((player) => (
          <Grid item xs={12} sm={6} md={4} lg={3} key={player.id} role="listitem">
            <UnmatchedPlayerCard
              player={player}
              onFixClick={onFixClick}
            />
          </Grid>
        ))}
      </Grid>
    </Box>
  );
});

UnmatchedPlayersSection.displayName = 'UnmatchedPlayersSection';

export default UnmatchedPlayersSection;
