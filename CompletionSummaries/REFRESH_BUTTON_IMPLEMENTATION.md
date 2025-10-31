# Manual MySportsFeeds Refresh Button - Implementation Guide ✅

**Status:** IMPLEMENTED & READY TO USE
**Date:** October 30, 2025
**Commit:** `bb8256a`
**Branch:** `feat-smart-score-api-8f7f7`

---

## Overview

Added a **"Refresh Data"** button to the main header that allows users to manually trigger the MySportsFeeds API data refresh on-demand. This provides immediate access to:
- Current player injury updates
- Latest Vegas Implied Team Total (ITT) for W7 calculations
- Current team defensive rankings for W8 calculations
- Recent player game logs for trend analysis

---

## What Was Implemented

### 1. Backend API Endpoint

**File:** `/backend/routers/refresh_router.py`

**Endpoint:** `POST /api/refresh/mysportsfeeds`

**What it does:**
- Accepts POST request with no parameters
- Instantiates `DailyDataRefreshJob`
- Executes the refresh job asynchronously
- Returns detailed statistics about what was refreshed

**Response (Success):**
```json
{
  "success": true,
  "start_time": "2025-10-30T10:15:00",
  "end_time": "2025-10-30T10:18:45",
  "duration_seconds": 225,
  "injuries": {
    "fetched": 52,
    "stored": 47,
    "errors": 5
  },
  "games": {
    "fetched": 16,
    "stored": 16,
    "errors": 0
  },
  "team_stats": {
    "fetched": 32,
    "stored": 32,
    "errors": 0
  },
  "gamelogs": {
    "fetched": 1200,
    "stored": 1150,
    "errors": 50
  },
  "errors": []
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "MySportsFeeds API key not configured",
  "message": "Please set MYSPORTSFEEDS_TOKEN in your environment."
}
```

**Error Handling:**
- `503 Service Unavailable` - MySportsFeeds token not configured
- `500 Internal Server Error` - Unexpected refresh job failure
- Graceful error messages with troubleshooting hints

---

### 2. Frontend Hook

**File:** `/frontend/src/hooks/useRefreshMySportsFeeds.ts`

**Hook:** `useRefreshMySportsFeeds()`

**Purpose:** Manages API communication and state for the refresh button

**Return Values:**
```typescript
{
  isLoading: boolean,        // True while refresh is in progress
  error: string | null,      // Error message if refresh failed
  success: boolean,          // True if refresh succeeded
  result: RefreshResult,     // Full refresh statistics
  refresh: () => Promise,    // Function to trigger refresh
  reset: () => void          // Function to reset state
}
```

**Features:**
- Uses native fetch API (no axios/extra dependencies)
- Handles loading state automatically
- Captures full refresh results with statistics
- Provides error messages for UI display
- Stateless per-call approach (safe for repeated use)

**Usage Example:**
```typescript
const { isLoading, error, success, result, refresh } = useRefreshMySportsFeeds();

const handleClick = async () => {
  const result = await refresh();
  if (result?.success) {
    console.log(`Updated ${result.games.stored} games`);
  }
};
```

---

### 3. Frontend Button Component

**File:** `/frontend/src/components/refresh/RefreshMySportsFeedsButton.tsx`

**Component:** `RefreshMySportsFeedsButton`

**Location in UI:** Header, between WeekSelector and ImportDataButton

