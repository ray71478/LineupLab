# Data Import System - Final Review & Scan

**Date:** October 27, 2025  
**Status:** Pre-Specification Review

---

## ✅ Decisions Finalized

1. **Manual Alias Mapping:** Skip during import, post-import review screen
2. **DraftKings Overwrite:** Destructive (replaces all data for week) ✅
3. **Backup Strategy:** 1 backup, user has source files ✅
4. **Notes Field:** Store as-is, display only ✅
5. **Week Selector:** Trust user (no validation) ✅
6. **Data Validation:** Comprehensive rules added ✅

---

## 🔍 Final Comprehensive Scan

### 1. **Data Flow - Complete?** ✅

**LineStar → Database:**
- File upload → Parse XLSX → Validate → Normalize names → Fuzzy match → Skip low-confidence → Insert → Success message ✅

**DraftKings → Database:**
- File upload → Parse FE sheet (skip row 1) → Validate → Normalize names → Fuzzy match → Skip low-confidence → Delete week data → Insert → Success message ✅

**Comprehensive Stats → Database:**
- File upload → Parse Points sheet → Validate → Normalize names → Backup → Delete all → Insert all weeks → Success message ✅

**All flows complete!** ✅

---

### 2. **Edge Cases Covered?** ✅

**Player Names:**
- ✅ Suffixes (Jr., Sr., III) - Removed
- ✅ Prefixes (D', O') - Removed
- ✅ Punctuation (periods, apostrophes) - Removed
- ✅ Same name, different teams - Team in key differentiates
- ✅ Fuzzy matching - 85% threshold
- ✅ Low confidence - Skip and review later

**Data Values:**
- ✅ Ownership format variations - Auto-detect (>1 = percentage)
- ✅ Salary range - Validated (3K-10K)
- ✅ Negative projections - Rejected (>= 0)
- ✅ Ceiling < Floor - Warning, use projection as both
- ✅ Invalid positions - Rejected (whitelist: QB, RB, WR, TE, DST)
- ✅ Week out of range - Rejected (1-18)
- ✅ Missing optional fields - Allow nulls

**File Issues:**
- ✅ Wrong format - Rejected (.xlsx only)
- ✅ Missing columns - Rejected with specific error
- ✅ Empty file - Rejected
- ✅ Invalid data types - Rejected with specific error
- ✅ DK FE header quirk - Skip row 1, use row 2

**All edge cases handled!** ✅

---

### 3. **Database Schema - Complete?** ✅

**player_pools:**
```sql
id, week_id, player_key, name, team, position, 
salary, projection, ownership, ceiling, floor, notes, 
source, uploaded_at
```
- ✅ All required fields
- ✅ Indexes: week_id, player_key, position, team
- ✅ Unique constraint: (week_id, player_key)

**historical_stats:**
```sql
id, player_key, week, season, team, opponent,
snaps, snap_pct, rush_attempts, rush_yards, rush_tds,
targets, target_share, receptions, rec_yards, rec_tds,
total_tds, touches, actual_points, salary
```
- ✅ All required fields
- ✅ Indexes: player_key, week, season
- ✅ Unique constraint: (player_key, week, season)

**historical_stats_backup:**
- ✅ Identical schema to historical_stats

**player_aliases:**
```sql
id, alias_name, canonical_player_key, created_at
```
- ✅ All required fields
- ✅ Index: alias_name
- ✅ Unique constraint: alias_name

**unmatched_players (NEW - Need to Add):**
```sql
id, import_id, imported_name, team, position, 
suggested_player_key, similarity_score, status, created_at
```
- ⚠️ **MISSING:** Need table to track skipped players for review
- Status: 'pending', 'mapped', 'ignored'

**Schema 99% complete - need unmatched_players table!** ⚠️

---

### 4. **API Endpoints - Complete?** ✅

**Required Endpoints:**
- ✅ `POST /api/import/linestar` - Upload LineStar file
- ✅ `POST /api/import/draftkings` - Upload DraftKings file
- ✅ `POST /api/import/nfl-stats` - Upload Comprehensive Stats
- ⚠️ `GET /api/unmatched-players?import_id={id}` - Get skipped players (NEW)
- ⚠️ `POST /api/unmatched-players/map` - Map alias (NEW)
- ⚠️ `POST /api/unmatched-players/ignore` - Ignore player (NEW)

**Need 3 new endpoints for unmatched player review!** ⚠️

---

### 5. **UI Components - Complete?** ✅

**Required Components:**
- ✅ Week selector (header)
- ✅ Import Data button (header, dropdown menu)
- ✅ File input (accept=".xlsx")
- ✅ Loading spinner
- ✅ Toast notifications (success/error)
- ⚠️ Unmatched Players Review Screen (NEW)
  - List of skipped players
  - Suggested matches with similarity scores
  - Map/Ignore buttons
  - Save mappings button

**Need Unmatched Players Review component!** ⚠️

---

### 6. **Validation - Comprehensive?** ✅

**File-Level:**
- ✅ Format (.xlsx)
- ✅ Required columns
- ✅ Not empty

**Data Type:**
- ✅ Salary (int)
- ✅ Projection (float)
- ✅ Ownership (float)
- ✅ Ceiling/Floor (float)
- ✅ Week (int)
- ✅ All stats (numeric)

**Business Rules:**
- ✅ Salary: 3K-10K
- ✅ Projection: >= 0
- ✅ Ownership: 0-1
- ✅ Ceiling >= Floor (warning)
- ✅ Position: Whitelist
- ✅ Week: 1-18

**Validation is comprehensive!** ✅

---

### 7. **Error Messages - Clear?** ✅

