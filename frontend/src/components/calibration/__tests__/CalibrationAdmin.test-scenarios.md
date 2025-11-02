# CalibrationAdmin Component Test Scenarios

This document outlines test scenarios for the CalibrationAdmin component. The project uses Playwright for E2E testing rather than Jest unit tests.

## Test Scenario 1: Position Tabs Switch Correctly

**Test:** Position tabs/selector switches correctly between positions

**Steps:**
1. Open CalibrationAdmin modal
2. Verify QB tab is selected by default (aria-selected="true")
3. Click RB tab
4. Verify RB tab is now selected (aria-selected="true")
5. Verify QB tab is no longer selected (aria-selected="false")
6. Click through all position tabs (WR, TE, K, DST)
7. Verify each tab switches correctly and displays corresponding calibration data

**Expected Result:**
- Position tabs switch smoothly
- Selected tab is highlighted
- Calibration values update to show position-specific data

---

## Test Scenario 2: Input Fields Validate Percentage Ranges

**Test:** Input fields validate percentage ranges (-50 to +50)

**Steps:**
1. Open CalibrationAdmin modal
2. Find Floor Adjustment % input field
3. Enter value above maximum (e.g., 51)
4. Blur the input field
5. Verify validation error message appears: "Must be between -50 and 50"
6. Enter value below minimum (e.g., -51)
7. Blur the input field
8. Verify validation error message appears
9. Enter valid value (e.g., 10)
10. Blur the input field
11. Verify no validation error is displayed

**Expected Result:**
- Invalid values (< -50 or > 50) show error message
- Valid values (-50 to 50) do not show error message
- Save button is disabled when validation errors present

---

## Test Scenario 3: Save Action Calls Batch Update API

**Test:** Save action calls batch update API with correct data

**Steps:**
1. Open CalibrationAdmin modal for week 1
2. Select QB position tab
3. Change Floor Adjustment % to 15
4. Change Median Adjustment % to 5
5. Change Ceiling Adjustment % to -8
6. Click Save button
7. Monitor network requests to verify POST /api/calibration/1/batch is called
8. Verify request body contains all 6 positions with updated QB values
9. Verify success message appears
10. Verify modal closes after successful save

**Expected Result:**
- Batch update API endpoint called with correct week ID
- Request body contains calibrations for all 6 positions
- Modified position (QB) has updated values
- Success message displayed
- Modal closes automatically

---

## Test Scenario 4: Reset to Defaults Action

**Test:** Reset action calls reset API and restores default values

**Steps:**
1. Open CalibrationAdmin modal
2. Modify several calibration values for different positions
3. Click "Reset to Defaults" button
4. Monitor network requests to verify POST /api/calibration/{week_id}/reset is called
5. Verify calibration values reset to default values:
   - QB: Floor +5%, Median 0%, Ceiling -5%
   - RB: Floor +10%, Median +8%, Ceiling -10%
   - WR: Floor +8%, Median +5%, Ceiling -12%
   - TE: Floor +10%, Median +7%, Ceiling -10%
   - K: Floor 0%, Median 0%, Ceiling 0%
   - DST: Floor 0%, Median 0%, Ceiling 0%
6. Verify success message appears

**Expected Result:**
- Reset API endpoint called
- All position calibrations reset to documented default values
- Success message displayed
- User can verify values by switching between position tabs

---

## Test Scenario 5: Active/Inactive Toggle

**Test:** Active/inactive toggle works correctly per position

**Steps:**
1. Open CalibrationAdmin modal
2. Select QB position tab
3. Verify "Active" switch is checked (default state)
4. Click the active toggle switch
5. Verify switch is now unchecked
6. Click the switch again
7. Verify switch is checked again
8. Switch to RB position tab
9. Toggle RB active switch off
10. Save changes
11. Verify both positions save with correct is_active flags

**Expected Result:**
- Active toggle switches on/off smoothly
- Toggle state is position-specific (each position has own toggle)
- Toggle state persists when switching between position tabs
- Save includes correct is_active flag for each position

---

## Test Scenario 6: Preview Calculation Displays Correctly

**Test:** Preview section shows accurate calibration calculations

