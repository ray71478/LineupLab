/**
 * SnapshotModal Component
 *
 * Modal showing before/after scores with delta indicators and top 10 highlighting.
 * - Displays player name, previous score, new score, delta
 * - Highlights top 10 biggest changes (orange border/background)
 * - Shows factor-level breakdowns (what caused the change)
 * - Shows player context (ownership, etc.)
 * - Keep Changes and Revert buttons
 *
 * Design: Dark theme with orange accents (#000000/#0a0a0a, #ff6b35)
 */

import React, { useState } from 'react';
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
  Chip,
  useTheme,
  useMediaQuery,
  IconButton,
  Collapse,
  Stack,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import type { ScoreChange } from '../../types/smartScore.types';

const FACTOR_LABELS: Record<string, string> = {
  W1: 'Projection',
  W2: 'Ceiling Factor',
  W3: 'Ownership Penalty',
  W4: 'Value Score',
  W5: 'Trend Adjustment',
  W6: 'Regression Penalty',
  W7: 'Vegas Context',
  W8: 'Matchup Adjustment',
};

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
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());

  const toggleRowExpansion = (playerId: number) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(playerId)) {
      newExpanded.delete(playerId);
    } else {
      newExpanded.add(playerId);
    }
    setExpandedRows(newExpanded);
  };

  const formatDelta = (delta: number): string => {
    const sign = delta >= 0 ? '+' : '';
    return `${sign}${delta.toFixed(2)}`;
  };

  const getDeltaColor = (delta: number): string => {
    if (delta > 0) {
      return '#4caf50'; // Green for positive
    } else if (delta < 0) {
      return '#f44336'; // Red for negative
    }
    return '#a0a0a0';
  };

  const getDeltaBgColor = (delta: number): string => {
    if (delta > 0) {
      return 'rgba(76, 175, 80, 0.15)'; // Green for positive
    } else if (delta < 0) {
      return 'rgba(244, 67, 54, 0.15)'; // Red for negative
    }
    return 'transparent';
  };

  const getTopContributingFactors = (change: ScoreChange): Array<{ factor: string; delta: number }> => {
    if (!change.factorChanges) return [];
    
    const factors = Object.entries(change.factorChanges)
      .map(([factor, data]) => ({
        factor,
        delta: data.delta,
        absDelta: Math.abs(data.delta),
      }))
      .sort((a, b) => b.absDelta - a.absDelta);
    
    return factors.slice(0, 3); // Top 3 contributing factors
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
          backgroundColor: '#0a0a0a',
          border: '1px solid rgba(255, 107, 53, 0.2)',
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
          backgroundColor: '#000000',
        }}
      >
        <Typography variant="h6" sx={{ fontWeight: 600, color: '#ffffff' }}>
          Score Changes Snapshot
        </Typography>
        {onClose && (
          <IconButton
            onClick={onClose}
            size="small"
            sx={{
              color: '#a0a0a0',
              '&:hover': {
                backgroundColor: 'rgba(255, 107, 53, 0.1)',
                color: '#ff6b35',
              },
            }}
          >
            <CloseIcon />
          </IconButton>
        )}
      </DialogTitle>

      <DialogContent sx={{ p: 0, backgroundColor: '#0a0a0a' }}>
        {changes.length === 0 ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="body1" sx={{ color: '#a0a0a0' }}>
              No score changes detected.
            </Typography>
          </Box>
        ) : (
          <TableContainer sx={{ maxHeight: '60vh' }}>
            <Table stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 600, backgroundColor: '#000000', color: '#ffffff', borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
                    Player
                  </TableCell>
                  <TableCell sx={{ fontWeight: 600, backgroundColor: '#000000', color: '#ffffff', borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }} align="right">
                    Previous Score
                  </TableCell>
                  <TableCell sx={{ fontWeight: 600, backgroundColor: '#000000', color: '#ffffff', borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }} align="right">
                    New Score
                  </TableCell>
                  <TableCell sx={{ fontWeight: 600, backgroundColor: '#000000', color: '#ffffff', borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }} align="right">
                    Change
                  </TableCell>
                  <TableCell sx={{ fontWeight: 600, backgroundColor: '#000000', color: '#ffffff', borderBottom: '1px solid rgba(255, 255, 255, 0.1)', width: 50 }} />
                </TableRow>
              </TableHead>
              <TableBody>
                {changes.map((change) => {
                  const isExpanded = expandedRows.has(change.playerId);
                  const topFactors = getTopContributingFactors(change);
                  const hasFactorChanges = change.factorChanges && Object.keys(change.factorChanges).length > 0;

                  return (
                    <React.Fragment key={change.playerId}>
                      <TableRow
                        sx={{
                          backgroundColor: change.isTopChange
                            ? 'rgba(255, 107, 53, 0.08)'
                            : 'transparent',
                          borderLeft: change.isTopChange
                            ? '3px solid #ff6b35'
                            : 'none',
                          '&:hover': {
                            backgroundColor: change.isTopChange
                              ? 'rgba(255, 107, 53, 0.12)'
                              : 'rgba(255, 255, 255, 0.03)',
                          },
                        }}
                      >
                        <TableCell sx={{ color: '#ffffff', borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            {change.playerName}
                            {change.isTopChange && (
                              <Chip
                                label="Top 10"
                                size="small"
                                sx={{
                                  backgroundColor: '#ff6b35',
                                  color: '#ffffff',
                                  fontSize: '0.65rem',
                                  height: 20,
                                  fontWeight: 600,
                                }}
                              />
                            )}
                            {hasFactorChanges && (
                              <Chip
                                label={`${Object.keys(change.factorChanges!).length} factors`}
                                size="small"
                                sx={{
                                  backgroundColor: 'rgba(255, 107, 53, 0.2)',
                                  color: '#ff6b35',
                                  fontSize: '0.65rem',
                                  height: 20,
                                  border: '1px solid rgba(255, 107, 53, 0.3)',
                                }}
                              />
                            )}
                          </Box>
                          {change.playerData?.ownership !== null && change.playerData?.ownership !== undefined && (
                            <Typography variant="caption" sx={{ color: '#a0a0a0', fontSize: '0.7rem', display: 'block', mt: 0.5 }}>
                              Ownership: {change.playerData.ownership.toFixed(1)}%
                            </Typography>
                          )}
                        </TableCell>
                        <TableCell align="right" sx={{ color: '#ffffff', borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                          {change.previousScore.toFixed(2)}
                        </TableCell>
                        <TableCell align="right" sx={{ color: '#ffffff', borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                          {change.newScore.toFixed(2)}
                        </TableCell>
                        <TableCell align="right" sx={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                          <Box
                            sx={{
                              display: 'inline-block',
                              px: 1.5,
                              py: 0.5,
                              borderRadius: 1,
                              backgroundColor: getDeltaBgColor(change.delta),
                              fontWeight: 600,
                              color: getDeltaColor(change.delta),
                              fontSize: '0.85rem',
                            }}
                          >
                            {formatDelta(change.delta)}
                          </Box>
                        </TableCell>
                        <TableCell sx={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                          {hasFactorChanges && (
                            <IconButton
                              size="small"
                              onClick={() => toggleRowExpansion(change.playerId)}
                              sx={{
                                color: '#ff6b35',
                                padding: '4px',
                                '&:hover': {
                                  backgroundColor: 'rgba(255, 107, 53, 0.1)',
                                },
                              }}
                            >
                              {isExpanded ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
                            </IconButton>
                          )}
                        </TableCell>
                      </TableRow>
                      {hasFactorChanges && (
                        <TableRow>
                          <TableCell colSpan={5} sx={{ p: 0, borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                            <Collapse in={isExpanded}>
                              <Box sx={{ p: 2, backgroundColor: 'rgba(0, 0, 0, 0.3)' }}>
                                <Typography variant="caption" sx={{ color: '#ff6b35', fontWeight: 600, fontSize: '0.75rem', mb: 1.5, display: 'block' }}>
                                  Factor Breakdown
                                </Typography>
                                {topFactors.length > 0 && (
                                  <Box sx={{ mb: 2 }}>
                                    <Typography variant="caption" sx={{ color: '#a0a0a0', fontSize: '0.7rem', mb: 1, display: 'block' }}>
                                      Top Contributing Factors:
                                    </Typography>
                                    <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mb: 2 }}>
                                      {topFactors.map(({ factor, delta }) => (
                                        <Chip
                                          key={factor}
                                          label={`${FACTOR_LABELS[factor]}: ${formatDelta(delta)}`}
                                          size="small"
                                          sx={{
                                            backgroundColor: delta < 0 ? 'rgba(244, 67, 54, 0.15)' : 'rgba(76, 175, 80, 0.15)',
                                            color: delta < 0 ? '#f44336' : '#4caf50',
                                            fontSize: '0.7rem',
                                            height: 22,
                                            fontWeight: 500,
                                          }}
                                        />
                                      ))}
                                    </Stack>
                                  </Box>
                                )}
                                <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 1.5 }}>
                                  {Object.entries(change.factorChanges!).map(([factor, data]) => (
                                    <Box
                                      key={factor}
                                      sx={{
                                        p: 1,
                                        borderRadius: 1,
                                        backgroundColor: 'rgba(255, 255, 255, 0.02)',
                                        border: '1px solid rgba(255, 255, 255, 0.05)',
                                      }}
                                    >
                                      <Typography variant="caption" sx={{ color: '#a0a0a0', fontSize: '0.7rem', display: 'block' }}>
                                        {FACTOR_LABELS[factor]}
                                      </Typography>
                                      <Typography variant="body2" sx={{ color: '#ffffff', fontSize: '0.75rem', fontWeight: 500 }}>
                                        {data.previous.toFixed(2)} → {data.current.toFixed(2)}
                                      </Typography>
                                      <Typography
                                        variant="caption"
                                        sx={{
                                          color: data.delta < 0 ? '#f44336' : '#4caf50',
                                          fontSize: '0.7rem',
                                          fontWeight: 600,
                                        }}
                                      >
                                        {formatDelta(data.delta)}
                                      </Typography>
                                    </Box>
                                  ))}
                                </Box>
                              </Box>
                            </Collapse>
                          </TableCell>
                        </TableRow>
                      )}
                    </React.Fragment>
                  );
                })}
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
          backgroundColor: '#000000',
        }}
      >
        <Button
          variant="outlined"
          onClick={onRevert}
          sx={{
            borderColor: 'rgba(255, 255, 255, 0.2)',
            color: '#ffffff',
            '&:hover': {
              borderColor: '#ff6b35',
              backgroundColor: 'rgba(255, 107, 53, 0.08)',
            },
          }}
        >
          Revert
        </Button>
        <Button
          variant="contained"
          onClick={onKeepChanges}
          sx={{
            backgroundColor: '#ff6b35',
            color: '#ffffff',
            '&:hover': {
              backgroundColor: '#e55a25',
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

