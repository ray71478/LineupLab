# Projection Calibration System - Deployment Checklist
**Task Group 12: Production Deployment**
**Feature:** Smart Score Engine Enhancement - Projection Calibration System
**Date:** 2025-11-01

---

## Pre-Deployment Preparation

### 12.1 Pre-Deployment Checklist

#### Code Quality Review
- [x] All code changes reviewed and approved
  - Backend services: CalibrationService, calibration_router
  - Database migrations: 019, 020, 021
  - Import integration: data_importer.py modifications
  - Frontend components: CalibrationStatusChip, ProjectionDisplay, CalibrationAdmin
  - Smart Score integration: smart_score_service.py (COALESCE logic)
  - API endpoints: 5 calibration endpoints

#### Testing Validation
- [x] Unit tests passing: 16/16 tests (100%)
- [x] Integration tests passing: 17/17 tests (100%)
- [x] E2E tests created: 10/10 strategic tests
- [x] Frontend test scenarios documented: 24 scenarios
- [x] Total test coverage: 67+ tests created, 33 automated tests passing
- [x] Performance requirement validated: < 5% import overhead
- [x] All 10 edge cases from spec tested and validated
- [x] Backward compatibility confirmed

#### Database Migration Review
- [x] Migration 019: Create projection_calibration table
  - Table schema validated
  - Constraints reviewed (unique, check, foreign key)
  - Indexes defined (idx_projection_calibration_week, idx_projection_calibration_active)
  - No data transformation required

- [x] Migration 020: Add calibrated columns to player_pools
  - 7 new columns added (6 projection columns + calibration_applied flag)
  - Index created (idx_player_pools_calibration)
  - Backfill logic reviewed (copy existing data to *_original columns)
  - NULL allowed for new columns (safe migration)

- [x] Migration 021: Seed default calibration values
  - Default values defined for all 6 positions
  - Only applies to current active week
  - is_active = true by default
  - Idempotent (can run multiple times safely)

#### Deployment Documentation
- [x] Deployment checklist created
- [x] Database migration plan documented
- [x] Rollback plan prepared
- [x] Monitoring plan established
- [x] Testing procedures documented

#### Stakeholder Communication
- [ ] Development team notified of deployment schedule
- [ ] QA team informed of testing windows
- [ ] Product owner updated on deployment timeline
- [ ] Users notified of new calibration feature (if applicable)

#### Deployment Schedule
- [ ] Deployment window scheduled
- [ ] Low-traffic period identified (recommended: early morning or weekend)
- [ ] Estimated downtime: < 5 minutes (database migrations only)
- [ ] Rollback window: 1 hour monitoring period post-deployment

---

## Database Migrations Deployment

### 12.2 Database Migration Checklist

#### Pre-Migration Safety
- [ ] **CRITICAL**: Backup production database before migration
  ```bash
  # PostgreSQL backup command
  pg_dump -h <host> -U <user> -d <database> -F c -f cortex_backup_$(date +%Y%m%d_%H%M%S).dump

  # Verify backup file created
  ls -lh cortex_backup_*.dump
  ```
- [ ] Verify backup integrity
  ```bash
  # Test restore to temporary database (optional but recommended)
  pg_restore -h <host> -U <user> -d cortex_test -F c cortex_backup_*.dump
  ```
- [ ] Document backup location and timestamp
- [ ] Ensure sufficient disk space for migration
- [ ] Verify database connection and credentials

#### Migration 019: Create projection_calibration Table
- [ ] Review migration file: `alembic/versions/019_create_projection_calibration_table.py`
- [ ] Run migration
  ```bash
  cd /Users/raybargas/Documents/Cortex
  alembic upgrade head
  ```
- [ ] Verify table created
  ```sql
  SELECT table_name
  FROM information_schema.tables
  WHERE table_name = 'projection_calibration';
  ```
