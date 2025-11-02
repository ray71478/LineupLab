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

  // Stage-based progress estimation with guaranteed minimums
  // Ensures progress never goes backwards - each stage builds on the previous
  // Portfolio optimization typically takes 30-90 seconds
  const getEstimatedProgress = (elapsed: number): { progress: number; estimate: string } => {
    // Stage 1: Early (0-15s) → 0% to 30%
    if (elapsed < 15) {
      const stageProgress = (elapsed / 15) * 30; // 0-30%
      return {
        progress: stageProgress,
        estimate: '~30-45s',
      };
    }
    
    // Stage 2: Mid (15-45s) → 30% to 85%
    if (elapsed < 45) {
      const stageElapsed = elapsed - 15; // Time within this stage
      const stageDuration = 30; // Duration of this stage (15-45s)
      const stageProgress = (stageElapsed / stageDuration) * 55; // 0-55% within stage
      const progress = 30 + stageProgress; // 30-85% total
      const remaining = Math.max(30 - stageElapsed, 10);
      return {
        progress,
        estimate: `~${Math.round(remaining)}s`,
      };
    }
    
    // Stage 3: Late (45-90s) → 85% to 95%
    const stageElapsed = elapsed - 45; // Time within this stage
    const stageDuration = 45; // Duration of this stage (45-90s)
    const stageProgress = Math.min((stageElapsed / stageDuration) * 10, 10); // 0-10% within stage
    const progress = 85 + stageProgress; // 85-95% total
    const remaining = Math.max(90 - elapsed, 0);
    
    return {
      progress: Math.min(progress, 95), // Cap at 95% until done
      estimate: remaining > 0 ? `~${Math.round(remaining)}s` : 'finishing up...',
    };
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
