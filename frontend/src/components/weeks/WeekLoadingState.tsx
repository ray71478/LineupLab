/**
 * Loading State Component for Week Management
 *
 * Displays loading indicators during:
 * - API calls to fetch week data
 * - Data import operations
 * - Week status updates
 *
 * Features:
 * - Spinner with customizable message
 * - Prevents double submission with loading flag
 * - Disabled state for interactive elements
 * - Accessible loading announcements
 */

import React from 'react';
import {
  Box,
  CircularProgress,
  Typography,
  Backdrop,
  Stack,
  LinearProgress,
} from '@mui/material';

export interface WeekLoadingStateProps {
  isLoading: boolean;
  message?: string;
  fullScreen?: boolean;
  progress?: number; // 0-100 for progress bar
}

/**
 * Inline loading spinner
 */
export const WeekLoadingSpinner: React.FC<{
  message?: string;
  size?: number;
}> = ({ message = 'Loading...', size = 40 }) => {
  return (
    <Stack
      direction="column"
      spacing={2}
      alignItems="center"
      justifyContent="center"
      sx={{
        padding: 4,
        minHeight: '200px',
      }}
    >
      <CircularProgress
        size={size}
        thickness={4}
        data-testid="week-loading-spinner"
      />
      {message && (
        <Typography variant="body2" color="text.secondary">
          {message}
        </Typography>
      )}
    </Stack>
  );
};

/**
 * Full-screen loading backdrop
 */
export const WeekLoadingBackdrop: React.FC<{
  isLoading: boolean;
  message?: string;
}> = ({ isLoading, message = 'Loading week data...' }) => {
  return (
    <Backdrop
      open={isLoading}
      sx={{
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        zIndex: (theme) => theme.zIndex.modal + 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
      data-testid="week-loading-backdrop"
    >
      <Stack
        spacing={2}
        alignItems="center"
        sx={{
          backgroundColor: 'background.paper',
          padding: 4,
          borderRadius: 1,
        }}
      >
        <CircularProgress size={50} thickness={4} />
        <Typography variant="subtitle1">{message}</Typography>
      </Stack>
    </Backdrop>
  );
};

/**
 * Progress loading state with percentage
 */
export const WeekLoadingProgress: React.FC<{
  progress: number; // 0-100
  message?: string;
}> = ({ progress, message = 'Loading...' }) => {
  return (
    <Box
      sx={{
        width: '100%',
        padding: 2,
      }}
      data-testid="week-loading-progress"
    >
      <Stack spacing={1}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Typography variant="body2">{message}</Typography>
          <Typography variant="body2" color="text.secondary">
            {Math.round(progress)}%
          </Typography>
        </Box>
        <LinearProgress
          variant="determinate"
          value={progress}
          sx={{
            height: 4,
            borderRadius: 2,
          }}
        />
      </Stack>
    </Box>
  );
};

/**
 * Disabled state for buttons during loading
 */
export const useLoadingState = (isLoading: boolean) => {
  return {
    disabled: isLoading,
    isLoading,
    sx: {
      opacity: isLoading ? 0.6 : 1,
      pointerEvents: isLoading ? 'none' : 'auto',
      transition: 'opacity 150ms ease-in-out',
    },
  };
};

/**
 * Hook to prevent double submission with loading flag
 */
export const usePreventDoubleSubmit = () => {
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  const handleSubmit = React.useCallback(
    async (callback: () => Promise<any>) => {
      if (isSubmitting) return;

      try {
        setIsSubmitting(true);
        await callback();
      } finally {
        setIsSubmitting(false);
      }
    },
    [isSubmitting]
  );

  return {
    isSubmitting,
    handleSubmit,
    preventDouble: (callback: () => any) => {
      if (isSubmitting) return;
      callback();
    },
  };
};

export default WeekLoadingSpinner;
