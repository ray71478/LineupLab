# Reusable Code Analysis for Player Management Feature

## Executive Summary

Extensive analysis of the existing codebase identified **significant reusable code** that will accelerate development. This document details all reusable components, services, and patterns found, with implementation notes.

**Key Finding:** The unmatched players API router and player matcher service are production-ready and can be used directly without modification.

---

## Frontend Reusable Code

### 1. Material-UI Dark Theme Configuration

**File:** `/frontend/src/theme.ts`

**Reusable Content:**
```typescript
export const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    background: {
      default: '#0f0f1a',  // Update to #0a0a0a per spec
      paper: '#1a1a2e',
    },
    primary: {
      main: '#00d4ff',     // Update to #ff8c42 (orange) per spec
    },
    secondary: {
      main: '#7c3aed',
    },
    text: {
      primary: '#e5e7eb',
      secondary: '#9ca3af',
    },
    divider: 'rgba(255, 255, 255, 0.1)',
  },
  typography: {
    fontFamily: 'Roboto, Arial, sans-serif',
  },
  components: {
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#0f0f1a',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        },
      },
    },
    // ... more component overrides
  },
});
```

**How to Reuse:**
- Extend existing theme with Player Management components
- Update primary color to #ff8c42 (orange accent) for buttons and badges
- Add component overrides for new button styles, modals, badges
- Keep existing text colors and background

