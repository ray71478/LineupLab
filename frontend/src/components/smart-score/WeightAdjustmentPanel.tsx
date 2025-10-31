/**
 * WeightAdjustmentPanel Component
 *
 * Sidebar panel with 8 weight sliders, projection source selector, and action buttons.
 * - 8 sliders (W1-W8) with labels
 * - Projection source selector (ETR/LineStar)
 * - Apply, Reset, and Save Profile buttons
 *
 * Design: Dark theme with orange accents
 */

import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Stack,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Divider,
  Collapse,
  IconButton,
  Tooltip,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import type { WeightProfile, ScoreConfig } from '../../types/smartScore.types';
import { ProfileSelector } from './ProfileSelector';

export interface WeightAdjustmentPanelProps {
  weights: WeightProfile;
  config: ScoreConfig;
  onApply: () => void;
  onReset: () => void;
  onWeightsChange?: (weights: WeightProfile) => void;
  onConfigChange?: (config: ScoreConfig) => void;
  onSaveProfile?: (name: string) => void;
  isCalculating?: boolean;
}

const WEIGHT_LABELS = {
  W1: 'Projection',
  W2: 'Ceiling Factor',
  W3: 'Ownership Penalty',
  W4: 'Value Score',
  W5: 'Trend Adjustment',
  W6: 'Regression Penalty',
  W7: 'Vegas Context',
  W8: 'Matchup Adjustment',
};

// Disabled weights that have no effect
const DISABLED_WEIGHTS = {
  W8: 'Disabled - Pending data configuration',
};

