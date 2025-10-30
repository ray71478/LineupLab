/**
 * WeekSelector Component
 *
 * Clean dropdown component for selecting the current week (1-18).
 * Uses Zustand global state for persistence across pages.
 * Factory.ai inspired design with orange accents.
 *
 * Features:
 * - Material-UI Select dropdown
 * - Display all weeks with status badges
 * - Highlight current week with orange glow
 * - Auto-scroll to current week when dropdown opens
 * - Smooth animations
 * - Tooltip on hover showing metadata
 * - Keyboard navigation support
 */

import React, { useCallback, useRef, useEffect, useState } from 'react';
import {
  FormControl,
  Select,
  MenuItem,
  SelectChangeEvent,
  Box,
  Tooltip,
  Typography,
} from '@mui/material';
import { useWeekStore, Week } from '../../store/weekStore';
import { WeekStatusBadge } from '../weeks/WeekStatusBadge';

export interface WeekSelectorProps {
  onWeekChange?: (week: number) => void;
  showMetadata?: boolean;
}

export const WeekSelector: React.FC<WeekSelectorProps> = ({
  onWeekChange,
  showMetadata = true,
}) => {
  const { currentWeek, setCurrentWeek, weeks } = useWeekStore();
  const selectRef = useRef<any>(null);
  const [open, setOpen] = useState(false);

  // Format metadata for tooltip
  const formatTooltip = (week: Week): string => {
    const lines: string[] = [];

    if (week.metadata) {
      lines.push(`Kickoff: ${week.metadata.kickoff_time}`);

      if (week.metadata.import_status === 'imported') {
        lines.push(`Imported: ${week.metadata.import_count} players`);
        if (week.metadata.import_timestamp) {
          const date = new Date(week.metadata.import_timestamp);
          lines.push(`Last import: ${date.toLocaleDateString()}`);
        }
      } else if (week.metadata.import_status === 'error') {
        lines.push('Import Error');
      }
    }

    return lines.join('\n');
  };

  const handleWeekChange = useCallback(
    (event: SelectChangeEvent<number>) => {
      const week = Number(event.target.value);
      setCurrentWeek(week);

      if (onWeekChange) {
        onWeekChange(week);
      }
    },
    [setCurrentWeek, onWeekChange]
  );

  // Handle keyboard navigation
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      if (!open || weeks.length === 0 || !currentWeek) return;

      const currentIndex = weeks.findIndex((w) => w.week_number === currentWeek);

      switch (e.key) {
        case 'ArrowRight':
        case 'ArrowDown':
          e.preventDefault();
          if (currentIndex < weeks.length - 1) {
            setCurrentWeek(weeks[currentIndex + 1].week_number);
          }
          break;

        case 'ArrowLeft':
        case 'ArrowUp':
          e.preventDefault();
          if (currentIndex > 0) {
            setCurrentWeek(weeks[currentIndex - 1].week_number);
          }
          break;

        case 'Home':
          e.preventDefault();
          setCurrentWeek(1);
          break;

        case 'End':
          e.preventDefault();
          setCurrentWeek(18);
          break;

        case 'Escape':
          e.preventDefault();
          setOpen(false);
          break;

        default:
          break;
      }
    },
    [open, weeks, currentWeek, setCurrentWeek]
  );

  // Auto-scroll to current week on dropdown open
  useEffect(() => {
    if (open && selectRef.current && currentWeek) {
      // The MUI Select automatically handles scrolling to selected value
    }
  }, [open, currentWeek]);

  return (
    <FormControl sx={{ minWidth: { xs: 140, sm: 160 } }} size="small">
      <Select
        ref={selectRef}
        labelId="week-selector-label"
        id="week-selector"
        value={currentWeek || 0}
        onChange={handleWeekChange}
        onKeyDown={handleKeyDown}
        onOpen={() => setOpen(true)}
        onClose={() => setOpen(false)}
        data-testid="week-selector"
        open={open}
        displayEmpty
        sx={{
          transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
          bgcolor: 'rgba(255, 255, 255, 0.03)',
          color: '#ffffff',
          fontWeight: 500,
          fontSize: { xs: '0.875rem', sm: '0.9375rem' },
          borderRadius: '10px',
          '& .MuiSelect-select': {
            fontWeight: 500,
            py: 1.25,
            px: 1.5,
          },
          '& .MuiSelect-icon': {
            color: '#a0a0a0',
            transition: 'color 0.2s ease',
          },
          '&:hover .MuiSelect-icon': {
            color: '#ffffff',
          },
          '& .MuiOutlinedInput-notchedOutline': {
            borderColor: 'rgba(255, 255, 255, 0.08)',
          },
          '&:hover .MuiOutlinedInput-notchedOutline': {
            borderColor: 'rgba(255, 255, 255, 0.15)',
          },
          '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
            borderColor: '#ff6b35',
          },
        }}
        MenuProps={{
          PaperProps: {
            sx: {
              bgcolor: '#0a0a0a',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '12px',
              maxHeight: 400,
              mt: 1,
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
              '& .MuiMenuItem-root': {
                color: '#ffffff',
                fontWeight: 500,
                fontSize: '0.9375rem',
                borderRadius: '8px',
                mx: 1,
                my: 0.5,
              },
              '& .MuiMenuItem-root.Mui-selected': {
                backgroundColor: 'rgba(255, 107, 53, 0.12)',
                color: '#ff6b35',
              },
              '& .MuiMenuItem-root.Mui-selected:hover': {
                backgroundColor: 'rgba(255, 107, 53, 0.2)',
              },
              '& .MuiMenuItem-root:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.05)',
              },
            }
          }
        }}
      >
        {weeks.map((week) => {
          const isCurrentWeek = week.week_number === currentWeek;
          const tooltip = showMetadata ? formatTooltip(week) : '';

          return (
            <MenuItem
              key={week.id}
              value={week.week_number}
              data-testid={`week-menu-item-${week.week_number}`}
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: 1.5,
                padding: '12px 16px',
                transition: 'all 0.15s ease',
                backgroundColor: isCurrentWeek ? 'rgba(255, 107, 53, 0.12)' : 'transparent',
                '&:hover': {
                  backgroundColor: isCurrentWeek
                    ? 'rgba(255, 107, 53, 0.2)'
                    : 'rgba(255, 255, 255, 0.05)',
                },
              }}
            >
              <Tooltip title={tooltip} arrow placement="right">
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1.5,
                    flex: 1,
                  }}
                >
                  <Typography
                    variant="body2"
                    sx={{
                      fontWeight: isCurrentWeek ? 600 : 500,
                      minWidth: 50,
                      color: isCurrentWeek ? '#ff6b35' : '#ffffff',
                      fontSize: '0.9375rem',
                    }}
                  >
                    Week {week.week_number}
                  </Typography>

                  {showMetadata && (
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      <WeekStatusBadge
                        status={week.status}
                        importStatus={week.metadata?.import_status}
                        isCurrentWeek={isCurrentWeek}
                        compact={true}
                      />
                    </Box>
                  )}

                  {week.is_locked && (
                    <Typography
                      variant="caption"
                      sx={{
                        color: '#666666',
                        fontSize: '0.6875rem',
                        marginLeft: 'auto',
                        fontWeight: 500,
                        textTransform: 'uppercase',
                        letterSpacing: '0.05em',
                      }}
                    >
                      locked
                    </Typography>
                  )}
                </Box>
              </Tooltip>
            </MenuItem>
          );
        })}
      </Select>
    </FormControl>
  );
};

export default WeekSelector;
