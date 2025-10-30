/**
 * Dark Mode Optimization Utilities
 *
 * Ensures dark mode is properly optimized for:
 * - Eye comfort (no harsh colors)
 * - Proper contrast ratios (WCAG AA)
 * - Reduced power consumption (especially on OLED)
 * - Professional appearance
 *
 * Color palette follows Material Design dark theme specifications
 */

import { createTheme } from '@mui/material/styles';

/**
 * Material Design Dark Mode Colors
 * Reference: https://material.io/design/color/the-color-system.html
 */
export const DARK_THEME_COLORS = {
  // Background and Surface colors
  background: '#121212',        // Very dark base
  surface: '#1e1e1e',          // Slightly lighter for elevation
  surfaceVariant: '#424242',   // For additional elevation

  // Text colors
  textPrimary: '#ffffff',      // Primary text
  textSecondary: '#b0bec5',    // Secondary text (reduced brightness)
  textTertiary: '#78909c',     // Tertiary text (even dimmer)

  // Component colors
  divider: '#424242',          // Subtle dividers
  outlineVariant: '#5f5f5f',   // Component outlines

  // Status colors (muted for dark mode)
  success: '#4caf50',          // Material Green
  warning: '#ff9800',          // Material Orange
  error: '#f44336',            // Material Red
  info: '#2196f3',             // Material Blue

  // Accent colors
  primary: '#1976d2',          // Material Blue
  secondary: '#dc004e',        // Material Pink
};

/**
 * Dark mode theme configuration for Material-UI
 */
export const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    background: {
      default: DARK_THEME_COLORS.background,
      paper: DARK_THEME_COLORS.surface,
    },
    primary: {
      main: DARK_THEME_COLORS.primary,
    },
    secondary: {
      main: DARK_THEME_COLORS.secondary,
    },
    success: {
      main: DARK_THEME_COLORS.success,
    },
    warning: {
      main: DARK_THEME_COLORS.warning,
    },
    error: {
      main: DARK_THEME_COLORS.error,
    },
    info: {
      main: DARK_THEME_COLORS.info,
    },
    text: {
      primary: DARK_THEME_COLORS.textPrimary,
      secondary: DARK_THEME_COLORS.textSecondary,
    },
    divider: DARK_THEME_COLORS.divider,
  },
  components: {
    // AppBar elevation and background
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: DARK_THEME_COLORS.background,
          // Subtle shadow for elevation
          boxShadow: '0px 1px 4px rgba(0, 0, 0, 0.5)',
        },
      },
    },

    // Paper elevation levels
    MuiPaper: {
      styleOverrides: {
        elevation1: {
          backgroundColor: DARK_THEME_COLORS.surface,
          boxShadow: '0px 1px 4px rgba(0, 0, 0, 0.5)',
        },
        elevation2: {
          backgroundColor: DARK_THEME_COLORS.surface,
          boxShadow: '0px 2px 8px rgba(0, 0, 0, 0.6)',
        },
      },
    },

    // Dialog styling
    MuiDialog: {
      styleOverrides: {
        paper: {
          backgroundColor: DARK_THEME_COLORS.surface,
          backgroundImage: 'none', // Remove Material Design pattern
        },
      },
    },

    // Select dropdown
    MuiSelect: {
      styleOverrides: {
        root: {
          backgroundColor: DARK_THEME_COLORS.surfaceVariant,
          color: DARK_THEME_COLORS.textPrimary,
          '&:hover': {
            backgroundColor: '#565656',
          },
        },
      },
    },

    // Typography default colors
    MuiTypography: {
      defaultProps: {
        color: DARK_THEME_COLORS.textPrimary,
      },
    },

    // Link styling
    MuiLink: {
      styleOverrides: {
        root: {
          color: DARK_THEME_COLORS.primary,
          '&:hover': {
            opacity: 0.8,
          },
        },
      },
    },

    // Button styling
    MuiButton: {
      styleOverrides: {
        contained: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0px 2px 8px rgba(0, 0, 0, 0.3)',
          },
        },
      },
    },
  },
});

/**
 * Contrast ratio validation utility
 * Ensures WCAG AA compliance
 */
