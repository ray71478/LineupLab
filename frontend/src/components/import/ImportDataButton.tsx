/**
 * ImportDataButton Component
 *
 * Button with dropdown menu for selecting import type (LineStar, DraftKings, Season Stats).
 * Handles file input and triggers the import process.
 * Shows spinner during upload and toast notifications on completion.
 * Integrates with Week Management to lock weeks after successful import.
 */

import React, { useState, useRef } from 'react';
import {
  Button,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  CircularProgress,
  Box,
  Snackbar,
  Alert,
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import useDataImport from '../../hooks/useDataImport';
import useImportIntegration from '../../hooks/useImportIntegration';
import WeekMismatchDialog from './WeekMismatchDialog';
import { useWeekStore } from '../../store/weekStore';

export interface ImportDataButtonProps {
  onSuccess?: (importId: string) => void;
  onError?: (error: string) => void;
}

type ImportType = 'linestar' | 'draftkings' | 'nfl-stats';

interface MenuConfig {
  type: ImportType;
  label: string;
  description: string;
}

const IMPORT_TYPES: MenuConfig[] = [
  {
    type: 'linestar',
    label: 'Import LineStar Data',
    description: 'Upload LineStar salary file',
  },
  {
    type: 'draftkings',
    label: 'Import DraftKings Data',
    description: 'Upload DraftKings salary file (FE sheet)',
  },
  {
    type: 'nfl-stats',
    label: 'Import Season Stats',
    description: 'Upload Comprehensive Stats file',
  },
];

export const ImportDataButton: React.FC<ImportDataButtonProps> = ({
  onSuccess,
  onError,
}) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedImportType, setSelectedImportType] = useState<ImportType | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [showSuccess, setShowSuccess] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { setCurrentWeek, currentWeek, weeks } = useWeekStore();
  const { lockWeekAfterImport, updateImportStatus } = useImportIntegration();

  const {
    isLoading,
    error,
    detectedWeek,
    selectedWeek,
    isWeekMismatch,
    importId,
    uploadFile,
    clearMessages,
  } = useDataImport();

  const handleButtonClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleImportTypeSelect = (type: ImportType) => {
    setSelectedImportType(type);
    handleMenuClose();
    // Trigger file input dialog
    fileInputRef.current?.click();
  };

  const handleFileSelected = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !selectedImportType) {
      return;
    }

    // Upload file - may return null if week mismatch detected
    const result = await uploadFile(file, selectedImportType);

    if (isWeekMismatch && detectedWeek && selectedWeek) {
      // Dialog will be shown by WeekMismatchDialog component
      return;
    }

    if (result && result.success && result.import_id) {
      // Show success notification
      const msg = result.message || `${result.player_count || result.record_count || 0} records imported successfully`;
      setSuccessMessage(msg);
      setShowSuccess(true);

      // Integration with Week Management: Lock the week (only for player pool imports, not nfl-stats)
      if (selectedImportType !== 'nfl-stats') {
        const currentWeekObj = weeks.find((w) => w.week_number === currentWeek);
        if (currentWeekObj) {
          const locked = await lockWeekAfterImport(
            currentWeekObj.id,
            result.import_id,
            result.player_count || 0
          );

          if (locked) {
            onSuccess?.(result.import_id);
          } else {
            onError?.('Failed to lock week after import');
          }
        } else {
          onSuccess?.(result.import_id);
        }
      } else {
        // For nfl-stats, no week locking needed
        onSuccess?.(result.import_id);
      }
    } else if (result && result.error) {
      onError?.(result.error);
    }

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleWeekMismatchChangeWeek = async () => {
    if (detectedWeek) {
      // Change the week selector to detected week
      setCurrentWeek(detectedWeek);
      clearMessages();

      // Retry upload with new week
      const file = fileInputRef.current?.files?.[0];
      if (file && selectedImportType) {
        const result = await uploadFile(file, selectedImportType, true);

        if (result && result.success && result.import_id) {
          // Show success notification
          const msg = result.message || `${result.player_count || result.record_count || 0} records imported successfully`;
          setSuccessMessage(msg);
          setShowSuccess(true);

          // Lock the detected week (only for player pool imports, not nfl-stats)
          if (selectedImportType !== 'nfl-stats') {
            const detectedWeekObj = weeks.find((w) => w.week_number === detectedWeek);
            if (detectedWeekObj) {
              const locked = await lockWeekAfterImport(
                detectedWeekObj.id,
                result.import_id,
                result.player_count || 0
              );

              if (locked) {
                onSuccess?.(result.import_id);
              } else {
                onError?.('Failed to lock week after import');
              }
            } else {
              onSuccess?.(result.import_id);
            }
          } else {
            // For nfl-stats, no week locking needed
            onSuccess?.(result.import_id);
          }
        } else if (result && result.error) {
          onError?.(result.error);
        }
      }
    }
  };

  const handleWeekMismatchContinue = async () => {
    clearMessages();

    // Continue upload with selected week (not detected week)
    const file = fileInputRef.current?.files?.[0];
    if (file && selectedImportType) {
      const result = await uploadFile(file, selectedImportType, false);

      if (result && result.success && result.import_id) {
        // Show success notification
        const msg = result.message || `${result.player_count || result.record_count || 0} records imported successfully`;
        setSuccessMessage(msg);
        setShowSuccess(true);

        // Lock the selected week (only for player pool imports, not nfl-stats)
        if (selectedImportType !== 'nfl-stats') {
          const selectedWeekObj = weeks.find((w) => w.week_number === currentWeek);
          if (selectedWeekObj) {
            const locked = await lockWeekAfterImport(
              selectedWeekObj.id,
              result.import_id,
              result.player_count || 0
            );

            if (locked) {
              onSuccess?.(result.import_id);
            } else {
              onError?.('Failed to lock week after import');
            }
          } else {
            onSuccess?.(result.import_id);
          }
        } else {
          // For nfl-stats, no week locking needed
          onSuccess?.(result.import_id);
        }
      } else if (result && result.error) {
        onError?.(result.error);
      }
    }
  };

  const handleWeekMismatchCancel = () => {
    clearMessages();
    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <>
      <Box sx={{ position: 'relative' }}>
        <Button
          variant="contained"
          startIcon={isLoading ? <CircularProgress size={20} /> : <CloudUploadIcon />}
          onClick={handleButtonClick}
          disabled={isLoading}
          data-testid="import-data-button"
        >
          {isLoading ? 'Uploading...' : 'Import Data'}
        </Button>

        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
          data-testid="import-menu"
        >
          {IMPORT_TYPES.map((config) => (
            <MenuItem
              key={config.type}
              onClick={() => handleImportTypeSelect(config.type)}
              data-testid={`import-option-${config.type}`}
            >
              <ListItemIcon>
                <UploadFileIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText
                primary={config.label}
                secondary={config.description}
                secondaryTypographyProps={{ variant: 'caption' }}
              />
            </MenuItem>
          ))}
        </Menu>
      </Box>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".xlsx"
        onChange={handleFileSelected}
        style={{ display: 'none' }}
        data-testid="file-input"
      />

      {/* Week Mismatch Dialog */}
      {detectedWeek && selectedWeek && (
        <WeekMismatchDialog
          open={isWeekMismatch}
          detectedWeek={detectedWeek}
          selectedWeek={selectedWeek}
          onChangeWeek={handleWeekMismatchChangeWeek}
          onContinue={handleWeekMismatchContinue}
          onCancel={handleWeekMismatchCancel}
          isLoading={isLoading}
        />
      )}

      {/* Success Notification */}
      <Snackbar
        open={showSuccess}
        autoHideDuration={6000}
        onClose={() => setShowSuccess(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
      >
        <Alert onClose={() => setShowSuccess(false)} severity="success" sx={{ width: '100%' }}>
          {successMessage}
        </Alert>
      </Snackbar>

      {/* Error Notification */}
      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => clearMessages()}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
      >
        <Alert onClose={() => clearMessages()} severity="error" sx={{ width: '100%' }}>
          {error}
        </Alert>
      </Snackbar>
    </>
  );
};

export default ImportDataButton;
