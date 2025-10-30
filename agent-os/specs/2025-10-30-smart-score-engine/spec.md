# Specification: Smart Score Engine

## Executive Summary

The Smart Score Engine calculates a comprehensive player value score using an 8-factor additive formula. This score combines projections, ceiling/floor ranges, ownership patterns, value metrics, trend analysis, regression risks, Vegas context, and matchup quality to provide a single actionable metric for lineup optimization. The system supports customizable weight profiles, real-time recalculation with snapshot comparisons, and intelligent handling of missing data to ensure reliable scoring across all player types and situations.

**Current Phase:** Phase 1 - MVP  
**Target Release:** Week of October 30, 2025  
**Alignment:** Follows Player Management (Phase 1), requires Data Import System (Phase 0) and Week Management (Phase 0)

---

## Goal

Enable users to evaluate player value holistically through a single Smart Score metric that synthesizes multiple data sources and analytical factors. The system provides flexible weight adjustment, projection source selection, and transparent score calculation to support informed lineup decisions.

---

## User Stories

### 1. View Smart Score Page
**As a** DFS manager,
**I want to** access a dedicated `/smart-score` page from the main navigation,
**So that** I can view and manage Smart Scores for all players.

**Acceptance Criteria:**
- A "Smart Score" link appears in the main navigation
- Clicking the link navigates to `/smart-score` page
- Page loads with Smart Scores for all players in the current selected week
- Page title displays "Smart Score Engine" or similar
- Navigation indicates current page is active
- Page is accessible from any location in the app

### 2. View Smart Score Table
**As a** DFS manager,
**I want to** see all players with their Smart Scores in a comprehensive table,
**So that** I can quickly identify the highest-value players for my lineup.

**Acceptance Criteria:**
- Table displays minimum columns:
  - Player Name (sortable, filterable)
  - Team (sortable, filterable)
  - Position (sortable, filterable)
  - Salary (sortable)
  - Projection (sortable)
  - Ownership % (sortable)
  - Smart Score (sortable, prominently displayed)
  - Projection Source (ETR/LineStar)
  - 20+ Snap Games count
  - Regression Risk indicator (WR only)
- Supports 150-200 players with virtual scrolling
- Column sorting works for all sortable columns (ascending/descending)
- Table handles empty states gracefully
- Smart Score column is highlighted visually

### 3. Adjust Weight Profile
**As a** DFS manager,
**I want to** adjust the weights (W1-W8) for each factor using sliders,
**So that** I can customize how Smart Score is calculated based on my strategy.

**Acceptance Criteria:**
- Weight adjustment panel displays 8 sliders (W1-W8)
- Each slider labeled with factor name:
  - W1: Projection
  - W2: Ceiling Factor
  - W3: Ownership Penalty
  - W4: Value Score
  - W5: Trend Adjustment
  - W6: Regression Penalty
  - W7: Vegas Context
  - W8: Matchup Adjustment
- Sliders have min/max bounds (0.0 to 1.0 recommended)
- Current weight values display next to each slider
- Weight values can be adjusted independently
- Changes are not applied until "Apply" button is clicked
- User can reset to default "Base" profile

### 4. Select Projection Source
**As a** DFS manager,
**I want to** choose between ETR and LineStar projections,
**So that** I can use my preferred projection source for Smart Score calculation.

**Acceptance Criteria:**
- Projection source dropdown appears in weight adjustment panel
- Options: "Establish The Run (ETR)" and "LineStar"
- Default: ETR if available, else LineStar
- Selection persists for the week
- Changing source triggers recalculation prompt
- UI indicates which source is currently active

### 5. Recalculate Smart Scores
**As a** DFS manager,
**I want to** click "Apply" to recalculate Smart Scores with new weights,
**So that** I can see the impact of my weight adjustments.

**Acceptance Criteria:**
- "Apply" button appears in weight adjustment panel
- Clicking "Apply" triggers recalculation for all players
- Loading indicator shows during calculation
- Recalculation completes within 500ms target
- Previous scores are stored before recalculation
- Snapshot modal appears after recalculation

### 6. View Score Changes Snapshot
**As a** DFS manager,
**I want to** see a modal showing before/after scores after recalculation,
**So that** I can review the impact of my weight changes before committing.

**Acceptance Criteria:**
- Modal appears automatically after clicking "Apply"
- Modal displays:
  - Player name
  - Previous Smart Score
  - New Smart Score
  - Delta (change amount: +X.X or -X.X)
- Top 10 biggest changes highlighted (orange border or background)
- Modal shows all players whose score changed
- Modal has "Keep Changes" and "Revert" buttons
- Clicking "Keep Changes" applies changes and closes modal
- Clicking "Revert" restores previous scores and closes modal
- Baseline does NOT persist after "Keep Changes"

### 7. View Delta Indicators
**As a** DFS manager,
**I want to** see delta indicators (+2.5, -1.3) next to Smart Scores,
**So that** I can quickly identify which players saw the biggest changes.

**Acceptance Criteria:**
- Delta indicators appear next to Smart Score after recalculation
- Format: `45.2 (+2.5)` or `38.7 (-1.3)`
- Positive deltas colored green (subtle)
- Negative deltas colored red (subtle)
- Indicators persist until next recalculation or revert
- Sort option available: "Sort by Score Change"
- Biggest changes highlighted in snapshot modal

