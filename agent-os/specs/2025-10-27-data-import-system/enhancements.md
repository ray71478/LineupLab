# Data Import System - MVP Enhancements

**Date:** October 27, 2025  
**Status:** Approved for MVP

---

## 1. Import History & Ownership Tracking

### Purpose
Track ownership and projection changes between imports to identify trends (who's getting chalky, who's fading).

### Database Schema Addition

**Table: `import_history`**
```sql
CREATE TABLE import_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    week_id INTEGER NOT NULL REFERENCES weeks(id),
    source VARCHAR(50) NOT NULL,  -- 'LineStar', 'DraftKings', 'ComprehensiveStats'
    file_name VARCHAR(255),
    player_count INTEGER NOT NULL,
    imported_at TIMESTAMP DEFAULT NOW(),
    import_summary JSONB  -- Store summary stats
);

CREATE INDEX idx_import_history_week_source ON import_history(week_id, source);
CREATE INDEX idx_import_history_imported_at ON import_history(imported_at);
```

**Table: `player_pool_history`** (tracks changes)
```sql
CREATE TABLE player_pool_history (
    id SERIAL PRIMARY KEY,
    import_id UUID NOT NULL REFERENCES import_history(id),
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

### Import Flow Changes

**On Each Import:**
1. Create `import_history` record (generate UUID)
2. Import players to `player_pools` (as normal)
3. Copy snapshot to `player_pool_history` (link to import_id)
4. Compare to previous import (same week, same source)
5. Calculate deltas (ownership changes, projection changes)
6. Display summary in success message

### Success Message Enhancement

**Without Changes (First Import):**
```
153 players imported successfully
```

**With Changes (Subsequent Import):**
```
153 players imported successfully

Changes from last import (2 hours ago):
• 12 ownership changes (avg +2.3%)
• 3 projection changes
• 2 new players added

[View Details]
```

### Change Detail View (Optional - Can Defer to Phase 2)

**Modal/Page showing:**
```
Import Comparison - Week 9 DraftKings
Current: Sunday 11:30 AM (153 players)
Previous: Sunday 10:00 AM (151 players)

Ownership Changes (12 players)
↑ Christian McCaffrey: 42.1% → 45.2% (+3.1%)
↑ Patrick Mahomes: 35.2% → 38.7% (+3.5%)
↑ Travis Kelce: 33.8% → 35.1% (+1.3%)
↓ Lamar Jackson: 28.4% → 26.1% (-2.3%)
...

Projection Changes (3 players)
↑ Lamar Jackson: 24.5 → 26.2 (+1.7 pts)
↓ Tyreek Hill: 16.8 → 15.9 (-0.9 pts)
...

New Players (2)
+ Gabe Davis (JAX, WR) - $5,200, 11.2 proj
+ Tyler Boyd (TEN, WR) - $4,800, 9.8 proj
```

### API Endpoints

**Get Import History:**
```
GET /api/import-history?week_id={week_id}&source={source}

Response:
[
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
    ...
]
```

**Get Import Comparison:**
```
GET /api/import-history/compare?current_id={uuid}&previous_id={uuid}

Response:
{
    "ownership_changes": [
        {
            "player_key": "christian_mccaffrey_SF_RB",
            "name": "Christian McCaffrey",
            "previous_ownership": 0.421,
            "current_ownership": 0.452,
            "delta": 0.031
        },
        ...
    ],
    "projection_changes": [...],
    "new_players": [...],
    "removed_players": [...]
}
```

### UI Components

**Component: `ImportHistoryButton`**
- Location: Near "Import Data" button or in data import section
- Shows count of imports for current week
- Opens import history modal

**Component: `ImportHistoryModal`**
- List of all imports for current week
- Shows timestamp, source, player count
- "View Changes" button for each import (except first)

**Component: `ImportComparisonView`**
- Shows side-by-side comparison
- Ownership changes (sorted by delta)
- Projection changes
- New/removed players

### MVP Implementation Notes

**Must Have:**
- ✅ Store import_history record on each import
- ✅ Store player_pool_history snapshot
- ✅ Calculate basic deltas (ownership/projection changes)
- ✅ Display summary in success message

**Nice to Have (Can Defer):**
- ⏭️ Full comparison view UI (Phase 2)
- ⏭️ Trend visualization (Phase 2)
- ⏭️ Export comparison to CSV (Phase 2)

---

## 2. Smart Defaults & Contextual Warnings

### Purpose
Prevent user errors by detecting potential issues (wrong week, unusual workflow).

### Week Number Detection

**Logic:**
1. Parse filename for week number using regex:
   - `WK(\d+)` → "LineStar_Football_WK8.xlsx" → Week 8
   - `Week (\d+)` → "DKSalaries Week 8.xlsx" → Week 8
   - `throughWeek(\d+)` → "ComprehensiveStats_throughWeek7.xlsx" → Week 7

2. Compare detected week to selected week (from header dropdown)

3. If mismatch, show warning modal BEFORE import starts

### Warning Modal

**Scenario: Week Mismatch**
```
⚠️ Week Mismatch Detected

You selected Week 9, but the filename suggests Week 8:
"DKSalaries Week 8.xlsx"

What would you like to do?

○ Import for Week 8 (change week selector to 8)
○ Continue with Week 9 (filename is incorrect)
○ Cancel import

