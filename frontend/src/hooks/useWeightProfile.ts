/**
 * useWeightProfile Hook
 *
 * Custom hook for managing weight profile state, loading, saving, and selection.
 * - Fetches profiles with React Query
 * - Manages profile selection state
 * - Handles profile saving and loading
 * - Manages current weights state
 *
 * @example
 * const {
 *   profiles,
 *   currentProfile,
 *   currentWeights,
 *   currentConfig,
 *   isLoading,
 *   error,
 *   saveProfile,
 *   loadProfile,
 *   loadDefaultProfile,
 *   updateWeights,
 *   updateConfig
 * } = useWeightProfile();
 */

import { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type {
  WeightProfile,
  ScoreConfig,
  WeightProfileResponse,
  WeightProfileListResponse,
  CreateProfileRequest,
  UpdateProfileRequest,
} from '../types/smartScore.types';

export interface UseWeightProfileReturn {
  profiles: WeightProfileResponse[];
  currentProfile: WeightProfileResponse | null;
  currentWeights: WeightProfile;
  currentConfig: ScoreConfig;
  isLoading: boolean;
  error: Error | null;
  saveProfile: (name: string, weights: WeightProfile, config: ScoreConfig) => Promise<void>;
  loadProfile: (profileId: number) => void;
  loadDefaultProfile: () => Promise<void>;
  updateWeights: (weights: WeightProfile) => void;
  updateConfig: (config: ScoreConfig) => void;
  createProfile: (request: CreateProfileRequest) => Promise<WeightProfileResponse>;
  updateProfile: (profileId: number, request: UpdateProfileRequest) => Promise<void>;
  deleteProfile: (profileId: number) => Promise<void>;
  isSaving: boolean;
}

// Default weights (equal 0.125 each)
const DEFAULT_WEIGHTS: WeightProfile = {
  W1: 0.125,
  W2: 0.125,
  W3: 0.125,
  W4: 0.125,
  W5: 0.125,
  W6: 0.125,
  W7: 0.125,
  W8: 0.125,
};

// Default config
const DEFAULT_CONFIG: ScoreConfig = {
  projection_source: 'ETR',
  eighty_twenty_enabled: true,
  eighty_twenty_threshold: 20.0,
};

/**
 * Fetch weight profiles list
 */
async function fetchProfiles(): Promise<WeightProfileResponse[]> {
  const response = await fetch('/api/smart-score/profiles');

  if (!response.ok) {
    throw new Error('Failed to fetch weight profiles');
  }

  const data: WeightProfileListResponse = await response.json();

  if (!data.success) {
    throw new Error('Failed to fetch weight profiles');
  }

  return data.profiles || [];
}

/**
 * Fetch default profile
 */
async function fetchDefaultProfile(): Promise<WeightProfileResponse> {
  const response = await fetch('/api/smart-score/profiles/default');

  if (!response.ok) {
    throw new Error('Failed to fetch default profile');
  }

  const data: WeightProfileResponse = await response.json();
  return data;
}

/**
 * Create a new profile
 */
async function createProfile(request: CreateProfileRequest): Promise<WeightProfileResponse> {
  const response = await fetch('/api/smart-score/profiles', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create profile');
  }

  return await response.json();
}

/**
 * Update a profile
 */
async function updateProfile(
  profileId: number,
  request: UpdateProfileRequest
): Promise<WeightProfileResponse> {
  const response = await fetch(`/api/smart-score/profiles/${profileId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update profile');
  }

  return await response.json();
}

/**
 * Delete a profile
 */
async function deleteProfile(profileId: number): Promise<void> {
  const response = await fetch(`/api/smart-score/profiles/${profileId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to delete profile');
  }
}

/**
 * useWeightProfile Hook
 *
 * Manages weight profile state and operations
 */
export const useWeightProfile = (): UseWeightProfileReturn => {
  const queryClient = useQueryClient();
  const [currentProfile, setCurrentProfile] = useState<WeightProfileResponse | null>(null);
  const [currentWeights, setCurrentWeights] = useState<WeightProfile>(DEFAULT_WEIGHTS);
  const [currentConfig, setCurrentConfig] = useState<ScoreConfig>(DEFAULT_CONFIG);

  // Fetch profiles list
  const {
    data: profiles = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: ['weight-profiles'],
    queryFn: fetchProfiles,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Load default profile on mount
  useEffect(() => {
    const loadDefault = async () => {
      try {
        const defaultProfile = await fetchDefaultProfile();
        setCurrentProfile(defaultProfile);
        setCurrentWeights(defaultProfile.weights);
        setCurrentConfig(defaultProfile.config);
      } catch (err) {
        // If default profile doesn't exist, use defaults
        console.warn('Could not load default profile, using defaults:', err);
      }
    };

    loadDefault();
  }, []);

  // Create profile mutation
  const createMutation = useMutation({
    mutationFn: createProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['weight-profiles'] });
    },
  });

  // Update profile mutation
  const updateMutation = useMutation({
    mutationFn: ({ profileId, request }: { profileId: number; request: UpdateProfileRequest }) =>
      updateProfile(profileId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['weight-profiles'] });
    },
  });

  // Delete profile mutation
  const deleteMutation = useMutation({
    mutationFn: deleteProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['weight-profiles'] });
    },
  });

  const saveProfile = useCallback(
    async (name: string, weights: WeightProfile, config: ScoreConfig) => {
      const newProfile = await createMutation.mutateAsync({
        name,
        weights,
        config,
        is_default: false,
      });
      setCurrentProfile(newProfile);
      setCurrentWeights(weights);
      setCurrentConfig(config);
    },
    [createMutation]
  );

  const loadProfile = useCallback((profileId: number) => {
    const profile = profiles.find((p) => p.id === profileId);
    if (profile) {
      setCurrentProfile(profile);
      setCurrentWeights(profile.weights);
      setCurrentConfig(profile.config);
    }
  }, [profiles]);

  const loadDefaultProfile = useCallback(async () => {
    try {
      const defaultProfile = await fetchDefaultProfile();
      setCurrentProfile(defaultProfile);
      setCurrentWeights(defaultProfile.weights);
      setCurrentConfig(defaultProfile.config);
    } catch (err) {
      console.error('Failed to load default profile:', err);
      throw err;
    }
  }, []);

  const updateWeights = useCallback((weights: WeightProfile) => {
    setCurrentWeights(weights);
  }, []);

  const updateConfig = useCallback((config: ScoreConfig) => {
    setCurrentConfig(config);
  }, []);

  return {
    profiles,
    currentProfile,
    currentWeights,
    currentConfig,
    isLoading,
    error: error as Error | null,
    saveProfile,
    loadProfile,
    loadDefaultProfile,
    updateWeights,
    updateConfig,
    createProfile: createMutation.mutateAsync,
    updateProfile: async (profileId: number, request: UpdateProfileRequest) => {
      await updateMutation.mutateAsync({ profileId, request });
      if (currentProfile?.id === profileId) {
        // Reload current profile if it was updated
        const updatedProfile = profiles.find((p) => p.id === profileId);
        if (updatedProfile) {
          setCurrentProfile(updatedProfile);
          setCurrentWeights(updatedProfile.weights);
          setCurrentConfig(updatedProfile.config);
        }
      }
    },
    deleteProfile: deleteMutation.mutateAsync,
    isSaving: createMutation.isPending || updateMutation.isPending,
  };
};