### 8. Save Weight Profile
**As a** DFS manager,
**I want to** save my custom weight profile with a name,
**So that** I can reuse it in future weeks or share with others.

**Acceptance Criteria:**
- "Save Profile" button appears in weight adjustment panel
- Clicking opens dialog to enter profile name
- Profile name must be unique
- Saved profile includes all 8 weights and projection source selection
- Profile is stored in database
- User can select saved profile from dropdown
- "Base" profile is default and cannot be deleted

### 9. View Regression Risk Indicator
**As a** DFS manager,
**I want to** see a visual flag for WRs who scored 20+ points last week,
**So that** I can identify players at risk of regression (80-20 rule).

**Acceptance Criteria:**
- Badge/icon appears next to WR players who scored >= 20 points last week
- Indicator only shows for WR position (not TE, RB, QB, DST)
- Visual indicator is orange/red colored
- Badge tooltip explains "Regression Risk: Scored 20+ points last week"
- If no historical data: Shows message "Historical data unavailable"
- Threshold is configurable (default: 20 DK points)

### 10. View 20+ Snap Games Count
**As a** DFS manager,
**I want to** see how many games a player had with 20+ snaps,
**So that** I can assess the reliability of trend calculations.

**Acceptance Criteria:**
- Column displays "20+ Snap Games" count
- Count shows number of games with >= 20 snaps from historical_stats
- Players with < 4 games highlighted (insufficient data warning)
- Tooltip explains: "Games with 20+ snaps used for trend calculation"
- Count updates based on historical data availability

### 11. Handle Missing Data
**As a** DFS manager,
**I want to** see Smart Scores calculated even when some data is missing,
**So that** I can evaluate players without complete information.

**Acceptance Criteria:**
- Missing projection: Uses 0 or excludes from calculation (with indicator)
- Missing ceiling/floor: Estimates based on projection volatility or position defaults
- Missing ownership: Uses league average ownership (calculated dynamically)
- Missing historical stats: Uses neutral trend (0 change)
- Missing ITT: Uses league average ITT (22.5 default)
- Missing opponent rank: Uses "middle" category
- Visual indicators show when defaults are used (tooltip or badge)

### 12. Filter by Smart Score Threshold
**As a** DFS manager,
**I want to** filter out players below a Smart Score threshold,
**So that** I can focus on high-value players for lineup optimization.

**Acceptance Criteria:**
- Threshold input field appears in filter panel
- Default value: 0 (no filter)
- Players below threshold are excluded from lineup optimizer input
- Players below threshold still visible in table (grayed out or flagged)
- Threshold applies to optimizer, not display filter

---

## Core Requirements

### Formula Structure
- **8-Factor Additive Formula:**
  1. Projection × W1
  2. + (Ceiling Factor × W2) [Ceiling - Floor, or volatility estimate]
  3. - (Ownership × W3) [Penalty]
  4. + (Value Score × W4) [(Projection / (Salary/100)) × 1000]
  5. + (Trend Adjustment × W5) [Position-specific: target_share/snap_pct/pass_attempts]
  6. - (Regression Penalty × W6) [WR only, visual flag in MVP]
  7. + (Vegas Context × W7) [(Team ITT / League Avg ITT) × W7]
  8. + (Matchup Adjustment × W8) [Opponent rank category]

- Weights are independent multipliers (not normalized to sum to 1.0)
- Default weights: Equal (0.125 each) initially, refine through data analysis
- Formula supports subtractions (ownership penalty, regression penalty)

### Data Sources
- **Projections:** ETR preferred (same format as DraftKings), LineStar fallback
- **ITT:** `vegas_lines` table (MVP, not Phase 2)
- **Opponent Rank:** Categorical (top_5, middle, bottom_5) from LineStar
- **Trends:** Last 2-4 games with 20+ snaps from `historical_stats`

### Weight Profiles
- Store as JSONB: `{W1: 0.3, W2: 0.15, W3: 0.2, W4: 0.1, W5: 0.15, W6: 0.05, W7: 0.05, W8: 0.0}`
- Store configuration: `{projection_source: "ETR", eighty_twenty_enabled: true, eighty_twenty_threshold: 20}`
- Default "Base" profile: Equal weights (0.125 each)
- User can create, save, and select custom profiles

### UI/UX Features
- **Recalculation:** "Apply" button (not real-time slider changes)
- **Snapshot Modal:** Shows all changed players, highlights top 10 biggest changes
- **Delta Indicators:** Show before/after scores with change amount
- **Baseline:** Does not persist after "Keep Changes"