**Implementation Note:**
The theme already provides excellent foundation. Only needs:
1. Update primary color to orange (#ff8c42)
2. Add MuiButton override for orange styling
3. Add MuiBadge component override for status badges
4. Add MuiModal/MuiDialog override for modal styling

---

### 2. WeekStatusBadge Component (Badge Pattern)

**File:** `/frontend/src/components/weeks/WeekStatusBadge.tsx`

**Reusable Pattern:**
```typescript
export interface WeekStatusBadgeProps {
  status: 'active' | 'upcoming' | 'completed';
  importStatus?: 'pending' | 'imported' | 'error';
  isCurrentWeek?: boolean;
  compact?: boolean;
}

// Key features:
// - Icon selection based on status
// - Color-coded display
// - Tooltip for additional context
// - Glow animation for current state
// - Material-UI icons integration
```

**How to Reuse:**
For **PlayerStatusBadge** component:
- Adapt the icon selection logic
- Use similar color scheme (green for matched, orange/red for unmatched)
- Simplify (no glow animation needed for player status)
- Keep tooltip pattern for status explanation

**Implementation Note:**
```typescript
// PlayerStatusBadge (simplified version of WeekStatusBadge)
export const PlayerStatusBadge: React.FC<PlayerStatusBadgeProps> = ({
  status,  // 'matched' | 'unmatched'
  compact = false,
}) => {
  const iconConfig = status === 'matched'
    ? { icon: CheckCircleIcon, color: '#4caf50', label: 'Matched' }
    : { icon: WarningIcon, color: '#ff5722', label: 'Unmatched' };

  // Rest similar to WeekStatusBadge
};
```

---

### 3. ImportDataButton Component (Modal & Notification Pattern)

**File:** `/frontend/src/components/import/ImportDataButton.tsx`

**Reusable Patterns:**

#### Pattern 1: Modal Workflow
```typescript
// Shows how to implement modal dialogs with lifecycle
// Example: WeekMismatchDialog component structure
// - Open/close state management
// - Props for content and callbacks
// - Loading state during async operations
// - Error handling and display
```

#### Pattern 2: Snackbar Notifications
```typescript
<Snackbar
  open={showSuccess}
  autoHideDuration={6000}
  onClose={() => setShowSuccess(false)}
  anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
>
  <Alert onClose={() => setShowSuccess(false)} severity="success">
    {successMessage}
  </Alert>
</Snackbar>
```

#### Pattern 3: File Input Handling
```typescript
const fileInputRef = useRef<HTMLInputElement>(null);

const handleImportTypeSelect = (type: ImportType) => {
  // Trigger file input dialog
  fileInputRef.current?.click();
};

const handleFileSelected = async (event: React.ChangeEvent<HTMLInputElement>) => {
  const file = event.target.files?.[0];
  if (!file) return;
  // Process file...
};

// Hidden file input
<input
  ref={fileInputRef}
  type="file"
  accept=".xlsx"
  onChange={handleFileSelected}
  style={{ display: 'none' }}
/>
```

**How to Reuse:**

For **PlayerMappingModal:**
- Use similar modal open/close pattern
- Apply Snackbar for success/error messages after mapping
- Handle async API calls with loading state

For **PlayerTableFilters:**
- Use file input pattern if adding import/export (Phase 2)
- Apply notification pattern for bulk operations

---

### 4. WeekStore (Zustand Store Pattern)

**File:** `/frontend/src/store/weekStore.ts`

**Reusable Pattern:**
```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useWeekStore = create<WeekState>()(
  persist(
    (set, get) => ({
      // State
      currentYear: new Date().getFullYear(),
      currentWeek: null,
      weeks: [],
      availableYears: [2025, 2026, 2027, 2028, 2029, 2030],
      isLoading: false,
      error: null,

      // Actions
      setCurrentYear: (year: number) => set({ currentYear: year }),
      setCurrentWeek: (week: number) => set({ currentWeek: week }),
      setWeeks: (weeks: Week[]) => set({ weeks }),
      setError: (error: string | null) => set({ error }),

      // Selectors
      getCurrentWeekData: () => {
        const state = get();
        return state.weeks.find(w => w.week_number === state.currentWeek) || null;
      },
    }),
    {
      name: 'week-store',
      version: 1,
    }
  )
);
```

**How to Reuse:**

For **Optional PlayerStore** (if filter persistence needed):
```typescript
export const usePlayerStore = create<PlayerFilterState>()(
  persist(
    (set, get) => ({
      // Filter state
      selectedPositions: [],
      selectedTeams: [],
      showUnmatchedOnly: false,
      searchQuery: '',
      sortColumn: 'name',
      sortDirection: 'asc',
      columnVisibility: { /* ... */ },

      // Actions
      setSelectedPositions: (positions: string[]) =>
        set({ selectedPositions: positions }),
      // ... etc
    }),
    {
      name: 'player-filter-store',
      version: 1,
    }
  )
);
```

**Key Benefits:**
- Persists to localStorage automatically
- Type-safe selectors
- Middleware support for versioning

---

### 5. useDataImport Hook (State Management Pattern)

**File:** `/frontend/src/hooks/useDataImport.ts`

**Reusable Pattern:**
```typescript
// Shows pattern for:
// - Async operations with loading state
// - Error handling
// - Result caching
// - State management for complex workflows

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
```

**How to Reuse:**

For **usePlayerManagement hook:**
```typescript
const {
  players,
  isLoading,
  error,
  unmatchedCount,
  fetchPlayers,
  refetch,
} = usePlayerManagement(weekId);
```

For **usePlayerMapping hook:**
```typescript
const {
  isLoading,
  error,
  mapPlayer,
  getUnmatchedPlayer,
  getSuggestions,
} = usePlayerMapping();
```

**Pattern Elements to Reuse:**
- Try-catch for error handling
- useState for isLoading, error, data states
- useCallback for async functions
- useEffect for side effects
- Return object with state + functions

---

### 6. useWeeks Hook (Data Fetching Pattern)

**File:** `/frontend/src/hooks/useWeeks.ts`

**Reusable Pattern:**
```typescript
// Shows pattern for:
// - Fetching data from backend
// - Handling loading states
// - Managing errors
// - Caching results

export const useWeeks = () => {
  // Fetch weeks from API
  // Return weeks, isLoading, error
};
```

**How to Reuse:**

For **usePlayerData hook:**
```typescript
export const usePlayerData = (weekId: number) => {
  // Similar pattern to useWeeks
  // Fetch players from /api/players/by-week/{weekId}
  // Return players, isLoading, error, refetch
};
```

---

### 7. React Router Structure (Navigation Pattern)

**File:** `/frontend/src/components/layout/MainLayout.tsx`

**Reusable Pattern:**
- Route organization in main layout
- Navigation links setup
- Theme provider wrapper

**How to Reuse:**
- Add `/players` route to MainLayout
- Import PlayerManagementPage component
- Add "Players" link to navigation menu (if present)

---

### 8. Material-UI Component Usage

**Reusable Components from MUI:**
- **Button:** Used throughout (existing)
- **Menu/MenuItem:** Dropdown patterns
- **Modal/Dialog:** Modal base component
- **Table/TablePagination:** Table structure (can reuse for reference)
- **Box/Container:** Layout containers
- **TextField/Input:** Form inputs
- **Select:** Dropdown selects
- **Badge:** Status indicators
- **Tooltip:** Additional information
- **Snackbar/Alert:** Notifications
- **CircularProgress:** Loading spinner
- **TextField:** Search input
- **Checkbox:** Filter options
- **Chip:** Tag-like displays

**Note:** The project uses Material-UI 5+, which provides all components needed.

---

## Backend Reusable Code

### 1. Unmatched Players Router (CRITICAL - READY TO USE)

**File:** `/backend/routers/unmatched_players_router.py`

**Status:** PRODUCTION-READY - Use directly without modification

**Existing Endpoints (Exact match to spec requirements):**

#### GET /api/unmatched-players?import_id={uuid}&status={status}
```python
@router.get("")
async def get_unmatched_players(
    import_id: str = Query(..., description="Required: Import ID (UUID)"),
    status: Optional[str] = Query(None, description="Optional: Filter by status"),
    db: Any = Depends(_get_current_db_dependency),
) -> dict:
    """
    Returns:
    {
        "success": true,
        "unmatched_players": [
            {
                "id": 456,
                "imported_name": "P. Mahomes",
                "team": "KC",
                "position": "QB",
                "suggested_player_key": "patrick_mahomes_KC_QB",
                "similarity_score": 0.82,
                "status": "pending|mapped|ignored"
            }
        ]
    }
    """
```

#### POST /api/unmatched-players/map
```python
@router.post("/map")
async def map_unmatched_player(
    request: MapPlayerRequest,
    db: Any = Depends(_get_current_db_dependency),
) -> dict:
    """
    Request body:
    {
        "unmatched_player_id": 456,
        "canonical_player_key": "patrick_mahomes_KC_QB"
    }

    Returns:
    {
        "success": true,
        "message": "Alias mapped successfully"
    }

    Side effects:
    - Creates or updates player_aliases record
    - Updates unmatched_players status to 'mapped'
    - Stores suggested_player_key for mapping
    """
```

#### POST /api/unmatched-players/ignore
```python
@router.post("/ignore")
async def ignore_unmatched_player(
    request: IgnorePlayerRequest,
    db: Any = Depends(_get_current_db_dependency),
) -> dict:
    """
    Marks player as ignored (no mapping created)
    """
```

**Why It's Perfect for Reuse:**
- Handles all database transactions correctly
- Validates input (unmatched player exists, canonical player exists)
- Creates aliases automatically
- Updates status consistently
- Error handling with meaningful messages
- Transaction rollback on failure

**How to Integrate:**
1. Frontend PlayerMappingModal calls POST /api/unmatched-players/map
2. Backend creates alias automatically
3. Frontend shows success notification
4. Table/unmatched section updates via React Query invalidation

---

### 2. PlayerMatcher Service (Fuzzy Matching - READY TO USE)

**File:** `/backend/services/player_matcher.py`

**Status:** PRODUCTION-READY - Use directly, no modifications needed

**Key Methods:**

#### fuzzy_match()
```python
def fuzzy_match(
    self,
    imported_name: str,
    team: str,
    position: str,
    existing_players: list[dict],
    threshold: Optional[float] = None,
) -> tuple[Optional[str], float]:
    """
    Returns: (player_key or None, similarity_score)

    Behavior:
    - Filters candidates by team and position (exact match)
    - Uses rapidfuzz.fuzz.ratio for matching
    - Returns None if score below 85% threshold (0.85)
    - Returns similarity as 0-1 float
    """
```

#### normalize_player_name()
```python
def normalize_player_name(self, name: str) -> str:
    """
    Normalizes names:
    - Remove suffixes: Jr., Sr., III, II, IV
    - Remove prefixes: D', O'
    - Remove punctuation: apostrophes, periods, hyphens
    - Convert to lowercase
    - Replace spaces with underscores

    Examples:
    - "D'Andre Swift Jr." → "dandre_swift"
    - "A.J. Brown" → "aj_brown"
    """
```

#### generate_player_key()
```python
def generate_player_key(self, name: str, team: str, position: str) -> str:
    """
    Generates composite key: {normalized_name}_{team}_{position}

    Example: "christian_mccaffrey_SF_RB"
    """
```

**How to Reuse:**
1. Create new endpoint GET /api/players/suggestions/{unmatched_player_id}
2. Instantiate PlayerMatcher with database session
3. Call fuzzy_match() with unmatched player vs. existing players
4. Return suggestions with similarity scores
5. Frontend displays to user for selection

**Implementation Example:**
```python
from backend.services.player_matcher import PlayerMatcher

matcher = PlayerMatcher(session=db)

unmatched_players = get_unmatched_players(import_id)
existing_players = get_existing_players(team, position)

suggestions = []
for existing in existing_players[:10]:  # Top 10 by similarity
    player_key, score = matcher.fuzzy_match(
        unmatched["imported_name"],
        unmatched["team"],
        unmatched["position"],
        [existing],
        threshold=0.70  # Lower threshold to get suggestions
    )
    if score > 0.70:
        suggestions.append({
            "player_key": player_key,
            "name": existing["name"],
            "similarity_score": score,
            ...
        })

return sorted(suggestions, key=lambda x: x["similarity_score"], reverse=True)[:5]
```

---

### 3. Database Models & ORM Patterns

**Note:** The codebase uses raw SQL with SQLAlchemy text() queries. No Pydantic models for tables yet.

**Reusable SQL Patterns:**

#### Raw SQL with Parameter Binding
```python
from sqlalchemy import text

stmt = text("""
    SELECT id, name, team, position, salary
    FROM player_pools
    WHERE week_id = :week_id AND position = :position
    ORDER BY name
""")
result = db.execute(stmt, {"week_id": week_id, "position": "QB"}).fetchall()
```

**How to Reuse:**
Use same pattern for new player queries:
- Always use parameterized queries (prevent SQL injection)
- Use text() for complex queries
- Avoid SELECT * (specify columns)
- Add LIMIT for pagination
- Create indexes for WHERE clauses

---

### 4. FastAPI Router Structure (Pattern)

**File:** `/backend/routers/unmatched_players_router.py`, `/backend/routers/week_router.py`

**Reusable Pattern:**
```python
from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/api/unmatched-players", tags=["unmatched-players"])

# Placeholder - will be set by main.py
get_db = None

def _get_current_db_dependency():
    """Wrapper to get current get_db function at runtime"""
    import sys
    current_module = sys.modules[__name__]
    if current_module.get_db is None:
        raise RuntimeError("get_db not initialized")
    yield from current_module.get_db()

class MyRequest(BaseModel):
    """Request schema"""
    field: str

class MyResponse(BaseModel):
    """Response schema"""
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None

@router.get("")
async def my_endpoint(
    param: str = Query(...),
    db: Any = Depends(_get_current_db_dependency),
) -> dict:
    """Endpoint implementation"""
    try:
        # Query database
        result = db.execute(...)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {"success": False, "error": "Error message"}
```

**How to Reuse:**
1. Create `players_router.py` with similar structure
2. Use same _get_current_db_dependency() pattern
3. Define Pydantic request/response models
4. Implement endpoints with error handling
5. Return consistent response format: {success, data/error, message}

---

## Database Schema (All Tables Exist - No Changes Needed)

### player_pools Table
```sql
CREATE TABLE player_pools (
    id INTEGER PRIMARY KEY,
    week_id INTEGER NOT NULL REFERENCES weeks(id),
    player_key VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    team VARCHAR(10) NOT NULL,
    position VARCHAR(10) CHECK (position IN ('QB', 'RB', 'WR', 'TE', 'DST')),
    salary INTEGER CHECK (salary BETWEEN 3000 AND 10000),
    projection FLOAT,
    ownership FLOAT,
    ceiling FLOAT,
    floor FLOAT,
    notes TEXT,
    source VARCHAR(50),
    uploaded_at TIMESTAMP,
    UNIQUE(week_id, player_key)
);

-- Existing indexes:
-- idx_player_pools_week_id
-- idx_player_pools_player_key
-- idx_player_pools_position
-- idx_player_pools_team
-- idx_player_pools_source
```

### unmatched_players Table
```sql
CREATE TABLE unmatched_players (
    id INTEGER PRIMARY KEY,
    import_id UUID NOT NULL,
    imported_name VARCHAR(255),
    team VARCHAR(10),
    position VARCHAR(10),
    salary INTEGER,
    suggested_player_key VARCHAR(255),
    similarity_score FLOAT,
    status VARCHAR(20) DEFAULT 'pending'
);

-- Can add indexes if needed:
-- CREATE INDEX idx_unmatched_status_import ON unmatched_players(import_id, status);
```

### player_aliases Table
```sql
CREATE TABLE player_aliases (
    id INTEGER PRIMARY KEY,
    alias_name VARCHAR(255) UNIQUE NOT NULL,
    canonical_player_key VARCHAR(255) NOT NULL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Can add index:
-- CREATE INDEX idx_player_aliases_name ON player_aliases(alias_name);
```

### weeks Table
```sql
CREATE TABLE weeks (
    id INTEGER PRIMARY KEY,
    season INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    status VARCHAR(20),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(season, week_number)
);

-- Existing indexes:
-- idx_weeks_week_number
-- idx_weeks_status
```

**What to Do:**
- Query these tables, no modifications needed
- Add optional performance indexes if needed
- Use existing constraints and unique constraints

---

## Styling & Theme Reusable Patterns

### Color Variables to Reuse
```typescript
// From theme.ts - update for Player Management
const COLORS = {
  background: '#0a0a0a',      // Black
  surface: '#1a1a2e',         // Dark gray
  surfaceHover: '#262641',    // Slightly lighter
  accentPrimary: '#ff8c42',   // Orange (UPDATE PRIMARY COLOR)
  accentDark: '#ff6b35',      // Dark orange
  accentLight: 'rgba(255, 140, 66, 0.1)',  // 10% opacity
  alert: '#ff5722',           // Orange-red
  success: '#4caf50',         // Green
  textPrimary: '#ffffff',     // White
  textSecondary: '#e5e7eb',   // Light gray
  textTertiary: '#9ca3af',    // Muted gray
  border: 'rgba(255, 255, 255, 0.1)',  // Standard border
  borderAccent: 'rgba(255, 140, 66, 0.4)',  // Orange with opacity
};
```

### Component Style Patterns
All components use MUI sx prop pattern:
```typescript
<Box
  sx={{
    backgroundColor: COLORS.surface,
    borderRadius: '8px',
    padding: '16px',
    border: `2px solid ${COLORS.accentPrimary}`,
    '&:hover': {
      backgroundColor: COLORS.surfaceHover,
      borderColor: COLORS.accentPrimary,
    },
    transition: 'all 0.2s ease-in-out',
  }}
>
  {children}
</Box>
```

**How to Reuse:**
- Copy color variables
- Follow sx prop pattern for all new components
- Apply 8px spacing unit consistently
- Use 0.2s transitions for hover states
- Use 8px border-radius for cards/buttons

---

## Testing Patterns to Reuse

### Frontend Test Pattern (if using Vitest/Jest)
The codebase has existing test files in `/frontend/src/components/__tests__/`

**Pattern to Reuse:**
```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Component } from './Component';

describe('Component', () => {
  it('should render', () => {
    render(<Component />);
    expect(screen.getByText('Expected Text')).toBeInTheDocument();
  });

  it('should handle user interaction', async () => {
    const user = userEvent.setup();
    render(<Component />);
    await user.click(screen.getByRole('button'));
    expect(screen.getByText('Result')).toBeInTheDocument();
  });
});
```

### Backend Test Pattern (pytest)
```python
import pytest
from backend.services.player_matcher import PlayerMatcher

@pytest.fixture
def matcher():
    return PlayerMatcher()

def test_fuzzy_match(matcher):
    result, score = matcher.fuzzy_match(
        "P. Mahomes",
        "KC",
        "QB",
        [{"name": "Patrick Mahomes", "player_key": "patrick_mahomes_KC_QB", ...}]
    )
    assert result == "patrick_mahomes_KC_QB"
    assert score >= 0.85
```

---

## Summary of Reusable Code Impact

### Estimated Code Reduction
- **Unmatched Players Router:** 100% reuse (297 lines saved)
- **PlayerMatcher Service:** 100% reuse (201 lines saved)
- **Material-UI Theme:** 95% reuse (70 lines saved)
- **Zustand Store Pattern:** 80% reuse (50 lines saved)
- **Hook Patterns:** 70% reuse (~100 lines saved)
- **Modal/Notification Pattern:** 60% reuse (~80 lines saved)

**Total Estimated Savings:** ~598 lines of code, ~25% of total new code

### Development Time Saved
- **Backend Development:** 4-5 hours saved (use existing router)
- **Fuzzy Matching:** 3-4 hours saved (use existing service)
- **Theme/Styling:** 5-6 hours saved (extend existing theme)
- **Hook Patterns:** 4-5 hours saved (follow established patterns)

**Total Time Saved:** ~16-20 hours (~12% of 145-hour estimate)

### Quality Improvements
- Using tested, production-ready code
- Consistency with existing patterns
- Reduced bugs through code reuse
- Easier maintenance (familiar patterns)

---

## Recommendations

### Priority 1: Use Existing Code
1. Use `unmatched_players_router.py` endpoints directly
2. Reuse `PlayerMatcher.fuzzy_match()` for suggestions
3. Extend Material-UI theme for orange accent color
4. Reuse Zustand store pattern for filters (optional)

### Priority 2: Follow Established Patterns
1. Use FastAPI router structure from existing routers
2. Follow raw SQL pattern with text() and parameterization
3. Use MUI sx prop for styling
4. Use React hook patterns from existing hooks

### Priority 3: Optional Reuse
1. Consider using existing WeekStatusBadge as template for PlayerStatusBadge
2. Reuse modal pattern from ImportDataButton for PlayerMappingModal
3. Reuse Snackbar notification pattern for success/error messages

### Priority 4: Create New (No Reuse Possible)
1. PlayerTable component (TanStack Table is new dependency)
2. PlayerTableFilters component (player-specific filtering)
3. PlayerSearchBox component (player name search specific)
4. UnmatchedPlayersSection component (unique to this feature)
5. FuzzyMatchSuggestions component (unique rendering logic)

---

## Integration Checklist

### Backend Integration
- [ ] Verify unmatched_players_router endpoints work
- [ ] Add GET /api/players/by-week/{week_id} endpoint
- [ ] Add GET /api/players/unmatched/{week_id} endpoint
- [ ] Add GET /api/players/suggestions/{player_id} endpoint
- [ ] Create PlayerManagementService for queries
- [ ] Create PlayerAliasService for alias logic
- [ ] Register players_router in main.py

### Frontend Integration
- [ ] Update theme.ts with orange primary color
- [ ] Add /players route to MainLayout
- [ ] Create PlayerManagementPage component
- [ ] Implement usePlayerManagement hook
- [ ] Build PlayerTable with TanStack Table
- [ ] Build PlayerMappingModal with API integration

### Testing Integration
- [ ] Write tests following established patterns
- [ ] Test unmatched_players_router endpoints
- [ ] Test fuzzy_match() functionality
- [ ] Test PlayerTable sorting/filtering
- [ ] Test modal workflow

---

## File References

### Reusable Frontend Files
- `/frontend/src/theme.ts` - Theme configuration
- `/frontend/src/components/weeks/WeekStatusBadge.tsx` - Badge pattern
- `/frontend/src/components/import/ImportDataButton.tsx` - Modal pattern
- `/frontend/src/store/weekStore.ts` - Store pattern
- `/frontend/src/hooks/useDataImport.ts` - Hook pattern
- `/frontend/src/hooks/useWeeks.ts` - Data fetching pattern
- `/frontend/src/components/layout/MainLayout.tsx` - Navigation pattern

### Reusable Backend Files
- `/backend/routers/unmatched_players_router.py` - API router (CRITICAL)
- `/backend/services/player_matcher.py` - Fuzzy matching (CRITICAL)
- `/backend/routers/week_router.py` - Router structure reference
- `/backend/services/week_management_service.py` - Service pattern reference

### Database Files
- `/alembic/versions/001_create_data_import_tables.py` - Schema reference
- `alembic/versions/002_extend_weeks_system.py` - Migration reference

---

## Conclusion

The existing codebase provides extensive reusable components, particularly in the backend. The production-ready unmatched players router and fuzzy matcher service can be used directly without modification, significantly accelerating development.

By leveraging established patterns for state management, hooks, theming, and API integration, the development team can focus on building new features specific to player management without duplicating existing work.

**Estimated code reuse: ~25-30% of total implementation**
**Estimated time saved: ~16-20 hours (~12% reduction)**

