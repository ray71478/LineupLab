/**
 * MissingDataIndicator Component
 *
 * Small indicator icon/tooltip showing which factors used default values.
 * - Shows warning icon when missing_data_indicators present
 * - Tooltip lists which factors used defaults
 * - Styled with subtle orange/yellow accent
 *
 * Design: Subtle indicator that doesn't distract from main content
 */

import React from 'react';
import { Box, Tooltip } from '@mui/material';
import WarningIcon from '@mui/icons-material/Warning';

export interface MissingDataIndicatorProps {
  missingDataIndicators?: Record<string, boolean> | null;
}

const FACTOR_NAMES: Record<string, string> = {
  W1: 'Projection',
  W2: 'Ceiling Factor',
  W3: 'Ownership Penalty',
  W4: 'Value Score',
  W5: 'Trend Adjustment',
  W6: 'Regression Penalty',
  W7: 'Vegas Context',
  W8: 'Matchup Adjustment',
};

export const MissingDataIndicator: React.FC<MissingDataIndicatorProps> = ({
  missingDataIndicators,
}) => {
  if (!missingDataIndicators) {
    return null;
  }

  // Find factors that used defaults
  const missingFactors = Object.entries(missingDataIndicators)
    .filter(([_, usedDefault]) => usedDefault)
    .map(([factor, _]) => FACTOR_NAMES[factor] || factor);

  if (missingFactors.length === 0) {
    return null;
  }

  const tooltipText = `Missing data used defaults: ${missingFactors.join(', ')}`;

  return (
    <Tooltip title={tooltipText} arrow>
      <Box
        sx={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: 18,
          height: 18,
          color: '#ff9800',
          cursor: 'help',
        }}
      >
        <WarningIcon sx={{ fontSize: 16 }} />
      </Box>
    </Tooltip>
  );
};

export default MissingDataIndicator;

