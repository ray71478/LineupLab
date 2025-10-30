# Smart Score Engine - Tasks List

**Feature:** Smart Score Engine  
**Phase:** Phase 1 - MVP  
**Created:** October 30, 2025  
**Based on:** spec.md and requirements.md

---

## Task Groups Overview

1. **Database & Backend Foundation** - Database migrations, schema updates, backend services
2. **Smart Score Calculation Engine** - Core formula implementation, factor calculations
3. **Weight Profile Management** - Profile CRUD operations, storage, retrieval
4. **Frontend Page & Components** - Page structure, table, weight adjustment panel
5. **Recalculation & Snapshot Workflow** - Apply button, snapshot modal, delta indicators
6. **Data Integration & Missing Data Handling** - ETR/LineStar integration, defaults
7. **Visual Indicators & UI Polish** - Regression badges, delta indicators, styling
8. **Testing & Quality Assurance** - Unit tests, integration tests, E2E tests
9. **Performance & Optimization** - Caching, virtual scrolling, calculation optimization

---

### Group 1: Database & Backend Foundation (Data Layer)

#### Task 1.1: Create Database Migration for Weight Profiles Table
**Status:** completed
**Type:** Database
**Effort:** S
**Priority:** High
**Dependencies:** None

**Description:**
Create Alembic migration to add `weight_profiles` table for storing custom weight profiles.

**Subtasks:**
- [x] 1.1.1 Create migration file: `XXXX_add_weight_profiles_table.py`
- [x] 1.1.2 Define `weight_profiles` table schema:
  - `id` (SERIAL PRIMARY KEY)
  - `name` (VARCHAR(100) UNIQUE NOT NULL)
  - `weights` (JSONB NOT NULL)
  - `config` (JSONB NOT NULL)
  - `is_default` (BOOLEAN DEFAULT FALSE)
  - `created_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
  - `updated_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
- [x] 1.1.3 Create index on `name` column
- [x] 1.1.4 Create seed data for default "Base" profile with equal weights (0.125 each)
- [x] 1.1.5 Test migration up/down
- [x] 1.1.6 Verify table creation and constraints

**Acceptance Criteria:**
- Migration runs successfully
- Table created with correct schema
- Default "Base" profile exists after migration
- Unique constraint on name works
- Indexes created properly

**Files to Create:**
- `/alembic/versions/XXXX_add_weight_profiles_table.py`

**Implementation Details:**
```python
# weight_profiles table structure
CREATE TABLE weight_profiles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    weights JSONB NOT NULL,  -- {W1: 0.125, W2: 0.125, ...}
    config JSONB NOT NULL,   -- {projection_source: "ETR", ...}
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

#### Task 1.2: Create Database Migration for Player Pools Smart Score Columns
**Status:** completed
**Type:** Database
**Effort:** S
**Priority:** High
**Dependencies:** None

**Description:**
Add Smart Score related columns to `player_pools` table for storing calculated scores and metadata.

**Subtasks:**
- [x] 1.2.1 Create migration file: `XXXX_add_smart_score_columns_to_player_pools.py`
- [x] 1.2.2 Add columns:
  - `smart_score` (FLOAT, nullable)
  - `projection_source` (VARCHAR(50), nullable)
  - `opponent_rank_category` (VARCHAR(10), nullable) -- top_5, middle, bottom_5
  - `games_with_20_plus_snaps` (INTEGER, nullable)
  - `regression_risk` (BOOLEAN DEFAULT FALSE)
- [x] 1.2.3 Create index on `(week_id, smart_score)` for filtering
- [x] 1.2.4 Create index on `opponent_rank_category` for filtering
- [x] 1.2.5 Test migration up/down
- [x] 1.2.6 Verify column additions and defaults

**Acceptance Criteria:**
- Migration runs successfully
- All columns added with correct types
- Indexes created properly
- Existing data preserved
- Nullable columns allow NULL values

**Files to Create:**
- `/alembic/versions/XXXX_add_smart_score_columns_to_player_pools.py`

**Implementation Details:**
```sql
ALTER TABLE player_pools ADD COLUMN smart_score FLOAT;
ALTER TABLE player_pools ADD COLUMN projection_source VARCHAR(50);
ALTER TABLE player_pools ADD COLUMN opponent_rank_category VARCHAR(10);
ALTER TABLE player_pools ADD COLUMN games_with_20_plus_snaps INTEGER;
ALTER TABLE player_pools ADD COLUMN regression_risk BOOLEAN DEFAULT FALSE;

CREATE INDEX idx_player_pools_smart_score ON player_pools(week_id, smart_score);
CREATE INDEX idx_player_pools_opponent_rank ON player_pools(opponent_rank_category);
```

---

#### Task 1.3: Create Pydantic Schemas for Smart Score
**Status:** completed
**Type:** Backend
**Effort:** S
**Priority:** High
**Dependencies:** Task 1.1, Task 1.2

**Description:**
Create Pydantic schema models for Smart Score API requests and responses.

**Subtasks:**
- [x] 1.3.1 Create `/backend/schemas/smart_score_schemas.py`
- [x] 1.3.2 Define `WeightProfile` schema (W1-W8 weights)
- [x] 1.3.3 Define `ScoreConfig` schema (projection_source, eighty_twenty settings)
- [x] 1.3.4 Define `CalculateScoreRequest` schema
- [x] 1.3.5 Define `ScoreBreakdown` schema (factor breakdown)
- [x] 1.3.6 Define `PlayerScoreResponse` schema
- [x] 1.3.7 Define `WeightProfileResponse` schema
- [x] 1.3.8 Define `CreateProfileRequest` schema
- [x] 1.3.9 Define `UpdateProfileRequest` schema
- [x] 1.3.10 Add validation rules (weight ranges, required fields)

**Acceptance Criteria:**
- All schemas defined with proper types
- Validation rules enforced
- Request/response schemas match API spec
- Default values set appropriately

**Files to Create:**
- `/backend/schemas/smart_score_schemas.py`

**Implementation Details:**
```python
# Example schemas
class WeightProfile(BaseModel):
    W1: float = Field(ge=0.0, le=1.0)
    W2: float = Field(ge=0.0, le=1.0)
    # ... W3-W8

