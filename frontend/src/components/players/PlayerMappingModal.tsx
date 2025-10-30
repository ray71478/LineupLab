/**
 * PlayerMappingModal Component
 *
 * Modal for mapping unmatched players to canonical players.
 * Shows player info, fuzzy match suggestions, and manual search.
 *
 * Mobile Optimizations:
 * - Full-screen on mobile
 * - Large touch buttons (44x44px minimum)
 * - Scrollable content area
 * - No hover-only interactions
 */

import React, { useState, useCallback, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Stack,
  Typography,
  CircularProgress,
  Alert,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import BuildIcon from '@mui/icons-material/Build';
import FuzzyMatchSuggestions from './FuzzyMatchSuggestions';
import PlayerSearchBox from './PlayerSearchBox';

export interface UnmatchedPlayer {
  id: number;
  imported_name: string;
  team: string;
  position: string;
  salary?: number;
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

export interface PlayerMappingModalProps {
  open: boolean;
  unmatchedPlayer?: UnmatchedPlayer;
  suggestions: PlayerSuggestion[];
  onClose: () => void;
  onConfirm: (selectedPlayer: PlayerSuggestion) => Promise<void>;
  onSkip?: () => void;
  isLoading?: boolean;
  isFetching?: boolean;
  error?: string | null;
}

export const PlayerMappingModal: React.FC<PlayerMappingModalProps> = ({
  open,
  unmatchedPlayer,
  suggestions,
  onClose,
  onConfirm,
  onSkip,
  isLoading = false,
  isFetching = false,
  error = null,
}) => {
  const [selectedPlayer, setSelectedPlayer] = useState<PlayerSuggestion | undefined>();
  const [searchResults, setSearchResults] = useState<PlayerSuggestion[]>([]);
  const [isConfirming, setIsConfirming] = useState(false);
  const [confirmError, setConfirmError] = useState<string | null>(null);

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  // Reset state when modal opens/closes
  useEffect(() => {
    if (open) {
      setSelectedPlayer(suggestions.length > 0 ? suggestions[0] : undefined);
      setSearchResults([]);
      setConfirmError(null);
    }
  }, [open, suggestions]);

  const handleSelectSuggestion = useCallback((player: PlayerSuggestion) => {
    setSelectedPlayer(player);
    setSearchResults([]);
  }, []);

  const handleSearch = useCallback((query: string) => {
    // Filter suggestions locally by player name or key
    if (query.trim()) {
      const filtered = suggestions.filter(
        (p) =>
          p.name.toLowerCase().includes(query.toLowerCase()) ||
          p.player_key.toLowerCase().includes(query.toLowerCase())
      );
      setSearchResults(filtered);
      // Auto-select first search result if only one match
      if (filtered.length === 1) {
        setSelectedPlayer(filtered[0]);
      }
    } else {
      setSearchResults([]);
    }
  }, [suggestions]);

  const handleConfirm = async () => {
    if (!selectedPlayer) {
      setConfirmError('Please select a player to map');
      return;
    }

    setIsConfirming(true);
    setConfirmError(null);

    try {
      await onConfirm(selectedPlayer);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to confirm mapping';
      setConfirmError(errorMsg);
      console.error('Mapping error:', err);
    } finally {
      setIsConfirming(false);
    }
  };

  const displaySuggestions = searchResults.length > 0 ? searchResults : suggestions;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      fullWidth
      maxWidth="sm"
      fullScreen={isMobile}
      PaperProps={{
        sx: {
          backgroundColor: '#1a1a2e',
          borderRadius: isMobile ? '0px' : '12px',
          border: '1px solid rgba(255, 140, 66, 0.3)',
          // Prevent layout shift on mobile
          m: isMobile ? 0 : 2,
        },
      }}
    >
      {/* Dialog Title */}
      <DialogTitle
        sx={{
          backgroundColor: '#0a0a0a',
          color: '#ffffff',
          borderBottom: '1px solid rgba(255, 140, 66, 0.2)',
          padding: isMobile ? '16px' : '20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 1,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <BuildIcon sx={{ color: '#ff8c42' }} />
          <div>
            <Typography
              variant="h6"
              sx={{
                fontWeight: 600,
                fontSize: isMobile ? '1rem' : '1.1rem',
              }}
            >
              Map Player
            </Typography>
            {unmatchedPlayer && (
              <Typography
                variant="caption"
                sx={{
                  color: '#9ca3af',
                  fontSize: isMobile ? '0.75rem' : '0.8rem',
                }}
              >
                {unmatchedPlayer.imported_name}
              </Typography>
            )}
          </div>
        </Box>
        <Button
          onClick={onClose}
          disabled={isConfirming}
          aria-label="Close modal"
          sx={{
            minWidth: 'auto',
            width: isMobile ? '40px' : 'auto',
            height: isMobile ? '40px' : 'auto',
            color: '#9ca3af',
            '&:hover': {
              color: '#ff8c42',
              backgroundColor: 'rgba(255, 140, 66, 0.1)',
            },
          }}
        >
          <CloseIcon />
        </Button>
      </DialogTitle>

      {/* Dialog Content - Scrollable */}
      <DialogContent
        sx={{
          padding: isMobile ? '16px' : '24px',
          backgroundColor: '#1a1a2e',
          // Ensure scrollable area
          overflowY: 'auto',
          maxHeight: isMobile ? 'calc(100vh - 140px)' : 'auto',
        }}
      >
        <Stack spacing={isMobile ? 2 : 3}>
          {/* Unmatched Player Info */}
          {unmatchedPlayer && (
            <Box
              sx={{
                padding: isMobile ? '12px' : '16px',
                backgroundColor: 'rgba(255, 87, 34, 0.1)',
                border: '1px solid rgba(255, 87, 34, 0.3)',
                borderRadius: '8px',
              }}
            >
              <Typography
                variant="subtitle2"
                sx={{
                  color: '#ff5722',
                  fontWeight: 600,
                  marginBottom: '8px',
                  fontSize: isMobile ? '0.8rem' : '0.85rem',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                }}
              >
                Unmatched Player
              </Typography>
              <Stack spacing={1}>
                <Typography
                  variant="body2"
                  sx={{
                    color: '#ffffff',
                    fontWeight: 500,
                    fontSize: isMobile ? '0.95rem' : '1rem',
                  }}
                >
                  {unmatchedPlayer.imported_name}
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {unmatchedPlayer.team && (
                    <Typography
                      variant="caption"
                      sx={{
                        backgroundColor: 'rgba(255, 87, 34, 0.2)',
                        color: '#ff5722',
                        padding: '2px 6px',
                        borderRadius: '3px',
                        fontSize: isMobile ? '0.7rem' : '0.75rem',
                      }}
                    >
                      {unmatchedPlayer.team}
                    </Typography>
                  )}
                  {unmatchedPlayer.position && (
                    <Typography
                      variant="caption"
                      sx={{
                        backgroundColor: 'rgba(255, 87, 34, 0.2)',
                        color: '#ff5722',
                        padding: '2px 6px',
                        borderRadius: '3px',
                        fontSize: isMobile ? '0.7rem' : '0.75rem',
                      }}
                    >
                      {unmatchedPlayer.position}
                    </Typography>
                  )}
                  {unmatchedPlayer.salary && (
                    <Typography
                      variant="caption"
                      sx={{
                        backgroundColor: 'rgba(255, 87, 34, 0.2)',
                        color: '#ff5722',
                        padding: '2px 6px',
                        borderRadius: '3px',
                        fontSize: isMobile ? '0.7rem' : '0.75rem',
                      }}
                    >
                      ${unmatchedPlayer.salary.toLocaleString()}
                    </Typography>
                  )}
                </Box>
              </Stack>
            </Box>
          )}

          {/* API Error Alert */}
          {error && (
            <Alert
              severity="error"
              sx={{
                backgroundColor: 'rgba(244, 67, 54, 0.1)',
                color: '#ff5722',
                borderColor: '#ff5722',
                fontSize: isMobile ? '0.8rem' : '0.9rem',
              }}
            >
              <Typography variant="body2" sx={{ fontSize: 'inherit' }}>
                {error}
              </Typography>
            </Alert>
          )}

          {/* Confirmation Error Alert */}
          {confirmError && (
            <Alert
              severity="error"
              sx={{
                backgroundColor: 'rgba(244, 67, 54, 0.1)',
                color: '#ff5722',
                borderColor: '#ff5722',
                fontSize: isMobile ? '0.8rem' : '0.9rem',
              }}
            >
              <Typography variant="body2" sx={{ fontSize: 'inherit' }}>
                {confirmError}
              </Typography>
            </Alert>
          )}

          {/* Manual Search Box */}
          <Box>
            <Typography
              variant="subtitle2"
              sx={{
                color: '#e5e7eb',
                marginBottom: '8px',
                fontWeight: 600,
                fontSize: isMobile ? '0.85rem' : '0.9rem',
              }}
            >
              Search or Browse Suggestions
            </Typography>
            <PlayerSearchBox
              onSearch={handleSearch}
              placeholder="Search for a player..."
            />
          </Box>

          {/* Suggestions List - with loading state */}
          <Box>
            {isFetching ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', padding: '20px' }}>
                <Stack alignItems="center" spacing={1}>
                  <CircularProgress sx={{ color: '#ff8c42' }} size={32} />
                  <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.85rem' }}>
                    Loading suggestions...
                  </Typography>
                </Stack>
              </Box>
            ) : (
              <FuzzyMatchSuggestions
                suggestions={displaySuggestions}
                selectedPlayer={selectedPlayer}
                onSelectSuggestion={handleSelectSuggestion}
                isLoading={isLoading}
              />
            )}
          </Box>

          {/* Selected Player Info */}
          {selectedPlayer && (
            <Box
              sx={{
                padding: isMobile ? '12px' : '12px 16px',
                backgroundColor: 'rgba(76, 175, 80, 0.1)',
                border: '2px solid rgba(76, 175, 80, 0.4)',
                borderRadius: '6px',
              }}
            >
              <Typography
                variant="caption"
                sx={{
                  color: '#4caf50',
                  fontWeight: 600,
                  fontSize: isMobile ? '0.7rem' : '0.75rem',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                }}
              >
                Selected Match
              </Typography>
              <Typography
                variant="body2"
                sx={{
                  color: '#ffffff',
                  fontWeight: 500,
                  marginTop: '6px',
                  fontSize: isMobile ? '0.95rem' : '1rem',
                }}
              >
                {selectedPlayer.name}
              </Typography>
              <Typography
                variant="caption"
                sx={{
                  color: '#9ca3af',
                  display: 'block',
                  marginTop: '4px',
                  fontSize: isMobile ? '0.75rem' : '0.85rem',
                }}
              >
                {selectedPlayer.team} • {selectedPlayer.position}
              </Typography>
            </Box>
          )}
        </Stack>
      </DialogContent>

      {/* Dialog Actions - Touch buttons >= 44x44px */}
      <DialogActions
        sx={{
          backgroundColor: '#0a0a0a',
          borderTop: '1px solid rgba(255, 140, 66, 0.2)',
          padding: isMobile ? '12px' : '16px',
          gap: 1,
          justifyContent: isMobile ? 'stretch' : 'flex-end',
          flexDirection: isMobile ? 'column' : 'row',
        }}
      >
        {onSkip && (
          <Button
            onClick={onSkip}
            disabled={isConfirming}
            sx={{
              color: '#9ca3af',
              textTransform: 'none',
              minHeight: isMobile ? '44px' : 'auto',
              fontSize: isMobile ? '0.95rem' : '0.9rem',
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.05)',
              },
              flex: isMobile ? 1 : 'auto',
            }}
          >
            Skip for Now
          </Button>
        )}

        <Button
          onClick={onClose}
          disabled={isConfirming}
          sx={{
            color: '#9ca3af',
            textTransform: 'none',
            minHeight: isMobile ? '44px' : 'auto',
            fontSize: isMobile ? '0.95rem' : '0.9rem',
            '&:hover': {
              backgroundColor: 'rgba(255, 255, 255, 0.05)',
            },
            flex: isMobile ? 1 : 'auto',
          }}
        >
          Cancel
        </Button>

        <Button
          onClick={handleConfirm}
          disabled={!selectedPlayer || isConfirming}
          variant="contained"
          sx={{
            backgroundColor: '#ff8c42',
            color: '#ffffff',
            textTransform: 'none',
            fontWeight: 500,
            minHeight: isMobile ? '44px' : 'auto',
            fontSize: isMobile ? '0.95rem' : '0.9rem',
            '@media (hover: hover)': {
              '&:hover': {
                backgroundColor: '#ff6b35',
              },
            },
            '&:disabled': {
              backgroundColor: 'rgba(255, 140, 66, 0.3)',
              color: 'rgba(255, 255, 255, 0.5)',
            },
            minWidth: isMobile ? 'auto' : '120px',
            flex: isMobile ? 1 : 'auto',
          }}
        >
          {isConfirming ? (
            <>
              <CircularProgress
                size={16}
                sx={{ marginRight: '8px', color: 'inherit' }}
              />
              Confirming...
            </>
          ) : (
            'Confirm Mapping'
          )}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default PlayerMappingModal;
