# Specification: Player Management Feature

## Executive Summary

The Player Management feature provides a dedicated interface for users to review, match, and manage player data imported from DFS platforms. This feature addresses the core workflow of handling unmatched players during the import process, enabling users to create global aliases and maintain data consistency across weeks. The feature includes a prominent unmatched players section, comprehensive player table with advanced filtering/sorting, and a manual mapping modal for resolving player matches.

**Current Phase:** Phase 1 - MVP
**Target Release:** Week of October 29, 2025
**Alignment:** Follows Week Management (Phase 0) and Data Import System (Phase 0)

---

## Goal

Enable users to efficiently review player data, resolve unmatched players through manual mapping, and create global aliases for consistent player matching across all future imports. The feature provides visibility into data quality issues while streamlining the resolution workflow.

---

## User Stories

### 1. View Player Management Dashboard
**As a** DFS manager,
**I want to** access a dedicated `/players` page from the main navigation,
**So that** I can manage and review all player data in one organized location.

**Acceptance Criteria:**
- A "Players" link appears in the main navigation
- Clicking the link navigates to `/players` page
- Page loads with player data from the current selected week
- Page title displays "Player Management" or similar
- Navigation indicates current page is active
- Page is accessible from any location in the app

### 2. View Unmatched Players Section
**As a** DFS manager,
**I want to** see unmatched players prominently at the top of the page with alert styling,
**So that** I can quickly identify and fix data quality issues before analysis.

**Acceptance Criteria:**
- Unmatched section displays before the main player table
- Section has orange/red alert styling (high visibility)
- Shows count of unmatched players (e.g., "3 Unmatched Players")
- Count updates in real-time when players are mapped
- Alert disappears when all players are matched (0 unmatched)
- Section shows unmatched player cards with: name, team, position, salary
- Each card has a "Fix" button to open mapping modal

### 3. View Comprehensive Player Table
**As a** DFS manager,
**I want to** see all players in a comprehensive table with sortable and filterable columns,
**So that** I can analyze player data, identify patterns, and make informed decisions.

**Acceptance Criteria:**
- Table displays minimum 10 columns:
  - Player Name (sortable, filterable)
  - Team (sortable, filterable)
  - Position (sortable, filterable)
  - Salary (sortable)
  - Projection (sortable)
  - Ownership % (sortable)
  - Notes (searchable)
  - Status (shows match status, filterable by unmatched)
  - Source (shows import source)
  - Last Updated (shows import timestamp)
- Additional columns for Phase 2:
  - Smart Score
  - Implied Team Total (ITT)
  - Last Week Comparison (salary, projection, ownership)
  - 80-20 Rule Indicator (pass catchers)
- Supports 150-200 players with virtual scrolling
- Column sorting works for all sortable columns (ascending/descending)
- Clicking column header toggles sort direction
- Sort indicator shows current sort state
- Table handles empty states gracefully

### 4. Filter Player Table
**As a** DFS manager,
**I want to** filter the player table by position, team, and match status,
**So that** I can focus on specific subsets of players for analysis.

**Acceptance Criteria:**
- Position filter allows multi-select (QB, RB, WR, TE, DST)
- Team filter allows multi-select (all NFL teams)
- Unmatched status filter shows only unmatched players
- Filters are chainable (can filter by position AND team)
- Filter UI includes clear button to reset all filters
- Active filters show visual indicator
- Table updates in real-time as filters change
- Filter state persists during session (not localStorage)

### 5. Expand Row for Additional Details
**As a** DFS manager,
**I want to** expand player rows to see additional details like ceiling, floor, and notes,
**So that** I can review all available information for a player without cluttering the main view.

**Acceptance Criteria:**
- Each player row has an expand toggle (chevron/arrow icon)
- Clicking expands to show additional columns:
  - Ceiling
  - Floor
  - Full notes/comments
  - Import source details
  - Week information
  - Historical context (Phase 2)
- Expanded state is per-row, not global
- Multiple rows can be expanded simultaneously
- Expanded rows show smooth animation
- Expand state resets when filters/sorts change

### 6. Search Player by Name
**As a** DFS manager,
**I want to** search for players by name in the player table,
**So that** I can quickly find specific players without scrolling.

**Acceptance Criteria:**
- Search box appears at the top of the player table
- Search filters results as user types
- Search is case-insensitive
- Partial name matches work (e.g., "Patrick" matches "Patrick Mahomes")
- Search clears when user clears the input
- Clear button appears when search has content
- Search works in combination with other filters
- No debounce delay (instant filtering)

### 7. Map Unmatched Player
**As a** DFS manager,
**I want to** manually map an unmatched player to a canonical player via a modal,
**So that** I can resolve mismatches caused by name variations or data inconsistencies.

**Acceptance Criteria:**
- "Fix" button on unmatched player card opens mapping modal
- Modal displays:
  - Unmatched player info (name, team, position, salary)
  - List of fuzzy-matched suggestions (up to 5) with similarity scores
  - Manual search box to find alternative matches
  - Selected match highlighted
- User can:
  - Select from suggestions
  - Search for alternative matches
  - Confirm selection
- On confirmation:
  - Player is marked as mapped in database
  - Player alias is created (global, week-agnostic)
  - Player moves from unmatched to matched section
  - Unmatched count decreases
  - Player table updates to show match
  - Modal closes
  - Success notification displays
- User can skip mapping without creating alias
- Modal closes without changes on cancel

### 8. Create Global Player Alias
**As a** DFS manager,
**I want to** create global aliases that persist across all future imports,
**So that** players with name variations are automatically matched in subsequent imports.

**Acceptance Criteria:**
- When user maps a player, an alias is automatically created
- Alias maps imported player name to canonical player key
- Alias is global, not week-specific
- Alias persists in `player_aliases` table
- If same alias is used again, it updates the canonical player key
- Aliases are applied automatically during future imports
- User can view all created aliases (future feature, Phase 2)
- User can delete/modify aliases (future feature, Phase 2)

### 9. View Player Match Status
**As a** DFS manager,
**I want to** see which players are matched vs. unmatched in the table,
**So that** I understand data quality at a glance.

**Acceptance Criteria:**
- Table shows match status for each player (matched/unmatched)
- Unmatched players have visual indicator (badge, color, icon)
- Status column is filterable
- Unmatched count displays prominently in alert section
- Can filter to show only unmatched players
- Matched players show green/success indicator
- Status updates in real-time

### 10. Mobile Responsive Player Management
**As a** mobile user,
**I want to** manage players on my mobile device with touch-optimized interface,
**So that** I can review data on the go.

**Acceptance Criteria:**
- Player table is responsive on mobile (< 768px)
- Critical columns always visible: name, team, position, salary
- Additional columns accessible via horizontal scroll
- Optional columns can be toggled on/off
- Tap targets are at least 44x44px
- Unmatched section displays as cards instead of table on mobile
- Modals display full-width on mobile
- Touch-friendly close buttons on modals
- No horizontal scroll required for unmatched section
- Filtering interface optimized for touch (dropdown menus vs. inline controls)

---

## Core Requirements

### Data Visibility
- Display all imported players from selected week's player pool
- Show unmatched players prominently with alert styling
- Display comprehensive player information with 10+ columns
- Support search and filtering across multiple dimensions
- Maintain real-time synchronization with database changes

### Unmatched Player Resolution
- Identify unmatched players during import process
- Provide fuzzy-matched suggestions with similarity scores
- Enable manual mapping with modal interface
- Create global aliases to prevent future mismatches
- Update player status in real-time after mapping

### Data Consistency
- Use player_key as canonical identifier
- Store aliases in player_aliases table (global scope)
- Apply aliases during future imports automatically
- Prevent duplicate mappings for same alias
- Maintain historical record of all mappings

### Performance & Scalability
- Handle 150-200 players per week efficiently
- Implement virtual scrolling to prevent DOM bloat
- Optimize database queries with proper indexing
- Lazy load additional columns/data
- Debounce search input for performance
- Cache player list during session

### Mobile Optimization
- Responsive design for screens < 768px
- Touch-optimized interface with 44x44px tap targets
- Full-width modals on mobile
- Horizontal scroll for optional columns
- Optimized filtering UI for touch devices

---

## Visual Design

