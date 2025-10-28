## Error handling best practices

### General Principles
- **User-Friendly Messages**: Provide clear, actionable error messages to users without exposing technical details
- **Fail Fast and Explicitly**: Validate input early; fail with clear error messages rather than allowing invalid state
- **Specific Exception Types**: Use specific exception/error types rather than generic ones
- **Centralized Error Handling**: Handle errors at appropriate boundaries (API layer, React error boundaries)
- **Graceful Degradation**: Design systems to degrade gracefully when non-critical services fail
- **Retry Strategies**: Implement exponential backoff for transient failures (Phase 2: API calls)
- **Clean Up Resources**: Always clean up resources (file handles, database connections) properly

### Cortex-Specific Error Handling

#### Backend Error Handling (FastAPI)

**Custom Exception Classes:**
```python
# exceptions.py
class CortexException(Exception):
    """Base exception for Cortex application"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class DataImportError(CortexException):
    """Raised when XLSX import fails"""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)

class PlayerNotFoundError(CortexException):
    """Raised when player lookup fails"""
    def __init__(self, player_key: str):
        super().__init__(f"Player not found: {player_key}", status_code=404)

class LineupOptimizationError(CortexException):
    """Raised when lineup optimization fails"""
    def __init__(self, message: str):
        super().__init__(message, status_code=422)

class SmartScoreCalculationError(CortexException):
    """Raised when Smart Score calculation fails"""
    def __init__(self, message: str):
        super().__init__(message, status_code=422)
```

**Global Exception Handler:**
```python
# main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from exceptions import CortexException

app = FastAPI()

@app.exception_handler(CortexException)
async def cortex_exception_handler(request: Request, exc: CortexException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.message,
            "details": None,
        },
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    # Log the full error for debugging
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Return generic error to user (don't expose internals)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "An unexpected error occurred. Please try again.",
            "details": None,
        },
    )
```

**Data Import Error Handling:**
```python
# services/data_importer.py
import pandas as pd
from exceptions import DataImportError

async def import_linestar_data(file_path: str, week_id: int):
    try:
        # Read XLSX file
        df = pd.read_excel(file_path, sheet_name="Players")
    except FileNotFoundError:
        raise DataImportError("File not found. Please check the file path.")
    except ValueError as e:
        raise DataImportError(f"Invalid file format: {str(e)}")
    
    # Validate required columns
    required_columns = ["Name", "Team", "Position", "Salary", "Projection"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise DataImportError(
            f"Missing required columns: {', '.join(missing_columns)}"
        )
    
    # Validate data types
    try:
        df["Salary"] = df["Salary"].astype(int)
        df["Projection"] = df["Projection"].astype(float)
    except ValueError:
        raise DataImportError(
            "Invalid data types. Salary must be integer, Projection must be float."
        )
    
    # Check for empty data
    if df.empty:
        raise DataImportError("File contains no player data.")
    
    # Import players to database
    try:
        players = [
            {
                "week_id": week_id,
                "player_key": generate_player_key(row),
                "name": row["Name"],
                "team": row["Team"],
                "position": row["Position"],
                "salary": row["Salary"],
                "projection": row["Projection"],
                "source": "LineStar",
            }
            for _, row in df.iterrows()
        ]
        
        session.bulk_insert_mappings(PlayerPool, players)
        session.commit()
        
        return {"success": True, "message": f"{len(players)} players imported"}
    
    except SQLAlchemyError as e:
        session.rollback()
        raise DataImportError(f"Database error: Failed to save player data")
```

**Lineup Optimization Error Handling:**
```python
# services/lineup_optimizer.py
from pulp import LpProblem, LpMaximize, LpVariable, lpSum, LpStatus
from exceptions import LineupOptimizationError

def generate_lineups(players: list, constraints: dict):
    try:
        # Create optimization problem
        prob = LpProblem("DFS_Lineup_Optimizer", LpMaximize)
        
        # ... optimization logic ...
        
        # Solve
        prob.solve()
        
        # Check if solution found
        if LpStatus[prob.status] != "Optimal":
            raise LineupOptimizationError(
                "Unable to generate lineups with current constraints. "
                "Try relaxing exposure limits or salary cap."
            )
        
        return lineups
    
    except Exception as e:
        if isinstance(e, LineupOptimizationError):
            raise
        raise LineupOptimizationError(
            f"Optimization failed: {str(e)}"
        )
```

#### Frontend Error Handling (React)

