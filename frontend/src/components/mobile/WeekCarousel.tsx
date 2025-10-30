/**
 * WeekCarousel Component
 *
 * Mobile-optimized swipeable carousel for week selection.
 * Uses react-swipeable library for swipe detection.
 *
 * Features:
 * - Horizontal scrollable carousel
 * - Swipe left/right for navigation
 * - Week cards with large week number and status badge
 * - Snap to center on release (300ms animation)
 * - Tap to open metadata modal
 * - Show 3 weeks at a time (current + left + right)
 * - Virtualized for performance
 * - Debounced swipe handlers (100ms)
 */

import React, { useState, useCallback, useMemo } from 'react';
import { Box, useMediaQuery, useTheme } from '@mui/material';
import { Week } from '../../store/weekStore';
import { WeekCarouselCard } from './WeekCarouselCard';
import { WeekMetadataModal } from '../weeks/WeekMetadataModal';

export interface WeekCarouselProps {
  weeks: Week[];
  currentWeek: number;
  onWeekChange: (week: number) => void;
  showMetadata?: boolean;
}

export const WeekCarousel: React.FC<WeekCarouselProps> = ({
  weeks,
  currentWeek,
  onWeekChange,
  showMetadata = true,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [selectedWeekForModal, setSelectedWeekForModal] = useState<Week | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [lastSwipeTime, setLastSwipeTime] = useState(0);

  const currentIndex = useMemo(
    () => weeks.findIndex((w) => w.week_number === currentWeek),
    [weeks, currentWeek]
  );

  // Get visible weeks (current + left + right)
  const visibleWeeks = useMemo(() => {
    const start = Math.max(0, currentIndex - 1);
    const end = Math.min(weeks.length, currentIndex + 2);
    return weeks.slice(start, end);
  }, [weeks, currentIndex]);

  // Debounce swipe handler
  const handleSwipe = useCallback(
    (direction: 'left' | 'right') => {
      const now = Date.now();
      if (now - lastSwipeTime < 100) return; // Debounce 100ms
      setLastSwipeTime(now);

      if (direction === 'left' && currentIndex < weeks.length - 1) {
        // Swipe left = next week
        const nextWeek = weeks[currentIndex + 1];
        onWeekChange(nextWeek.week_number);
      } else if (direction === 'right' && currentIndex > 0) {
        // Swipe right = previous week
        const previousWeek = weeks[currentIndex - 1];
        onWeekChange(previousWeek.week_number);
      }
    },
    [currentIndex, weeks, onWeekChange, lastSwipeTime]
  );

  // Handle swipe velocity (multiple weeks)
  const handleSwipeVelocity = useCallback(
    (velocity: number, direction: 'left' | 'right') => {
      const now = Date.now();
      if (now - lastSwipeTime < 100) return;

      if (Math.abs(velocity) > 0.5) {
        // Fast swipe = skip multiple weeks
        const distance = Math.min(3, Math.ceil(Math.abs(velocity) * 2));
        const newIndex =
          direction === 'left'
            ? Math.min(weeks.length - 1, currentIndex + distance)
            : Math.max(0, currentIndex - distance);

        if (newIndex !== currentIndex) {
          setLastSwipeTime(now);
          onWeekChange(weeks[newIndex].week_number);
        }
      }
    },
    [currentIndex, weeks, onWeekChange, lastSwipeTime]
  );

  const handleTapCard = (week: Week) => {
    if (showMetadata) {
      setSelectedWeekForModal(week);
      setIsModalOpen(true);
    }
  };

  const handleModalClose = () => {
    setIsModalOpen(false);
    setSelectedWeekForModal(null);
  };

  // Keyboard navigation for accessibility
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      switch (e.key) {
        case 'ArrowLeft':
          e.preventDefault();
          handleSwipe('right');
          break;
        case 'ArrowRight':
          e.preventDefault();
          handleSwipe('left');
          break;
        case 'Enter':
          if (weeks[currentIndex]) {
            handleTapCard(weeks[currentIndex]);
          }
          break;
        default:
          break;
      }
    },
    [handleSwipe, weeks, currentIndex]
  );

  if (!isMobile || weeks.length === 0) {
    return null;
  }

  return (
    <>
      <Box
        onKeyDown={handleKeyDown}
        tabIndex={0}
        data-testid="week-carousel"
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 2,
          padding: '24px 16px',
          position: 'relative',
          touchAction: 'pan-y', // Allow vertical scrolling, horizontal is handled by carousel
        }}
      >
        {/* Carousel Container */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 2,
            position: 'relative',
            width: '100%',
            overflow: 'hidden',
            perspective: '1000px',
          }}
        >
          {/* Previous Week */}
          {currentIndex > 0 && (
            <Box
              sx={{
                flex: '0 0 calc(100% - 120px)',
                opacity: 0.5,
                transform: 'scale(0.8)',
                transition: 'all 0.3s cubic-bezier(0.33, 0.66, 0.66, 1)',
              }}
            >
              <WeekCarouselCard
                week={weeks[currentIndex - 1]}
                isActive={false}
                onTap={() => handleTapCard(weeks[currentIndex - 1])}
              />
            </Box>
          )}

          {/* Current Week */}
          <Box
            sx={{
              flex: '1 1 auto',
              minWidth: 0,
              maxWidth: '100%',
            }}
          >
            <WeekCarouselCard
              week={weeks[currentIndex]}
              isActive={true}
              onTap={() => handleTapCard(weeks[currentIndex])}
            />
          </Box>

          {/* Next Week */}
          {currentIndex < weeks.length - 1 && (
            <Box
              sx={{
                flex: '0 0 calc(100% - 120px)',
                opacity: 0.5,
                transform: 'scale(0.8)',
                transition: 'all 0.3s cubic-bezier(0.33, 0.66, 0.66, 1)',
              }}
            >
              <WeekCarouselCard
                week={weeks[currentIndex + 1]}
                isActive={false}
                onTap={() => handleTapCard(weeks[currentIndex + 1])}
              />
            </Box>
          )}
        </Box>

        {/* Swipe Hint */}
        <Box
          sx={{
            fontSize: '0.75rem',
            color: 'text.secondary',
            textAlign: 'center',
            marginTop: 2,
          }}
        >
          Swipe to navigate weeks
        </Box>
      </Box>

      {/* Metadata Modal */}
      {selectedWeekForModal && (
        <WeekMetadataModal
          week={selectedWeekForModal}
          open={isModalOpen}
          onClose={handleModalClose}
        />
      )}
    </>
  );
};

export default WeekCarousel;