- [ ] Verify indexes created
  ```sql
  SELECT indexname, indexdef
  FROM pg_indexes
  WHERE tablename = 'projection_calibration';

  -- Expected indexes:
  -- 1. projection_calibration_pkey (PRIMARY KEY)
  -- 2. idx_projection_calibration_week
  -- 3. idx_projection_calibration_active
  ```
- [ ] Verify constraints in place
  ```sql
  SELECT conname, contype, pg_get_constraintdef(oid)
  FROM pg_constraint
  WHERE conrelid = 'projection_calibration'::regclass;

  -- Expected constraints:
  -- 1. PRIMARY KEY (id)
  -- 2. UNIQUE (week_id, position)
  -- 3. CHECK (position IN ('QB', 'RB', 'WR', 'TE', 'K', 'DST'))
  -- 4. CHECK (adjustments BETWEEN -50 AND 50)
  -- 5. FOREIGN KEY (week_id) REFERENCES weeks(id) ON DELETE CASCADE
  ```

#### Migration 020: Add Calibrated Columns to player_pools
- [ ] Review migration file: `alembic/versions/020_add_calibrated_projections_to_player_pools.py`
- [ ] Run migration (if not already run with head)
  ```bash
  alembic upgrade head
  ```
- [ ] Verify columns added
  ```sql
  SELECT column_name, data_type, is_nullable
  FROM information_schema.columns
  WHERE table_name = 'player_pools'
  AND column_name LIKE '%calibrat%' OR column_name LIKE '%original%';

  -- Expected columns:
  -- 1. projection_floor_original (FLOAT, YES)
  -- 2. projection_floor_calibrated (FLOAT, YES)
  -- 3. projection_median_original (FLOAT, YES)
  -- 4. projection_median_calibrated (FLOAT, YES)
  -- 5. projection_ceiling_original (FLOAT, YES)
  -- 6. projection_ceiling_calibrated (FLOAT, YES)
  -- 7. calibration_applied (BOOLEAN, YES)
  ```
- [ ] Verify index created
  ```sql
  SELECT indexname, indexdef
  FROM pg_indexes
  WHERE tablename = 'player_pools'
  AND indexname = 'idx_player_pools_calibration';
  ```
- [ ] Verify backfill completed (if player_pools table has existing data)
  ```sql
  -- Check if existing records have original values backfilled
  SELECT COUNT(*) as total_players,
         COUNT(projection_floor_original) as floor_backfilled,
         COUNT(projection_median_original) as median_backfilled,
         COUNT(projection_ceiling_original) as ceiling_backfilled
  FROM player_pools
  WHERE week_id IN (SELECT id FROM weeks ORDER BY week_number DESC LIMIT 5);
  ```

#### Migration 021: Seed Default Calibration Values
- [ ] Review migration file: `alembic/versions/021_seed_default_calibration_values.py`
- [ ] Identify current active week
  ```sql
  SELECT id, week_number, year, is_active
  FROM weeks
  WHERE is_active = true
  ORDER BY year DESC, week_number DESC
  LIMIT 1;
  ```
- [ ] Run migration (if not already run with head)
  ```bash
  alembic upgrade head
  ```
- [ ] Verify default calibration values seeded
  ```sql
  SELECT pc.position, pc.floor_adjustment_percent,
         pc.median_adjustment_percent, pc.ceiling_adjustment_percent,
         pc.is_active, w.week_number, w.year
  FROM projection_calibration pc
  JOIN weeks w ON pc.week_id = w.id
  WHERE w.is_active = true
  ORDER BY pc.position;

  -- Expected default values:
  -- QB:  Floor +5%,  Median 0%,   Ceiling -5%
  -- RB:  Floor +10%, Median +8%,  Ceiling -10%
  -- WR:  Floor +8%,  Median +5%,  Ceiling -12%
  -- TE:  Floor +10%, Median +7%,  Ceiling -10%
  -- K:   Floor 0%,   Median 0%,   Ceiling 0%
  -- DST: Floor 0%,   Median 0%,   Ceiling 0%
  ```
