# Specification: Smart Score Engine Enhancement - Projection Calibration System

## Goal
Enhance the Smart Score Engine with position-based projection calibration to improve player pool quality and lineup generation accuracy by adjusting ETR projection floor, median, and ceiling values based on historical accuracy data.

## User Stories
- As a DFS optimizer user, I want calibrated projections applied automatically during data imports so that my player pools reflect more accurate point projections without manual intervention
- As a DFS optimizer user, I want to see both original and calibrated projection values in player detail views so that I can understand how calibration affects specific players
- As a DFS optimizer user, I want to know when calibration is active via a status indicator so that I'm aware when my player pools use calibrated vs original projections
- As a system administrator, I want to configure and manage calibration factors per position through an admin interface so that I can tune projection accuracy based on observed performance
- As a DFS optimizer user, I want the Smart Score and lineup optimizer to use calibrated projections so that player selection and lineup generation are based on the most accurate data available

## Core Requirements

### Projection Calibration System
- Apply position-based calibration (QB, RB, WR, TE, K, DST) with three adjustment factors: Floor %, Median %, Ceiling %
- Automatically apply calibration during weekly DraftKings/LineStar imports when calibration data exists for current week
- Preserve original projection values alongside calibrated values in database
- Do NOT modify DraftKings salary-based projections (only analytical projections like ETR)
- Support sensible default calibration values for each position
- Store calibration profiles per position with ability to modify and save

### Data Management
- Store both original and calibrated values for floor, median, and ceiling projections
- Maintain calibration factors in database per position and week
- Allow calibration profiles to be active or inactive per week
- Track calibration application history and timestamps

### User Interface
- Display calibration status chip on Player Pool screen showing "Projection Calibration: Active" or "Not Active"
- Show both original and calibrated projection values in player pool detail view (not main table)
- Provide admin interface for direct editing of calibration factors per position
- Allow viewing and editing of calibration profiles for current week

### Integration with Existing Systems
- Use calibrated projections in Smart Score calculations when calibration is active
- Feed calibrated projections into lineup optimizer for improved lineup generation
- Integrate calibration application into existing DraftKings import pipeline
- Maintain backward compatibility with existing projection display and filtering

## Visual Design

### Calibration Status Chip (Player Pool Screen Header)
- Position: Top right of Player Pool screen, near week selector
- Format: Chip/badge component (not prominent banner)
- States:
  - "Projection Calibration: Active" (green/success color) - when calibration exists and is active for current week
  - "Projection Calibration: Not Active" (gray/neutral color) - when no calibration or inactive
- Behavior: Click to open calibration management modal

### Player Detail View - Dual Value Display
- Location: Player detail modal/drawer (existing component)
- Display format: Side-by-side or stacked original vs calibrated values
- Example layout:
  ```
  Floor:    5.2 (original: 4.8)
  Median:   12.5 (original: 11.8)
  Ceiling:  22.1 (original: 24.3)
  ```
- Styling: Calibrated value prominent, original value muted/secondary text
- Only show dual values when calibration is active; otherwise show single value

### Admin Interface - Calibration Management
- Access: Settings or Admin section of application
- Components:
  - Week selector dropdown (which week to configure)
  - Position tabs/selector (QB, RB, WR, TE, K, DST)
  - Input fields for each position:
    - Floor Adjustment % (number input, accepts positive/negative percentages)
    - Median Adjustment % (number input, accepts positive/negative percentages)
    - Ceiling Adjustment % (number input, accepts positive/negative percentages)
  - Active/Inactive toggle per week
  - Save/Cancel action buttons
  - Reset to defaults button
  - Preview section showing sample calculation
- Validation: Reasonable percentage range limits (-50% to +50%)

## Reusable Components

### Existing Code to Leverage

**Data Import Pipeline:**
- File: `/backend/services/data_importer.py`
- Reuse: Import flow structure, data validation patterns, bulk insert logic
- Integration point: Hook calibration application after DraftKings data parsing, before database insertion (line ~420-450)

