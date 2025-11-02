# Smart Score Engine Enhancement - Decision Summary

## Quick Reference: Key Decisions

### Calibration Application
- **When:** Automatically during weekly data import
- **Condition:** Only if calibration data is available for that week
- **Fallback:** Continue with original values if calibration missing
- **Decision:** Automatic application beats manual per-week application

### Calibration Structure
- **Scope:** Position-based only (QB, RB, WR, TE, K, DEF)
- **Factors:** Three adjustment percentages per position
  1. Floor adjustment %
  2. Median adjustment %
  3. Ceiling adjustment %
- **Source:** Position-based regardless of projection source (ETR, DraftKings, etc.)
- **Decision:** Percentage-based adjustments for flexibility and reusability

### Data Handling
- **Original Projections:** Preserved in database (not overwritten)
- **Calibrated Projections:** Calculated and stored separately
- **DraftKings Salary Data:** NEVER modified by calibration
- **Display:** Show both original and calibrated values
- **Decision:** Preserve all data for transparency and audit trail

### Management Interface
- **Type:** Simple admin interface (not external import)
- **Capability:** Enter/update calibration factors
- **Defaults:** Start with sensible defaults
- **Direct Editing:** Allow direct factor entry (not slider-based)
- **Decision:** Admin UI provides best balance of control and simplicity

### User Interface
- **Status Indicator:** Chip format (not banner) on Player Pool screen
- **Status Messages:** "Projection Calibration: Active" or "Not Active"
- **Dual Value Display:** In player pool detail view (not main table)
- **Main Table:** No changes to existing table view
- **Decision:** Minimal UI disruption, essential information provided subtly

### Smart Score Integration
- **Calculation Input:** Uses calibrated projection values
- **Impact:** Should improve smart score accuracy and player pool quality
- **Backward Compatibility:** Consider preserving option to use original values if needed
- **Decision:** Calibrated values become default for smart score

### Lineup Optimizer Integration
- **Input:** Receives calibrated projection values
- **Expected Outcome:** Better lineup quality through improved projections
- **Testing:** Verify optimizer handles adjusted values correctly
- **Decision:** Optimizer uses calibrated values for improved performance

### Out of Scope Items (Deferred)
- Historical accuracy analysis and tracking
- Analytics dashboard showing calibration effectiveness
- Inline analytics displays in player views
- Source-specific calibration profiles
- Advanced analytics features
- **Decision:** Keep initial implementation focused, add later if beneficial

## Calibration Factor Guidance

### Position-Specific Adjustments
Based on ETR projection analysis provided:

**Problem Areas Identified:**
- Floor/ceiling ranges too wide (affecting prediction accuracy)
- Median projections skewed for RB, TE, and WR positions
- Need position-specific calibration to address these issues

**Recommended Approach:**
- Start with conservative adjustments (±5% to ±15% range)
- RB, TE, WR likely need median adjustments
- All positions may benefit from floor/ceiling range compression
- Document and justify default values

### Calculation Method
```
Calibrated Value = Original Value × (1 + Adjustment % / 100)
Example: Floor 5.0 with -10% = 5.0 × 0.9 = 4.5
```

## Integration Points (Code References)

**Import Process:**
- File: `backend/services/data_importer.py`
- Action: Hook calibration application after DraftKings import, before data storage

**Smart Score Component:**
- Location: `/frontend/src/components/smart-score/`
- Action: Update to consume calibrated projections

**Lineup Optimizer:**
- Currently uses projection values
- Action: Update to use calibrated projection inputs

**Player Pool Services:**
- Backend services for player data management
- Action: Ensure both original and calibrated values are stored/retrieved

**Import Router:**
- File: `backend/routers/import_router.py`
- Action: May need calibration trigger or parameter

## Risk Mitigation

**Data Integrity:**
- Always preserve original values
- Audit trail of calibration application
- Test with historical data before production rollout

**Performance:**
- Calibration factors are static per week (not per-request calculation)
- No significant performance impact expected
- Percentage calculation is minimal overhead

**User Confusion:**
- Clear indicator when calibration is active
- Both original and calibrated values shown in detail view
- Documentation of what calibration means

## Success Metrics

**Technical Success:**
- Calibration applies correctly during import
- Both original and calibrated values persist correctly
- Smart score calculations use calibrated values
- Lineup optimizer receives calibrated inputs

**Business Success:**
- Better player pool quality from calibrated projections
- Improved lineup generation with better accuracy
- Reduced projection outliers (too high or too low floor/ceiling)

## Implementation Priority

**Phase 1: Foundation**
1. Create ProjectionCalibration data model
2. Build admin interface for calibration management
3. Implement calibration application logic in import
4. Add original + calibrated value storage

**Phase 2: Integration**
1. Update smart score calculation to use calibrated values
2. Update player pool display to show status and dual values
3. Integrate with lineup optimizer

**Phase 3: Refinement**
1. Test and validate with real data
2. Adjust default calibration values based on testing
3. Monitor impact on player pool and lineup quality
4. Document calibration methodology

## Document References

**Comprehensive Requirements:**
- `/planning/requirements.md` - Full requirements specification

**Implementation Details:**
- `/planning/implementation-guide.md` - Technical implementation guidance

**Original Concept:**
- `/planning/raw-idea.md` - Initial feature description

## Next Steps for Spec Writers

1. Review the complete requirements in `/planning/requirements.md`
2. Reference implementation guidance in `/planning/implementation-guide.md`
3. Create detailed specifications for:
   - ProjectionCalibration data model
   - Admin calibration interface
   - Calibration application logic in import
   - Smart score calculation updates
   - Player detail view display changes
   - Status indicator component
4. Identify database migrations needed
5. Create task list with dependencies between components
