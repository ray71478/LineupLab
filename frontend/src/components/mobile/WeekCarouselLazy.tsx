/**
 * Lazy-loaded WeekCarousel Component
 *
 * Wraps the WeekCarousel with React.lazy() for code splitting.
 * Only loaded when rendered on mobile devices.
 *
 * Usage:
 * const WeekCarouselLazy = lazy(() => import('./WeekCarouselLazy'));
 *
 * <Suspense fallback={<CircularProgress />}>
 *   <WeekCarouselLazy weeks={weeks} currentWeek={currentWeek} />
 * </Suspense>
 */

import React, { Suspense, lazy, CircleProps } from 'react';
import { Box, CircularProgress, useMediaQuery, useTheme } from '@mui/material';

// Lazy load the actual carousel component
const WeekCarouselComponent = lazy(() =>
  import('./WeekCarousel').then((module) => ({
    default: module.WeekCarousel,
  }))
);

// Lazy load modal only when needed
const WeekMetadataModalComponent = lazy(() =>
  import('../weeks/WeekMetadataModal').then((module) => ({
    default: module.WeekMetadataModal,
  }))
);

export interface WeekCarouselLazyProps {
  weeks: any[];
  currentWeek: number;
  onWeekChange: (week: number) => void;
  showMetadata?: boolean;
}

// Loading fallback component
const CarouselLoadingFallback: React.FC = () => (
  <Box
    sx={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '150px',
      width: '100%',
    }}
  >
    <CircularProgress size={40} />
  </Box>
);

/**
 * LazyWeekCarousel - Lazy-loaded carousel for mobile
 * Only renders on mobile breakpoints to reduce bundle size
 */
export const WeekCarouselLazy: React.FC<WeekCarouselLazyProps> = ({
  weeks,
  currentWeek,
  onWeekChange,
  showMetadata = true,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  // Only render on mobile to save bandwidth on desktop
  if (!isMobile) {
    return null;
  }

  return (
    <Suspense fallback={<CarouselLoadingFallback />}>
      <WeekCarouselComponent
        weeks={weeks}
        currentWeek={currentWeek}
        onWeekChange={onWeekChange}
        showMetadata={showMetadata}
      />
    </Suspense>
  );
};

export default WeekCarouselLazy;