[Import for Week 8] [Continue with Week 9] [Cancel]
```

**User Actions:**
- **Import for Week 8:** Change week selector to 8, proceed with import
- **Continue with Week 9:** Ignore warning, import to Week 9 as selected
- **Cancel:** Close dialog, no import

### Additional Contextual Checks

**Check 1: Importing LineStar After Wednesday**
```
ℹ️ Import Suggestion

It's Wednesday 2:00 PM. You're importing LineStar data.

DraftKings data is typically available by now and is more accurate.
Have you considered importing DraftKings instead?

[Import LineStar Anyway] [Switch to DraftKings] [Cancel]
```

**Implementation:**
- If day >= Wednesday AND source = LineStar → Show suggestion
- User can proceed with LineStar or switch to DraftKings
- Optional: Add "Don't show this again" checkbox

**Check 2: Multiple Imports Same Day (Optional)**
```
ℹ️ Recent Import Detected

You imported DraftKings data 15 minutes ago.

Are you sure you want to import again?
(Ownership typically updates every 1-2 hours)

[Import Anyway] [Cancel]
```

**Implementation:**
- Check if import exists for same week/source within last 30 minutes
- Show warning (not blocking, just informational)
- Optional: Can defer to Phase 2

### API Changes

**Import Endpoint Enhancement:**
```
POST /api/import/draftkings

Request (multipart/form-data):
- file: XLSX file
- week_id: Integer
- detected_week: Integer (parsed from filename, optional)

Response (if mismatch):
{
    "success": false,
    "warning": "week_mismatch",
    "message": "Filename suggests Week 8, but Week 9 selected",
    "detected_week": 8,
    "selected_week": 9,
    "requires_confirmation": true
}

Response (if confirmed):
{
    "success": true,
    "message": "153 players imported successfully",
    ...
}
```

### UI Flow

**Flow 1: Week Mismatch**
1. User selects Week 9 from header
2. User clicks "Import Data" → "Import DraftKings"
3. User selects "DKSalaries Week 8.xlsx"
4. Frontend parses filename → detects Week 8
5. Frontend compares: 8 ≠ 9 → Show warning modal
6. User chooses action:
   - **Week 8:** Frontend changes week selector to 8, proceeds with import
   - **Week 9:** Frontend sends `confirmed=true` flag, proceeds with import
   - **Cancel:** Close modal, no import

**Flow 2: No Mismatch**
1. User selects Week 9
2. User uploads "DKSalaries Week 9.xlsx"
3. Frontend detects Week 9 → matches selected week
4. Import proceeds immediately (no warning)

### Implementation Notes

**Must Have:**
- ✅ Parse week number from filename (regex)
- ✅ Compare to selected week
- ✅ Show warning modal if mismatch
- ✅ Allow user to change week or continue

**Nice to Have (Can Defer):**
- ⏭️ LineStar timing suggestion (Wednesday check)
- ⏭️ Recent import warning (30-minute check)
- ⏭️ "Don't show again" preference

---

## Implementation Priority

### Phase 1 (MVP - Must Have)
1. ✅ Import history tracking (database tables + basic storage)
2. ✅ Import comparison calculation (deltas in success message)
3. ✅ Week mismatch detection (parse filename + warning modal)

### Phase 2 (Post-MVP - Nice to Have)
4. ⏭️ Full import comparison UI (detailed view)
5. ⏭️ Trend visualization (ownership/projection charts)
6. ⏭️ Timing suggestions (LineStar on Wednesday)
7. ⏭️ Recent import warnings

---

## Database Schema Summary

**New Tables:**
1. `import_history` - Track each import session
2. `player_pool_history` - Snapshot of player data per import
3. `unmatched_players` - Track skipped players (from earlier decision)

**Total New Tables: 3**

---

## API Endpoints Summary

**New Endpoints:**
1. `GET /api/import-history?week_id={id}&source={source}` - Get import history
2. `GET /api/import-history/compare?current_id={uuid}&previous_id={uuid}` - Compare imports
3. `GET /api/unmatched-players?import_id={uuid}` - Get unmatched players
4. `POST /api/unmatched-players/map` - Map alias
5. `POST /api/unmatched-players/ignore` - Ignore player

**Enhanced Endpoints:**
- `POST /api/import/*` - Add week detection and comparison logic

**Total New Endpoints: 5**

---

## UI Components Summary

**New Components:**
1. `ImportHistoryButton` - Show import count, open history
2. `ImportHistoryModal` - List of imports with timestamps
3. `ImportComparisonView` - Detailed comparison (Phase 2)
4. `WeekMismatchWarning` - Modal for week detection
5. `UnmatchedPlayersReview` - Review skipped players

**Total New Components: 5**

---

## Estimated Implementation Time

**Import History:**
- Database tables: 15 min
- Backend logic: 30 min
- Success message enhancement: 15 min
- **Total: 1 hour**

**Week Mismatch Detection:**
- Filename parsing: 15 min
- Warning modal: 20 min
- Frontend logic: 15 min
- **Total: 50 minutes**

**Unmatched Players (from earlier):**
- Database table: 10 min
- API endpoints: 30 min
- Review UI: 45 min
- **Total: 1.5 hours**

**Grand Total: ~3.5 hours additional work for MVP enhancements**

---

## Final Status

✅ **Spec is now 100% complete with approved enhancements!**

Ready to write the formal specification document.

