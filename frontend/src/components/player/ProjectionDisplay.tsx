/**
 * ProjectionDisplay Component
 *
 * Reusable component for displaying projection values with dual-value support.
 * Shows calibrated and original values when calibration is applied, or single value when not.
 *
 * Props:
 * - label: Display label (e.g., "Floor", "Median", "Ceiling")
 * - originalValue: Original projection value
 * - calibratedValue: Calibrated projection value (if calibration applied)
 * - calibrationApplied: Whether calibration was applied to this player
 *
 * Display format per spec lines 54-61:
 * - If calibrationApplied: "Label: calibrated (original: original)"
 * - If not calibrationApplied: "Label: value"
 * - If NULL: Display "N/A"
 */

import React from 'react';
import { Box, Typography } from '@mui/material';

export interface ProjectionDisplayProps {
  label: string;
  originalValue?: number | null;
  calibratedValue?: number | null;
  calibrationApplied: boolean;
}

const ProjectionDisplay: React.FC<ProjectionDisplayProps> = ({
  label,
  originalValue,
  calibratedValue,
  calibrationApplied,
}) => {
  // Handle NULL values
  const hasOriginal = originalValue !== null && originalValue !== undefined;
  const hasCalibrated = calibratedValue !== null && calibratedValue !== undefined;

  // If both are NULL, display N/A
  if (!hasOriginal && !hasCalibrated) {
    return (
      <Box>
        <Typography
          variant="caption"
          sx={{
            color: '#9ca3af',
            fontSize: '0.75rem',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
          }}
        >
          {label}
        </Typography>
        <Typography
          variant="body2"
          sx={{
            color: '#6b7280',
            fontSize: '1.1rem',
            fontWeight: 400,
            marginTop: '4px',
            fontStyle: 'italic',
          }}
        >
          N/A
        </Typography>
      </Box>
    );
  }

  // Determine display value
  let displayValue: number;
  if (calibrationApplied && hasCalibrated) {
    displayValue = calibratedValue!;
  } else if (hasOriginal) {
    displayValue = originalValue!;
  } else if (hasCalibrated) {
    displayValue = calibratedValue!;
  } else {
    displayValue = 0; // Fallback
  }

  return (
    <Box>
      <Typography
        variant="caption"
        sx={{
          color: '#9ca3af',
          fontSize: '0.75rem',
          fontWeight: 600,
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
        }}
      >
        {label}
      </Typography>

      {calibrationApplied && hasOriginal && hasCalibrated && originalValue !== calibratedValue ? (
        // Dual-value display: Calibrated with original in muted text
        <Box sx={{ marginTop: '4px' }}>
          <Typography
            variant="body2"
            component="span"
            sx={{
              color: '#ffffff',
              fontSize: '1.1rem',
              fontWeight: 600,
            }}
          >
            {calibratedValue.toFixed(2)}
          </Typography>
          <Typography
            variant="body2"
            component="span"
            sx={{
              color: '#6b7280',
              fontSize: '0.9rem',
              fontWeight: 400,
              marginLeft: '8px',
              fontStyle: 'italic',
            }}
          >
            (original: {originalValue.toFixed(2)})
          </Typography>
        </Box>
      ) : (
        // Single value display
        <Typography
          variant="body2"
          sx={{
            color: '#ffffff',
            fontSize: '1.1rem',
            fontWeight: 600,
            marginTop: '4px',
          }}
        >
          {displayValue.toFixed(2)}
        </Typography>
      )}
    </Box>
  );
};

export default ProjectionDisplay;
