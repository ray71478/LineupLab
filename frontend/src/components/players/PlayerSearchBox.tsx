/**
 * PlayerSearchBox Component
 *
 * Search input for filtering players by name.
 * Implements debounce to prevent excessive filtering.
 */

import React, { useCallback, useState, useEffect } from 'react';
import {
  TextField,
  InputAdornment,
  IconButton,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import ClearIcon from '@mui/icons-material/Clear';

export interface PlayerSearchBoxProps {
  onSearch: (query: string) => void;
  placeholder?: string;
  debounceMs?: number;
}

export const PlayerSearchBox: React.FC<PlayerSearchBoxProps> = ({
  onSearch,
  placeholder = 'Search player by name...',
  debounceMs = 300,
}) => {
  const [searchInput, setSearchInput] = useState('');
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      onSearch(searchInput);
    }, debounceMs);

    return () => clearTimeout(timer);
  }, [searchInput, onSearch, debounceMs]);

  const handleInputChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      setSearchInput(event.target.value);
    },
    []
  );

  const handleClear = useCallback(() => {
    setSearchInput('');
  }, []);

  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (event.key === 'Escape') {
      setSearchInput('');
    }
  }, []);

  return (
    <TextField
      fullWidth
      size="small"
      placeholder={placeholder}
      value={searchInput}
      onChange={handleInputChange}
      onKeyDown={handleKeyDown}
      variant="outlined"
      inputProps={{
        'aria-label': 'Search players',
        spellCheck: 'false',
      }}
      InputProps={{
        startAdornment: (
          <InputAdornment position="start">
            <SearchIcon
              sx={{
                color: '#ff8c42',
                fontSize: isMobile ? '1.25rem' : '1.5rem',
              }}
            />
          </InputAdornment>
        ),
        endAdornment: searchInput && (
          <InputAdornment position="end">
            <IconButton
              size="small"
              onClick={handleClear}
              edge="end"
              aria-label="clear search"
              sx={{
                color: '#ff8c42',
                '&:hover': {
                  backgroundColor: 'rgba(255, 140, 66, 0.1)',
                },
              }}
            >
              <ClearIcon fontSize="small" />
            </IconButton>
          </InputAdornment>
        ),
      }}
      sx={{
        backgroundColor: 'rgba(255, 255, 255, 0.05)',
        borderRadius: '6px',
        '& .MuiOutlinedInput-root': {
          color: '#ffffff',
          fontSize: isMobile ? '0.875rem' : '1rem',
          padding: isMobile ? '8px 12px' : '12px 16px',
          '& fieldset': {
            borderColor: 'rgba(255, 255, 255, 0.1)',
          },
          '&:hover fieldset': {
            borderColor: 'rgba(255, 255, 255, 0.2)',
          },
          '&.Mui-focused fieldset': {
            borderColor: '#ff8c42',
            boxShadow: '0 0 8px rgba(255, 140, 66, 0.3)',
          },
        },
        '& .MuiOutlinedInput-input::placeholder': {
          color: '#9ca3af',
          opacity: 1,
        },
      }}
    />
  );
};

export default PlayerSearchBox;
