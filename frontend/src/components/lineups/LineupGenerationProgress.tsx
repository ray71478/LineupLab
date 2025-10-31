/**
 * Lineup Generation Progress Component
 * 
 * Displays progress indicator during lineup generation:
 * - Elapsed time
 * - Adaptive progress estimate (based on typical patterns)
 * - Visual feedback
 * 
 * Note: Cannot get exact progress from CBC solver, so we use heuristic estimates
 * based on elapsed time and problem characteristics.
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
  numLineups?: number;
  numPlayers?: number;
}

export const LineupGenerationProgress: React.FC<LineupGenerationProgressProps> = ({
  isGenerating,
  numLineups = 10,
  numPlayers = 137,
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

  // Adaptive progress estimation based on elapsed time
  // Portfolio optimization typically takes 30-90 seconds
  // If it's been running longer, it's likely taking the full time
  const getEstimatedProgress = (elapsed: number): { progress: number; estimate: string } => {
    // Base estimate: 30-60 seconds for typical problems
    const baseEstimate = 45;
    
    // If it's been running longer than base estimate, likely going to 90s timeout
    if (elapsed < 15) {
      // Early stage: optimistic estimate
      return {
        progress: Math.min((elapsed / 45) * 100, 30), // Cap at 30% for early stage
        estimate: '~30-45s',
      };
    } else if (elapsed < 45) {
      // Mid stage: use elapsed time as indicator
      const remaining = Math.max(30 - elapsed, 10);
      return {
        progress: Math.min((elapsed / 60) * 100, 85), // Cap at 85% until near completion
        estimate: `~${Math.round(remaining)}s`,
      };
    } else {
      // Late stage: likely going to timeout or very close
      return {
        progress: Math.min((elapsed / 90) * 100, 95), // Cap at 95% until done
        estimate: elapsed < 90 ? `~${Math.round(90 - elapsed)}s` : 'finishing up...',
      };
    }
  };

  const { progress, estimate } = getEstimatedProgress(elapsedSeconds);
  const remainingSeconds = Math.max(0, 90 - elapsedSeconds);

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
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1, flexWrap: 'wrap' }}>
          <Typography variant="body1" sx={{ fontWeight: 600, color: '#ff6b35' }}>
            Generating Lineups...
          </Typography>
          <Typography variant="body2" sx={{ color: 'text.secondary' }}>
            {formatTime(elapsedSeconds)} elapsed
          </Typography>
          {remainingSeconds > 0 && (
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              Est. {estimate} remaining
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
          Portfolio optimization for {numLineups} lineups ({numPlayers} players). 
          Solver runtime varies by problem complexity (typically 30-90 seconds).
        </Typography>
      </CardContent>
    </Card>
  );
};

export default LineupGenerationProgress;
