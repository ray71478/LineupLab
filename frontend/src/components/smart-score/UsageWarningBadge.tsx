/**
 * UsageWarningBadge Component
 *
 * Displays warnings for players with declining usage patterns.
 */

import React from 'react';
import { Box, Tooltip, Chip } from '@mui/material';
import WarningIcon from '@mui/icons-material/Warning';

export interface UsageWarningBadgeProps {
  warnings?: string[] | null;
}

export const UsageWarningBadge: React.FC<UsageWarningBadgeProps> = ({
  warnings,
}) => {
  if (!warnings || warnings.length === 0) {
    return null;
  }

  return (
    <Tooltip title={warnings.join(', ')} arrow>
      <Chip
        icon={<WarningIcon sx={{ fontSize: '0.875rem !important' }} />}
        label={`${warnings.length}`}
        size="small"
        sx={{
          height: 20,
          fontSize: '0.7rem',
          backgroundColor: 'rgba(255, 152, 0, 0.15)',
          color: '#ff9800',
          border: '1px solid rgba(255, 152, 0, 0.3)',
          '& .MuiChip-icon': {
            marginLeft: '4px',
          },
        }}
      />
    </Tooltip>
  );
};

export default UsageWarningBadge;

