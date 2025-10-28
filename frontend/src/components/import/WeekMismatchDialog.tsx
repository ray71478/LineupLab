/**
 * WeekMismatchDialog Component
 *
 * Modal dialog shown when the week detected in a filename doesn't match
 * the currently selected week. Allows users to:
 * 1. Change the week selector to match the detected week
 * 2. Continue with the selected week (filename is wrong)
 * 3. Cancel the import
 */

import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  RadioGroup,
  FormControlLabel,
  Radio,
  Box,
  Alert,
} from '@mui/material';
import WarningIcon from '@mui/icons-material/Warning';

export interface WeekMismatchDialogProps {
  open: boolean;
  detectedWeek: number;
  selectedWeek: number;
  onChangeWeek: () => void;
  onContinue: () => void;
  onCancel: () => void;
  isLoading?: boolean;
}

type ActionType = 'change' | 'continue';

export const WeekMismatchDialog: React.FC<WeekMismatchDialogProps> = ({
  open,
  detectedWeek,
  selectedWeek,
  onChangeWeek,
  onContinue,
  onCancel,
  isLoading = false,
}) => {
  const [selectedAction, setSelectedAction] = useState<ActionType>('change');

  const handleConfirm = () => {
    if (selectedAction === 'change') {
      onChangeWeek();
    } else {
      onContinue();
    }
  };

  const handleClose = () => {
    if (!isLoading) {
      onCancel();
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      data-testid="week-mismatch-dialog"
    >
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <WarningIcon color="warning" />
        Week Mismatch Detected
      </DialogTitle>

      <DialogContent sx={{ py: 3 }}>
        <Alert severity="warning" sx={{ mb: 2 }}>
          The filename suggests Week {detectedWeek}, but you selected Week {selectedWeek}.
        </Alert>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          What would you like to do?
        </Typography>

        <RadioGroup
          value={selectedAction}
          onChange={(e) => setSelectedAction(e.target.value as ActionType)}
        >
          <Box sx={{ mb: 2 }}>
            <FormControlLabel
              value="change"
              control={<Radio />}
              label={
                <Box>
                  <Typography variant="body1">
                    Import for Week {detectedWeek}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Change week selector to match filename
                  </Typography>
                </Box>
              }
            />
          </Box>

          <Box>
            <FormControlLabel
              value="continue"
              control={<Radio />}
              label={
                <Box>
                  <Typography variant="body1">
                    Continue with Week {selectedWeek}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Filename is incorrect, use selected week instead
                  </Typography>
                </Box>
              }
            />
          </Box>
        </RadioGroup>
      </DialogContent>

      <DialogActions sx={{ p: 2 }}>
        <Button onClick={handleClose} disabled={isLoading}>
          Cancel
        </Button>
        <Button
          onClick={handleConfirm}
          variant="contained"
          disabled={isLoading}
          data-testid="week-mismatch-confirm"
        >
          Confirm
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default WeekMismatchDialog;
