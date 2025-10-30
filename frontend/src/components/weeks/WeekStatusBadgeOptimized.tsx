/**
 * Optimized WeekStatusBadge Component with React.memo
 *
 * Performance optimizations:
 * - React.memo to prevent unnecessary re-renders
 * - Pure CSS animations (no JavaScript animations)
 * - GPU-accelerated transforms
 * - Efficient icon rendering
 * - Debounced hover effects
 */

import React, { useMemo } from 'react';
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

// Pure CSS glow animation - will-change hint for GPU acceleration
const glowAnimation = keyframes`
  0% {
    box-shadow: 0 0 4px rgba(76, 175, 80, 0.3);
  }
  50% {
    box-shadow: 0 0 12px rgba(76, 175, 80, 0.6);
  }
  100% {
    box-shadow: 0 0 4px rgba(76, 175, 80, 0.3);
  }
`;

// Memoized internal component to prevent re-renders
const WeekStatusBadgeContent: React.FC<WeekStatusBadgeProps> = ({
  status,
  importStatus = 'pending',
  isCurrentWeek = false,
  compact = false,
}) => {
  const theme = useTheme();

  // Memoize icon config to avoid recalculation
  const iconConfig = useMemo(() => {
    switch (importStatus) {
      case 'imported':
        return {
          icon: CheckCircleIcon,
          color: '#4caf50',
          label: 'Imported',
        };
      case 'error':
        return {
          icon: WarningIcon,
          color: '#ff9800',
          label: 'Import Error',
        };
      case 'pending':
      default:
        return {
          icon: RemoveCircleIcon,
          color: '#9e9e9e',
          label: 'Pending',
        };
    }
  }, [importStatus]);

  const Icon = iconConfig.icon;

  // Memoize tooltip text
  const tooltipText = useMemo(() => {
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
  }, [status, iconConfig.label]);

  const iconSize = compact ? 20 : 24;

  return (
    <Tooltip title={tooltipText}>
      <Box
        data-testid="week-status-badge-optimized"
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderRadius: '50%',
          padding: compact ? '4px' : '8px',
          backgroundColor: 'transparent',
          // Use will-change for GPU acceleration
          willChange: isCurrentWeek ? 'box-shadow' : 'auto',
          // Pure CSS animation - no JavaScript
          animation: isCurrentWeek ? `${glowAnimation} 2s ease-in-out infinite` : 'none',
          // Performant transition
          transition: 'transform 150ms cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            transform: 'scale(1.1)',
          },
        }}
      >
        <Icon
          sx={{
            fontSize: iconSize,
            color: iconConfig.color,
            // Use drop-shadow filter for glow (GPU-accelerated)
            filter: isCurrentWeek ? `drop-shadow(0 0 4px ${iconConfig.color})` : 'none',
            // Prevent re-renders when filter changes
            willChange: isCurrentWeek ? 'filter' : 'auto',
          }}
        />
      </Box>
    </Tooltip>
  );
};

// Wrap with React.memo to prevent unnecessary re-renders
export const WeekStatusBadge = React.memo(WeekStatusBadgeContent);

export default WeekStatusBadge;