**Import Router:**
- File: `/backend/routers/import_router.py`
- Reuse: File upload handling, week validation, transaction management
- Integration point: Add calibration trigger in `import_linestar()` and `import_draftkings()` endpoints

**Player Pool Data Structure:**
- File: `/alembic/versions/001_create_data_import_tables.py`
- Reuse: Existing player_pools table structure with projection columns
- Extension: Add calibrated projection columns alongside originals

**Smart Score Components:**
- Directory: `/frontend/src/components/smart-score/`
- Files: `SmartScoreTable.tsx`, `ProfileSelector.tsx`, `WeightAdjustmentPanel.tsx`
- Reuse: Table display patterns, modal/panel UI patterns, configuration management patterns
- Integration point: Update Smart Score calculation to consume calibrated values

**Player Schemas:**
- File: `/backend/schemas/player_schemas.py`
- Reuse: PlayerResponse model structure
- Extension: Add calibrated projection fields to response schema

**Database Migration Patterns:**
- Files: `/alembic/versions/011_add_smart_score_columns_to_player_pools.py`, `/alembic/versions/018_add_draftkings_fields_to_player_pools.py`
- Reuse: Column addition patterns, index creation, constraint management
- Pattern: Follow similar structure for adding calibrated projection columns

### New Components Required

**ProjectionCalibration Model:**
- New database table required (no existing calibration storage)
- Reason: Need persistent storage for position-based calibration factors per week

**CalibrationService:**
- New backend service for applying calibration calculations
- Reason: Complex percentage-based adjustment logic needs dedicated service layer

**CalibrationAdmin Component:**
- New React component for calibration management UI
- Reason: No existing admin interface for this type of configuration

**CalibrationStatusChip Component:**
- New React component for status indicator
- Reason: Unique UI element not matching existing badge patterns (requires calibration-aware logic)

## Technical Approach

### Database Schema Changes

**New Table: `projection_calibration`**
```sql
CREATE TABLE projection_calibration (
    id SERIAL PRIMARY KEY,
    week_id INTEGER NOT NULL REFERENCES weeks(id) ON DELETE CASCADE,
    position VARCHAR(10) NOT NULL,
    floor_adjustment_percent DECIMAL(5,2) NOT NULL,
    median_adjustment_percent DECIMAL(5,2) NOT NULL,
    ceiling_adjustment_percent DECIMAL(5,2) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_week_position UNIQUE (week_id, position),
    CONSTRAINT check_position CHECK (position IN ('QB', 'RB', 'WR', 'TE', 'K', 'DST')),
    CONSTRAINT check_adjustment_range CHECK (
        floor_adjustment_percent BETWEEN -50 AND 50 AND
        median_adjustment_percent BETWEEN -50 AND 50 AND
        ceiling_adjustment_percent BETWEEN -50 AND 50
    )
);

CREATE INDEX idx_projection_calibration_week ON projection_calibration(week_id);
CREATE INDEX idx_projection_calibration_active ON projection_calibration(week_id, is_active);
```

**Enhanced Table: `player_pools`**
Add columns for calibrated projections:
```sql
ALTER TABLE player_pools ADD COLUMN projection_floor_original FLOAT;
ALTER TABLE player_pools ADD COLUMN projection_floor_calibrated FLOAT;
ALTER TABLE player_pools ADD COLUMN projection_median_original FLOAT;
ALTER TABLE player_pools ADD COLUMN projection_median_calibrated FLOAT;
ALTER TABLE player_pools ADD COLUMN projection_ceiling_original FLOAT;
ALTER TABLE player_pools ADD COLUMN projection_ceiling_calibrated FLOAT;
ALTER TABLE player_pools ADD COLUMN calibration_applied BOOLEAN DEFAULT false;

CREATE INDEX idx_player_pools_calibration ON player_pools(week_id, calibration_applied);
```

**Migration Strategy:**
- Backfill existing data: Copy current `floor`, `projection`, `ceiling` to `*_original` columns
- Default `calibration_applied` to `false` for existing records
- Maintain backward compatibility: If calibrated values are NULL, fall back to original values

### Calibration Calculation Logic

