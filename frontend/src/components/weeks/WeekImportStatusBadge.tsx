/**
 * WeekImportStatusBadge Component
 *
 * Displays import status with visual indicators:
 * - Imported: Green checkmark with player count
 * - Pending: Gray dash
 * - Error: Orange warning with error message in tooltip
 *
 * Shows import timestamp when available.
 * Dark mode optimized.
 */

import React from 'react';
import {
  Box,
  Chip,
  Tooltip,
  Typography,
  Stack,
  useTheme,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import RemoveCircleIcon from '@mui/icons-material/RemoveCircle';
import WarningIcon from '@mui/icons-material/Warning';

export interface WeekImportStatusBadgeProps {
  importStatus: 'pending' | 'imported' | 'error';
  importCount?: number;
  importTimestamp?: string | null;
  errorMessage?: string | null;
}

export const WeekImportStatusBadge: React.FC<WeekImportStatusBadgeProps> = ({
  importStatus,
  importCount = 0,
  importTimestamp = null,
  errorMessage = null,
}) => {
  const theme = useTheme();

  // Get status configuration
  const getStatusConfig = () => {
    switch (importStatus) {
      case 'imported':
        return {
          icon: CheckCircleIcon,
          color: '#4caf50',
          backgroundColor: 'rgba(76, 175, 80, 0.1)',
          label: 'Imported',
          textColor: '#4caf50',
        };
      case 'error':
        return {
          icon: WarningIcon,
          color: '#ff9800',
          backgroundColor: 'rgba(255, 152, 0, 0.1)',
          label: 'Error',
          textColor: '#ff9800',
        };
      case 'pending':
      default:
        return {
          icon: RemoveCircleIcon,
          color: '#9e9e9e',
          backgroundColor: 'rgba(158, 158, 158, 0.1)',
          label: 'Pending',
          textColor: '#9e9e9e',
        };
    }
  };

  const statusConfig = getStatusConfig();
  const Icon = statusConfig.icon;

  // Format import timestamp
  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return timestamp;
    }
  };

  // Build tooltip content
  const getTooltipContent = () => {
    let content = statusConfig.label;

    if (importStatus === 'imported' && importTimestamp) {
      content += ` - ${formatTimestamp(importTimestamp)}`;
      if (importCount > 0) {
        content += ` (${importCount} players)`;
      }
    } else if (importStatus === 'error' && errorMessage) {
      content = `Import Error: ${errorMessage}`;
    }

    return content;
  };

  const tooltipText = getTooltipContent();

  return (
    <Tooltip title={tooltipText}>
      <Chip
        data-testid="import-status-badge"
        title={tooltipText}
        icon={<Icon />}
        label={
          importStatus === 'imported' && importCount > 0
            ? `${statusConfig.label} (${importCount})`
            : statusConfig.label
        }
        size="small"
        sx={{
          backgroundColor: statusConfig.backgroundColor,
          color: statusConfig.textColor,
          borderColor: statusConfig.color,
          border: `1px solid ${statusConfig.color}`,
          fontWeight: 500,
          fontSize: '0.75rem',
          '& .MuiChip-icon': {
            color: statusConfig.textColor,
            marginLeft: '4px',
          },
          '& .MuiChip-label': {
            paddingLeft: '4px',
            paddingRight: '8px',
          },
        }}
      />
    </Tooltip>
  );
};

export default WeekImportStatusBadge;
