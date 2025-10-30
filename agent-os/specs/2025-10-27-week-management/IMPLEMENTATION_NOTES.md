# Week Management Feature - Implementation Notes

## Specification Status

A comprehensive specification document has been created at:
**`/Users/raybargas/Documents/Cortex/agent-os/specs/2025-10-27-week-management/spec.md`**

---

## Specification Overview

The specification document is 850+ lines and covers all aspects required for production implementation:

### Core Sections

1. **Overview** (Purpose, Objectives, Success Metrics)
   - Dynamic week generation based on NFL calendar
   - Automatic status management (Active/Upcoming/Completed)
   - Professional, modern Material Design UI with dark mode
   - Integration with Data Import System
   - Immutable weeks once data imported

2. **Architecture** (System design, technology stack, data flow)
   - Complete system diagram
   - Frontend: React 18, TypeScript, Material-UI v5, Zustand
   - Backend: FastAPI, SQLAlchemy 2.0, PostgreSQL
   - Mobile: React Swipeable (carousel pattern)

3. **Database Schema** (Extended weeks table + 3 new tables)
   - `weeks` table extended with: `nfl_slate_date`, `status_override`, `is_locked`, `locked_at`, `metadata`
   - `week_metadata` table (kickoff times, ESPN links, import status)
   - `nfl_schedule` table (NFL schedule seed data)
   - `week_status_overrides` table (manual override tracking)

4. **API Specifications** (8 REST endpoints)
   - `GET /api/weeks?year=2025` - Get weeks with metadata
   - `GET /api/current-week` - Auto-detect current week
   - `GET /api/weeks/{id}/metadata` - Rich metadata
   - `PUT /api/weeks/{id}/status` - Manual status override
   - `POST /api/weeks/generate` - Auto-generate season weeks
   - `GET /api/nfl-schedule` - Get NFL schedule
   - `PUT /api/weeks/{id}/lock` - Lock week on data import
   - `PUT /api/weeks/{id}/import-status` - Update import status

5. **Frontend Components** (5 new components)
   - **WeekSelector** (enhanced): Dropdown with year selector, status badges, glow effect
   - **YearSelector**: Dropdown for 2025-2030
   - **WeekCarousel**: Mobile swipeable carousel (xs, sm breakpoints)
   - **WeekMetadataPanel**: Rich metadata display (NFL date, time, ESPN link)
   - **WeekStatusBadge**: Material Design icons (green checkmark, gray dash, orange warning)

6. **UI/UX Design** (Dark mode optimized)
   - Material Design v5 color palette
   - Professional typography system
   - Responsive breakpoints (xs, sm, md, lg, xl)
   - Animations: 200ms dropdown, 300ms carousel, 2s glow effect
   - NO emojis (strictly icon-based)
   - Touch-friendly (44x44px minimum targets)

7. **State Management**
   - Zustand store structure (currentYear, currentWeek, weeks[], availableYears)
   - TanStack Query hooks (useWeeks, useCurrentWeek, useWeekMetadata)
   - localStorage persistence (existing pattern)

8. **Data Flow**
   - Week selection flow (year change → fetch weeks → update UI)
   - Week change flow (select week → update state → import system uses selection)
   - Import status update flow (import completes → lock week → badge updates)
   - Current week auto-detection (page load + 60s refresh)

9. **Mobile Considerations**
   - Swipeable carousel as primary navigation
   - Metadata in full-screen modal on tap
   - Touch gestures: swipe left/right, tap for details
   - Performance: virtualization, lazy loading, preloading adjacent weeks
   - Responsive sizing (font-size, padding, spacing)

10. **Validation Rules**
    - Week validation (1-18 range)
    - Year validation (current to +5 years)
    - Status validation (active/upcoming/completed)
    - Week immutability (prevent editing locked weeks)

11. **Error Handling**
    - Custom exceptions (WeekNotFoundError, WeekLockedError, InvalidYearError, NFLScheduleError)
    - Graceful error recovery (auto-retry, fallback data, user-friendly messages)
    - Error responses with clear messages (never stack traces)

