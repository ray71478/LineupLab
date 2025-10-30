/**
 * Material-UI Dark Theme Configuration
 * Inspired by Factory.ai design system
 *
 * Color Palette:
 * - Background: #000000 (pure black)
 * - Paper: #0a0a0a (near black for cards)
 * - Primary/Accent: #ff6b35 (vibrant orange)
 * - Text Primary: #ffffff (pure white)
 * - Text Secondary: #a0a0a0 (light gray)
 * - Borders: rgba(255, 255, 255, 0.1) (subtle white)
 *
 * Typography: Inter font family (modern, clean)
 * NO EMOJIS in any text content or typography
 */

import { createTheme } from '@mui/material/styles';

export const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    background: {
      default: '#000000',
      paper: '#0a0a0a',
    },
    primary: {
      main: '#ff6b35',
      light: '#ff8c5e',
      dark: '#e65a2b',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#ff6b35',
      light: '#ff8c5e',
      dark: '#e65a2b',
      contrastText: '#ffffff',
    },
    text: {
      primary: '#ffffff',
      secondary: '#a0a0a0',
      disabled: '#666666',
    },
    divider: 'rgba(255, 255, 255, 0.1)',
    action: {
      hover: 'rgba(255, 107, 53, 0.08)',
      selected: 'rgba(255, 107, 53, 0.12)',
      disabled: 'rgba(255, 255, 255, 0.3)',
      disabledBackground: 'rgba(255, 255, 255, 0.12)',
    },
    error: {
      main: '#f44336',
    },
    success: {
      main: '#4caf50',
    },
  },
  typography: {
    fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    h1: {
      fontWeight: 800,
      fontSize: '5.5rem',
      lineHeight: 1.1,
      letterSpacing: '-0.03em',
    },
    h2: {
      fontWeight: 700,
      fontSize: '3rem',
      lineHeight: 1.2,
      letterSpacing: '-0.02em',
    },
    h3: {
      fontWeight: 600,
      fontSize: '2rem',
      lineHeight: 1.3,
      letterSpacing: '-0.01em',
    },
    h4: {
      fontWeight: 600,
      fontSize: '1.75rem',
      lineHeight: 1.3,
      letterSpacing: '-0.01em',
    },
    h5: {
      fontWeight: 600,
      fontSize: '1.5rem',
      lineHeight: 1.4,
      letterSpacing: '0',
    },
    h6: {
      fontWeight: 600,
      fontSize: '1.125rem',
      lineHeight: 1.4,
      letterSpacing: '-0.01em',
    },
    body1: {
      fontSize: '1.0625rem',
      lineHeight: 1.7,
      letterSpacing: '0',
      fontWeight: 300,
    },
    body2: {
      fontSize: '0.9375rem',
      lineHeight: 1.7,
      letterSpacing: '0',
      fontWeight: 300,
    },
    button: {
      textTransform: 'none',
      fontWeight: 500,
      letterSpacing: '0.02em',
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#000000',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          boxShadow: 'none',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundColor: '#0a0a0a',
          backgroundImage: 'none',
          border: '1px solid rgba(255, 255, 255, 0.1)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
          borderRadius: 8,
        },
        contained: {
          backgroundColor: '#ff6b35',
          color: '#ffffff',
          boxShadow: 'none',
          '&:hover': {
            backgroundColor: '#e65a2b',
            boxShadow: '0 4px 12px rgba(255, 107, 53, 0.3)',
          },
          '&:active': {
            boxShadow: 'none',
          },
        },
        outlined: {
          borderColor: 'rgba(255, 255, 255, 0.2)',
          color: '#ffffff',
          '&:hover': {
            borderColor: '#ff6b35',
            backgroundColor: 'rgba(255, 107, 53, 0.08)',
          },
        },
        text: {
          color: '#ff6b35',
          '&:hover': {
            backgroundColor: 'rgba(255, 107, 53, 0.08)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundColor: '#0a0a0a',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: 12,
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            borderColor: '#ff6b35',
            transform: 'translateY(-4px)',
            boxShadow: '0 8px 24px rgba(255, 107, 53, 0.15)',
          },
        },
      },
    },
    MuiSelect: {
      styleOverrides: {
        root: {
          backgroundColor: '#0a0a0a',
          borderRadius: 8,
          '& .MuiOutlinedInput-notchedOutline': {
            borderColor: 'rgba(255, 255, 255, 0.2)',
          },
          '&:hover .MuiOutlinedInput-notchedOutline': {
            borderColor: 'rgba(255, 255, 255, 0.3)',
          },
          '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
            borderColor: '#ff6b35',
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            backgroundColor: '#0a0a0a',
            borderRadius: 8,
            '& fieldset': {
              borderColor: 'rgba(255, 255, 255, 0.2)',
            },
            '&:hover fieldset': {
              borderColor: 'rgba(255, 255, 255, 0.3)',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#ff6b35',
            },
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          backgroundColor: 'rgba(255, 255, 255, 0.08)',
          color: '#ffffff',
          borderRadius: 6,
          '&:hover': {
            backgroundColor: 'rgba(255, 107, 53, 0.15)',
          },
        },
        filled: {
          backgroundColor: 'rgba(255, 107, 53, 0.15)',
          color: '#ff6b35',
          fontWeight: 500,
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          border: '1px solid',
        },
        standardError: {
          backgroundColor: 'rgba(244, 67, 54, 0.1)',
          borderColor: 'rgba(244, 67, 54, 0.3)',
        },
        standardSuccess: {
          backgroundColor: 'rgba(76, 175, 80, 0.1)',
          borderColor: 'rgba(76, 175, 80, 0.3)',
        },
        standardInfo: {
          backgroundColor: 'rgba(255, 107, 53, 0.1)',
          borderColor: 'rgba(255, 107, 53, 0.3)',
        },
      },
    },
    MuiLinearProgress: {
      styleOverrides: {
        root: {
          backgroundColor: 'rgba(255, 255, 255, 0.1)',
          borderRadius: 4,
        },
        bar: {
          backgroundColor: '#ff6b35',
        },
      },
    },
    MuiCircularProgress: {
      styleOverrides: {
        root: {
          color: '#ff6b35',
        },
      },
    },
  },
});
