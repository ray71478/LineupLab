/**
 * PlayerTableRow Component
 *
 * Individual table row with expand toggle and expanded details display.
 * Handles unmatched player styling with orange border highlight.
 *
 * Mobile Optimizations:
 * - Touch targets >= 44x44px
 * - Larger expand button on mobile
 * - Responsive padding and font sizes
 */

import React from 'react';
import {
  TableRow,
  TableCell,
  Box,
  Collapse,
  IconButton,
  Typography,
  Stack,
} from '@mui/material';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import PlayerStatusBadge from './PlayerStatusBadge';

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

export interface PlayerTableRowProps {
  player: PlayerData;
  isExpanded: boolean;
  onToggleExpand: (playerId: number) => void;
  isMobile?: boolean;
}

export const PlayerTableRow: React.FC<PlayerTableRowProps> = ({
  player,
  isExpanded,
  onToggleExpand,
  isMobile = false,
}) => {
  const isUnmatched = player.status === 'unmatched';

  return (
    <>
      {/* Main Row */}
      <TableRow
        sx={{
          backgroundColor: isUnmatched ? 'rgba(255, 87, 34, 0.05)' : 'transparent',
          borderLeft: isUnmatched ? '4px solid #ff5722' : '4px solid transparent',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            backgroundColor: isUnmatched
              ? 'rgba(255, 87, 34, 0.1)'
              : 'rgba(255, 140, 66, 0.05)',
          },
        }}
      >
        {/* Expand Toggle - Touch target >= 44x44px */}
        <TableCell
          align="center"
          sx={{
            width: isMobile ? '50px' : '48px',
            padding: isMobile ? '8px 4px' : '12px 4px',
            verticalAlign: 'middle',
          }}
        >
          <IconButton
            size={isMobile ? 'medium' : 'small'}
            onClick={() => onToggleExpand(player.id)}
            aria-label={isExpanded ? 'Collapse row' : 'Expand row'}
            sx={{
              color: '#ff8c42',
              width: isMobile ? '44px' : 'auto',
              height: isMobile ? '44px' : 'auto',
              '&:hover': {
                backgroundColor: 'rgba(255, 140, 66, 0.1)',
              },
              // Ensure clickable area on mobile
              minWidth: isMobile ? '44px' : 'auto',
              minHeight: isMobile ? '44px' : 'auto',
            }}
          >
            {isExpanded ? (
              <KeyboardArrowUpIcon fontSize={isMobile ? 'medium' : 'small'} />
            ) : (
              <KeyboardArrowDownIcon fontSize={isMobile ? 'medium' : 'small'} />
            )}
          </IconButton>
        </TableCell>

        {/* Player Name */}
        <TableCell
          sx={{
            color: '#ffffff',
            fontWeight: 500,
            fontSize: isMobile ? '0.8rem' : '0.95rem',
            padding: isMobile ? '10px 8px' : '12px 16px',
            wordBreak: 'break-word',
            maxWidth: isMobile ? '150px' : 'auto',
          }}
        >
          {player.name}
        </TableCell>

        {/* Team */}
        <TableCell
          align="center"
          sx={{
            color: '#e5e7eb',
            fontSize: isMobile ? '0.8rem' : '0.9rem',
            padding: isMobile ? '10px 6px' : '12px 16px',
            fontWeight: 500,
          }}
        >
          {player.team}
        </TableCell>

        {/* Position */}
        <TableCell
          align="center"
          sx={{
            color: '#e5e7eb',
            fontSize: isMobile ? '0.8rem' : '0.9rem',
            padding: isMobile ? '10px 6px' : '12px 16px',
            fontWeight: 500,
          }}
        >
          {player.position}
        </TableCell>

        {/* Salary */}
        <TableCell
          align="right"
          sx={{
            color: '#e5e7eb',
            fontSize: isMobile ? '0.8rem' : '0.9rem',
            padding: isMobile ? '10px 6px' : '12px 16px',
            fontWeight: 500,
          }}
        >
          ${player.salary.toLocaleString()}
        </TableCell>

        {/* Projection - hidden on mobile */}
        {!isMobile && (
          <TableCell
            align="right"
            sx={{
              color: '#e5e7eb',
              fontSize: '0.9rem',
              padding: '12px 16px',
              fontWeight: 500,
            }}
          >
            {player.projection?.toFixed(1) ?? '-'}
          </TableCell>
        )}

        {/* Ownership - hidden on mobile */}
        {!isMobile && (
          <TableCell
            align="right"
            sx={{
              color: '#e5e7eb',
              fontSize: '0.9rem',
              padding: '12px 16px',
              fontWeight: 500,
            }}
          >
            {player.ownership !== undefined
              ? `${(player.ownership * 100).toFixed(1)}%`
              : '-'}
          </TableCell>
        )}

        {/* Status Badge */}
        <TableCell
          align="center"
          sx={{
            padding: isMobile ? '10px 6px' : '12px 8px',
          }}
        >
          <PlayerStatusBadge status={player.status} size="small" />
        </TableCell>
      </TableRow>

      {/* Expanded Row */}
      <TableRow
        sx={{
          backgroundColor: 'transparent',
        }}
      >
        <TableCell
          colSpan={isMobile ? 6 : 8}
          sx={{
            padding: 0,
            borderBottom: isExpanded ? '1px solid rgba(255, 255, 255, 0.1)' : 'none',
          }}
        >
          <Collapse in={isExpanded} timeout="auto" unmountOnExit>
            <Box
              sx={{
                padding: isMobile ? '16px 12px' : '20px',
                backgroundColor: 'rgba(255, 140, 66, 0.05)',
              }}
            >
              <Stack spacing={isMobile ? 1.5 : 2}>
                {/* Expanded Details Grid - responsive */}
                <Box
                  sx={{
                    display: 'grid',
                    gridTemplateColumns: isMobile
                      ? 'repeat(auto-fit, minmax(150px, 1fr))'
                      : 'repeat(auto-fit, minmax(200px, 1fr))',
                    gap: isMobile ? '12px' : '16px',
                  }}
                >
                  {/* Ceiling */}
                  {player.ceiling !== undefined && (
                    <Box>
                      <Typography
                        variant="caption"
                        sx={{
                          color: '#9ca3af',
                          fontSize: isMobile ? '0.7rem' : '0.75rem',
                          fontWeight: 600,
                          textTransform: 'uppercase',
                          letterSpacing: '0.5px',
                        }}
                      >
                        Ceiling
                      </Typography>
                      <Typography
                        variant="body2"
                        sx={{
                          color: '#ffffff',
                          fontSize: isMobile ? '0.95rem' : '1.1rem',
                          fontWeight: 600,
                          marginTop: '4px',
                        }}
                      >
                        {player.ceiling.toFixed(2)}
                      </Typography>
                    </Box>
                  )}

                  {/* Floor */}
                  {player.floor !== undefined && (
                    <Box>
                      <Typography
                        variant="caption"
                        sx={{
                          color: '#9ca3af',
                          fontSize: isMobile ? '0.7rem' : '0.75rem',
                          fontWeight: 600,
                          textTransform: 'uppercase',
                          letterSpacing: '0.5px',
                        }}
                      >
                        Floor
                      </Typography>
                      <Typography
                        variant="body2"
                        sx={{
                          color: '#ffffff',
                          fontSize: isMobile ? '0.95rem' : '1.1rem',
                          fontWeight: 600,
                          marginTop: '4px',
                        }}
                      >
                        {player.floor.toFixed(2)}
                      </Typography>
                    </Box>
                  )}

                  {/* Source */}
                  {player.source && (
                    <Box>
                      <Typography
                        variant="caption"
                        sx={{
                          color: '#9ca3af',
                          fontSize: isMobile ? '0.7rem' : '0.75rem',
                          fontWeight: 600,
                          textTransform: 'uppercase',
                          letterSpacing: '0.5px',
                        }}
                      >
                        Source
                      </Typography>
                      <Typography
                        variant="body2"
                        sx={{
                          color: '#ffffff',
                          fontSize: isMobile ? '0.9rem' : '1rem',
                          marginTop: '4px',
                        }}
                      >
                        {player.source}
                      </Typography>
                    </Box>
                  )}

                  {/* Last Updated */}
                  {player.uploaded_at && (
                    <Box>
                      <Typography
                        variant="caption"
                        sx={{
                          color: '#9ca3af',
                          fontSize: isMobile ? '0.7rem' : '0.75rem',
                          fontWeight: 600,
                          textTransform: 'uppercase',
                          letterSpacing: '0.5px',
                        }}
                      >
                        Last Updated
                      </Typography>
                      <Typography
                        variant="body2"
                        sx={{
                          color: '#ffffff',
                          fontSize: isMobile ? '0.8rem' : '0.9rem',
                          marginTop: '4px',
                        }}
                      >
                        {new Date(player.uploaded_at).toLocaleDateString()}
                      </Typography>
                    </Box>
                  )}
                </Box>

                {/* Notes */}
                {player.notes && (
                  <Box>
                    <Typography
                      variant="caption"
                      sx={{
                        color: '#9ca3af',
                        fontSize: isMobile ? '0.7rem' : '0.75rem',
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px',
                      }}
                    >
                      Notes
                    </Typography>
                    <Typography
                      variant="body2"
                      sx={{
                        color: '#e5e7eb',
                        fontSize: isMobile ? '0.8rem' : '0.9rem',
                        marginTop: '8px',
                        fontStyle: 'italic',
                      }}
                    >
                      {player.notes}
                    </Typography>
                  </Box>
                )}
              </Stack>
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  );
};

export default PlayerTableRow;
