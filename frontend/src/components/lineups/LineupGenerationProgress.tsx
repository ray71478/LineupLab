/**
 * Lineup Generation Progress Component
 * 
 * Displays progress indicator during lineup generation:
 * - Elapsed time
 * - Progress bar (estimated max 90 seconds)
 * - Visual feedback
 */

import React, { useEffect, useState } from 'react';
import {
  Box,
  LinearProgress,
  Typography,
  Card,
  CardContent,
} from '@mui/material';

interface LineupGenerationProgressProps {
  isGenerating: boolean;
  maxTimeSeconds?: number; // Estimated max time (default: 90 seconds)
}

export const LineupGenerationProgress: React.FC<LineupGenerationProgressProps> = ({
  isGenerating,
  maxTimeSeconds = 90,
}) => {
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  useEffect(() => {
    if (!isGenerating) {
      setElapsedSeconds(0);
      return;
    }

    const interval = setInterval(() => {
      setElapsedSeconds((prev) => {
        const next = prev + 0.1; // Update every 100ms for smooth progress
        return next;
      });
    }, 100);

    return () => clearInterval(interval);
  }, [isGenerating]);

  if (!isGenerating) {
    return null;
  }

  const progress = Math.min((elapsedSeconds / maxTimeSeconds) * 100, 100);
  const remainingSeconds = Math.max(0, maxTimeSeconds - elapsedSeconds);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    if (mins > 0) {
      return `${mins}m ${secs}s`;
    }
    return `${secs}s`;
  };

  return (
    <Card
      sx={{
        mb: 3,
        backgroundColor: 'rgba(255, 107, 53, 0.1)',
        border: '1px solid rgba(255, 107, 53, 0.3)',
      }}
    >
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
          <Typography variant="body1" sx={{ fontWeight: 600, color: '#ff6b35' }}>
            Generating Lineups...
          </Typography>
          <Typography variant="body2" sx={{ color: 'text.secondary' }}>
            {formatTime(elapsedSeconds)} elapsed
          </Typography>
          {remainingSeconds > 0 && (
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              ~{formatTime(remainingSeconds)} remaining
            </Typography>
          )}
        </Box>
        <LinearProgress
          variant="determinate"
          value={progress}
          sx={{
            height: 8,
            borderRadius: 4,
            backgroundColor: 'rgba(255, 107, 53, 0.2)',
            '& .MuiLinearProgress-bar': {
              backgroundColor: '#ff6b35',
            },
          }}
        />
        <Typography
          variant="caption"
          sx={{
            mt: 1,
            display: 'block',
            color: 'text.secondary',
            fontStyle: 'italic',
          }}
        >
          Portfolio optimization may take up to 90 seconds for 10 lineups
        </Typography>
      </CardContent>
    </Card>
  );
};

export default LineupGenerationProgress;

