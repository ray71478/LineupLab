/**
 * CalibrationAdmin Component
 *
 * Modal/dialog component for managing calibration factors per position.
 * Opens when CalibrationStatusChip is clicked.
 *
 * Features per spec lines 65-76:
 * - Week selector dropdown (which week to configure)
 * - Position tabs/selector (QB, RB, WR, TE, K, DST)
 * - Input fields for Floor, Median, Ceiling adjustments (-50% to +50%)
 * - Active/Inactive toggle per week
 * - Save/Cancel/Reset buttons
 * - Preview section using CalibrationPreview component
 *
 * Validation: Percentage range limits (-50 to +50)
 * Accessibility: Full keyboard navigation, ARIA attributes, screen reader support
 * Responsive: Mobile/Tablet/Desktop layouts
 */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Stack,
  Tabs,
  Tab,
  TextField,
  FormControlLabel,
  Switch,
  Typography,
  IconButton,
  Divider,
  CircularProgress,
  Alert,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import SaveIcon from '@mui/icons-material/Save';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import {
  useCalibrations,
  useBatchUpdateCalibrations,
  useResetCalibrations,
  CalibrationFactor,
  CalibrationUpdateRequest,
} from '../../hooks/useCalibration';
import { CalibrationPreview } from './CalibrationPreview';

export interface CalibrationAdminProps {
  open: boolean;
  onClose: () => void;
  weekId: number | null;
}

// Position list
const POSITIONS = ['QB', 'RB', 'WR', 'TE', 'K', 'DST'];

// Sample values for preview (typical median projections by position)
const SAMPLE_VALUES: Record<string, number> = {
  QB: 18.5,
  RB: 12.0,
  WR: 11.5,
  TE: 9.0,
  K: 8.5,
  DST: 7.5,
};

/**
 * CalibrationAdmin Component
 */
