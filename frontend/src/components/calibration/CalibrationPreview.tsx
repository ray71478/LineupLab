/**
 * CalibrationPreview Component
 *
 * Displays a sample calibration calculation preview showing how
 * adjustment percentages affect projection values.
 *
 * Props:
 * - originalValue: Sample original projection value
 * - adjustmentPercent: Adjustment percentage to apply
 * - label: Label for the projection type (Floor, Median, Ceiling)
 *
 * Formula: Original × (1 + adjustment% / 100) = calibrated
 * Example: 12.0 × 1.05 = 12.6
 */

import React from 'react';
import { Box, Typography, Stack, Divider } from '@mui/material';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';

export interface CalibrationPreviewProps {
  originalValue: number;
  adjustmentPercent: number;
  label: string;
}

/**
 * Calculate calibrated value using the calibration formula
 */
function calculateCalibratedValue(original: number, adjustmentPercent: number): number {
  const calibrated = original * (1 + adjustmentPercent / 100);
  return Math.max(0, Math.round(calibrated * 100) / 100); // Round to 2 decimals, min 0
}

/**
 * CalibrationPreview Component
 */
export const CalibrationPreview: React.FC<CalibrationPreviewProps> = ({
  originalValue,
  adjustmentPercent,
  label,
}) => {
  const calibratedValue = calculateCalibratedValue(originalValue, adjustmentPercent);
  const difference = calibratedValue - originalValue;
  const isIncrease = difference > 0;
  const isDecrease = difference < 0;

  return (
    <Box
      sx={{
        padding: 2,
        backgroundColor: 'rgba(255, 255, 255, 0.02)',
        borderRadius: 1,
        border: '1px solid rgba(255, 255, 255, 0.1)',
      }}
    >
      <Typography
        variant="caption"
        sx={{
          display: 'block',
          color: 'text.secondary',
          fontWeight: 600,
          textTransform: 'uppercase',
          letterSpacing: 0.5,
          marginBottom: 1.5,
        }}
      >
        {label} Calibration Preview
      </Typography>

      <Stack direction="row" alignItems="center" spacing={2} sx={{ marginBottom: 2 }}>
        {/* Original Value */}
        <Box
          sx={{
            flex: 1,
            padding: 1.5,
            backgroundColor: 'rgba(158, 158, 158, 0.1)',
            borderRadius: 1,
            border: '1px solid rgba(158, 158, 158, 0.2)',
          }}
        >
          <Typography
            variant="caption"
            sx={{
              display: 'block',
              color: 'text.secondary',
              fontSize: '0.7rem',
              marginBottom: 0.5,
            }}
          >
            Original
          </Typography>
          <Typography variant="h6" sx={{ fontWeight: 600, color: '#9e9e9e' }}>
            {originalValue.toFixed(1)}
          </Typography>
        </Box>

        {/* Arrow */}
        <ArrowForwardIcon sx={{ color: 'text.secondary', fontSize: 20 }} />

        {/* Calibrated Value */}
        <Box
          sx={{
            flex: 1,
            padding: 1.5,
            backgroundColor: isIncrease
              ? 'rgba(76, 175, 80, 0.1)'
              : isDecrease
              ? 'rgba(244, 67, 54, 0.1)'
              : 'rgba(158, 158, 158, 0.1)',
            borderRadius: 1,
            border: `1px solid ${
              isIncrease
                ? 'rgba(76, 175, 80, 0.3)'
                : isDecrease
                ? 'rgba(244, 67, 54, 0.3)'
                : 'rgba(158, 158, 158, 0.2)'
            }`,
          }}
        >
          <Typography
            variant="caption"
            sx={{
              display: 'block',
              color: 'text.secondary',
              fontSize: '0.7rem',
              marginBottom: 0.5,
            }}
          >
            Calibrated
          </Typography>
          <Typography
            variant="h6"
            sx={{
              fontWeight: 600,
              color: isIncrease ? '#4caf50' : isDecrease ? '#f44336' : '#9e9e9e',
            }}
          >
            {calibratedValue.toFixed(1)}
          </Typography>
        </Box>
      </Stack>

      {/* Difference Indicator */}
      {difference !== 0 && (
        <Box
          sx={{
            padding: 1,
            backgroundColor: isIncrease
              ? 'rgba(76, 175, 80, 0.05)'
              : 'rgba(244, 67, 54, 0.05)',
            borderRadius: 0.5,
          }}
        >
          <Typography
            variant="caption"
            sx={{
              color: isIncrease ? '#4caf50' : '#f44336',
              fontWeight: 500,
              fontSize: '0.75rem',
            }}
          >
            {isIncrease ? '+' : ''}
            {difference.toFixed(1)} ({isIncrease ? '+' : ''}
            {adjustmentPercent.toFixed(1)}%)
          </Typography>
        </Box>
      )}

      {/* Formula Display */}
      <Divider sx={{ marginY: 1.5, opacity: 0.3 }} />

      <Box
        sx={{
          padding: 1,
          backgroundColor: 'rgba(0, 0, 0, 0.2)',
          borderRadius: 0.5,
          fontFamily: 'monospace',
        }}
      >
        <Typography
          variant="caption"
          sx={{
            display: 'block',
            color: 'text.secondary',
            fontSize: '0.65rem',
            marginBottom: 0.5,
          }}
        >
          Formula:
        </Typography>
        <Typography
          variant="body2"
          sx={{
            color: 'text.primary',
            fontSize: '0.75rem',
            fontFamily: 'monospace',
          }}
        >
          {originalValue.toFixed(1)} × (1 + {adjustmentPercent.toFixed(1)} / 100) ={' '}
          {calibratedValue.toFixed(1)}
        </Typography>
      </Box>
    </Box>
  );
};

export default CalibrationPreview;
