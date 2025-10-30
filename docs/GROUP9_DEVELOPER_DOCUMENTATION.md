# Player Management Developer Documentation

**Version:** 1.0
**Date:** October 29, 2025
**Scope:** Task 9.3 - Developer Documentation

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Component Documentation](#component-documentation)
3. [Hook Interfaces](#hook-interfaces)
4. [Service Documentation](#service-documentation)
5. [API Endpoints](#api-endpoints)
6. [Database Schema](#database-schema)
7. [Development Setup](#development-setup)
8. [Testing Guide](#testing-guide)

---

## Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Frontend (React/TypeScript)           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  PlayerManagementPage                                  │
│  ├─ UnmatchedPlayersSection                            │
│  │  └─ UnmatchedPlayerCard[]                           │
│  ├─ PlayerTableControls                                │
│  │  ├─ PlayerSearchBox                                 │
│  │  └─ PlayerTableFilters                              │
│  ├─ PlayerTable (TanStack Table)                       │
│  │  └─ PlayerTableRow[] (virtual scrolling)            │
│  │     └─ ExpandedRow                                  │
│  └─ PlayerMappingModal                                 │
│     ├─ PlayerInfo                                      │
│     ├─ FuzzyMatchSuggestions                           │
│     └─ ActionButtons                                   │
│                                                         │
│  Hooks:                                                 │
│  ├─ usePlayerManagement (data fetching)                │
│  ├─ usePlayerFiltering (filter state)                  │
│  ├─ usePlayerSorting (sort state)                      │
│  └─ usePlayerMapping (modal workflow)                  │
│                                                         │
│  Store:                                                 │
│  └─ useWeekStore (current week selection)              │
│                                                         │
└─────────────────────────────────────────────────────────┘
         │
         │ HTTP Requests
         ▼
┌─────────────────────────────────────────────────────────┐
│                Backend (FastAPI)                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  players_router.py                                     │
│  ├─ GET /api/players/by-week/{week_id}                │
│  ├─ GET /api/players/unmatched/{week_id}              │
│  ├─ GET /api/players/search                           │
│  └─ GET /api/players/suggestions/{id}                 │
│                                                         │
│  unmatched_players_router.py                           │
│  ├─ POST /api/unmatched-players/map                   │
│  └─ POST /api/unmatched-players/ignore                │
│                                                         │
│  Services:                                              │
│  ├─ PlayerManagementService                            │
│  │  ├─ get_players_by_week()                          │
│  │  ├─ get_unmatched_players()                        │
│  │  └─ search_players()                               │
│  ├─ PlayerAliasService                                 │
│  │  ├─ create_alias()                                 │
│  │  └─ resolve_alias()                                │
│  └─ PlayerMatcher (existing)                           │
│     └─ fuzzy_match()                                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
         │
         │ SQL Queries
         ▼
┌─────────────────────────────────────────────────────────┐
│              PostgreSQL Database                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Tables:                                                │
│  ├─ weeks                                               │
│  ├─ player_pools                                        │
│  ├─ unmatched_players                                   │
│  ├─ player_aliases                                      │
│  └─ import_history                                      │
│                                                         │
│  Indexes (Performance):                                 │
│  ├─ idx_player_pools_week_position_team                │
│  ├─ idx_player_pools_week_key                          │
│  └─ idx_player_aliases_name                            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Page Load**
   - PlayerManagementPage mounts
   - usePlayerManagement hook calls GET /api/players/by-week/{week_id}
   - Backend returns player data with match status
   - Frontend renders table + unmatched section

2. **User Actions**
   - Filter change → Local state update → Table re-render (no API call)
   - Sort change → Local state update → Table re-render (no API call)
   - Search → Local filter → Table re-render (no API call)
   - Map player → POST /api/unmatched-players/map → React Query invalidation → Refetch

3. **Mapping Workflow**
   - User clicks "Fix" button
   - PlayerMappingModal opens
   - Modal fetches suggestions via GET /api/players/suggestions/{id}
   - User selects player + confirms
   - POST /api/unmatched-players/map called
   - Success → Cache invalidated → Table re-fetches data
   - Player moves to matched section

---

## Component Documentation

### PlayerManagementPage

**Location:** `/frontend/src/pages/PlayerManagementPage.tsx`

**Purpose:** Main page container for player management feature

**Props:** None (uses hooks and store)

**State:**
```typescript
{
  currentWeek: Week | null;
  players: Player[];
  isLoading: boolean;
  error: string | null;
}
```

**Key Methods:**
- `useEffect()` - Fetch players when week changes
- `handleWeekChange()` - Update week selection
- `handlePlayerMapped()` - Refresh player list

**Usage:**
```tsx
import PlayerManagementPage from '@/pages/PlayerManagementPage';

// In router
<Route path="/players" element={<PlayerManagementPage />} />
```

### PlayerTable

**Location:** `/frontend/src/components/players/PlayerTable.tsx`

**Purpose:** Render sortable, filterable player data table with virtual scrolling

**Props:**
```typescript
interface PlayerTableProps {
  players: Player[];
  isLoading: boolean;
  onRowClick?: (player: Player) => void;
  onExpandChange?: (playerId: number, expanded: boolean) => void;
}
```

**Features:**
- TanStack Table for sorting/filtering
- TanStack Virtual for virtualization (500+ rows)
- Responsive columns (hide/show based on breakpoint)
- Row expansion for additional details
- Status badges for match status

**Example:**
```tsx
<PlayerTable
  players={players}
  isLoading={isLoading}
  onRowClick={(player) => console.log(player)}
/>
```

### PlayerMappingModal

**Location:** `/frontend/src/components/players/PlayerMappingModal.tsx`

**Purpose:** Modal dialog for mapping unmatched players

**Props:**
```typescript
interface PlayerMappingModalProps {
  open: boolean;
  unmatchedPlayer: UnmatchedPlayer;
  suggestions: Player[];
  onClose: () => void;
  onConfirm: (selectedPlayer: Player) => void;
  isLoading?: boolean;
}
```

**Features:**
- Displays unmatched player info
- Shows fuzzy match suggestions (up to 5)
- Manual search for alternatives
- Selection confirmation workflow
- Error handling and loading states

**Example:**
```tsx
const [selectedPlayer, setSelectedPlayer] = useState<Player | null>(null);

<PlayerMappingModal
  open={modalOpen}
  unmatchedPlayer={unmatchedPlayer}
  suggestions={suggestions}
  onClose={() => setModalOpen(false)}
  onConfirm={(player) => {
    mapPlayer(unmatchedPlayer.id, player.player_key);
    setSelectedPlayer(null);
  }}
/>
```

### PlayerTableFilters

**Location:** `/frontend/src/components/players/PlayerTableFilters.tsx`

**Purpose:** Filter controls for position, team, and unmatched status

**Props:**
```typescript
interface PlayerTableFiltersProps {
  onFilterChange: (filters: PlayerFilters) => void;
  positions: string[];
  teams: string[];
  activeFilters?: PlayerFilters;
}
```

**Features:**
- Multi-select dropdown for positions
- Multi-select dropdown for teams
- Unmatched-only toggle
- Clear all filters button
- Real-time filter updates

**Example:**
```tsx
<PlayerTableFilters
  positions={['QB', 'RB', 'WR', 'TE', 'DST']}
  teams={['KC', 'LAR', 'MIA']}
  onFilterChange={(filters) => applyFilters(filters)}
/>
```

### UnmatchedPlayersSection

**Location:** `/frontend/src/components/players/UnmatchedPlayersSection.tsx`

**Purpose:** Display alert and cards for unmatched players

**Props:**
```typescript
interface UnmatchedPlayersSectionProps {
  players: UnmatchedPlayer[];
  count: number;
  onFixClick: (playerId: number) => void;
  isLoading?: boolean;
}
```

**Features:**
- Orange/red alert styling
- Count display
- Player cards with Fix buttons
- Responsive grid layout

**Example:**
```tsx
<UnmatchedPlayersSection
  players={unmatchedPlayers}
  count={unmatchedPlayers.length}
  onFixClick={(id) => openMappingModal(id)}
/>
```

---

## Hook Interfaces

### usePlayerManagement

**Location:** `/frontend/src/hooks/usePlayerManagement.ts`

**Purpose:** Centralized player data management and fetching

**Interface:**
```typescript
interface UsePlayerManagementReturn {
  players: Player[];
  unmatched_players: UnmatchedPlayer[];
  isLoading: boolean;
  error: string | null;
  weekId: number | null;
  refetch: () => Promise<void>;
  invalidateCache: () => void;
}

const usePlayerManagement = (weekId: number): UsePlayerManagementReturn => {
  // Implementation
}
```

**Usage:**
```typescript
const { players, unmatched_players, isLoading, error, refetch } = usePlayerManagement(weekId);

// In component
useEffect(() => {
  if (weekChanged) {
    refetch();
  }
}, [weekChanged, refetch]);
```

**Features:**
- Uses React Query for server state
- 5-minute stale time for caching
- Automatic error handling
- Manual refetch capability
- Cache invalidation on mapping

### usePlayerFiltering

**Location:** `/frontend/src/hooks/usePlayerFiltering.ts`

**Purpose:** Filter state and filtering logic

**Interface:**
```typescript
interface UsePlayerFilteringReturn {
  filters: PlayerFilters;
  setFilters: (filters: PlayerFilters) => void;
  clearFilters: () => void;
  filteredPlayers: Player[];
  isFilterActive: boolean;
}

const usePlayerFiltering = (players: Player[]): UsePlayerFilteringReturn => {
  // Implementation
}
```

**Usage:**
```typescript
const { filters, filteredPlayers, setFilters, clearFilters } = usePlayerFiltering(allPlayers);

// Apply filters
setFilters({
  positions: ['QB'],
  teams: ['KC'],
  searchQuery: '',
  unmatchedOnly: false
});
```

### usePlayerMapping

**Location:** `/frontend/src/hooks/usePlayerMapping.ts`

**Purpose:** Unmatched player mapping workflow management

**Interface:**
```typescript
interface UsePlayerMappingReturn {
  modalOpen: boolean;
  currentUnmatchedPlayer: UnmatchedPlayer | null;
  suggestions: Player[];
  isLoadingSuggestions: boolean;
  selectedPlayer: Player | null;
  openModal: (player: UnmatchedPlayer) => Promise<void>;
  closeModal: () => void;
  selectPlayer: (player: Player) => void;
  confirmMapping: () => Promise<boolean>;
  skipMapping: () => void;
}

const usePlayerMapping = (): UsePlayerMappingReturn => {
  // Implementation
}
```

**Usage:**
```typescript
const {
  modalOpen,
  currentUnmatchedPlayer,
  suggestions,
  selectedPlayer,
  openModal,
  closeModal,
  confirmMapping
} = usePlayerMapping();

// Open modal
await openModal(unmatchedPlayer);

// Confirm mapping
const success = await confirmMapping();
```

---

## Service Documentation

### PlayerManagementService

**Location:** `/backend/services/player_management_service.py`

**Purpose:** Orchestrate player data retrieval and transformation

**Methods:**

#### get_players_by_week
```python
def get_players_by_week(
    session: Session,
    week_id: int,
    position: Optional[str] = None,
    team: Optional[str] = None,
    sort_by: str = "name",
    sort_dir: str = "asc",
    limit: int = 200,
    offset: int = 0
) -> PlayerResponse:
    """
    Fetch all players for a week with optional filtering.

    Args:
        session: Database session
        week_id: Week ID to fetch
        position: Filter by position (QB, RB, WR, TE, DST)
        team: Filter by team (2-3 char abbrev)
        sort_by: Column to sort by
        sort_dir: Sort direction (asc/desc)
        limit: Max results (1-200)
        offset: Pagination offset

    Returns:
        PlayerResponse with players list and metadata

    Raises:
        WeekNotFound: If week_id doesn't exist
        InvalidFilter: If filters invalid
    """
```

#### get_unmatched_players
```python
def get_unmatched_players(
    session: Session,
    week_id: int,
    with_suggestions: bool = True,
    limit: int = 50
) -> UnmatchedPlayersResponse:
    """
    Fetch unmatched players for a week with suggestions.

    Returns:
        UnmatchedPlayersResponse with unmatched list
    """
```

#### search_players
```python
def search_players(
    session: Session,
    query: str,
    limit: int = 20,
    week_id: Optional[int] = None
) -> SearchResponse:
    """
    Search for players by name.

    Returns:
        SearchResponse with matching players
    """
```

**Usage:**
```python
from backend.services.player_management_service import PlayerManagementService

service = PlayerManagementService()

# Get QBs from KC
players = service.get_players_by_week(
    session=db,
    week_id=42,
    position="QB",
    team="KC",
    sort_by="salary",
    sort_dir="desc"
)

# Get unmatched
unmatched = service.get_unmatched_players(
    session=db,
    week_id=42,
    with_suggestions=True
)
```

### PlayerAliasService

**Location:** `/backend/services/player_alias_service.py`

**Purpose:** Manage player alias creation and resolution

**Methods:**

#### create_alias
```python
def create_alias(
    session: Session,
    alias_name: str,
    canonical_player_key: str
) -> PlayerAlias:
    """
    Create or update a global alias.

    Args:
        session: Database session
        alias_name: Imported name (e.g., "P. Mahomes")
        canonical_player_key: Target player key

    Returns:
        PlayerAlias record

    Raises:
        AlreadyMapped: If different mapping exists
    """
```

#### resolve_alias
```python
def resolve_alias(
    session: Session,
    alias_name: str
) -> Optional[str]:
    """
    Look up canonical player key for alias.

    Returns:
        Player key or None if not found
    """
```

#### get_all_aliases
```python
def get_all_aliases(session: Session) -> List[PlayerAlias]:
    """
    Fetch all aliases.

    Returns:
        List of all PlayerAlias records
    """
```

**Usage:**
```python
from backend.services.player_alias_service import PlayerAliasService

service = PlayerAliasService()

# Create alias
alias = service.create_alias(
    session=db,
    alias_name="P. Mahomes",
    canonical_player_key="patrick_mahomes_KC_QB"
)

# Resolve alias
player_key = service.resolve_alias(
    session=db,
    alias_name="P. Mahomes"
)
```

---

## API Endpoints

### Implemented Endpoints

**GET /api/players/by-week/{week_id}**
- Query all players for a week
- Supports filtering, sorting, pagination
- Response includes match status for each player

**GET /api/players/unmatched/{week_id}**
- Query unmatched players only
- Includes fuzzy match suggestions
- Limited to 100 unmatched players

**GET /api/players/search**
- Full-text search for players
- Optional week filter
- Returns player info with week availability

**GET /api/players/suggestions/{unmatched_player_id}**
- Get fuzzy match suggestions for specific player
- Returns top 5-10 matches with scores

**POST /api/unmatched-players/map**
- Map unmatched player to canonical player
- Creates global alias automatically
- Returns confirmation with alias details

**POST /api/unmatched-players/ignore**
- Mark unmatched player as ignored
- Player stays in unmatched list but hidden

### Endpoint Response Formats

All endpoints return standardized response:

```json
{
  "success": boolean,
  "data": object | array | null,
  "error": string | null,
  "message": string | null
}
```

### Error Handling

See `/docs/GROUP9_API_DOCUMENTATION.md` for complete error code reference.

---

## Database Schema

### player_pools
```sql
CREATE TABLE player_pools (
  id SERIAL PRIMARY KEY,
  week_id INTEGER NOT NULL,
  player_key VARCHAR(255) NOT NULL,
  name VARCHAR(255) NOT NULL,
  team VARCHAR(10),
  position VARCHAR(5),
  salary INTEGER,
  projection FLOAT,
  ownership FLOAT,
  ceiling FLOAT,
  floor FLOAT,
  notes TEXT,
  source VARCHAR(50),
  uploaded_at TIMESTAMP,

  FOREIGN KEY (week_id) REFERENCES weeks(id),
  INDEX idx_player_pools_week_id (week_id),
  INDEX idx_player_pools_player_key (player_key),
  INDEX idx_player_pools_week_position_team (week_id, position, team)
);
```

### unmatched_players
```sql
CREATE TABLE unmatched_players (
  id SERIAL PRIMARY KEY,
  import_id UUID,
  imported_name VARCHAR(255),
  team VARCHAR(10),
  position VARCHAR(5),
  salary INTEGER,
  similarity_score FLOAT,
  status VARCHAR(20),

  FOREIGN KEY (import_id) REFERENCES import_history(id),
  INDEX idx_unmatched_import_status (import_id, status)
);
```

### player_aliases
```sql
CREATE TABLE player_aliases (
  id SERIAL PRIMARY KEY,
  alias_name VARCHAR(255) UNIQUE,
  canonical_player_key VARCHAR(255),
  created_at TIMESTAMP,
  updated_at TIMESTAMP,

  INDEX idx_player_aliases_name (alias_name),
  INDEX idx_player_aliases_canonical_key (canonical_player_key)
);
```

---

## Development Setup

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL 12+
- Git

### Frontend Setup

```bash
# Install dependencies
cd /Users/raybargas/Documents/Cortex/frontend
npm install

# Start development server
npm run dev

# Run tests
npm test

# Build for production
npm run build
```

### Backend Setup

```bash
# Install dependencies
cd /Users/raybargas/Documents/Cortex/backend
pip install -r requirements.txt

# Run migrations
cd /Users/raybargas/Documents/Cortex
alembic upgrade head

# Start development server
cd backend
uvicorn main:app --reload --port 8000

# Run tests
pytest tests/
```

### Environment Variables

**Frontend (.env):**
```
VITE_API_URL=http://localhost:8000/api
VITE_API_TIMEOUT=5000
```

**Backend (.env):**
```
DATABASE_URL=postgresql://user:password@localhost/player_management
JWT_SECRET=your_secret_key
DEBUG=true
```

### Running Locally

```bash
# Terminal 1: Backend
cd backend
uvicorn main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Database (if using Docker)
docker-compose up -d postgres
```

---

## Testing Guide

### Unit Tests

**Backend:**
```bash
cd /Users/raybargas/Documents/Cortex
pytest tests/unit/test_player_management_service.py -v
pytest tests/unit/test_player_alias_service.py -v
pytest tests/unit/test_players_router.py -v
```

**Frontend:**
```bash
cd frontend
npm run test:unit

# Watch mode
npm run test:watch
```

### Integration Tests

```bash
# Backend
pytest tests/integration/test_player_management_integration.py -v

# Frontend
npm run test:integration
```

### E2E Tests

```bash
# Run Playwright tests
npx playwright test

# Run in headed mode (see browser)
npx playwright test --headed

# Run specific test
npx playwright test player-management.spec.ts
```

### Test Coverage

```bash
# Backend coverage
pytest tests/ --cov=backend --cov-report=html

# Frontend coverage
npm run test:coverage
```

### Writing Tests

**Backend Example:**
```python
def test_get_players_by_week_filters_by_position(db_session):
    # Arrange
    week = create_test_week(db_session)
    qb = create_test_player(db_session, week, position="QB")
    rb = create_test_player(db_session, week, position="RB")

    # Act
    result = PlayerManagementService.get_players_by_week(
        db_session,
        week.id,
        position="QB"
    )

    # Assert
    assert len(result.players) == 1
    assert result.players[0].position == "QB"
```

**Frontend Example:**
```typescript
it('should display unmatched players alert', async () => {
  const { getByText } = render(
    <UnmatchedPlayersSection
      players={[mockUnmatchedPlayer]}
      count={1}
      onFixClick={jest.fn()}
    />
  );

  expect(getByText(/1 Unmatched Player/i)).toBeInTheDocument();
});
```

---

## Debugging

### Common Issues

**1. Players Not Loading**
- Check network tab (DevTools)
- Verify API endpoint URL in .env
- Check backend logs for errors
- Verify week_id is valid

**2. Filter Not Working**
- Check filter state in Redux DevTools
- Verify filter values are correct format
- Check console for JavaScript errors

**3. Modal Not Opening**
- Check if modal state is updating
- Verify unmatchedPlayer prop is set
- Check console for React errors

**4. Database Connection Error**
- Verify DATABASE_URL in .env
- Check PostgreSQL is running
- Test connection: `psql $DATABASE_URL -c "SELECT 1"`

### Logging

**Backend:**
```python
import logging

logger = logging.getLogger(__name__)
logger.info(f"Fetching players for week {week_id}")
logger.error(f"Database error: {str(e)}")
```

**Frontend:**
```typescript
console.log('Player data:', players);
console.error('API error:', error);
```

### Profiling

**Backend:**
```python
import time

start = time.time()
result = service.get_players_by_week(...)
elapsed = time.time() - start
print(f"Query took {elapsed:.2f}s")
```

**Frontend:**
```typescript
console.time('fetch-players');
const data = await fetchPlayers();
console.timeEnd('fetch-players');
```

---

**Developer Documentation Complete**
**Last Updated:** October 29, 2025
**For Questions:** See README or contact development team