**React Error Boundary:**
```typescript
// components/ErrorBoundary.tsx
import { Component, ReactNode } from 'react';
import { Box, Typography, Button } from '@mui/material';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <Box sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h5" color="error" gutterBottom>
            Something went wrong
          </Typography>
          <Typography variant="body1" color="text.secondary" gutterBottom>
            {this.state.error?.message || 'An unexpected error occurred'}
          </Typography>
          <Button
            variant="contained"
            onClick={() => window.location.reload()}
            sx={{ mt: 2 }}
          >
            Reload Page
          </Button>
        </Box>
      );
    }

    return this.props.children;
  }
}
```

**API Error Handling with TanStack Query:**
```typescript
// hooks/usePlayerPool.ts
import { useQuery } from '@tanstack/react-query';
import { fetchPlayerPool } from '../api/players';
import { useSnackbar } from 'notistack';

export const usePlayerPool = (weekId: number) => {
  const { enqueueSnackbar } = useSnackbar();

  return useQuery({
    queryKey: ['playerPool', weekId],
    queryFn: () => fetchPlayerPool(weekId),
    onError: (error: Error) => {
      enqueueSnackbar(
        error.message || 'Failed to load player pool',
        { variant: 'error' }
      );
    },
    retry: 2, // Retry failed requests twice
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
};
```

**Form Validation Errors:**
```typescript
// components/LineupGenerator.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const lineupSchema = z.object({
  numLineups: z.number().min(1).max(20),
  strategyMode: z.enum(['Chalk', 'Balanced', 'Contrarian']),
  maxPlayersPerTeam: z.number().min(1).max(9),
});

export const LineupGenerator: FC = () => {
  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(lineupSchema),
  });

  const onSubmit = (data) => {
    // Generate lineups
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <TextField
        {...register('numLineups')}
        error={!!errors.numLineups}
        helperText={errors.numLineups?.message}
      />
      {/* ... */}
    </form>
  );
};
```

**Data Import Error Display:**
```typescript
// components/DataImportButton.tsx
import { useState } from 'react';
import { Button, Alert, CircularProgress } from '@mui/material';
import { Upload } from '@mui/icons-material';

export const DataImportButton: FC = () => {
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleFileUpload = async (file: File) => {
    setError(null);
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/import/linestar', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!data.success) {
        setError(data.error || 'Import failed');
        return;
      }

      // Success
      enqueueSnackbar(data.message, { variant: 'success' });
    } catch (err) {
      setError('Network error. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Button
        variant="contained"
        startIcon={loading ? <CircularProgress size={20} /> : <Upload />}
        disabled={loading}
        component="label"
      >
        Import LineStar Data
        <input
          type="file"
          hidden
          accept=".xlsx"
          onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
        />
      </Button>

      {error && (
        <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
    </Box>
  );
};
```

### User-Friendly Error Messages

**Good Error Messages:**
- ✅ "Missing required columns: Name, Team, Position"
- ✅ "Unable to generate lineups. Try relaxing exposure limits."
- ✅ "Player 'Christian McCaffrey' not found in Week 9 data"
- ✅ "File must be .xlsx format (Excel)"

**Bad Error Messages:**
- ❌ "KeyError: 'Name'"
- ❌ "Optimization failed"
- ❌ "500 Internal Server Error"
- ❌ "NoneType object has no attribute 'salary'"

### Logging Strategy

**Backend Logging:**
```python
import logging

logger = logging.getLogger(__name__)

# Log errors with context
try:
    result = import_data(file_path, week_id)
except DataImportError as e:
    logger.error(
        f"Data import failed for week {week_id}: {e.message}",
        extra={"week_id": week_id, "file_path": file_path}
    )
    raise
```

**Frontend Logging (Phase 3: Sentry):**
```typescript
import * as Sentry from '@sentry/react';

try {
  // ... code ...
} catch (error) {
  Sentry.captureException(error, {
    tags: { component: 'PlayerTable', weekId },
  });
  throw error;
}
```

### Critical Error Scenarios

**Zero Data Import Errors (MVP Priority):**
- Validate file format before processing
- Check required columns exist
- Validate data types (salary = int, projection = float)
- Handle duplicate player keys gracefully
- Provide clear feedback on success/failure

**Lineup Generation Failures:**
- Check player pool is not empty
- Validate salary cap constraints
- Handle infeasible optimization problems
- Provide actionable suggestions (relax constraints)

**Database Connection Errors:**
- Retry transient failures (3 attempts)
- Fail gracefully with user-friendly message
- Log full error for debugging
