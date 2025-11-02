# ProjectionDisplay Component - Test Scenarios

## Overview
Test scenarios for the ProjectionDisplay component that displays dual-value projections (calibrated and original).

## Test Scenarios

### 1. Calibration Applied - Dual Value Display
**Scenario**: When calibration is applied and values differ, show both calibrated and original values.

**Given**:
- `calibrationApplied = true`
- `originalValue = 10.5`
- `calibratedValue = 11.6`

**Expected**:
- Calibrated value (11.6) displayed prominently in white, font-weight 600
- Original value (10.5) displayed in muted gray color with "(original: 10.5)" text
- Label displayed above values

### 2. Calibration Applied - Formatting
**Scenario**: Verify correct formatting per spec (lines 54-61).

**Given**:
- `calibrationApplied = true`
- `originalValue = 11.8`
- `calibratedValue = 12.5`

**Expected**:
- Format: "12.5 (original: 11.8)"
- Both values shown with 2 decimal places
- Original value in italic, muted text

### 3. Calibration Not Applied - Single Value Display
**Scenario**: When calibration is not applied, show only one value.

**Given**:
- `calibrationApplied = false`
- `originalValue = 10.5`
- `calibratedValue = 10.5`

**Expected**:
- Single value (10.5) displayed
- No "(original: ...)" text shown
- Same styling as calibrated value (prominent, white)

### 4. NULL Value Handling - Both NULL
**Scenario**: When both original and calibrated values are NULL, show "N/A".

**Given**:
- `originalValue = null`
- `calibratedValue = null`

**Expected**:
- "N/A" displayed in muted gray color
- Label still shown
- Italic font style

### 5. NULL Value Handling - Undefined Values
**Scenario**: Handle undefined values gracefully (same as NULL).

**Given**:
- `originalValue = undefined`
- `calibratedValue = undefined`

**Expected**:
- "N/A" displayed
- Same behavior as NULL values

### 6. Label Display
**Scenario**: Verify label is displayed correctly.

**Given**:
- `label = "Floor"`
- Any valid values

**Expected**:
- "Floor" displayed in uppercase, gray color
- Font size 0.75rem
- Letter spacing 0.5px
- Above the value display

### 7. Different Values When Calibrated
**Scenario**: When calibration applied and values differ, show dual display.

**Given**:
- `calibrationApplied = true`
- `originalValue = 24.3`
- `calibratedValue = 22.1`

**Expected**:
- Calibrated value (22.1) prominent
- Original value (24.3) muted
- Clear visual distinction between the two

### 8. Same Values When Calibrated
**Scenario**: When calibration applied but values are identical, show single value.

**Given**:
- `calibrationApplied = true`
- `originalValue = 15.0`
- `calibratedValue = 15.0`

**Expected**:
- Single value (15.0) displayed
- No "(original: ...)" text (since values are identical)

## Manual Testing Checklist

To verify ProjectionDisplay component manually:

1. [ ] Import a week with calibration applied
2. [ ] Open player detail view (expand player row in player table)
3. [ ] Verify Floor shows: "calibrated (original: original)" if calibration active and values differ
4. [ ] Verify Median shows: "calibrated (original: original)" if calibration active and values differ
5. [ ] Verify Ceiling shows: "calibrated (original: original)" if calibration active and values differ
6. [ ] Import a week without calibration
7. [ ] Verify Floor shows single value
8. [ ] Verify Median shows single value
9. [ ] Verify Ceiling shows single value
10. [ ] Check player with NULL projection values shows "N/A"

## Acceptance Criteria

- [x] ProjectionDisplay component created
- [x] Dual-value display format matches spec (lines 54-61)
- [x] NULL values handled gracefully (show "N/A")
- [x] Single value shown when calibration not applied
- [x] Calibrated value prominent, original value muted
- [x] Component integrated into PlayerTableRow
- [x] Backend API returns calibrated projection fields
- [ ] Manual verification in browser complete

## Browser Testing Steps

1. Start the application: `cd frontend && npm run dev`
2. Navigate to Player Pool page
3. Import DraftKings data for a week with active calibration
4. Click expand arrow on a player row
5. Verify projection values display format:
   - With calibration: "12.5 (original: 11.8)"
   - Without calibration: "12.5"
   - NULL values: "N/A"
6. Check visual styling:
   - Calibrated value: white, bold (font-weight 600)
   - Original value: gray (#6b7280), italic, smaller font
   - Label: uppercase, gray (#9ca3af)

## Related Files

- Component: `/frontend/src/components/player/ProjectionDisplay.tsx`
- Integration: `/frontend/src/components/players/PlayerTableRow.tsx`
- Types: `/frontend/src/types/player.types.ts`
- Backend Schema: `/backend/schemas/player_schemas.py`
- Backend Service: `/backend/services/player_management_service.py`
