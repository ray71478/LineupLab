/**
 * RefreshMySportsFeedsButton Component
 *
 * Button to manually trigger API data refresh from the header.
 * Fetches and updates:
 * - Vegas lines (Implied Team Total for W7 factor)
 * - Player injuries (for availability filtering)
 * - Team defensive stats (for W8 factor)
 * - Player game logs (for trend analysis)
 * - Opponent data from ESPN API (fills missing opponents)
 *
 * Features:
 * - Shows loading spinner during refresh
 * - Displays success/error toast notifications
 * - Shows detailed refresh statistics in success toast
 * - Disables button during refresh to prevent double-clicking
 */

import React, { useState } from 'react';
import {
  Button,
  CircularProgress,
  Box,
  Snackbar,
  Alert,
  AlertTitle,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import { useRefreshMySportsFeeds } from '../../hooks/useRefreshMySportsFeeds';

interface RefreshMySportsFeedsButtonProps {
  onSuccess?: () => void;
  onError?: () => void;
}

export const RefreshMySportsFeedsButton: React.FC<RefreshMySportsFeedsButtonProps> = ({
  onSuccess,
  onError,
}) => {
  const { isLoading, error, success, result, refresh } = useRefreshMySportsFeeds();
  const [showSuccess, setShowSuccess] = useState(false);
  const [showError, setShowError] = useState(false);

  const handleRefresh = async () => {
    const refreshResult = await refresh();

    if (refreshResult?.success) {
      // After successful data refresh, invalidate Smart Score cache
      // so that fresh calculations use the updated Vegas data
      try {
        await fetch('/api/smart-score/cache/invalidate', {
          method: 'POST',
        });
        
        // Dispatch custom event to trigger Smart Score recalculation
        // SmartScorePage listens to this event and recalculates scores
        window.dispatchEvent(new CustomEvent('dataRefreshComplete', {
          detail: { refreshResult }
        }));
      } catch (cacheError) {
        console.warn('Failed to invalidate Smart Score cache:', cacheError);
        // Don't fail the refresh if cache invalidation fails
      }

      setShowSuccess(true);
      onSuccess?.();
    } else if (error || !refreshResult?.success) {
      setShowError(true);
      onError?.();
    }
  };

  const handleCloseSuccess = (event?: React.SyntheticEvent | Event, reason?: string) => {
    if (reason === 'clickaway') return;
    setShowSuccess(false);
  };

  const handleCloseError = (event?: React.SyntheticEvent | Event, reason?: string) => {
    if (reason === 'clickaway') return;
    setShowError(false);
  };

  // Format duration for display
  const formatDuration = (seconds?: number): string => {
    if (!seconds) return '0s';
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${minutes}m ${secs}s`;
  };

  return (
    <>
      <Button
        variant="contained"
        size="small"
        startIcon={isLoading ? <CircularProgress size={20} /> : <RefreshIcon />}
        onClick={handleRefresh}
        disabled={isLoading}
        sx={{
          px: 3,
          py: 1,
          fontSize: '0.95rem',
          fontWeight: 500,
          textTransform: 'none',
          borderRadius: 2,
          bgcolor: '#ff4500',
          color: '#ffffff',
          '&:hover': {
            bgcolor: '#e03e00',
          },
          '&:disabled': {
            bgcolor: 'rgba(255, 69, 0, 0.5)',
            color: 'rgba(255, 255, 255, 0.7)',
          },
          whiteSpace: 'nowrap',
        }}
      >
        {isLoading ? 'Refreshing...' : 'Refresh Data'}
      </Button>

      {/* Success Toast */}
      <Snackbar
        open={showSuccess}
        autoHideDuration={6000}
        onClose={handleCloseSuccess}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
      >
        <Alert
          onClose={handleCloseSuccess}
          severity="success"
          sx={{
            width: '100%',
            backgroundColor: '#2d5016',
            color: '#ffffff',
            '& .MuiAlert-icon': {
              color: '#4caf50',
            },
          }}
        >
          <AlertTitle sx={{ fontWeight: 600, marginBottom: 1 }}>
            ✅ Data Refresh Complete
          </AlertTitle>

          {result && (
            <Box sx={{ fontSize: '0.85rem', lineHeight: 1.6 }}>
              {/* Duration */}
              {result.duration_seconds && (
                <Box sx={{ marginBottom: 1 }}>
                  Completed in <strong>{formatDuration(result.duration_seconds)}</strong>
                </Box>
              )}

              {/* Statistics */}
              {(result.injuries || result.games || result.team_stats || result.gamelogs || result.espn_opponents) && (
                <Box>
                  <Box sx={{ fontWeight: 600, marginBottom: 0.5 }}>Updates:</Box>
                  <List dense sx={{ paddingY: 0 }}>
                    {result.injuries && (
                      <ListItem sx={{ paddingY: 0, paddingX: 2 }}>
                        <ListItemText
                          primary={`Injuries: ${result.injuries.stored} stored${
                            result.injuries.errors > 0 ? `, ${result.injuries.errors} errors` : ''
                          }`}
                          primaryTypographyProps={{ fontSize: '0.85rem' }}
                        />
                      </ListItem>
                    )}
                    {result.games && (
                      <ListItem sx={{ paddingY: 0, paddingX: 2 }}>
                        <ListItemText
                          primary={`Vegas Lines: ${result.games.stored} stored${
                            result.games.errors > 0 ? `, ${result.games.errors} errors` : ''
                          }`}
                          primaryTypographyProps={{ fontSize: '0.85rem' }}
                        />
                      </ListItem>
                    )}
                    {result.espn_opponents && result.espn_opponents.updated > 0 && (
                      <ListItem sx={{ paddingY: 0, paddingX: 2 }}>
                        <ListItemText
                          primary={`ESPN Opponents: ${result.espn_opponents.updated} updated${
                            result.espn_opponents.errors > 0 ? `, ${result.espn_opponents.errors} errors` : ''
                          }`}
                          primaryTypographyProps={{ fontSize: '0.85rem' }}
                        />
                      </ListItem>
                    )}
                    {result.team_stats && (
                      <ListItem sx={{ paddingY: 0, paddingX: 2 }}>
                        <ListItemText
                          primary={`Defense Stats: ${result.team_stats.stored} stored${
                            result.team_stats.errors > 0 ? `, ${result.team_stats.errors} errors` : ''
                          }`}
                          primaryTypographyProps={{ fontSize: '0.85rem' }}
                        />
                      </ListItem>
                    )}
                    {result.gamelogs && (
                      <ListItem sx={{ paddingY: 0, paddingX: 2 }}>
                        <ListItemText
                          primary={`Game Logs: ${result.gamelogs.stored} stored${
                            result.gamelogs.errors > 0 ? `, ${result.gamelogs.errors} errors` : ''
                          }`}
                          primaryTypographyProps={{ fontSize: '0.85rem' }}
                        />
                      </ListItem>
                    )}
                  </List>
                </Box>
              )}
            </Box>
          )}
        </Alert>
      </Snackbar>

      {/* Error Toast */}
      <Snackbar
        open={showError}
        autoHideDuration={8000}
        onClose={handleCloseError}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
      >
        <Alert
          onClose={handleCloseError}
          severity="error"
          sx={{
            width: '100%',
            backgroundColor: '#5c1414',
            color: '#ffffff',
            '& .MuiAlert-icon': {
              color: '#f44336',
            },
          }}
        >
          <AlertTitle sx={{ fontWeight: 600, marginBottom: 0.5 }}>
            ❌ Refresh Failed
          </AlertTitle>
          <Box sx={{ fontSize: '0.85rem' }}>
            {error || result?.error || 'Unknown error occurred'}
          </Box>
          {result?.message && (
            <Box sx={{ fontSize: '0.8rem', marginTop: 0.5, opacity: 0.9 }}>
              {result.message}
            </Box>
          )}
        </Alert>
      </Snackbar>
    </>
  );
};
