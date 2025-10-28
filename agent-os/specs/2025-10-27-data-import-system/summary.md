# Data Import System - Spec Shaping Summary

**Created:** October 27, 2025  
**Status:** ✅ Complete - Ready for Specification Writing

---

## What We're Building

A zero-error data import system that allows users to upload XLSX files from three sources (LineStar, DraftKings, Comprehensive Stats) to populate player pools and historical data for DFS lineup optimization.

---

## Key Decisions Made

### 1. **Upload Flow**
- Single "Import Data" button in main navigation
- Opens menu with 3 options: LineStar, DraftKings, Season Stats
- Week selector in header (always visible, sets global context)
- No preview, no confirmation dialogs - immediate import

### 2. **File Handling**
- **LineStar:** First sheet only, standard column mapping
- **DraftKings:** FE sheet only (no user prompt), skip row 1, use row 2 as header
- **DraftKings ITT:** Skip for MVP (proper Vegas tracking in Phase 2 with API)
- **Comprehensive Stats:** "Points" sheet, full replace with automated backup

### 3. **Player Normalization**
- Composite key format: `{normalized_name}_{team}_{position}`
- Remove suffixes (Jr., Sr., III), prefixes (D', O'), all punctuation
- Lowercase, underscores between parts
- Example: "D'Andre Swift Jr." → `dandre_swift_PHI_RB`

### 4. **Fuzzy Matching**
- Threshold: 85% similarity
- Below threshold: Pause import, show manual mapping dialog (one at a time)
- Store aliases in `player_aliases` table for future auto-resolution

### 5. **Overwrite Behavior**
- **LineStar:** Delete week's LineStar data, insert new
- **DraftKings:** Delete ALL week's data (replaces LineStar), insert new
- **Comprehensive Stats:** Delete all historical data (with backup), insert all weeks
- No confirmation dialogs

### 6. **Error Handling**
- Detailed error messages (specific column/issue)
- No partial imports (rollback on error)
- Toast notifications for success/error

### 7. **Success Messages**
- Simple format: "{count} players imported successfully"
- Auto-dismiss after 5 seconds

---

## File Structures Analyzed

### LineStar File
- **Pattern:** `LineStar_Football_WK{X}.xlsx`
- **Sheet:** First sheet (name varies)
- **Rows:** ~505 players
- **Key Columns:** Name, Position, Team, Salary, Projected, Ceiling, Floor, ProjOwn

### DraftKings File
- **Pattern:** `DKSalaries Week {X}.xlsx`
- **Sheet:** FE (skip row 1, use row 2 as header)
- **Rows:** ~174 players
- **Key Columns:** Name, Pos, T, S, Proj, Ceil, Flr, Own, Notes

### Comprehensive Stats File
- **Pattern:** `ComprehensiveStats_throughWeek{X}.xlsx`
- **Sheet:** Points
- **Rows:** ~2,690 player-week records
- **Key Columns:** Player, Tm, Pos, Wk, Snaps, Snp %, Rush/Rec stats, DK Pts, Sal

---

## Technical Approach

### Backend (FastAPI)
- Three endpoints: `/api/import/linestar`, `/api/import/draftkings`, `/api/import/nfl-stats`
- pandas + openpyxl for XLSX parsing
- SQLAlchemy bulk inserts (200+ players in <5 seconds)
- Transaction-based imports (rollback on error)
- Custom exception handling (DataImportError)

### Frontend (React + MUI)
- Week selector in header (Zustand global state)
- "Import Data" button with dropdown menu
- File input (accept=".xlsx")
- Loading spinner during import
- Toast notifications (success/error)
- Manual alias mapping dialog (when needed)

### Database
- `player_pools` - Weekly player data (week_id, player_key, source)
- `historical_stats` - Multi-week performance data (player_key, week, season)
- `historical_stats_backup` - Automated backup (1 previous version)
- `player_aliases` - Name variation mappings (alias_name, canonical_player_key)

---

## Performance Requirements

- ✅ Process 200+ players in <5 seconds
- ✅ 100% import success rate for valid files
- ✅ Zero parsing errors for standard formats
- ✅ Fuzzy matching accuracy >95% (manual mapping <5%)
- ✅ Clear error messages for invalid files

---

## Out of Scope (MVP)

- ❌ Automated data fetching (APIs) - Phase 2
- ❌ Vegas line movement tracking - Phase 2
- ❌ Real-time data updates
- ❌ CSV import (XLSX only)
- ❌ Drag-and-drop upload
- ❌ Multiple file upload at once
- ❌ Data export (separate feature)
- ❌ Historical data visualization

---

## Phase 2 Preview

**Vegas Line Tracking:**
- Hourly API calls for live Vegas data
- Time-series storage (track every fetch)
- Line movement detection (flag 2+ point swings)
- Alert system for significant changes
- Movement visualization in app

---

## Dependencies

**Must be complete before implementation:**
- ✅ PostgreSQL database setup
- ✅ Week management system (weeks table)
- ✅ SQLAlchemy models defined
- ✅ Alembic migrations run
- ✅ Frontend foundation (React + MUI + Zustand)

---

## Files Created

1. `overview.md` - Feature description and scope
2. `file-structures.md` - Detailed file format analysis
3. `requirements.md` - Complete functional requirements
4. `summary.md` - This document

---

## MVP Enhancements Added

### 1. Import History & Ownership Tracking ✅
- Track each import session (import_history table)
- Store player snapshots (player_pool_history table)
- Calculate ownership/projection deltas between imports
- Display changes in success message: "12 ownership changes (avg +2.3%)"
- **Value:** Identify ownership trends, spot chalky plays, make contrarian decisions

### 2. Week Mismatch Detection ✅
- Parse week number from filename (regex: WK8, Week 8, throughWeek7)
- Compare to selected week in header
- Show warning modal if mismatch detected
- Allow user to change week or continue
- **Value:** Prevent importing to wrong week (common user error)

### 3. Unmatched Players Tracking ✅
- Skip low-confidence matches during import (don't block)
- Track skipped players (unmatched_players table)
- Post-import review screen with suggested matches
- Batch mapping more efficient than one-at-a-time dialogs
- **Value:** Fast imports, flexible alias management

---

## Implementation Estimates

**Core Import System:** ~8-10 hours
- Database schema + migrations: 1 hour
- Backend endpoints (3): 3 hours
- Data validation logic: 1.5 hours
- Frontend components: 2.5 hours
- Testing: 2 hours

**MVP Enhancements:** ~3.5 hours
- Import history tracking: 1 hour
- Week mismatch detection: 50 minutes
- Unmatched players system: 1.5 hours

**Total MVP Effort:** ~12-14 hours

---

## Next Steps

1. ✅ Spec shaping complete
2. ✅ MVP enhancements identified and approved
3. ⏭️ Run `/write-spec` to generate formal specification document
4. ⏭️ Implement backend (database + API endpoints)
5. ⏭️ Implement frontend (components + UI)
6. ⏭️ Test with real data files
7. ⏭️ Deploy to local environment

---

**Status:** 100% ready for specification writing! 🚀

