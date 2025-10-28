/**
 * ImportDataButton Component
 *
 * Button with dropdown menu for selecting import type (LineStar, DraftKings, Season Stats).
 * Handles file input and triggers the import process.
 * Shows spinner during upload and toast notifications on completion.
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
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import useDataImport from '../../hooks/useDataImport';
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
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { setCurrentWeek } = useWeekStore();

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
      onSuccess?.(result.import_id);
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
          onSuccess?.(result.import_id);
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
        onSuccess?.(result.import_id);
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
    </>
  );
};

export default ImportDataButton;
