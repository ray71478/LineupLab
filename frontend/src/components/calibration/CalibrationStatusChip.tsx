/**
 * CalibrationStatusChip Component
 *
 * Displays the calibration status of projection adjustments for the current week.
 * Shows "Projection Calibration: Active" or "Projection Calibration: Not Active"
 * with appropriate color coding (green for active, gray for inactive).
 *
 * Position: Top right of Player Pool screen header (per spec lines 43-49)
 * Click behavior: Opens CalibrationAdmin modal
 * States: Active (green/success) vs Not Active (gray/neutral)
 *
 * Design: Chip/badge component with minimal visual impact
 */

import React from 'react';
import {
  Chip,
  Tooltip,
  CircularProgress,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import RemoveCircleIcon from '@mui/icons-material/RemoveCircle';
import { useCalibrationStatus } from '../../hooks/useCalibration';

export interface CalibrationStatusChipProps {
  weekId: number | null;
  onClick?: () => void;
  compact?: boolean;
}

/**
 * CalibrationStatusChip Component
 *
 * Displays calibration status with color-coded chip.
 * Integrates with useCalibrationStatus hook for real-time data.
 */
export const CalibrationStatusChip: React.FC<CalibrationStatusChipProps> = ({
  weekId,
  onClick,
  compact = false,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const { data, isLoading, error } = useCalibrationStatus(weekId);

  // Show loading state
  if (isLoading || weekId === null) {
    return (
      <Chip
        size={compact || isMobile ? 'small' : 'medium'}
        icon={<CircularProgress size={16} sx={{ color: '#9e9e9e' }} />}
        label={compact || isMobile ? 'Calibration' : 'Projection Calibration'}
        sx={{
          backgroundColor: 'rgba(158, 158, 158, 0.1)',
          color: '#9e9e9e',
          border: '1px solid rgba(158, 158, 158, 0.3)',
          cursor: onClick ? 'pointer' : 'default',
          '&:hover': onClick
            ? {
                backgroundColor: 'rgba(158, 158, 158, 0.2)',
              }
            : {},
        }}
        onClick={onClick}
      />
    );
  }

  // Show error state
  if (error) {
    return (
      <Tooltip title={`Error: ${error.message}`}>
        <Chip
          size={compact || isMobile ? 'small' : 'medium'}
          icon={<RemoveCircleIcon />}
          label={compact || isMobile ? 'Error' : 'Calibration Error'}
          sx={{
            backgroundColor: 'rgba(255, 152, 0, 0.1)',
            color: '#ff9800',
            border: '1px solid rgba(255, 152, 0, 0.3)',
            cursor: onClick ? 'pointer' : 'default',
            '&:hover': onClick
              ? {
                  backgroundColor: 'rgba(255, 152, 0, 0.2)',
                }
              : {},
          }}
          onClick={onClick}
        />
      </Tooltip>
    );
  }

  // Determine status
  const isActive = data?.is_active ?? false;
  const positionsConfigured = data?.positions_configured ?? 0;
  const totalPositions = data?.total_positions ?? 6;

  // Status text and color
  const statusText = isActive ? 'Active' : 'Not Active';
  const fullLabel = compact || isMobile ? statusText : `Projection Calibration: ${statusText}`;

  // Tooltip content
  const tooltipContent = isActive
    ? `Calibration is active for ${positionsConfigured}/${totalPositions} positions. Click to manage calibration settings.`
    : 'Calibration is not active. Click to configure calibration settings.';

  // Color scheme
  const activeColor = '#4caf50'; // Green
  const inactiveColor = '#9e9e9e'; // Gray

  const chipColor = isActive ? activeColor : inactiveColor;
  const Icon = isActive ? CheckCircleIcon : RemoveCircleIcon;

  return (
    <Tooltip title={tooltipContent} arrow placement="bottom">
      <Chip
        data-testid="calibration-status-chip"
        size={compact || isMobile ? 'small' : 'medium'}
        icon={<Icon sx={{ fontSize: 18 }} />}
        label={fullLabel}
        sx={{
          backgroundColor: `rgba(${isActive ? '76, 175, 80' : '158, 158, 158'}, 0.1)`,
          color: chipColor,
          border: `1px solid rgba(${isActive ? '76, 175, 80' : '158, 158, 158'}, 0.3)`,
          fontWeight: 500,
          cursor: onClick ? 'pointer' : 'default',
          transition: 'all 0.2s ease-in-out',
          '&:hover': onClick
            ? {
                backgroundColor: `rgba(${isActive ? '76, 175, 80' : '158, 158, 158'}, 0.2)`,
                transform: 'scale(1.02)',
                boxShadow: `0 2px 8px rgba(${isActive ? '76, 175, 80' : '158, 158, 158'}, 0.3)`,
              }
            : {},
        }}
        onClick={onClick}
      />
    </Tooltip>
  );
};

export default CalibrationStatusChip;
