/**
 * ScoreDeltaIndicator Component
 *
 * Displays delta indicators (+2.5, -1.3) next to Smart Scores in table after recalculation.
 * - Format: `45.2 (+2.5)` or `38.7 (-1.3)`
 * - Color positive deltas green (subtle)
 * - Color negative deltas red (subtle)
 * - Shows only after recalculation
 */

import React from 'react';
import { Box, Typography } from '@mui/material';

export interface ScoreDeltaIndicatorProps {
  score: number | null | undefined;
  delta: number | null | undefined;
  showDelta?: boolean;
}

export const ScoreDeltaIndicator: React.FC<ScoreDeltaIndicatorProps> = ({
  score,
  delta,
  showDelta = true,
}) => {
  if (score === null || score === undefined) {
    return <Typography>-</Typography>;
  }

  const formatDelta = (deltaValue: number): string => {
    const sign = deltaValue >= 0 ? '+' : '';
    return `${sign}${deltaValue.toFixed(2)}`;
  };

  const getDeltaColor = (deltaValue: number): string => {
    if (deltaValue > 0) {
      return 'rgba(76, 175, 80, 0.6)'; // Green for positive
    } else if (deltaValue < 0) {
      return 'rgba(244, 67, 54, 0.6)'; // Red for negative
    }
    return 'transparent';
  };

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
      <Typography sx={{ fontWeight: 600 }}>{score.toFixed(2)}</Typography>
      {showDelta && delta !== null && delta !== undefined && delta !== 0 && (
        <Typography
          sx={{
            fontSize: '0.75rem',
            color: getDeltaColor(delta),
            fontWeight: 500,
          }}
        >
          ({formatDelta(delta)})
        </Typography>
      )}
    </Box>
  );
};

export default ScoreDeltaIndicator;