export const CalibrationAdmin: React.FC<CalibrationAdminProps> = ({
  open,
  onClose,
  weekId,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));

  // Current selected position tab
  const [selectedPosition, setSelectedPosition] = useState<string>('QB');

  // Local state for calibration factors (editable)
  const [localCalibrations, setLocalCalibrations] = useState<Record<string, CalibrationFactor>>(
    {}
  );

  // Validation errors
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  // Fetch calibration data
  const { data: calibrations, isLoading, error } = useCalibrations(weekId);

  // Mutations
  const batchUpdate = useBatchUpdateCalibrations();
  const reset = useResetCalibrations();

  // Initialize local calibrations when data loads
  useEffect(() => {
    if (calibrations && calibrations.length > 0) {
      const calibrationMap: Record<string, CalibrationFactor> = {};
      calibrations.forEach((cal) => {
        calibrationMap[cal.position] = cal;
      });
      setLocalCalibrations(calibrationMap);
    } else if (calibrations && calibrations.length === 0) {
      // Initialize with default values if no calibrations exist
      const defaultCalibrations: Record<string, CalibrationFactor> = {};
      POSITIONS.forEach((pos) => {
        defaultCalibrations[pos] = {
          position: pos,
          floor_adjustment_percent: 0,
          median_adjustment_percent: 0,
          ceiling_adjustment_percent: 0,
          is_active: true,
        };
      });
      setLocalCalibrations(defaultCalibrations);
    }
  }, [calibrations]);

  // Get current position calibration
  const currentCalibration = localCalibrations[selectedPosition] || {
    position: selectedPosition,
    floor_adjustment_percent: 0,
    median_adjustment_percent: 0,
    ceiling_adjustment_percent: 0,
    is_active: true,
  };

  // Validate percentage value
  const validatePercentage = (value: number, _field: string): string | null => {
    if (isNaN(value)) {
      return 'Must be a valid number';
    }
    if (value < -50 || value > 50) {
      return 'Must be between -50 and 50';
    }
    return null;
  };

  // Handle input change
  const handleInputChange = (field: keyof CalibrationFactor, value: string | boolean) => {
    const numValue = typeof value === 'string' ? parseFloat(value) || 0 : value;

    // Update local state
    setLocalCalibrations((prev) => ({
      ...prev,
      [selectedPosition]: {
        ...prev[selectedPosition],
        [field]: numValue,
      },
    }));

    // Validate if it's a percentage field
    if (
      field === 'floor_adjustment_percent' ||
      field === 'median_adjustment_percent' ||
      field === 'ceiling_adjustment_percent'
    ) {
      const error = validatePercentage(numValue as number, field);
      setValidationErrors((prev) => ({
        ...prev,
        [`${selectedPosition}_${field}`]: error || '',
      }));
    }
  };

  // Check if there are any validation errors
  const hasValidationErrors = Object.values(validationErrors).some((error) => error !== '');

  // Handle save
  const handleSave = () => {
    if (hasValidationErrors || !weekId) return;

    const calibrationArray: CalibrationUpdateRequest[] = POSITIONS.map((pos) => {
      const cal = localCalibrations[pos] || {
        position: pos,
        floor_adjustment_percent: 0,
        median_adjustment_percent: 0,
        ceiling_adjustment_percent: 0,
        is_active: true,
      };
      return {
        position: cal.position,
        floor_adjustment_percent: cal.floor_adjustment_percent,
        median_adjustment_percent: cal.median_adjustment_percent,
        ceiling_adjustment_percent: cal.ceiling_adjustment_percent,
        is_active: cal.is_active,
      };
    });

    batchUpdate.mutate(
      {
        weekId,
        request: { calibrations: calibrationArray },
      },
      {
        onSuccess: () => {
          onClose();
        },
      }
    );
  };

  // Handle reset
  const handleReset = () => {
    if (!weekId) return;

    reset.mutate(weekId, {
      onSuccess: (data) => {
        const calibrationMap: Record<string, CalibrationFactor> = {};
        data.forEach((cal) => {
          calibrationMap[cal.position] = cal;
        });
        setLocalCalibrations(calibrationMap);
      },
    });
  };

  // Handle cancel
  const handleCancel = () => {
    setValidationErrors({});
    onClose();
  };

  return (
    <Dialog
      open={open}
      onClose={handleCancel}
      fullScreen={isMobile}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          backgroundImage: 'none',
          backgroundColor: theme.palette.mode === 'dark' ? '#0a0a0a' : '#ffffff',
        },
      }}
    >
      {/* Header */}
      <DialogTitle
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          paddingBottom: 1,
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        }}
      >
        <Typography variant="h6" component="span" sx={{ fontWeight: 600 }}>
          Calibration Settings
        </Typography>
        <IconButton
          onClick={handleCancel}
          size="small"
          sx={{
            color: 'inherit',
            '&:hover': {
              backgroundColor: 'rgba(255, 107, 53, 0.1)',
            },
          }}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ paddingTop: 2, paddingBottom: 2 }}>
        {/* Loading State */}
        {isLoading && (
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              minHeight: 400,
            }}
          >
            <CircularProgress />
          </Box>
        )}

        {/* Error State */}
        {error && (
          <Alert severity="error" sx={{ marginBottom: 2 }}>
            {error.message || 'Failed to load calibration data'}
          </Alert>
        )}

        {/* Success Messages */}
        {batchUpdate.isSuccess && (
          <Alert severity="success" sx={{ marginBottom: 2 }}>
            Calibration settings saved successfully!
          </Alert>
        )}

        {reset.isSuccess && (
          <Alert severity="success" sx={{ marginBottom: 2 }}>
            Calibration settings reset to defaults!
          </Alert>
        )}

        {/* Main Content */}
        {!isLoading && !error && (
          <Stack spacing={3}>
            {/* Position Tabs */}
            <Box>
              <Typography
                variant="caption"
                sx={{
                  display: 'block',
                  color: 'text.secondary',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: 0.5,
                  marginBottom: 1,
                }}
              >
                Position
              </Typography>
              <Tabs
                value={selectedPosition}
                onChange={(_e, newValue) => setSelectedPosition(newValue)}
                variant={isMobile ? 'scrollable' : 'fullWidth'}
                scrollButtons={isMobile ? 'auto' : false}
                sx={{
                  borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                  '& .MuiTab-root': {
                    minWidth: isMobile ? 60 : 80,
                    fontWeight: 600,
                  },
                }}
              >
                {POSITIONS.map((pos) => (
                  <Tab key={pos} label={pos} value={pos} />
                ))}
              </Tabs>
            </Box>

            <Divider sx={{ opacity: 0.3 }} />

            {/* Adjustment Input Fields */}
            <Box>
              <Typography
                variant="caption"
                sx={{
                  display: 'block',
                  color: 'text.secondary',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: 0.5,
                  marginBottom: 2,
                }}
              >
                Adjustment Percentages
              </Typography>

              <Stack spacing={2}>
                {/* Floor Adjustment */}
                <TextField
                  label="Floor Adjustment %"
                  type="number"
                  value={currentCalibration.floor_adjustment_percent}
                  onChange={(e) =>
                    handleInputChange('floor_adjustment_percent', e.target.value)
                  }
                  error={Boolean(
                    validationErrors[`${selectedPosition}_floor_adjustment_percent`]
                  )}
                  helperText={
                    validationErrors[`${selectedPosition}_floor_adjustment_percent`] ||
                    'Adjust floor projection (-50 to +50)'
                  }
                  inputProps={{
                    min: -50,
                    max: 50,
                    step: 0.5,
                    'aria-label': 'Floor Adjustment Percentage',
                  }}
                  fullWidth
                  size="small"
                />

                {/* Median Adjustment */}
                <TextField
                  label="Median Adjustment %"
                  type="number"
                  value={currentCalibration.median_adjustment_percent}
                  onChange={(e) =>
                    handleInputChange('median_adjustment_percent', e.target.value)
                  }
                  error={Boolean(
                    validationErrors[`${selectedPosition}_median_adjustment_percent`]
                  )}
                  helperText={
                    validationErrors[`${selectedPosition}_median_adjustment_percent`] ||
                    'Adjust median projection (-50 to +50)'
                  }
                  inputProps={{
                    min: -50,
                    max: 50,
                    step: 0.5,
                    'aria-label': 'Median Adjustment Percentage',
                  }}
                  fullWidth
                  size="small"
                />

                {/* Ceiling Adjustment */}
                <TextField
                  label="Ceiling Adjustment %"
                  type="number"
                  value={currentCalibration.ceiling_adjustment_percent}
                  onChange={(e) =>
                    handleInputChange('ceiling_adjustment_percent', e.target.value)
                  }
                  error={Boolean(
                    validationErrors[`${selectedPosition}_ceiling_adjustment_percent`]
                  )}
                  helperText={
                    validationErrors[`${selectedPosition}_ceiling_adjustment_percent`] ||
                    'Adjust ceiling projection (-50 to +50)'
                  }
                  inputProps={{
                    min: -50,
                    max: 50,
                    step: 0.5,
                    'aria-label': 'Ceiling Adjustment Percentage',
                  }}
                  fullWidth
                  size="small"
                />
              </Stack>
            </Box>

            <Divider sx={{ opacity: 0.3 }} />

            {/* Active Toggle */}
            <Box>
              <FormControlLabel
                control={
                  <Switch
                    checked={currentCalibration.is_active}
                    onChange={(e) => handleInputChange('is_active', e.target.checked)}
                    inputProps={{ 'aria-label': 'Active calibration toggle' }}
                  />
                }
                label={
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>
                    Active for this position
                  </Typography>
                }
              />
              <Typography variant="caption" sx={{ display: 'block', color: 'text.secondary' }}>
                When active, calibration will be applied to this position during imports
              </Typography>
            </Box>

            <Divider sx={{ opacity: 0.3 }} />

            {/* Preview Section */}
            <Box data-testid="calibration-preview-section">
              <Typography
                variant="caption"
                sx={{
                  display: 'block',
                  color: 'text.secondary',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: 0.5,
                  marginBottom: 2,
                }}
              >
                Preview
              </Typography>

              <Stack
                spacing={2}
                direction={isTablet ? 'column' : 'row'}
                sx={{ width: '100%' }}
              >
                <CalibrationPreview
                  label="Floor"
                  originalValue={SAMPLE_VALUES[selectedPosition]}
                  adjustmentPercent={currentCalibration.floor_adjustment_percent}
                />
                <CalibrationPreview
                  label="Median"
                  originalValue={SAMPLE_VALUES[selectedPosition]}
                  adjustmentPercent={currentCalibration.median_adjustment_percent}
                />
                <CalibrationPreview
                  label="Ceiling"
                  originalValue={SAMPLE_VALUES[selectedPosition]}
                  adjustmentPercent={currentCalibration.ceiling_adjustment_percent}
                />
              </Stack>
            </Box>
          </Stack>
        )}
      </DialogContent>

      <Divider sx={{ opacity: 0.3 }} />

      {/* Action Buttons */}
      <DialogActions
        sx={{
          padding: 2,
          borderTop: '1px solid rgba(255, 255, 255, 0.1)',
          gap: 1,
          flexWrap: isMobile ? 'wrap' : 'nowrap',
        }}
      >
        <Button
          onClick={handleReset}
          disabled={reset.isPending || isLoading}
          startIcon={<RestartAltIcon />}
          sx={{
            color: 'text.secondary',
            borderColor: 'rgba(255, 255, 255, 0.2)',
            '&:hover': {
              borderColor: '#ff9800',
              backgroundColor: 'rgba(255, 152, 0, 0.08)',
            },
          }}
          variant="outlined"
          size="small"
        >
          Reset to Defaults
        </Button>

        <Box sx={{ flex: 1 }} />

        <Button
          onClick={handleCancel}
          disabled={batchUpdate.isPending || reset.isPending}
          sx={{
            color: 'text.primary',
            '&:hover': {
              backgroundColor: 'rgba(255, 255, 255, 0.05)',
            },
          }}
        >
          Cancel
        </Button>

        <Button
          onClick={handleSave}
          disabled={hasValidationErrors || batchUpdate.isPending || isLoading}
          variant="contained"
          startIcon={batchUpdate.isPending ? <CircularProgress size={16} /> : <SaveIcon />}
          sx={{
            backgroundColor: '#4caf50',
            color: '#ffffff',
            '&:hover': {
              backgroundColor: '#388e3c',
            },
            '&:disabled': {
              backgroundColor: 'rgba(76, 175, 80, 0.3)',
              color: 'rgba(255, 255, 255, 0.5)',
            },
          }}
        >
          {batchUpdate.isPending ? 'Saving...' : 'Save'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CalibrationAdmin;