**Formula:**
```
Calibrated Value = Original Value × (1 + Adjustment % / 100)

Examples:
- Floor of 5.0 with -10% adjustment = 5.0 × 0.90 = 4.5
- Median of 12.0 with +5% adjustment = 12.0 × 1.05 = 12.6
- Ceiling of 25.0 with -15% adjustment = 25.0 × 0.85 = 21.25
```

**Application During Import:**
```python
# Pseudocode for calibration application in data_importer.py

def apply_calibration(players: list[dict], week_id: int, db: Session) -> list[dict]:
    """Apply calibration to player projections."""

    # Query active calibration factors for this week
    calibrations = db.execute(
        text("""
            SELECT position, floor_adjustment_percent,
                   median_adjustment_percent, ceiling_adjustment_percent
            FROM projection_calibration
            WHERE week_id = :week_id AND is_active = true
        """),
        {"week_id": week_id}
    ).fetchall()

    # Create lookup dict by position
    calibration_map = {row[0]: row[1:] for row in calibrations}

    for player in players:
        position = player['position']

        # Store original values
        player['projection_floor_original'] = player.get('floor')
        player['projection_median_original'] = player.get('projection')
        player['projection_ceiling_original'] = player.get('ceiling')

        # Apply calibration if exists for this position
        if position in calibration_map:
            floor_adj, median_adj, ceiling_adj = calibration_map[position]

            # Calculate calibrated values
            if player['projection_floor_original'] is not None:
                player['projection_floor_calibrated'] = (
                    player['projection_floor_original'] * (1 + floor_adj / 100)
                )

            if player['projection_median_original'] is not None:
                player['projection_median_calibrated'] = (
                    player['projection_median_original'] * (1 + median_adj / 100)
                )

            if player['projection_ceiling_original'] is not None:
                player['projection_ceiling_calibrated'] = (
                    player['projection_ceiling_original'] * (1 + ceiling_adj / 100)
                )

            player['calibration_applied'] = True
        else:
            # No calibration - copy original to calibrated
            player['projection_floor_calibrated'] = player['projection_floor_original']
            player['projection_median_calibrated'] = player['projection_median_original']
            player['projection_ceiling_calibrated'] = player['projection_ceiling_original']
            player['calibration_applied'] = False

    return players
```

### Default Calibration Values

Based on ETR projection accuracy analysis (floor/ceiling too wide, median skewed for RB/TE/WR):

| Position | Floor Adj % | Median Adj % | Ceiling Adj % | Rationale |
|----------|-------------|--------------|---------------|-----------|
| QB       | +5%         | 0%           | -5%           | Compress range slightly |
| RB       | +10%        | +8%          | -10%          | Median too low, range too wide |
| WR       | +8%         | +5%          | -12%          | Median skewed low, ceiling too high |
| TE       | +10%        | +7%          | -10%          | Similar to RB - median low, range wide |
| K        | 0%          | 0%           | 0%            | No observed issues |
| DST      | 0%          | 0%           | 0%            | No observed issues |

**Note:** These defaults should be configurable and adjustable through admin interface based on ongoing accuracy monitoring.

### API Endpoints

**Get Calibration for Week**
```
GET /api/calibration/{week_id}

Response:
{
  "success": true,
  "week_id": 8,
  "calibrations": [
    {
      "position": "QB",
      "floor_adjustment_percent": 5.0,
      "median_adjustment_percent": 0.0,
      "ceiling_adjustment_percent": -5.0,
      "is_active": true
    },
    // ... other positions
  ]
}
```

**Update Calibration**
```
POST /api/calibration/{week_id}

Request:
{
  "position": "RB",
  "floor_adjustment_percent": 10.0,
  "median_adjustment_percent": 8.0,
  "ceiling_adjustment_percent": -10.0,
  "is_active": true
}

Response:
{
  "success": true,
  "message": "Calibration updated for RB",
  "calibration": { ... }
}
```

