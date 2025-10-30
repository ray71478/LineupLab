/**
 * UnmatchedPlayerCard Component
 *
 * Individual card displaying unmatched player information with "Fix" button.
 * Shows player name, team, position, and salary with option to open mapping modal.
 *
 * Mobile Optimizations:
 * - Full-width on mobile
 * - Touch button >= 44x44px
 * - Proper spacing and readable text
 */

import React from 'react';
import {
  Card,
  CardContent,
  Box,
  Typography,
  Button,
  Stack,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import BuildIcon from '@mui/icons-material/Build';

export interface UnmatchedPlayer {
  id: number;
  imported_name: string;
  team: string;
  position: string;
  salary?: number;
  similarity_score?: number;
}

export interface UnmatchedPlayerCardProps {
  player: UnmatchedPlayer;
  onFixClick: (playerId: number) => void;
}

export const UnmatchedPlayerCard: React.FC<UnmatchedPlayerCardProps> = ({
  player,
  onFixClick,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const handleClick = () => {
    onFixClick(player.id);
  };

  return (
    <Card
      sx={{
        backgroundColor: '#1a1a2e',
        border: '2px solid rgba(255, 140, 66, 0.4)',
        borderRadius: '8px',
        padding: isMobile ? '12px' : '16px',
        transition: 'all 0.2s ease-in-out',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        // Focus state for keyboard navigation
        '&:focus-within': {
          borderColor: '#ff8c42',
          boxShadow: '0 0 0 2px rgba(255, 140, 66, 0.2)',
        },
        // Click/tap state
        '&:active': {
          transform: 'scale(0.98)',
        },
      }}
    >
      <CardContent sx={{ padding: 0, flex: 1 }}>
        <Stack spacing={isMobile ? 0.75 : 1}>
          {/* Player Name */}
          <Typography
            variant="h6"
            sx={{
              fontSize: isMobile ? '0.9rem' : '1.1rem',
              fontWeight: 600,
              color: '#ffffff',
              wordBreak: 'break-word',
            }}
            title={player.imported_name}
          >
            {player.imported_name}
          </Typography>

          {/* Player Info Row */}
          <Stack
            direction="row"
            spacing={1}
            sx={{
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: isMobile ? 0.5 : 1,
            }}
          >
            {/* Team */}
            <Box
              sx={{
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                padding: isMobile ? '3px 6px' : '4px 8px',
                borderRadius: '4px',
              }}
            >
              <Typography
                variant="caption"
                sx={{
                  color: '#e5e7eb',
                  fontSize: isMobile ? '0.75rem' : '0.8rem',
                  fontWeight: 500,
                }}
              >
                {player.team}
              </Typography>
            </Box>

            {/* Position */}
            <Box
              sx={{
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                padding: isMobile ? '3px 6px' : '4px 8px',
                borderRadius: '4px',
              }}
            >
              <Typography
                variant="caption"
                sx={{
                  color: '#e5e7eb',
                  fontSize: isMobile ? '0.75rem' : '0.8rem',
                  fontWeight: 500,
                }}
              >
                {player.position}
              </Typography>
            </Box>

            {/* Salary */}
            {player.salary && (
              <Box
                sx={{
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                  padding: isMobile ? '3px 6px' : '4px 8px',
                  borderRadius: '4px',
                }}
              >
                <Typography
                  variant="caption"
                  sx={{
                    color: '#e5e7eb',
                    fontSize: isMobile ? '0.75rem' : '0.8rem',
                    fontWeight: 500,
                  }}
                >
                  ${player.salary.toLocaleString()}
                </Typography>
              </Box>
            )}
          </Stack>

          {/* Confidence Score (if available) */}
          {player.similarity_score !== undefined && (
            <Typography
              variant="caption"
              sx={{
                color: '#9ca3af',
                fontSize: isMobile ? '0.7rem' : '0.75rem',
              }}
            >
              Match score: {(player.similarity_score * 100).toFixed(0)}%
            </Typography>
          )}
        </Stack>
      </CardContent>

      {/* Fix Button - Touch target >= 44x44px */}
      <Box sx={{ marginTop: isMobile ? 1.5 : 2 }}>
        <Button
          variant="contained"
          startIcon={<BuildIcon />}
          onClick={handleClick}
          aria-label={`Fix mapping for ${player.imported_name}`}
          sx={{
            backgroundColor: '#ff8c42',
            color: '#ffffff',
            width: '100%',
            textTransform: 'none',
            fontWeight: 500,
            // Touch target sizing
            minHeight: isMobile ? '44px' : '40px',
            padding: isMobile ? '10px 16px' : '10px 16px',
            borderRadius: '6px',
            transition: 'all 0.2s ease-in-out',
            fontSize: isMobile ? '0.9rem' : '0.95rem',
            // Hover state - only on devices that support it
            '@media (hover: hover)': {
              '&:hover': {
                backgroundColor: '#ff6b35',
                boxShadow: '0 4px 12px rgba(255, 140, 66, 0.3)',
              },
            },
            // Active/pressed state
            '&:active': {
              transform: 'scale(0.98)',
            },
            // Focus state for keyboard navigation
            '&:focus-visible': {
              outline: '2px solid #ff8c42',
              outlineOffset: '2px',
            },
          }}
        >
          Fix
        </Button>
      </Box>
    </Card>
  );
};

export default UnmatchedPlayerCard;
