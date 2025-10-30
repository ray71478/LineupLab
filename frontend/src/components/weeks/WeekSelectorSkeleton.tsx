/**
 * Skeleton Loader for Week Selector
 *
 * Displays a loading state while weeks data is being fetched.
 * Matches the appearance of the actual WeekSelector component.
 *
 * Usage:
 * {isLoading ? <WeekSelectorSkeleton /> : <WeekSelector />}
 */

import React from 'react';
import {
  FormControl,
  InputLabel,
  Skeleton,
  Box,
  Stack,
} from '@mui/material';

export interface WeekSelectorSkeletonProps {
  count?: number;
}

export const WeekSelectorSkeleton: React.FC<WeekSelectorSkeletonProps> = ({
  count = 3,
}) => {
  return (
    <FormControl sx={{ minWidth: 180 }} size="small">
      <InputLabel id="week-selector-label">Week</InputLabel>
      <Box
        data-testid="week-selector-skeleton"
        sx={{
          height: 56,
          display: 'flex',
          alignItems: 'center',
          paddingX: 2,
        }}
      >
        <Skeleton variant="rectangular" width={60} height={20} />
      </Box>
    </FormControl>
  );
};

/**
 * Skeleton loader for multiple week cards
 * Useful for carousel or list views
 */
export const WeekCardSkeleton: React.FC<{ count?: number }> = ({ count = 3 }) => {
  return (
    <Stack direction="row" spacing={2}>
      {Array.from({ length: count }).map((_, i) => (
        <Box
          key={i}
          sx={{
            flex: '0 0 auto',
            width: 120,
            height: 150,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 1,
          }}
        >
          <Skeleton variant="circular" width={60} height={60} />
          <Skeleton variant="text" width={80} height={24} />
          <Skeleton variant="text" width={60} height={16} />
        </Box>
      ))}
    </Stack>
  );
};

/**
 * Skeleton loader for metadata panel
 */
export const WeekMetadataPanelSkeleton: React.FC = () => {
  return (
    <Box
      data-testid="week-metadata-panel-skeleton"
      sx={{
        width: '100%',
        padding: 2,
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
      }}
    >
      <Stack spacing={0.5}>
        <Skeleton variant="text" width="40%" height={16} />
        <Skeleton variant="text" width="60%" height={20} />
      </Stack>

      <Stack spacing={0.5}>
        <Skeleton variant="text" width="40%" height={16} />
        <Skeleton variant="text" width="50%" height={20} />
      </Stack>

      <Skeleton variant="text" width="45%" height={20} />
    </Box>
  );
};

export default WeekSelectorSkeleton;