### Missing Data Handling
- **Ceiling/Floor:** Estimate based on projection volatility or position defaults
- **Trends:** Use available games (min 2) or neutral (0) if insufficient
- **ITT:** Use league average (22.5)
- **Ownership:** Use league average
- **Opponent Rank:** Use "middle" category

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
- Weight adjustment panel: Dark gray surface (#1a1a2e), orange accent borders
- Smart Score column: Highlighted background, bold text
- Delta indicators: Green for positive (rgba(76, 175, 80, 0.3)), Red for negative (rgba(244, 67, 54, 0.3))
- Regression risk badge: Orange background (#ff5722), white text
- Snapshot modal: Dark background with orange accent header
- Top 10 changes highlight: Orange border (#ff8c42) or background

### Layout
- Page header: "Smart Score Engine" with breadcrumb navigation
- Main layout: Weight panel (left sidebar) + Player table (main area)
- Weight panel: Fixed width (300px), scrollable if needed
- Player table: Full-width with scroll container
- Snapshot modal: Centered, max-width 800px, overlay background

### Responsive Breakpoints
- Mobile: < 768px (stacked layout, weight panel above table)
- Tablet: 768px - 1024px (collapsible sidebar)
- Desktop: > 1024px (side-by-side layout)

---

## Reusable Components

### Existing Code to Leverage

#### Frontend Components
- **MainLayout** (`/frontend/src/components/layout/MainLayout.tsx`)
  - Reuse navigation structure for /smart-score route
  - Follow layout patterns for page container
  - Use existing theme/styling patterns

- **PlayerTable** (`/frontend/src/components/players/PlayerTable.tsx`) - IF EXISTS
  - Reuse table structure and sorting/filtering logic
  - Adapt for Smart Score columns
  - Extend with delta indicators

#### Frontend Hooks & Stores
- **useWeekStore** (`/frontend/src/store/weekStore.ts`)
  - Query current week to fetch week-specific players
  - Get week metadata for context (week number, season, status)
  - Monitor week selection changes to reload Smart Scores

- **React Query** patterns
  - Follow state management pattern for Smart Score data
  - Reuse loading/error state handling
  - Use similar async operation patterns

#### Backend Patterns
- **PlayerManagementService** (`/backend/services/player_management_service.py`) - IF EXISTS
  - Reuse player data retrieval patterns
  - Extend with Smart Score calculation logic

- **Database Schema** (existing tables from migrations)
  - `player_pools`: Player data per week
  - `historical_stats`: Historical performance data
  - `vegas_lines`: Vegas lines and ITT data
  - `weeks`: Week metadata for context

#### Styling & Theme
- **darkTheme** (`/frontend/src/theme.ts`)
  - Use Material-UI dark theme as base
  - Extend with orange accent color (#ff8c42)
  - Follow existing typography patterns
  - Maintain consistency with current design

### New Components Required

#### Frontend Components
1. **SmartScorePage**
   - New component: Main page container for /smart-score route
   - Why: Orchestrates child components, manages page-level state

2. **WeightAdjustmentPanel**
   - New component: Sidebar with weight sliders and controls
   - Why: Specialized UI for weight adjustment

3. **SmartScoreTable**
   - New component: Table displaying players with Smart Scores
   - Why: Extends PlayerTable with Smart Score-specific columns and features

4. **ScoreDeltaIndicator**
   - New component: Displays delta (+2.5, -1.3) next to scores
   - Why: Visual indicator for score changes

5. **SnapshotModal**
   - New component: Modal showing before/after scores
   - Why: User review workflow for weight changes

6. **WeightSlider**
   - New component: Individual slider for weight adjustment
   - Why: Reusable slider component with label and value display

7. **RegressionRiskBadge**
   - New component: Badge indicating regression risk
   - Why: Visual indicator for 80-20 rule

8. **ProfileSelector**
   - New component: Dropdown to select/save weight profiles
   - Why: Profile management UI

#### Frontend Hooks
1. **useSmartScore**
   - New hook: Centralized Smart Score calculation and data management
   - Manages: Fetching players, calculating scores, handling recalculation

2. **useWeightProfile**
   - New hook: Weight profile state and management
   - Manages: Current weights, saving/loading profiles

3. **useScoreSnapshot**
   - New hook: Snapshot/baseline comparison logic
   - Manages: Before/after scores, delta calculation

#### Backend Services
1. **SmartScoreService**
   - New service: Calculate Smart Scores for players
   - Responsibilities: Formula application, data enrichment, missing data handling

2. **WeightProfileService**
   - New service: Manage weight profiles
   - Responsibilities: Create, read, update, delete profiles

#### Database Changes
- New table: `weight_profiles`
  - `id` (PK)
  - `name` (STRING, unique)
  - `weights` (JSONB: {W1: 0.3, W2: 0.15, ...})
  - `config` (JSONB: {projection_source: "ETR", ...})
  - `created_at` (TIMESTAMP)
  - `updated_at` (TIMESTAMP)
  - `is_default` (BOOLEAN, default false)

- Update `player_pools` table:
  - Add `smart_score` (FLOAT, nullable)
  - Add `projection_source` (VARCHAR, nullable)
  - Add `opponent_rank_category` (VARCHAR: top_5/middle/bottom_5)
  - Add `games_with_20_plus_snaps` (INTEGER, nullable)
  - Add `regression_risk` (BOOLEAN, default false)

---

## Technical Approach

### Frontend Architecture

#### State Management
- **Global State (Zustand):** Week selection (reuse existing useWeekStore)
- **Local State (React hooks):** Weight state, profile selection, modal visibility
- **Component State (useState):** Snapshot comparison, loading states
- **Server State (React Query):** Player data fetching, Smart Score calculation

#### Data Flow
1. User navigates to `/smart-score` route
2. SmartScorePage component mounts
3. useSmartScore hook queries players for current week via React Query
4. SmartScoreService calculates Smart Scores for all players
5. Player table displays with Smart Scores
6. User adjusts weight sliders (local state only)
7. User clicks "Apply" → Previous scores stored → Recalculation triggered
8. Snapshot modal displays with before/after comparison
9. User clicks "Keep Changes" → Scores updated → Modal closes
10. Table updates with new Smart Scores and delta indicators

#### Component Hierarchy
```
SmartScorePage
├─ Header (title, breadcrumb)
├─ WeightAdjustmentPanel (sidebar)
│  ├─ ProfileSelector
│  ├─ WeightSlider[] (W1-W8)
│  ├─ ProjectionSourceSelector
│  └─ ActionButtons (Apply, Reset, Save Profile)
├─ SmartScoreTable (main area)
│  └─ PlayerRow[] (virtual scrolling)
│     ├─ SmartScoreCell (with delta indicator)
│     ├─ RegressionRiskBadge (if applicable)
│     └─ Other columns
└─ SnapshotModal (conditional)
   ├─ PlayerChangeRow[] (with delta)
   └─ ActionButtons (Keep Changes, Revert)
```

#### API Integration
- Use axios with configured base URL from environment
- React Query for server state management
- Cache Smart Score data with 5 minute stale time
- Invalidate cache on weight profile changes
- Handle loading and error states consistently
- Implement retry logic for failed requests (max 3 retries)

### Backend Architecture

#### Route Organization
- Create new `smart_score_router.py` for dedicated Smart Score endpoints

#### Service Layer
- **SmartScoreService:** Calculate Smart Scores
  - `calculate_smart_score(player, week_id, weights, config)` → Smart Score value
  - `calculate_for_all_players(week_id, weights, config)` → All player scores
  - `get_missing_data_defaults(week_id)` → Default values for missing data
  - `calculate_trend_adjustment(player, week_id)` → Position-specific trend
  - `calculate_vegas_context(player, week_id)` → ITT-based adjustment
  - `calculate_regression_risk(player, week_id)` → 80-20 rule check

- **WeightProfileService:** Profile management
  - `create_profile(name, weights, config)` → Profile ID
  - `get_profile(profile_id)` → Profile data
  - `list_profiles()` → All profiles
  - `update_profile(profile_id, weights, config)` → Updated profile
  - `delete_profile(profile_id)` → Success status

#### Database Queries
- Use SQLAlchemy ORM (if models exist) or raw SQL with proper parameterization
- Leverage existing indexes on player_pools and weeks tables
- Consider adding indexes:
  - `player_pools (week_id, smart_score)` for filtering
  - `historical_stats (player_key, week, snaps)` for trend calculation
  - `vegas_lines (week_id, team)` for ITT lookup

#### Error Handling
- Validate week_id exists and user has access
- Handle missing data gracefully (use defaults)
- Return structured error responses with meaningful messages
- Log all errors with context for debugging

### Performance Considerations

#### Frontend Optimization
- Virtual scrolling with TanStack Table (150-200 player threshold)
- Memoize expensive component renders with React.memo
- Debounce weight slider changes (visual only, not calculation)
- Lazy load modal content on open
- Client-side filtering/sorting for already-loaded data
- React Query stale-while-revalidate pattern for fresh data

#### Backend Optimization
- Batch Smart Score calculations (all players in single query if possible)
- Cache league averages (ownership, ITT) per week
- Use database indexes for lookups
- Implement calculation result caching (optional, Phase 2)
- Optimize historical_stats queries with proper filters

#### Data Transfer
- Only send necessary columns initially
- Compress responses with gzip (default for most servers)
- Implement incremental loading for large datasets

---

## Data Model & Database Changes

### New Tables

#### weight_profiles
```sql
CREATE TABLE weight_profiles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    weights JSONB NOT NULL,  -- {W1: 0.3, W2: 0.15, ...}
    config JSONB NOT NULL,   -- {projection_source: "ETR", eighty_twenty_enabled: true, ...}
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_weight_profiles_name ON weight_profiles(name);
```

### Table Updates

#### player_pools
```sql
ALTER TABLE player_pools ADD COLUMN smart_score FLOAT;
ALTER TABLE player_pools ADD COLUMN projection_source VARCHAR(50);
ALTER TABLE player_pools ADD COLUMN opponent_rank_category VARCHAR(10);  -- top_5, middle, bottom_5
ALTER TABLE player_pools ADD COLUMN games_with_20_plus_snaps INTEGER;
ALTER TABLE player_pools ADD COLUMN regression_risk BOOLEAN DEFAULT FALSE;

CREATE INDEX idx_player_pools_smart_score ON player_pools(week_id, smart_score);
CREATE INDEX idx_player_pools_opponent_rank ON player_pools(opponent_rank_category);
```

### Required Tables (Already Exist)

#### historical_stats
- Used for trend calculations
- Filter by `snaps >= 20` for trend data
- Query last 2-4 games per player

#### vegas_lines
- Used for ITT (Implied Team Total) lookup
- Calculate league average ITT per week
- Marked as MVP requirement (not Phase 2)

#### player_pools
- Base player data
- Enhanced with Smart Score columns (see above)

---

## Component Architecture

### Frontend Component Specs

#### SmartScorePage
- **Location:** `/frontend/src/pages/SmartScorePage.tsx`
- **Type:** Page component, main entry point for `/smart-score` route
- **Responsibilities:**
  - Fetch current week from store
  - Fetch player data via useSmartScore hook
  - Render weight panel and table
  - Handle page-level state (loading, error)
  - Coordinate recalculation workflow
- **Props:** None (uses store and hooks)
- **State:**
  - isLoading: boolean
  - error: string | null
- **Hooks:** useWeekStore, useSmartScore, useEffect for title

#### WeightAdjustmentPanel
- **Location:** `/frontend/src/components/smart-score/WeightAdjustmentPanel.tsx`
- **Type:** Feature component, sidebar panel
- **Responsibilities:**
  - Display weight sliders (W1-W8)
  - Handle weight changes (local state)
  - Display projection source selector
  - Handle Apply/Reset/Save Profile actions
- **Props:** `{ onApply: (weights, config) => void, onReset: () => void }`
- **State:**
  - weights: {W1: number, W2: number, ...}
  - projectionSource: string
  - selectedProfile: string | null
- **Sub-components:** WeightSlider, ProfileSelector

#### SmartScoreTable
- **Location:** `/frontend/src/components/smart-score/SmartScoreTable.tsx`
- **Type:** Feature component, uses TanStack Table
- **Responsibilities:**
  - Display players with Smart Scores
  - Show delta indicators
  - Display regression risk badges
  - Handle sorting/filtering
- **Props:** `{ players: Player[], isLoading: boolean, scoreDeltas: Map<playerId, number> }`
- **State:**
  - sorting: SortingState (TanStack)
  - expanded: ExpandedState (TanStack)
- **Hooks:** TanStack Table hooks, TanStack Virtual

#### SnapshotModal
- **Location:** `/frontend/src/components/smart-score/SnapshotModal.tsx`
- **Type:** Modal component
- **Responsibilities:**
  - Display before/after scores
  - Show delta for each player
  - Highlight top 10 biggest changes
  - Handle Keep Changes/Revert actions
- **Props:** `{ open: boolean, changes: ScoreChange[], onKeepChanges: () => void, onRevert: () => void }`
- **State:** None (presentation only)
- **Sub-components:** ScoreChangeRow

### Backend Endpoint Specs

#### POST /api/smart-score/calculate
- **Purpose:** Calculate Smart Scores for all players in a week
- **Body:**
  ```json
  {
    "week_id": 42,
    "weights": {
      "W1": 0.3,
      "W2": 0.15,
      "W3": 0.2,
      "W4": 0.1,
      "W5": 0.15,
      "W6": 0.05,
      "W7": 0.05,
      "W8": 0.0
    },
    "config": {
      "projection_source": "ETR",
      "eighty_twenty_enabled": true,
      "eighty_twenty_threshold": 20
    }
  }
  ```
- **Response (200):**
  ```json
  {
    "success": true,
    "scores": [
      {
        "player_id": 123,
        "player_key": "patrick_mahomes_KC_QB",
        "name": "Patrick Mahomes",
        "smart_score": 45.2,
        "breakdown": {
          "projection_factor": 24.5,
          "ceiling_factor": 8.5,
          "ownership_penalty": -0.175,
          "value_score": 306.25,
          "trend_adjustment": 0.05,
          "regression_penalty": 0,
          "vegas_context": 0.061,
          "matchup_adjustment": 0
        }
      }
    ],
    "calculation_time_ms": 234
  }
  ```

#### GET /api/smart-score/profiles
- **Purpose:** List all weight profiles
- **Response (200):**
  ```json
  {
    "success": true,
    "profiles": [
      {
        "id": 1,
        "name": "Base",
        "weights": {"W1": 0.125, "W2": 0.125, ...},
        "config": {"projection_source": "ETR", ...},
        "is_default": true
      }
    ]
  }
  ```

#### POST /api/smart-score/profiles
- **Purpose:** Create a new weight profile
- **Body:**
  ```json
  {
    "name": "My Custom Profile",
    "weights": {"W1": 0.3, "W2": 0.15, ...},
    "config": {"projection_source": "ETR", ...}
  }
  ```
- **Response (200):**
  ```json
  {
    "success": true,
    "profile": {
      "id": 2,
      "name": "My Custom Profile",
      ...
    }
  }
  ```

#### GET /api/smart-score/profiles/{profile_id}
- **Purpose:** Get a specific weight profile
- **Response (200):**
  ```json
  {
    "success": true,
    "profile": {
      "id": 1,
      "name": "Base",
      "weights": {...},
      "config": {...}
    }
  }
  ```

#### PUT /api/smart-score/profiles/{profile_id}
- **Purpose:** Update a weight profile
- **Body:** Same as POST (name, weights, config)
- **Response:** Updated profile

#### DELETE /api/smart-score/profiles/{profile_id}
- **Purpose:** Delete a weight profile
- **Response (200):**
  ```json
  {
    "success": true,
    "message": "Profile deleted"
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
| Accent | Orange | #ff8c42 | Buttons, active states |
| Smart Score Highlight | Orange | #ff8c42 | Smart Score column background |
| Delta Positive | Green | rgba(76, 175, 80, 0.3) | Positive delta indicators |
| Delta Negative | Red | rgba(244, 67, 54, 0.3) | Negative delta indicators |
| Regression Risk | Orange Red | #ff5722 | Regression risk badge |
| Top 10 Highlight | Orange | #ff8c42 | Top 10 changes in snapshot modal |

### Typography
- Page Title: 32px Bold Roboto
- Section Header: 20px Bold Roboto
- Smart Score: 18px Bold Roboto (highlighted)
- Table Header: 14px Medium Roboto
- Body Text: 14px Regular Roboto
- Delta Indicator: 12px Medium Roboto

### Spacing System (8px base unit)
- Page container: 24px horizontal, 32px vertical
- Weight panel: 300px width, 24px padding
- Table: Full-width with 16px padding
- Modal: 32px padding, max-width 800px

---

## Formula Implementation Details

### Factor Calculations

#### W1: Projection Factor
```
projection_factor = projection × W1
```
- Uses ETR or LineStar projection based on config
- Missing projection: Use 0 or exclude factor

#### W2: Ceiling Factor
```
ceiling_factor = (ceiling - floor) × W2
```
- If ceiling/floor missing: Estimate based on projection volatility
- Volatility estimate: `projection × volatility_multiplier` (position-based defaults)
- WR defaults: ±5 points, RB defaults: ±4 points

#### W3: Ownership Penalty
```
ownership_penalty = -(ownership × W3)
```
- Ownership stored as 0-1 decimal (0.35 = 35%)
- Higher ownership = larger penalty (subtracted from score)
- Missing ownership: Use league average

#### W4: Value Score
```
value_score = ((projection × 1000) / (salary / 100)) × W4
```
- Simplified: `(projection × 100000) / salary × W4`
- Lower weight (user indicates not highly reliable)

#### W5: Trend Adjustment
```
trend_adjustment = trend_percentage × W5
```
- Position-specific:
  - WR/TE: Target share trend
  - RB: Snap % trend
  - QB: Pass attempts trend
- Calculate from last 2-4 games with 20+ snaps
- Minimum 2 games required, otherwise neutral (0)

#### W6: Regression Penalty
```
regression_penalty = 0 (visual flag only in MVP)
```
- WR only, 20+ points last week
- MVP: Visual flag only, no penalty calculation
- Future: May add penalty adjustment

#### W7: Vegas Context
```
vegas_context = ((team_itt / league_avg_itt) × W7)
```
- ITT from `vegas_lines` table
- League average ITT calculated per week
- Missing ITT: Use league average (22.5 default)
- Additive (not multiplier)

#### W8: Matchup Adjustment
```
matchup_adjustment = category_value × W8
```
- Opponent rank category: top_5, middle, bottom_5
- Category values: top_5 = +1.0, middle = 0.0, bottom_5 = -1.0
- Lower weight (user indicates minimal impact)
- Missing: Use "middle" (0.0)

### Complete Formula
```
Smart Score = 
  (projection × W1) +
  ((ceiling - floor) × W2) +
  (-(ownership × W3)) +
  (((projection × 100000) / salary) × W4) +
  (trend_percentage × W5) +
  (-(regression_penalty × W6)) +  // 0 in MVP
  (((team_itt / league_avg_itt) × W7)) +
  (matchup_category_value × W8)
```

---

## Testing Strategy

### Unit Tests

#### Frontend Components
- **SmartScoreTable:** Test sorting, delta indicators, badge display
- **WeightAdjustmentPanel:** Test slider updates, profile selection, Apply button
- **SnapshotModal:** Test change display, top 10 highlighting, Keep/Revert actions

#### Frontend Hooks
- **useSmartScore:** Test calculation triggering, score updates, error handling
- **useWeightProfile:** Test profile loading, saving, selection
- **useScoreSnapshot:** Test snapshot creation, delta calculation

#### Backend Services
- **SmartScoreService:** Test formula calculation, missing data handling, each factor
- **WeightProfileService:** Test CRUD operations, validation

### Integration Tests

#### Frontend Integration
- Test weight adjustment → Apply → Snapshot modal → Keep Changes → Table update
- Test profile save → reload → profile selection → calculation

#### Backend Integration
- Test full calculation workflow with real database
- Test missing data defaults
- Test Vegas context calculation with ITT data

### E2E Tests

#### Happy Path Scenarios
1. **Calculate Smart Scores:** Load page, see scores calculated
2. **Adjust Weights:** Change sliders, click Apply, see snapshot modal
3. **Keep Changes:** Review snapshot, click Keep Changes, see updated scores
4. **Save Profile:** Enter name, save profile, see in dropdown
5. **Filter by Threshold:** Set threshold, see filtered results

#### Edge Cases
1. **Missing Data:** Verify defaults used, indicators shown
2. **No Historical Data:** Verify neutral trends, indicators shown
3. **Revert Changes:** Click Revert, verify scores restored
4. **Large Dataset:** Verify performance with 200+ players

### Performance Tests
- Calculation completes within 500ms for 200 players
- Snapshot modal renders within 100ms
- Table scroll maintains 60fps
- Weight slider updates smooth (no lag)

---

## Dependencies & Phase Alignment

### Phase Alignment

#### Phase 0 Completed (Foundations)
- Data Import System: Imports players, projections, historical stats
- Week Management: Manages week selection
- Database: All tables created (player_pools, historical_stats, vegas_lines)

#### Phase 1 (Current)
- Smart Score Engine: Calculate and display Smart Scores
- Weight Profile Management: Save/load custom profiles
- Recalculation Workflow: Snapshot comparison and delta indicators

#### Phase 2 (Future)
- Regression Penalty Calculation: Add penalty adjustment beyond visual flag
- Advanced Analytics: Historical Smart Score tracking
- Profile Sharing: Share profiles between users
- Performance Optimization: Caching, batch processing

### External Dependencies

#### Frontend Libraries
- **React 18+:** Core framework (existing)
- **React Router 6+:** Page routing (existing, extend with /smart-score route)
- **Zustand 4+:** Global state (existing, reuse week store)
- **TanStack React Query 5+:** Server state management (existing)
- **TanStack Table (React Table) 8+:** Data table (existing or add)
- **Material-UI 5+:** Component library (existing, extend with Smart Score components)
- **Axios 1+:** HTTP client (existing)

#### Backend Dependencies
- **FastAPI 0.100+:** Web framework (existing)
- **SQLAlchemy 2+:** ORM (existing)
- **Alembic:** Database migrations (existing)
- **Python 3.9+:** Runtime (existing)
- **PostgreSQL 12+:** Database (existing)

### Database Migrations Required
- Create `weight_profiles` table
- Add columns to `player_pools` table
- Create indexes for performance

---

## Known Constraints & Limitations

### Phase 1 Scope

#### Out of Scope Features
- **Regression Penalty Calculation:** Visual flag only, no penalty in formula
- **Historical Score Tracking:** Track scores across weeks (Phase 2)
- **Profile Sharing:** Share profiles between users (Phase 2)
- **Advanced Analytics:** Score distribution, correlation analysis (Phase 2)
- **Batch Processing:** Optimize for very large datasets (Phase 2)

### Technical Constraints

#### Database Constraints
- Must work with existing schema
- JSONB columns for flexibility
- Indexes for performance optimization

#### Performance Constraints
- Calculation must complete within 500ms for 200 players
- Snapshot modal must render within 100ms
- Table must support virtual scrolling

#### Data Constraints
- ETR data format assumed (same as DraftKings)
- Vegas lines table must be populated (MVP requirement)
- Historical stats must have snap data for trends

### Known Issues & Workarounds

#### Issue 1: Missing Ceiling/Floor
- **Problem:** Not all sources provide ceiling/floor
- **Solution:** Estimate based on projection volatility or position defaults
- **Workaround:** Use projection ± defaults if volatility unavailable

#### Issue 2: Insufficient Historical Data
- **Problem:** Some players have < 2 games with 20+ snaps
- **Solution:** Use neutral trend (0) if insufficient data
- **Workaround:** Show indicator for insufficient data

#### Issue 3: Vegas Lines Not Available
- **Problem:** ITT data may not be available for all weeks
- **Solution:** Use league average ITT (22.5 default)
- **Workaround:** Show indicator when defaults used

---

## Success Criteria

### User Experience Goals
- Users can access Smart Score page within 1 click from navigation
- Smart Scores calculated and displayed within 3 seconds of page load
- Weight adjustment and recalculation workflow takes < 2 minutes
- Snapshot modal clearly shows impact of changes
- Mobile users can perform all tasks

### Functional Goals
- Smart Scores calculated correctly for all players
- Weight profiles save and load correctly
- Missing data handled gracefully with defaults
- Recalculation workflow functions without errors
- Delta indicators show accurate changes

### Performance Goals
- Calculation completes within 500ms for 200 players
- Snapshot modal renders within 100ms
- Table scroll maintains 60fps
- Page loads in < 3 seconds

### Quality Goals
- Zero console errors on page load
- No TypeScript type errors (strict mode)
- All user stories have passing tests
- Formula calculations verified with test data

---

## File Structure Overview

```
frontend/
├─ src/
│  ├─ pages/
│  │  └─ SmartScorePage.tsx                    (NEW)
│  ├─ components/
│  │  ├─ smart-score/                           (NEW directory)
│  │  │  ├─ WeightAdjustmentPanel.tsx           (NEW)
│  │  │  ├─ WeightSlider.tsx                    (NEW)
│  │  │  ├─ SmartScoreTable.tsx                 (NEW)
│  │  │  ├─ ScoreDeltaIndicator.tsx             (NEW)
│  │  │  ├─ SnapshotModal.tsx                   (NEW)
│  │  │  ├─ ScoreChangeRow.tsx                  (NEW)
│  │  │  ├─ RegressionRiskBadge.tsx             (NEW)
│  │  │  ├─ ProfileSelector.tsx                 (NEW)
│  │  │  └─ index.ts                            (NEW)
│  │  └─ layout/
│  │     └─ MainLayout.tsx                      (MODIFY - add /smart-score route)
│  ├─ hooks/
│  │  ├─ useSmartScore.ts                       (NEW)
│  │  ├─ useWeightProfile.ts                    (NEW)
│  │  ├─ useScoreSnapshot.ts                   (NEW)
│  │  └─ index.ts                               (MODIFY - export new hooks)
│  └─ main.tsx                                  (MODIFY - add /smart-score route)

backend/
├─ routers/
│  └─ smart_score_router.py                    (NEW)
├─ services/
│  ├─ smart_score_service.py                   (NEW)
│  └─ weight_profile_service.py                (NEW)
├─ schemas/
│  └─ smart_score_schemas.py                    (NEW - Pydantic models)
└─ main.py                                      (MODIFY - register new router)

alembic/
└─ versions/
   └─ XXXX_add_smart_score_tables.py           (NEW migration)
```

---

## Implementation Timeline

### Week 1 (Oct 30 - Nov 5)
- Set up component structure and routing
- Implement database migrations
- Build SmartScoreService backend logic
- Build WeightAdjustmentPanel component
- Total estimated effort: 40 hours

### Week 2 (Nov 6 - Nov 12)
- Build SmartScoreTable component
- Implement formula calculation logic
- Build SnapshotModal component
- Implement weight profile management
- Total estimated effort: 40 hours

### Week 3 (Nov 13 - Nov 19)
- Missing data handling implementation
- Delta indicators and visual feedback
- Integration testing
- Performance optimization
- Total estimated effort: 35 hours

### Week 4 (Nov 20 - Nov 26)
- Bug fixes from testing
- Documentation
- UAT and user testing
- Final deployment
- Total estimated effort: 30 hours

**Total Estimated Effort:** 145 hours (3.6 weeks for 1 developer)

---

## Sign-Off & Approval

**Prepared by:** AI Assistant (Claude Code)  
**Date:** 2025-10-30  
**Version:** 1.0 - Initial Specification  
**Status:** Ready for Development

**Key Stakeholders:**
- Product Manager: Approval needed
- Tech Lead: Review for technical feasibility
- Design Lead: Review for design consistency
- QA Lead: Review for testability

---

## Appendices

### A. Formula Breakdown Example

```
Player: Patrick Mahomes (QB, KC)
Projection: 24.5 (ETR)
Ceiling: 45.2, Floor: 18.3
Ownership: 0.35 (35%)
Salary: 8000 ($80)
Trend: +5% (pass attempts increasing)
ITT: 27.5 (KC), League Avg: 22.5
Opponent Rank: middle

Weights: W1=0.3, W2=0.15, W3=0.2, W4=0.1, W5=0.15, W6=0.05, W7=0.05, W8=0.0

Calculation:
  Projection Factor: 24.5 × 0.3 = 7.35
  Ceiling Factor: (45.2 - 18.3) × 0.15 = 4.035
  Ownership Penalty: -(0.35 × 0.2) = -0.07
  Value Score: ((24.5 × 100000) / 8000) × 0.1 = 30.625
  Trend Adjustment: 0.05 × 0.15 = 0.0075
  Regression Penalty: 0 (not WR)
  Vegas Context: ((27.5 / 22.5) × 0.05) = 0.061
  Matchup Adjustment: 0.0 × 0.0 = 0

Smart Score = 7.35 + 4.035 - 0.07 + 30.625 + 0.0075 + 0 + 0.061 + 0
           = 42.0085
```

### B. API Request/Response Examples

#### Calculate Smart Scores
```bash
POST /api/smart-score/calculate

Body:
{
  "week_id": 42,
  "weights": {
    "W1": 0.3,
    "W2": 0.15,
    "W3": 0.2,
    "W4": 0.1,
    "W5": 0.15,
    "W6": 0.05,
    "W7": 0.05,
    "W8": 0.0
  },
  "config": {
    "projection_source": "ETR",
    "eighty_twenty_enabled": true,
    "eighty_twenty_threshold": 20
  }
}

Response:
{
  "success": true,
  "scores": [
    {
      "player_id": 123,
      "player_key": "patrick_mahomes_KC_QB",
      "name": "Patrick Mahomes",
      "smart_score": 42.01,
      "breakdown": {
        "projection_factor": 7.35,
        "ceiling_factor": 4.035,
        "ownership_penalty": -0.07,
        "value_score": 30.625,
        "trend_adjustment": 0.0075,
        "regression_penalty": 0,
        "vegas_context": 0.061,
        "matchup_adjustment": 0
      }
    }
  ],
  "calculation_time_ms": 234
}
```

### C. Component Prop Interfaces (TypeScript)

```typescript
// WeightAdjustmentPanel
interface WeightAdjustmentPanelProps {
  initialWeights: WeightProfile;
  onApply: (weights: WeightProfile, config: ScoreConfig) => void;
  onReset: () => void;
  onSaveProfile: (name: string, weights: WeightProfile, config: ScoreConfig) => void;
}

// SmartScoreTable
interface SmartScoreTableProps {
  players: PlayerWithScore[];
  isLoading: boolean;
  scoreDeltas: Map<number, number>;
  onPlayerClick?: (player: PlayerWithScore) => void;
}

// SnapshotModal
interface SnapshotModalProps {
  open: boolean;
  changes: ScoreChange[];
  onKeepChanges: () => void;
  onRevert: () => void;
}

// ScoreChange
interface ScoreChange {
  playerId: number;
  playerName: string;
  previousScore: number;
  newScore: number;
  delta: number;
  isTopChange: boolean;
}

// WeightProfile
interface WeightProfile {
  W1: number;
  W2: number;
  W3: number;
  W4: number;
  W5: number;
  W6: number;
  W7: number;
  W8: number;
}

// ScoreConfig
interface ScoreConfig {
  projection_source: "ETR" | "LineStar";
  eighty_twenty_enabled: boolean;
  eighty_twenty_threshold: number;
}
```

### D. Glossary

- **Smart Score:** Comprehensive player value score calculated from 8 factors
- **Weight Profile:** Set of 8 weights (W1-W8) used for calculation
- **Ceiling Factor:** Range between ceiling and floor projections
- **Ownership Penalty:** Negative adjustment based on ownership percentage
- **Value Score:** Points per dollar metric (projection / salary)
- **Trend Adjustment:** Percentage change in key metrics over last 2-4 games
- **Regression Risk:** 80-20 rule indicator for WRs who scored 20+ last week
- **Vegas Context:** Adjustment based on team's implied team total vs. league average
- **Matchup Adjustment:** Adjustment based on opponent defensive rank category
- **ITT:** Implied Team Total (from Vegas lines)
- **Snapshot:** Before/after score comparison after recalculation
- **Delta:** Change amount (+X.X or -X.X) between scores

