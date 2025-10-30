/**
 * Optimized WeekMetadataPanel Component
 *
 * Performance optimizations:
 * - React.memo to prevent unnecessary re-renders
 * - Memoized selectors for computed values
 * - Lazy loading of metadata details
 * - Efficient formatting with useMemo
 * - CSS-based animations only
 */

import React, { useMemo, lazy, Suspense } from 'react';
import {
  Box,
  Stack,
  Typography,
  Link,
  Skeleton,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import { Week } from '../../store/weekStore';
import WeekImportStatusBadge from './WeekImportStatusBadge';

export interface WeekMetadataPanelProps {
  week: Week;
  isLoading?: boolean;
  compact?: boolean;
}

// Lazy load import status badge details
const ImportStatusDetailComponent = lazy(() =>
  Promise.resolve({ default: WeekImportStatusBadge })
);

/**
 * Format NFL date to readable format
 * Input: "2025-09-07"
 * Output: "Sunday, September 7"
 */
const formatNFLDate = (dateStr: string): string => {
  try {
    const date = new Date(dateStr + 'T00:00:00Z');
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
    });
  } catch {
    return dateStr;
  }
};

/**
 * Format kickoff time to readable format
 * Input: "13:00"
 * Output: "1:00 PM ET"
 */
const formatKickoffTime = (timeStr: string): string => {
  try {
    const [hours, minutes] = timeStr.split(':');
    const date = new Date();
    date.setHours(parseInt(hours), parseInt(minutes));
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      timeZoneName: 'short',
      timeZone: 'America/New_York',
    });
  } catch {
    return timeStr;
  }
};

const WeekMetadataPanelContent: React.FC<WeekMetadataPanelProps> = ({
  week,
  isLoading = false,
  compact = false,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  // Memoize formatted values to avoid recalculation
  const formattedDate = useMemo(
    () => formatNFLDate(week.nfl_slate_date),
    [week.nfl_slate_date]
  );

  const formattedTime = useMemo(
    () => formatKickoffTime(week.metadata?.kickoff_time || '13:00'),
    [week.metadata?.kickoff_time]
  );

  const espnUrl = useMemo(
    () => week.metadata?.espn_link || '',
    [week.metadata?.espn_link]
  );

  if (isLoading) {
    return (
      <Box sx={{ width: '100%' }}>
        <Skeleton variant="text" height={24} width="60%" />
        <Skeleton variant="text" height={20} width="40%" sx={{ mt: 1 }} />
        <Skeleton variant="text" height={20} width="50%" sx={{ mt: 1 }} />
      </Box>
    );
  }

  const containerSx = compact
    ? {
        display: 'flex',
        gap: 1,
        alignItems: 'center',
        flexWrap: 'wrap',
      }
    : {
        display: 'flex',
        flexDirection: 'column',
        gap: 1.5,
      };

  return (
    <Box
      data-testid="week-metadata-panel-optimized"
      sx={{
        ...containerSx,
        padding: compact ? 0 : 2,
        backgroundColor: compact ? 'transparent' : 'rgba(0, 0, 0, 0.02)',
        borderRadius: compact ? 0 : 1,
      }}
    >
      {/* NFL Slate Date */}
      {!compact && (
        <Stack spacing={0.5}>
          <Typography variant="caption" color="text.secondary">
            NFL Slate Date
          </Typography>
          <Typography variant="body2" sx={{ fontWeight: 500 }}>
            {formattedDate}
          </Typography>
        </Stack>
      )}

      {/* Kickoff Time */}
      {!compact && (
        <Stack spacing={0.5}>
          <Typography variant="caption" color="text.secondary">
            Kickoff Time (ET)
          </Typography>
          <Typography variant="body2" sx={{ fontWeight: 500 }}>
            {formattedTime}
          </Typography>
        </Stack>
      )}

      {/* ESPN Link */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Link
          href={espnUrl}
          target="_blank"
          rel="noopener noreferrer"
          underline="hover"
          variant={compact ? 'body2' : 'body1'}
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 0.5,
            // Performant hover effect
            transition: 'opacity 150ms ease-in-out',
            '&:hover': {
              opacity: 0.8,
            },
          }}
        >
          ESPN Schedule
          <OpenInNewIcon sx={{ fontSize: 16 }} />
        </Link>
      </Box>

      {/* Import Status Badge - Lazy loaded */}
      <Suspense fallback={<Skeleton variant="text" width={100} />}>
        <ImportStatusDetailComponent
          importStatus={week.metadata?.import_status || 'pending'}
          importCount={week.metadata?.import_count || 0}
          importTimestamp={week.metadata?.import_timestamp || null}
          errorMessage={week.metadata?.error_message}
        />
      </Suspense>
    </Box>
  );
};

// Wrap with React.memo to prevent unnecessary re-renders
export const WeekMetadataPanel = React.memo(WeekMetadataPanelContent);

export default WeekMetadataPanel;