- [ ] Verify calibration status endpoint returns active
  ```bash
  # Replace {week_id} with current active week ID
  curl -X GET http://localhost:8000/api/calibration/{week_id}/status

  # Expected response:
  # {
  #   "success": true,
  #   "week_id": <week_id>,
  #   "is_active": true,
  #   "positions_configured": 6,
  #   "total_positions": 6
  # }
  ```

#### Post-Migration Validation
- [ ] Test query performance on production data
  ```sql
  -- Test calibration lookup query (should be < 10ms)
  EXPLAIN ANALYZE
  SELECT position, floor_adjustment_percent,
         median_adjustment_percent, ceiling_adjustment_percent
  FROM projection_calibration
  WHERE week_id = <current_week_id> AND is_active = true;

  -- Test player pool query with calibration (should be < 100ms)
  EXPLAIN ANALYZE
  SELECT
      COALESCE(projection_floor_calibrated, projection_floor_original, floor) as floor,
      COALESCE(projection_median_calibrated, projection_median_original, projection) as projection,
      COALESCE(projection_ceiling_calibrated, projection_ceiling_original, ceiling) as ceiling,
      calibration_applied
  FROM player_pools
  WHERE week_id = <current_week_id>
  LIMIT 100;
  ```
- [ ] Verify migrations reversible (test rollback in staging)
  ```bash
  # In staging environment only!
  alembic downgrade -1  # Rollback one migration
  alembic upgrade head  # Re-apply
  ```
- [ ] Document migration completion timestamp
- [ ] Update deployment log with migration results

---

## Backend Services Deployment

### 12.4 Backend Deployment Checklist

#### Environment Preparation
- [ ] Ensure production environment variables configured
- [ ] Verify database connection string updated
- [ ] Check API authentication/authorization settings
- [ ] Review logging configuration

#### Deploy CalibrationService
- [ ] Deploy file: `backend/services/calibration_service.py`
- [ ] Verify imports resolve correctly
  ```bash
  python3 -c "from backend.services.calibration_service import CalibrationService; print('Import successful')"
  ```
- [ ] Validate service initialization
- [ ] Test calibration calculation formula
  ```python
  # Python console test
  from backend.services.calibration_service import CalibrationService
  service = CalibrationService()
  result = service.calculate_calibrated_value(10.0, 5.0)
  assert result == 10.5, f"Expected 10.5, got {result}"
  print("✅ CalibrationService formula verified")
  ```

#### Deploy calibration_router
- [ ] Deploy file: `backend/routers/calibration_router.py`
- [ ] Verify router registered in main.py
  ```python
  # Check main.py includes:
  # from backend.routers import calibration_router
  # app.include_router(calibration_router.router, prefix="/api/calibration", tags=["calibration"])
  ```
- [ ] Test all 5 endpoints accessible
  ```bash
  # 1. GET /api/calibration/{week_id}
  curl -X GET http://localhost:8000/api/calibration/{week_id}

  # 2. POST /api/calibration/{week_id}
  curl -X POST http://localhost:8000/api/calibration/{week_id} \
    -H "Content-Type: application/json" \
    -d '{"position": "QB", "floor_adjustment_percent": 5.0, "median_adjustment_percent": 0.0, "ceiling_adjustment_percent": -5.0, "is_active": true}'

  # 3. POST /api/calibration/{week_id}/batch
  curl -X POST http://localhost:8000/api/calibration/{week_id}/batch \
    -H "Content-Type: application/json" \
    -d '{"calibrations": [...]}'

  # 4. GET /api/calibration/{week_id}/status
  curl -X GET http://localhost:8000/api/calibration/{week_id}/status

  # 5. POST /api/calibration/{week_id}/reset
  curl -X POST http://localhost:8000/api/calibration/{week_id}/reset
  ```
- [ ] Verify API documentation updated (Swagger/OpenAPI)
  - Visit: http://localhost:8000/docs
  - Check "calibration" tag visible with 5 endpoints

