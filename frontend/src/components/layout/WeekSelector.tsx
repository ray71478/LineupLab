/**
 * WeekSelector Component
 *
 * Dropdown component for selecting the current week (1-18).
 * Uses Zustand global state for persistence across pages.
 * Displays in the header and allows users to change the active week.
 */

import React from 'react';
import { FormControl, InputLabel, Select, MenuItem, SelectChangeEvent } from '@mui/material';
import { useWeekStore } from '../../store/weekStore';

export interface WeekSelectorProps {
  // No props - uses Zustand global state
}

export const WeekSelector: React.FC<WeekSelectorProps> = () => {
  const { currentWeek, setCurrentWeek } = useWeekStore();

  const handleWeekChange = (event: SelectChangeEvent<number>) => {
    setCurrentWeek(Number(event.target.value));
  };

  return (
    <FormControl sx={{ minWidth: 140 }} size="small">
      <InputLabel id="week-selector-label">Week</InputLabel>
      <Select
        labelId="week-selector-label"
        id="week-selector"
        value={currentWeek}
        label="Week"
        onChange={handleWeekChange}
        data-testid="week-selector"
      >
        {Array.from({ length: 18 }, (_, i) => i + 1).map((week) => (
          <MenuItem key={week} value={week}>
            Week {week}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
};

export default WeekSelector;
