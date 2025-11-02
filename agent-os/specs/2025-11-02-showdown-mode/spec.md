# Specification: Showdown Mode (DraftKings Single-Game Slates)

## Goal
Add support for DraftKings Showdown contests (single-game slates) while preserving the existing main slate workflow entirely. Users can switch between modes at any time and import/manage data for both contest types independently.

## User Stories
- As a DFS player, I want to switch between Main Slate and Showdown modes so that I can build lineups for different contest types
- As a DFS player, I want to import Linestar Showdown files for single-game slates so that I can leverage the same data sources
- As a DFS player, I want to use the Smart Score Engine with Showdown players so that I can evaluate single-game opportunities
- As a DFS player, I want to generate Showdown lineups with Captain + 5 FLEX positions so that I can optimize for single-game contests
- As a DFS player, I want the system to automatically select the best captain based on value so that I can maximize my lineup potential

## Core Requirements

### Mode Selector
- Add toggle control in HomePage header: "Main Slate" / "Showdown"
- Display mode selector alongside Week Selector (two independent controls)
- Persist selected mode across all pages during user session
- Default mode: Main Slate
- Mode selector remains visible in header across all pages

### Data Model
- Store both Main Slate and Showdown data per week using same week IDs
- Week ID (e.g., Week 17) + Mode determines which dataset loads
- Import same Linestar file format for both modes (no file changes needed)
- Support 40-60 player pool (both teams) including Position = "K"
- No captain indicator in file - system determines captain during lineup generation

### File Import
- Reuse existing ImportDataButton component
- Import flow: User selects Mode -> Selects Week -> Clicks "Import Linestar"
- System populates correct data table based on selected mode
- File format identical to main slate (Linestar columns)
- Store mode flag with imported players to separate datasets

### Smart Score Engine
- No changes to 8 scoring factors or weight profiles
- Applies identically to showdown players
- All historical stats and regression analysis work same as main slate
- Save/load weight profiles works identically

### Player Selection
- Reuse PlayerSelectionPage component entirely
- Load showdown player pool when mode = Showdown
- Display all players from single game (both teams)
- No UI changes needed

### Lineup Generator
- Adapt roster construction to Showdown format: 1 CPT + 5 FLEX
- Salary cap: $50,000
- Captain rules:
  - Captain salary = Base salary × 1.5
  - Captain points = Base points × 1.5
  - Auto-select best captain by (Smart Score × 1.5) / (Salary × 1.5) value
- Allow manual captain lock (user can force specific player as captain)
- Generate multiple variations with different captains for diversity
- Keep ALL existing constraints (max ownership, stacking, etc.) - user adjusts manually

### Contest Structure
- Roster: 1 Captain + 5 FLEX = 6 total positions
- Salary Cap: $50,000
- Captain multiplier: 1.5x salary and points
- Eligible positions: QB, RB, WR, TE, K, DST
- Any player eligible as captain

### Export
- No changes - user reads from screen and manually creates DK lineups

## Visual Design

