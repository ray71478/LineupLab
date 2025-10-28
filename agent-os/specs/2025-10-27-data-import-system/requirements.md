# Data Import System - Requirements

**Last Updated:** October 27, 2025  
**Status:** Ready for Specification

## Finalized Requirements

### 1. Upload Button & Flow

**UI Location:**
- "Import Data" button in main navigation/header (always accessible)
- Button opens a menu/dropdown with 3 options:
  1. Import LineStar Data
  2. Import DraftKings Data
  3. Import Season Stats

**Week Selection:**
- Week selector dropdown in main navigation/header (always visible)
- User selects week BEFORE clicking "Import Data"
- Selected week is locked in for all subsequent operations
- Week context persists across all pages

**Import Flow:**
1. User selects week from header dropdown (e.g., Week 8)
2. User clicks "Import Data" button
3. Menu appears with 3 file type options
4. User selects file type
5. File picker opens (accept=".xlsx")
6. User selects file
7. Import begins immediately (no preview)
8. Spinner shows during processing
9. Success toast: "153 players imported successfully"
10. Error toast (if failure): Detailed error message

### 2. LineStar Import

**File Pattern:** `LineStar_Football_WK{X}.xlsx`

**Sheet Selection:** First sheet (index 0) - name varies

**Column Mapping:**
- `Name` → `name` (store as-is)
- `Position` → `position`
- `Team` → `team`
- `Salary` → `salary` (integer)
- `Projected` → `projection` (float)
- `Ceiling` → `ceiling` (float)
- `Floor` → `floor` (float)
- `ProjOwn` → `ownership` (float, auto-detect format: if >1, divide by 100)

**Processing:**
1. Read first sheet
2. Validate required columns exist
3. Validate data types
4. Generate `player_key` for each player (see normalization rules below)
5. Set `source` = "LineStar"
6. Set `week_id` = currently selected week
7. **Overwrite behavior:** Delete all existing players for this week with source="LineStar"
8. Bulk insert into `player_pools` table
9. Return success message: "{count} players imported successfully"

**Error Handling:**
- Missing required columns → "Import failed: Missing required column '{column_name}'"
- Invalid data type → "Import failed: Column '{column_name}' contains non-numeric values"
- Empty file → "Import failed: File contains no player data"
- Wrong format → "Import failed: File must be .xlsx format"

### 3. DraftKings Import

**File Pattern:** `DKSalaries Week {X}.xlsx`

**Sheet Selection:** FE sheet only (no user prompt needed)

**Header Row:** Row 2 (skip row 1, which contains numeric values)

**Column Mapping (FE sheet):**
- `Name` → `name` (store as-is)
- `Pos` → `position`
- `T` → `team`
- `S` → `salary` (integer)
- `Proj` → `projection` (float)
- `Ceil` → `ceiling` (float)
- `Flr` → `floor` (float)
- `Own` → `ownership` (float, already in 0-1 format)
- `Notes` → `notes` (text, optional)

**ITT Sheet Handling:**
- **Decision:** Skip ITT import for MVP
- Rationale: Will implement proper Vegas line tracking in Phase 2 with hourly API calls and movement tracking
- LineStar already provides Vegas data for MVP needs

**Processing:**
1. Read FE sheet (skip row 1, use row 2 as header)
2. Validate required columns exist
3. Validate data types
4. Generate `player_key` for each player
5. Set `source` = "DraftKings"
6. Set `week_id` = currently selected week
7. **Overwrite behavior:** Delete ALL existing players for this week (regardless of source)
8. Bulk insert into `player_pools` table
9. Return success message: "{count} players imported successfully"

**Error Handling:** Same as LineStar

### 4. Comprehensive Stats Import

**File Pattern:** `ComprehensiveStats_throughWeek{X}.xlsx`

**Sheet Selection:** "Points" sheet

**Column Mapping:**
- `Player` → `player_name` (store as-is)
- `Tm` → `team`
- `Pos` → `position`
- `Wk` → `week` (integer)
- `Opp` → `opponent`
- `Snaps` → `snaps` (integer)
- `Snp %` → `snap_pct` (float, 0-1 format)
- `Ratt` → `rush_attempts` (integer)
- `Rsh_yds` → `rush_yards` (integer)
- `Rsh_td` → `rush_tds` (integer)
- `CTGT` → `targets` (integer)
- `CTGT%` → `target_share` (float, 0-1 format)
- `Rec` → `receptions` (integer)
- `Rc_yds` → `rec_yards` (integer)
- `Rc_td` → `rec_tds` (integer)
- `Tot TD` → `total_tds` (integer)
- `Touch` → `touches` (integer)
- `DK Pts` → `actual_points` (float)
- `Sal` → `salary` (integer)

**Processing:**
1. Read "Points" sheet
2. Validate required columns exist
3. Validate data types
4. Generate `player_key` for each player-week record
5. **Automated Backup:** Create backup table `historical_stats_backup` (copy current data)
6. **Full Replace:** Delete ALL existing records from `historical_stats` table
7. Bulk insert all records (all weeks) into `historical_stats` table
8. Return success message: "{count} records imported successfully"

