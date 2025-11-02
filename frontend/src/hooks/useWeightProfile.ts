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

// LocalStorage keys for persisting current weights/config
const STORAGE_KEY_WEIGHTS = 'smart-score-current-weights';
const STORAGE_KEY_CONFIG = 'smart-score-current-config';
const STORAGE_KEY_PROFILE_ID = 'smart-score-current-profile-id';

/**
 * Load persisted weights from localStorage
 */
function loadPersistedWeights(): WeightProfile | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY_WEIGHTS);
    if (stored) {
      return JSON.parse(stored) as WeightProfile;
    }
  } catch (err) {
    console.warn('Failed to load persisted weights:', err);
  }
  return null;
}

/**
 * Load persisted config from localStorage
 */
function loadPersistedConfig(): ScoreConfig | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY_CONFIG);
    if (stored) {
      return JSON.parse(stored) as ScoreConfig;
    }
  } catch (err) {
    console.warn('Failed to load persisted config:', err);
  }
  return null;
}

/**
 * Load persisted profile ID from localStorage
 */
function loadPersistedProfileId(): number | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY_PROFILE_ID);
    if (stored) {
      const profileId = parseInt(stored, 10);
      if (!isNaN(profileId)) {
        return profileId;
      }
    }
  } catch (err) {
    console.warn('Failed to load persisted profile ID:', err);
  }
  return null;
}

/**
 * Save weights to localStorage
 */
function savePersistedWeights(weights: WeightProfile): void {
  try {
    localStorage.setItem(STORAGE_KEY_WEIGHTS, JSON.stringify(weights));
  } catch (err) {
    console.warn('Failed to save persisted weights:', err);
  }
}

/**
 * Save config to localStorage
 */
function savePersistedConfig(config: ScoreConfig): void {
  try {
    localStorage.setItem(STORAGE_KEY_CONFIG, JSON.stringify(config));
  } catch (err) {
    console.warn('Failed to save persisted config:', err);
  }
}

/**
 * Save profile ID to localStorage
 */
