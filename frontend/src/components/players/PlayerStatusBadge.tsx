/**
 * PlayerStatusBadge Component
 *
 * Displays matched/unmatched status badge for players in table.
 * Green for matched, orange/red for unmatched.
 */

import React from 'react';
import { Chip, ChipProps } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import WarningIcon from '@mui/icons-material/Warning';

export interface PlayerStatusBadgeProps {
  status: 'matched' | 'unmatched';
  size?: 'small' | 'medium';
}

export const PlayerStatusBadge: React.FC<PlayerStatusBadgeProps> = ({
  status,
  size = 'small',
}) => {
  const isMatched = status === 'matched';

  const chipProps: ChipProps = {
    size: size === 'small' ? 'small' : 'medium',
    icon: isMatched ? <CheckCircleIcon /> : <WarningIcon />,
    label: isMatched ? 'Matched' : 'Unmatched',
    variant: 'outlined',
    sx: {
      backgroundColor: isMatched ? 'rgba(76, 175, 80, 0.1)' : 'rgba(255, 87, 34, 0.1)',
      borderColor: isMatched ? '#4caf50' : '#ff5722',
      color: isMatched ? '#4caf50' : '#ff5722',
      fontWeight: 500,
      fontSize: size === 'small' ? '0.75rem' : '0.875rem',
      '& .MuiChip-icon': {
        fontSize: size === 'small' ? '1rem' : '1.25rem',
        color: 'inherit',
      },
    },
  };

  return <Chip {...chipProps} />;
};

export default PlayerStatusBadge;
