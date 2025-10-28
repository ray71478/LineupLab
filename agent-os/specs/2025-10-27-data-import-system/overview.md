# Data Import System - Spec Overview

**Created:** October 27, 2025  
**Status:** Shaping  
**Phase:** MVP (Phase 1)

## Feature Description

The Data Import System enables users to upload and parse XLSX files from multiple sources (LineStar, DraftKings, NFL Stats) to populate the player pool and historical data for weekly DFS lineup optimization.

## Key Objectives

1. **Zero-error data import** - 100% success rate for valid XLSX files
2. **Multi-source support** - Handle LineStar, DraftKings (multi-sheet), and NFL Stats formats
3. **Player normalization** - Composite key generation (name_team_position) with fuzzy matching
4. **User feedback** - Clear progress and success/error messages
5. **Data validation** - Validate required columns, data types, and business rules
6. **Overwrite behavior** - Latest upload replaces previous data for the same week

## Scope

### In Scope (MVP)
- Manual XLSX file upload (multipart/form-data)
- LineStar Football WKX.xlsx parsing (single sheet)
- DKSalaries Week X.xlsx parsing (FE, ETR, ITT sheets)
- NFL 2025 Stats.xlsx parsing (comprehensive historical data)
- User-prompted projection/ownership source selection (FE vs ETR)
- Player name normalization with composite keys
- Fuzzy matching for player name variations
- Manual alias mapping UI for low-confidence matches
- Bulk database inserts (200+ players)
- Upload feedback ("153 players imported successfully")
- Automated backup before NFL Stats import (1 previous version)

### Out of Scope (MVP)
- ❌ Automated data fetching (no APIs)
- ❌ Real-time data updates
- ❌ CSV import (XLSX only)
- ❌ Drag-and-drop file upload (use file input)
- ❌ Multiple file upload at once
- ❌ Data export (separate feature)
- ❌ Historical data visualization

## Success Metrics

- ✅ 100% import success rate for valid files
- ✅ Process 200+ players in <5 seconds
- ✅ Zero parsing errors for standard file formats
- ✅ Clear error messages for invalid files
- ✅ Fuzzy matching accuracy >95% (manual mapping <5% of players)

## Technical Approach

**Backend:**
- FastAPI endpoints for each file type
- pandas + openpyxl for XLSX parsing
- SQLAlchemy bulk inserts
- Custom exception handling (DataImportError)
- Transaction-based imports (rollback on failure)

**Frontend:**
- File input with accept=".xlsx"
- Upload progress indicator
- Success/error toast notifications
- Manual alias mapping dialog

**Database:**
- player_pools table (week_id, player_key, source)
- historical_stats table (player_key, week, season)
- player_aliases table (alias_name, canonical_player_key)

## Dependencies

- PostgreSQL database setup
- Week management (week_id must exist)
- SQLAlchemy models defined
- Alembic migrations run

## Next Steps

1. Gather detailed requirements (PHASE 2)
2. Write formal specification
3. Implement backend endpoints
4. Implement frontend components
5. Test with real data files