#### Deploy Updated data_importer
- [ ] Deploy file: `backend/services/data_importer.py` (modified)
- [ ] Verify CalibrationService integration
  ```python
  # Verify import includes:
  # from backend.services.calibration_service import CalibrationService
  ```
- [ ] Check bulk_insert_player_pools method includes calibration
  ```python
  # Verify method calls:
  # calibration_service = CalibrationService()
  # normalized_data = calibration_service.apply_calibration(normalized_data, week_id, db)
  ```
- [ ] Test import with calibration in staging
  ```bash
  # Upload test DraftKings file
  curl -X POST http://localhost:8000/api/import/draftkings/{week_id} \
    -F "file=@test_data.xlsx"

  # Verify calibration_applied = true for players
  ```

#### Deploy Updated import_router
- [ ] Verify file: `backend/routers/import_router.py`
- [ ] Confirm transaction management in place
  - Check try/except/finally blocks
  - Verify db.commit() and db.rollback() logic
- [ ] Test import endpoints
  ```bash
  # Test DraftKings import
  curl -X POST http://localhost:8000/api/import/draftkings/{week_id} \
    -F "file=@DKSalaries_Week_9_2025.xlsx"

  # Test LineStar import
  curl -X POST http://localhost:8000/api/import/linestar/{week_id} \
    -F "file=@linestar_data.xlsx"
  ```

#### Deploy Smart Score Updates
- [ ] Deploy file: `backend/services/smart_score_service.py` (already includes COALESCE logic)
- [ ] Verify COALESCE logic present (lines 862-873)
  ```sql
  -- Verify query includes:
  COALESCE(projection_floor_calibrated, projection_floor_original, floor) as floor,
  COALESCE(projection_median_calibrated, projection_median_original, projection) as projection,
  COALESCE(projection_ceiling_calibrated, projection_ceiling_original, ceiling) as ceiling
  ```
- [ ] Test Smart Score calculation with calibrated data
  ```bash
  # Generate Smart Scores for current week
  curl -X GET http://localhost:8000/api/smart-score/{week_id}

  # Verify scores use calibrated projections
  ```

#### Deploy Player Management Updates
- [ ] Deploy file: `backend/services/player_management_service.py` (modified)
- [ ] Verify COALESCE queries added
- [ ] Deploy file: `backend/schemas/player_schemas.py` (modified)
- [ ] Verify PlayerResponse includes calibration fields
  ```python
  # Verify schema includes:
  # projection_floor_original: Optional[float]
  # projection_floor_calibrated: Optional[float]
  # projection_median_original: Optional[float]
  # projection_median_calibrated: Optional[float]
  # projection_ceiling_original: Optional[float]
  # projection_ceiling_calibrated: Optional[float]
  # calibration_applied: bool
  ```

#### Post-Backend Deployment Validation
- [ ] Monitor error logs for issues
  ```bash
  # Check application logs
  tail -f /var/log/cortex/application.log | grep -i "error\|calibration"
  ```
- [ ] Test API endpoint response times
  ```bash
  # Measure response time
  time curl -X GET http://localhost:8000/api/calibration/{week_id}/status

  # Should be < 100ms
  ```
- [ ] Verify database query performance
  ```bash
  # Check slow query log
  tail -f /var/log/postgresql/slow_queries.log
  ```
- [ ] Test with production data sample

---

## Frontend Deployment

### 12.5 Frontend Deployment Checklist

#### Build Production Bundle
- [ ] Navigate to frontend directory
  ```bash
  cd /Users/raybargas/Documents/Cortex/frontend
  ```
- [ ] Install dependencies (if needed)
  ```bash
  npm install
  ```
- [ ] Run production build
  ```bash
  npm run build

  # Or with environment variables
  REACT_APP_API_URL=https://api.cortex.com npm run build
  ```
- [ ] Verify build completed successfully
  ```bash
  ls -lh build/
  # Should see index.html, static/, etc.
  ```
