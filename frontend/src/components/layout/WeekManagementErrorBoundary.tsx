/**
 * Error Boundary for Week Management Feature
 *
 * Catches errors in week management components and displays
 * a user-friendly error message with recovery options.
 *
 * Usage:
 * <WeekManagementErrorBoundary>
 *   <WeekNavigation />
 * </WeekManagementErrorBoundary>
 */

import React, { ReactNode, ErrorInfo } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Stack,
  Alert,
  useTheme,
} from '@mui/material';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';

export interface WeekManagementErrorBoundaryProps {
  children: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class WeekManagementErrorBoundary extends React.Component<
  WeekManagementErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: WeekManagementErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error for debugging
    console.error('Week Management Error:', error, errorInfo);

    // Store error details
    this.setState({
      error,
      errorInfo,
    });

    // Call parent error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Log to monitoring service (e.g., Sentry) in production
    if (process.env.NODE_ENV === 'production') {
      // sentryClient.captureException(error, { contexts: { react: errorInfo } });
    }
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <Box
          data-testid="week-management-error-boundary"
          sx={{
            width: '100%',
            padding: 3,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '200px',
          }}
        >
          <Paper
            elevation={1}
            sx={{
              padding: 4,
              maxWidth: '600px',
              width: '100%',
              backgroundColor: 'rgba(244, 67, 54, 0.05)',
              borderLeft: '4px solid #f44336',
            }}
          >
            {/* Error Icon and Title */}
            <Stack spacing={3}>
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 2,
                }}
              >
                <ErrorOutlineIcon
                  sx={{
                    fontSize: 32,
                    color: '#f44336',
                  }}
                />
                <Typography variant="h6" component="h2">
                  Week Management Error
                </Typography>
              </Box>

              {/* Error Description */}
              <Alert severity="error" sx={{ width: '100%' }}>
                <Typography variant="body2">
                  {this.state.error?.message ||
                    'An unexpected error occurred while loading week management features.'}
                </Typography>
              </Alert>

              {/* Error Details (Development Only) */}
              {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
                <Box
                  sx={{
                    backgroundColor: 'rgba(0, 0, 0, 0.05)',
                    padding: 2,
                    borderRadius: 1,
                    maxHeight: '200px',
                    overflow: 'auto',
                    fontFamily: 'monospace',
                    fontSize: '0.75rem',
                  }}
                >
                  <Typography variant="caption" component="pre">
                    {this.state.errorInfo.componentStack}
                  </Typography>
                </Box>
              )}

              {/* Recovery Actions */}
              <Stack direction="row" spacing={2}>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={this.handleReset}
                  fullWidth
                >
                  Try Again
                </Button>
                <Button
                  variant="outlined"
                  color="primary"
                  onClick={this.handleReload}
                  fullWidth
                >
                  Reload Page
                </Button>
              </Stack>

              {/* Additional Help Text */}
              <Typography variant="caption" color="text.secondary">
                If the problem persists, please refresh the page or contact support.
              </Typography>
            </Stack>
          </Paper>
        </Box>
      );
    }

    return this.props.children;
  }
}

export default WeekManagementErrorBoundary;
