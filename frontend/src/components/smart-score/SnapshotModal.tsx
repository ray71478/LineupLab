/**
 * SnapshotModal Component
 *
 * Modal showing before/after scores with delta indicators and top 10 highlighting.
 * - Displays player name, previous score, new score, delta
 * - Highlights top 10 biggest changes (orange border/background)
 * - Shows all players whose score changed
 * - Keep Changes and Revert buttons
 *
 * Design: Dark theme with orange accents
 */

import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  useTheme,
  useMediaQuery,
  IconButton,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import type { ScoreChange } from '../../types/smartScore.types';

export interface SnapshotModalProps {
  open: boolean;
  changes: ScoreChange[];
  onKeepChanges: () => void;
  onRevert: () => void;
  onClose?: () => void;
}

export const SnapshotModal: React.FC<SnapshotModalProps> = ({
  open,
  changes,
  onKeepChanges,
  onRevert,
  onClose,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const formatDelta = (delta: number): string => {
    const sign = delta >= 0 ? '+' : '';
    return `${sign}${delta.toFixed(2)}`;
  };

  const getDeltaColor = (delta: number): string => {
    if (delta > 0) {
      return 'rgba(76, 175, 80, 0.3)'; // Green for positive
    } else if (delta < 0) {
      return 'rgba(244, 67, 54, 0.3)'; // Red for negative
    }
    return 'transparent';
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      fullScreen={isMobile}
      PaperProps={{
        sx: {
          backgroundColor: '#1a1a2e',
          border: '1px solid rgba(255, 140, 66, 0.2)',
        },
      }}
    >
      <DialogTitle
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          pb: 2,
        }}
      >
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          Score Changes Snapshot
        </Typography>
        {onClose && (
          <IconButton
            onClick={onClose}
            size="small"
            sx={{
              color: 'text.secondary',
              '&:hover': {
                backgroundColor: 'rgba(255, 140, 66, 0.1)',
              },
            }}
          >
            <CloseIcon />
          </IconButton>
        )}
      </DialogTitle>

      <DialogContent sx={{ p: 0 }}>
        {changes.length === 0 ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="body1" sx={{ color: 'text.secondary' }}>
              No score changes detected.
            </Typography>
          </Box>
        ) : (
          <TableContainer sx={{ maxHeight: '60vh' }}>
            <Table stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 600 }}>Player</TableCell>
                  <TableCell sx={{ fontWeight: 600 }} align="right">
                    Previous Score
                  </TableCell>
                  <TableCell sx={{ fontWeight: 600 }} align="right">
                    New Score
                  </TableCell>
                  <TableCell sx={{ fontWeight: 600 }} align="right">
                    Change
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {changes.map((change) => (
                  <TableRow
                    key={change.playerId}
                    sx={{
                      backgroundColor: change.isTopChange
                        ? 'rgba(255, 140, 66, 0.08)'
                        : 'transparent',
                      borderLeft: change.isTopChange
                        ? '3px solid #ff8c42'
                        : 'none',
                      '&:hover': {
                        backgroundColor: change.isTopChange
                          ? 'rgba(255, 140, 66, 0.12)'
                          : 'rgba(255, 255, 255, 0.05)',
                      },
                    }}
                  >
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {change.playerName}
                        {change.isTopChange && (
                          <Chip
                            label="Top 10"
                            size="small"
                            sx={{
                              backgroundColor: '#ff8c42',
                              color: 'white',
                              fontSize: '0.65rem',
                              height: 20,
                            }}
                          />
                        )}
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      {change.previousScore.toFixed(2)}
                    </TableCell>
                    <TableCell align="right">
                      {change.newScore.toFixed(2)}
                    </TableCell>
                    <TableCell align="right">
                      <Box
                        sx={{
                          display: 'inline-block',
                          px: 1.5,
                          py: 0.5,
                          borderRadius: 1,
                          backgroundColor: getDeltaColor(change.delta),
                          fontWeight: 600,
                          color: change.delta >= 0 ? '#4caf50' : '#f44336',
                        }}
                      >
                        {formatDelta(change.delta)}
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </DialogContent>

      <DialogActions
        sx={{
          borderTop: '1px solid rgba(255, 255, 255, 0.1)',
          p: 2,
          gap: 1,
        }}
      >
        <Button
          variant="outlined"
          onClick={onRevert}
          sx={{
            borderColor: 'rgba(255, 255, 255, 0.2)',
            color: 'text.primary',
            '&:hover': {
              borderColor: '#ff8c42',
              backgroundColor: 'rgba(255, 140, 66, 0.08)',
            },
          }}
        >
          Revert
        </Button>
        <Button
          variant="contained"
          onClick={onKeepChanges}
          sx={{
            backgroundColor: '#ff8c42',
            '&:hover': {
              backgroundColor: '#e65a2b',
            },
          }}
        >
          Keep Changes
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default SnapshotModal;