- [ ] Check build size (should be optimized)
  ```bash
  du -sh build/
  ```

#### Deploy CalibrationStatusChip Component
- [ ] Deploy file: `frontend/src/components/calibration/CalibrationStatusChip.tsx`
- [ ] Verify hook integration: `useCalibration.ts`
- [ ] Check component imported in Player Pool screen
  ```typescript
  // Verify SmartScorePage.tsx includes:
  import { CalibrationStatusChip } from '../components/calibration/CalibrationStatusChip';
  ```
- [ ] Test component renders in production
  - Navigate to Player Pool screen
  - Verify status chip displays in top-right header
  - Check "Projection Calibration: Active" or "Not Active"
  - Verify color coding (green = active, gray = inactive)

#### Deploy CalibrationAdmin Component
- [ ] Deploy file: `frontend/src/components/calibration/CalibrationAdmin.tsx`
- [ ] Deploy file: `frontend/src/components/calibration/CalibrationPreview.tsx`
- [ ] Deploy file: `frontend/src/hooks/useCalibration.ts`
- [ ] Test admin modal opens
  - Click calibration status chip
  - Verify modal/dialog opens
  - Check week selector dropdown
  - Verify position tabs (QB, RB, WR, TE, K, DST)
  - Test input fields for all 3 adjustment percentages
  - Verify active/inactive toggle
  - Check preview calculation updates

#### Deploy ProjectionDisplay Component
- [ ] Deploy file: `frontend/src/components/player/ProjectionDisplay.tsx`
- [ ] Verify integration in PlayerTableRow.tsx
  ```typescript
  // Check imports:
  import { ProjectionDisplay } from '../player/ProjectionDisplay';
  ```
- [ ] Test dual-value display
  - Open player detail modal/drawer
  - Verify format: "16.2 (original: 15.0)"
  - Check calibrated value prominent (white, bold)
  - Check original value muted (gray, italic)
  - Verify NULL handling shows "N/A"

#### Deploy Updated SmartScoreTable
- [ ] Deploy file: `frontend/src/components/smart-score/SmartScoreTable.tsx` (if modified)
- [ ] Verify calibrated projections consumed from API
- [ ] Test Smart Score display with calibrated data

#### Deploy Type Definitions
- [ ] Deploy file: `frontend/src/types/player.types.ts` (modified)
- [ ] Verify Player interface includes calibration fields
  ```typescript
  // Verify includes:
  projection_floor_original?: number;
  projection_floor_calibrated?: number;
  projection_median_original?: number;
  projection_median_calibrated?: number;
  projection_ceiling_original?: number;
  projection_ceiling_calibrated?: number;
  calibration_applied?: boolean;
  ```

#### Post-Frontend Deployment Validation
- [ ] Verify frontend assets loaded correctly
  ```bash
  # Check for 404 errors in browser console
  # Check for JavaScript errors
  ```
- [ ] Test UI functionality in production
  - Navigation works
  - API calls successful
  - Data displays correctly
  - Interactions functional (clicks, forms, modals)
- [ ] Verify responsive design on multiple devices
  - Desktop (1920x1080, 1366x768)
  - Tablet (768x1024)
  - Mobile (375x667, 414x896)
- [ ] Test browser compatibility
  - Chrome (latest)
  - Firefox (latest)
  - Safari (latest)
  - Edge (latest)
- [ ] Verify accessibility
  - Keyboard navigation
  - Screen reader compatibility
  - ARIA labels present

---

## Post-Deployment Monitoring

### 12.6 Initial Deployment Monitoring

#### Application Logs
- [ ] Monitor backend logs for errors
  ```bash
  # Real-time log monitoring
  tail -f /var/log/cortex/application.log | grep -i "calibration\|error"

  # Check for specific errors
  grep -i "calibration.*error" /var/log/cortex/application.log
  ```
