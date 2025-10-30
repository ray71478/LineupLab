/**
 * YearSelector Component
 *
 * Dropdown component for selecting the season year (2025-2030).
 * Triggers week loading on year change via useWeeks hook.
 * Displays loading state while fetching weeks for selected year.
 */

import React, { useCallback } from 'react';
import {
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  CircularProgress,
  Box,
} from '@mui/material';
import { useWeekStore } from '../../store/weekStore';
import { useWeeks } from '../../hooks/useWeeks';

export interface YearSelectorProps {
  currentYear: number;
  onYearChange?: (year: number) => void;
  availableYears?: number[];
}

export const YearSelector: React.FC<YearSelectorProps> = ({
  currentYear,
  onYearChange,
  availableYears = [2025, 2026, 2027, 2028, 2029, 2030],
}) => {
  const { setCurrentYear, setWeeks, setIsLoading, setError } = useWeekStore();
  const { isLoading } = useWeeks(currentYear);

  const handleYearChange = useCallback(
    (event: SelectChangeEvent<number>) => {
      const year = Number(event.target.value);
      setCurrentYear(year);
      setIsLoading(true);

      // Trigger useWeeks hook to fetch weeks for new year
      // The hook will automatically update the store via useEffect

      if (onYearChange) {
        onYearChange(year);
      }
    },
    [setCurrentYear, setIsLoading, onYearChange]
  );

  return (
    <FormControl sx={{ minWidth: 140 }} size="small" disabled={isLoading}>
      <InputLabel id="year-selector-label">Year</InputLabel>
      <Select
        labelId="year-selector-label"
        id="year-selector"
        value={currentYear}
        label="Year"
        onChange={handleYearChange}
        data-testid="year-selector"
        sx={{
          transition: 'all 0.2s ease-in-out',
        }}
        endAdornment={
          isLoading ? (
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                paddingRight: 1,
              }}
            >
              <CircularProgress size={20} />
            </Box>
          ) : undefined
        }
      >
        {availableYears.map((year) => (
          <MenuItem key={year} value={year}>
            {year}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
};

export default YearSelector;
