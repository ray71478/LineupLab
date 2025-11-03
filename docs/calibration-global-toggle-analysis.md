# Projection Calibration Global Toggle - Feasibility Analysis

## Executive Summary

**Complexity Assessment: MEDIUM** ✅

Adding a global toggle to disable calibration is **feasible and moderate in complexity**. The existing architecture already supports this capability - both original and calibrated values are stored. The main work involves:
1. Adding a global setting mechanism
2. Modifying 2 SQL query locations
3. Updating UI components
4. Handling cache invalidation

**Estimated Effort:** 4-6 hours of focused development work

---

## Current Implementation Overview

### Architecture

The calibration system uses a **non-destructive design**:
- **Original values** are always preserved in `projection_*_original` columns
- **Calibrated values** are calculated and stored in `projection_*_calibrated` columns  
- **Both values** coexist in the database
- **COALESCE logic** in SQL queries decides which value to use

### Data Flow

```
1. IMPORT
   LineStar/DraftKings → DataImporter → CalibrationService.apply_calibration()
   → Stores both original + calibrated in player_pools table

2. QUERY  
   SmartScoreService/PlayerManagementService → SQL with COALESCE
   → Returns calibrated if exists, else original

3. CALCULATION
   Smart Score calculation → Uses projections from query
   → No knowledge of calibration - just uses projection values
```

### Current Query Pattern

**Location 1: SmartScoreService (Smart Score calculations)**
```sql
COALESCE(
    projection_median_calibrated,    -- 1st choice: Calibrated
    projection_median_original,      -- 2nd choice: Original  
    projection                        -- 3rd choice: Legacy fallback
) as projection
```

**Location 2: PlayerManagementService (Player listing API)**
```sql
COALESCE(
    p.projection_median_calibrated,
    p.projection_median_original,
    p.projection
) as projection
```

### Current Activation Model

- **Per-position toggle**: Each position (QB, RB, WR, TE, K, DST) has an `is_active` flag
- **Status calculation**: "Active" if ANY position has `is_active = true`
- **No global override**: Position-level toggles are the only control mechanism

---

## Implementation Requirements

### 1. Storage Location (Where to store global setting?)

**Option A: Database Table - `week_settings` or `global_settings`** ⭐ RECOMMENDED
- **Pros:**
  - Persistent across restarts
  - Per-week control (different weeks can have different settings)
  - Easy to query in SQL
  - Can add audit trail (who changed it, when)
- **Cons:**
  - Requires database migration
  - More infrastructure

**Option B: Existing `projection_calibration` table**
- Add `global_enabled` boolean column
- **Pros:**
  - No new table
  - Existing table already week-scoped
- **Cons:**
  - Mixing concerns (calibration config vs. global toggle)
  - Multiple rows per week (one per position) - which row's flag do we check?

**Option C: Environment Variable**
- **Pros:**
  - Simple, no database changes
- **Cons:**
  - Can't change per-week
  - Requires app restart
  - Not user-friendly

**Option D: Frontend localStorage**
- **Pros:**
  - No backend changes
- **Cons:**
  - Per-user, not global
  - Lost on clear cache
  - Doesn't affect calculations (UI-only)

**Recommendation: Option A** - Create a simple `week_settings` table with `week_id`, `calibration_global_enabled` boolean.

---

### 2. Query Modification (Changing COALESCE logic)

**Current Pattern (2 locations):**
```python
# smart_score_service.py line 901
COALESCE(projection_median_calibrated, projection_median_original, projection)

# player_management_service.py line 95  
COALESCE(p.projection_median_calibrated, p.projection_median_original, p.projection)
```

**Modified Pattern (with global toggle check):**
```python
# Option 1: Conditional COALESCE (recommended)
# Query week_settings first, then conditionally use calibrated or original
calibration_enabled = self._check_calibration_global_enabled(week_id)
if calibration_enabled:
    # Use calibrated (current behavior)
    projection_field = "COALESCE(projection_median_calibrated, projection_median_original, projection)"
else:
    # Skip calibrated entirely
    projection_field = "COALESCE(projection_median_original, projection)"

# Option 2: CASE statement in SQL (more complex but single query)
CASE 
    WHEN EXISTS(SELECT 1 FROM week_settings WHERE week_id = :week_id AND calibration_global_enabled = true)
    THEN COALESCE(projection_median_calibrated, projection_median_original, projection)
    ELSE COALESCE(projection_median_original, projection)
END as projection
```