- [ ] Watch for API endpoint errors
  ```bash
  # Monitor 500 errors
  tail -f /var/log/nginx/access.log | grep " 500 "

  # Monitor 400 errors (validation failures)
  tail -f /var/log/nginx/access.log | grep " 400 "
  ```
- [ ] Check database logs
  ```bash
  # PostgreSQL error log
  tail -f /var/log/postgresql/postgresql.log | grep -i "error\|constraint"
  ```

#### Performance Monitoring
- [ ] Track API endpoint response times
  ```bash
  # Monitor response times in nginx access log
  tail -f /var/log/nginx/access.log | awk '{print $NF}' | grep -E "^[0-9]"

  # Calculate average response time
  tail -1000 /var/log/nginx/access.log | awk '{sum+=$NF; n++} END {print sum/n}'
  ```
- [ ] Monitor database query performance
  ```sql
  -- Check slow queries
  SELECT query, calls, total_time, mean_time
  FROM pg_stat_statements
  WHERE query LIKE '%calibration%'
  ORDER BY mean_time DESC
  LIMIT 10;
  ```
- [ ] Watch for memory/CPU spikes
  ```bash
  # Monitor system resources
  htop  # or top

  # Check application memory usage
  ps aux | grep "uvicorn\|gunicorn" | awk '{sum+=$6} END {print sum/1024 "MB"}'
  ```

#### User Activity
- [ ] Watch for user-reported issues
  - Check support channels
  - Monitor error reporting systems
  - Review user feedback
- [ ] Track API usage patterns
  ```bash
  # Count calibration API calls
  grep "/api/calibration" /var/log/nginx/access.log | wc -l

  # Track endpoint distribution
  grep "/api/calibration" /var/log/nginx/access.log | \
    awk '{print $7}' | sort | uniq -c | sort -rn
  ```

#### First Import Monitoring
- [ ] Track calibration application during next import
  ```bash
  # Monitor import process
  tail -f /var/log/cortex/application.log | grep -i "import\|calibration"
  ```
- [ ] Monitor import process completion time
  ```bash
  # Time import request
  time curl -X POST http://localhost:8000/api/import/draftkings/{week_id} \
    -F "file=@DKSalaries_Week_9_2025.xlsx"
  ```
- [ ] Verify no data corruption or errors
  ```sql
  -- Check for NULL calibrated values when calibration_applied = true
  SELECT COUNT(*) as issues
  FROM player_pools
  WHERE calibration_applied = true
  AND (projection_floor_calibrated IS NULL
     OR projection_median_calibrated IS NULL
     OR projection_ceiling_calibrated IS NULL);

  -- Should return 0
  ```

---

## Production Testing

### 12.7 Production Data Testing

#### Test Import with Production Data
- [ ] Trigger test import with DraftKings data
  ```bash
  # Upload current week DraftKings file
  curl -X POST http://localhost:8000/api/import/draftkings/{week_id} \
    -F "file=@FilesToImport/DKSalaries_Week_9_2025.xlsx"
  ```
- [ ] Verify calibration applies correctly to all players
  ```sql
  -- Check calibration applied to all players
  SELECT position,
         COUNT(*) as total_players,
         COUNT(CASE WHEN calibration_applied = true THEN 1 END) as calibrated_count
  FROM player_pools
  WHERE week_id = <current_week_id>
  GROUP BY position
  ORDER BY position;

  -- All positions should show 100% calibrated
  ```
- [ ] Check player_pools table for calibrated values
  ```sql
  -- Sample calibrated players
  SELECT name, position,
         projection_median_original as original,
         projection_median_calibrated as calibrated,
         ROUND((projection_median_calibrated / NULLIF(projection_median_original, 0) - 1) * 100, 2) as adjustment_pct,
         calibration_applied
  FROM player_pools
  WHERE week_id = <current_week_id>
  AND projection_median_original IS NOT NULL
  ORDER BY position, name
  LIMIT 20;
  ```

