# Data Import System - Technical Specification

**Feature:** Data Import System  
**Version:** 1.0  
**Date:** October 27, 2025  
**Status:** Ready for Implementation  
**Estimated Effort:** 12-14 hours

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Database Schema](#database-schema)
4. [API Specifications](#api-specifications)
5. [Frontend Components](#frontend-components)
6. [Data Processing Logic](#data-processing-logic)
7. [Validation Rules](#validation-rules)
8. [Error Handling](#error-handling)
9. [Implementation Plan](#implementation-plan)
10. [Test Cases](#test-cases)
11. [Acceptance Criteria](#acceptance-criteria)

---

## Overview

### Purpose
Enable users to upload and parse XLSX files from three sources (LineStar, DraftKings, Comprehensive Stats) to populate player pools and historical data for DFS lineup optimization.

### Key Objectives
1. **Zero-error data import** - 100% success rate for valid files
2. **Multi-source support** - Handle LineStar, DraftKings (FE sheet), and NFL Stats
3. **Player normalization** - Composite key generation with fuzzy matching
4. **Import tracking** - Track ownership/projection changes between imports
5. **Data validation** - Comprehensive validation rules (salary range, projections, positions)
6. **User feedback** - Clear progress, success/error messages, change tracking

### Success Metrics
- ✅ Process 200+ players in <5 seconds
- ✅ 100% import success rate for valid files
- ✅ Zero parsing errors for standard file formats
- ✅ Fuzzy matching accuracy >95%
- ✅ Clear, actionable error messages

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                      │
│                                                          │
│  ┌────────────────────────────────────────────────┐   │
│  │  Week Selector (Header)                        │   │
│  │  - Dropdown: Week 1-18                         │   │
│  │  - Global state (Zustand)                      │   │
│  └────────────────────────────────────────────────┘   │
│                                                          │
│  ┌────────────────────────────────────────────────┐   │
│  │  Import Data Button (Header)                   │   │
│  │  - Dropdown Menu:                              │   │
│  │    • Import LineStar                           │   │
│  │    • Import DraftKings                         │   │
│  │    • Import Season Stats                       │   │
│  └────────────────────────────────────────────────┘   │
│                                                          │
│  ┌────────────────────────────────────────────────┐   │
│  │  File Upload Flow                              │   │
│  │  1. Parse filename → detect week               │   │
│  │  2. Compare to selected week                   │   │
│  │  3. Show warning if mismatch                   │   │
│  │  4. Upload file (multipart/form-data)          │   │
│  │  5. Show spinner                               │   │
│  │  6. Display success/error toast                │   │
│  └────────────────────────────────────────────────┘   │
│                                                          │
│  ┌────────────────────────────────────────────────┐   │
│  │  Unmatched Players Review (Post-Import)        │   │
│  │  - List skipped players                        │   │
│  │  - Suggested matches                           │   │
│  │  - Map/Ignore actions                          │   │
│  └────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          ↓ HTTP/REST API
┌─────────────────────────────────────────────────────────┐
│                  BACKEND (FastAPI)                       │
│                                                          │
│  ┌────────────────────────────────────────────────┐   │
│  │  API Endpoints                                  │   │
│  │  - POST /api/import/linestar                   │   │
│  │  - POST /api/import/draftkings                 │   │
│  │  - POST /api/import/nfl-stats                  │   │
│  │  - GET  /api/import-history                    │   │
│  │  - GET  /api/import-history/compare            │   │
│  │  - GET  /api/unmatched-players                 │   │
│  │  - POST /api/unmatched-players/map             │   │
│  │  - POST /api/unmatched-players/ignore          │   │
│  └────────────────────────────────────────────────┘   │
│                                                          │
│  ┌────────────────────────────────────────────────┐   │
│  │  Core Services                                  │   │
│  │                                                 │   │
│  │  DataImporter                                   │   │
│  │  - parse_xlsx()                                │   │
│  │  - validate_data()                             │   │
│  │  - normalize_players()                         │   │
│  │  - bulk_insert()                               │   │
│  │                                                 │   │
│  │  PlayerMatcher                                  │   │
│  │  - fuzzy_match()                               │   │
│  │  - generate_player_key()                       │   │
│  │  - resolve_alias()                             │   │
│  │                                                 │   │
│  │  ImportHistoryTracker                          │   │
│  │  - create_import_record()                      │   │
│  │  - snapshot_players()                          │   │
│  │  - calculate_deltas()                          │   │
│  │                                                 │   │
│  │  ValidationService                             │   │
│  │  - validate_salary_range()                     │   │
│  │  - validate_projection()                       │   │
│  │  - validate_position()                         │   │
│  │  - validate_ownership()                        │   │
│  └────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          ↓ SQLAlchemy ORM
┌─────────────────────────────────────────────────────────┐
│              DATABASE (PostgreSQL)                       │
│                                                          │
│  Tables:                                                │
│  - weeks                                                │
│  - player_pools                                         │
│  - historical_stats                                     │
│  - historical_stats_backup                              │
│  - player_aliases                                       │
│  - import_history                                       │
│  - player_pool_history                                  │
│  - unmatched_players                                    │
└─────────────────────────────────────────────────────────┘
```

### Technology Stack

**Backend:**
- FastAPI (Python 3.11+)
- SQLAlchemy 2.0 (ORM)
- Alembic (migrations)
- pandas + openpyxl (XLSX parsing)
- PuLP (future: lineup optimization)
- rapidfuzz (fuzzy string matching)

**Frontend:**
- React 18 + TypeScript
- Vite (build tool)
- Material-UI (MUI) v5
- Zustand (state management)
- TanStack Query (data fetching)
- React Hook Form + Zod (forms/validation)

**Database:**
- PostgreSQL 15

---

## Database Schema

### Table: `weeks`

```sql
CREATE TABLE weeks (
    id SERIAL PRIMARY KEY,
    season INTEGER NOT NULL,
    week_number INTEGER NOT NULL CHECK (week_number BETWEEN 1 AND 18),
    status VARCHAR(20) DEFAULT 'upcoming' CHECK (status IN ('upcoming', 'active', 'completed')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_season_week UNIQUE (season, week_number)
);

CREATE INDEX idx_weeks_week_number ON weeks(week_number);
CREATE INDEX idx_weeks_status ON weeks(status);
```

### Table: `player_pools`

```sql
CREATE TABLE player_pools (
    id SERIAL PRIMARY KEY,
    week_id INTEGER NOT NULL REFERENCES weeks(id) ON DELETE CASCADE,
    player_key VARCHAR(255) NOT NULL,  -- normalized: {name}_{team}_{position}
    name VARCHAR(255) NOT NULL,  -- original name
    team VARCHAR(10) NOT NULL,
    position VARCHAR(10) NOT NULL CHECK (position IN ('QB', 'RB', 'WR', 'TE', 'DST')),
    salary INTEGER NOT NULL CHECK (salary BETWEEN 3000 AND 10000),
    projection FLOAT CHECK (projection >= 0),
    ownership FLOAT CHECK (ownership BETWEEN 0 AND 1),
    ceiling FLOAT,
    floor FLOAT,
    notes TEXT,
    source VARCHAR(50) NOT NULL CHECK (source IN ('LineStar', 'DraftKings')),
    uploaded_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_week_player UNIQUE (week_id, player_key)
);

CREATE INDEX idx_player_pools_week_id ON player_pools(week_id);
CREATE INDEX idx_player_pools_player_key ON player_pools(player_key);
CREATE INDEX idx_player_pools_position ON player_pools(position);
CREATE INDEX idx_player_pools_team ON player_pools(team);
CREATE INDEX idx_player_pools_source ON player_pools(source);
```

### Table: `historical_stats`

```sql
CREATE TABLE historical_stats (
    id SERIAL PRIMARY KEY,
    player_key VARCHAR(255) NOT NULL,
    week INTEGER NOT NULL CHECK (week BETWEEN 1 AND 18),
    season INTEGER NOT NULL,
    team VARCHAR(10) NOT NULL,
    opponent VARCHAR(10),
    snaps INTEGER,
    snap_pct FLOAT CHECK (snap_pct BETWEEN 0 AND 1),
    rush_attempts INTEGER,
    rush_yards INTEGER,
    rush_tds INTEGER,
    targets INTEGER,
    target_share FLOAT CHECK (target_share BETWEEN 0 AND 1),
    receptions INTEGER,
    rec_yards INTEGER,
    rec_tds INTEGER,
    total_tds INTEGER,
    touches INTEGER,
    actual_points FLOAT,
    salary INTEGER,
    CONSTRAINT unique_player_week_season UNIQUE (player_key, week, season)
);

CREATE INDEX idx_historical_stats_player_key ON historical_stats(player_key);
CREATE INDEX idx_historical_stats_week ON historical_stats(week);
CREATE INDEX idx_historical_stats_season ON historical_stats(season);
```

### Table: `historical_stats_backup`

```sql
CREATE TABLE historical_stats_backup (
    -- Identical schema to historical_stats
    id SERIAL PRIMARY KEY,
    player_key VARCHAR(255) NOT NULL,
    week INTEGER NOT NULL CHECK (week BETWEEN 1 AND 18),
    season INTEGER NOT NULL,
    team VARCHAR(10) NOT NULL,
    opponent VARCHAR(10),
    snaps INTEGER,
    snap_pct FLOAT CHECK (snap_pct BETWEEN 0 AND 1),
    rush_attempts INTEGER,
    rush_yards INTEGER,
    rush_tds INTEGER,
    targets INTEGER,
    target_share FLOAT CHECK (target_share BETWEEN 0 AND 1),
    receptions INTEGER,
    rec_yards INTEGER,
    rec_tds INTEGER,
    total_tds INTEGER,
    touches INTEGER,
    actual_points FLOAT,
    salary INTEGER,
    backed_up_at TIMESTAMP DEFAULT NOW()
);
```

### Table: `player_aliases`

```sql
CREATE TABLE player_aliases (
    id SERIAL PRIMARY KEY,
    alias_name VARCHAR(255) NOT NULL UNIQUE,
    canonical_player_key VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_player_aliases_alias_name ON player_aliases(alias_name);
CREATE INDEX idx_player_aliases_canonical_key ON player_aliases(canonical_player_key);
```

### Table: `import_history`

```sql
CREATE TABLE import_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    week_id INTEGER NOT NULL REFERENCES weeks(id) ON DELETE CASCADE,
    source VARCHAR(50) NOT NULL CHECK (source IN ('LineStar', 'DraftKings', 'ComprehensiveStats')),
    file_name VARCHAR(255),
    player_count INTEGER NOT NULL,
    import_summary JSONB,  -- Store change summary
    imported_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_import_history_week_source ON import_history(week_id, source);
CREATE INDEX idx_import_history_imported_at ON import_history(imported_at);
```

### Table: `player_pool_history`

```sql
CREATE TABLE player_pool_history (
    id SERIAL PRIMARY KEY,
    import_id UUID NOT NULL REFERENCES import_history(id) ON DELETE CASCADE,
    player_key VARCHAR(255) NOT NULL,
    salary INTEGER,
    projection FLOAT,
    ownership FLOAT,
    ceiling FLOAT,
    floor FLOAT,
    imported_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_player_pool_history_import_id ON player_pool_history(import_id);
CREATE INDEX idx_player_pool_history_player_key ON player_pool_history(player_key);
```

### Table: `unmatched_players`

```sql
CREATE TABLE unmatched_players (
    id SERIAL PRIMARY KEY,
    import_id UUID NOT NULL REFERENCES import_history(id) ON DELETE CASCADE,
    imported_name VARCHAR(255) NOT NULL,
    team VARCHAR(10) NOT NULL,
    position VARCHAR(10) NOT NULL,
    suggested_player_key VARCHAR(255),
    similarity_score FLOAT CHECK (similarity_score BETWEEN 0 AND 1),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'mapped', 'ignored')),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_unmatched_players_import_id ON unmatched_players(import_id);
CREATE INDEX idx_unmatched_players_status ON unmatched_players(status);
```

---

## API Specifications

### 1. Import LineStar Data

**Endpoint:** `POST /api/import/linestar`

**Request:**
```
Content-Type: multipart/form-data

Fields:
- file: File (XLSX)
- week_id: Integer
- detected_week: Integer (optional, parsed from filename)
```

**Response (Success):**
```json
{
  "success": true,
  "import_id": "uuid-string",
  "message": "153 players imported successfully",
  "player_count": 153,
  "changes_from_previous": null,  // First import
  "unmatched_count": 0
}
```

**Response (Success with Changes):**
```json
{
  "success": true,
  "import_id": "uuid-string",
  "message": "153 players imported successfully",
  "player_count": 153,
  "changes_from_previous": {
    "ownership_changes": 12,
    "avg_ownership_delta": 2.3,
    "projection_changes": 3,
    "new_players": 2,
    "removed_players": 0
  },
  "unmatched_count": 3
}
```

**Response (Week Mismatch Warning):**
```json
{
  "success": false,
  "warning": "week_mismatch",
  "message": "Filename suggests Week 8, but Week 9 selected",
  "detected_week": 8,
  "selected_week": 9,
  "requires_confirmation": true
}
```

**Response (Validation Error):**
```json
{
  "success": false,
  "error": "Invalid salary for Christian McCaffrey: $15000. Must be between $3,000 and $10,000"
}
```

**Processing Logic:**
1. Validate file format (.xlsx)
2. Parse filename for week number (regex: `WK(\d+)`)
3. Compare detected week to selected week
4. If mismatch and not confirmed, return warning
5. Read first sheet (index 0)
6. Validate required columns exist
7. Parse and validate data
8. Normalize player names (generate player_key)
9. Fuzzy match against existing players
10. Skip low-confidence matches (<85%), store in unmatched_players
11. Create import_history record
12. Delete existing LineStar data for this week
13. Bulk insert new players to player_pools
14. Snapshot to player_pool_history
15. Calculate deltas from previous import
16. Return success with summary

---

### 2. Import DraftKings Data

**Endpoint:** `POST /api/import/draftkings`

**Request:**
```
Content-Type: multipart/form-data

Fields:
- file: File (XLSX)
- week_id: Integer
- detected_week: Integer (optional)
```

**Response:** Same format as LineStar import

**Processing Logic:**
1. Validate file format (.xlsx)
2. Parse filename for week number (regex: `Week (\d+)`)
3. Compare detected week to selected week
4. If mismatch and not confirmed, return warning
5. Read FE sheet (skip row 1, use row 2 as header)
6. Validate required columns exist
7. Parse and validate data
8. Normalize player names (generate player_key)
9. Fuzzy match against existing players
10. Skip low-confidence matches (<85%), store in unmatched_players
11. Create import_history record
12. **Delete ALL existing players for this week** (DK replaces everything)
13. Bulk insert new players to player_pools
14. Snapshot to player_pool_history
15. Calculate deltas from previous DraftKings import
16. Return success with summary

---

### 3. Import NFL Stats Data

**Endpoint:** `POST /api/import/nfl-stats`

**Request:**
```
Content-Type: multipart/form-data

Fields:
- file: File (XLSX)
```

**Response:**
```json
{
  "success": true,
  "import_id": "uuid-string",
  "message": "2690 records imported successfully",
  "record_count": 2690,
  "backup_created": true
}
```

**Processing Logic:**
1. Validate file format (.xlsx)
2. Read "Points" sheet
3. Validate required columns exist
4. Parse and validate data
5. Normalize player names (generate player_key)
6. Create import_history record
7. **Backup existing data:** Copy all records from historical_stats to historical_stats_backup
8. **Delete all existing records** from historical_stats
9. Bulk insert all new records to historical_stats
10. Return success with record count

---

### 4. Get Import History

**Endpoint:** `GET /api/import-history`

**Query Parameters:**
- `week_id` (required): Integer
- `source` (optional): String ('LineStar', 'DraftKings', 'ComprehensiveStats')

**Response:**
```json
{
  "success": true,
  "imports": [
    {
      "id": "uuid-1",
      "week_id": 9,
      "source": "DraftKings",
      "file_name": "DKSalaries Week 9.xlsx",
      "player_count": 153,
      "imported_at": "2024-10-27T11:30:00Z",
      "changes_from_previous": {
        "ownership_changes": 12,
        "avg_ownership_delta": 2.3,
        "projection_changes": 3,
        "new_players": 2
      }
    },
    {
      "id": "uuid-2",
      "week_id": 9,
      "source": "DraftKings",
      "file_name": "DKSalaries Week 9.xlsx",
      "player_count": 151,
      "imported_at": "2024-10-27T10:00:00Z",
      "changes_from_previous": null
    }
  ]
}
```

---

### 5. Compare Imports

**Endpoint:** `GET /api/import-history/compare`

**Query Parameters:**
- `current_id` (required): UUID
- `previous_id` (required): UUID

**Response:**
```json
{
  "success": true,
  "comparison": {
    "current": {
      "id": "uuid-1",
      "imported_at": "2024-10-27T11:30:00Z",
      "player_count": 153
    },
    "previous": {
      "id": "uuid-2",
      "imported_at": "2024-10-27T10:00:00Z",
      "player_count": 151
    },
    "ownership_changes": [
      {
        "player_key": "christian_mccaffrey_SF_RB",
        "name": "Christian McCaffrey",
        "previous_ownership": 0.421,
        "current_ownership": 0.452,
        "delta": 0.031
      }
    ],
    "projection_changes": [
      {
        "player_key": "lamar_jackson_BAL_QB",
        "name": "Lamar Jackson",
        "previous_projection": 24.5,
        "current_projection": 26.2,
        "delta": 1.7
      }
    ],
    "new_players": [
      {
        "player_key": "gabe_davis_JAX_WR",
        "name": "Gabe Davis",
        "salary": 5200,
        "projection": 11.2
      }
    ],
    "removed_players": []
  }
}
```

---

### 6. Get Unmatched Players

**Endpoint:** `GET /api/unmatched-players`

**Query Parameters:**
- `import_id` (required): UUID
- `status` (optional): String ('pending', 'mapped', 'ignored')

**Response:**
```json
{
  "success": true,
  "unmatched_players": [
    {
      "id": 1,
      "imported_name": "C. McCaffrey",
      "team": "SF",
      "position": "RB",
      "suggested_player_key": "christian_mccaffrey_SF_RB",
      "similarity_score": 0.82,
      "status": "pending"
    },
    {
      "id": 2,
      "imported_name": "AJ Dillon",
      "team": "GB",
      "position": "RB",
      "suggested_player_key": "aj_dillon_GB_RB",
      "similarity_score": 0.78,
      "status": "pending"
    }
  ]
}
```

---

### 7. Map Unmatched Player

**Endpoint:** `POST /api/unmatched-players/map`

**Request:**
```json
{
  "unmatched_player_id": 1,
  "canonical_player_key": "christian_mccaffrey_SF_RB"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Alias mapped successfully"
}
```

**Processing Logic:**
1. Validate unmatched_player_id exists
2. Validate canonical_player_key exists in player_pools
3. Insert alias into player_aliases table
4. Update unmatched_players status to 'mapped'
5. Return success

---

### 8. Ignore Unmatched Player

**Endpoint:** `POST /api/unmatched-players/ignore`

**Request:**
```json
{
  "unmatched_player_id": 1
}
```

**Response:**
```json
{
  "success": true,
  "message": "Player ignored"
}
```

**Processing Logic:**
1. Validate unmatched_player_id exists
2. Update unmatched_players status to 'ignored'
3. Return success

---

## Frontend Components

### 1. WeekSelector Component

**Location:** Header (always visible)

**Props:**
```typescript
interface WeekSelectorProps {
  // No props - uses Zustand global state
}
```

**State (Zustand):**
```typescript
interface WeekState {
  currentWeek: number;
  setCurrentWeek: (week: number) => void;
}
```

**UI:**
```tsx
<Select
  value={currentWeek}
  onChange={(e) => setCurrentWeek(e.target.value)}
  sx={{ minWidth: 120 }}
>
  {Array.from({ length: 18 }, (_, i) => i + 1).map((week) => (
    <MenuItem key={week} value={week}>
      Week {week}
    </MenuItem>
  ))}
</Select>
```

---

### 2. ImportDataButton Component

**Location:** Header (next to WeekSelector)

**Props:**
```typescript
interface ImportDataButtonProps {
  // No props
}
```

**UI:**
```tsx
<Button
  variant="contained"
  startIcon={<Upload />}
  onClick={handleClick}
>
  Import Data
</Button>
<Menu
  anchorEl={anchorEl}
  open={Boolean(anchorEl)}
  onClose={handleClose}
>
  <MenuItem onClick={() => handleImportType('linestar')}>
    Import LineStar Data
  </MenuItem>
  <MenuItem onClick={() => handleImportType('draftkings')}>
    Import DraftKings Data
  </MenuItem>
  <MenuItem onClick={() => handleImportType('nfl-stats')}>
    Import Season Stats
  </MenuItem>
</Menu>
```

**Logic:**
1. User clicks button → Menu opens
2. User selects import type → File input opens
3. User selects file → Parse filename for week
4. Compare to selected week → Show warning if mismatch
5. Upload file → Show spinner
6. Display success/error toast

---

### 3. WeekMismatchDialog Component

**Props:**
```typescript
interface WeekMismatchDialogProps {
  open: boolean;
  detectedWeek: number;
  selectedWeek: number;
  onChangeWeek: () => void;
  onContinue: () => void;
  onCancel: () => void;
}
```

**UI:**
```tsx
<Dialog open={open} onClose={onCancel}>
  <DialogTitle>⚠️ Week Mismatch Detected</DialogTitle>
  <DialogContent>
    <Typography>
      You selected Week {selectedWeek}, but the filename suggests Week {detectedWeek}.
    </Typography>
    <RadioGroup>
      <FormControlLabel
        value="change"
        control={<Radio />}
        label={`Import for Week ${detectedWeek} (change week selector)`}
      />
      <FormControlLabel
        value="continue"
        control={<Radio />}
        label={`Continue with Week ${selectedWeek} (filename is incorrect)`}
      />
    </RadioGroup>
  </DialogContent>
  <DialogActions>
    <Button onClick={onCancel}>Cancel</Button>
    <Button onClick={handleAction} variant="contained">
      Confirm
    </Button>
  </DialogActions>
</Dialog>
```

---

### 4. UnmatchedPlayersReview Component

**Props:**
```typescript
interface UnmatchedPlayersReviewProps {
  importId: string;
}
```

**State:**
```typescript
interface UnmatchedPlayer {
  id: number;
  imported_name: string;
  team: string;
  position: string;
  suggested_player_key: string | null;
  similarity_score: number | null;
  status: 'pending' | 'mapped' | 'ignored';
}
```

**UI:**
```tsx
<Box>
  <Typography variant="h5">Unmatched Players ({unmatchedCount})</Typography>
  
  {unmatchedPlayers.map((player) => (
    <Card key={player.id} sx={{ mb: 2 }}>
      <CardContent>
        <Typography variant="h6">
          {player.imported_name} ({player.team}, {player.position})
        </Typography>
        
        {player.suggested_player_key && (
          <Box sx={{ mt: 1 }}>
            <Typography variant="body2" color="text.secondary">
              Suggested: {player.suggested_player_key.replace(/_/g, ' ')} 
              ({(player.similarity_score * 100).toFixed(0)}% match)
            </Typography>
            <Button
              variant="outlined"
              size="small"
              onClick={() => handleMap(player.id, player.suggested_player_key)}
            >
              Map to Suggested
            </Button>
          </Box>
        )}
        
        <Button
          variant="text"
          size="small"
          onClick={() => handleIgnore(player.id)}
        >
          Ignore
        </Button>
      </CardContent>
    </Card>
  ))}
  
  <Button variant="contained" onClick={handleSave}>
    Save Mappings
  </Button>
</Box>
```

---

## Data Processing Logic

### Player Name Normalization

**Function:** `normalize_player_name(name: str) -> str`

**Logic:**
```python
import re

def normalize_player_name(name: str) -> str:
    """
    Normalize player name for composite key generation.
    
    Steps:
    1. Remove suffixes: Jr., Sr., III, II, IV
    2. Remove prefixes: D', O'
    3. Remove all punctuation: apostrophes, periods, hyphens, commas
    4. Convert to lowercase
    5. Replace spaces with underscores
    
    Examples:
    - "D'Andre Swift Jr." → "dandre_swift"
    - "A.J. Brown" → "aj_brown"
    - "Christian McCaffrey" → "christian_mccaffrey"
    """
    # Remove suffixes
    suffixes = r'\s+(Jr\.?|Sr\.?|III|II|IV)$'
    name = re.sub(suffixes, '', name, flags=re.IGNORECASE)
    
    # Remove prefixes
    prefixes = r"^(D'|O')"
    name = re.sub(prefixes, '', name, flags=re.IGNORECASE)
    
    # Remove all punctuation
    name = re.sub(r"['\.\-,]", '', name)
    
    # Convert to lowercase
    name = name.lower()
    
    # Replace spaces with underscores
    name = name.replace(' ', '_')
    
    # Remove multiple underscores
    name = re.sub(r'_+', '_', name)
    
    # Strip leading/trailing underscores
    name = name.strip('_')
    
    return name
```

**Generate Player Key:**
```python
def generate_player_key(name: str, team: str, position: str) -> str:
    """
    Generate composite player key.
    
    Format: {normalized_name}_{team}_{position}
    
    Example: "christian_mccaffrey_SF_RB"
    """
    normalized_name = normalize_player_name(name)
    return f"{normalized_name}_{team}_{position}"
```

---

### Fuzzy Matching

**Function:** `fuzzy_match_player(imported_name: str, team: str, position: str) -> tuple`

**Logic:**
```python
from rapidfuzz import fuzz, process

def fuzzy_match_player(
    imported_name: str,
    team: str,
    position: str,
    existing_players: list[dict],
    threshold: float = 0.85
) -> tuple[str | None, float]:
    """
    Fuzzy match imported player against existing players.
    
    Returns:
    - (player_key, similarity_score) if match found above threshold
    - (None, 0.0) if no match found
    
    Logic:
    1. Filter existing players by team and position (must match exactly)
    2. Compare imported name against filtered players using fuzzy matching
    3. Return best match if similarity >= threshold
    4. Otherwise return None
    """
    # Filter by team and position
    candidates = [
        p for p in existing_players
        if p['team'] == team and p['position'] == position
    ]
    
    if not candidates:
        return (None, 0.0)
    
    # Fuzzy match against candidate names
    names = [p['name'] for p in candidates]
    result = process.extractOne(
        imported_name,
        names,
        scorer=fuzz.ratio
    )
    
    if result is None:
        return (None, 0.0)
    
    best_match_name, score, _ = result
    similarity = score / 100.0  # Convert to 0-1 range
    
    if similarity >= threshold:
        # Find player_key for best match
        player = next(p for p in candidates if p['name'] == best_match_name)
        return (player['player_key'], similarity)
    
    return (None, similarity)
```

---

### Ownership Format Auto-Detection

**Function:** `normalize_ownership(value: float) -> float`

**Logic:**
```python
def normalize_ownership(value: float) -> float:
    """
    Auto-detect ownership format and normalize to 0-1 range.
    
    Logic:
    - If value > 1: Assume percentage format (e.g., 11.2 = 11.2%), divide by 100
    - If value <= 1: Assume decimal format (e.g., 0.112 = 11.2%), use as-is
    
    Examples:
    - 11.2 → 0.112
    - 0.112 → 0.112
    - 100.0 → 1.0
    - 0.5 → 0.5
    """
    if value > 1:
        return value / 100.0
    return value
```

---

### Import Comparison

**Function:** `calculate_import_deltas(current_import_id: UUID, previous_import_id: UUID) -> dict`

**Logic:**
```python
def calculate_import_deltas(
    current_import_id: UUID,
    previous_import_id: UUID,
    session: Session
) -> dict:
    """
    Calculate deltas between two imports.
    
    Returns:
    {
        "ownership_changes": int,
        "avg_ownership_delta": float,
        "projection_changes": int,
        "new_players": int,
        "removed_players": int
    }
    """
    # Fetch current and previous snapshots
    current_players = session.execute(
        select(PlayerPoolHistory)
        .where(PlayerPoolHistory.import_id == current_import_id)
    ).scalars().all()
    
    previous_players = session.execute(
        select(PlayerPoolHistory)
        .where(PlayerPoolHistory.import_id == previous_import_id)
    ).scalars().all()
    
    # Convert to dicts keyed by player_key
    current_dict = {p.player_key: p for p in current_players}
    previous_dict = {p.player_key: p for p in previous_players}
    
    # Calculate ownership changes
    ownership_changes = []
    for player_key in current_dict:
        if player_key in previous_dict:
            current_own = current_dict[player_key].ownership
            previous_own = previous_dict[player_key].ownership
            if current_own != previous_own:
                delta = current_own - previous_own
                ownership_changes.append(delta)
    
    # Calculate projection changes
    projection_changes = 0
    for player_key in current_dict:
        if player_key in previous_dict:
            current_proj = current_dict[player_key].projection
            previous_proj = previous_dict[player_key].projection
            if current_proj != previous_proj:
                projection_changes += 1
    
    # Calculate new/removed players
    new_players = len(set(current_dict.keys()) - set(previous_dict.keys()))
    removed_players = len(set(previous_dict.keys()) - set(current_dict.keys()))
    
    return {
        "ownership_changes": len(ownership_changes),
        "avg_ownership_delta": sum(ownership_changes) / len(ownership_changes) if ownership_changes else 0,
        "projection_changes": projection_changes,
        "new_players": new_players,
        "removed_players": removed_players
    }
```

---

## Validation Rules

### File-Level Validation

```python
def validate_file(file: UploadFile) -> None:
    """Validate uploaded file."""
    # Check file extension
    if not file.filename.endswith('.xlsx'):
        raise DataImportError("File must be .xlsx format")
    
    # Check file size (optional, e.g., max 10MB)
    if file.size > 10 * 1024 * 1024:
        raise DataImportError("File size exceeds 10MB limit")
```

### Column Validation

```python
def validate_columns(df: pd.DataFrame, required_columns: list[str]) -> None:
    """Validate required columns exist."""
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise DataImportError(
            f"Missing required columns: {', '.join(missing_columns)}"
        )
```

### Data Type Validation

```python
def validate_data_types(df: pd.DataFrame) -> None:
    """Validate data types."""
    try:
        df['Salary'] = df['Salary'].astype(int)
        df['Projection'] = df['Projection'].astype(float)
        df['Ownership'] = df['Ownership'].astype(float)
        df['Ceiling'] = df['Ceiling'].astype(float)
        df['Floor'] = df['Floor'].astype(float)
    except ValueError as e:
        raise DataImportError(f"Invalid data type: {str(e)}")
```

### Business Rule Validation

```python
def validate_player_data(player: dict) -> None:
    """Validate individual player data against business rules."""
    
    # Salary range: 3,000 - 10,000
    if not (3000 <= player['salary'] <= 10000):
        raise DataImportError(
            f"Invalid salary for {player['name']}: ${player['salary']}. "
            f"Must be between $3,000 and $10,000"
        )
    
    # Projection >= 0
    if player['projection'] < 0:
        raise DataImportError(
            f"Invalid projection for {player['name']}: {player['projection']}. "
            f"Must be >= 0"
        )
    
    # Ownership: 0-1 (after normalization)
    if not (0 <= player['ownership'] <= 1):
        raise DataImportError(
            f"Invalid ownership for {player['name']}: {player['ownership']}. "
            f"Must be between 0 and 1"
        )
    
    # Position whitelist
    valid_positions = ['QB', 'RB', 'WR', 'TE', 'DST']
    if player['position'] not in valid_positions:
        raise DataImportError(
            f"Invalid position for {player['name']}: '{player['position']}'. "
            f"Must be QB, RB, WR, TE, or DST"
        )
    
    # Ceiling >= Floor (warning, not error)
    if player.get('ceiling') and player.get('floor'):
        if player['ceiling'] < player['floor']:
            logger.warning(
                f"Ceiling < Floor for {player['name']}. "
                f"Using projection as both ceiling and floor"
            )
            player['ceiling'] = player['projection']
            player['floor'] = player['projection']
```

---

## Error Handling

### Custom Exception Classes

```python
# exceptions.py

class CortexException(Exception):
    """Base exception for Cortex application."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class DataImportError(CortexException):
    """Raised when data import fails."""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)

class ValidationError(CortexException):
    """Raised when validation fails."""
    def __init__(self, message: str):
        super().__init__(message, status_code=422)
```

### Global Exception Handler

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
            "error": exc.message
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "An unexpected error occurred. Please try again."
        }
    )
```

### Error Message Examples

**Good Error Messages:**
- ✅ "Import failed: Missing required column 'Salary'"
- ✅ "Import failed: Invalid salary for Christian McCaffrey: $15000. Must be between $3,000 and $10,000"
- ✅ "Import failed: Invalid position for John Doe: 'K'. Must be QB, RB, WR, TE, or DST"
- ✅ "Import failed: Invalid projection for Patrick Mahomes: -5.2. Must be >= 0"

**Bad Error Messages:**
- ❌ "KeyError: 'Salary'"
- ❌ "Optimization failed"
- ❌ "500 Internal Server Error"
- ❌ "NoneType object has no attribute 'salary'"

---

## Implementation Plan

### Phase 1: Database Setup (1 hour)

**Tasks:**
1. Create Alembic migration for all 8 tables
2. Add indexes and constraints
3. Run migration locally
4. Verify schema with `psql`

**Deliverables:**
- Migration file: `alembic/versions/001_create_data_import_tables.py`
- All tables created in PostgreSQL

---

### Phase 2: Backend Core Services (3 hours)

**Tasks:**
1. Implement `DataImporter` service
   - `parse_xlsx()` - pandas + openpyxl
   - `validate_data()` - all validation rules
   - `normalize_players()` - name normalization
   - `bulk_insert()` - SQLAlchemy bulk operations

2. Implement `PlayerMatcher` service
   - `fuzzy_match()` - rapidfuzz integration
   - `generate_player_key()` - composite key generation
   - `resolve_alias()` - alias lookup

3. Implement `ImportHistoryTracker` service
   - `create_import_record()` - insert to import_history
   - `snapshot_players()` - copy to player_pool_history
   - `calculate_deltas()` - compare imports

4. Implement `ValidationService`
   - All validation rules from spec

**Deliverables:**
- `services/data_importer.py`
- `services/player_matcher.py`
- `services/import_history_tracker.py`
- `services/validation_service.py`

---

### Phase 3: Backend API Endpoints (2 hours)

**Tasks:**
1. Implement 3 import endpoints
   - `POST /api/import/linestar`
   - `POST /api/import/draftkings`
   - `POST /api/import/nfl-stats`

2. Implement 2 history endpoints
   - `GET /api/import-history`
   - `GET /api/import-history/compare`

3. Implement 3 unmatched player endpoints
   - `GET /api/unmatched-players`
   - `POST /api/unmatched-players/map`
   - `POST /api/unmatched-players/ignore`

**Deliverables:**
- `routers/import_router.py`
- `routers/import_history_router.py`
- `routers/unmatched_players_router.py`

---

### Phase 4: Frontend Components (2.5 hours)

**Tasks:**
1. Implement `WeekSelector` component (Zustand state)
2. Implement `ImportDataButton` component (dropdown menu)
3. Implement `WeekMismatchDialog` component
4. Implement `UnmatchedPlayersReview` component
5. Implement file upload logic with week detection
6. Implement toast notifications (success/error)

**Deliverables:**
- `components/layout/WeekSelector.tsx`
- `components/import/ImportDataButton.tsx`
- `components/import/WeekMismatchDialog.tsx`
- `components/import/UnmatchedPlayersReview.tsx`
- `hooks/useDataImport.ts`

---

### Phase 5: Integration & Testing (2 hours)

**Tasks:**
1. Test LineStar import with sample file
2. Test DraftKings import with sample file
3. Test Comprehensive Stats import with sample file
4. Test week mismatch detection
5. Test fuzzy matching with edge cases
6. Test import history tracking
7. Test unmatched players workflow
8. Test all validation rules
9. Test error handling

**Deliverables:**
- All imports working end-to-end
- Zero errors on valid files
- Clear error messages on invalid files

---

## Test Cases

### Test Case 1: LineStar Import (Happy Path)

**Setup:**
- Week 9 selected in header
- Valid LineStar file: `LineStar_Football_WK9.xlsx`

**Steps:**
1. Click "Import Data" → "Import LineStar"
2. Select file
3. Wait for upload

**Expected Result:**
- ✅ Success toast: "153 players imported successfully"
- ✅ Players visible in player pool
- ✅ Source = "LineStar"

---

### Test Case 2: DraftKings Import (Replaces LineStar)

**Setup:**
- Week 9 selected
- LineStar data already imported
- Valid DraftKings file: `DKSalaries Week 9.xlsx`

**Steps:**
1. Click "Import Data" → "Import DraftKings"
2. Select file
3. Wait for upload

**Expected Result:**
- ✅ Success toast: "174 players imported successfully"
- ✅ LineStar data deleted
- ✅ Only DraftKings data remains
- ✅ Source = "DraftKings"

---

### Test Case 3: Week Mismatch Detection

**Setup:**
- Week 9 selected in header
- File: `DKSalaries Week 8.xlsx`

**Steps:**
1. Click "Import Data" → "Import DraftKings"
2. Select Week 8 file

**Expected Result:**
- ✅ Warning dialog appears
- ✅ Message: "You selected Week 9, but filename suggests Week 8"
- ✅ Options: Change to Week 8, Continue with Week 9, Cancel
- ✅ User can choose action

---

### Test Case 4: Validation Error (Invalid Salary)

**Setup:**
- Week 9 selected
- Modified file with salary = $15,000 (exceeds max)

**Steps:**
1. Upload file

**Expected Result:**
- ✅ Error toast: "Import failed: Invalid salary for Christian McCaffrey: $15000. Must be between $3,000 and $10,000"
- ✅ No data imported (rollback)

---

### Test Case 5: Fuzzy Matching (Low Confidence)

**Setup:**
- Week 9 selected
- File contains "C. McCaffrey" (82% match to existing "Christian McCaffrey")

**Steps:**
1. Upload file

**Expected Result:**
- ✅ Success toast: "153 players imported successfully. 1 player skipped (low confidence match)"
- ✅ "Review Unmatched Players" button visible
- ✅ C. McCaffrey not in player pool
- ✅ Stored in unmatched_players table

---

### Test Case 6: Import History Tracking

**Setup:**
- Week 9 selected
- DraftKings imported at 10:00 AM (ownership: 42.1%)
- DraftKings imported again at 11:30 AM (ownership: 45.2%)

**Steps:**
1. Upload second DraftKings file

**Expected Result:**
- ✅ Success toast: "153 players imported successfully. Changes from last import (1 hour ago): 12 ownership changes (avg +2.3%)"
- ✅ Import history shows both imports
- ✅ Comparison available

---

### Test Case 7: Comprehensive Stats Import (Full Replace)

**Setup:**
- Existing historical stats (Week 1-7)
- New file: `ComprehensiveStats_throughWeek8.xlsx`

**Steps:**
1. Upload file

**Expected Result:**
- ✅ Backup created in historical_stats_backup
- ✅ All old data deleted
- ✅ New data (Week 1-8) inserted
- ✅ Success toast: "2690 records imported successfully"

---

### Test Case 8: Unmatched Players Review

**Setup:**
- Import completed with 3 unmatched players

**Steps:**
1. Click "Review Unmatched Players"
2. Review list
3. Click "Map to Suggested" for player 1
4. Click "Ignore" for player 2
5. Click "Save Mappings"

**Expected Result:**
- ✅ Player 1 alias saved to player_aliases
- ✅ Player 2 status = 'ignored'
- ✅ Player 3 status = 'pending' (no action)
- ✅ Success toast: "Mappings saved"

---

## Acceptance Criteria

### Must Have (MVP)

1. ✅ **Import LineStar data**
   - Parse first sheet
   - Validate all required columns
   - Normalize player names
   - Fuzzy match (85% threshold)
   - Skip low-confidence matches
   - Bulk insert to player_pools
   - Success message with count

2. ✅ **Import DraftKings data**
   - Parse FE sheet (skip row 1)
   - Validate all required columns
   - Normalize player names
   - Fuzzy match (85% threshold)
   - Skip low-confidence matches
   - Delete ALL existing week data
   - Bulk insert to player_pools
   - Success message with count

3. ✅ **Import Comprehensive Stats**
   - Parse Points sheet
   - Validate all required columns
   - Normalize player names
   - Backup existing data
   - Delete all historical_stats
   - Bulk insert all weeks
   - Success message with count

4. ✅ **Week mismatch detection**
   - Parse week from filename
   - Compare to selected week
   - Show warning dialog if mismatch
   - Allow user to change week or continue

5. ✅ **Import history tracking**
   - Store import_history record
   - Snapshot to player_pool_history
   - Calculate deltas from previous import
   - Display changes in success message

6. ✅ **Unmatched players workflow**
   - Skip low-confidence matches
   - Store in unmatched_players table
   - Post-import review screen
   - Map aliases or ignore

7. ✅ **Data validation**
   - Salary range: 3K-10K
   - Projection >= 0
   - Ownership: 0-1
   - Position whitelist
   - Week range: 1-18
   - Ceiling >= Floor (warning)

8. ✅ **Error handling**
   - Detailed error messages
   - No partial imports (rollback)
   - Clear, actionable feedback

9. ✅ **Performance**
   - Process 200+ players in <5 seconds
   - Bulk inserts (not individual)
   - Single transaction per import

10. ✅ **UI/UX**
    - Week selector in header
    - Import Data button with dropdown
    - File upload with spinner
    - Toast notifications
    - Week mismatch dialog
    - Unmatched players review

---

## Out of Scope (Phase 2)

- ❌ Full import comparison UI (detailed view)
- ❌ Trend visualization (charts)
- ❌ Vegas line tracking (API integration)
- ❌ Automated data fetching
- ❌ CSV import
- ❌ Drag-and-drop upload
- ❌ Multiple file upload at once

---

## Appendix

### File Name Patterns

**LineStar:**
- Pattern: `LineStar_Football_WK{X}.xlsx`
- Regex: `WK(\d+)`
- Example: `LineStar_Football_WK8.xlsx` → Week 8

**DraftKings:**
- Pattern: `DKSalaries Week {X}.xlsx`
- Regex: `Week (\d+)`
- Example: `DKSalaries Week 8.xlsx` → Week 8

**Comprehensive Stats:**
- Pattern: `ComprehensiveStats_throughWeek{X}.xlsx`
- Regex: `throughWeek(\d+)`
- Example: `ComprehensiveStats_throughWeek7.xlsx` → Week 7

### Column Mappings

**LineStar → player_pools:**
```python
{
    "Name": "name",
    "Position": "position",
    "Team": "team",
    "Salary": "salary",
    "Projected": "projection",
    "Ceiling": "ceiling",
    "Floor": "floor",
    "ProjOwn": "ownership",
}
```

**DraftKings FE → player_pools:**
```python
{
    "Name": "name",
    "Pos": "position",
    "T": "team",
    "S": "salary",
    "Proj": "projection",
    "Ceil": "ceiling",
    "Flr": "floor",
    "Own": "ownership",
    "Notes": "notes",
}
```

**Comprehensive Stats Points → historical_stats:**
```python
{
    "Player": "player_name",
    "Tm": "team",
    "Pos": "position",
    "Wk": "week",
    "Opp": "opponent",
    "Snaps": "snaps",
    "Snp %": "snap_pct",
    "Ratt": "rush_attempts",
    "Rsh_yds": "rush_yards",
    "Rsh_td": "rush_tds",
    "CTGT": "targets",
    "CTGT%": "target_share",
    "Rec": "receptions",
    "Rc_yds": "rec_yards",
    "Rc_td": "rec_tds",
    "Tot TD": "total_tds",
    "Touch": "touches",
    "DK Pts": "actual_points",
    "Sal": "salary",
}
```

---

**End of Specification**

**Status:** ✅ Ready for Implementation  
**Next Step:** Run `/create-tasks` to generate implementation tasks

