# Spec Requirements: Smart Score Engine Enhancement

## Initial Description
Enhance the Smart Score Engine to incorporate projection calibration and advanced analytics. The focus is primarily on backend capabilities that leverage historical projection accuracy data (like ETR projection performance by position) to create better player pools and lineups. Keep UI enhancements minimal - we like the current UI, but consider essential user controls. The system should be empowered with enough analytical information to make optimal decisions about player selection and lineup generation.

Analysis shows ETR projections need calibration (floor/ceiling ranges too wide, median projections skewed for RB/TE/WR). Goal is to create the best possible player pools and lineups using this enhanced intelligence.

## Requirements Discussion

### First Round Questions

**Q1:** Should calibration be applied automatically during import if calibration data is available for that week?
**Answer:** Yes, apply automatically during import if calibration data is available for that week.

**Q2:** Should the system use existing floor/ceiling data from the DraftKings import, or establish new methodology?
**Answer:** Use existing floor/ceiling data from DraftKings import (already available).

**Q3:** How should calibration profiles be stored and managed - per position, per source, or both?
**Answer:** Store per position with ability to modify and save them.

**Q4:** Should we implement historical analysis of projection accuracy as a separate analytics feature?
**Answer:** Skip this for now (out of scope).

**Q5:** When displaying calibrated projections to users, should we show original and calibrated values separately?
**Answer:** Show both original AND calibrated values.

**Q6:** What level of user control should be provided for calibration adjustments?
**Answer:** Granular controls with sliders.

**Q7:** Should there be an analytics dashboard or inline analytics display showing how calibration impacts projections?
**Answer:** No analytics dashboard, no inline display - keep scope smaller.

**Q8:** Is the focused scope correct: backend calibration system with minimal UI for manual controls?
**Answer:** Confirmed - keep it focused.

### Follow-up Questions

**Follow-up Q1:** How should calibration data be sourced and managed - should we build an admin interface or import from external sources?
**Answer:** Build a simple admin interface to enter/update calibration factors; start with sensible defaults.

**Follow-up Q2:** Can you confirm the calibration structure: Floor adjustment %, Median adjustment %, Ceiling adjustment % per position?
**Answer:** Correct structure confirmed.

**Follow-up Q3:** How should users know calibration is active - should it be a prominent banner or a subtle indicator?
**Answer:** Top of Player Pool screen with a chip (not banner) showing "Projection Calibration: Active" or "Not Active".

**Follow-up Q4:** Where should the dual-value display (original + calibrated) appear - in the main player pool table or detail view?
**Answer:** Display in player pool detail view (not the main table).

**Follow-up Q5:** For granular controls, should users interact with intensity sliders or directly edit calibration factors?
**Answer:** Direct editing of calibration factors (not intensity sliders); need location for these controls.

**Follow-up Q6:** Should DraftKings salary-based projections also be adjusted by calibration, or left as-is?
**Answer:** Do NOT adjust DraftKings salary-based projections - leave those as-is.

**Follow-up Q7:** Should calibration be position-based regardless of projection source, or have separate profiles per source?
**Answer:** Position-based calibration regardless of projection source.

### Existing Code to Reference

**Similar Features Identified:**
- Smart Score Engine: Existing projection system in `/frontend/src/components/smart-score/` - understand current architecture
- Player Pool Management: Backend services for player data handling
- DraftKings Integration: Existing import logic and data structure in `backend/routers/import_router.py` and `backend/services/data_importer.py`

## Visual Assets

### Files Provided
Analysis indicated an image showing ETR projection accuracy analysis with observations about:
- Floor/ceiling ranges being too wide
- Median projections skewed for RB/TE/WR positions
- Position-specific calibration needs

**Note:** Visual file was referenced during discussion but not formally stored in visuals folder for review.

### Visual Insights
- ETR projections require position-specific calibration
- Different positions have different accuracy patterns
- Need to address both floor/ceiling range width and median value accuracy
- Calibration approach should be granular enough to handle position-specific issues

## Requirements Summary

### Functional Requirements

**Calibration System:**
- Apply projection calibration automatically during weekly data import when calibration data is available
- Store calibration profiles per NFL position (QB, RB, WR, TE, etc.)
- Support three calibration factors per position: Floor adjustment %, Median adjustment %, Ceiling adjustment %
- Allow modification and saving of calibration profiles through admin interface
- Start with sensible default calibration values

**Data Processing:**
- Preserve original DraftKings salary-based projections without modification
- Apply calibration adjustments only to analytical projections (ETR, etc.)
- Maintain both original and calibrated projection values in the system
- Position-based calibration applies regardless of projection source

**User Interface:**
- Display calibration status indicator (chip format) on Player Pool screen showing "Projection Calibration: Active" or "Not Active"
- Show both original and calibrated projection values in player pool detail view (not main table)
- Provide direct editing interface for calibration factors (not intensity sliders)
- Build simple admin interface for entering/updating calibration factors

**Player Pool and Lineup Generation:**
- Use calibrated projections in smart score calculations for player pool creation
- Use calibrated projections in lineup generation optimization

### Reusability Opportunities

**Existing Code to Leverage:**
- Smart Score Engine (`/frontend/src/components/smart-score/`): Current projection display and calculation logic
- DraftKings Import System (`backend/routers/import_router.py`, `backend/services/data_importer.py`): Integration point for automatic calibration application during import
- Player Pool Services: Existing backend logic for player data management and filtering
- Lineup Optimizer: Current optimization logic that will consume calibrated projections

### Scope Boundaries

**In Scope:**
- Position-based projection calibration with three adjustment factors (floor, median, ceiling)
- Admin interface for calibration factor management
- Automatic calibration application during weekly imports
- Dual-value display (original + calibrated) in player detail views
- Calibration status indicator on Player Pool screen
- Use of calibrated projections in smart score and lineup generation
- Support for sensible default calibration values

**Out of Scope:**
- Historical analysis of projection accuracy
- Analytics dashboard showing calibration impact
- Inline analytics displays in main UI
- Modification of DraftKings salary-based projections
- Source-specific calibration profiles (position-based across all sources)
- Prominent banner displays (using subtle chip indicator instead)
- Main player pool table modifications for displaying calibrated values

**Future Enhancements:**
- Historical accuracy analysis and tracking
- Machine learning-based calibration recommendations
- Analytics dashboard for calibration effectiveness
- Source-specific calibration profiles if needed
- Advanced analytics displays

### Technical Considerations

**Integration Points:**
- DraftKings import process: Hook for applying calibration during import
- Smart Score calculation: Consume calibrated projection values
- Lineup optimizer: Use calibrated projections in optimization algorithm
- Player pool backend services: Store and retrieve calibration profiles and values

**Data Management:**
- Store calibration factors per position in database
- Maintain original projection values alongside calibrated values
- Default calibration values for new weeks/positions

**Design Principles:**
- Minimal UI changes to preserve current design
- Backend-focused enhancement (analytics and data processing)
- Direct editing approach rather than slider-based intensity controls
- Preserve DraftKings data integrity (no modification of salary-based projections)
- Position-based methodology for consistency across sources

### Key Assumptions Confirmed
1. Calibration is applied at import time, not runtime
2. Floor/ceiling calibration uses percentage adjustments
3. DraftKings salary-based projections should not be modified
4. Calibration factors are position-based only (not source-based)
5. Admin interface is preferred over external import for calibration management
6. Status indicator should be subtle (chip) not prominent (banner)
7. Dual-value display belongs in detail view, not main table
8. Direct factor editing is preferred over slider-based controls
