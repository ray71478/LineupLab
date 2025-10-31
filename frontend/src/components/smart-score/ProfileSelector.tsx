/**
 * ProfileSelector Component
 *
 * Dropdown component for selecting and saving weight profiles.
 * - Displays dropdown with list of profiles
 * - Shows selected profile name
 * - Allows selecting profile (loads weights)
 * - Add "Save Profile" button/action
 * - Opens dialog to enter profile name
 * - Validates unique name
 * - Handles save success/error
 *
 * Design: Dark theme with orange accents
 */

import React, { useState } from 'react';
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  Typography,
  IconButton,
} from '@mui/material';
import SaveIcon from '@mui/icons-material/Save';
import CloseIcon from '@mui/icons-material/Close';
import type { WeightProfileResponse, WeightProfile, ScoreConfig } from '../../types/smartScore.types';
import { useWeightProfile } from '../../hooks';

export interface ProfileSelectorProps {
  currentWeights: WeightProfile;
  currentConfig: ScoreConfig;
  onProfileChange?: (profileId: number, weights: WeightProfile, config: ScoreConfig) => void;
  onApplyProfile?: (weights: WeightProfile, config: ScoreConfig) => void;
  isCalculating?: boolean;
}

export const ProfileSelector: React.FC<ProfileSelectorProps> = ({
  currentWeights,
  currentConfig,
  onProfileChange,
  onApplyProfile,
  isCalculating = false,
}) => {
  const {
    profiles,
    currentProfile,
    loadProfile,
    createProfile,
    isLoading,
    error,
  } = useWeightProfile();

  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [profileName, setProfileName] = useState('');
  const [saveError, setSaveError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const handleProfileSelect = (profileId: number) => {
    console.log('Profile selected:', profileId, 'Available profiles:', profiles.map(p => ({ id: p.id, name: p.name })));
    const profile = profiles.find(p => p.id === profileId);
    if (!profile) {
      console.error('Profile not found:', profileId);
      return;
    }
    console.log('Loading profile:', profile.name);
    loadProfile(profileId);
    // Notify parent component to update sliders immediately
    if (onProfileChange) {
      onProfileChange(profileId, profile.weights, profile.config);
    }
  };

  const handleOpenSaveDialog = () => {
    setProfileName('');
    setSaveError(null);
    setSaveDialogOpen(true);
  };

  const handleCloseSaveDialog = () => {
    setSaveDialogOpen(false);
    setProfileName('');
    setSaveError(null);
  };

  const handleSaveProfile = async () => {
    if (!profileName.trim()) {
      setSaveError('Profile name is required');
      return;
    }

    // Check for duplicate name
    const nameExists = profiles.some(
      (p) => p.name.toLowerCase() === profileName.trim().toLowerCase()
    );
    if (nameExists) {
      setSaveError('A profile with this name already exists');
      return;
    }

    setIsSaving(true);
    setSaveError(null);

    try {
      await createProfile({
        name: profileName.trim(),
        weights: currentWeights,
        config: currentConfig,
        is_default: false,
      });

      handleCloseSaveDialog();
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : 'Failed to save profile');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'flex-start', mb: 1.5 }}>
        <FormControl fullWidth size="small" sx={{ flex: 1 }}>
          <InputLabel sx={{ fontSize: '0.875rem' }}>Profile</InputLabel>
          <Select
            value={currentProfile?.id || ''}
            label="Profile"
            onChange={(e) => handleProfileSelect(e.target.value as number)}
            disabled={isLoading}
            sx={{
              fontSize: '0.875rem',
              '& .MuiSelect-select': {
                py: 1,
              },
            }}
          >
            {profiles.map((profile) => (
              <MenuItem key={profile.id} value={profile.id} sx={{ fontSize: '0.875rem' }}>
                {profile.name}
                {profile.is_default && (
                  <Typography
                    component="span"
                    sx={{ ml: 1, fontSize: '0.7rem', color: 'text.secondary' }}
                  >
                    (Default)
                  </Typography>
                )}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <Button
          variant="outlined"
          startIcon={<SaveIcon sx={{ fontSize: '1rem' }} />}
          onClick={handleOpenSaveDialog}
          disabled={isLoading}
          size="small"
          sx={{
            borderColor: 'rgba(255, 255, 255, 0.2)',
            color: 'text.primary',
            fontSize: '0.8rem',
            px: 1.5,
            py: 0.75,
            whiteSpace: 'nowrap',
            '&:hover': {
              borderColor: '#ff6b35',
              backgroundColor: 'rgba(255, 107, 53, 0.08)',
            },
          }}
        >
          Save
        </Button>
      </Box>

      {/* Save Profile Dialog */}
      <Dialog
        open={saveDialogOpen}
        onClose={handleCloseSaveDialog}
        PaperProps={{
          sx: {
            backgroundColor: '#0a0a0a',
            border: '1px solid rgba(255, 107, 53, 0.2)',
          },
        }}
      >
        <DialogTitle
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
            pb: 2,
            backgroundColor: '#000000',
          }}
        >
          <Typography variant="h6" sx={{ fontWeight: 600, color: '#ffffff' }}>
            Save Weight Profile
          </Typography>
          <IconButton
            onClick={handleCloseSaveDialog}
            size="small"
            sx={{
              color: '#a0a0a0',
              '&:hover': {
                backgroundColor: 'rgba(255, 107, 53, 0.1)',
                color: '#ff6b35',
              },
            }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>

        <DialogContent sx={{ pt: 3, backgroundColor: '#0a0a0a' }}>
          {saveError && (
            <Alert 
              severity="error" 
              sx={{ 
                mb: 2,
                backgroundColor: 'rgba(244, 67, 54, 0.15)',
                color: '#f44336',
                '& .MuiAlert-icon': {
                  color: '#f44336',
                },
              }}
            >
              {saveError}
            </Alert>
          )}

          <TextField
            autoFocus
            fullWidth
            label="Profile Name"
            value={profileName}
            onChange={(e) => {
              setProfileName(e.target.value);
              setSaveError(null);
            }}
            placeholder="Enter profile name"
            disabled={isSaving}
            sx={{
              '& .MuiInputLabel-root': {
                color: '#a0a0a0',
              },
              '& .MuiInputBase-input': {
                color: '#ffffff',
              },
              '& .MuiOutlinedInput-root': {
                backgroundColor: 'rgba(0, 0, 0, 0.3)',
                '& fieldset': {
                  borderColor: 'rgba(255, 255, 255, 0.2)',
                },
                '&:hover fieldset': {
                  borderColor: '#ff6b35',
                },
                '&.Mui-focused fieldset': {
                  borderColor: '#ff6b35',
                },
              },
            }}
          />
        </DialogContent>

        <DialogActions sx={{ borderTop: '1px solid rgba(255, 255, 255, 0.1)', p: 2, backgroundColor: '#000000' }}>
          <Button
            onClick={handleCloseSaveDialog}
            disabled={isSaving}
            sx={{
              color: '#ffffff',
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.05)',
              },
            }}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSaveProfile}
            disabled={isSaving || !profileName.trim()}
            variant="contained"
            sx={{
              backgroundColor: '#ff6b35',
              color: '#ffffff',
              '&:hover': {
                backgroundColor: '#e55a25',
              },
              '&:disabled': {
                backgroundColor: 'rgba(255, 107, 53, 0.3)',
                color: 'rgba(255, 255, 255, 0.5)',
              },
            }}
          >
            {isSaving ? 'Saving...' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ProfileSelector;

