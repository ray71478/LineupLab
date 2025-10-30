/**
 * WeekCarouselCard Component
 *
 * Individual week card component for mobile carousel.
 * Displays large week number, status badge, and optional metadata preview.
 * Active week is larger and highlighted; inactive weeks are smaller and muted.
 */

import React from 'react';
import { Box, Typography, keyframes } from '@mui/material';
import { Week } from '../../store/weekStore';
import { WeekStatusBadge } from '../weeks/WeekStatusBadge';

export interface WeekCarouselCardProps {
  week: Week;
  isActive: boolean;
  onTap?: () => void;
}

// Glow animation for active card
const glowAnimation = keyframes`
  0% {
    box-shadow: 0 0 8px rgba(76, 175, 80, 0.3);
  }
  50% {
    box-shadow: 0 0 16px rgba(76, 175, 80, 0.6);
  }
  100% {
    box-shadow: 0 0 8px rgba(76, 175, 80, 0.3);
  }
`;

export const WeekCarouselCard: React.FC<WeekCarouselCardProps> = ({
  week,
  isActive,
  onTap,
}) => {
  const fontSize = isActive ? 48 : 32;
  const scale = isActive ? 1.1 : 0.9;
  const opacity = isActive ? 1 : 0.6;

  return (
    <Box
      onClick={onTap}
      data-testid={`week-carousel-card-${week.week_number}`}
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 1,
        padding: '24px 16px',
        borderRadius: '12px',
        minWidth: '100%',
        maxWidth: '100%',
        flex: '0 0 100%',
        transition: 'all 0.3s cubic-bezier(0.33, 0.66, 0.66, 1)',
        transform: `scale(${scale})`,
        opacity: opacity,
        backgroundColor: isActive ? 'rgba(76, 175, 80, 0.08)' : 'transparent',
        border: isActive ? '1px solid rgba(76, 175, 80, 0.2)' : '1px solid transparent',
        animation: isActive ? `${glowAnimation} 2s ease-in-out infinite` : 'none',
        cursor: 'pointer',
        userSelect: 'none',
        WebkitUserSelect: 'none',
        '&:active': {
          transform: `scale(${scale * 0.95})`,
        },
      }}
    >
      {/* Week Number - Large */}
      <Typography
        variant="h2"
        sx={{
          fontSize: `${fontSize}px`,
          fontWeight: isActive ? 700 : 500,
          color: isActive ? '#4caf50' : 'text.primary',
          lineHeight: 1,
          marginBottom: 1,
        }}
      >
        {week.week_number}
      </Typography>

      {/* Status Badge Below Week Number */}
      <Box>
        <WeekStatusBadge
          status={week.status}
          importStatus={week.metadata?.import_status}
          isCurrentWeek={isActive}
          compact={false}
        />
      </Box>

      {/* Week Range Indicator */}
      <Typography
        variant="caption"
        sx={{
          color: 'text.secondary',
          marginTop: 1,
          fontSize: '0.875rem',
        }}
      >
        Week {week.week_number} of 18
      </Typography>

      {/* Optional Metadata Preview */}
      {isActive && week.metadata && (
        <Box
          sx={{
            marginTop: 2,
            padding: '8px 12px',
            backgroundColor: 'rgba(76, 175, 80, 0.05)',
            borderRadius: '6px',
            textAlign: 'center',
            maxWidth: '100%',
          }}
        >
          <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block' }}>
            {week.metadata.kickoff_time}
          </Typography>
          {week.metadata.import_status === 'imported' && (
            <Typography variant="caption" sx={{ color: '#4caf50', display: 'block' }}>
              {week.metadata.import_count} imported
            </Typography>
          )}
        </Box>
      )}
    </Box>
  );
};

export default WeekCarouselCard;
