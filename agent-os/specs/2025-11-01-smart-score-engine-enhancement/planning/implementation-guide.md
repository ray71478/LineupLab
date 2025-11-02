# Smart Score Engine Enhancement - Implementation Guide

## Overview
This document provides guidance for spec writers and task list creators on the Smart Score Engine Enhancement implementation approach.

## Core Components to Implement

### 1. Calibration Data Model
**What it does:** Stores the calibration adjustment factors per position

**Key attributes:**
- Position (QB, RB, WR, TE, K, DEF)
- Floor adjustment percentage (e.g., -5%, +10%)
- Median adjustment percentage
- Ceiling adjustment percentage
- Active/inactive status
- Week (which week this calibration applies to)
- Created/updated timestamps

**Database considerations:**
- Should be queryable by position + week
- Should support versioning for historical tracking
- Should allow rollback to previous calibration sets

### 2. Projection Enhancement Pipeline
**What it does:** Applies calibration adjustments during import and when displaying projections

**Key integration points:**
- Hook into `backend/services/data_importer.py` during weekly import
- Apply adjustments after DraftKings data is imported but before storing in database
- Preserve original values in separate fields

**Data structure:**
- Store both `projection_original` and `projection_calibrated` for each type (floor, median, ceiling)
- Example: `projection_floor_original`, `projection_floor_calibrated`, `projection_median_original`, `projection_median_calibrated`

### 3. Admin Interface for Calibration Management
**What it does:** Allows users to enter and modify calibration factors

**Key screens/forms:**
- Calibration configuration form (one per position)
- Week selector (which week's calibration to view/edit)
- Factor input fields (Floor %, Median %, Ceiling %)
- Default calibration suggestion display
- Save/cancel actions
- Calibration history view (optional: showing previous calibration values)

**Default values:**
- Starting point: Consider conservative adjustments based on ETR projection analysis
- Should be documented and justified

### 4. Smart Score Calculation Update
**What it does:** Uses calibrated projections instead of original projections in calculations

**Key logic:**
- Update the smart score formula to use `projection_*_calibrated` values
- Maintain backward compatibility if needed (option to use original or calibrated)
- Ensure consistency across all projection sources

### 5. Lineup Optimizer Integration
**What it does:** Feeds calibrated projections into optimization algorithm

**Key changes:**
- Update lineup optimizer input to use calibrated projection values
- Verify optimizer correctly handles the potentially adjusted values
- Test that lineup quality improves with calibration

### 6. Player Pool Display Enhancement
**What it does:** Shows calibration status and dual values where appropriate

**UI elements:**
- Status chip on Player Pool page header showing "Projection Calibration: Active" or "Not Active"
- In player detail view: Display both original and calibrated values side-by-side
- Format suggestion: Show original in muted text, calibrated in prominent styling
- Example display: "Floor: 5.2 (calibrated from 4.8)"

### 7. Data Import Automation
**What it does:** Automatically applies calibration during weekly data import

**Key logic:**
- Before: Import raw DraftKings data with original projections
- During: Check if calibration exists for the current week/positions
- After: Calculate and store calibrated values alongside originals
- Error handling: If calibration data missing, continue with original values and log

## Database Schema Considerations

### New Table: ProjectionCalibration
```
- id (primary key)
- position (varchar)
- week (int)
- floor_adjustment_percent (decimal)
- median_adjustment_percent (decimal)
- ceiling_adjustment_percent (decimal)
- is_active (boolean)
- created_at (timestamp)
- updated_at (timestamp)
- created_by (user reference, if applicable)
```

### Enhanced Player Table
Add fields to existing player/projection records:
```
- projection_floor_original (decimal)
- projection_floor_calibrated (decimal)
- projection_median_original (decimal)
- projection_median_calibrated (decimal)
- projection_ceiling_original (decimal)
- projection_ceiling_calibrated (decimal)
```

## DraftKings Integration Specifics

**Important:** DraftKings salary-based projections should NOT be modified by calibration.

**Approach:**
- Identify which projections come from DraftKings salary model vs ETR
- Only apply calibration to non-DraftKings-salary projections
- Store salary-based projections in separate field if needed for clarity
- DraftKings data remains untouched during import

## Calibration Application Logic

### Default Starting Values
Based on the ETR analysis showing projection accuracy issues:
- Positions with median skew (RB, TE, WR) may need median adjustments
- Positions with wide ranges may need floor/ceiling compression
- These should be configurable but have sensible defaults

### Percentage Adjustment Calculation
```
Calibrated Value = Original Value * (1 + Adjustment %/100)
Example: Floor of 5.0 with -10% adjustment = 5.0 * 0.9 = 4.5
```

### Application During Import
```
1. Load raw projection data from import
2. Query calibration factors for this week and positions
3. For each player, apply calibration factors
4. Store both original and calibrated values
5. Use calibrated values in smart score calculations
```

## Testing Considerations

**Key test scenarios:**
1. Verify calibration applies correctly during import with various adjustment percentages
2. Confirm original values are preserved
3. Test smart score changes when using calibrated vs original projections
4. Verify DraftKings salary-based data is not modified
5. Ensure admin interface validation (e.g., realistic percentage ranges)
6. Test fallback when calibration data is missing for a position
7. Verify lineup optimizer produces different/better lineups with calibration
8. Test status chip displays correctly based on calibration active state

## Reusable Code Patterns

**From existing codebase:**
- Import flow structure: Reference `backend/services/data_importer.py`
- Player data structure: Reference existing player pool models
- Smart score calculation: Reference `/frontend/src/components/smart-score/`
- Admin form patterns: Reference similar admin interfaces in the application
- Projection display patterns: Reference existing projection component displays

## Configuration and Deployment

**Configuration approach:**
- Store default calibration values in a configuration file or database seed
- Allow override per week through admin interface
- Document default values and rationale

**Deployment considerations:**
- Calibration should be applied starting from next import cycle
- Existing data can optionally be backfilled with calibration
- Feature flag could be used to gradually roll out calibration usage