**Files to Modify:**
1. `backend/services/smart_score_service.py` - `calculate_for_all_players()` method
2. `backend/services/player_management_service.py` - `get_players_by_week()` method

**Complexity:** LOW-MEDIUM - Straightforward logic change, but need to ensure consistent behavior

---

### 3. UI Changes

**Status Chip Component (`CalibrationStatusChip.tsx`)**
- Currently shows "Active" if any position is active
- **Change:** Show "Disabled" if global toggle is OFF, regardless of position settings
- **Logic:** `global_enabled = false` → Always show "Not Active"

**Calibration Admin Modal (`CalibrationAdmin.tsx`)**
- Currently has per-position toggles
- **Add:** Global toggle at top of modal (above position tabs)
- **Behavior:** When global toggle OFF, disable all position toggles (gray them out)
- **Visual:** Show clear indication that global override is active

**Complexity:** LOW - Standard React component updates

---

### 4. Cache Invalidation

**Current Caching:**
- Smart Score cache key: `['smart-scores', weekId, mode]` 
- Cache includes calibration in key generation

**When Global Toggle Changes:**
- Invalidate Smart Score cache for that week
- Trigger recalculation of all Smart Scores
- Update React Query cache

**Implementation:**
```typescript
// In CalibrationAdmin after save
await queryClient.invalidateQueries({ 
  queryKey: ['smart-scores', weekId] 
});
```

**Complexity:** LOW - Standard cache invalidation pattern

---

### 5. API Endpoints

**New Endpoint Needed:**
```
PUT /api/calibration/{week_id}/global-toggle
Body: { "enabled": true/false }
```

**Or extend existing:**
```
GET /api/calibration/{week_id}/status
Response: { 
  is_active: boolean,      // Current: position-based
  global_enabled: boolean,  // NEW: global override
  positions_configured: number
}
```

**Complexity:** LOW - Simple CRUD operation

---

## Implementation Approach

### Phase 1: Database Schema
1. Create `week_settings` table with:
   - `week_id` (FK to weeks)
   - `calibration_global_enabled` (boolean, default true for backward compat)
   - `updated_at` timestamp
2. Create Alembic migration
3. Backfill existing weeks with `global_enabled = true` (current behavior)

### Phase 2: Backend Logic
1. Add helper method: `_check_calibration_global_enabled(week_id) -> bool`
2. Modify SmartScoreService query (conditional COALESCE)
3. Modify PlayerManagementService query (conditional COALESCE)
4. Add API endpoint for getting/setting global toggle

### Phase 3: Frontend
1. Update `CalibrationStatusChip` to check global toggle
2. Add global toggle switch to `CalibrationAdmin` modal
3. Add API hook for toggling global setting
4. Implement cache invalidation on toggle

### Phase 4: Testing
1. Test with global ON (should use calibrated)
2. Test with global OFF (should use original)
3. Test per-position toggles with global OFF (should be ignored)
4. Test Smart Score recalculation
5. Test cache invalidation

---

## Complexity Breakdown

| Task | Complexity | Effort | Notes |
|------|-----------|--------|-------|
| Database schema + migration | **LOW** | 30 min | Simple table, straightforward migration |
| Backend query modifications | **MEDIUM** | 1-2 hours | 2 locations, need helper method, test thoroughly |
| API endpoints | **LOW** | 30 min | Standard CRUD, similar to existing calibration API |
| Frontend status chip | **LOW** | 30 min | Check global flag before checking positions |
| Frontend admin modal | **MEDIUM** | 1 hour | Add toggle, disable position toggles when global OFF |
| Cache invalidation | **LOW** | 15 min | Standard React Query pattern |
| Testing | **MEDIUM** | 1-2 hours | Need to test all combinations of global + per-position |
| **TOTAL** | **MEDIUM** | **4-6 hours** | Well-scoped, manageable changes |

---

## Technical Considerations

### 1. Backward Compatibility ✅
- **Current behavior preserved:** Default `global_enabled = true`
- **Existing data works:** COALESCE still works if calibrated values are NULL
- **No breaking changes:** All existing APIs continue to function

### 2. Performance Impact ⚠️
- **Additional query:** Need to check `week_settings` table for each Smart Score calculation
- **Mitigation:** 
  - Cache the global setting per week (in-memory cache)
  - Add index on `week_settings(week_id)`
  - Consider joining in main query (CASE statement approach)