**Backup Strategy:**
- Before delete, copy all data to `historical_stats_backup` table
- Keep only 1 previous version (overwrite old backup)
- Backup table has identical schema to `historical_stats`

**Error Handling:** Same as LineStar

### 5. Player Name Normalization

**Composite Key Format:** `{normalized_name}_{team}_{position}`

**Example:** "D'Andre Swift Jr." (PHI, RB) → `dandre_swift_PHI_RB`

**Normalization Rules:**
1. Remove suffixes: "Jr.", "Sr.", "III", "II", "IV"
2. Remove prefixes: "D'", "O'"
3. Remove all punctuation: apostrophes, periods, hyphens, commas
4. Convert to lowercase
5. Replace spaces with underscores
6. Combine: `{name}_{team}_{position}`

**Examples:**
- "Christian McCaffrey" (SF, RB) → `christian_mccaffrey_SF_RB`
- "A.J. Brown" (PHI, WR) → `aj_brown_PHI_WR`
- "D'Andre Swift Jr." (PHI, RB) → `dandre_swift_PHI_RB`
- "Odell Beckham Jr." (MIA, WR) → `odell_beckham_MIA_WR`

**Team Normalization:**
- Store team abbreviations as-is (already consistent across files)
- Handle potential variations: "LA" → "LAR" or "LAC" (context-dependent)

**Position Normalization:**
- Store positions as-is: QB, RB, WR, TE, DST (already consistent)

### 6. Fuzzy Matching & Alias Mapping

**Fuzzy Matching Threshold:** 85%

**Logic:**
- If similarity >= 85%: Auto-match (no user prompt)
- If similarity < 85%: Show manual mapping dialog

