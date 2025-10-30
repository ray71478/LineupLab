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
        p: { xs: 2, md: 3 },
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
          mb: 2,
        }}
      >
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          Weight Adjustment
        </Typography>
        {isMobile && (
          <IconButton
            onClick={() => setExpanded(!expanded)}
            size="small"
            sx={{
              color: 'text.secondary',
              '&:hover': {
                backgroundColor: 'rgba(255, 140, 66, 0.1)',
              },
            }}
          >
            {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        )}
      </Box>

      <Collapse in={expanded}>
        {/* Profile Selector */}
        <Box sx={{ mb: 3 }}>
          <ProfileSelector
            currentWeights={localWeights}
            currentConfig={localConfig}
          />
        </Box>

        <Divider sx={{ mb: 3 }} />

        {/* Projection Source Selector */}
      <FormControl fullWidth sx={{ mb: 3 }}>
        <InputLabel>Projection Source</InputLabel>
          <Select
            value={localConfig.projection_source}
            label="Projection Source"
            onChange={(e) =>
              handleConfigChange({
                ...localConfig,
                projection_source: e.target.value as 'ETR' | 'LineStar',
              })
            }
          >
          <MenuItem value="ETR">Establish The Run (ETR)</MenuItem>
          <MenuItem value="LineStar">LineStar</MenuItem>
        </Select>
      </FormControl>

      <Divider sx={{ mb: 3 }} />

      {/* Weight Sliders */}
      <Stack spacing={3}>
        {(Object.keys(WEIGHT_LABELS) as Array<keyof WeightProfile>).map((key) => (
          <Box key={key}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {WEIGHT_LABELS[key]}
              </Typography>
              <Typography variant="body2" sx={{ color: 'text.secondary', minWidth: 50, textAlign: 'right' }}>
                {localWeights[key].toFixed(3)}
              </Typography>
            </Box>
            <Slider
              value={localWeights[key]}
              min={0}
              max={1}
              step={0.001}
              onChange={(_, value) => handleWeightChange(key, value as number)}
              sx={{
                color: '#ff8c42',
                '& .MuiSlider-thumb': {
                  '&:hover': {
                    boxShadow: '0 0 0 8px rgba(255, 140, 66, 0.16)',
                  },
                },
              }}
            />
          </Box>
        ))}
      </Stack>

      <Divider sx={{ my: 3 }} />

      {/* Action Buttons */}
      <Stack spacing={2}>
        <Button
          variant="contained"
          fullWidth
          onClick={handleApply}
          disabled={isCalculating}
          sx={{
            backgroundColor: '#ff8c42',
            '&:hover': {
              backgroundColor: '#e65a2b',
            },
            minHeight: { xs: 44, md: 36 }, // Touch-friendly on mobile
          }}
        >
          {isCalculating ? 'Calculating...' : 'Apply'}
        </Button>
        <Button
          variant="outlined"
          fullWidth
          onClick={onReset}
          disabled={isCalculating}
          sx={{
            minHeight: { xs: 44, md: 36 }, // Touch-friendly on mobile
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