**Examples:**
- ✅ "Import failed: Missing required column 'Salary'"
- ✅ "Import failed: Invalid salary for Christian McCaffrey: $15000. Must be between $3,000 and $10,000"
- ✅ "Import failed: Invalid position for John Doe: 'K'. Must be QB, RB, WR, TE, or DST"
- ✅ "Import failed: Invalid projection for Patrick Mahomes: -5.2. Must be >= 0"

**All errors are specific and actionable!** ✅

---

### 8. **Success Messages - Clear?** ✅

**Examples:**
- ✅ "153 players imported successfully"
- ✅ "267 players imported successfully. 3 players skipped (low confidence matches)" [Review button]

**Messages are clear and actionable!** ✅

---

### 9. **Performance - Achievable?** ✅

**Requirements:**
- ✅ Process 200+ players in <5 seconds
  - Using bulk inserts (SQLAlchemy `bulk_insert_mappings`) ✅
  - Single transaction per import ✅
  
- ✅ Fuzzy matching performance
  - rapidfuzz is fast (thousands of comparisons per second) ✅
  - Only match against existing players (not entire database) ✅

**Performance targets are realistic!** ✅

---

### 10. **Dependencies - Identified?** ✅

**Backend:**
- ✅ PostgreSQL database
- ✅ SQLAlchemy models
- ✅ Alembic migrations
- ✅ pandas + openpyxl
- ✅ rapidfuzz

**Frontend:**
- ✅ Week selector component
- ✅ File input component
- ✅ Toast notification system
- ✅ Loading spinner

**Database:**
- ✅ weeks table (populated)
- ✅ player_pools table (created)
- ✅ historical_stats table (created)
- ✅ historical_stats_backup table (created)
- ✅ player_aliases table (created)
- ⚠️ unmatched_players table (NEW)

**Dependencies identified!** ✅

---

## 🚨 Items to Add Before Writing Spec

### 1. **Unmatched Players Table** (NEW)

```sql
CREATE TABLE unmatched_players (
    id SERIAL PRIMARY KEY,
    import_id UUID NOT NULL,  -- Track which import session
    imported_name VARCHAR(255) NOT NULL,
    team VARCHAR(10) NOT NULL,
    position VARCHAR(10) NOT NULL,
    suggested_player_key VARCHAR(255),  -- Best fuzzy match (if any)
    similarity_score FLOAT,  -- 0-1 similarity
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'mapped', 'ignored'
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unmatched_players_status_check CHECK (status IN ('pending', 'mapped', 'ignored'))
);

CREATE INDEX idx_unmatched_players_import_id ON unmatched_players(import_id);
CREATE INDEX idx_unmatched_players_status ON unmatched_players(status);
```

### 2. **Unmatched Players API Endpoints** (NEW)

```python
# Get unmatched players for review
GET /api/unmatched-players?import_id={uuid}
Response: [
    {
        "id": 1,
        "imported_name": "C. McCaffrey",
        "team": "SF",
        "position": "RB",
        "suggested_player_key": "christian_mccaffrey_SF_RB",
        "similarity_score": 0.82,
        "status": "pending"
    },
    ...
]

# Map unmatched player to alias
POST /api/unmatched-players/map
Body: {
    "unmatched_player_id": 1,
    "canonical_player_key": "christian_mccaffrey_SF_RB"
}
Response: { "success": true, "message": "Alias mapped successfully" }

# Ignore unmatched player
POST /api/unmatched-players/ignore
Body: {
    "unmatched_player_id": 1
}
Response: { "success": true, "message": "Player ignored" }
```

### 3. **Unmatched Players Review Component** (NEW)

**Component:** `UnmatchedPlayersReview.tsx`

**Features:**
- Display list of unmatched players
- Show suggested matches with similarity scores
- "Map to Suggested" button
- "Ignore" button
- "Save Mappings" button (batch save)
- Filter by status (pending, mapped, ignored)

---

## 📋 Final Checklist

### Core Functionality
- ✅ LineStar import flow
- ✅ DraftKings import flow
- ✅ Comprehensive Stats import flow
- ✅ Player name normalization
- ✅ Fuzzy matching (85% threshold)
- ⚠️ **Unmatched player tracking** (NEW - need to add)
- ⚠️ **Post-import review screen** (NEW - need to add)
- ✅ Overwrite behavior
- ✅ Automated backup
- ✅ Data validation (comprehensive)
- ✅ Error handling
- ✅ Success messaging

### Database
- ✅ player_pools table
- ✅ historical_stats table
- ✅ historical_stats_backup table
- ✅ player_aliases table
- ⚠️ **unmatched_players table** (NEW - need to add)

### API Endpoints
- ✅ POST /api/import/linestar
- ✅ POST /api/import/draftkings
- ✅ POST /api/import/nfl-stats
- ⚠️ **GET /api/unmatched-players** (NEW - need to add)
- ⚠️ **POST /api/unmatched-players/map** (NEW - need to add)
- ⚠️ **POST /api/unmatched-players/ignore** (NEW - need to add)

### UI Components
- ✅ Week selector
- ✅ Import Data button
- ✅ File input
- ✅ Loading spinner
- ✅ Toast notifications
- ⚠️ **Unmatched Players Review Screen** (NEW - need to add)

---

## ✅ Final Status

**Spec is 95% complete!**

**Need to add:**
1. ⚠️ Unmatched players table schema
2. ⚠️ Unmatched players API endpoints (3 endpoints)
3. ⚠️ Unmatched players review UI component

**Everything else is solid and ready for implementation!**

---

## 🎯 Recommendation

**Add the unmatched players tracking system to the spec, then we're 100% ready to write the formal specification.**

This is a critical piece for the "skip and review later" workflow you requested.

**Shall I add these 3 items to the requirements document?**