function savePersistedProfileId(profileId: number | null): void {
  try {
    if (profileId !== null) {
      localStorage.setItem(STORAGE_KEY_PROFILE_ID, profileId.toString());
    } else {
      localStorage.removeItem(STORAGE_KEY_PROFILE_ID);
    }
  } catch (err) {
    console.warn('Failed to save persisted profile ID:', err);
  }
}

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
  
  // Initialize state - load persisted values once on mount
  const [currentProfile, setCurrentProfile] = useState<WeightProfileResponse | null>(null);
  const [currentWeights, setCurrentWeights] = useState<WeightProfile>(() => {
    // Load persisted weights on initial state creation
    const persisted = loadPersistedWeights();
    return persisted || DEFAULT_WEIGHTS;
  });
  const [currentConfig, setCurrentConfig] = useState<ScoreConfig>(() => {
    // Load persisted config on initial state creation
    const persisted = loadPersistedConfig();
    return persisted || DEFAULT_CONFIG;
  });
  const [hasInitialized, setHasInitialized] = useState(false);

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

  // Load profile on mount - check persisted profile first, then default
  useEffect(() => {
    const initializeProfile = async () => {
      if (hasInitialized) {
        return;
      }

      // Load persisted values once
      const persistedWeights = loadPersistedWeights();
      const persistedConfig = loadPersistedConfig();
      const persistedProfileId = loadPersistedProfileId();

      try {
        // If we have a persisted profile ID, try to load that profile
        if (persistedProfileId !== null && profiles.length > 0) {
          const profile = profiles.find((p) => p.id === persistedProfileId);
          if (profile) {
            console.log('Loading persisted profile:', profile.name);
            setCurrentProfile(profile);
            // Use persisted weights/config if they exist, otherwise use profile values
            if (persistedWeights) {
              setCurrentWeights(persistedWeights);
            } else {
              setCurrentWeights(profile.weights);
              savePersistedWeights(profile.weights);
            }
            if (persistedConfig) {
              setCurrentConfig(persistedConfig);
            } else {
              setCurrentConfig(profile.config);
              savePersistedConfig(profile.config);
            }
            setHasInitialized(true);
            return;
          }
        }

        // If we have persisted weights/config but no profile, use persisted values
        if (persistedWeights && persistedConfig) {
          console.log('Using persisted weights/config (no profile)');
          // Keep currentProfile as null to indicate custom weights
          setHasInitialized(true);
          return;
        }

        // Otherwise, load default profile
        console.log('Loading default profile on mount...');
        const defaultProfile = await fetchDefaultProfile();
        setCurrentProfile(defaultProfile);
        
        // Use persisted values if they exist, otherwise use profile values
        if (persistedWeights) {
          setCurrentWeights(persistedWeights);
        } else {
          setCurrentWeights(defaultProfile.weights);
          savePersistedWeights(defaultProfile.weights);
        }
        if (persistedConfig) {
          setCurrentConfig(persistedConfig);
        } else {
          setCurrentConfig(defaultProfile.config);
          savePersistedConfig(defaultProfile.config);
        }
        savePersistedProfileId(defaultProfile.id);
        setHasInitialized(true);
        console.log('Default profile loaded:', defaultProfile.name);
      } catch (err) {
        // If default profile doesn't exist, use persisted or defaults
        console.warn('Could not load default profile, using persisted or defaults:', err);
        const persistedWeights = loadPersistedWeights();
        const persistedConfig = loadPersistedConfig();
        if (!persistedWeights || !persistedConfig) {
          // No persisted values, use hardcoded defaults
          setCurrentWeights(DEFAULT_WEIGHTS);
          setCurrentConfig(DEFAULT_CONFIG);
          savePersistedWeights(DEFAULT_WEIGHTS);
          savePersistedConfig(DEFAULT_CONFIG);
        }
        setHasInitialized(true);
      }
    };

    initializeProfile();
  }, [profiles.length, hasInitialized]);

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
      // Persist the saved profile
      savePersistedWeights(weights);
      savePersistedConfig(config);
      savePersistedProfileId(newProfile.id);
    },
    [createMutation]
  );

  const loadProfile = useCallback((profileId: number) => {
    console.log('loadProfile called with profileId:', profileId);
    console.log('Available profiles:', profiles.map(p => ({ id: p.id, name: p.name })));
    const profile = profiles.find((p) => p.id === profileId);
    if (profile) {
      console.log('loadProfile: Setting profile to', profile.name, 'with weights:', profile.weights);
      console.log('loadProfile: Current profile before update:', currentProfile?.name);
      setCurrentProfile(profile);
      setCurrentWeights(profile.weights);
      setCurrentConfig(profile.config);
      // Persist the loaded profile
      savePersistedWeights(profile.weights);
      savePersistedConfig(profile.config);
      savePersistedProfileId(profile.id);
      console.log('loadProfile: State update called - profile should be:', profile.name);
    } else {
      console.error('loadProfile: Profile not found with ID:', profileId, 'Available profiles:', profiles.map(p => ({ id: p.id, name: p.name })));
    }
  }, [profiles, currentProfile]);

  const loadDefaultProfile = useCallback(async () => {
    try {
      const defaultProfile = await fetchDefaultProfile();
      setCurrentProfile(defaultProfile);
      setCurrentWeights(defaultProfile.weights);
      setCurrentConfig(defaultProfile.config);
      // Persist the default profile
      savePersistedWeights(defaultProfile.weights);
      savePersistedConfig(defaultProfile.config);
      savePersistedProfileId(defaultProfile.id);
    } catch (err) {
      console.error('Failed to load default profile:', err);
      throw err;
    }
  }, []);

  const updateWeights = useCallback((weights: WeightProfile) => {
    setCurrentWeights(weights);
    // Persist custom weights (clear profile ID since these are custom, not from a profile)
    savePersistedWeights(weights);
    savePersistedProfileId(null);
  }, []);

  const updateConfig = useCallback((config: ScoreConfig) => {
    setCurrentConfig(config);
    // Persist custom config
    savePersistedConfig(config);
    // If updating config while using a profile, keep the profile ID
    // (config changes are considered customizations)
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
          // Persist the updated profile
          savePersistedWeights(updatedProfile.weights);
          savePersistedConfig(updatedProfile.config);
          savePersistedProfileId(updatedProfile.id);
        }
      }
    },
    deleteProfile: deleteMutation.mutateAsync,
    isSaving: createMutation.isPending || updateMutation.isPending,
  };
};