### Design System Reference
This feature follows the design aesthetic specified in planning/requirements.md:
- **Primary background:** Black (#0a0a0a)
- **Accent:** Orange (#ff8c42) for interactive elements and alerts
- **Surfaces:** Dark gray (#1a1a2e) for cards and panels
- **Text:** White (#ffffff) primary, light gray (#e5e7eb) secondary
- **Borders:** Orange accents for active states, subtle dark borders
- **Typography:** Bold sans-serif headings, regular body text, tight spacing

### Component Styling
- Unmatched alert box: Orange background (#ff8c42 or #ff6b35) with 20% opacity, dark text
- Unmatched player cards: Dark gray surface (#1a1a2e), white text, orange accent border
- Player table: Striped rows (alternating opacity), orange hover state
- Buttons: Orange background (#ff8c42), white text, rounded corners
- Modals: Dark background with orange accent header
- Status badges: Green for matched, orange/red for unmatched
- Icons: Material Design icons, orange color for active/interactive

### Layout
- Page header: "Player Management" with breadcrumb navigation
- Main layout: Vertical stacking (unmatched section → table)
- Unmatched section: Grid of cards (responsive: 1-4 per row)
- Player table: Full-width with scroll container
- Sidebar/controls: Filter controls above table (horizontal layout)
- Modal: Centered, max-width 600px, overlay background

### Responsive Breakpoints
- Mobile: < 768px (single column, full-width modals)
- Tablet: 768px - 1024px (2-3 columns, adjusted table)
- Desktop: > 1024px (4+ columns, full table display)

---

## Reusable Components

### Existing Code to Leverage

#### Frontend Components
- **WeekStatusBadge** (`/frontend/src/components/weeks/WeekStatusBadge.tsx`)
  - Reuse badge styling for player match status indicators
  - Adapt glow animation for unmatched player highlight
  - Use icon patterns for status display

- **ImportDataButton** (`/frontend/src/components/import/ImportDataButton.tsx`)
  - Learn modal pattern (WeekMismatchDialog) for mapping modal
  - Reuse success/error notification pattern with Snackbar
  - Follow file upload patterns for data handling

- **MainLayout** (`/frontend/src/components/layout/MainLayout.tsx`)
  - Reuse navigation structure for /players route
  - Follow layout patterns for page container
  - Use existing theme/styling patterns

#### Frontend Hooks & Stores
- **useWeekStore** (`/frontend/src/store/weekStore.ts`)
  - Query current week to fetch week-specific players
  - Get week metadata for context (week number, season, status)
  - Monitor week selection changes to reload player data

- **useDataImport** (`/frontend/src/hooks/useDataImport.ts`)
  - Follow state management pattern for player management
  - Reuse loading/error state handling
  - Use similar async operation patterns

- **Zustand persist middleware**
  - Implement player filter state persistence (position, team, search)
  - Store player table preferences (sort column, column visibility)

#### Backend Patterns
- **unmatched_players_router** (`/backend/routers/unmatched_players_router.py`)
  - REUSE existing `/api/unmatched-players` endpoints
  - GET `/api/unmatched-players?import_id={uuid}` for unmatched list
  - POST `/api/unmatched-players/map` for mapping players
  - POST `/api/unmatched-players/ignore` for ignoring players
  - Endpoints already handle database operations

- **PlayerMatcher** (`/backend/services/player_matcher.py`)
  - REUSE fuzzy matching logic (fuzzy_match method)
  - Already handles normalization and composite key generation
  - Fuzzy matching with 85% threshold
  - Similarity scoring (0-1 scale)

- **Database Schema** (existing tables from migrations)
  - `player_pools`: Player data per week
  - `unmatched_players`: Unmatched players with fuzzy scores
  - `player_aliases`: Global alias mappings
  - `weeks`: Week metadata for context
  - Proper indexes already in place

#### Styling & Theme
- **darkTheme** (`/frontend/src/theme.ts`)
  - Use Material-UI dark theme as base
  - Extend with orange accent color (#ff8c42)
  - Follow existing typography patterns
  - Maintain consistency with current design

- **Typography & Spacing**
  - Use Roboto font stack (existing)
  - Follow Material Design spacing (8px base unit)
  - Use existing button styles as templates
  - Apply consistent border radius (8px on modals, 4px on badges)

### New Components Required

#### Frontend Components
1. **PlayerManagementPage**
   - New component: Main page container for /players route
   - Why: Orchestrates child components, manages page-level state
   - Cannot reuse: Unique to player management workflow

2. **UnmatchedPlayersSection**
   - New component: Alert box with unmatched player cards
   - Why: Specialized layout and styling for alert presentation
   - Cannot reuse: Specific to unmatched players concept

3. **UnmatchedPlayerCard**
   - New component: Individual unmatched player card
   - Why: Specialized card design with "Fix" button
   - Cannot reuse: Specific UI pattern not used elsewhere

4. **PlayerTable**
   - New component: TanStack Table implementation for player list
   - Why: Requires complex sorting, filtering, virtual scrolling
   - Cannot reuse: Specialized data grid not needed in other features

5. **PlayerTableFilters**
   - New component: Filter controls (position, team, unmatched status)
   - Why: Custom filter UI with multi-select dropdowns
   - Cannot reuse: Specific to player management filters

6. **PlayerTableRow**
   - New component: Individual player row with expand toggle
   - Why: Custom row styling, expansion logic, status indicators
   - Cannot reuse: Specific to player table structure

7. **PlayerSearchBox**
   - New component: Search input for player name filtering
   - Why: Real-time search filtering implementation
   - Cannot reuse: Specific input pattern with instant filtering

8. **PlayerMappingModal**
   - New component: Modal for mapping unmatched players
   - Why: Custom modal with fuzzy match suggestions and confirm workflow
   - Cannot reuse: Unique workflow not used elsewhere

9. **FuzzyMatchSuggestions**
   - New component: List of fuzzy-matched player suggestions
   - Why: Displays similarity scores with custom styling
   - Cannot reuse: Specific to mapping workflow

10. **PlayerStatusBadge**
    - New component: Badge for matched/unmatched status
    - Why: Similar to WeekStatusBadge but simplified for player status
    - Could partially reuse: Adapt WeekStatusBadge styling
    - New implementation preferred: Different meaning, cleaner separation

#### Frontend Hooks
1. **usePlayerManagement**
   - New hook: Centralized player data management
   - Manages: Fetching players, handling mapping, state synchronization
   - Why: Complex state logic deserves custom hook

2. **usePlayerFiltering**
   - New hook: Filter state and filtering logic
   - Manages: Position filter, team filter, search, unmatched filter
   - Why: Encapsulates filter logic from component

3. **usePlayerSorting**
   - New hook: Table sort state and sorting logic
   - Manages: Current sort column, sort direction
   - Why: Complex sorting logic with virtual scrolling

4. **usePlayerMapping**
   - New hook: Unmatched player mapping workflow
   - Manages: Modal state, mapping requests, success/error handling
   - Why: Encapsulates modal workflow complexity

#### Backend Endpoints
1. **GET /api/players/by-week/{week_id}**
   - New endpoint: Fetch all players for a specific week
   - Cannot reuse existing: No equivalent endpoint
   - Returns: Player data with match status, sorted/paginated

2. **GET /api/players/unmatched/{week_id}**
   - New endpoint: Fetch only unmatched players for a week
   - Cannot reuse existing: `/api/unmatched-players` requires import_id
   - Returns: Unmatched players with fuzzy suggestions

3. **GET /api/players/search**
   - New endpoint: Search players by name across all weeks
   - Cannot reuse existing: Need full-text search capability
   - Returns: Matching players with context (week, team, position)

4. **GET /api/players/suggestions/{import_id}/{player_id}**
   - New endpoint: Get fuzzy match suggestions for unmatched player
   - Cannot reuse existing: PlayerMatcher.fuzzy_match needs to be exposed via API
   - Returns: List of candidate players with similarity scores

#### Backend Services
1. **PlayerManagementService**
   - New service: Orchestrate player data retrieval and transformation
   - Why: Encapsulates complex query logic and data formatting
   - Responsibilities: Fetch players, apply filters, enrich data

2. **PlayerAliasService**
   - New service: Manage player alias creation and resolution
   - Why: Encapsulates alias business logic
   - Responsibilities: Create aliases, resolve aliases, list aliases

#### Database - No New Tables
- All required tables exist: `player_pools`, `unmatched_players`, `player_aliases`, `weeks`
- May need new indexes for performance optimization
- Player table columns already support all Phase 1 requirements

---

## Technical Approach

### Frontend Architecture

#### State Management
- **Global State (Zustand):** Week selection (reuse existing useWeekStore)
- **Local State (React hooks):** Filter state, sort state, modal visibility
- **Component State (useState):** Search input, row expansion, loading states
- **Server State (React Query):** Player data fetching, caching

#### Data Flow
1. User navigates to `/players` route
2. PlayerManagementPage component mounts
3. usePlayerManagement hook queries players for current week via React Query
4. Player data cached with configurable stale time (5 minutes recommended)
5. UnmatchedPlayersSection displays unmatched subset
6. PlayerTable displays full player list with virtual scrolling
7. User interactions (sort, filter, search) update local state
8. Filter/sort state updates trigger table re-render but not API call
9. User clicks "Fix" on unmatched player → PlayerMappingModal opens
10. Modal calls playerMatch API to get suggestions
11. User selects match and confirms → POST /api/unmatched-players/map
12. Success triggers React Query invalidation
13. Table re-fetches and updates with mapped player in matched section

#### Component Hierarchy
```
PlayerManagementPage
├─ Header (title, breadcrumb)
├─ UnmatchedPlayersSection
│  ├─ AlertBox (count, styling)
│  └─ UnmatchedPlayerCard[] (for each unmatched player)
│     └─ MapButton (opens modal)
├─ PlayerTableControls
│  ├─ PlayerSearchBox
│  └─ PlayerTableFilters
│     ├─ PositionFilter
│     ├─ TeamFilter
│     └─ UnmatchedStatusFilter
├─ PlayerTable (TanStack Table)
│  └─ PlayerTableRow[] (virtual scrolling)
│     ├─ CellRenderer[]
│     └─ ExpandedRow (if expanded)
└─ PlayerMappingModal
   ├─ PlayerInfo (unmatched player)
   ├─ FuzzyMatchSuggestions
   │  └─ SuggestionRow[] (clickable)
   ├─ ManualSearchBox
   └─ ActionButtons (confirm, skip, cancel)
```

#### API Integration
- Use axios with configured base URL from environment
- React Query for server state management
- Cache player data with 5 minute stale time
- Invalidate cache on successful mapping
- Handle loading and error states consistently
- Implement retry logic for failed requests (max 3 retries)

### Backend Architecture

#### Route Organization
- Extend `import_router.py` with new `/api/players/*` routes
- Or create new `players_router.py` for dedicated player endpoints
- Recommended: Separate router for clarity

#### Service Layer
- **PlayerManagementService:** Query player data with filtering
  - `get_players_by_week(week_id)` → All players for week
  - `get_unmatched_players(week_id)` → Unmatched only
  - `search_players(query)` → Name-based search
  - `get_player_with_history(player_key, week_id)` → Enriched data

- **PlayerAliasService:** Alias management
  - `create_alias(alias_name, canonical_player_key)` → Create or update
  - `resolve_alias(name)` → Look up canonical key
  - `get_all_aliases()` → List all aliases

#### Database Queries
- Use SQLAlchemy ORM (if models exist) or raw SQL with proper parameterization
- Leverage existing indexes on player_pools and weeks tables
- Consider adding indexes:
  - `player_pools (week_id, position, team)` for filtering
  - `player_pools (week_id, name)` for search
  - `unmatched_players (import_id, status)` for unmatched retrieval

#### Error Handling
- Validate week_id exists and user has access
- Handle empty player pools gracefully (return empty list, not error)
- Return structured error responses with meaningful messages
- Log all errors with context for debugging

### Mobile Optimization

#### Responsive Breakpoints
- **Mobile (< 768px):** Single column layout, full-width elements
- **Tablet (768px - 1024px):** 2-3 column layouts
- **Desktop (> 1024px):** Full multi-column experience

#### Touch Optimization
- Minimum 44x44px tap targets for buttons and links
- Avoid hover-based interactions (use click/tap instead)
- Full-width modals on mobile (no side padding)
- Horizontal scroll for tables instead of cramped columns
- Large text input fields for easier interaction
- Swipe gestures for table navigation (Phase 2 enhancement)

#### Mobile Table Strategy
- Keep critical columns visible (name, team, position, salary)
- Use horizontal scroll for additional columns
- Collapse optional columns on mobile
- Use card-based view for unmatched players
- Touch-friendly expand buttons (larger hit target)
- Lazy load images/avatars (if added in Phase 2)

### Performance Considerations

#### Frontend Optimization
- Virtual scrolling with TanStack Table (150-200 player threshold)
- Memoize expensive component renders with React.memo
- Debounce search input (300ms recommended)
- Lazy load modal content on open
- Paginate if virtual scrolling insufficient
- Client-side filtering/sorting for already-loaded data
- React Query stale-while-revalidate pattern for fresh data

#### Backend Optimization
- Use database indexes for filtering (position, team, week_id)
- Implement query pagination (limit 200 per request)
- Cache player lists in Redis (optional, Phase 2)
- Batch API requests where possible
- Use database views for complex queries if needed

#### Data Transfer
- Only send necessary columns initially
- Lazy load additional columns on expand
- Compress responses with gzip (default for most servers)
- Implement incremental loading for large datasets

---

## Data Model & Database Changes

### Existing Tables (No Changes Required)

#### player_pools
```
- id (PK)
- week_id (FK to weeks)
- player_key (STRING, composite key)
- name (STRING, player name)
- team (STRING, 2-3 char abbrev)
- position (VARCHAR, QB|RB|WR|TE|DST)
- salary (INTEGER, 3000-10000)
- projection (FLOAT, nullable)
- ownership (FLOAT, nullable, 0-1 range)
- ceiling (FLOAT, nullable)
- floor (FLOAT, nullable)
- notes (TEXT, nullable)
- source (VARCHAR, LineStar|DraftKings)
- uploaded_at (TIMESTAMP)

Indexes:
- idx_player_pools_week_id
- idx_player_pools_player_key
- idx_player_pools_position
- idx_player_pools_team
- idx_player_pools_source
```

#### unmatched_players
```
- id (PK)
- import_id (FK to import_history)
- imported_name (STRING)
- team (STRING)
- position (STRING)
- salary (INTEGER, nullable)
- suggested_player_key (STRING, nullable)
- similarity_score (FLOAT, nullable, 0-1)
- status (VARCHAR, pending|mapped|ignored)

Indexes:
- (implicit) import_id
- (implicit) status
```

#### player_aliases
```
- id (PK)
- alias_name (STRING, unique)
- canonical_player_key (STRING)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

Indexes:
- idx_player_aliases_alias_name (unique)
- idx_player_aliases_canonical_player_key
```

#### weeks
```
- id (PK)
- season (INTEGER)
- week_number (INTEGER, 1-18)
- status (VARCHAR, upcoming|active|completed)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

Constraints:
- unique (season, week_number)
```

### Potential Index Additions (Performance)

```sql
-- For player filtering by team and position
CREATE INDEX idx_player_pools_team_position ON player_pools(team, position);

-- For player search by name
CREATE INDEX idx_player_pools_name_pattern ON player_pools(name);

-- For unmatched player queries
CREATE INDEX idx_unmatched_status_import ON unmatched_players(import_id, status);

-- For alias resolution during imports
CREATE INDEX idx_player_aliases_name ON player_aliases(alias_name);
```

### No Database Migrations Needed for Phase 1
- All required tables exist
- No new columns needed
- No schema changes
- Optional index additions for performance (non-blocking)

---

## Component Architecture

### Frontend Component Specs

#### PlayerManagementPage
- **Location:** `/frontend/src/pages/PlayerManagementPage.tsx`
- **Type:** Page component, main entry point for `/players` route
- **Responsibilities:**
  - Fetch current week from store
  - Fetch player data via usePlayerManagement hook
  - Render child components
  - Handle page-level state (loading, error)
  - Coordinate data refreshes
- **Props:** None (uses store and hooks)
- **State:**
  - isLoading: boolean
  - error: string | null
- **Hooks:** useWeekStore, usePlayerManagement, useEffect for title

#### UnmatchedPlayersSection
- **Location:** `/frontend/src/components/players/UnmatchedPlayersSection.tsx`
- **Type:** Feature component
- **Responsibilities:**
  - Display alert box with unmatched count
  - Render unmatched player cards
  - Handle "Fix" button clicks
- **Props:** `{ unmatchedPlayers: Player[], onFixClick: (id) => void }`
- **State:** None (presentation only)
- **Sub-components:** UnmatchedPlayerCard

#### PlayerTable
- **Location:** `/frontend/src/components/players/PlayerTable.tsx`
- **Type:** Feature component, uses TanStack Table
- **Responsibilities:**
  - Manage table state (sorting, column visibility)
  - Render virtual scrolling table
  - Handle row expansion
  - Display loading states
- **Props:** `{ players: Player[], isLoading: boolean }`
- **State:**
  - columnVisibility: object
  - sorting: SortingState (TanStack)
  - expanded: ExpandedState (TanStack)
- **Hooks:** TanStack Table hooks, TanStack Virtual

#### PlayerMappingModal
- **Location:** `/frontend/src/components/players/PlayerMappingModal.tsx`
- **Type:** Modal component
- **Responsibilities:**
  - Display unmatched player info
  - Fetch and show fuzzy match suggestions
  - Handle user selection
  - Submit mapping request
- **Props:** `{ open: boolean, player: Player, onClose: (), onConfirm: () }`
- **State:**
  - selectedPlayer: Player | null
  - suggestions: Player[]
  - isLoading: boolean
  - searchInput: string
- **Hooks:** usePlayerMapping, useQuery for suggestions

#### PlayerTableFilters
- **Location:** `/frontend/src/components/players/PlayerTableFilters.tsx`
- **Type:** Control component
- **Responsibilities:**
  - Render filter controls
  - Manage filter state
  - Call parent callback on change
- **Props:** `{ onFilterChange: (filters) => void, positions: [], teams: [] }`
- **State:**
  - selectedPositions: string[]
  - selectedTeams: string[]
  - showUnmatchedOnly: boolean
- **Hooks:** None (uses useState)

#### PlayerSearchBox
- **Location:** `/frontend/src/components/players/PlayerSearchBox.tsx`
- **Type:** Control component
- **Responsibilities:**
  - Render search input
  - Debounce search queries
  - Call parent callback on search
- **Props:** `{ onSearch: (query: string) => void, placeholder?: string }`
- **State:**
  - searchInput: string
- **Hooks:** useCallback, useEffect (debounce)

### Backend Endpoint Specs

#### GET /api/players/by-week/{week_id}
- **Purpose:** Fetch all players for a specific week
- **Path params:** `week_id: integer` (FK to weeks.id)
- **Query params:**
  - `position?: string` (filter: QB|RB|WR|TE|DST)
  - `team?: string` (filter: NFL team abbrev)
  - `sort_by?: string` (column name for sorting)
  - `sort_dir?: string` (asc|desc)
  - `limit?: integer` (default: 200, max: 200)
  - `offset?: integer` (default: 0, for pagination)
- **Response (200):**
  ```json
  {
    "success": true,
    "players": [
      {
        "id": 123,
        "player_key": "patrick_mahomes_KC_QB",
        "name": "Patrick Mahomes",
        "team": "KC",
        "position": "QB",
        "salary": 8000,
        "projection": 24.5,
        "ownership": 0.35,
        "ceiling": 45.2,
        "floor": 18.3,
        "notes": "MVP candidate",
        "source": "DraftKings",
        "status": "matched",
        "uploaded_at": "2025-10-29T10:00:00Z"
      }
    ],
    "total": 156,
    "unmatched_count": 3
  }
  ```
- **Response (400):** Invalid week_id or bad parameters
- **Response (404):** Week not found

#### GET /api/players/unmatched/{week_id}
- **Purpose:** Fetch only unmatched players for a week with suggestions
- **Path params:** `week_id: integer`
- **Query params:**
  - `with_suggestions?: boolean` (default: true, include fuzzy suggestions)
  - `limit?: integer` (default: 50)
- **Response (200):**
  ```json
  {
    "success": true,
    "unmatched_players": [
      {
        "id": 456,
        "imported_name": "P. Mahomes",
        "team": "KC",
        "position": "QB",
        "salary": 8000,
        "similarity_score": 0.82,
        "status": "pending",
        "suggestions": [
          {
            "player_key": "patrick_mahomes_KC_QB",
            "name": "Patrick Mahomes",
            "team": "KC",
            "position": "QB",
            "salary": 8000,
            "similarity_score": 0.95
          }
        ]
      }
    ],
    "total_unmatched": 3
  }
  ```

#### GET /api/players/search
- **Purpose:** Search for players by name across weeks
- **Query params:**
  - `q: string` (required, search query)
  - `limit?: integer` (default: 20)
  - `week_id?: integer` (optional filter to specific week)
- **Response (200):**
  ```json
  {
    "success": true,
    "results": [
      {
        "player_key": "patrick_mahomes_KC_QB",
        "name": "Patrick Mahomes",
        "team": "KC",
        "position": "QB",
        "weeks": [1, 2, 3],
        "latest_salary": 8000,
        "latest_projection": 24.5
      }
    ]
  }
  ```

#### GET /api/players/suggestions/{unmatched_player_id}
- **Purpose:** Get fuzzy match suggestions for an unmatched player
- **Path params:** `unmatched_player_id: integer` (FK to unmatched_players.id)
- **Query params:**
  - `limit?: integer` (default: 5)
- **Response (200):**
  ```json
  {
    "success": true,
    "unmatched_player": {
      "id": 456,
      "imported_name": "P. Mahomes",
      "team": "KC",
      "position": "QB"
    },
    "suggestions": [
      {
        "player_key": "patrick_mahomes_KC_QB",
        "name": "Patrick Mahomes",
        "team": "KC",
        "position": "QB",
        "salary": 8000,
        "similarity_score": 0.95
      }
    ]
  }
  ```

#### POST /api/unmatched-players/map (REUSE)
- **Purpose:** Map unmatched player to canonical player (EXISTING)
- **Body:**
  ```json
  {
    "unmatched_player_id": 456,
    "canonical_player_key": "patrick_mahomes_KC_QB"
  }
  ```
- **Response (200):**
  ```json
  {
    "success": true,
    "message": "Alias mapped successfully"
  }
  ```

#### POST /api/unmatched-players/ignore (REUSE)
- **Purpose:** Mark player as ignored (EXISTING)
- **Body:**
  ```json
  {
    "unmatched_player_id": 456
  }
  ```

---

## Design Specifications

### Color Palette

| Element | Color | Hex | Usage |
|---------|-------|-----|-------|
| Background | Black | #0a0a0a | Page background |
| Primary Surface | Dark Gray | #1a1a2e | Cards, panels, table |
| Secondary Surface | Dark Gray | #262641 | Hover states |
| Text Primary | White | #ffffff | Headings, labels |
| Text Secondary | Light Gray | #e5e7eb | Body text, descriptions |
| Text Tertiary | Muted Gray | #9ca3af | Disabled, helper text |
| Accent | Orange | #ff8c42 | Buttons, active states, alerts |
| Accent Dark | Dark Orange | #ff6b35 | Hover states on buttons |
| Alert | Orange Red | #ff5722 | Unmatched alert background |
| Success | Green | #4caf50 | Matched status badge |
| Border | Dark Orange | #ff8c4266 | Accent borders (66 = 40% opacity) |
| Border Default | Gray | rgba(255,255,255,0.1) | Standard borders |

### Typography

| Element | Font | Size | Weight | Line Height | Letter Spacing |
|---------|------|------|--------|------------|-----------------|
| Page Title | Roboto | 32px | Bold (700) | 1.4 | 0 |
| Section Header | Roboto | 20px | Bold (700) | 1.3 | 0 |
| Table Header | Roboto | 14px | Medium (500) | 1.5 | 0.5px |
| Body Text | Roboto | 14px | Regular (400) | 1.5 | 0 |
| Button | Roboto | 14px | Medium (500) | 1.5 | 0.5px |
| Badge | Roboto | 12px | Medium (500) | 1.4 | 0.4px |
| Helper Text | Roboto | 12px | Regular (400) | 1.4 | 0.4px |

### Spacing System (8px base unit)

| Element | Padding/Margin | Sizes |
|---------|---|---|
| Page container | Horizontal: 24px | Vertical: 32px | |
| Section | Padding: 24px | Margin bottom: 32px | |
| Card | Padding: 16px | |
| Button | Padding: 12px 24px | |
| Form input | Padding: 12px 16px | |
| Badge | Padding: 4px 8px | |
| Modal | Padding: 32px | Max-width: 600px | |

### Border Radius
- Buttons: 8px
- Cards/Panels: 8px
- Modal: 12px
- Input fields: 6px
- Badges: 4px
- Chips: 20px (if used)

### Shadows
- Card shadow: `0 2px 8px rgba(0, 0, 0, 0.25)`
- Modal shadow: `0 4px 16px rgba(0, 0, 0, 0.4)`
- Button hover shadow: `0 4px 12px rgba(255, 140, 66, 0.3)`
- Alert shadow: `0 2px 8px rgba(255, 87, 34, 0.2)`

### Component-Specific Styles

#### Unmatched Alert Box
- Background: rgba(255, 87, 34, 0.1) (alert-color with 10% opacity)
- Border: 2px solid #ff5722 (alert-color)
- Border-radius: 8px
- Padding: 20px
- Margin-bottom: 24px
- Display: flex, justify-content: space-between, align-items: center

#### Unmatched Player Card
- Background: #1a1a2e (primary surface)
- Border: 2px solid #ff8c42 (accent, 40% opacity for inactive, 100% for hover)
- Border-radius: 8px
- Padding: 16px
- Display: flex, justify-content: space-between, align-items: center
- Transition: all 0.2s ease-in-out
- Hover: border-color #ff8c42 (100% opacity), background: #262641

#### Player Table Header
- Background: #0a0a0a (background)
- Border-bottom: 1px solid rgba(255,255,255,0.1)
- Padding: 12px 16px
- Font: Bold 14px Roboto
- Text-transform: uppercase
- Letter-spacing: 0.5px
- Sticky: position sticky, top 0, z-index 10

#### Player Table Row (Regular)
- Background: #1a1a2e
- Border-bottom: 1px solid rgba(255,255,255,0.05)
- Padding: 12px 16px
- Transition: all 0.1s ease-in-out

#### Player Table Row (Hover)
- Background: #262641
- Cursor: pointer

#### Player Table Row (Unmatched)
- Background: rgba(255, 87, 34, 0.05) (alert-color with 5% opacity)
- Border-left: 4px solid #ff5722 (alert-color)

#### Player Status Badge
- Matched: Background #4caf50 (success), text white
- Unmatched: Background #ff5722 (alert), text white
- Padding: 4px 8px
- Border-radius: 4px
- Font: Medium 12px Roboto

#### Buttons
- Default: Background #ff8c42, text white, padding 12px 24px
- Hover: Background #ff6b35, shadow 0 4px 12px rgba(255, 140, 66, 0.3)
- Active/Pressed: Background #e85a1a, transform scale(0.98)
- Disabled: Background rgba(255, 140, 66, 0.3), text rgba(255,255,255,0.5)
- Border-radius: 8px
- Font: Medium 14px Roboto
- Transition: all 0.2s ease-in-out
- Text-transform: none
- Letter-spacing: 0.5px

#### Modal Overlay
- Background: rgba(0, 0, 0, 0.7)
- Z-index: 1000

#### Modal Container
- Background: #1a1a2e
- Border-radius: 12px
- Max-width: 600px
- Width: 90% (mobile), 100% (mobile < 400px)
- Padding: 32px
- Box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4)
- Animation: fade-in 0.3s ease-in-out

#### Input Fields
- Background: rgba(255, 255, 255, 0.05)
- Border: 1px solid rgba(255, 255, 255, 0.1)
- Border-radius: 6px
- Padding: 12px 16px
- Color: #ffffff
- Font: Regular 14px Roboto
- Transition: all 0.2s ease-in-out
- Focus: border-color #ff8c42, box-shadow 0 0 8px rgba(255, 140, 66, 0.3)

#### Filter Dropdown
- Background: #1a1a2e
- Border: 1px solid rgba(255, 255, 255, 0.1)
- Border-radius: 6px
- Padding: 12px 16px
- Color: #e5e7eb
- Font: Regular 14px Roboto

#### Loading Spinner
- Color: #ff8c42 (accent)
- Size: 40px (full page), 24px (inline)
- Animation: spin 1s linear infinite

---

## API Specifications

### Authentication & Authorization
- All endpoints authenticated (add Bearer token check if not already implemented)
- No role-based restrictions for Phase 1 (all users can access)
- Future: Add admin restrictions for alias management

### Response Format
All endpoints return JSON with structure:
```json
{
  "success": boolean,
  "data": object | array | null,
  "error": string | null,
  "message": string | null
}
```

### Error Handling
- 400: Invalid input (bad parameters, validation errors)
- 404: Resource not found (week not found, player not found)
- 500: Server error (database connection, processing error)
- Include detailed error message for debugging

### Rate Limiting
- Recommended: 100 requests per minute per IP
- Future: Implement based on server capacity

### CORS
- Allow requests from frontend domain
- Allow credentials if needed
- Allow necessary headers

---

## Performance Considerations

### Frontend Performance

#### Virtual Scrolling
- Implement TanStack Virtual for 150-200+ players
- Render only visible rows (+ overscan buffer)
- Estimated: 15-30 DOM nodes at a time vs. 200+ without virtualization
- Expected performance: 60fps on 2020+ devices

#### Memoization
- Memoize PlayerTable component (expensive render)
- Memoize PlayerTableRow components
- Memoize filter/sort controls
- Use useCallback for event handlers passed as props

#### Code Splitting
- Lazy load PlayerMappingModal component (only needed on demand)
- Lazy load PlayerManagementPage (separate from home/dashboard)
- Expected bundle size reduction: ~15-20KB gzipped

#### Caching
- React Query cache: 5 minute stale time for player data
- Stale-while-revalidate: Show cached data while refreshing in background
- Manual invalidation on successful mapping
- Implement isBackgroundLoading state to show gentle loading indicator

#### Search Debouncing
- 300ms debounce on search input
- Prevents excessive re-renders and API calls
- Reasonable trade-off: slight typing delay not noticeable to users

#### Image Optimization (Phase 2)
- Lazy load player photos/headshots
- WebP format with PNG fallback
- Responsive images (srcset for different device sizes)
- Consider CDN for image caching

### Backend Performance

#### Database Optimization
- Ensure indexes exist:
  - player_pools (week_id, position, team)
  - player_pools (week_id, player_key)
  - unmatched_players (import_id, status)
  - player_aliases (alias_name, canonical_player_key)
- Monitor query performance with EXPLAIN ANALYZE
- Consider connection pooling (PgBouncer)

#### Query Optimization
- Use SELECT specific columns, not SELECT *
- Add LIMIT clause to all queries
- Use OFFSET-based pagination (not ID-based yet)
- Consider materialized views for complex queries (Phase 2)

#### API Response Size
- Limit player list response to 200 players max
- Only include necessary columns initially
- Lazy load ceiling/floor on row expansion
- Compress responses with gzip

#### Caching Strategy
- Cache player aliases in-memory (Redis) - refreshed on update
- Cache player list (if relatively static) - 5 minute TTL
- Cache search results - 10 second TTL
- Cache suggestions - no cache (compute on demand)

#### Load Testing
- Test with 1000+ players to ensure virtual scrolling efficiency
- Load test 100 concurrent users on player list endpoint
- Measure P99 response time: target < 500ms
- Monitor database CPU during peak load

### Metrics to Monitor

#### Frontend Metrics
- Time to Interactive (TTI): < 2s target
- Largest Contentful Paint (LCP): < 2.5s target
- Cumulative Layout Shift (CLS): < 0.1 target
- First Input Delay (FID): < 100ms target
- JavaScript bundle size: < 100KB (gzipped) target
- Virtual scroll render performance: 60fps target

#### Backend Metrics
- API response time (p50): < 200ms
- API response time (p99): < 500ms
- Database query time (p99): < 300ms
- Error rate: < 0.1%
- Cache hit rate: > 80%

#### User Metrics
- Page load time: < 3s
- Time to first interactivity: < 2s
- Time to map player: < 10s (from click to confirm)
- Error recovery time: < 2s (with clear messaging)

---

## Mobile & Responsive Design

### Responsive Breakpoints

#### Mobile (< 768px)
- **Layout:** Single column, full-width elements
- **Player Table:**
  - Show critical columns: Name, Team, Position, Salary
  - Hide optional columns by default
  - Use horizontal scroll for additional columns
  - Add column toggle UI to show/hide optional columns
- **Unmatched Section:**
  - Display as cards instead of compact list
  - Stack cards vertically
  - Full-width "Fix" buttons
- **Filters:**
  - Use dropdown/modal for filter selection instead of inline
  - Stack filter controls vertically
  - Full-width inputs
- **Modal:**
  - Full-width with 16px side margin
  - No max-width constraint
  - Top position with scroll container
  - Full-height if needed
- **Typography:**
  - Page title: 24px
  - Section header: 18px
  - Body: 14px (keep readable)
  - Avoid text smaller than 12px

#### Tablet (768px - 1024px)
- **Layout:** 2-column or sidebar layout possible
- **Player Table:**
  - Show primary columns: Name, Team, Position, Salary, Projection, Ownership
  - Show secondary columns with scroll: Notes, Source, Status
  - Column headers might wrap slightly
- **Filters:**
  - Mix of inline and dropdown filters
  - Can use horizontal arrangement if space permits
- **Modal:**
  - Max-width 500px, centered
  - Side padding 20px

#### Desktop (> 1024px)
- **Layout:** Full multi-column experience
- **Player Table:**
  - Show all columns up to 80vw width
  - Horizontal scroll for any overflow
  - Full feature set (expand rows, sorting, filtering)
- **Filters:**
  - Horizontal arrangement of all filters
  - Inline search box
  - Filter dropdown on the side

### Touch Optimization

#### Tap Targets
- Minimum 44x44px for all interactive elements
- Button text should not require precision tap
- Space between tap targets: at least 8px
- Add padding to increase tap target size if needed

#### Touch Gestures
- Tap/Click: Standard interaction (no hover-only interfaces)
- Long press: Not required for Phase 1
- Swipe: Optional future enhancement for table navigation
- Pinch-zoom: Allow native pinch-zoom, don't disable

#### Avoid
- Hover-only interactions (use click/tap alternative)
- Double-tap to select (can confuse zoom gestures)
- Hover tooltips (use touch-triggered tooltips or remove)
- Drag-and-drop if not essential (harder on mobile)

#### Inputs
- Large text input fields: min 44px height
- Dropdown toggles: min 44x44px
- Checkboxes/radio buttons: min 44x44px touch area
- Default to native inputs where possible (easier for mobile)
- Avoid custom inputs that conflict with mobile conventions

### Mobile Navigation

#### Header
- Keep header sticky for easy navigation
- Show week selector in header (not sidebar)
- Mobile menu button if additional navigation needed

#### Breadcrumb
- Show: Home > Player Management
- Or: Show only current page title, remove breadcrumb

#### Back Button
- Include back button on Player Management page
- Option to go back to Dashboard or Home

### Image & Media Handling (Phase 2)

#### Player Photos
- Responsive images with srcset
- Lazy load with intersection observer
- Placeholder color while loading
- Fallback to generic player icon

#### Icons
- Ensure icons are at least 24x24px
- Use filled icons on mobile (better visibility)
- Outline icons on desktop (cleaner)

### Performance on Mobile

#### Network Optimization
- Reduce image sizes for mobile networks
- Implement service worker for offline support (Phase 2)
- Cache critical assets
- Lazy load non-critical data

#### Device Constraints
- Test on low-end devices (iPhone SE, Pixel 3a equivalent)
- Optimize for slower CPUs
- Minimize animations on low-end devices
- Use efficient CSS instead of JS animations

#### Testing Strategy
- Test on real devices (not just browser emulation)
- Use Chrome DevTools device emulation as baseline
- Test on iOS and Android
- Test with network throttling (3G, 4G)
- Test with CPU throttling (4x slowdown)

---

## Testing Strategy

### Unit Tests

#### Frontend Components
- **PlayerTable:** Test sorting, filtering, virtual scroll rendering
- **UnmatchedPlayersSection:** Test card rendering, count display, button callbacks
- **PlayerMappingModal:** Test suggestion display, selection, form submission
- **PlayerTableFilters:** Test filter state management and callbacks
- **PlayerSearchBox:** Test debounce, input handling, clear button

#### Frontend Hooks
- **usePlayerManagement:** Test data fetching, state updates, error handling
- **usePlayerFiltering:** Test filter logic, chaining, state persistence
- **usePlayerMapping:** Test modal workflow, API calls

#### Backend Services
- **PlayerManagementService:** Test queries with various filters, pagination
- **PlayerAliasService:** Test alias creation, resolution, conflicts
- **PlayerMatcher.fuzzy_match:** Test matching algorithm (already tested, verify reuse)

#### Backend Endpoints
- **GET /api/players/by-week:** Test with filters, sorting, pagination
- **GET /api/players/unmatched:** Test with suggestions, limit
- **POST /api/unmatched-players/map:** Test validation, alias creation

### Integration Tests

#### Frontend Integration
- Test data flow from store → component → API → update
- Test filter + sort + search working together
- Test modal workflow: open → select → close
- Test unmatched player card → modal → confirmation → table update

#### Backend Integration
- Test import workflow → unmatched detection → mapping
- Test alias creation during mapping → apply to future imports
- Test full player management workflow with real database

#### API Integration
- Test API authentication
- Test error responses
- Test data consistency between endpoints

### E2E Tests

#### Happy Path Scenarios
1. **View Players Page:** Navigate to players, see data, verify column headers
2. **View Unmatched Players:** Verify alert displays, count shows correctly
3. **Map a Player:** Click Fix → modal opens → select suggestion → confirm → updates
4. **Filter Players:** Select position filter → table updates, count changes
5. **Search Players:** Type name → results filter, clear search → all back

#### Edge Cases
1. **No Unmatched Players:** Alert shows "No unmatched players" or disappears
2. **Empty Player Pool:** Table shows empty state
3. **Network Error:** Show error message, retry button
4. **Slow Network:** Show loading state, don't timeout
5. **Mobile View:** All interactions work on mobile screen size

#### Error Scenarios
1. **Invalid Week ID:** Show error, redirect home
2. **Alias Creation Fails:** Show error message, allow retry
3. **API Timeout:** Retry request, show timeout error after 3 attempts
4. **Database Connection Error:** Show maintenance message

### Performance Tests

#### Frontend Performance
- Page load time < 3s (with network throttling)
- Filter/sort action completes within 100ms
- Table scroll (with 200 players) maintains 60fps
- Modal open/close animations smooth (60fps)
- Search debounce prevents excessive re-renders

#### Backend Performance
- GET /api/players/by-week returns < 500ms with 200 players
- GET /api/players/unmatched returns < 300ms with suggestions
- POST /api/unmatched-players/map completes < 200ms
- Database queries use indexes (verify with EXPLAIN)

### Mobile Testing

#### Responsive Design
- Page is usable on 320px width (iPhone SE)
- Page is usable on 600px width (tablet in portrait)
- Page is usable on 1024px width (desktop)
- Text is readable without zoom

#### Touch Interaction
- All buttons are >= 44x44px
- Modals are full-width on mobile
- Table is scrollable horizontally
- No interactions require hover

#### Performance
- Page loads on 3G connection < 5s
- Interactions responsive on low-end device
- No console errors on iOS Safari

### Accessibility Testing

#### WCAG 2.1 Level AA
- Color contrast ratio >= 4.5:1 for text
- Interactive elements have accessible labels
- Focus order is logical
- Keyboard navigation works (Tab, Enter, Escape)
- Screen reader announces page title, sections, interactive elements

#### Keyboard Navigation
- Tab navigates through all interactive elements
- Shift+Tab navigates backwards
- Enter/Space activate buttons
- Escape closes modals
- Arrow keys work in dropdowns/lists

#### Screen Reader
- Table headers announced correctly
- Button purposes are clear
- Form labels associated with inputs
- Status changes announced (e.g., "Player mapped")

### Test Coverage Targets
- Unit tests: > 80% code coverage
- Integration tests: All critical paths covered
- E2E tests: All user stories verified
- Performance tests: All targets met on CI/CD

### Testing Tools
- **Frontend:** Vitest or Jest, React Testing Library, Playwright for E2E
- **Backend:** pytest with fixtures, mock database
- **Performance:** Lighthouse, Web Vitals, Artillery for load testing
- **Accessibility:** axe DevTools, WAVE, screen reader testing

---

## Dependencies & Phase Alignment

### Phase Alignment

#### Phase 0 Completed (Foundations)
- Data Import System: Imports players, detects unmatched, stores in database
- Week Management: Manages week selection, locks weeks after import
- Database: All tables created (player_pools, unmatched_players, player_aliases, weeks)

#### Phase 1 (Current)
- Player Management: UI for player review, unmatched resolution, alias creation
- Fuzzy Matching: Used during import (already implemented)
- Manual Mapping: New feature to resolve unmatched players

#### Phase 2 (Future)
- Smart Score Engine: Calculate player value scores
- Vegas Lines API: Import odds and lines
- Historical Stats API: Pull player historical performance
- Advanced Analytics: 80-20 rule, week-over-week comparison
- Alias Management UI: View, edit, delete aliases
- Player Photos: Display player headshots
- Mobile Enhancements: Swipe gestures, offline support

### External Dependencies

#### Frontend Libraries
- **React 18+:** Core framework (existing)
- **React Router 6+:** Page routing (existing, extend with /players route)
- **Zustand 4+:** Global state (existing, reuse week store)
- **TanStack React Query 5+:** Server state management (existing)
- **TanStack Table (React Table) 8+:** NEW - Data table with sorting/filtering
- **TanStack Virtual:** NEW - Virtual scrolling for large tables
- **Material-UI 5+:** Component library (existing, extend with Player components)
- **Axios 1+:** HTTP client (existing)

#### Backend Dependencies
- **FastAPI 0.100+:** Web framework (existing)
- **SQLAlchemy 2+:** ORM (existing, optional for models)
- **Alembic:** Database migrations (existing)
- **RapidFuzz 2+:** Fuzzy matching (existing, reuse)
- **Python 3.9+:** Runtime (existing)
- **PostgreSQL 12+:** Database (existing)

#### DevDependencies
- **TypeScript 5+:** Type checking (existing)
- **Vite 5+:** Build tool (existing)
- **Playwright 1.56+:** E2E testing (existing)
- **Vitest:** Unit testing (add if not present)
- **React Testing Library:** Component testing (add if not present)
- **pytest:** Python testing (existing)

### Installation Commands

```bash
# Frontend dependencies (add to package.json)
npm install @tanstack/react-table@latest @tanstack/react-virtual@latest

# Or with specific versions
npm install @tanstack/react-table@8.11.0 @tanstack/react-virtual@3.0.0

# Backend dependencies (add to requirements.txt)
# Already installed: fastapi, sqlalchemy, alembic, rapidfuzz
# No new backend dependencies needed for Phase 1
```

### Version Compatibility

| Package | Version | Phase |
|---------|---------|-------|
| React | 18.2+ | Phase 0+ |
| React Router | 6.20+ | Phase 0+ |
| Zustand | 4.4+ | Phase 0+ |
| TanStack Query | 5.12+ | Phase 0+ |
| TanStack Table | 8.11+ | Phase 1 (new) |
| TanStack Virtual | 3.0+ | Phase 1 (new) |
| Material-UI | 5.14+ | Phase 0+ |
| Axios | 1.6+ | Phase 0+ |
| FastAPI | 0.100+ | Phase 0+ |
| SQLAlchemy | 2.0+ | Phase 0+ |
| RapidFuzz | 2.0+ | Phase 0+ |
| Python | 3.9+ | Phase 0+ |
| PostgreSQL | 12+ | Phase 0+ |

### Feature Flag Considerations

For Phase 2 features not in scope for Phase 1:
- Smart Score: Can add column conditionally if data available
- Implied Team Total: Can add column conditionally with placeholder
- 80-20 Rule: Can add badge conditionally for pass catchers
- Historical Comparison: Can add expandable row conditionally
- Vegas Lines: Can add as separate modal/sheet in Phase 2

Implementation: Use feature flags or data availability checks to gracefully degrade.

---

## Known Constraints & Limitations

### Phase 1 Scope

#### Out of Scope Features
- **Smart Score:** Requires machine learning model (Phase 2)
- **Vegas Lines API:** Requires external API integration (Phase 2)
- **Historical Stats API:** Requires historical data aggregation (Phase 2)
- **Last Week Comparison:** Requires week-over-week data (Phase 2)
- **80-20 Rule Indicator:** Requires advanced analytics (Phase 2)
- **Implied Team Total (ITT):** Requires Vegas API (Phase 2)
- **Alias Management UI:** View/edit/delete aliases (Phase 2)
- **Player Photos:** Requires image hosting/CDN (Phase 2)
- **Advanced Search:** Full-text search with operators (Phase 2)
- **Offline Mode:** Service worker caching (Phase 2)

#### Partially Implemented Features
- **Table Columns:** Columns 1-7 implemented, columns 8-11 placeholders only
- **Expandable Rows:** Shows ceiling, floor, notes; Phase 2 adds historical data
- **Filters:** Position, team, unmatched; Phase 2 adds more dimensions

### Technical Constraints

#### Database Constraints
- Cannot modify existing table schema (backward compatibility)
- Must work with existing indexes
- No new tables needed for Phase 1
- Limited to PostgreSQL features available in version 12+

#### Frontend Constraints
- Must use existing Material-UI theme (with orange accent)
- Must support React 18+ features
- Must not break existing components or routes
- Must maintain TypeScript strict mode

#### Performance Constraints
- Page must load in < 3 seconds (all networks)
- Table must support up to 200 players
- Virtual scrolling required for > 50 players
- No database queries should take > 500ms

#### Browser Support
- Modern browsers only (Chrome, Firefox, Safari, Edge recent versions)
- No IE11 support (dropped by Material-UI 5+)
- Mobile: iOS 12+, Android 5+

### Known Issues & Workarounds

#### Issue 1: Player Name Normalization
- **Problem:** Different import sources format names differently ("P. Mahomes" vs "Patrick Mahomes")
- **Solution:** Use fuzzy matching with 85% threshold + manual mapping for edge cases
- **Workaround:** Create aliases for common variations after first occurrence

#### Issue 2: Team Abbreviation Variations
- **Problem:** Some sources use different team abbreviations ("LAR" vs "LA")
- **Solution:** Normalize team abbreviations during import
- **Workaround:** Manual mapping for unmatched players

#### Issue 3: Position Variations
- **Problem:** Some sources use different position names ("OP" vs "DST")
- **Solution:** Validate positions during import, reject invalid positions
- **Workaround:** Manual assignment during mapping

#### Issue 4: Duplicate Players
- **Problem:** Same player appears twice with slightly different info (salary varies week to week)
- **Solution:** Use player_key (name_team_position) to identify unique players per week
- **Workaround:** Implement duplicate detection in import process (Phase 2)

#### Issue 5: Virtual Scrolling with Filtering
- **Problem:** Dynamic row heights can cause scroll position issues with virtual scrolling
- **Solution:** Use fixed row heights for virtual scrolling implementation
- **Workaround:** Implement expandable rows at fixed height, expand into overlay

#### Issue 6: Mobile Modal Scroll
- **Problem:** Modal content might exceed viewport on small screens
- **Solution:** Implement scrollable modal content with fixed header/footer
- **Workaround:** Reduce modal content or implement tabs (Phase 2)

### Future Considerations

#### Performance Optimization (Phase 2+)
- Consider Redis caching for player lists and aliases
- Implement database query result caching
- Add pagination beyond 200 players
- Implement incremental data loading

#### Feature Expansion (Phase 2+)
- Add player comparison view (side-by-side)
- Add player history timeline
- Add bulk operations (import, update, delete)
- Add export functionality (CSV, Excel)

#### Analytics & Monitoring (Phase 2+)
- Add analytics for unmatched player patterns
- Monitor alias creation patterns
- Track user interaction metrics
- Dashboard for import health

#### Admin Features (Phase 2+)
- Audit trail for all alias creations
- Bulk alias import/export
- Merge duplicate players
- Manual player override interface

---

## Success Criteria

### User Experience Goals
- Users can access player management page within 1 click from navigation
- Unmatched players are visible immediately on page load
- Mapping an unmatched player takes < 2 minutes (include modal interaction)
- Player data is accurate after mapping (no sync issues)
- Mobile users can perform all tasks (filtering, mapping, search)

### Functional Goals
- 100% of unmatched players can be mapped or marked as ignored
- No data loss during mapping (audit trail exists)
- All global aliases persist across weeks/imports
- Table displays all necessary columns without horizontal scroll on desktop
- Search returns results within 500ms

### Performance Goals
- Page loads in < 3 seconds (3G network, measured on Lighthouse)
- Table renders with 200 players at 60fps
- Sorting any column completes within 100ms
- Filtering updates display within 50ms
- Mapping player completes within 1 second

### Quality Goals
- Zero console errors on page load
- No TypeScript type errors (strict mode)
- No accessibility violations (WCAG 2.1 Level AA)
- All user stories have passing tests
- Mobile version has >= 90 Lighthouse score

### Adoption Goals
- Used for managing players in at least 1 production week
- Positive feedback from at least 3 test users
- No critical bugs reported after 1 week of use
- Unmatched player resolution workflow adopted (not bypassed)

---

## File Structure Overview

```
frontend/
├─ src/
│  ├─ pages/
│  │  └─ PlayerManagementPage.tsx          (NEW)
│  ├─ components/
│  │  ├─ players/                          (NEW directory)
│  │  │  ├─ PlayerManagementPage.tsx       (moved to pages/)
│  │  │  ├─ UnmatchedPlayersSection.tsx    (NEW)
│  │  │  ├─ UnmatchedPlayerCard.tsx        (NEW)
│  │  │  ├─ PlayerTable.tsx                (NEW)
│  │  │  ├─ PlayerTableFilters.tsx         (NEW)
│  │  │  ├─ PlayerTableRow.tsx             (NEW)
│  │  │  ├─ PlayerSearchBox.tsx            (NEW)
│  │  │  ├─ PlayerMappingModal.tsx         (NEW)
│  │  │  ├─ FuzzyMatchSuggestions.tsx      (NEW)
│  │  │  ├─ PlayerStatusBadge.tsx          (NEW)
│  │  │  └─ index.ts                       (NEW)
│  │  ├─ layout/
│  │  │  └─ MainLayout.tsx                 (MODIFY - add /players route)
│  │  └─ import/
│  │     └─ ImportDataButton.tsx           (existing)
│  ├─ hooks/
│  │  ├─ usePlayerManagement.ts            (NEW)
│  │  ├─ usePlayerFiltering.ts             (NEW)
│  │  ├─ usePlayerSorting.ts               (NEW)
│  │  ├─ usePlayerMapping.ts               (NEW)
│  │  └─ index.ts                          (MODIFY - export new hooks)
│  ├─ store/
│  │  ├─ weekStore.ts                      (existing)
│  │  ├─ playerStore.ts                    (NEW - optional, for filter persistence)
│  │  └─ index.ts                          (MODIFY if playerStore added)
│  └─ main.tsx                             (MODIFY - add /players route)

backend/
├─ routers/
│  ├─ unmatched_players_router.py          (existing, REUSE)
│  └─ players_router.py                    (NEW - add GET endpoints)
├─ services/
│  ├─ player_matcher.py                    (existing, REUSE fuzzy_match)
│  ├─ player_management_service.py         (NEW)
│  └─ player_alias_service.py              (NEW)
├─ schemas/
│  └─ player_schemas.py                    (NEW - Pydantic models)
└─ main.py                                 (MODIFY - register new router)

tests/
├─ components/                             (NEW directory)
│  ├─ PlayerTable.test.tsx                 (NEW)
│  ├─ PlayerMappingModal.test.tsx          (NEW)
│  └─ PlayerTableFilters.test.tsx          (NEW)
├─ hooks/                                  (NEW directory)
│  ├─ usePlayerManagement.test.ts          (NEW)
│  └─ usePlayerMapping.test.ts             (NEW)
├─ integration/                            (existing)
│  └─ player_management.test.py            (NEW)
├─ e2e/                                    (existing)
│  └─ player_management.spec.ts            (NEW)
└─ features/                               (existing)
   └─ players.feature                      (NEW - BDD scenarios)
```

---

## Implementation Timeline

### Week 1 (Oct 29 - Nov 4)
- Set up component structure and routing
- Implement backend GET endpoints
- Build PlayerTable component with TanStack Table
- Build UnmatchedPlayersSection component
- Build PlayerTableFilters component
- Total estimated effort: 40 hours

### Week 2 (Nov 5 - Nov 11)
- Build PlayerMappingModal component
- Build FuzzyMatchSuggestions component
- Implement usePlayerManagement hook
- Integrate with existing APIs
- Build unit tests for components
- Total estimated effort: 40 hours

### Week 3 (Nov 12 - Nov 18)
- Mobile responsive optimization
- Accessibility fixes and WCAG compliance
- Performance optimization (virtual scrolling tuning)
- Integration testing
- E2E test scenarios
- Total estimated effort: 35 hours

### Week 4 (Nov 19 - Nov 25)
- Bug fixes from testing
- Performance fine-tuning
- Documentation
- UAT and user testing
- Final deployment
- Total estimated effort: 30 hours

**Total Estimated Effort:** 145 hours (3.6 weeks for 1 developer)

---

## Rollout Strategy

### Internal Testing (Week 4, Nov 19-25)
- Test with development data
- Verify all workflows work correctly
- Performance testing on staging
- Accessibility compliance check

### Limited Beta (Week 5, Nov 26 - Dec 2)
- Roll out to 3-5 power users
- Gather feedback
- Monitor error rates
- Performance metrics

### Full Release (Week 6, Dec 3+)
- Release to all users
- Monitor adoption and usage
- Provide documentation
- Gather analytics

### Rollback Plan
- Keep previous version running on separate URL
- Monitor error rate for 24 hours
- If error rate > 0.1%, roll back
- Document issues and fix before next release

---

## Documentation Requirements

### User Documentation
- Player Management feature overview
- How to map unmatched players
- How to search and filter
- Mobile usage guide
- Troubleshooting guide

### Developer Documentation
- Component API documentation
- Hook usage examples
- Backend API documentation
- Database schema documentation
- Setup and development guide

### API Documentation
- OpenAPI/Swagger specification for new endpoints
- Request/response examples
- Error codes and meanings
- Rate limiting information

---

## Sign-Off & Approval

**Prepared by:** AI Assistant (Claude Code)
**Date:** 2025-10-29
**Version:** 1.0 - Initial Specification
**Status:** Ready for Development

**Key Stakeholders:**
- Product Manager: Approval needed
- Tech Lead: Review for technical feasibility
- Design Lead: Review for design consistency
- QA Lead: Review for testability

---

## Appendices

### A. Data Model Diagrams

#### Entity Relationships
```
weeks (1) ──── (many) player_pools
 │
 └─── (implicit) ├──── (many) unmatched_players
                 └──── player_aliases

player_pools: {id, week_id, player_key, name, team, position, salary, ...}
unmatched_players: {id, import_id, imported_name, team, position, ...}
player_aliases: {id, alias_name, canonical_player_key, created_at, ...}
weeks: {id, season, week_number, status, ...}
```

### B. API Request/Response Examples

#### Get Players by Week
```bash
GET /api/players/by-week/42?position=QB&sort_by=salary&sort_dir=desc

Response:
{
  "success": true,
  "players": [
    {
      "id": 100,
      "player_key": "patrick_mahomes_KC_QB",
      "name": "Patrick Mahomes",
      "team": "KC",
      "position": "QB",
      "salary": 8000,
      "projection": 24.5,
      "ownership": 0.35,
      "status": "matched"
    }
  ],
  "total": 5,
  "unmatched_count": 0
}
```

#### Map Unmatched Player
```bash
POST /api/unmatched-players/map

Body:
{
  "unmatched_player_id": 456,
  "canonical_player_key": "patrick_mahomes_KC_QB"
}

Response:
{
  "success": true,
  "message": "Alias mapped successfully"
}
```

### C. Component Prop Interfaces (TypeScript)

```typescript
// UnmatchedPlayersSection
interface UnmatchedPlayersSectionProps {
  players: UnmatchedPlayer[];
  count: number;
  onFixClick: (playerId: number) => void;
  isLoading?: boolean;
}

// PlayerTable
interface PlayerTableProps {
  players: Player[];
  isLoading: boolean;
  onRowClick?: (player: Player) => void;
  onExpandChange?: (playerId: number, expanded: boolean) => void;
}

// PlayerMappingModal
interface PlayerMappingModalProps {
  open: boolean;
  unmatchedPlayer: UnmatchedPlayer;
  suggestions: Player[];
  onClose: () => void;
  onConfirm: (selectedPlayer: Player) => void;
  isLoading?: boolean;
}

// PlayerTableFilters
interface PlayerTableFiltersProps {
  onFilterChange: (filters: PlayerFilters) => void;
  positions: string[];
  teams: string[];
}

// Filter State
interface PlayerFilters {
  positions: string[];
  teams: string[];
  unmatchedOnly: boolean;
  searchQuery: string;
}
```

### D. Glossary

- **Player Key:** Composite unique identifier (name_team_position)
- **Unmatched Player:** Imported player that failed fuzzy matching
- **Canonical Player:** The official/standard player record in player_pools
- **Alias:** Mapping from imported name to canonical player key
- **Fuzzy Matching:** Algorithm to find similar names despite variations
- **Similarity Score:** Confidence rating (0-1) for fuzzy match
- **Virtual Scrolling:** Rendering only visible rows in large lists
- **Stale-While-Revalidate:** Serving cached data while refreshing in background

