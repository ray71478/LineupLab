/**
 * LineupConfigurationPanel Component
 *
 * Configuration panel for lineup optimization settings:
 * - Number of lineups
 * - Strategy mode (Chalk/Balanced/Contrarian)
 * - Max players per team/game
 * - Stacking rules
 * - Captain lock (showdown mode only)
 *
 * Design: Dark theme with orange accents
 */

import React from 'react';
import {
  Box,
  Paper,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Switch,
  FormControlLabel,
  Stack,
  Divider,
  Collapse,
  IconButton,
  useTheme,
  useMediaQuery,
  Tooltip,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import InfoIcon from '@mui/icons-material/Info';
import type { OptimizationSettings } from '../../types/lineup.types';
import type { PlayerScoreResponse } from '../../types/smartScore.types';

export interface LineupConfigurationPanelProps {
  settings: OptimizationSettings;
  onSettingsChange: (settings: OptimizationSettings) => void;
  mode?: 'main' | 'showdown';
  selectedPlayers?: PlayerScoreResponse[];
}

export const LineupConfigurationPanel: React.FC<LineupConfigurationPanelProps> = ({
  settings,
  onSettingsChange,
  mode = 'main',
  selectedPlayers = [],
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [expanded, setExpanded] = React.useState(!isMobile);

  const handleChange = (key: keyof OptimizationSettings, value: any) => {
    onSettingsChange({
      ...settings,
      [key]: value,
    });
  };

  const handleStackingChange = (key: keyof NonNullable<OptimizationSettings['stacking_rules']>, value: boolean) => {
    onSettingsChange({
      ...settings,
      stacking_rules: {
        ...settings.stacking_rules,
        [key]: value,
      },
    });
  };

  const handleCaptainChange = (captainId: string | null) => {
    onSettingsChange({
      ...settings,
      locked_captain_id: captainId,
    });
  };

  const isShowdownMode = mode === 'showdown';

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
          Optimization Settings
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
        <Stack spacing={2}>
          {/* Number of Lineups */}
          <TextField
            label="Number of Lineups"
            type="number"
            value={settings.num_lineups}
            onChange={(e) => handleChange('num_lineups', parseInt(e.target.value) || 10)}
            inputProps={{ min: 1, max: 20 }}
            size="small"
            fullWidth
            sx={{
              '& .MuiInputBase-input': {
                fontSize: '0.875rem',
              },
            }}
          />

          {/* Strategy Mode */}
          <FormControl fullWidth size="small">
            <InputLabel sx={{ fontSize: '0.75rem' }}>Strategy Mode</InputLabel>
            <Select
              value={settings.strategy_mode}
              label="Strategy Mode"
              onChange={(e) => handleChange('strategy_mode', e.target.value)}
              sx={{
                fontSize: '0.875rem',
              }}
            >
              <MenuItem value="Chalk" sx={{ fontSize: '0.875rem' }}>Chalk (High Ownership)</MenuItem>
              <MenuItem value="Balanced" sx={{ fontSize: '0.875rem' }}>Balanced</MenuItem>
              <MenuItem value="Contrarian" sx={{ fontSize: '0.875rem' }}>Contrarian (Low Ownership)</MenuItem>
              <MenuItem value="Tournament" sx={{ fontSize: '0.875rem' }}>Tournament (Ceiling + Leverage)</MenuItem>
            </Select>
          </FormControl>

          {/* Captain Lock (Showdown Only) */}
          {isShowdownMode && (
            <>
              <Divider />
              <Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}>
                  <Typography variant="caption" sx={{ fontWeight: 600, fontSize: '0.75rem' }}>
                    Captain Selection
                  </Typography>
                  <Tooltip
                    title="Captain will earn 1.5x salary and 1.5x points. Leave as 'None' to auto-select the best captain by value."
                    arrow
                  >
                    <InfoIcon sx={{ fontSize: '0.875rem', color: 'text.secondary' }} />
                  </Tooltip>
                </Box>
                <FormControl fullWidth size="small">
                  <InputLabel sx={{ fontSize: '0.75rem' }}>Locked Captain (Optional)</InputLabel>
                  <Select
                    value={settings.locked_captain_id ?? ''}
                    label="Locked Captain (Optional)"
                    onChange={(e) => handleCaptainChange(e.target.value || null)}
                    disabled={selectedPlayers.length === 0}
                    sx={{
                      fontSize: '0.875rem',
                    }}
                  >
                    <MenuItem value="" sx={{ fontSize: '0.875rem' }}>
                      None (Auto-select best captain)
                    </MenuItem>
                    {selectedPlayers.map((player) => (
                      <MenuItem
                        key={player.player_key}
                        value={player.player_key}
                        sx={{ fontSize: '0.875rem' }}
                      >
                        {mode === 'showdown' 
                          ? `${player.name} - $${(player.salary / 1000).toFixed(1)}K`
                          : `${player.name} (${player.position}) - $${(player.salary / 1000).toFixed(1)}K`}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                {selectedPlayers.length === 0 && (
                  <Typography
                    variant="caption"
                    sx={{
                      fontSize: '0.65rem',
                      color: 'text.secondary',
                      display: 'block',
                      mt: 0.5
                    }}
                  >
                    Select players first to enable captain lock
                  </Typography>
                )}
              </Box>
            </>
          )}

          <Divider />

          {/* Max Ownership */}
          <TextField
            label="Max Avg Ownership %"
            type="number"
            value={((settings.max_ownership ?? (isShowdownMode ? 0.75 : 0.15)) * 100).toFixed(0)}
            onChange={(e) => {
              const value = parseFloat(e.target.value) || 0;
              // Convert percentage to decimal (0-1)
              handleChange('max_ownership', Math.max(0, Math.min(100, value)) / 100);
            }}
            inputProps={{ min: 0, max: 100, step: 1 }}
            size="small"
            fullWidth
            helperText="Maximum average ownership for entire lineup (not individual players)"
            sx={{
              '& .MuiInputBase-input': {
                fontSize: '0.875rem',
              },
            }}
          />

          {/* Main Slate Only Constraints */}
          {!isShowdownMode && (
            <>
              {/* Max Players Per Team */}
              <TextField
                label="Max Players Per Team"
                type="number"
                value={settings.max_players_per_team}
                onChange={(e) => handleChange('max_players_per_team', parseInt(e.target.value) || 4)}
                inputProps={{ min: 1, max: 9 }}
                size="small"
                fullWidth
                sx={{
                  '& .MuiInputBase-input': {
                    fontSize: '0.875rem',
                  },
                }}
              />

              {/* Max Players Per Game */}
              <TextField
                label="Max Players Per Game"
                type="number"
                value={settings.max_players_per_game}
                onChange={(e) => handleChange('max_players_per_game', parseInt(e.target.value) || 5)}
                inputProps={{ min: 1, max: 9 }}
                size="small"
                fullWidth
                sx={{
                  '& .MuiInputBase-input': {
                    fontSize: '0.875rem',
                  },
                }}
              />

              <Divider />

              {/* Stacking Rules */}
              <Typography variant="caption" sx={{ fontWeight: 600, fontSize: '0.75rem', mb: 1 }}>
                Stacking Rules
              </Typography>

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.stacking_rules?.qb_wr_stack_enabled || false}
                    onChange={(e) => handleStackingChange('qb_wr_stack_enabled', e.target.checked)}
                    size="small"
                    sx={{
                      '& .MuiSwitch-switchBase.Mui-checked': {
                        color: '#ff6b35',
                      },
                      '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                        backgroundColor: '#ff6b35',
                      },
                    }}
                  />
                }
                label={
                  <Typography variant="caption" sx={{ fontSize: '0.75rem' }}>
                    QB + WR Stack (Same Team)
                  </Typography>
                }
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.stacking_rules?.bring_back_enabled || false}
                    onChange={(e) => handleStackingChange('bring_back_enabled', e.target.checked)}
                    size="small"
                    sx={{
                      '& .MuiSwitch-switchBase.Mui-checked': {
                        color: '#ff6b35',
                      },
                      '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                        backgroundColor: '#ff6b35',
                      },
                    }}
                  />
                }
                label={
                  <Typography variant="caption" sx={{ fontSize: '0.75rem' }}>
                    Bring-Back (Opposing Team)
                  </Typography>
                }
              />
            </>
          )}
        </Stack>
      </Collapse>
    </Paper>
  );
};

export default LineupConfigurationPanel;
