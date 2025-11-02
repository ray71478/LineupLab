/**
 * useDataImport Hook
 *
 * Custom hook for handling data import operations including:
 * - File upload with week detection
 * - Week mismatch detection
 * - API calls to import endpoints with contest mode support
 * - Error and success handling
 * - Unmatched players workflow
 */

import { useState, useCallback } from 'react';
import { useWeekStore } from '../store/weekStore';
import { useMode } from './useMode';

export interface ImportResponse {
  success: boolean;
  import_id?: string;
  message?: string;
  player_count?: number;
  record_count?: number;
  changes_from_previous?: {
    ownership_changes: number;
    avg_ownership_delta: number;
    projection_changes: number;
    new_players: number;
    removed_players: number;
  };
  unmatched_count?: number;
  warning?: string;
  detected_week?: number;
  selected_week?: number;
  requires_confirmation?: boolean;
  error?: string;
}

export interface UseDataImportReturn {
  isLoading: boolean;
  error: string | null;
  successMessage: string | null;
  detectedWeek: number | null;
  selectedWeek: number | null;
  isWeekMismatch: boolean;
  importId: string | null;
  uploadFile: (file: File, importType: 'linestar' | 'draftkings' | 'nfl-stats', confirmWeekMismatch?: boolean) => Promise<ImportResponse | null>;
  clearMessages: () => void;
}

/**
 * Week detection patterns for different import types
 */
const WEEK_PATTERNS = {
  linestar: /WK(\d+)/i,
  draftkings: /Week\s+(\d+)/i,
  'nfl-stats': /throughWeek(\d+)/i,
};

/**
 * Extract week number from filename using import-type-specific regex
 */
function detectWeekFromFilename(
  filename: string,
  importType: 'linestar' | 'draftkings' | 'nfl-stats'
): number | null {
  const pattern = WEEK_PATTERNS[importType];
  const match = filename.match(pattern);
  if (match && match[1]) {
    const week = parseInt(match[1], 10);
    if (week >= 1 && week <= 18) {
      return week;
    }
  }
  return null;
}

/**
 * Get the API endpoint URL for the given import type
 */
function getApiEndpoint(importType: 'linestar' | 'draftkings' | 'nfl-stats'): string {
  const endpoints = {
    linestar: '/api/import/linestar',
    draftkings: '/api/import/draftkings',
    'nfl-stats': '/api/import/nfl-stats',
  };
  return endpoints[importType];
}

/**
 * useDataImport Hook
 *
 * Handles the complete file upload flow:
 * 1. Parse filename for week number
 * 2. Compare to selected week
 * 3. Detect week mismatch
 * 4. Upload file via FormData with contest mode
 * 5. Handle responses (success, warning, error)
 */
export const useDataImport = (): UseDataImportReturn => {
  const { currentWeek } = useWeekStore();
  const { mode } = useMode();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [detectedWeek, setDetectedWeek] = useState<number | null>(null);
  const [selectedWeek, setSelectedWeek] = useState<number | null>(null);
  const [isWeekMismatch, setIsWeekMismatch] = useState(false);
  const [importId, setImportId] = useState<string | null>(null);

  const clearMessages = useCallback(() => {
    setError(null);
    setSuccessMessage(null);
    setDetectedWeek(null);
    setSelectedWeek(null);
    setIsWeekMismatch(false);
    setImportId(null);
  }, []);

  const uploadFile = useCallback(
    async (
      file: File,
      importType: 'linestar' | 'draftkings' | 'nfl-stats',
      confirmWeekMismatch = false
    ): Promise<ImportResponse | null> => {
      try {
        setIsLoading(true);
        clearMessages();

        // Validate file is .xlsx
        if (!file.name.endsWith('.xlsx')) {
          setError('File must be in .xlsx format');
          setIsLoading(false);
          return null;
        }

        // Detect week from filename (not needed for nfl-stats)
        let detectedWeekNum: number | null = null;
        if (importType !== 'nfl-stats') {
          detectedWeekNum = detectWeekFromFilename(file.name, importType);
        }

        // Check for week mismatch (only for linestar and draftkings)
        if (importType !== 'nfl-stats' && detectedWeekNum && detectedWeekNum !== currentWeek && !confirmWeekMismatch) {
          setDetectedWeek(detectedWeekNum);
          setSelectedWeek(currentWeek);
          setIsWeekMismatch(true);
          setIsLoading(false);
          return null; // Caller should show dialog and retry with confirmWeekMismatch=true
        }

        // Prepare form data
        const formData = new FormData();
        formData.append('file', file);

        // Add week information for linestar and draftkings
        if (importType !== 'nfl-stats') {
          const weekToUse = confirmWeekMismatch ? detectedWeekNum : currentWeek;
          formData.append('week_id', String(weekToUse || currentWeek));
          if (detectedWeekNum) {
            formData.append('detected_week', String(detectedWeekNum));
          }
          // Add contest mode parameter
          formData.append('contest_mode', mode);
        }

        // Make API request
        const endpoint = getApiEndpoint(importType);
        const response = await fetch(endpoint, {
          method: 'POST',
          body: formData,
        });

        const data: ImportResponse = await response.json();

        if (!response.ok) {
          setError(data.error || `Import failed with status ${response.status}`);
          setIsLoading(false);
          return data;
        }

        if (!data.success) {
          // Week mismatch warning
          if (data.warning === 'week_mismatch' && data.requires_confirmation) {
            setDetectedWeek(data.detected_week || null);
            setSelectedWeek(data.selected_week || null);
            setIsWeekMismatch(true);
            setIsLoading(false);
            return data; // Caller should show dialog
          }

          // Other error
          setError(data.error || 'Import failed');
          setIsLoading(false);
          return data;
        }

        // Success - include mode in message
        const modeText = mode === 'showdown' ? ' (Showdown mode)' : ' (Main Slate)';
        const message = data.message ? `${data.message}${modeText}` : `Import successful${modeText}`;
        setSuccessMessage(message);
        setImportId(data.import_id || null);
        setIsLoading(false);

        return data;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'An unexpected error occurred';
        setError(errorMessage);
        setIsLoading(false);
        return null;
      }
    },
    [currentWeek, mode, clearMessages]
  );

  return {
    isLoading,
    error,
    successMessage,
    detectedWeek,
    selectedWeek,
    isWeekMismatch,
    importId,
    uploadFile,
    clearMessages,
  };
};

export default useDataImport;