### Mode Selector UI
- Location: HomePage header, next to Week Selector
- Style: Toggle button group matching existing design system
- States: "Main Slate" (active) | "Showdown" (inactive)
- Responsive: Collapses gracefully on mobile
- Visual indicator: Orange accent (#ff6b35) for active mode

### Lineup Display Adaptations
- Show 6 positions instead of 9
- Highlight Captain row with special styling (larger font, captain badge)
- Display captain multiplier (1.5x) next to salary/points
- Maintain dark theme with orange accents

## Reusable Components

### Existing Code to Leverage
**Frontend Components:**
- `ImportDataButton.tsx` - File import with dropdown menu
- `WeekNavigation.tsx` - Week selector (works identically)
- `SmartScorePage.tsx` - Smart Score Engine (no changes)
- `PlayerSelectionPage.tsx` - Player selection (no changes)
- `LineupConfigurationPanel.tsx` - Settings panel (reuse as-is)
- `LineupDisplay.tsx` - Lineup visualization (adapt for 6 positions)
- `LineupGenerationProgress.tsx` - Progress indicator

**Backend Services:**
- `lineup_optimizer_service.py` - Core PuLP optimizer (adapt constraints)
- `player_management_service.py` - Player data handling (add mode filter)
- `week_management_service.py` - Week data (no changes)
- Smart Score calculation (no changes)

**Data Models:**
- `PlayerResponse` schema - Add optional `contest_mode` field
- `LineupPlayer` schema - Add `is_captain: boolean` field
- `OptimizationSettings` schema - No changes needed

### New Components Required

**Frontend:**
- `ModeSelector.tsx` - Toggle between Main Slate and Showdown
  - Cannot reuse WeekSelector (different purpose and data)
  - New component for mode toggle UI
  - Integrates with new `useModeStore` for global mode state

**Backend:**
- Showdown roster construction logic in lineup optimizer
  - Cannot reuse main slate position logic (different roster structure)
  - New constraint set for 1 CPT + 5 FLEX
  - Captain selection algorithm

**Database:**
- Add `contest_mode` column to player pool tables
  - Required to separate Main Slate vs Showdown data for same week
  - Index on (week_id, contest_mode) for fast filtering

## Technical Approach

### Frontend State Management

**Mode State (New):**
```typescript
// New Zustand store: src/store/modeStore.ts
interface ModeStore {
  mode: 'main' | 'showdown';  // Contest mode
  setMode: (mode: 'main' | 'showdown') => void;
}
```

**Integration Points:**
- Mode selector sets global mode state
- Week selector unchanged (works for both modes)
- Data fetching hooks (useWeeks, usePlayers, useLineups) include mode parameter
- Smart Score Engine reads mode from store, no UI changes

### Backend Data Separation

**Player Pool Storage:**
- Add `contest_mode` column to player data tables
- Filter queries by `(week_id, contest_mode)` tuple
- Same week ID used for both modes (e.g., Week 17 can have Main + Showdown data)

**API Endpoint Updates:**
- `GET /api/players?week_id=X&mode=showdown` - Filter by mode
- `POST /api/import/linestar` - Accept mode parameter, store with players
- `POST /api/lineups/generate` - Accept mode in request, apply appropriate constraints

### Captain Selection Algorithm

**Auto-Selection Logic:**
```python
# For each viable player:
captain_value = (smart_score * 1.5) / (salary * 1.5)
# Select player with highest captain_value that fits under salary cap
```

**Manual Lock:**
- User can force specific player as captain via UI
- Lock persists across lineup generation variations
- System respects lock and optimizes remaining 5 FLEX positions

**Diversity Strategy:**
- Generate lineups with different captains (top 5 captain values)
- Ensures unique lineup constructions
- User gets variety in showdown approaches

### Lineup Optimizer Adaptations

**Position Constraints (Showdown):**
```python
SHOWDOWN_POSITION_REQUIREMENTS = {
    'CPT': 1,      # Captain (any position)
    'FLEX': 5,     # FLEX (QB/RB/WR/TE/K/DST)
}
SHOWDOWN_SALARY_CAP = 50000
```

**Captain Constraints:**
- Exactly 1 player marked as captain
- Captain salary = base_salary * 1.5
- Captain points = base_points * 1.5
- No position restrictions (QB, RB, WR, TE, K, DST all eligible)

**Existing Constraints (Preserved):**
- Max ownership limit (user-adjustable)
- Smart Score percentile filtering (user-adjustable)
- Max players per team (not applicable to single-game, user ignores)
- QB + WR stacking (not applicable to single-game, user disables)
- Elite appearance constraints (adapt to 6-position roster if used)

### Database Schema Changes

**Player Pool Table:**
```sql
ALTER TABLE player_pool
ADD COLUMN contest_mode VARCHAR(20) DEFAULT 'main' NOT NULL;

CREATE INDEX idx_player_pool_week_mode
ON player_pool(week_id, contest_mode);
```

**Lineup Storage:**
```sql
ALTER TABLE saved_lineups
ADD COLUMN contest_mode VARCHAR(20) DEFAULT 'main' NOT NULL;

-- Update LineupPlayer JSON to include is_captain flag
-- Example: {"position": "QB", "is_captain": true, ...}
```

## Edge Cases and Validation

### Week + Mode Combinations
- **Scenario:** User imports Main Slate for Week 17, then switches to Showdown
  - **Behavior:** Showdown shows "No data" until user imports Showdown file
  - **Validation:** Each mode maintains independent dataset

- **Scenario:** User switches mode mid-workflow (after selecting players)
  - **Behavior:** Clear player selection, reload appropriate data for new mode
  - **Validation:** Prevent mixing Main Slate and Showdown players in same lineup

### Import Overwrite
- **Scenario:** Import Monday Night showdown after Sunday showdown
  - **Behavior:** Overwrites previous showdown data for that week
  - **Validation:** Show confirmation dialog: "This will replace existing Showdown data for Week X"
  - **Acceptable:** Single-game-at-a-time design (per requirements)

### Captain Selection
- **Scenario:** No valid captain found under salary cap
  - **Behavior:** Return error: "Cannot fit any captain + 5 FLEX under $50k cap"
  - **Validation:** Pre-check captain viability before optimization

- **Scenario:** User locks high-salary captain, no valid FLEX combinations
  - **Behavior:** Return error: "Captain lock prevents valid lineup construction"
  - **Validation:** Check remaining salary can support 5 FLEX players

### Kicker Support
- **Scenario:** File includes Position = "K"
  - **Behavior:** Treat as FLEX-eligible (same as QB/RB/WR/TE/DST)
  - **Validation:** No special handling needed beyond position recognition

### Smart Score Edge Cases
- **Scenario:** Single-game slate has limited opponent data
  - **Behavior:** Matchup Adjustment factor may have limited context, but still applies
  - **Validation:** Smart Score Engine works identically, accepts limited data

- **Scenario:** Regression Penalty on showdown players
  - **Behavior:** Applies normally using week-over-week history (same players as main slate)
  - **Validation:** Historical stats fully available for showdown players

## Success Criteria

### Functional Requirements
- User can toggle between Main Slate and Showdown modes from any page
- Import Linestar file successfully populates correct dataset based on selected mode
- Smart Score Engine calculates scores identically for both modes
- Lineup generator produces valid 1 CPT + 5 FLEX lineups under $50k cap
- Captain automatically selected by optimal value, with manual lock option
- Generated lineups display captain with 1.5x multiplier clearly indicated

### Performance Metrics
- Lineup generation completes within 30 seconds for 10 showdown lineups
- Mode switching updates UI within 500ms
- Import process handles 40-60 player files same speed as main slate (< 5 seconds)

### User Experience Goals
- No changes to existing main slate workflow (complete preservation)
- Minimal learning curve - mode selector intuitive and visible
- Captain selection transparent (user understands auto-selection logic)
- Lineup display clearly differentiates captain vs FLEX

## Out of Scope

### Not in Initial Release
- DraftKings file import (only Linestar supported)
- Custom showdown-specific constraint defaults
- Multi-game showdown support (single game at a time only)
- Automated lineup export to DraftKings format
- Player filtering changes or enhancements
- Smart Score factor modifications for showdown
- Special handling for defenses/kickers beyond FLEX eligibility
- Showdown-specific analytics or visualizations
- Historical showdown lineup tracking
- Captain correlation analysis

### Future Enhancements
- Multi-game showdown slate support (different week IDs per game)
- Showdown-specific strategy modes (e.g., "Leverage Captain", "Balanced FLEX")
- Captain correlation recommendations (e.g., "If Captain = QB, suggest bring-back")
- Export to DraftKings CSV format
- Historical showdown performance tracking
- Captain usage analytics across lineups

## Testing Considerations

### Unit Tests
- Mode selector state management (set/get mode correctly)
- Captain selection algorithm (correct value calculation)
- Showdown constraint validation (1 CPT + 5 FLEX enforced)
- Salary cap with captain multiplier (total <= $50k)
- Contest mode filtering in data queries

### Integration Tests
- Import Linestar file in Showdown mode -> verify mode flag stored
- Switch mode mid-session -> verify data reloads correctly
- Generate showdown lineup -> verify captain multiplier applied
- Save showdown lineup -> verify contest_mode persists

### End-to-End Tests
- Full user flow: Select Showdown -> Import file -> Smart Score -> Select Players -> Generate Lineups
- Mode independence: Verify Main Slate data unaffected by Showdown import
- Captain variations: Verify multiple lineups use different captains

### Manual Testing Scenarios
- Import sample showdown file (SEA @ WAS) from `/planning/visuals/linestar-showdown-sample.csv`
- Verify 54 players load correctly with kickers included
- Generate 10 lineups, confirm captain diversity
- Switch back to Main Slate, verify no data crossover
- Test with locked captain, verify FLEX optimization respects lock

### Performance Tests
- Lineup generation time for 10 showdown lineups (target: < 30 seconds)
- Mode switching responsiveness (target: < 500ms)
- Large player pool handling (60 players, both teams)

---

## Implementation Notes

### Phase 1: Data Model & Import
1. Add `contest_mode` column to database
2. Update import service to accept and store mode
3. Update data fetching to filter by mode

### Phase 2: Mode Selector UI
1. Create ModeSelector component
2. Add to HomePage header
3. Create useModeStore for global state
4. Integrate with existing components

### Phase 3: Lineup Generator
1. Adapt lineup optimizer for showdown constraints
2. Implement captain selection algorithm
3. Update LineupDisplay for 6-position format
4. Add captain multiplier display

### Phase 4: Testing & Polish
1. Test all edge cases
2. Verify main slate workflow unaffected
3. Performance optimization
4. Documentation updates

### Key Design Decisions
- **Single dataset per mode per week:** Simplifies data model, acceptable tradeoff for v1
- **No automatic constraint adjustment:** User manually adjusts settings, preserves flexibility
- **Auto-captain selection:** Optimizes for value, user can override if desired
- **Component reuse priority:** Minimize code changes, leverage existing Smart Score Engine entirely
