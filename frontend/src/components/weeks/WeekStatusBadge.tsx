/**
 * WeekStatusBadge Component
 *
 * Displays the status of a week (completed, pending, active) with appropriate icons.
 * Shows import status via badge color/icon.
 * Applies glow effect for the current active week.
 * Dark mode optimized with Material Design icons.
 */

import React from 'react';
import {
  Box,
  Tooltip,
  useTheme,
  keyframes,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import RemoveCircleIcon from '@mui/icons-material/RemoveCircle';
import WarningIcon from '@mui/icons-material/Warning';

export interface WeekStatusBadgeProps {
  status: 'active' | 'upcoming' | 'completed';
  importStatus?: 'pending' | 'imported' | 'error';
  isCurrentWeek?: boolean;
  compact?: boolean;
}

// Glow animation for active weeks
const glowAnimation = keyframes`
  0% {
    box-shadow: 0 0 4px rgba(255, 69, 0, 0.3);
  }
  50% {
    box-shadow: 0 0 12px rgba(255, 69, 0, 0.6);
  }
  100% {
    box-shadow: 0 0 4px rgba(255, 69, 0, 0.3);
  }
`;

export const WeekStatusBadge: React.FC<WeekStatusBadgeProps> = ({
  status,
  importStatus = 'pending',
  isCurrentWeek = false,
  compact = false,
}) => {
  const theme = useTheme();

  // Determine icon and color based on import status
  const getIconConfig = () => {
    switch (importStatus) {
      case 'imported':
        return {
          icon: CheckCircleIcon,
          color: '#ff4500', // Orange
          label: 'Imported',
        };
      case 'error':
        return {
          icon: WarningIcon,
          color: '#ff9800', // Material Orange
          label: 'Import Error',
        };
      case 'pending':
      default:
        return {
          icon: RemoveCircleIcon,
          color: '#9e9e9e', // Material Gray
          label: 'Pending',
        };
    }
  };

  const iconConfig = getIconConfig();
  const Icon = iconConfig.icon;

  // Determine tooltip text based on status
  const getTooltipText = () => {
    let statusText = '';
    switch (status) {
      case 'active':
        statusText = 'Current Week';
        break;
      case 'upcoming':
        statusText = 'Upcoming Week';
        break;
      case 'completed':
        statusText = 'Completed Week';
        break;
    }

    return `${statusText} - ${iconConfig.label}`;
  };

  const iconSize = compact ? 20 : 24;

  return (
    <Tooltip title={getTooltipText()}>
      <Box
        data-testid="week-status-badge"
        className={`
          week-status-badge
          ${importStatus === 'imported' ? 'completed-badge' : ''}
          ${importStatus === 'pending' ? 'pending-badge' : ''}
          ${importStatus === 'error' ? 'error-badge' : ''}
          ${isCurrentWeek ? 'glow-effect' : ''}
        `}
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderRadius: '50%',
          padding: compact ? '4px' : '8px',
          backgroundColor: 'transparent',
          transition: 'all 0.2s ease-in-out',
          animation: isCurrentWeek ? `${glowAnimation} 2s ease-in-out infinite` : 'none',
          '&:hover': {
            transform: 'scale(1.1)',
          },
        }}
      >
        <Icon
          sx={{
            fontSize: iconSize,
            color: iconConfig.color,
            filter: isCurrentWeek ? `drop-shadow(0 0 4px ${iconConfig.color})` : 'none',
          }}
        />
      </Box>
    </Tooltip>
  );
};

export default WeekStatusBadge;