**Batch Update Calibrations**
```
POST /api/calibration/{week_id}/batch

Request:
{
  "calibrations": [
    {"position": "QB", "floor_adjustment_percent": 5.0, ...},
    {"position": "RB", "floor_adjustment_percent": 10.0, ...},
    // ... all positions
  ]
}
```

**Get Calibration Status for Week**
```
GET /api/calibration/{week_id}/status

Response:
{
  "success": true,
  "week_id": 8,
  "is_active": true,
  "positions_configured": 4,
  "total_positions": 6
}
```

**Reset to Defaults**
```
POST /api/calibration/{week_id}/reset

Response:
{
  "success": true,
  "message": "Calibration reset to defaults for week 8",
  "calibrations": [ ... ]
}
```

### Integration Points

**Smart Score Calculation:**
- Location: Frontend calculation or backend service (TBD based on current implementation)
- Change: Update to use `projection_*_calibrated` values instead of original values when `calibration_applied = true`
- Fallback: If calibrated values are NULL, use original values

**Lineup Optimizer:**
- Location: Backend optimizer service
- Change: Query calibrated projections when available
- SQL modification: Select calibrated columns with COALESCE fallback to originals
```sql
SELECT
    COALESCE(projection_floor_calibrated, projection_floor_original, floor) as floor,
    COALESCE(projection_median_calibrated, projection_median_original, projection) as projection,
    COALESCE(projection_ceiling_calibrated, projection_ceiling_original, ceiling) as ceiling,
    calibration_applied
FROM player_pools
WHERE week_id = :week_id
```

**Player Pool Display:**
- Frontend components: Player detail modal, player cards
- Change: Add conditional rendering to show dual values when `calibration_applied = true`
- Format: `{calibrated_value} (original: {original_value})`

## Out of Scope

### Deferred Features
- Historical accuracy analysis and tracking dashboard
- Analytics dashboard showing calibration effectiveness metrics
- Inline analytics displays in main player pool table
- Source-specific calibration profiles (ETR vs LineStar separate factors)
- Machine learning-based automatic calibration recommendations
- A/B testing framework for comparing calibration strategies
- Real-time calibration adjustment based on week-to-week performance
- Calibration factor versioning and rollback history UI
- Player-specific calibration overrides

### Future Enhancements
- **Phase 2:** Historical tracking of calibration accuracy
  - Track how calibrated projections perform vs actual points
  - Compare calibrated vs original projection accuracy
  - Generate reports on calibration effectiveness by position

- **Phase 3:** Advanced calibration strategies
  - Game script adjustments (blowout vs close game scenarios)
  - Weather-based calibration factors
  - Opponent-specific adjustments beyond rank
  - Stack correlation adjustments for calibrated projections

- **Phase 4:** Automated calibration tuning
  - ML model to suggest optimal calibration factors
  - Automated A/B testing of calibration strategies
  - Feedback loop from lineup performance to calibration tuning

## Success Criteria

### Technical Success Metrics
- Calibration applies correctly to 100% of players during import when active
- Both original and calibrated values persist correctly with no data loss
- Smart Score calculations consume calibrated values when calibration is active
- Lineup optimizer receives and uses calibrated projections
- Import process completes without performance degradation (< 5% increase in import time)
- Zero data corruption or calibration misapplication errors
- Admin interface allows configuration changes that take effect immediately on next import

### Business Success Metrics
- Improved lineup quality: Calibrated lineups score 5-10% higher on average than non-calibrated
- Reduced projection outliers: Floor/ceiling ranges compress by 15-25% for RB/TE/WR positions
- Better player pool quality: Smart Score distribution shows more separation between elite and mediocre players
- User adoption: 80%+ of users enable calibration within 2 weeks of release
- Projection accuracy improvement: Calibrated projections reduce RMSE (root mean square error) by 8-12% vs original projections

### User Experience Metrics
- Calibration status is clear: Users understand when calibration is active vs inactive
- Dual-value display provides transparency: Users can see impact of calibration on specific players
- Admin interface is intuitive: Calibration factor updates completed in < 2 minutes
- No confusion about projection sources: Clear distinction between original and calibrated values

## Implementation Phases