### 3. Interaction with Per-Position Toggles 🤔
**Decision needed:** When global toggle is OFF:
- **Option A:** Ignore position-level toggles entirely (always use original)
- **Option B:** Position toggles still work, but only if global is ON (AND logic)

**Recommendation: Option A** - Global OFF = always use original, regardless of position settings. Simpler and clearer.

### 4. Import Behavior
- **Current:** Calibration is applied during import
- **With global toggle:** Still calculate calibrated values during import, but queries ignore them if global OFF
- **Alternative:** Skip calibration calculation entirely if global OFF
  - **Pros:** Saves computation during import
  - **Cons:** Can't toggle on later without re-import

**Recommendation:** Keep calculating during import (current behavior). The overhead is minimal, and allows instant toggling.

### 5. Smart Score Cache
**Current cache key:** `['smart-scores', weekId, mode]`
**Need to add:** `calibration_global_enabled` to cache key so ON/OFF states don't share cache

**New cache key:** `['smart-scores', weekId, mode, calibrationEnabled]`

---

## Alternative Approaches Considered

### Approach A: Per-Week Global Flag (RECOMMENDED) ✅
- Add `calibration_global_enabled` to `week_settings` table
- **Pros:** 
  - Per-week control
  - Clear separation of concerns
  - Easy to audit changes
- **Cons:**
  - Requires new table/migration

### Approach B: Environment Variable
- Set `CALIBRATION_ENABLED=false` in environment
- **Pros:**
  - Simple, no code changes
- **Cons:**
  - Can't toggle per-week
  - Requires restart
  - Not user-friendly

### Approach C: Skip Calibrated Values in COALESCE
- Just change COALESCE to: `COALESCE(projection_median_original, projection)`
- **Pros:**
  - Simplest code change
- **Cons:**
  - Can't toggle back on without code change
  - No user control
  - Not what user wants

---

## Risk Assessment

### Low Risk ✅
- **Data integrity:** Original values always preserved, no data loss
- **Backward compatibility:** Default ON preserves current behavior
- **Rollback:** Can disable feature by setting all weeks to `global_enabled = false`

### Medium Risk ⚠️
- **Performance:** Additional query per Smart Score calculation (mitigate with caching)
- **Cache invalidation:** Need to ensure Smart Scores recalculate when toggling
- **User confusion:** Need clear UI indication when global toggle overrides position toggles

### Mitigation Strategies
1. **Caching:** Cache global setting lookup per request/session
2. **Clear UI:** Visual indicators in CalibrationAdmin modal
3. **Documentation:** Update user guide explaining global vs. position toggles
4. **Testing:** Comprehensive test coverage for all toggle combinations

---

## Recommended Implementation Plan

### Step 1: Database (30 min)
```sql
CREATE TABLE week_settings (
    week_id INTEGER PRIMARY KEY REFERENCES weeks(id),
    calibration_global_enabled BOOLEAN NOT NULL DEFAULT true,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_week_settings_week ON week_settings(week_id);
```

### Step 2: Backend Service Method (15 min)
```python
def _check_calibration_global_enabled(self, week_id: int) -> bool:
    """Check if calibration is globally enabled for a week."""
    result = self.session.execute(
        text("""
            SELECT calibration_global_enabled 
            FROM week_settings 
            WHERE week_id = :week_id
        """),
        {"week_id": week_id}
    ).scalar()
    
    # Default to True if no setting exists (backward compat)
    return result if result is not None else True
```

### Step 3: Modify Queries (1 hour)
Update 2 query locations to conditionally use calibrated values based on global setting.

### Step 4: API Endpoint (30 min)
Add endpoint to get/set global calibration toggle.

### Step 5: Frontend (1.5 hours)
Update status chip and admin modal.

### Step 6: Testing (1-2 hours)
Test all scenarios.

---

## Conclusion

**Feasibility: HIGH ✅**

This feature is **moderately complex but very feasible**. The architecture already supports it - we just need to change which values are selected. The main challenges are:
1. Deciding where to store the global setting (recommend `week_settings` table)
2. Ensuring consistent behavior across all query locations
3. Clear UI/UX for the toggle interaction

**Estimated Total Time: 4-6 hours** of focused development work, including testing.

**Recommendation:** Proceed with implementation. The benefits (user control, ability to test uncalibrated vs calibrated) outweigh the moderate implementation effort.