12. **Integration Points**
    - Data Import System: Week locking on successful import
    - Player Pool Context: Week selection updates global context
    - Phase 2: Lineup History (view historical lineups for locked weeks)

13. **Implementation Plan** (7 phases, 8-10 hours total)
    - Phase 1: Database setup (3h) - migrations, schema, seed data
    - Phase 2: Backend services (2.5h) - week management, status, NFL schedule
    - Phase 3: API endpoints (2h) - 8 REST endpoints with validation
    - Phase 4: Frontend state (1.5h) - Zustand, hooks, TanStack Query
    - Phase 5: Frontend components (2h) - 5 components, responsive, dark mode
    - Phase 6: Integration & polish (1h) - import locking, animations
    - Phase 7: Testing (1h) - unit, integration, E2E tests

14. **Test Cases** (8 comprehensive scenarios)
    - Week loading and auto-status
    - Week selection and metadata
    - Mobile carousel navigation
    - Data import locking
    - Manual status override
    - Year selection
    - Locked week immutability

15. **Acceptance Criteria** (10 must-have requirements)
    - Auto-generate weeks from NFL calendar
    - Status auto-update + manual override
    - Modern Material Design with glow effects
    - Rich metadata display (dates, times, ESPN links)
    - Mobile swipeable carousel
    - Import status badges (green/gray/orange)
    - Week locking on import
    - Full responsiveness
    - Dark mode optimized
    - Performance targets (<200ms, 60fps)

---

## Key Features Documented

### Dynamic Week Generation
- Not hardcoded (1-18 hardcoded values, but weeks generated from NFL schedule)
- Supports multiple years (2025-2030)
- Auto-populate metadata (kickoff times, dates)
- Seed data included for 2025 NFL schedule

### Smart Status Management
- **Automatic**: Based on current date vs nfl_slate_date
  - Completed: nfl_slate_date < today
  - Active: nfl_slate_date = today
  - Upcoming: nfl_slate_date > today
- **Manual Override**: `PUT /api/weeks/{id}/status` with reason tracking
- **Auto-Update**: On page load and every 60 seconds

### Professional Visual Design
- Material Design v5 compliance throughout
- Dark mode optimized (primary use case)
- Color palette: Blue primary, no harsh colors
- Typography: Proper sizing and spacing
- NO EMOJIS (strictly Material-UI icons)
- Animations: Smooth, professional
- Modern glow effect on current week

### Mobile UX (Recommended Pattern)
- Swipeable horizontal carousel (most intuitive)
- Large week numbers (48px font)
- Status badge directly below week
- Metadata in full-screen modal on tap
- Fast swipe = multiple weeks
- Proper touch targeting (44x44px min)

### Data Immutability
- `is_locked` boolean flag prevents editing
- `locked_at` timestamp tracks when locked
- Called by Data Import System on successful import
- Week becomes read-only once locked
- Cannot be unlocked by user

### Rich Metadata Display
- NFL slate date (e.g., "Sunday, September 7")
- Kickoff time (e.g., "1:00 PM ET")
- ESPN schedule link (clickable, opens new tab)
- Import status badge with icon
- Tooltip showing:
  - Player count
  - Import timestamp
  - Data source (LineStar, DraftKings)
  - Error message (if applicable)

### Integration with Data Import System
- Uses `selectedWeekForImport` from Zustand
- Week mismatch detection (filename vs selected)
- Lock week after successful import
- Update metadata with import count/timestamp
- Show error status if import fails
- Block imports for locked weeks (optional UX)

---

## Reusable Code Patterns

The spec leverages existing patterns from the Data Import System:

### 1. Zustand Store Pattern
- Existing `useWeekStore` extended with additional state
- `persist` middleware for localStorage
- Proper TypeScript interfaces
- Selector functions for computed state

### 2. TanStack Query Hooks
- Query caching with staleTime/cacheTime
- Auto-retry on network errors
- Proper error boundaries
- Integration with Zustand state