### Phase 1: Foundation (Days 1-3)
**Database and Core Logic:**
1. Create `projection_calibration` table migration
2. Add calibrated projection columns to `player_pools` table
3. Create CalibrationService backend service with calculation logic
4. Create calibration API endpoints (CRUD operations)
5. Add default calibration values seeding script
6. Write unit tests for calibration calculation logic

**Deliverables:**
- Database migrations completed and tested
- CalibrationService with calculation logic
- API endpoints functional
- Unit tests passing

### Phase 2: Import Integration (Days 4-5)
**Data Import Pipeline:**
1. Modify `DataImporter.normalize_players()` to store original values
2. Add `apply_calibration()` method to DataImporter
3. Integrate calibration application into import flow (after validation, before bulk insert)
4. Update bulk insert SQL to include calibrated projection columns
5. Add error handling and logging for calibration failures
6. Test import with and without calibration active

**Deliverables:**
- Import pipeline applies calibration correctly
- Original values preserved
- Fallback logic works when calibration missing
- Integration tests passing

### Phase 3: UI Components (Days 6-8)
**Frontend Development:**
1. Create CalibrationStatusChip component for Player Pool screen
2. Add calibration status API integration
3. Update player detail view to show dual values (original + calibrated)
4. Build CalibrationAdmin component with position tabs and input fields
5. Add validation and preview functionality to admin interface
6. Implement save/cancel/reset actions
7. Add responsive design and accessibility

**Deliverables:**
- Status chip displays correctly
- Player detail view shows dual values when calibration active
- Admin interface functional and intuitive
- Component tests passing

### Phase 4: Smart Score Integration (Days 9-10)
**Smart Score and Optimizer:**
1. Update Smart Score calculation to use calibrated projections
2. Add calibration-aware queries to player pool service
3. Modify lineup optimizer to consume calibrated projections
4. Add COALESCE fallback logic for backward compatibility
5. Update player schemas to include calibrated fields
6. Test Smart Score and optimizer with calibrated data

**Deliverables:**
- Smart Score uses calibrated projections
- Lineup optimizer generates lineups with calibrated data
- Backward compatibility maintained
- Integration tests passing

### Phase 5: Testing and Refinement (Days 11-12)
**End-to-End Testing:**
1. Full import-to-lineup generation workflow testing
2. Test all edge cases (no calibration, partial calibration, inactive calibration)
3. Performance testing on large datasets
4. User acceptance testing with sample data
5. Documentation updates (API docs, user guide, admin guide)
6. Bug fixes and refinements based on testing

**Deliverables:**
- All tests passing (unit, integration, E2E)
- Performance benchmarks met
- Documentation complete
- Production-ready code

### Phase 6: Deployment and Monitoring (Days 13-14)
**Release:**
1. Deploy database migrations to production
2. Seed default calibration values for current week
3. Deploy backend services and API endpoints
4. Deploy frontend components
5. Monitor import process for errors
6. Monitor calibration application accuracy
7. Gather initial user feedback

**Deliverables:**
- Feature deployed to production
- Monitoring dashboards configured
- Initial calibration applied successfully
- User feedback collected

## Edge Cases and Error Handling

### Edge Case 1: Calibration Missing for Position
**Scenario:** Calibration exists for QB, RB, WR but not TE, K, DST for current week

**Handling:**
- Apply calibration to QB, RB, WR
- For TE, K, DST: Copy original values to calibrated columns
- Set `calibration_applied = false` for uncalibrated positions
- Log warning but continue import
- Display accurate status in UI (e.g., "Partial Calibration Active: 3/6 positions")

### Edge Case 2: Calibration Inactive for Week
**Scenario:** Calibration exists but `is_active = false` for current week

**Handling:**
- Skip calibration application entirely
- Copy original values to calibrated columns for consistency
- Set `calibration_applied = false` for all players
- Display "Projection Calibration: Not Active" status chip
- Allow admin to activate calibration without re-importing data

### Edge Case 3: Invalid Calibration Factors
**Scenario:** Admin enters calibration factor outside allowed range (e.g., -100%)

