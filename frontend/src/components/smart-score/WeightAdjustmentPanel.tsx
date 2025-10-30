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
    onWeightsChange?.(updated);
  };

  const handleConfigChange = (newConfig: ScoreConfig) => {
    setLocalConfig(newConfig);
    onConfigChange?.(newConfig);
  };

  const handleApply = () => {
    onApply();
  };

  return (
    <Paper
      sx={{
        p: { xs: 1.5, md: 2 },
        backgroundColor: '#1a1a2e',
        border: '1px solid rgba(255, 140, 66, 0.2)',
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
                backgroundColor: 'rgba(255, 140, 66, 0.1)',
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
        <InputLabel sx={{ fontSize: '0.875rem' }}>Projection Source</InputLabel>
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
              fontSize: '0.875rem',
              '& .MuiSelect-select': {
                py: 1,
              },
            }}
          >
          <MenuItem value="ETR" sx={{ fontSize: '0.875rem' }}>Establish The Run (ETR)</MenuItem>
          <MenuItem value="LineStar" sx={{ fontSize: '0.875rem' }}>LineStar</MenuItem>
        </Select>
      </FormControl>

      <Divider sx={{ mb: 2 }} />

      {/* Weight Sliders */}
      <Stack spacing={1.5}>
        {(Object.keys(WEIGHT_LABELS) as Array<keyof WeightProfile>).map((key) => (
          <Box key={key}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
              <Typography variant="caption" sx={{ fontWeight: 500, fontSize: '0.75rem' }}>
                {WEIGHT_LABELS[key]}
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
              onChange={(_, value) => handleWeightChange(key, value as number)}
              size="small"
              sx={{
                color: '#ff8c42',
                height: 4,
                '& .MuiSlider-thumb': {
                  width: 14,
                  height: 14,
                  '&:hover': {
                    boxShadow: '0 0 0 6px rgba(255, 140, 66, 0.16)',
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
        ))}
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
            backgroundColor: '#ff8c42',
            fontSize: '0.875rem',
            py: 0.75,
            '&:hover': {
              backgroundColor: '#e65a2b',
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
            fontSize: '0.875rem',
            py: 0.75,
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

