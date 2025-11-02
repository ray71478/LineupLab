/**
 * useCalibration Hooks
 *
 * Custom hooks for managing calibration data fetching and mutations.
 * - useCalibrationStatus: Fetch calibration status for a week
 * - useCalibrations: Fetch all calibration factors for a week
 * - useUpdateCalibration: Mutation hook for updating single position
 * - useBatchUpdateCalibrations: Mutation hook for batch updates
 * - useResetCalibrations: Mutation hook for resetting to defaults
 *
 * Uses React Query for data fetching and caching.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

/**
 * Types for calibration data
 */
export interface CalibrationStatus {
  week_id: number;
  is_active: boolean;
  positions_configured: number;
  total_positions: number;
}

export interface CalibrationFactor {
  position: string;
  floor_adjustment_percent: number;
  median_adjustment_percent: number;
  ceiling_adjustment_percent: number;
  is_active: boolean;
}

export interface CalibrationListResponse {
  success: boolean;
  week_id: number;
  calibrations: CalibrationFactor[];
}

export interface CalibrationUpdateRequest {
  position: string;
  floor_adjustment_percent: number;
  median_adjustment_percent: number;
  ceiling_adjustment_percent: number;
  is_active: boolean;
}

export interface CalibrationBatchRequest {
  calibrations: CalibrationUpdateRequest[];
}

/**
 * Fetch calibration status for a week
 */
async function fetchCalibrationStatus(weekId: number): Promise<CalibrationStatus> {
  const response = await fetch(`/api/calibration/${weekId}/status`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch calibration status');
  }

  const data = await response.json();

  if (!data.success) {
    throw new Error('Failed to fetch calibration status');
  }

  return {
    week_id: data.week_id,
    is_active: data.is_active,
    positions_configured: data.positions_configured,
    total_positions: data.total_positions,
  };
}

/**
 * Fetch calibration factors for a week
 */
async function fetchCalibrations(weekId: number): Promise<CalibrationFactor[]> {
  const response = await fetch(`/api/calibration/${weekId}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch calibrations');
  }

  const data: CalibrationListResponse = await response.json();

  if (!data.success) {
    throw new Error('Failed to fetch calibrations');
  }

  return data.calibrations || [];
}

/**
 * Update single calibration factor
 */
async function updateCalibration(
  weekId: number,
  request: CalibrationUpdateRequest
): Promise<CalibrationFactor> {
  const response = await fetch(`/api/calibration/${weekId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update calibration');
  }

  const data = await response.json();

  if (!data.success) {
    throw new Error('Failed to update calibration');
  }

  return data.calibration;
}

/**
 * Batch update calibration factors
 */
async function batchUpdateCalibrations(
  weekId: number,
  request: CalibrationBatchRequest
): Promise<CalibrationFactor[]> {
  const response = await fetch(`/api/calibration/${weekId}/batch`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to batch update calibrations');
  }

  const data = await response.json();

  if (!data.success) {
    throw new Error('Failed to batch update calibrations');
  }

  return data.calibrations || [];
}

/**
 * Reset calibrations to defaults
 */
async function resetCalibrations(weekId: number): Promise<CalibrationFactor[]> {
  const response = await fetch(`/api/calibration/${weekId}/reset`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to reset calibrations');
  }

  const data = await response.json();

  if (!data.success) {
    throw new Error('Failed to reset calibrations');
  }

  return data.calibrations || [];
}

/**
 * Hook: useCalibrationStatus
 *
 * Fetches calibration status for a week with caching and revalidation.
 */
export function useCalibrationStatus(weekId: number | null) {
  return useQuery({
    queryKey: ['calibration-status', weekId],
    queryFn: () => fetchCalibrationStatus(weekId!),
    enabled: weekId !== null,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
    retry: 2,
    retryDelay: 1000,
  });
}

/**
 * Hook: useCalibrations
 *
 * Fetches all calibration factors for a week.
 */
export function useCalibrations(weekId: number | null) {
  return useQuery({
    queryKey: ['calibrations', weekId],
    queryFn: () => fetchCalibrations(weekId!),
    enabled: weekId !== null,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    retry: 2,
    retryDelay: 1000,
  });
}

/**
 * Hook: useUpdateCalibration
 *
 * Mutation hook for updating a single position's calibration.
 */
export function useUpdateCalibration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ weekId, request }: { weekId: number; request: CalibrationUpdateRequest }) =>
      updateCalibration(weekId, request),
    onSuccess: (_data, variables) => {
      // Invalidate both status and calibrations queries
      queryClient.invalidateQueries({ queryKey: ['calibration-status', variables.weekId] });
      queryClient.invalidateQueries({ queryKey: ['calibrations', variables.weekId] });
    },
  });
}

/**
 * Hook: useBatchUpdateCalibrations
 *
 * Mutation hook for batch updating multiple positions.
 */
export function useBatchUpdateCalibrations() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ weekId, request }: { weekId: number; request: CalibrationBatchRequest }) =>
      batchUpdateCalibrations(weekId, request),
    onSuccess: (data, variables) => {
      // Update cache with new data
      queryClient.setQueryData(['calibrations', variables.weekId], data);

      // Invalidate status query to refresh
      queryClient.invalidateQueries({ queryKey: ['calibration-status', variables.weekId] });
      queryClient.invalidateQueries({ queryKey: ['calibrations', variables.weekId] });
    },
  });
}

/**
 * Hook: useResetCalibrations
 *
 * Mutation hook for resetting calibrations to default values.
 */
export function useResetCalibrations() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (weekId: number) => resetCalibrations(weekId),
    onSuccess: (data, weekId) => {
      // Update cache with reset data
      queryClient.setQueryData(['calibrations', weekId], data);

      // Invalidate status query to refresh
      queryClient.invalidateQueries({ queryKey: ['calibration-status', weekId] });
      queryClient.invalidateQueries({ queryKey: ['calibrations', weekId] });
    },
  });
}