**Handling:**
- Validate input on frontend before submission
- Reject API request with 400 Bad Request error
- Display clear error message: "Adjustment must be between -50% and +50%"
- Do not save invalid calibration
- Maintain previous valid calibration values

### Edge Case 4: NULL Original Projection Values
**Scenario:** Player imported with NULL floor, projection, or ceiling

**Handling:**
- Store NULL in both original and calibrated columns
- Set `calibration_applied = false` (cannot calibrate NULL)
- Skip calibration calculation for NULL values
- Display "N/A" or "--" in UI for missing values
- Log warning for data quality monitoring

### Edge Case 5: Mid-Week Calibration Change
**Scenario:** User updates calibration factors after players already imported for the week

**Handling:**
- Option 1 (Recommended): Require re-import to apply new calibration
  - Display warning: "Calibration updated. Re-import player data to apply changes."
  - Provide "Re-import" button in admin interface
- Option 2 (Future Enhancement): Retroactive calibration update
  - Run batch update to recalculate calibrated values for existing players
  - Update `updated_at` timestamp
  - Log calibration change in history

### Edge Case 6: Database Transaction Failure During Import
**Scenario:** Import fails halfway through after some calibrations applied

**Handling:**
- Wrap entire import in database transaction
- On failure: Rollback all changes (player inserts + calibration applications)
- Return error to user with clear message
- Log full error details for debugging
- Ensure no partial/inconsistent data state

### Edge Case 7: Calibration Produces Negative Projections
**Scenario:** Large negative adjustment (e.g., -40%) applied to low original value produces negative result

**Handling:**
- Validate calibration calculation result
- If calibrated value < 0: Set to 0 and log warning
- Alternative: Reject calibration factor that would produce negative values
- Display warning in admin preview: "This adjustment may produce unrealistic values for some players"

### Edge Case 8: Multiple Weeks with Same Calibration
**Scenario:** User wants to apply same calibration factors to weeks 8, 9, 10

**Handling:**
- Provide "Copy to Other Weeks" function in admin interface
- Allow multi-select week range
- Batch create calibration records for selected weeks
- Confirm action before executing: "Apply current calibration to 3 weeks?"

### Edge Case 9: Historical Data Without Calibration
**Scenario:** User views old player pool data from before calibration feature existed

**Handling:**
- Backfill: Set `calibration_applied = false` for all historical records
- Copy existing `floor`, `projection`, `ceiling` to `*_original` columns
- Set `*_calibrated` columns to NULL or same as original
- Display single value in UI (no dual value display)
- Status chip shows "Not Active" for historical weeks

### Edge Case 10: DraftKings vs ETR Projection Source
**Scenario:** Player pool contains mix of DraftKings salary-based and ETR projections

**Handling:**
- Check `projection_source` field before applying calibration
- Apply calibration ONLY to ETR projections (per requirements)
- Skip calibration for DraftKings salary-based projections
- Set `calibration_applied = true` only for ETR projections
- Log count of calibrated vs skipped players

### Performance Considerations

**Import Time Impact:**
- Calibration calculation is lightweight (simple multiplication)
- Database query for calibration factors: Single query per week (6 positions max)
- Expected overhead: < 100ms per import of ~500 players
- Mitigation: Cache calibration factors in memory during import batch

**Database Query Optimization:**
- Index on `projection_calibration.week_id` for fast lookup
- Index on `player_pools.calibration_applied` for filtered queries
- Use COALESCE in SELECT to avoid multiple columns in WHERE clauses

**Frontend Rendering:**
- Conditional rendering of dual values only when `calibration_applied = true`
- Avoid re-calculating calibration in frontend (use pre-calculated backend values)
- Memoize calibration status to prevent excessive API calls

## Dependencies and Prerequisites

**Backend:**
- SQLAlchemy ORM (existing)
- Alembic migrations (existing)
- FastAPI for API endpoints (existing)
- PostgreSQL database with player_pools table (existing)

**Frontend:**
- React (existing)
- TypeScript (existing)
- Existing player pool components and hooks
- Existing smart score components

