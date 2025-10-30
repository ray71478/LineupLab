/**
 * WeekMetadataPanel Component
 *
 * Displays NFL week metadata:
 * - NFL slate date (formatted: "Sunday, September 7")
 * - Kickoff time (formatted: "1:00 PM ET")
 * - ESPN schedule link (clickable, opens in new tab)
 * - Import status badge
 * - Import details tooltip
 *
 * Responsive layout:
 * - Full panel for desktop
 * - Compact layout for mobile
 * - Loading skeleton while data loads
 * - Dark mode optimized
 */

import React from 'react';
import {
  Box,
  Stack,
  Typography,
  Link,
  Skeleton,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import EventIcon from '@mui/icons-material/Event';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import WeekImportStatusBadge from './WeekImportStatusBadge';

interface Week {
  id: number;
  season: number;
  week_number: number;
  status: 'active' | 'upcoming' | 'completed';
  status_override: string | null;
  nfl_slate_date: string;
  is_locked: boolean;
  locked_at: string | null;
  metadata: {
    kickoff_time: string;
    espn_link: string;
    slate_start: string;
    import_status: 'pending' | 'imported' | 'error';
    import_count: number;
    import_timestamp: string | null;
    error_message?: string | null;
  };
}

export interface WeekMetadataPanelProps {
  week: Week;
  isLoading?: boolean;
  compact?: boolean;
}

// Format date as "Sunday, September 7"
const formatNFLDate = (dateStr: string): string => {
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
    });
  } catch {
    return dateStr;
  }
};

// Format time as "1:00 PM ET"
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

export const WeekMetadataPanel: React.FC<WeekMetadataPanelProps> = ({
  week,
  isLoading = false,
  compact = false,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  if (isLoading) {
    return (
      <Box
        data-testid="metadata-skeleton"
        sx={{
          display: 'flex',
          flexDirection: 'column',
          gap: 1.5,
          padding: compact ? 1 : 2,
        }}
      >
        <Skeleton variant="text" width="80%" height={24} />
        <Skeleton variant="text" width="60%" height={20} />
        <Skeleton variant="rectangular" width="40%" height={32} />
      </Box>
    );
  }

  const formattedDate = formatNFLDate(week.nfl_slate_date);
  const formattedTime = formatKickoffTime(week.metadata.kickoff_time);

  if (compact || isMobile) {
    // Compact layout - suitable for tooltips or mobile
    return (
      <Box
        data-testid="week-metadata-panel"
        className="compact-layout"
        sx={{
          display: 'flex',
          flexDirection: 'column',
          gap: 1,
          padding: 1.5,
        }}
      >
        <Stack direction="row" spacing={1} alignItems="center">
          <EventIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
          <Typography variant="body2" color="text.secondary">
            {formattedDate}
          </Typography>
        </Stack>

        <Stack direction="row" spacing={1} alignItems="center">
          <AccessTimeIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
          <Typography variant="body2" color="text.secondary">
            {formattedTime}
          </Typography>
        </Stack>

        <Stack direction="row" spacing={1} alignItems="center">
          <Link
            href={week.metadata.espn_link}
            target="_blank"
            rel="noopener noreferrer"
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 0.5,
              fontSize: '0.875rem',
              fontWeight: 500,
            }}
          >
            Schedule
            <OpenInNewIcon sx={{ fontSize: 14 }} />
          </Link>
        </Stack>

        <WeekImportStatusBadge
          importStatus={week.metadata.import_status}
          importCount={week.metadata.import_count}
          importTimestamp={week.metadata.import_timestamp}
          errorMessage={week.metadata.error_message}
        />
      </Box>
    );
  }

  // Full layout for desktop
  return (
    <Box
      data-testid="week-metadata-panel"
      sx={{
        display: 'flex',
        flexDirection: 'column',
        gap: 2.5,
        padding: 2.5,
        backgroundColor: 'background.paper',
        borderRadius: 1,
        border: `1px solid ${theme.palette.divider}`,
      }}
    >
      <Stack spacing={1.5}>
        {/* NFL Slate Date */}
        <Stack direction="row" spacing={1.5} alignItems="flex-start">
          <EventIcon
            sx={{
              fontSize: 20,
              color: 'primary.main',
              marginTop: 0.5,
              flexShrink: 0,
            }}
          />
          <Stack spacing={0.5} flex={1}>
            <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'uppercase' }}>
              NFL Slate Date
            </Typography>
            <Typography variant="body1" sx={{ fontWeight: 500 }}>
              {formattedDate}
            </Typography>
          </Stack>
        </Stack>

        {/* Kickoff Time */}
        <Stack direction="row" spacing={1.5} alignItems="flex-start">
          <AccessTimeIcon
            sx={{
              fontSize: 20,
              color: 'primary.main',
              marginTop: 0.5,
              flexShrink: 0,
            }}
          />
          <Stack spacing={0.5} flex={1}>
            <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'uppercase' }}>
              Kickoff Time
            </Typography>
            <Typography variant="body1" sx={{ fontWeight: 500 }}>
              {formattedTime}
            </Typography>
          </Stack>
        </Stack>
      </Stack>

      {/* ESPN Schedule Link */}
      <Link
        href={week.metadata.espn_link}
        target="_blank"
        rel="noopener noreferrer"
        sx={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 0.5,
          fontWeight: 500,
          color: 'primary.main',
          textDecoration: 'none',
          '&:hover': {
            textDecoration: 'underline',
          },
        }}
      >
        View Full Schedule on ESPN
        <OpenInNewIcon sx={{ fontSize: 16 }} />
      </Link>

      {/* Import Status */}
      <Box
        sx={{
          paddingTop: 2,
          borderTop: `1px solid ${theme.palette.divider}`,
        }}
      >
        <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'uppercase', display: 'block', marginBottom: 1 }}>
          Import Status
        </Typography>
        <WeekImportStatusBadge
          importStatus={week.metadata.import_status}
          importCount={week.metadata.import_count}
          importTimestamp={week.metadata.import_timestamp}
          errorMessage={week.metadata.error_message}
        />
      </Box>
    </Box>
  );
};

export default WeekMetadataPanel;