export const WeightAdjustmentPanel: React.FC<WeightAdjustmentPanelProps> = ({
  weights,
  config,
  onApply,
  onReset,
  onWeightsChange,
  onConfigChange,
  isCalculating = false,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [expanded, setExpanded] = React.useState(!isMobile);
  const [localWeights, setLocalWeights] = React.useState<WeightProfile>(weights);
  const [localConfig, setLocalConfig] = React.useState<ScoreConfig>(config);

  // Update local state when props change
  React.useEffect(() => {
    setLocalWeights(weights);
  }, [weights]);

  React.useEffect(() => {
    setLocalConfig(config);
  }, [config]);

  // Auto-expand on mobile when opened
  React.useEffect(() => {
    if (!isMobile) {
      setExpanded(true);
    }
  }, [isMobile]);

  const handleWeightChange = (key: keyof WeightProfile, value: number) => {
    const updated = {
      ...localWeights,
      [key]: value,
    };
    setLocalWeights(updated);
    // Don't call onWeightsChange here - it will be called on onChangeCommitted
  };

  const handleWeightChangeCommitted = (key: keyof WeightProfile, value: number) => {
    const updated = {
      ...localWeights,
      [key]: value,
    };
    setLocalWeights(updated);
    onWeightsChange?.(updated);
  };

  const handleConfigChange = (newConfig: ScoreConfig) => {
    setLocalConfig(newConfig);
    onConfigChange?.(newConfig);
  };

  const handleApply = async () => {
    // First, invalidate Smart Score cache so fresh calculations use new weights
    try {
      await fetch('/api/smart-score/cache/invalidate', {
        method: 'POST',
      });
    } catch (cacheError) {
      console.warn('Failed to invalidate Smart Score cache:', cacheError);
      // Don't block the apply if cache invalidation fails
    }

    // Then call the original apply handler
    onApply();
  };

  return (
    <Paper
      sx={{
        p: { xs: 1.5, md: 2 },
        backgroundColor: '#0a0a0a',
        border: '1px solid rgba(255, 107, 53, 0.2)',
        borderRadius: 2,
      }}
    >
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 1.5,
        }}
      >
        <Typography variant="subtitle1" sx={{ fontWeight: 600, fontSize: '0.95rem' }}>
          Weight Adjustment
        </Typography>
        {isMobile && (
          <IconButton
            onClick={() => setExpanded(!expanded)}
            size="small"
            sx={{
              color: 'text.secondary',
              padding: '4px',
              '&:hover': {
                backgroundColor: 'rgba(255, 107, 53, 0.1)',
              },
            }}
          >
            {expanded ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
          </IconButton>
        )}
      </Box>

      <Collapse in={expanded}>
        {/* Profile Selector */}
        <Box sx={{ mb: 2 }}>
          <ProfileSelector
            currentWeights={localWeights}
            currentConfig={localConfig}
          />
        </Box>

        <Divider sx={{ mb: 2 }} />

        {/* Projection Source Selector */}
      <FormControl fullWidth size="small" sx={{ mb: 2 }}>
        <InputLabel sx={{ fontSize: '0.75rem' }}>Projection Source</InputLabel>
          <Select
            value={localConfig.projection_source}
            label="Projection Source"
            onChange={(e) =>
              handleConfigChange({
                ...localConfig,
                projection_source: e.target.value as 'ETR' | 'LineStar',
              })
            }
            sx={{
              fontSize: '0.75rem',
              '& .MuiSelect-select': {
                py: 1.2,
              },
            }}
          >
          <MenuItem value="ETR" sx={{ fontSize: '0.75rem' }}>Establish The Run (ETR)</MenuItem>
          <MenuItem value="LineStar" sx={{ fontSize: '0.75rem' }}>LineStar</MenuItem>
        </Select>
      </FormControl>

      <Divider sx={{ mb: 2 }} />

      {/* Weight Sliders */}
      <Stack spacing={1.5}>
        {(Object.keys(WEIGHT_LABELS) as Array<keyof WeightProfile>).map((key) => {
          const isDisabled = key in DISABLED_WEIGHTS;
          const disabledReason = DISABLED_WEIGHTS[key as keyof typeof DISABLED_WEIGHTS];

          return (
            <Tooltip
              key={key}
              title={isDisabled ? disabledReason : ''}
              placement="right"
            >
              <Box
                sx={{
                  opacity: isDisabled ? 0.5 : 1,
                  pointerEvents: isDisabled ? 'auto' : 'auto',
                }}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                  <Typography
                    variant="caption"
                    sx={{
                      fontWeight: 500,
                      fontSize: '0.75rem',
                      color: isDisabled ? 'text.disabled' : 'inherit',
                    }}
                  >
                    {WEIGHT_LABELS[key]}
                    {isDisabled && ' (Disabled)'}
                  </Typography>
                  <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.75rem', minWidth: 45, textAlign: 'right' }}>
                    {localWeights[key].toFixed(3)}
                  </Typography>
                </Box>
                <Slider
                  value={localWeights[key]}
                  min={0}
                  max={1}
                  step={0.001}
                  onChange={(_, value) => {
                    if (!isDisabled) {
                      handleWeightChange(key, value as number);
                    }
                  }}
                  onChangeCommitted={(_, value) => {
                    if (!isDisabled) {
                      handleWeightChangeCommitted(key, value as number);
                    }
                  }}
                  disabled={isDisabled}
                  size="small"
                  sx={{
                    color: isDisabled ? '#666' : '#ff6b35',
                    height: 4,
                    '& .MuiSlider-thumb': {
                      width: 14,
                      height: 14,
                      '&:hover': {
                        boxShadow: isDisabled ? 'none' : '0 0 0 6px rgba(255, 107, 53, 0.16)',
                      },
                    },
                    '& .MuiSlider-track': {
                      height: 3,
                    },
                    '& .MuiSlider-rail': {
                      height: 3,
                    },
                  }}
                />
              </Box>
            </Tooltip>
          );
        })}
      </Stack>

      <Divider sx={{ my: 2 }} />

      {/* Action Buttons */}
      <Stack spacing={1.5}>
        <Button
          variant="contained"
          fullWidth
          onClick={handleApply}
          disabled={isCalculating}
          size="small"
          sx={{
            backgroundColor: '#ff6b35',
            fontSize: '0.75rem',
            py: 0.75,
            '&:hover': {
              backgroundColor: '#e55a25',
            },
          }}
        >
          {isCalculating ? 'Calculating...' : 'Apply'}
        </Button>
        <Button
          variant="outlined"
          fullWidth
          onClick={onReset}
          disabled={isCalculating}
          size="small"
          sx={{
            fontSize: '0.75rem',
            py: 0.75,
            borderColor: '#ff6b35',
            color: '#ff6b35',
            '&:hover': {
              borderColor: '#e55a25',
              backgroundColor: 'rgba(255, 107, 53, 0.08)',
            },
          }}
        >
          Reset to Default
        </Button>
      </Stack>
      </Collapse>
    </Paper>
  );
};

export default WeightAdjustmentPanel;