**Steps:**
1. Open CalibrationAdmin modal
2. Select QB position tab
3. Set Floor Adjustment % to 10
4. Verify Floor preview shows:
   - Original value (sample ~18.5)
   - Calibrated value calculated as: 18.5 × 1.10 = 20.35
   - Difference indicator showing +1.85 (+10%)
   - Formula display
5. Set Median Adjustment % to -5
6. Verify Median preview shows:
   - Original value (sample ~18.5)
   - Calibrated value calculated as: 18.5 × 0.95 = 17.58
   - Difference indicator showing -0.92 (-5%)
7. Verify preview updates in real-time as values change

**Expected Result:**
- Preview section visible (data-testid="calibration-preview-section")
- Three preview cards shown: Floor, Median, Ceiling
- Calculations are accurate
- Color coding: green for increases, red for decreases
- Formula display shows calculation breakdown
- Preview updates immediately when adjustment percentages change

---

## Test Scenario 7: Modal Closes on Cancel

**Test:** Modal closes when Cancel button is clicked

**Steps:**
1. Open CalibrationAdmin modal
2. Make some changes to calibration values
3. Click "Cancel" button
4. Verify modal closes
5. Reopen modal
6. Verify previous changes were NOT saved (values reverted)

**Expected Result:**
- Cancel button closes modal
- Changes are discarded
- Modal can be reopened with original values

---

## Test Scenario 8: Loading State Displays Correctly

**Test:** Loading state shows spinner while fetching calibration data

**Steps:**
1. Simulate slow API response for calibration data
2. Open CalibrationAdmin modal
3. Verify loading spinner (CircularProgress) is displayed
4. Verify no calibration controls are visible during loading
5. Wait for data to load
6. Verify loading spinner disappears
7. Verify calibration controls appear

**Expected Result:**
- Loading spinner visible initially
- User cannot interact with controls during loading
- Controls become available after data loads
- No errors or broken UI during loading state

---

## Additional Integration Tests

### Test Scenario 9: Multi-Position Batch Save

**Steps:**
1. Open CalibrationAdmin modal
2. Configure QB: Floor +5%, Median 0%, Ceiling -5%
3. Switch to RB tab
4. Configure RB: Floor +10%, Median +8%, Ceiling -10%
5. Switch to WR tab
6. Configure WR: Floor +8%, Median +5%, Ceiling -12%
7. Click Save
8. Verify batch update includes all modified positions

**Expected Result:**
- All position changes saved in single API call
- No data loss between tab switches

---

### Test Scenario 10: Responsive Design

**Steps:**
1. Open CalibrationAdmin on mobile viewport (320px)
2. Verify modal is full-screen
3. Verify position tabs are scrollable
4. Verify preview cards stack vertically
5. Resize to tablet viewport (768px)
6. Verify modal is centered with side margins
7. Verify preview cards in 2-column grid
8. Resize to desktop viewport (1024px+)
9. Verify modal is centered
10. Verify preview cards side-by-side

**Expected Result:**
- Modal adapts to screen size
- All controls remain accessible on mobile
- Layouts change appropriately for each breakpoint

---

## Accessibility Tests

### Test Scenario 11: Keyboard Navigation

**Steps:**
1. Open CalibrationAdmin modal
2. Use Tab key to navigate through controls
3. Verify focus moves through: position tabs, input fields, toggle, buttons
4. Use Arrow keys to switch position tabs
5. Use Enter/Space to toggle active switch
6. Use Escape key to close modal

**Expected Result:**
- Full keyboard navigation support
- Visible focus indicators on all interactive elements
- Modal traps focus (Tab doesn't escape modal)
- Escape key closes modal

---

### Test Scenario 12: Screen Reader Support

**Steps:**
1. Enable screen reader
2. Open CalibrationAdmin modal
3. Verify screen reader announces:
   - Modal title: "Calibration Settings"
   - Current position tab
   - Input field labels: "Floor Adjustment %", etc.
   - Active toggle label: "Active for this position"
   - Button labels: "Save", "Cancel", "Reset to Defaults"
   - Validation error messages

**Expected Result:**
- All interactive elements have proper ARIA labels
- Error messages are announced by screen reader
- Screen reader can navigate entire interface

---

## Notes

- This project uses Playwright for E2E testing, not Jest unit tests
- Tests should be implemented as E2E browser tests
- Mock API responses using Playwright's network interception
- Test with real Material-UI Dialog component behavior
- Verify all animations and transitions complete before assertions
