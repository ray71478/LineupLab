# Cortex Frontend - Data Import System

React 18 + TypeScript frontend for the Data Import System.

## Architecture

### Tech Stack
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool (recommended)
- **Material-UI (MUI) v5** - Component library
- **Zustand** - State management
- **TanStack Query** - Data fetching (optional)

### Directory Structure

```
frontend/src/
├── components/
│   ├── layout/
│   │   ├── WeekSelector.tsx      # Week dropdown (1-18)
│   │   └── index.ts
│   ├── import/
│   │   ├── ImportDataButton.tsx       # Import button with menu
│   │   ├── WeekMismatchDialog.tsx     # Week mismatch warning
│   │   ├── UnmatchedPlayersReview.tsx # Post-import player review
│   │   └── index.ts
│   └── index.ts
├── hooks/
│   ├── useDataImport.ts          # File upload & import logic
│   └── index.ts
├── store/
│   ├── weekStore.ts              # Zustand week state
│   └── index.ts
└── README.md (this file)
```

## Components

### WeekSelector
Dropdown component for selecting the active week (1-18).

**Usage:**
```tsx
import { WeekSelector } from '@/components';

export function Header() {
  return (
    <Box sx={{ display: 'flex', gap: 2 }}>
      <WeekSelector />
    </Box>
  );
}
```

**Features:**
- Displays weeks 1-18
- Uses Zustand global state
- Persists to localStorage
- Default to Week 1

### ImportDataButton
Button with dropdown menu for selecting import type.

**Usage:**
```tsx
import { ImportDataButton } from '@/components';

export function Header() {
  return (
    <ImportDataButton
      onSuccess={(importId) => console.log('Import success:', importId)}
      onError={(error) => console.error('Import failed:', error)}
    />
  );
}
```

**Features:**
- Dropdown menu with 3 import types:
  - Import LineStar Data
  - Import DraftKings Data
  - Import Season Stats
- File input (.xlsx only)
- Week detection from filename
- Spinner during upload
- Handles week mismatch detection

### WeekMismatchDialog
Modal dialog shown when filename week doesn't match selected week.

**Usage:**
```tsx
import { WeekMismatchDialog } from '@/components';

export function MyComponent() {
  const [open, setOpen] = useState(false);

  return (
    <WeekMismatchDialog
      open={open}
      detectedWeek={8}
      selectedWeek={9}
      onChangeWeek={() => {
        // Change week selector to detected week
        setOpen(false);
      }}
      onContinue={() => {
        // Continue with selected week
        setOpen(false);
      }}
      onCancel={() => setOpen(false)}
    />
  );
}
```

**Features:**
- Shows detected vs selected week
- Radio buttons for action selection
- Change week option
- Continue with selected option
- Cancel button

### UnmatchedPlayersReview
Post-import review screen for players that couldn't be fuzzy-matched.

**Usage:**
```tsx
import { UnmatchedPlayersReview } from '@/components';

export function ImportResults() {
  return (
    <UnmatchedPlayersReview
      importId="uuid-from-import-response"
      onClose={() => console.log('Done reviewing')}
      onSave={() => console.log('Mappings saved')}
    />
  );
}
```

**Features:**
- Lists all unmatched players
- Shows suggested matches with similarity scores
- Map to suggested button
- Create new player option
- Ignore button
- Save mappings button
- Fetches from `/api/unmatched-players`
- Posts to `/api/unmatched-players/map` and `/api/unmatched-players/ignore`

## Hooks

### useDataImport
Custom hook for handling file uploads and import operations.

**Usage:**
```tsx
import { useDataImport } from '@/hooks';

export function MyComponent() {
  const {
    isLoading,
    error,
    successMessage,
    detectedWeek,
    selectedWeek,
    isWeekMismatch,
    importId,
    uploadFile,
    clearMessages,
  } = useDataImport();

  const handleUpload = async () => {
    const file = /* ... */;
    const result = await uploadFile(file, 'linestar');

    if (result?.success) {
      console.log('Import successful:', result.import_id);
    }
  };

  return (
    <>
      {error && <Alert severity="error">{error}</Alert>}
      {successMessage && <Alert severity="success">{successMessage}</Alert>}
      <button onClick={handleUpload} disabled={isLoading}>
        {isLoading ? 'Uploading...' : 'Upload'}
      </button>
    </>
  );
}
```

**Features:**
- Week detection from filename (regex patterns)
- Week mismatch detection
- Multipart/form-data file upload
- Error handling with clear messages
- Success message with import summary
- Spinner/loading state
- Unmatched players tracking