class ScoreConfig(BaseModel):
    projection_source: Literal["ETR", "LineStar"]
    eighty_twenty_enabled: bool = True
    eighty_twenty_threshold: float = 20.0
```

---

### Group 2: Smart Score Calculation Engine (Core Logic)

#### Task 2.1: Create SmartScoreService - Core Calculation Logic
**Status:** pending
**Type:** Backend Service
**Effort:** L
**Priority:** High
**Dependencies:** Task 1.3

**Description:**
Implement the core SmartScoreService with the 8-factor formula calculation logic.

**Subtasks:**
- [ ] 2.1.1 Create `/backend/services/smart_score_service.py`
- [ ] 2.1.2 Implement `calculate_smart_score(player, week_id, weights, config)` method
- [ ] 2.1.3 Implement W1: Projection Factor calculation
- [ ] 2.1.4 Implement W2: Ceiling Factor calculation (with missing data handling)
- [ ] 2.1.5 Implement W3: Ownership Penalty calculation
- [ ] 2.1.6 Implement W4: Value Score calculation
- [ ] 2.1.7 Implement W5: Trend Adjustment calculation (position-specific)
- [ ] 2.1.8 Implement W6: Regression Penalty calculation (WR only, visual flag in MVP)
- [ ] 2.1.9 Implement W7: Vegas Context calculation (ITT-based)
- [ ] 2.1.10 Implement W8: Matchup Adjustment calculation
- [ ] 2.1.11 Implement `calculate_for_all_players(week_id, weights, config)` method
- [ ] 2.1.12 Return score breakdown for each factor
- [ ] 2.1.13 Add unit tests for each factor calculation

**Acceptance Criteria:**
- All 8 factors calculated correctly
- Formula matches spec: `Smart Score = W1 + W2 - W3 + W4 + W5 - W6 + W7 + W8`
- Missing data handled gracefully
- Position-specific logic implemented correctly
- Calculation time < 500ms for 200 players

**Files to Create:**
- `/backend/services/smart_score_service.py`
- `/tests/unit/test_smart_score_service.py`

**Implementation Details:**
- Formula: `Smart Score = (projection × W1) + ((ceiling - floor) × W2) - (ownership × W3) + (value_score × W4) + (trend × W5) - (regression × W6) + (vegas_context × W7) + (matchup × W8)`
- Each factor method returns tuple: `(factor_value, breakdown_info)`
- Breakdown includes per-factor values for debugging/display

---

#### Task 2.2: Implement Missing Data Handling
**Status:** pending
**Type:** Backend Service
**Effort:** M
**Priority:** High
**Dependencies:** Task 2.1

**Description:**
Implement intelligent defaults and fallbacks for missing data in Smart Score calculation.

**Subtasks:**
- [ ] 2.2.1 Implement `get_missing_data_defaults(week_id)` method
- [ ] 2.2.2 Calculate league average ownership per week
- [ ] 2.2.3 Calculate league average ITT per week from `vegas_lines`
- [ ] 2.2.4 Implement ceiling/floor estimation based on projection volatility
- [ ] 2.2.5 Implement position-based default ranges (WR: ±5, RB: ±4)
- [ ] 2.2.6 Handle missing projection (use 0 or exclude factor)
- [ ] 2.2.7 Handle missing historical stats (neutral trend = 0)
- [ ] 2.2.8 Handle missing ITT (use league average 22.5)
- [ ] 2.2.9 Handle missing opponent rank (use "middle" category)
- [ ] 2.2.10 Return indicators for which defaults were used

**Acceptance Criteria:**
- All missing data scenarios handled
- Defaults calculated dynamically from available data
- Indicators show when defaults used
- No calculation errors from missing data

**Files to Modify:**
- `/backend/services/smart_score_service.py`

**Implementation Details:**
- League average ownership: `SELECT AVG(ownership) FROM player_pools WHERE week_id = X`
- League average ITT: `SELECT AVG(implied_team_total) FROM vegas_lines WHERE week_id = X`
- Volatility estimate: Calculate `std_dev(projections)` from historical_stats if available

---

#### Task 2.3: Implement Trend Calculation (Position-Specific)
**Status:** pending
**Type:** Backend Service
**Effort:** M
**Priority:** High
**Dependencies:** Task 2.1

**Description:**
Calculate trend adjustments for each position using position-specific metrics from historical_stats.

**Subtasks:**
- [ ] 2.3.1 Implement `calculate_trend_adjustment(player, week_id)` method
- [ ] 2.3.2 Query `historical_stats` for last 2-4 games with `snaps >= 20`
- [ ] 2.3.3 Implement WR/TE trend: Calculate `target_share` trend
- [ ] 2.3.4 Implement RB trend: Calculate `snap_pct` trend
- [ ] 2.3.5 Implement QB trend: Calculate `pass_attempts` trend (or derive from pass_yards)
- [ ] 2.3.6 Implement DST trend: Skip (return 0 or neutral)
- [ ] 2.3.7 Calculate percentage change: `(most_recent - oldest) / oldest`
- [ ] 2.3.8 Handle minimum 2 games requirement (use neutral if < 2 games)
- [ ] 2.3.9 Count games with 20+ snaps for display
- [ ] 2.3.10 Add unit tests for each position type

**Acceptance Criteria:**
- Position-specific metrics used correctly
- Trends calculated from 20+ snap games only
- Minimum 2 games enforced
- Percentage change calculated correctly
- Games count returned for display

**Files to Modify:**
- `/backend/services/smart_score_service.py`

**Implementation Details:**
- Query: `SELECT * FROM historical_stats WHERE player_key = X AND snaps >= 20 ORDER BY week DESC LIMIT 4`
- Trend formula: `(current_value - previous_value) / previous_value`
- If < 2 games: Return 0 (neutral trend)

---

#### Task 2.4: Implement Vegas Context Calculation (ITT)
**Status:** pending
**Type:** Backend Service
**Effort:** M
**Priority:** High
**Dependencies:** Task 2.1, Task 2.2

**Description:**
Calculate Vegas Context factor using player's team ITT vs. league average ITT from vegas_lines table.

**Subtasks:**
- [ ] 2.4.1 Implement `calculate_vegas_context(player, week_id)` method
- [ ] 2.4.2 Query `vegas_lines` for player's team ITT for the week
- [ ] 2.4.3 Calculate league average ITT from all teams in `vegas_lines` for the week
- [ ] 2.4.4 Calculate ratio: `team_itt / league_avg_itt`
- [ ] 2.4.5 Apply weight: `ratio × W7`
- [ ] 2.4.6 Handle missing ITT: Use league average (22.5 default)
- [ ] 2.4.7 Handle missing team ITT: Use league average
- [ ] 2.4.8 Add unit tests for ITT calculation

**Acceptance Criteria:**
- ITT retrieved from vegas_lines table
- League average calculated correctly
- Ratio calculation correct
- Missing data handled with defaults
- Formula: `(team_itt / league_avg_itt) × W7`

**Files to Modify:**
- `/backend/services/smart_score_service.py`

**Implementation Details:**
- Query: `SELECT implied_team_total FROM vegas_lines WHERE week_id = X AND team = player_team`
- League avg: `SELECT AVG(implied_team_total) FROM vegas_lines WHERE week_id = X`
- Default: If no data, use 22.5 for league average

---

#### Task 2.5: Implement Regression Risk Detection (80-20 Rule)
**Status:** pending
**Type:** Backend Service
**Effort:** S
**Priority:** Medium
**Dependencies:** Task 2.1

**Description:**
Detect WR players who scored 20+ points last week (regression risk indicator).

**Subtasks:**
- [ ] 2.5.1 Implement `calculate_regression_risk(player, week_id)` method
- [ ] 2.5.2 Check if player position is WR (only WR, not TE/RB/QB/DST)
- [ ] 2.5.3 Query `historical_stats` for previous week's `actual_points`
- [ ] 2.5.4 Check if `actual_points >= threshold` (default 20)
- [ ] 2.5.5 Return boolean flag: `regression_risk = True/False`
- [ ] 2.5.6 Handle missing historical data: Return False with indicator
- [ ] 2.5.7 MVP: Visual flag only, no penalty calculation (W6 = 0 in formula)
- [ ] 2.5.8 Add unit tests for regression detection

**Acceptance Criteria:**
- Only WR players checked
- Threshold configurable (default 20)
- Missing data handled gracefully
- Flag stored in `player_pools.regression_risk`
- MVP: No penalty calculation, visual flag only

**Files to Modify:**
- `/backend/services/smart_score_service.py`

**Implementation Details:**
- Query: `SELECT actual_points FROM historical_stats WHERE player_key = X AND week = previous_week`
- Filter: Only check if `position = 'WR'`
- Threshold: Configurable, default 20 DK points

---

#### Task 2.6: Implement Opponent Rank Categorization
**Status:** pending
**Type:** Backend Service
**Effort:** S
**Priority:** Medium
**Dependencies:** Task 2.1

**Description:**
Categorize opponent defensive rank into top_5, middle, bottom_5 categories for matchup adjustment.

**Subtasks:**
- [ ] 2.6.1 Implement `categorize_opponent_rank(opp_rank)` method
- [ ] 2.6.2 Categorize: Rank 1-5 = "top_5", Rank 28-32 = "bottom_5", else "middle"
- [ ] 2.6.3 Implement `calculate_matchup_adjustment(player, week_id)` method
- [ ] 2.6.4 Map category to value: top_5 = +1.0, middle = 0.0, bottom_5 = -1.0
- [ ] 2.6.5 Apply weight: `category_value × W8`
- [ ] 2.6.6 Handle missing opponent rank: Use "middle" (0.0)
- [ ] 2.6.7 Store category in `player_pools.opponent_rank_category`
- [ ] 2.6.8 Add unit tests for categorization

**Acceptance Criteria:**
- Categories assigned correctly
- Category values mapped correctly
- Missing data defaults to "middle"
- Category stored in database
- Formula: `category_value × W8`

**Files to Modify:**
- `/backend/services/smart_score_service.py`

**Implementation Details:**
- Import `OppRank` from LineStar during import
- Categorize during import or calculation
- Store as VARCHAR: "top_5", "middle", "bottom_5"

---

### Group 3: Weight Profile Management (Backend API)

#### Task 3.1: Create WeightProfileService
**Status:** pending
**Type:** Backend Service
**Effort:** M
**Priority:** High
**Dependencies:** Task 1.1, Task 1.3

**Description:**
Implement WeightProfileService for CRUD operations on weight profiles.

**Subtasks:**
- [ ] 3.1.1 Create `/backend/services/weight_profile_service.py`
- [ ] 3.1.2 Implement `create_profile(name, weights, config)` method
- [ ] 3.1.3 Implement `get_profile(profile_id)` method
- [ ] 3.1.4 Implement `list_profiles()` method
- [ ] 3.1.5 Implement `update_profile(profile_id, weights, config)` method
- [ ] 3.1.6 Implement `delete_profile(profile_id)` method
- [ ] 3.1.7 Implement `get_default_profile()` method
- [ ] 3.1.8 Validate unique name constraint
- [ ] 3.1.9 Prevent deletion of default "Base" profile
- [ ] 3.1.10 Add unit tests for all CRUD operations

**Acceptance Criteria:**
- All CRUD operations work correctly
- Name uniqueness enforced
- Default profile protected from deletion
- Validation errors handled properly
- Database transactions handled correctly

**Files to Create:**
- `/backend/services/weight_profile_service.py`
- `/tests/unit/test_weight_profile_service.py`

**Implementation Details:**
- Use SQLAlchemy ORM or raw SQL with parameterization
- Validate JSONB structure for weights and config
- Handle database errors gracefully

---

#### Task 3.2: Create Smart Score Router API Endpoints
**Status:** pending
**Type:** Backend API
**Effort:** M
**Priority:** High
**Dependencies:** Task 2.1, Task 3.1

**Description:**
Create FastAPI router with endpoints for Smart Score calculation and weight profile management.

**Subtasks:**
- [ ] 3.2.1 Create `/backend/routers/smart_score_router.py`
- [ ] 3.2.2 Implement `POST /api/smart-score/calculate` endpoint
- [ ] 3.2.3 Implement `GET /api/smart-score/profiles` endpoint
- [ ] 3.2.4 Implement `POST /api/smart-score/profiles` endpoint (create)
- [ ] 3.2.5 Implement `GET /api/smart-score/profiles/{profile_id}` endpoint
- [ ] 3.2.6 Implement `PUT /api/smart-score/profiles/{profile_id}` endpoint
- [ ] 3.2.7 Implement `DELETE /api/smart-score/profiles/{profile_id}` endpoint
- [ ] 3.2.8 Add request validation using Pydantic schemas
- [ ] 3.2.9 Add error handling and appropriate HTTP status codes
- [ ] 3.2.10 Register router in main.py
- [ ] 3.2.11 Add API documentation (OpenAPI/Swagger)

**Acceptance Criteria:**
- All endpoints implemented correctly
- Request validation works
- Error responses are meaningful
- API documentation generated
- Router registered in main app

**Files to Create:**
- `/backend/routers/smart_score_router.py`

**Files to Modify:**
- `/backend/main.py` (register router)

**Implementation Details:**
- Use FastAPI dependency injection for services
- Return structured responses: `{success: bool, data: ..., error: ...}`
- Handle 400 (bad request), 404 (not found), 500 (server error)

---

### Group 4: Frontend Page & Components (UI Foundation)

#### Task 4.1: Create SmartScorePage Component
**Status:** pending
**Type:** Frontend Component
**Effort:** M
**Priority:** High
**Dependencies:** None

**Description:**
Create main page component for Smart Score Engine with routing and layout.

**Subtasks:**
- [ ] 4.1.1 Create `/frontend/src/pages/SmartScorePage.tsx`
- [ ] 4.1.2 Set up page layout (header, weight panel, table)
- [ ] 4.1.3 Integrate with useWeekStore for current week
- [ ] 4.1.4 Add page title "Smart Score Engine"
- [ ] 4.1.5 Handle loading and error states
- [ ] 4.1.6 Add route `/smart-score` in main router
- [ ] 4.1.7 Add navigation link in MainLayout
- [ ] 4.1.8 Style page with dark theme
- [ ] 4.1.9 Add responsive layout structure

**Acceptance Criteria:**
- Page loads and displays correctly
- Route works from navigation
- Week selection integrated
- Loading/error states displayed
- Responsive layout works

**Files to Create:**
- `/frontend/src/pages/SmartScorePage.tsx`

**Files to Modify:**
- `/frontend/src/main.tsx` (add route)
- `/frontend/src/components/layout/MainLayout.tsx` (add nav link)

---

#### Task 4.2: Create useSmartScore Hook
**Status:** pending
**Type:** Frontend Hook
**Effort:** M
**Priority:** High
**Dependencies:** Task 3.2

**Description:**
Create React hook for managing Smart Score data fetching, calculation, and state.

**Subtasks:**
- [ ] 4.2.1 Create `/frontend/src/hooks/useSmartScore.ts`
- [ ] 4.2.2 Implement player data fetching with React Query
- [ ] 4.2.3 Implement Smart Score calculation trigger
- [ ] 4.2.4 Implement score recalculation function
- [ ] 4.2.5 Manage loading and error states
- [ ] 4.2.6 Cache scores with 5 minute stale time
- [ ] 4.2.7 Implement score invalidation on weight changes
- [ ] 4.2.8 Return players with scores, loading, error, recalculate function

**Acceptance Criteria:**
- Hook fetches player data correctly
- Calculation can be triggered
- Loading/error states managed
- Caching works correctly
- Invalidation triggers refresh

**Files to Create:**
- `/frontend/src/hooks/useSmartScore.ts`

**Implementation Details:**
- Use React Query for server state
- Cache key: `['smart-scores', week_id]`
- Stale time: 5 minutes
- Invalidate on weight profile changes

---

#### Task 4.3: Create SmartScoreTable Component
**Status:** pending
**Type:** Frontend Component
**Effort:** L
**Priority:** High
**Dependencies:** Task 4.1, Task 4.2

**Description:**
Create table component displaying players with Smart Scores, sortable columns, and virtual scrolling.

**Subtasks:**
- [ ] 4.3.1 Create `/frontend/src/components/smart-score/SmartScoreTable.tsx`
- [ ] 4.3.2 Set up TanStack Table with columns:
  - Player Name (sortable, filterable)
  - Team (sortable, filterable)
  - Position (sortable, filterable)
  - Salary (sortable)
  - Projection (sortable)
  - Ownership % (sortable)
  - Smart Score (sortable, highlighted)
  - Projection Source (ETR/LineStar)
  - 20+ Snap Games count
  - Regression Risk indicator (WR only)
- [ ] 4.3.3 Implement virtual scrolling for 150-200 players
- [ ] 4.3.4 Add sorting functionality for all sortable columns
- [ ] 4.3.5 Add filtering by position and team
- [ ] 4.3.6 Style Smart Score column (highlighted background)
- [ ] 4.3.7 Handle empty states gracefully
- [ ] 4.3.8 Add loading skeleton
- [ ] 4.3.9 Make responsive for mobile

**Acceptance Criteria:**
- Table displays all required columns
- Sorting works for all columns
- Virtual scrolling handles 200+ players smoothly
- Smart Score column highlighted
- Mobile responsive
- Empty states handled

**Files to Create:**
- `/frontend/src/components/smart-score/SmartScoreTable.tsx`

**Dependencies:**
- TanStack Table (@tanstack/react-table)
- TanStack Virtual (@tanstack/react-virtual)

---

#### Task 4.4: Create WeightAdjustmentPanel Component
**Status:** pending
**Type:** Frontend Component
**Effort:** L
**Priority:** High
**Dependencies:** Task 4.1

**Description:**
Create sidebar panel with 8 weight sliders, projection source selector, and action buttons.

**Subtasks:**
- [ ] 4.4.1 Create `/frontend/src/components/smart-score/WeightAdjustmentPanel.tsx`
- [ ] 4.4.2 Create WeightSlider component for individual weight
- [ ] 4.4.3 Add 8 sliders (W1-W8) with labels:
  - W1: Projection
  - W2: Ceiling Factor
  - W3: Ownership Penalty
  - W4: Value Score
  - W5: Trend Adjustment
  - W6: Regression Penalty
  - W7: Vegas Context
  - W8: Matchup Adjustment
- [ ] 4.4.4 Set slider min/max bounds (0.0 to 1.0)
- [ ] 4.4.5 Display current weight value next to each slider
- [ ] 4.4.6 Add ProjectionSourceSelector dropdown (ETR/LineStar)
- [ ] 4.4.7 Add "Apply" button (triggers recalculation)
- [ ] 4.4.8 Add "Reset" button (resets to default profile)
- [ ] 4.4.9 Add "Save Profile" button (opens save dialog)
- [ ] 4.4.10 Style panel with dark theme, orange accents
- [ ] 4.4.11 Make panel collapsible on mobile

**Acceptance Criteria:**
- All 8 sliders displayed and functional
- Weight values update on slider change
- Projection source selector works
- Buttons trigger correct actions
- Panel styled correctly
- Mobile responsive

**Files to Create:**
- `/frontend/src/components/smart-score/WeightAdjustmentPanel.tsx`
- `/frontend/src/components/smart-score/WeightSlider.tsx`

**Dependencies:**
- Material-UI Slider component or custom slider

---

#### Task 4.5: Create useWeightProfile Hook
**Status:** pending
**Type:** Frontend Hook
**Effort:** M
**Priority:** High
**Dependencies:** Task 3.2

**Description:**
Create React hook for managing weight profile state, loading, saving, and selection.

**Subtasks:**
- [ ] 4.5.1 Create `/frontend/src/hooks/useWeightProfile.ts`
- [ ] 4.5.2 Implement profile fetching with React Query
- [ ] 4.5.3 Implement profile selection state
- [ ] 4.5.4 Implement profile saving function
- [ ] 4.5.5 Implement profile loading function
- [ ] 4.5.6 Implement default profile loading
- [ ] 4.5.7 Manage current weights state
- [ ] 4.5.8 Handle loading and error states
- [ ] 4.5.9 Return profiles list, current profile, save/load functions

**Acceptance Criteria:**
- Profiles fetched correctly
- Profile selection works
- Saving creates new profile
- Loading applies profile weights
- Default profile loads on mount

**Files to Create:**
- `/frontend/src/hooks/useWeightProfile.ts`

**Implementation Details:**
- Use React Query for profile list
- Store current weights in local state
- Save/load functions update local state

---

### Group 5: Recalculation & Snapshot Workflow (User Interaction)

#### Task 5.1: Implement Recalculation Logic
**Status:** pending
**Type:** Frontend Logic
**Effort:** M
**Priority:** High
**Dependencies:** Task 4.2, Task 4.4, Task 4.5

**Description:**
Implement the Apply button workflow to trigger recalculation and store previous scores.

**Subtasks:**
- [ ] 5.1.1 Store previous Smart Scores before recalculation
- [ ] 5.1.2 Implement "Apply" button click handler
- [ ] 5.1.3 Show loading indicator during calculation
- [ ] 5.1.4 Call API to recalculate scores with new weights
- [ ] 5.1.5 Wait for calculation to complete (< 500ms target)
- [ ] 5.1.6 Store new scores
- [ ] 5.1.7 Calculate deltas (new - previous) for each player
- [ ] 5.1.8 Open SnapshotModal with changes
- [ ] 5.1.9 Handle errors during recalculation

**Acceptance Criteria:**
- Previous scores stored correctly
- Recalculation triggered on Apply click
- Loading indicator shows
- Calculation completes within 500ms
- Deltas calculated correctly
- Snapshot modal opens automatically

**Files to Modify:**
- `/frontend/src/hooks/useSmartScore.ts`
- `/frontend/src/components/smart-score/WeightAdjustmentPanel.tsx`

---

#### Task 5.2: Create SnapshotModal Component
**Status:** pending
**Type:** Frontend Component
**Effort:** M
**Priority:** High
**Dependencies:** Task 5.1

**Description:**
Create modal showing before/after scores with delta indicators and top 10 highlighting.

**Subtasks:**
- [ ] 5.2.1 Create `/frontend/src/components/smart-score/SnapshotModal.tsx`
- [ ] 5.2.2 Display player name, previous score, new score, delta
- [ ] 5.2.3 Highlight top 10 biggest changes (orange border/background)
- [ ] 5.2.4 Show all players whose score changed
- [ ] 5.2.5 Add "Keep Changes" button (applies changes, closes modal)
- [ ] 5.2.6 Add "Revert" button (restores previous scores, closes modal)
- [ ] 5.2.7 Style modal with dark theme
- [ ] 5.2.8 Make modal scrollable for many players
- [ ] 5.2.9 Add close button (X) in header
- [ ] 5.2.10 Make responsive for mobile (full-width)

**Acceptance Criteria:**
- Modal displays all changed players
- Top 10 highlighted correctly
- Keep Changes applies new scores
- Revert restores previous scores
- Modal closes after action
- Responsive on mobile

**Files to Create:**
- `/frontend/src/components/smart-score/SnapshotModal.tsx`
- `/frontend/src/components/smart-score/ScoreChangeRow.tsx`

---

#### Task 5.3: Create useScoreSnapshot Hook
**Status:** pending
**Type:** Frontend Hook
**Effort:** S
**Priority:** High
**Dependencies:** Task 5.1

**Description:**
Create hook for managing snapshot comparison logic (before/after scores, deltas).

**Subtasks:**
- [ ] 5.3.1 Create `/frontend/src/hooks/useScoreSnapshot.ts`
- [ ] 5.3.2 Implement snapshot storage (previous scores)
- [ ] 5.3.3 Implement delta calculation (new - previous)
- [ ] 5.3.4 Implement top 10 changes identification
- [ ] 5.3.5 Implement Keep Changes function (apply new scores)
- [ ] 5.3.6 Implement Revert function (restore previous scores)
- [ ] 5.3.7 Clear snapshot after Keep Changes (not persist)
- [ ] 5.3.8 Return snapshot data, keepChanges, revert functions

**Acceptance Criteria:**
- Snapshot stored before recalculation
- Deltas calculated correctly
- Top 10 identified correctly
- Keep Changes applies new scores
- Revert restores previous
- Snapshot cleared after Keep Changes

**Files to Create:**
- `/frontend/src/hooks/useScoreSnapshot.ts`

---

#### Task 5.4: Implement Delta Indicators in Table
**Status:** pending
**Type:** Frontend Component
**Effort:** S
**Priority:** Medium
**Dependencies:** Task 4.3, Task 5.1

**Description:**
Display delta indicators (+2.5, -1.3) next to Smart Scores in table after recalculation.

**Subtasks:**
- [ ] 5.4.1 Create ScoreDeltaIndicator component
- [ ] 5.4.2 Display format: `45.2 (+2.5)` or `38.7 (-1.3)`
- [ ] 5.4.3 Color positive deltas green (subtle: rgba(76, 175, 80, 0.3))
- [ ] 5.4.4 Color negative deltas red (subtle: rgba(244, 67, 54, 0.3))
- [ ] 5.4.5 Show indicators only after recalculation (not on initial load)
- [ ] 5.4.6 Clear indicators on revert or next recalculation
- [ ] 5.4.7 Add sort option: "Sort by Score Change"
- [ ] 5.4.8 Integrate into SmartScoreTable component

**Acceptance Criteria:**
- Delta indicators display correctly
- Colors applied appropriately
- Indicators persist until next recalculation
- Sort by change works
- Indicators cleared on revert

**Files to Create:**
- `/frontend/src/components/smart-score/ScoreDeltaIndicator.tsx`

**Files to Modify:**
- `/frontend/src/components/smart-score/SmartScoreTable.tsx`

---

### Group 6: Data Integration & Missing Data Handling (Backend Integration)

#### Task 6.1: Integrate ETR Projection Source
**Status:** pending
**Type:** Backend Integration
**Effort:** M
**Priority:** High
**Dependencies:** Task 2.1

**Description:**
Ensure ETR projections can be used in Smart Score calculation (assume same format as DraftKings).

**Subtasks:**
- [ ] 6.1.1 Verify ETR data import format matches DraftKings
- [ ] 6.1.2 Update import logic to handle ETR as projection source
- [ ] 6.1.3 Store projection_source in player_pools table
- [ ] 6.1.4 Update SmartScoreService to select projection by source
- [ ] 6.1.5 Default to ETR if available, else LineStar
- [ ] 6.1.6 Handle missing ETR data gracefully
- [ ] 6.1.7 Test with sample ETR data

**Acceptance Criteria:**
- ETR projections used when available
- Source selection works correctly
- Fallback to LineStar works
- Missing data handled gracefully

**Files to Modify:**
- `/backend/services/smart_score_service.py`
- `/backend/services/data_import_service.py` (if exists)

---

#### Task 6.2: Ensure Vegas Lines Table Population
**Status:** pending
**Type:** Backend Integration
**Effort:** M
**Priority:** High
**Dependencies:** Task 2.4

**Description:**
Ensure vegas_lines table is populated with ITT data (MVP requirement, not Phase 2).

**Subtasks:**
- [ ] 6.2.1 Verify vegas_lines table exists and has ITT column
- [ ] 6.2.2 Create/update import script for vegas_lines data
- [ ] 6.2.3 Ensure ITT (implied_team_total) is imported
- [ ] 6.2.4 Test ITT lookup in SmartScoreService
- [ ] 6.2.5 Handle missing ITT data with defaults
- [ ] 6.2.6 Document vegas_lines import process

**Acceptance Criteria:**
- vegas_lines table populated
- ITT data available for calculation
- Missing data handled with defaults
- Import process documented

**Files to Modify:**
- `/backend/services/smart_score_service.py`
- `/backend/scripts/import_vegas_lines.py` (create if needed)

---

#### Task 6.3: Implement Opponent Rank Import and Categorization
**Status:** pending
**Type:** Backend Integration
**Effort:** S
**Priority:** Medium
**Dependencies:** Task 2.6

**Description:**
Import OppRank from LineStar and categorize during import or calculation.

**Subtasks:**
- [ ] 6.3.1 Import OppRank from LineStar during player import
- [ ] 6.3.2 Categorize during import: Rank 1-5 = "top_5", Rank 28-32 = "bottom_5", else "middle"
- [ ] 6.3.3 Store category in player_pools.opponent_rank_category
- [ ] 6.3.4 Handle missing OppRank: Store as "middle"
- [ ] 6.3.5 Test categorization logic

**Acceptance Criteria:**
- OppRank imported correctly
- Categorization works correctly
- Category stored in database
- Missing data defaults to "middle"

**Files to Modify:**
- `/backend/services/data_import_service.py` (if exists)
- `/backend/services/smart_score_service.py`

---

#### Task 6.4: Calculate and Store 20+ Snap Games Count
**Status:** pending
**Type:** Backend Service
**Effort:** S
**Priority:** Medium
**Dependencies:** Task 2.3

**Description:**
Calculate count of games with 20+ snaps for each player and store in player_pools.

**Subtasks:**
- [ ] 6.4.1 Query historical_stats for games with snaps >= 20 per player
- [ ] 6.4.2 Count total games with 20+ snaps
- [ ] 6.4.3 Store count in player_pools.games_with_20_plus_snaps
- [ ] 6.4.4 Update count during Smart Score calculation
- [ ] 6.4.5 Display count in frontend table

**Acceptance Criteria:**
- Count calculated correctly
- Stored in database
- Displayed in table
- Updates during calculation

**Files to Modify:**
- `/backend/services/smart_score_service.py`
- `/frontend/src/components/smart-score/SmartScoreTable.tsx`

---

### Group 7: Visual Indicators & UI Polish (User Experience)

#### Task 7.1: Create RegressionRiskBadge Component
**Status:** pending
**Type:** Frontend Component
**Effort:** S
**Priority:** Medium
**Dependencies:** Task 2.5, Task 4.3

**Description:**
Create badge component to display regression risk indicator for WR players.

**Subtasks:**
- [ ] 7.1.1 Create `/frontend/src/components/smart-score/RegressionRiskBadge.tsx`
- [ ] 7.1.2 Display badge only for WR position
- [ ] 7.1.3 Show badge when regression_risk = true
- [ ] 7.1.4 Style badge with orange/red color (#ff5722)
- [ ] 7.1.5 Add tooltip: "Regression Risk: Scored 20+ points last week"
- [ ] 7.1.6 Show "Historical data unavailable" if no data
- [ ] 7.1.7 Integrate into SmartScoreTable component

**Acceptance Criteria:**
- Badge displays for WR only
- Badge shows when risk detected
- Tooltip explains risk
- Missing data message shown
- Styled correctly

**Files to Create:**
- `/frontend/src/components/smart-score/RegressionRiskBadge.tsx`

**Files to Modify:**
- `/frontend/src/components/smart-score/SmartScoreTable.tsx`

---

#### Task 7.2: Create ProfileSelector Component
**Status:** pending
**Type:** Frontend Component
**Effort:** M
**Priority:** Medium
**Dependencies:** Task 4.5

**Description:**
Create dropdown component for selecting and saving weight profiles.

**Subtasks:**
- [ ] 7.2.1 Create `/frontend/src/components/smart-score/ProfileSelector.tsx`
- [ ] 7.2.2 Display dropdown with list of profiles
- [ ] 7.2.3 Show selected profile name
- [ ] 7.2.4 Allow selecting profile (loads weights)
- [ ] 7.2.5 Add "Save Profile" button/action
- [ ] 7.2.6 Open dialog to enter profile name
- [ ] 7.2.7 Validate unique name
- [ ] 7.2.8 Handle save success/error
- [ ] 7.2.9 Style with dark theme

**Acceptance Criteria:**
- Dropdown shows all profiles
- Selection loads weights
- Save creates new profile
- Name validation works
- Success/error handling works

**Files to Create:**
- `/frontend/src/components/smart-score/ProfileSelector.tsx`

**Files to Modify:**
- `/frontend/src/components/smart-score/WeightAdjustmentPanel.tsx`

---

#### Task 7.3: Style Smart Score Column Highlight
**Status:** pending
**Type:** Frontend Styling
**Effort:** S
**Priority:** Low
**Dependencies:** Task 4.3

**Description:**
Apply visual highlighting to Smart Score column in table.

**Subtasks:**
- [ ] 7.3.1 Apply highlighted background color to Smart Score column
- [ ] 7.3.2 Use orange accent color (#ff8c42) with subtle opacity
- [ ] 7.3.3 Make column header bold
- [ ] 7.3.4 Ensure text remains readable
- [ ] 7.3.5 Test contrast ratios for accessibility

**Acceptance Criteria:**
- Column visually highlighted
- Text remains readable
- Accessible contrast ratios
- Consistent with design system

**Files to Modify:**
- `/frontend/src/components/smart-score/SmartScoreTable.tsx`

---

#### Task 7.4: Add Missing Data Indicators
**Status:** pending
**Type:** Frontend Component
**Effort:** S
**Priority:** Low
**Dependencies:** Task 2.2

**Description:**
Add visual indicators (tooltips/badges) when default values are used for missing data.

**Subtasks:**
- [ ] 7.4.1 Add indicator badge/tooltip for missing projection
- [ ] 7.4.2 Add indicator for estimated ceiling/floor
- [ ] 7.4.3 Add indicator for league average ownership
- [ ] 7.4.4 Add indicator for league average ITT
- [ ] 7.4.5 Add indicator for neutral trend (insufficient data)
- [ ] 7.4.6 Style indicators subtly (not intrusive)
- [ ] 7.4.7 Tooltip explains what default was used

**Acceptance Criteria:**
- Indicators show when defaults used
- Tooltips explain defaults
- Not intrusive to user experience
- Accessible (keyboard navigation)

**Files to Modify:**
- `/frontend/src/components/smart-score/SmartScoreTable.tsx`

---

### Group 8: Testing & Quality Assurance (Validation)

#### Task 8.1: Write Unit Tests for SmartScoreService
**Status:** pending
**Type:** Testing
**Effort:** L
**Priority:** High
**Dependencies:** Task 2.1 through Task 2.6

**Description:**
Write comprehensive unit tests for all Smart Score calculation methods.

**Subtasks:**
- [ ] 8.1.1 Test W1: Projection Factor calculation
- [ ] 8.1.2 Test W2: Ceiling Factor calculation (with missing data)
- [ ] 8.1.3 Test W3: Ownership Penalty calculation
- [ ] 8.1.4 Test W4: Value Score calculation
- [ ] 8.1.5 Test W5: Trend Adjustment (all position types)
- [ ] 8.1.6 Test W6: Regression Risk detection (WR only)
- [ ] 8.1.7 Test W7: Vegas Context calculation
- [ ] 8.1.8 Test W8: Matchup Adjustment calculation
- [ ] 8.1.9 Test complete formula calculation
- [ ] 8.1.10 Test missing data handling for all factors
- [ ] 8.1.11 Test edge cases (zero values, negative values)
- [ ] 8.1.12 Achieve > 80% code coverage

**Acceptance Criteria:**
- All factors tested
- Missing data scenarios tested
- Edge cases covered
- > 80% code coverage
- Tests pass consistently

**Files to Create:**
- `/tests/unit/test_smart_score_service.py`

---

#### Task 8.2: Write Unit Tests for WeightProfileService
**Status:** pending
**Type:** Testing
**Effort:** M
**Priority:** High
**Dependencies:** Task 3.1

**Description:**
Write unit tests for weight profile CRUD operations.

**Subtasks:**
- [ ] 8.2.1 Test create_profile
- [ ] 8.2.2 Test get_profile
- [ ] 8.2.3 Test list_profiles
- [ ] 8.2.4 Test update_profile
- [ ] 8.2.5 Test delete_profile
- [ ] 8.2.6 Test get_default_profile
- [ ] 8.2.7 Test unique name validation
- [ ] 8.2.8 Test prevent deletion of default profile
- [ ] 8.2.9 Test error handling

**Acceptance Criteria:**
- All CRUD operations tested
- Validation tested
- Error cases tested
- Tests pass consistently

**Files to Create:**
- `/tests/unit/test_weight_profile_service.py`

---

#### Task 8.3: Write Unit Tests for Frontend Components
**Status:** pending
**Type:** Testing
**Effort:** M
**Priority:** Medium
**Dependencies:** Task 4.3, Task 4.4, Task 5.2

**Description:**
Write unit tests for key frontend components using React Testing Library.

**Subtasks:**
- [ ] 8.3.1 Test SmartScoreTable rendering and sorting
- [ ] 8.3.2 Test WeightAdjustmentPanel slider updates
- [ ] 8.3.3 Test SnapshotModal display and actions
- [ ] 8.3.4 Test ScoreDeltaIndicator display
- [ ] 8.3.5 Test RegressionRiskBadge display
- [ ] 8.3.6 Test ProfileSelector dropdown

**Acceptance Criteria:**
- Components render correctly
- User interactions tested
- State updates tested
- Tests pass consistently

**Files to Create:**
- `/tests/components/SmartScoreTable.test.tsx`
- `/tests/components/WeightAdjustmentPanel.test.tsx`
- `/tests/components/SnapshotModal.test.tsx`

---

#### Task 8.4: Write Integration Tests
**Status:** pending
**Type:** Testing
**Effort:** M
**Priority:** High
**Dependencies:** Task 3.2, Task 8.1, Task 8.2

**Description:**
Write integration tests for Smart Score calculation workflow with real database.

**Subtasks:**
- [ ] 8.4.1 Test full calculation workflow (API → Service → Database)
- [ ] 8.4.2 Test weight profile CRUD workflow
- [ ] 8.4.3 Test missing data handling with real database
- [ ] 8.4.4 Test Vegas context calculation with ITT data
- [ ] 8.4.5 Test trend calculation with historical_stats
- [ ] 8.4.6 Test recalculation with different weights

**Acceptance Criteria:**
- Full workflows tested
- Database interactions work correctly
- Missing data handled correctly
- Tests pass consistently

**Files to Create:**
- `/tests/integration/test_smart_score_workflow.py`

---

#### Task 8.5: Write E2E Tests
**Status:** pending
**Type:** Testing
**Effort:** M
**Priority:** Medium
**Dependencies:** All frontend tasks

**Description:**
Write end-to-end tests for Smart Score Engine user workflows.

**Subtasks:**
- [ ] 8.5.1 Test navigate to Smart Score page
- [ ] 8.5.2 Test view Smart Score table
- [ ] 8.5.3 Test adjust weight sliders
- [ ] 8.5.4 Test click Apply button
- [ ] 8.5.5 Test view snapshot modal
- [ ] 8.5.6 Test Keep Changes action
- [ ] 8.5.7 Test Revert action
- [ ] 8.5.8 Test save weight profile
- [ ] 8.5.9 Test load weight profile
- [ ] 8.5.10 Test sort by Smart Score
- [ ] 8.5.11 Test sort by score change

**Acceptance Criteria:**
- All user workflows tested
- Tests pass consistently
- No flaky tests
- Tests run in CI/CD

**Files to Create:**
- `/tests/e2e/smart-score.spec.ts`

---

### Group 9: Performance & Optimization (Polish)

#### Task 9.1: Optimize Calculation Performance
**Status:** pending
**Type:** Performance
**Effort:** M
**Priority:** Medium
**Dependencies:** Task 2.1

**Description:**
Optimize Smart Score calculation to meet < 500ms target for 200 players.

**Subtasks:**
- [ ] 9.1.1 Profile calculation performance
- [ ] 9.1.2 Optimize database queries (batch lookups)
- [ ] 9.1.3 Cache league averages per week
- [ ] 9.1.4 Optimize historical_stats queries
- [ ] 9.1.5 Parallelize factor calculations if possible
- [ ] 9.1.6 Reduce database round trips
- [ ] 9.1.7 Verify < 500ms target met

**Acceptance Criteria:**
- Calculation completes < 500ms for 200 players
- Database queries optimized
- Caching reduces redundant queries
- Performance targets met

**Files to Modify:**
- `/backend/services/smart_score_service.py`

---

#### Task 9.2: Optimize Frontend Virtual Scrolling
**Status:** pending
**Type:** Performance
**Effort:** S
**Priority:** Medium
**Dependencies:** Task 4.3

**Description:**
Ensure virtual scrolling performs smoothly with 200+ players.

**Subtasks:**
- [ ] 9.2.1 Verify virtual scrolling implementation
- [ ] 9.2.2 Test scroll performance (60fps target)
- [ ] 9.2.3 Optimize row rendering (memoization)
- [ ] 9.2.4 Test with 200+ players
- [ ] 9.2.5 Fix any performance issues

**Acceptance Criteria:**
- Virtual scrolling smooth (60fps)
- Handles 200+ players without lag
- Memoization reduces re-renders
- Performance targets met

**Files to Modify:**
- `/frontend/src/components/smart-score/SmartScoreTable.tsx`

---

#### Task 9.3: Implement Calculation Result Caching
**Status:** pending
**Type:** Performance
**Effort:** S
**Priority:** Low
**Dependencies:** Task 2.1

**Description:**
Cache calculation results per week/weight profile combination to avoid redundant calculations.

**Subtasks:**
- [ ] 9.3.1 Implement cache key: `(week_id, weight_profile_id)`
- [ ] 9.3.2 Cache calculation results in memory (or Redis if available)
- [ ] 9.3.3 Invalidate cache on weight profile changes
- [ ] 9.3.4 Set cache TTL (e.g., 5 minutes)
- [ ] 9.3.5 Test cache hit/miss scenarios

**Acceptance Criteria:**
- Cache reduces redundant calculations
- Cache invalidation works correctly
- Cache TTL enforced
- Performance improved

**Files to Modify:**
- `/backend/services/smart_score_service.py`

---

## Summary

**Total Tasks:** 47 tasks across 9 groups
**Estimated Effort:** ~145 hours (3.6 weeks for 1 developer)

**Priority Breakdown:**
- **High Priority:** 30 tasks (Database, Core Logic, API, Frontend Foundation)
- **Medium Priority:** 14 tasks (UI Polish, Testing, Integration)
- **Low Priority:** 3 tasks (Styling, Caching)

**Dependencies:**
- Group 1 (Database) → Groups 2-3 (Backend)
- Groups 2-3 (Backend) → Group 4 (Frontend)
- Group 4 (Frontend) → Group 5 (Workflow)
- Groups 2-6 (Backend/Frontend) → Group 8 (Testing)

**Recommended Implementation Order:**
1. Complete Group 1 (Database migrations)
2. Complete Group 2 (Core calculation logic)
3. Complete Group 3 (Backend API)
4. Complete Group 4 (Frontend foundation)
5. Complete Group 5 (Workflow)
6. Complete Group 6 (Data integration)
7. Complete Group 7 (UI polish)
8. Complete Group 8 (Testing)
9. Complete Group 9 (Performance)

