# Opponent Data Display Verification Checklist

Based on user prompt: "does clicking the 'refresh data' button pull that back? verify that opp data is in that api call. then verify that clicking the button actually calls espn's api. then verify that we are writing to the table anew when that button is clicked. then verify that the table is displaying the db data for opp."

## Checklist

### ✅ 1. Verify clicking "Refresh Data" button calls the refresh endpoint
**Status:** VERIFIED
- **File:** `frontend/src/components/refresh/RefreshMySportsFeedsButton.tsx`
- **Flow:** Button → `handleRefresh()` → `refresh()` from hook → `POST /api/refresh/mysportsfeeds`
- **Evidence:** Line 47-48 calls `refresh()` which calls fetch to `/api/refresh/mysportsfeeds`

### ✅ 2. Verify opponent data is included in the refresh API call/response
**Status:** VERIFIED
- **File:** `backend/routers/refresh_router.py`
- **Response includes:** `espn_opponents: {checked, updated, errors}`
- **Frontend displays:** Success toast shows ESPN Opponents update count (lines 176-184 in RefreshMySportsFeedsButton.tsx)

### ✅ 3. Verify clicking the button actually calls ESPN's API
**Status:** VERIFIED
- **File:** `backend/scheduler/daily_refresh_job.py`
- **Method:** `_refresh_espn_opponents()` (line 398)
- **Calls:** `await self.espn_service.get_opponent_for_team(team, season, week_number)` (line 444-446)
- **ESPN Service:** `backend/services/espn_service.py` → `get_opponent_for_team()` → `fetch_week_schedule()` → ESPN API

### ✅ 4. Verify we are writing opponent data to vegas_lines table when button is clicked
**Status:** VERIFIED (RECENTLY FIXED)
- **File:** `backend/scheduler/daily_refresh_job.py`
- **Method:** `_refresh_espn_opponents()` (lines 451-464)
- **SQL:** `UPDATE vegas_lines SET opponent = :opponent WHERE week_id = :week_id AND team = :team`
- **Fix Applied:** Now updates ALL teams (not just missing ones), always overwrites with ESPN data

### ✅ 5. Verify Smart Score calculation reads opponent from database
**Status:** VERIFIED
- **File:** `backend/services/smart_score_service.py`
- **Method:** `calculate_for_all_players()` (lines 971-1039)
- **Flow:** 
  1. PRIMARY: Calls ESPN API first (lines 976-1004)
  2. FALLBACK: Reads from vegas_lines if ESPN fails (lines 1006-1024)
  3. Uses opponent to calculate matchup history (lines 1026-1039)

### ✅ 6. Verify frontend recalculates Smart Scores after refresh completes
**Status:** FIXED
- **File:** `frontend/src/components/refresh/RefreshMySportsFeedsButton.tsx` & `frontend/src/pages/SmartScorePage.tsx`
- **Fix Applied:** 
  1. Refresh button dispatches `dataRefreshComplete` custom event` after cache invalidation (line 60-62)
  2. SmartScorePage listens to this event and automatically recalculates (lines 140-166)
- **Impact:** Smart Scores now automatically recalculate after refresh, using fresh opponent data

### ❌ 7. Verify historical_stats table has opponent data for matchup history
**Status:** UNKNOWN - NEEDS VERIFICATION
- **Table:** `historical_stats.opponent` column exists
- **Query:** `get_opponent_matchup_history()` filters by `opponent` (line 147 in historical_insights_service.py)
- **Issue:** If `historical_stats.opponent` is NULL for past games, `opponent_matchup_avg` will be None
- **Root Cause:** Even if we have current week opponent from ESPN, past game data might not have opponent

### ⚠️ 8. Verify frontend table is displaying opponent_matchup_avg from database
**Status:** VERIFIED CODE, BUT DATA NOT SHOWING
- **File:** `frontend/src/components/smart-score/SmartScoreTable.tsx`
- **Column:** "vs Opp" (lines 310-324)
- **Displays:** `player.opponent_matchup_avg` - shows "-" if null/undefined
- **Problem:** Data is null - either not calculated or historical_stats.opponent is missing

## ROOT CAUSES IDENTIFIED

### Issue #1: No Auto-Recalculate After Refresh
- **Problem:** Refresh invalidates cache but doesn't trigger Smart Score recalculation
- **Fix Needed:** Trigger recalculation in `handleImportSuccess` callback or add to refresh button

### Issue #2: Historical Stats May Not Have Opponent Data
- **Problem:** `historical_stats.opponent` might be NULL for past games
- **Impact:** Even with current week opponent, `opponent_matchup_avg` returns None
- **Fix Needed:** Verify data exists, or handle gracefully with message

## RECOMMENDED FIXES

1. **Trigger Smart Score recalculation after refresh**
   - Add recalculation to `handleImportSuccess` in App.tsx
   - Or trigger it from RefreshMySportsFeedsButton after cache invalidation

2. **Verify historical_stats.opponent data exists**
   - Check if past games have opponent data populated
   - If not, we need to backfill or handle gracefully

3. **Add logging/debugging**
   - Log when opponent is found/not found
   - Log when opponent_matchup_avg is calculated vs None
   - Add frontend console logs to see what data is received