export const ContrastValidator = {
  /**
   * Check contrast ratio between two colors
   * WCAG AA requires 4.5:1 for normal text, 3:1 for large text
   * WCAG AAA requires 7:1 for normal text, 4.5:1 for large text
   */
  checkContrast: (foreground: string, background: string): {
    ratio: number;
    compliesAA: boolean;
    compliesAAA: boolean;
  } => {
    // Convert hex to RGB
    const rgb1 = parseInt(foreground.slice(1), 16);
    const rgb2 = parseInt(background.slice(1), 16);

    const r1 = (rgb1 >> 16) & 0xff;
    const g1 = (rgb1 >> 8) & 0xff;
    const b1 = rgb1 & 0xff;

    const r2 = (rgb2 >> 16) & 0xff;
    const g2 = (rgb2 >> 8) & 0xff;
    const b2 = rgb2 & 0xff;

    // Calculate relative luminance
    const lum1 = (0.299 * r1 + 0.587 * g1 + 0.114 * b1) / 255;
    const lum2 = (0.299 * r2 + 0.587 * g2 + 0.114 * b2) / 255;

    const lighter = Math.max(lum1, lum2);
    const darker = Math.min(lum1, lum2);

    const ratio = (lighter + 0.05) / (darker + 0.05);

    return {
      ratio: parseFloat(ratio.toFixed(2)),
      compliesAA: ratio >= 4.5,
      compliesAAA: ratio >= 7,
    };
  },

  /**
   * Validate all theme colors meet contrast requirements
   */
  validateTheme: (): {
    passed: boolean;
    results: Array<{
      colors: string;
      ratio: number;
      compliesAA: boolean;
    }>;
  } => {
    const results = [];
    const tests = [
      {
        name: 'Primary text on background',
        fg: DARK_THEME_COLORS.textPrimary,
        bg: DARK_THEME_COLORS.background,
      },
      {
        name: 'Secondary text on background',
        fg: DARK_THEME_COLORS.textSecondary,
        bg: DARK_THEME_COLORS.background,
      },
      {
        name: 'Primary on surface',
        fg: DARK_THEME_COLORS.primary,
        bg: DARK_THEME_COLORS.surface,
      },
    ];

    let allPassed = true;

    tests.forEach((test) => {
      const check = ContrastValidator.checkContrast(test.fg, test.bg);
      results.push({
        colors: test.name,
        ratio: check.ratio,
        compliesAA: check.compliesAA,
      });

      if (!check.compliesAA) {
        allPassed = false;
      }
    });

    return { passed: allPassed, results };
  },
};

/**
 * Dark mode detection utility
 */
export const DarkModeDetector = {
  /**
   * Check if system prefers dark mode
   */
  prefersDarkMode: (): boolean => {
    if (typeof window === 'undefined') return false;
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  },

  /**
   * Watch for system dark mode changes
   */
  watchDarkMode: (callback: (isDark: boolean) => void): (() => void) => {
    if (typeof window === 'undefined') return () => {};

    const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const listener = (e: MediaQueryListEvent) => callback(e.matches);

    darkModeQuery.addEventListener('change', listener);

    return () => darkModeQuery.removeEventListener('change', listener);
  },
};

/**
 * Optimization checklist for dark mode
 */
export const DarkModeChecklist = [
  '[ ] Background color: #121212 (very dark)',
  '[ ] Surface elevation: subtle shadows only',
  '[ ] Text primary: #ffffff (full white)',
  '[ ] Text secondary: #b0bec5 (reduced brightness)',
  '[ ] Divider: #424242 (subtle)',
  '[ ] No bright accent colors causing strain',
  '[ ] All contrast ratios meet WCAG AA (4.5:1)',
  '[ ] Links color: #1976d2 (subdued blue)',
  '[ ] Status colors muted (not harsh)',
  '[ ] Tested in low light conditions',
  '[ ] Icon colors match text contrast',
  '[ ] Tooltip backgrounds dark',
  '[ ] Modal backdrop semi-transparent',
];

/**
 * Power efficiency optimization (OLED screens)
 * Pure black (#000000) uses 0% power on OLED
 * But use #121212 for readability vs pure black
 */
export const OLEDOptimization = {
  considerOLED: true,
  reasoning: 'Dark mode reduces power consumption on OLED screens',
  implementation: 'Use #121212 instead of pure #000000 for better readability',
};