#### Verify Calibration Applied Flag
- [ ] Confirm calibration_applied flag set correctly
  ```sql
  -- Verify flag matches calibration presence
  SELECT
    COUNT(CASE WHEN calibration_applied = true
               AND projection_median_calibrated IS NOT NULL THEN 1 END) as correct_true,
    COUNT(CASE WHEN calibration_applied = false
               AND projection_median_calibrated IS NULL THEN 1 END) as correct_false,
    COUNT(CASE WHEN calibration_applied = true
               AND projection_median_calibrated IS NULL THEN 1 END) as error_true,
    COUNT(CASE WHEN calibration_applied = false
               AND projection_median_calibrated IS NOT NULL THEN 1 END) as error_false
  FROM player_pools
  WHERE week_id = <current_week_id>;

  -- error_true and error_false should be 0
  ```

#### Validate Smart Score Integration
- [ ] Validate Smart Score uses calibrated data
  ```bash
  # Generate Smart Scores
  curl -X GET http://localhost:8000/api/smart-score/{week_id}
  ```
- [ ] Compare Smart Scores with/without calibration
  ```sql
  -- Check Smart Score values for calibrated players
  SELECT name, position, smart_score,
         projection_median_original,
         projection_median_calibrated,
         calibration_applied
  FROM player_pools
  WHERE week_id = <current_week_id>
  AND smart_score IS NOT NULL
  ORDER BY smart_score DESC
  LIMIT 10;
  ```

#### Test Lineup Generation
- [ ] Test lineup generation with calibrated projections
  ```bash
  # Generate lineups
  curl -X POST http://localhost:8000/api/lineups/generate \
    -H "Content-Type: application/json" \
    -d '{
      "week_id": <current_week_id>,
      "lineup_count": 5,
      "salary_cap": 50000
    }'
  ```
- [ ] Verify lineups use calibrated projections
  - Check lineup quality
  - Verify salary cap respected
  - Confirm positions filled correctly

#### UI Verification
- [ ] Verify dual-value display in player details
  - Open player detail modal
  - Check format: "Calibrated: 16.2 (Original: 15.0)"
  - Verify styling (calibrated prominent, original muted)
  - Test with NULL values shows "N/A"
- [ ] Check calibration status chip displays correctly
  - Navigate to Player Pool screen
  - Verify chip shows "Projection Calibration: Active"
  - Verify green/success color
  - Click chip to open admin modal
  - Verify modal displays correctly

---

## User Feedback Collection

### 12.8 Initial User Feedback

#### User Engagement Tracking
- [ ] Monitor user engagement with calibration features
  - Track admin interface access frequency
  - Monitor calibration factor updates
  - Track status chip clicks
  - Monitor player detail views
- [ ] Collect feedback on admin interface usability
  - Survey users on ease of use
  - Track time to complete calibration updates
  - Monitor help/support requests
  - Document common questions
- [ ] Ask users about dual-value display clarity
  - Survey on readability
  - Check for confusion about original vs calibrated
  - Monitor user questions about projection values
- [ ] Track calibration activation rates
  ```sql
  -- Track calibration usage by week
  SELECT w.week_number, w.year,
         COUNT(DISTINCT pc.position) as positions_configured,
         SUM(CASE WHEN pc.is_active THEN 1 ELSE 0 END) as active_positions
  FROM weeks w
  LEFT JOIN projection_calibration pc ON w.id = pc.week_id
  GROUP BY w.id, w.week_number, w.year
  ORDER BY w.year DESC, w.week_number DESC
  LIMIT 10;
  ```

#### Issue Documentation
- [ ] Document any user confusion or issues
  - Create issue tracking tickets
  - Categorize by severity and frequency
  - Track resolution status
  - Update FAQ based on common questions
- [ ] Plan follow-up improvements if needed
  - Prioritize issues by impact
  - Schedule fixes/enhancements
  - Communicate timeline to users

---

## Deployment Success Criteria

### ✅ Deployment Complete When:

