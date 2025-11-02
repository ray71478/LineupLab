/**
 * ModeSelector Component
 *
 * Toggle button group for switching between Main Slate and Showdown contest modes.
 * Integrates with global mode state via useModeStore.
 *
 * Features:
 * - Toggle button group with "Main Slate" | "Showdown"
 * - Active state with orange accent (#ff6b35) matching design system
 * - Responsive: Horizontal on desktop, adjusts for mobile
 * - Keyboard navigation support (Tab, Enter)
 * - Screen reader accessible with ARIA labels
 * - Smooth transitions and hover states
 * - Optimistic UI updates with loading indicators (Task 15.4)
 */

import React, { useCallback, useState } from 'react';
import { Box, ButtonGroup, Button, useMediaQuery, useTheme, CircularProgress } from '@mui/material';
import { useModeStore, ContestMode } from '../../store/modeStore';

export interface ModeSelectorProps {
  // Component uses useModeStore internally, no props needed
  // Props can be added later for custom behavior if needed
}

export const ModeSelector: React.FC<ModeSelectorProps> = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm')); // <600px

  const { mode, setMode } = useModeStore();
  const [isSwitching, setIsSwitching] = useState(false);

  // Handle mode change with optimistic UI update (Task 15.4)
  const handleModeChange = useCallback(
    async (newMode: ContestMode) => {
      if (newMode !== mode) {
        // Optimistic UI update - show loading state immediately
        setIsSwitching(true);

        // Update mode (this triggers data refetch in hooks)
        setMode(newMode);

        // Performance monitoring (Task 15.5)
        const startTime = performance.now();

        // Allow UI to update optimistically
        // Data fetch happens asynchronously in hooks
        requestAnimationFrame(() => {
          const elapsed = performance.now() - startTime;
          console.log(`[PERFORMANCE] Mode switch latency: ${elapsed.toFixed(2)}ms`);

          // Hide loading state after brief delay
          setTimeout(() => {
            setIsSwitching(false);
          }, 200); // Minimum 200ms loading indicator for UX
        });
      }
    },
    [mode, setMode]
  );

  // Handle keyboard Enter key
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLButtonElement>, targetMode: ContestMode) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        handleModeChange(targetMode);
      }
    },
    [handleModeChange]
  );

  return (
    <Box
      data-testid="mode-selector"
      aria-label="Select contest mode"
      sx={{
        display: 'flex',
        alignItems: 'center',
        position: 'relative',
      }}
    >
      <ButtonGroup
        variant="contained"
        disabled={isSwitching}
        sx={{
          boxShadow: 'none',
          '& .MuiButtonGroup-grouped': {
            minWidth: { xs: 100, sm: 120 },
            '&:not(:last-of-type)': {
              borderRight: '1px solid rgba(255, 255, 255, 0.1)',
            },
          },
        }}
      >
        {/* Main Slate Button */}
        <Button
          data-testid="mode-button-main"
          aria-pressed={mode === 'main'}
          onClick={() => handleModeChange('main')}
          onKeyDown={(e) => handleKeyDown(e, 'main')}
          disabled={isSwitching}
          sx={{
            px: { xs: 2, sm: 2.5 },
            py: 1,
            fontSize: { xs: '0.8125rem', sm: '0.875rem' },
            fontWeight: mode === 'main' ? 600 : 500,
            textTransform: 'none',
            borderRadius: '10px 0 0 10px',
            backgroundColor: mode === 'main' ? '#ff6b35' : 'rgba(255, 255, 255, 0.03)',
            color: mode === 'main' ? '#ffffff' : 'rgba(255, 255, 255, 0.7)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
            opacity: isSwitching ? 0.6 : 1,
            '&:hover': {
              backgroundColor: mode === 'main' ? '#e05e2e' : 'rgba(255, 255, 255, 0.08)',
              color: mode === 'main' ? '#ffffff' : 'rgba(255, 255, 255, 0.9)',
              borderColor: 'rgba(255, 255, 255, 0.15)',
              transform: isSwitching ? 'none' : 'translateY(-1px)',
              boxShadow:
                mode === 'main'
                  ? '0 4px 12px rgba(255, 107, 53, 0.3)'
                  : '0 2px 8px rgba(0, 0, 0, 0.2)',
            },
            '&:active': {
              transform: 'translateY(0)',
            },
            '&:focus-visible': {
              outline: '2px solid #ff6b35',
              outlineOffset: '2px',
            },
            '&:disabled': {
              backgroundColor: mode === 'main' ? '#ff6b35' : 'rgba(255, 255, 255, 0.03)',
              color: mode === 'main' ? '#ffffff' : 'rgba(255, 255, 255, 0.7)',
            },
          }}
        >
          Main Slate
        </Button>

        {/* Showdown Button */}
        <Button
          data-testid="mode-button-showdown"
          aria-pressed={mode === 'showdown'}
          onClick={() => handleModeChange('showdown')}
          onKeyDown={(e) => handleKeyDown(e, 'showdown')}
          disabled={isSwitching}
          sx={{
            px: { xs: 2, sm: 2.5 },
            py: 1,
            fontSize: { xs: '0.8125rem', sm: '0.875rem' },
            fontWeight: mode === 'showdown' ? 600 : 500,
            textTransform: 'none',
            borderRadius: '0 10px 10px 0',
            backgroundColor: mode === 'showdown' ? '#ff6b35' : 'rgba(255, 255, 255, 0.03)',
            color: mode === 'showdown' ? '#ffffff' : 'rgba(255, 255, 255, 0.7)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderLeft: 'none',
            transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
            opacity: isSwitching ? 0.6 : 1,
            '&:hover': {
              backgroundColor: mode === 'showdown' ? '#e05e2e' : 'rgba(255, 255, 255, 0.08)',
              color: mode === 'showdown' ? '#ffffff' : 'rgba(255, 255, 255, 0.9)',
              borderColor: 'rgba(255, 255, 255, 0.15)',
              transform: isSwitching ? 'none' : 'translateY(-1px)',
              boxShadow:
                mode === 'showdown'
                  ? '0 4px 12px rgba(255, 107, 53, 0.3)'
                  : '0 2px 8px rgba(0, 0, 0, 0.2)',
            },
            '&:active': {
              transform: 'translateY(0)',
            },
            '&:focus-visible': {
              outline: '2px solid #ff6b35',
              outlineOffset: '2px',
            },
            '&:disabled': {
              backgroundColor: mode === 'showdown' ? '#ff6b35' : 'rgba(255, 255, 255, 0.03)',
              color: mode === 'showdown' ? '#ffffff' : 'rgba(255, 255, 255, 0.7)',
            },
          }}
        >
          Showdown
        </Button>
      </ButtonGroup>

      {/* Loading indicator (Task 15.4) */}
      {isSwitching && (
        <CircularProgress
          size={20}
          sx={{
            position: 'absolute',
            right: -30,
            color: '#ff6b35',
          }}
          aria-label="Switching mode"
        />
      )}
    </Box>
  );
};

export default ModeSelector;