**Data:**
- Weekly player data imports (DraftKings/LineStar) (existing)
- Position classification for all players (existing)
- Projection values (floor, median/projection, ceiling) (existing)

## Risks and Mitigations

### Risk 1: Calibration Reduces Accuracy
**Risk:** Calibration factors based on historical data may not improve future week projections

**Mitigation:**
- Start with conservative default adjustments (5-10%)
- Allow easy disable/enable toggle per week
- Plan Phase 2 tracking to monitor calibration effectiveness
- Provide "reset to defaults" option for quick reversal

### Risk 2: User Confusion About Dual Values
**Risk:** Showing both original and calibrated values may confuse users

**Mitigation:**
- Clear labeling: "Calibrated: 12.5 (Original: 11.8)"
- Prominent status indicator showing calibration is active
- Help text/tooltips explaining calibration
- Option to hide original values in settings (future)

### Risk 3: Import Performance Degradation
**Risk:** Additional calibration calculations slow down import process

**Mitigation:**
- Batch calibration calculation (not per-player queries)
- Cache calibration factors during import
- Monitor import time metrics
- Optimize SQL queries with proper indexes

### Risk 4: Database Migration Issues
**Risk:** Adding multiple columns to large player_pools table could cause downtime

**Mitigation:**
- Run migration during low-traffic period
- Test migration on staging environment first
- Add columns with NULL allowed (no data transformation required)
- Backfill data in separate step if needed

### Risk 5: Inconsistent Calibration Application
**Risk:** Some players get calibrated, others don't due to bugs

**Mitigation:**
- Comprehensive unit and integration tests
- Set `calibration_applied` flag to track application status
- Log all calibration applications
- Add validation query: "SELECT COUNT(*) WHERE calibration_applied = true AND calibrated values IS NULL"

## Appendix: File Locations and Code References

### Backend Files to Modify
- `/backend/services/data_importer.py` - Add calibration application logic
- `/backend/routers/import_router.py` - Trigger calibration during import

### Backend Files to Create
- `/backend/services/calibration_service.py` - Calibration calculation and management
- `/backend/routers/calibration_router.py` - API endpoints for calibration CRUD
- `/backend/schemas/calibration_schemas.py` - Pydantic models for calibration API

### Database Migrations
- `/alembic/versions/019_create_projection_calibration_table.py` - New calibration table
- `/alembic/versions/020_add_calibrated_projections_to_player_pools.py` - Add calibrated columns
- `/alembic/versions/021_seed_default_calibration_values.py` - Seed defaults

### Frontend Files to Create
- `/frontend/src/components/calibration/CalibrationStatusChip.tsx` - Status indicator
- `/frontend/src/components/calibration/CalibrationAdmin.tsx` - Admin interface
- `/frontend/src/components/calibration/CalibrationPreview.tsx` - Sample calculation preview
- `/frontend/src/hooks/useCalibration.ts` - API integration hook

### Frontend Files to Modify
- `/frontend/src/components/smart-score/SmartScoreTable.tsx` - Use calibrated projections
- Player detail modal/drawer (exact file TBD) - Add dual value display
- Player Pool screen header (exact file TBD) - Add status chip

### Test Files to Create
- `/tests/unit/test_calibration_service.py` - Unit tests for calculations
- `/tests/integration/test_calibration_import.py` - Integration tests for import flow
- `/tests/integration/test_calibration_api.py` - API endpoint tests
- `/frontend/src/components/calibration/__tests__/` - Component tests

## Documentation Requirements

### User Documentation
- User guide: "Understanding Projection Calibration"
- Admin guide: "Managing Calibration Factors"
- FAQ: Common calibration questions

### Developer Documentation
- API documentation: Calibration endpoints
- Database schema documentation: Updated ER diagrams
- Architecture documentation: Calibration system overview
- Migration guide: Deploying calibration feature

### Training Materials
- Video tutorial: "Configuring Calibration for Your League"
- Screenshot guide: "Reading Calibrated Projections"
- Best practices: "When to Adjust Calibration Factors"