**Manual Mapping Strategy:**
- **Approach:** Skip low-confidence matches during import (don't block import)
- **Post-Import Review:**
  - Show "Unmatched Players" notification after import completes
  - Display count: "153 players imported successfully. 3 players skipped (low confidence matches)"
  - Provide "Review Unmatched Players" button/link
  - Review screen shows all skipped players with suggested matches
  - User can map aliases or ignore
  - Skipped players won't appear in player pool until mapped

**Review Screen (Post-Import):**
```
Unmatched Players (3)

1. Imported: "C. McCaffrey" (SF, RB)
   Suggested: Christian McCaffrey (SF, RB) - 82% match
   [Map to Suggested] [Ignore]

2. Imported: "AJ Dillon" (GB, RB)
   Suggested: A.J. Dillon (GB, RB) - 78% match
   [Map to Suggested] [Ignore]

3. Imported: "Gabe Davis" (JAX, WR)
   No match found
   [Create New Player] [Ignore]

[Save Mappings]
```

**Benefits:**
- Import completes quickly (not blocked by dialogs)
- User can fix source file and re-import if preferred
- Batch review is more efficient than one-at-a-time dialogs
- Unmatched players are tracked but don't break the import

**Alias Storage:**
- Table: `player_aliases`
- Columns: `alias_name`, `canonical_player_key`, `created_at`
- Example: `alias_name="C. McCaffrey"`, `canonical_player_key="christian_mccaffrey_SF_RB"`
- Future imports: Auto-resolve using stored aliases (no prompt)

### 7. Ownership Format Handling

**Auto-Detection Logic:**
- If ownership value > 1: Assume percentage format (e.g., 11.2 = 11.2%), divide by 100
- If ownership value <= 1: Assume decimal format (e.g., 0.112 = 11.2%), store as-is
- Store in database as decimal (0-1 range)

**Examples:**
- LineStar `ProjOwn=11.2` → Store as `0.112`
- DraftKings `Own=0.112` → Store as `0.112`

### 8. Data Validation Rules

**File-Level Validation:**
1. File format: Must be .xlsx
2. Required columns: All mapped columns must exist
3. Empty file: Must have at least 1 data row

**Data Type Validation:**
1. Salary: Must be integer
2. Projection: Must be float
3. Ownership: Must be float
4. Ceiling: Must be float
5. Floor: Must be float
6. Week: Must be integer (Comprehensive Stats)
7. Snaps: Must be integer (Comprehensive Stats)
8. All stat fields: Must be numeric

**Business Rule Validation:**
1. **Salary Range:** 3,000 <= salary <= 10,000
   - Error: "Invalid salary for {player}: ${salary}. Must be between $3,000 and $10,000"
   
2. **Projection Range:** projection >= 0
   - Error: "Invalid projection for {player}: {projection}. Must be >= 0"
   
3. **Ownership Range:** 0 <= ownership <= 1 (after auto-conversion)
   - Error: "Invalid ownership for {player}: {ownership}. Must be between 0 and 1"
   
4. **Ceiling >= Floor:** ceiling >= floor
   - Warning (not error): "Ceiling < Floor for {player}. Using projection as both ceiling and floor"
   
5. **Position Whitelist:** position in ['QB', 'RB', 'WR', 'TE', 'DST']
   - Error: "Invalid position for {player}: '{position}'. Must be QB, RB, WR, TE, or DST"
   
6. **Team Format:** 2-3 character abbreviation (no strict validation, allow any string)
   - Rationale: Team abbreviations vary, fuzzy matching handles typos
   
7. **Week Range:** 1 <= week <= 18 (Comprehensive Stats)
   - Error: "Invalid week number: {week}. Must be between 1 and 18"

**Validation Behavior:**
- **Hard Errors:** Stop import, rollback, show detailed error message
- **Warnings:** Log warning, continue import (use fallback values if needed)
- **Missing Optional Fields:** Allow nulls for ceiling, floor, notes, ownership

**Validation Error Examples:**
- "Import failed: Invalid salary for Christian McCaffrey: $15000. Must be between $3,000 and $10,000"
- "Import failed: Invalid position for John Doe: 'K'. Must be QB, RB, WR, TE, or DST"
- "Import failed: Invalid projection for Patrick Mahomes: -5.2. Must be >= 0"
- "Import failed: Invalid ownership for Lamar Jackson: 1.5. Must be between 0 and 1"

### 9. Error Handling

**Error Display:**
- Show detailed error toast with specific issue
- No partial imports (rollback on any error)
- Log full error for debugging

**Error Message Examples:**
- "Import failed: Missing required column 'Salary'"
- "Import failed: Column 'Salary' contains non-numeric values"
- "Import failed: File contains no player data"
- "Import failed: File must be .xlsx format"

### 9. Success Messaging

**Format (No Unmatched Players):**
- "{count} players imported successfully"

**Format (With Unmatched Players):**
- "{count} players imported successfully. {skipped_count} players skipped (low confidence matches)"
- Show "Review Unmatched Players" button in toast

**Examples:**
- "153 players imported successfully"
- "267 players imported successfully. 3 players skipped (low confidence matches)"
- "2690 records imported successfully"

**Display:** 
- Toast notification (auto-dismiss after 5 seconds if no unmatched players)
- Persist toast with "Review" button if unmatched players exist

### 10. Overwrite Behavior

**LineStar Import:**
- Delete all players for selected week where `source="LineStar"`
- Insert new LineStar data
- No confirmation dialog

**DraftKings Import:**
- Delete ALL players for selected week (regardless of source)
- Insert new DraftKings data
- No confirmation dialog
- Rationale: DraftKings is "source of truth" and replaces LineStar

**Comprehensive Stats Import:**
- Delete ALL records from `historical_stats` table
- Insert all new records (all weeks)
- No confirmation dialog
- Automated backup created before delete

### 11. Performance Requirements

- Process 200+ players in <5 seconds
- Use bulk inserts (SQLAlchemy `bulk_insert_mappings`)
- Use transactions (rollback on error)
- Show spinner during processing (no progress bar needed)

### 12. Database Tables

**player_pools:**
- `id`, `week_id`, `player_key`, `name`, `team`, `position`, `salary`, `projection`, `ownership`, `ceiling`, `floor`, `notes`, `source`, `uploaded_at`

**historical_stats:**
- `id`, `player_key`, `week`, `season`, `team`, `opponent`, `snaps`, `snap_pct`, `rush_attempts`, `rush_yards`, `rush_tds`, `targets`, `target_share`, `receptions`, `rec_yards`, `rec_tds`, `total_tds`, `touches`, `actual_points`, `salary`

**historical_stats_backup:**
- Identical schema to `historical_stats`

**player_aliases:**
- `id`, `alias_name`, `canonical_player_key`, `created_at`

**vegas_lines (Phase 2):**
- `id`, `week_id`, `team`, `opponent`, `implied_team_total`, `spread`, `over_under`, `updated_at`

### 13. Dependencies

**Backend:**
- PostgreSQL database running
- SQLAlchemy models defined
- Alembic migrations run
- Week management system (weeks table populated)

**Frontend:**
- Week selector component in header
- File input component
- Toast notification system
- Loading spinner component

**Python Libraries:**
- pandas (XLSX parsing)
- openpyxl (Excel file support)
- rapidfuzz (fuzzy string matching)
- SQLAlchemy (ORM)

### 14. Out of Scope (MVP)

- ❌ Automated data fetching (APIs)
- ❌ Real-time data updates
- ❌ CSV import
- ❌ Drag-and-drop upload
- ❌ Multiple file upload at once
- ❌ Data export
- ❌ Historical data visualization
- ❌ Vegas line movement tracking (Phase 2)
- ❌ Projection accuracy analysis (Phase 2)

---

## Phase 2 Preview: Vegas Line Tracking

**Future Enhancement (not in MVP):**
- Hourly API calls to fetch current Vegas lines
- Store each fetch as new record (time-series data)
- Track line movement over time (ITT, spread, over/under)
- Flag significant movements (e.g., 2+ point ITT swing)
- Alert users about game script changes
- Visualize line movement in app

**Table Structure (Phase 2):**
```sql
vegas_lines_history:
  - id, week_id, team, opponent
  - implied_team_total, spread, over_under
  - fetched_at (timestamp)
  - movement_flag (boolean)
```

This will be implemented properly in Phase 2 with the Vegas API integration.

