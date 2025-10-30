/**
 * WeekNavigation Component
 *
 * Responsive wrapper component that conditionally renders appropriate
 * week navigation based on device size.
 *
 * Features:
 * - Desktop (>600px): WeekSelector + YearSelector side-by-side
 * - Mobile (<600px): WeekCarousel
 * - Uses Material-UI useMediaQuery hook for responsiveness
 * - Smooth transitions between layouts
 */

import React, { useCallback } from 'react';
import { Box, Container, useMediaQuery, useTheme, Stack } from '@mui/material';
import { useWeekStore } from '../../store/weekStore';
import { useWeeks } from '../../hooks/useWeeks';
import WeekSelector from './WeekSelector';
import YearSelector from './YearSelector';
import { WeekCarousel } from '../mobile/WeekCarousel';

export interface WeekNavigationProps {
  onWeekChange?: (week: number) => void;
  showMetadata?: boolean;
  maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
}

export const WeekNavigation: React.FC<WeekNavigationProps> = ({
  onWeekChange,
  showMetadata = true,
  maxWidth = 'md',
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm')); // <600px
  const isTablet = useMediaQuery(theme.breakpoints.down('md')); // <960px

  const { currentYear, currentWeek, weeks, setCurrentYear } = useWeekStore();
  const { data: weeksData, isLoading } = useWeeks(currentYear);

  // Handle week selection
  const handleWeekChange = useCallback(
    (week: number) => {
      if (onWeekChange) {
        onWeekChange(week);
      }
    },
    [onWeekChange]
  );

  // Handle year selection
  const handleYearChange = useCallback(
    (year: number) => {
      setCurrentYear(year);
    },
    [setCurrentYear]
  );

  // Desktop View: WeekSelector + YearSelector
  if (!isMobile) {
    return (
      <Container maxWidth={maxWidth} disableGutters>
        <Stack
          direction="row"
          spacing={2}
          alignItems="center"
          sx={{
            padding: '8px 16px',
            backgroundColor: 'transparent',
            transition: 'all 0.2s ease-out',
          }}
        >
          {/* Year Selector */}
          <YearSelector
            currentYear={currentYear}
            onYearChange={handleYearChange}
            availableYears={[2025, 2026, 2027, 2028, 2029, 2030]}
          />

          {/* Week Selector */}
          <WeekSelector
            onWeekChange={handleWeekChange}
            showMetadata={showMetadata}
          />
        </Stack>
      </Container>
    );
  }

  // Mobile View: WeekCarousel
  return (
    <Box
      sx={{
        width: '100%',
        padding: 0,
        backgroundColor: 'transparent',
        transition: 'all 0.2s ease-out',
      }}
    >
      {weeks.length > 0 && currentWeek && (
        <WeekCarousel
          weeks={weeks}
          currentWeek={currentWeek}
          onWeekChange={handleWeekChange}
          showMetadata={showMetadata}
        />
      )}
    </Box>
  );
};

export default WeekNavigation;