**Week Detection Patterns:**
- LineStar: `WK(\d+)` - e.g., `LineStar_Football_WK8.xlsx` = Week 8
- DraftKings: `Week (\d+)` - e.g., `DKSalaries Week 8.xlsx` = Week 8
- Comprehensive Stats: `throughWeek(\d+)` - e.g., `ComprehensiveStats_throughWeek7.xlsx` = Week 7

## Store

### useWeekStore
Zustand store for global week state.

**Usage:**
```tsx
import { useWeekStore } from '@/store';

export function MyComponent() {
  const { currentWeek, setCurrentWeek } = useWeekStore();

  return (
    <button onClick={() => setCurrentWeek(8)}>
      Current week: {currentWeek}
    </button>
  );
}
```

**Features:**
- Global state across entire app
- Persists to localStorage
- Default to Week 1
- Week validation (1-18)

## API Endpoints

The frontend communicates with these backend endpoints:

### Import Endpoints
- `POST /api/import/linestar` - Import LineStar data
- `POST /api/import/draftkings` - Import DraftKings data
- `POST /api/import/nfl-stats` - Import Comprehensive Stats

**Request Body:**
```
Content-Type: multipart/form-data

Fields:
- file: File (.xlsx)
- week_id: Integer (for linestar/draftkings)
- detected_week: Integer (optional)
```

**Response (Success):**
```json
{
  "success": true,
  "import_id": "uuid-string",
  "message": "153 players imported successfully",
  "player_count": 153,
  "unmatched_count": 3
}
```

**Response (Week Mismatch):**
```json
{
  "success": false,
  "warning": "week_mismatch",
  "detected_week": 8,
  "selected_week": 9,
  "requires_confirmation": true
}
```

### Unmatched Players Endpoints
- `GET /api/unmatched-players?import_id={id}` - Get unmatched players
- `POST /api/unmatched-players/map` - Map an unmatched player
- `POST /api/unmatched-players/ignore` - Ignore an unmatched player

## Integration Example

Here's a complete example integrating all components in a header:

```tsx
import React from 'react';
import { Box, AppBar, Toolbar, Container } from '@mui/material';
import { WeekSelector, ImportDataButton } from '@/components';

export function Header() {
  const handleImportSuccess = (importId: string) => {
    // Show success toast or navigate to review screen
    console.log('Import successful:', importId);
  };

  const handleImportError = (error: string) => {
    // Show error toast
    console.error('Import failed:', error);
  };

  return (
    <AppBar position="static">
      <Toolbar>
        <Container maxWidth="lg" sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>Logo/Title</Box>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <WeekSelector />
            <ImportDataButton
              onSuccess={handleImportSuccess}
              onError={handleImportError}
            />
          </Box>
        </Container>
      </Toolbar>
    </AppBar>
  );
}
```

## Installation

1. Install dependencies:
```bash
npm install zustand zustand/middleware @mui/material @mui/icons-material @emotion/react @emotion/styled
```

2. Set up tsconfig.json path alias (optional):
```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  }
}
```

3. Update Vite config (if using path aliases):
```ts
import react from '@vitejs/plugin-react';
import path from 'path';

export default {
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
};
```

## Development

### Component Testing
Each component includes `data-testid` attributes for easy testing:

```tsx
// Test WeekSelector
fireEvent.change(screen.getByTestId('week-selector'), { target: { value: 8 } });

// Test ImportDataButton
fireEvent.click(screen.getByTestId('import-data-button'));
fireEvent.click(screen.getByTestId('import-option-linestar'));

// Test WeekMismatchDialog
fireEvent.click(screen.getByTestId('week-mismatch-confirm'));

// Test UnmatchedPlayersReview
const fileInput = screen.getByTestId('file-input');
```

### Error Handling
All components follow consistent error handling patterns:
- Clear error messages in Alert components
- Error state in hooks
- API errors returned in response objects

## Performance Considerations

1. **Week State Persistence**: Uses localStorage via Zustand middleware
2. **Lazy Loading**: Components only fetch data when needed
3. **File Upload**: Uses FormData for efficient multipart uploads
4. **Error Boundaries**: Wrap components in error boundaries for production

## Future Enhancements

- [ ] Toast notifications (Snackbar component)
- [ ] Import history visualization
- [ ] Detailed import comparison UI
- [ ] Drag-and-drop file upload
- [ ] Multiple file upload
- [ ] CSV import support
- [ ] Progress tracking for large imports
- [ ] Undo/rollback functionality

---

**Phase 4 Implementation Complete** - All components fully typed, documented, and ready for integration.