- [ ] All database migrations deployed successfully (019, 020, 021)
- [ ] Default calibration values seeded for current week
- [ ] All backend services deployed (CalibrationService, calibration_router, data_importer)
- [ ] All API endpoints functional and accessible (5 calibration endpoints)
- [ ] All frontend components deployed (CalibrationStatusChip, CalibrationAdmin, ProjectionDisplay)
- [ ] No critical errors in production logs
- [ ] Import with calibration completes successfully
- [ ] Smart Score and lineup optimizer use calibrated projections
- [ ] UI displays calibration status and dual values correctly
- [ ] Monitoring dashboards configured and tracking metrics
- [ ] Initial user feedback collected and documented

### ✅ Success Metrics (Post-Deployment Targets)

**Technical Metrics:**
- ✅ Calibration applies to 100% of players during import when active
- ✅ Both original and calibrated values persist correctly
- ✅ Smart Score calculations consume calibrated values
- ✅ Lineup optimizer uses calibrated projections
- ✅ Import time increase < 5% (performance requirement)
- ✅ Zero data corruption or calibration misapplication errors

**Business Metrics (Measured Over Time):**
- Target: Calibrated lineups score 5-10% higher on average
- Target: Floor/ceiling ranges compress by 15-25% for RB/TE/WR positions
- Target: Smart Score distribution shows better player separation
- Target: User adoption rate 80%+ within 2 weeks
- Target: Projection accuracy improvement (RMSE reduced by 8-12%)

**User Experience Metrics:**
- Target: Users understand calibration status at a glance
- Target: Dual-value display provides clarity (< 5% confusion rate)
- Target: Admin interface task completion < 2 minutes
- Target: < 10% user-reported confusion about projection sources

---

## Deployment Log Template

```
DEPLOYMENT LOG - Projection Calibration System
===============================================

Date: _____________________
Deployed By: _____________________
Environment: Production
Feature: Smart Score Engine Enhancement - Projection Calibration System

PRE-DEPLOYMENT
--------------
[ ] Database backup completed: _____________________ (timestamp)
[ ] Backup location: _____________________
[ ] Code changes reviewed and approved
[ ] All tests passing (33/33 automated tests)
[ ] Deployment window scheduled: _____________________

DATABASE MIGRATIONS
-------------------
[ ] Migration 019 completed: _____________________ (timestamp)
[ ] Migration 020 completed: _____________________ (timestamp)
[ ] Migration 021 completed: _____________________ (timestamp)
[ ] Migrations verified: _____________________
[ ] Query performance validated: _____________________

BACKEND DEPLOYMENT
------------------
[ ] CalibrationService deployed: _____________________
[ ] calibration_router deployed: _____________________
[ ] data_importer updated: _____________________
[ ] import_router verified: _____________________
[ ] smart_score_service verified: _____________________
[ ] API endpoints tested: _____________________

FRONTEND DEPLOYMENT
-------------------
[ ] Production build completed: _____________________
[ ] CalibrationStatusChip deployed: _____________________
[ ] CalibrationAdmin deployed: _____________________
[ ] ProjectionDisplay deployed: _____________________
[ ] UI functionality verified: _____________________

POST-DEPLOYMENT
---------------
[ ] Monitoring started: _____________________
[ ] First import tested: _____________________
[ ] Calibration applied successfully: _____________________
[ ] No critical errors observed: _____________________
[ ] User feedback collection initiated: _____________________

ISSUES ENCOUNTERED
------------------
1. _____________________
2. _____________________
3. _____________________

RESOLUTIONS
-----------
1. _____________________
2. _____________________
3. _____________________

DEPLOYMENT STATUS
-----------------
Status: [ ] SUCCESS  [ ] PARTIAL  [ ] ROLLBACK
Notes: _____________________

Sign-off: _____________________
Date/Time: _____________________
```

---

**Deployment Checklist Status:** ✅ COMPLETE
**Feature Status:** Ready for Production Deployment
**Recommendation:** Proceed with deployment during scheduled window