### 3. Material-UI Components
- FormControl + Select for dropdowns
- Icons from @mui/icons-material
- sx prop for responsive styling
- Dark theme support built-in
- Proper spacing and typography

### 4. API Response Format
- `{success: true/false, ...}` pattern
- Detailed error messages
- Consistent field naming
- UUID for IDs (import_id style)

### 5. Error Handling
- Custom exception classes extending CortexException
- Global exception handler in main.py
- Proper HTTP status codes (404, 409, 422, 500)
- User-friendly error messages

---

## Critical Implementation Details

### 1. Week Status Auto-Detection
```
Current date = 2025-10-08
- Week 1-4: completed (past dates)
- Week 5: active (current week = 2025-10-05)
- Week 6-18: upcoming (future dates)

Must check nfl_slate_date field to determine status
Must run on page load AND periodically (60s)
```

### 2. Week Locking Flow
```
Data Import System → successful import
  ↓
Call: PUT /api/weeks/{week_id}/lock
  ↓
Backend:
  1. Set is_locked = true
  2. Set locked_at = NOW()
  3. Update week_metadata.import_status
  4. Update week_metadata.import_count
  ↓
Frontend:
  1. Zustand updates week object
  2. WeekStatusBadge shows green checkmark
  3. Week becomes read-only in selector
```

### 3. NFL Schedule Seed Data
```
Must be populated in nfl_schedule table before first use
Includes all 18 weeks with:
- Week number (1-18)
- Slate date (Sunday of week)
- Kickoff time (primary time)
- Game count (usually 16)
- Is_playoff flag (for future expansion)
```

### 4. Year Selector Logic
```
Available years: [2025, 2026, 2027, 2028, 2029, 2030]
Default: Current year (e.g., 2025)
When changed:
  1. Update Zustand currentYear
  2. Trigger useWeeks hook with new year
  3. Fetch weeks for that year
  4. Auto-generate if not exists
  5. Update all UI components
```

### 5. Mobile Carousel Implementation
- Use react-swipeable library
- Implement virtualization for smooth scrolling
- Preload adjacent weeks data
- Snap to center on swipe end
- Double-tap to return to current week (optional)

---

## Missing from Spec (Intentional)

The following are **intentionally excluded** as Phase 2 features:
- Replay weeks / view historical lineups
- Detailed import comparison UI
- Trend visualization (charts)
- Vegas line integration
- Automated external API fetching
- CSV import support
- Drag-and-drop file upload
- Multiple file simultaneous upload

---

## Files Created

```
/Users/raybargas/Documents/Cortex/agent-os/specs/2025-10-27-week-management/spec.md
```

**Total Lines:** 850+
**Sections:** 15 major sections
**API Endpoints:** 8 documented
**Components:** 5 new components
**Database Tables:** 3 new + 1 extended
**Test Cases:** 8 comprehensive scenarios

---

## Next Steps for Development

1. **Kickoff Meeting**
   - Review spec with development team
   - Clarify mobile UX decision (carousel vs bottom sheet)
   - Confirm 2025-2030 year range

2. **Phase 1 Implementation**
   - Create Alembic migration
   - Create nfl_schedule seed data
   - Test migrations locally

3. **Parallel Work** (Phases 2-5)
   - Backend services development
   - Frontend components development
   - Can work in parallel

4. **Integration**
   - Connect with Data Import System
   - Test week locking flow
   - Test status updates

5. **Testing**
   - Unit tests for services
   - Component tests
   - E2E tests for workflows

---

## Success Criteria

Implementation is complete when:
- All 8 API endpoints working
- All 5 React components rendering
- Mobile carousel smooth (60fps)
- Dropdown opens <200ms
- Week data loads <500ms
- Dark mode fully optimized
- Week locking prevents editing
- All test cases passing
- Zero known bugs

---

**Specification Status:** COMPLETE AND READY FOR IMPLEMENTATION

**Estimated Timeline:** 8-10 hours for full implementation

**Complexity:** Medium (builds on existing Data Import System patterns)
