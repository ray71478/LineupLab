/**
 * WeekMetadataModal Component
 *
 * Full-screen modal for displaying week metadata on mobile.
 * Features:
 * - Full-screen modal on mobile (<600px)
 * - Display all metadata with larger typography
 * - Include ESPN link
 * - Include import details
 * - Close button / swipe to close
 * - Material-UI Dialog component
 * - Dark mode optimized
 */

import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Stack,
  Typography,
  Link,
  Divider,
  useTheme,
  useMediaQuery,
  IconButton,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import EventIcon from '@mui/icons-material/Event';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
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

export interface WeekMetadataModalProps {
  week: Week | null;
  open: boolean;
  onClose: () => void;
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

// Format timestamp as "Oct 5, 2:30 PM"
const formatTimestamp = (timestamp: string | null): string | null => {
  if (!timestamp) return null;
  try {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return timestamp;
  }
};

export const WeekMetadataModal: React.FC<WeekMetadataModalProps> = ({
  week,
  open,
  onClose,
}) => {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));

  if (!week) {
    return null;
  }

  const formattedDate = formatNFLDate(week.nfl_slate_date);
  const formattedTime = formatKickoffTime(week.metadata.kickoff_time);
  const formattedTimestamp = formatTimestamp(week.metadata.import_timestamp);

  return (
    <Dialog
      open={open}
      onClose={onClose}
      fullScreen={fullScreen}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          backgroundImage: 'none',
        },
      }}
    >
      {/* Header with close button */}
      <DialogTitle
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          paddingBottom: 1,
        }}
      >
        <Typography variant="h6" component="span">
          Week {week.week_number} Details
        </Typography>
        <IconButton
          onClick={onClose}
          size="small"
          sx={{
            color: 'inherit',
          }}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <Divider />

      <DialogContent sx={{ paddingTop: 3 }}>
        <Stack spacing={3}>
          {/* NFL Slate Information */}
          <Box>
            <Stack direction="row" spacing={2} alignItems="flex-start" marginBottom={2}>
              <EventIcon
                sx={{
                  fontSize: 28,
                  color: 'primary.main',
                  marginTop: 0.5,
                }}
              />
              <Stack spacing={0.5} flex={1}>
                <Typography
                  variant="overline"
                  color="text.secondary"
                  sx={{ fontSize: '0.75rem', fontWeight: 600 }}
                >
                  NFL Slate Date
                </Typography>
                <Typography variant="h6" sx={{ fontWeight: 500 }}>
                  {formattedDate}
                </Typography>
              </Stack>
            </Stack>

            <Stack direction="row" spacing={2} alignItems="flex-start">
              <AccessTimeIcon
                sx={{
                  fontSize: 28,
                  color: 'primary.main',
                  marginTop: 0.5,
                }}
              />
              <Stack spacing={0.5} flex={1}>
                <Typography
                  variant="overline"
                  color="text.secondary"
                  sx={{ fontSize: '0.75rem', fontWeight: 600 }}
                >
                  Kickoff Time
                </Typography>
                <Typography variant="h6" sx={{ fontWeight: 500 }}>
                  {formattedTime}
                </Typography>
              </Stack>
            </Stack>
          </Box>

          <Divider />

          {/* ESPN Schedule Link */}
          <Box>
            <Typography
              variant="overline"
              color="text.secondary"
              sx={{ fontSize: '0.75rem', fontWeight: 600, display: 'block', marginBottom: 1 }}
            >
              Schedule
            </Typography>
            <Link
              href={week.metadata.espn_link}
              target="_blank"
              rel="noopener noreferrer"
              sx={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 0.75,
                fontWeight: 500,
                color: 'primary.main',
                textDecoration: 'none',
                fontSize: '1rem',
                '&:hover': {
                  textDecoration: 'underline',
                },
              }}
            >
              View Full Schedule on ESPN
              <OpenInNewIcon sx={{ fontSize: 18 }} />
            </Link>
          </Box>

          <Divider />

          {/* Import Status */}
          <Box>
            <Typography
              variant="overline"
              color="text.secondary"
              sx={{ fontSize: '0.75rem', fontWeight: 600, display: 'block', marginBottom: 1.5 }}
            >
              Import Status
            </Typography>

            <Stack spacing={2}>
              <WeekImportStatusBadge
                importStatus={week.metadata.import_status}
                importCount={week.metadata.import_count}
                importTimestamp={week.metadata.import_timestamp}
                errorMessage={week.metadata.error_message}
              />

              {/* Import Details */}
              {week.metadata.import_status === 'imported' && (
                <Box>
                  {week.metadata.import_count > 0 && (
                    <Typography variant="body2" color="text.secondary" paragraph>
                      <strong>{week.metadata.import_count}</strong> players imported
                    </Typography>
                  )}
                  {formattedTimestamp && (
                    <Typography variant="body2" color="text.secondary">
                      Imported on <strong>{formattedTimestamp}</strong>
                    </Typography>
                  )}
                </Box>
              )}

              {week.metadata.import_status === 'error' && week.metadata.error_message && (
                <Box
                  sx={{
                    padding: 1.5,
                    backgroundColor: 'rgba(244, 67, 54, 0.1)',
                    borderRadius: 1,
                    border: '1px solid rgba(244, 67, 54, 0.2)',
                  }}
                >
                  <Typography variant="body2" color="error">
                    {week.metadata.error_message}
                  </Typography>
                </Box>
              )}

              {week.metadata.import_status === 'pending' && (
                <Typography variant="body2" color="text.secondary">
                  No data imported yet. You can import player pool data for this week.
                </Typography>
              )}
            </Stack>
          </Box>

          {/* Locked Indicator */}
          {week.is_locked && (
            <>
              <Divider />
              <Box
                sx={{
                  padding: 1.5,
                  backgroundColor: 'rgba(76, 175, 80, 0.1)',
                  borderRadius: 1,
                  border: '1px solid rgba(76, 175, 80, 0.2)',
                }}
              >
                <Typography variant="body2" color="success.main">
                  This week is locked and cannot be modified.
                </Typography>
              </Box>
            </>
          )}
        </Stack>
      </DialogContent>

      <Divider />

      {/* Action Buttons */}
      <DialogActions sx={{ padding: 2 }}>
        <Button onClick={onClose} variant="contained" fullWidth>
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default WeekMetadataModal;
