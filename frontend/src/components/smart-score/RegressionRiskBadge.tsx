/**
 * RegressionRiskBadge Component
 *
 * Badge component to display regression risk indicator for WR players.
 * - Displays badge only for WR position
 * - Shows badge when regression_risk = true
 * - Styled with orange/red color (#ff5722)
 * - Tooltip explains risk
 * - Handles missing data gracefully
 *
 * Design: Dark theme with orange/red accent
 */

import React from 'react';
import { Box, Tooltip } from '@mui/material';

export interface RegressionRiskBadgeProps {
  regressionRisk: boolean;
  position: string;
  hasHistoricalData?: boolean;
}

export const RegressionRiskBadge: React.FC<RegressionRiskBadgeProps> = ({
  regressionRisk,
  position,
  hasHistoricalData = true,
}) => {
  // Only show for WR position
  if (position !== 'WR') {
    return null;
  }

  // Handle missing historical data
  if (!hasHistoricalData) {
    return (
      <Tooltip title="Historical data unavailable">
        <Box
          sx={{
            display: 'inline-block',
            px: 1,
            py: 0.5,
            backgroundColor: 'rgba(128, 128, 128, 0.3)',
            borderRadius: 1,
            fontSize: '0.75rem',
            color: 'rgba(255, 255, 255, 0.6)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
          }}
        >
          N/A
        </Box>
      </Tooltip>
    );
  }

  // Show badge if regression risk detected
  if (regressionRisk) {
    return (
      <Tooltip title="Regression Risk: Scored 20+ points last week">
        <Box
          sx={{
            display: 'inline-block',
            px: 1,
            py: 0.5,
            backgroundColor: '#ff5722',
            borderRadius: 1,
            fontSize: '0.75rem',
            color: 'white',
            fontWeight: 600,
            cursor: 'help',
          }}
        >
          Risk
        </Box>
      </Tooltip>
    );
  }

  // No risk
  return null;
};

export default RegressionRiskBadge;