**Visual Properties:**
- **Color:** Orange (#ff4500) - matches theme
- **Hover State:** Darker orange (#e03e00)
- **Disabled State:** Semi-transparent orange when loading
- **Size:** Small/compact to fit header
- **Icon:** Refresh icon from Material-UI

**Button States:**
1. **Ready:** "Refresh Data" with refresh icon
2. **Loading:** "Refreshing..." with spinner
3. **Success:** Shows toast notification with statistics
4. **Error:** Shows error toast with error message

**Toast Notifications:**

**Success Toast:**
```
✅ Data Refresh Complete
Completed in 3m 45s

Updates:
• Injuries: 47 stored, 5 errors
• Vegas Lines: 16 stored, 0 errors
• Defense Stats: 32 stored, 0 errors
• Game Logs: 1150 stored, 50 errors
```

**Error Toast:**
```
❌ Refresh Failed
MySportsFeeds API key not configured

Please set MYSPORTSFEEDS_TOKEN in your environment.
```

**Features:**
- Spinner shows during loading
- Button disabled during refresh (prevents double-clicking)
- Auto-dismissing toasts (success: 6s, error: 8s)
- Detailed statistics in success toast
- Helpful error messages
- Colored toasts (green success, red error)

---

### 4. Integration into App Header

**File:** `/frontend/src/App.tsx`

**Location:** Line 161 in header menuItems

**Header Layout (left to right):**
1. NavigationMenu (Smart Score / Lineups links)
2. WeekSelector (Select NFL week)
3. **RefreshMySportsFeedsButton** ← NEW
4. ImportDataButton (Upload CSV files)

**Code Integration:**
```typescript
<Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
  <NavigationMenu />
  <WeekSelector onWeekChange={undefined} showMetadata={false} />
  <RefreshMySportsFeedsButton onSuccess={...} onError={...} />
  <ImportDataButton onSuccess={...} onError={...} />
</Box>
```

---

## How to Use

### For Users

1. **Click "Refresh Data"** button in the header
   - Location: Top-right area, between "Select Week" and "Import Data"
   - Color: Orange with refresh icon

2. **Wait for refresh to complete**
   - Button shows "Refreshing..." with spinner
   - Takes typically 2-5 minutes depending on data volume

3. **Check the notification**
   - Success: Green toast shows what was updated
   - Error: Red toast shows what went wrong

4. **View updated Smart Scores**
   - Vegas lines (W7) now use real ITT data
   - Defense stats (W8) now use real rankings

### For Developers

**Testing the endpoint:**

```bash
# Manual API test
curl -X POST http://localhost:8000/api/refresh/mysportsfeeds

# Response
{
  "success": true,
  "duration_seconds": 225,
  "injuries": {"fetched": 52, "stored": 47, "errors": 5},
  ...
}
```

**Debugging:**

If "Refresh Data" button doesn't work:
1. Check browser console for errors
2. Verify `/api/refresh/mysportsfeeds` endpoint is registered
3. Check that `MYSPORTSFEEDS_TOKEN` is set in `.env`
4. Check backend logs for refresh job errors

---

## Files Modified

| File | Change | Purpose |
|------|--------|---------|
| `backend/main.py` | Added refresh_router import and registration | Register new endpoint |
| `backend/routers/refresh_router.py` | Created new file | API endpoint for manual refresh |
| `frontend/src/App.tsx` | Added import and button | Integrate button into header |
| `frontend/src/hooks/useRefreshMySportsFeeds.ts` | Created new file | Hook for refresh API calls |
| `frontend/src/components/refresh/RefreshMySportsFeedsButton.tsx` | Created new file | Button UI component |

---

## Summary

✅ **Backend:** Complete API endpoint for manual refresh
✅ **Frontend:** Hook and button component implemented
✅ **Integration:** Button added to header in correct location
✅ **Styling:** Matches existing UI theme (orange #ff4500)
✅ **Notifications:** Success and error toasts with detailed statistics
✅ **Error Handling:** Graceful errors with helpful messages
✅ **Ready for Use:** Can be used immediately

Users can now click the **"Refresh Data"** button in the header to get the latest Vegas lines, injuries, and defense stats whenever they need them - no need to wait for the 5 AM daily refresh!

---

**Status:** ✅ IMPLEMENTED & DEPLOYED
**Date:** October 30, 2025
**Commit:** `bb8256a`
**Branch:** `feat-smart-score-api-8f7f7`
