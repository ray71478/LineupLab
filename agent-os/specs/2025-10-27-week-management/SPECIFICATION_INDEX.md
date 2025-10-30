# Week Management Feature - Specification Index

## Quick Links

**Main Specification:** [`spec.md`](spec.md) (1,747 lines)
**Implementation Notes:** [`IMPLEMENTATION_NOTES.md`](IMPLEMENTATION_NOTES.md) (364 lines)
**User Guide:** [`README.md`](README.md) (312 lines)

---

## Specification Document Structure

### spec.md (Main Technical Specification)

#### Overview (Lines 1-60)
- Purpose and key objectives
- Success metrics
- Links to dependent systems

#### Architecture (Lines 61-215)
- System overview diagram
- Component architecture
- Technology stack breakdown
- Data relationships

#### Database Schema (Lines 216-480)
- Extended `weeks` table with new columns
- New `week_metadata` table schema
- New `nfl_schedule` table schema
- New `week_status_overrides` table
- SQL CREATE statements with constraints and indexes

#### API Specifications (Lines 481-950)
1. **GET /api/weeks** - Get weeks with metadata and current week info
2. **GET /api/current-week** - Auto-detect current week with details
3. **GET /api/weeks/{id}/metadata** - Get rich week metadata
4. **PUT /api/weeks/{id}/status** - Manual status override
5. **POST /api/weeks/generate** - Auto-generate season weeks
6. **GET /api/nfl-schedule** - Get NFL schedule data
7. **PUT /api/weeks/{id}/lock** - Lock week on import (called by Data Import System)
8. **PUT /api/weeks/{id}/import-status** - Update import status with count/timestamp

Each endpoint includes:
- HTTP method and path
- Query/path parameters
- Request body (if applicable)
- Success response example
- Error response example
- Processing logic step-by-step

#### Frontend Components (Lines 951-1200)
1. **WeekSelector** (enhanced)
   - Location: Header
   - Props interface
   - State structure
   - UI features (glow effect, auto-scroll)
   - Responsive behavior

2. **WeekCarousel** (mobile)
   - Location: Main content (mobile only)
   - Swipeable carousel
   - Large week display
   - Status badges

3. **WeekMetadataPanel**
   - Rich metadata display
   - NFL dates, times, ESPN links
   - Import status with tooltip

4. **WeekStatusBadge**
   - Material Design icons
   - Color-coded status (green/gray/orange)
   - Active week glow effect

5. **YearSelector**
   - Year dropdown (2025-2030)
   - Year change handling
   - Week loading

#### UI/UX Design (Lines 1201-1400)
- Design principles (modern, sleek, dark-mode optimized)
- Material Design v5 color palette
- Typography system
- Spacing guidelines
- Animation specifications
- Dark mode specifics
- Responsive breakpoints

#### State Management (Lines 1401-1550)
- Zustand store structure
- WeekState interface
- TanStack Query hooks
- Integration with Data Import System

#### Data Flow (Lines 1551-1700)
- Week selection flow diagram
- Week change flow
- Import status update flow
- Current week auto-detection flow

#### Mobile Considerations (Lines 1701-1850)
- Mobile UX patterns (swipeable carousel recommended)
- Touch interactions (swipe, tap, long-press)
- Performance optimizations
- Responsive images/icons
- Touch-friendly sizing

#### Validation Rules (Lines 1851-1950)
- Backend validation (week, year, status)
- Frontend validation
- Immutability validation

#### Error Handling (Lines 1951-2050)
- Custom exception classes
- Backend error cases
- Frontend error handling
- Error recovery strategies

#### Integration Points (Lines 2051-2150)
- Data Import System integration
- Week locking flow
- Player Pool Context integration
- Phase 2 Lineup History integration

#### Implementation Plan (Lines 2151-2500)
**7 Phases (8-10 hours total):**
1. Database & Backend Setup (3h)
2. Backend Services (2.5h)
3. API Endpoints (2h)
4. Frontend State & Hooks (1.5h)
5. Frontend Components (2h)
6. Integration & Polish (1h)
7. Testing (1h)

Each phase includes:
- Tasks to complete
- Deliverables
- File locations

#### Test Cases (Lines 2501-2850)
8 comprehensive test scenarios:
1. Load weeks for year
2. Auto-status update
3. Week selection
4. Mobile carousel navigation
5. Data import locking
6. Locked week immutability
7. Manual status override
8. Year selection

#### Acceptance Criteria (Lines 2851-3000)
10 must-have requirements:
1. Week management
2. Status management
3. Selection UI
4. Metadata display
5. Status indicators
6. Data immutability
7. Integration
8. Responsive design
9. Performance
10. Dark mode

#### Appendix (Lines 3001-1747)
- NFL schedule seed data for 2025
- ESPN schedule link generator
- Date formatting utilities
- Keyboard navigation support
- Mobile touch gestures

---

## IMPLEMENTATION_NOTES.md Quick Reference

- Specification status and overview
- Core sections summary
- Key features documentation
- Reusable code patterns
- Critical implementation details
- Missing features (Phase 2+)
- Files created
- Next steps

---

## README.md User Guide

- Overview and package contents
- What's included breakdown
- Key deliverables
- Technology stack
- Responsive design grid
- Implementation timeline
- Critical features checklist
- Integration with Data Import System
- Success criteria checklist
- Phase 2+ features
- File structure
- How to use specification
- Version history

---

## Key Sections by Role

### For Backend Developers
- **Start with:** Architecture section (lines 61-215)
- **Then read:** Database Schema (lines 216-480)
- **Then read:** API Specifications (lines 481-950)
- **Reference:** Implementation Plan Phase 1-3 (lines 2151-2500)
- **Reference:** Error Handling (lines 1951-2050)

### For Frontend Developers
- **Start with:** Architecture section (lines 61-215)
- **Then read:** Frontend Components (lines 951-1200)
- **Then read:** UI/UX Design (lines 1201-1400)
- **Then read:** State Management (lines 1401-1550)
- **Reference:** Implementation Plan Phase 4-6 (lines 2151-2500)
- **Reference:** Mobile Considerations (lines 1701-1850)

### For Designers
- **Read:** UI/UX Design section (lines 1201-1400)
- **Review:** Each Component specification with props
- **Check:** Responsive breakpoints and dark mode
- **Validate:** Material Design v5 compliance

### For QA/Testing
- **Read:** Test Cases section (lines 2501-2850)
- **Read:** Acceptance Criteria (lines 2851-3000)
- **Reference:** API Specifications for endpoint testing
- **Reference:** Validation Rules (lines 1851-1950)

### For Project Management
- **Review:** Implementation Timeline (README.md)
- **Check:** Phase breakdown (spec.md lines 2151-2500)
- **Reference:** Success Criteria (README.md)
- **Estimated Effort:** 8-10 hours

---

## Critical Implementation Details

### Week Status Auto-Detection
**Location:** spec.md, line ~1550
```
Active = current week (today matches nfl_slate_date)
Upcoming = future weeks (date > today)
Completed = past weeks (date < today)
Auto-updates on page load + every 60 seconds
```

### Week Locking Flow
**Location:** spec.md, lines 481-550
```
Data Import System → successful import
  ↓
Call: PUT /api/weeks/{week_id}/lock
  ↓
is_locked = true, locked_at = NOW()
  ↓
Frontend updates week object in Zustand
  ↓
Week becomes immutable
```

### Mobile Carousel Implementation
**Location:** spec.md, lines 1701-1850
- Swipeable horizontal carousel recommended
- Preload adjacent weeks
- 60fps target
- React Swipeable library

### NFL Schedule Seed Data
**Location:** spec.md, Appendix (lines 3001+)
- 18 weeks for 2025
- Includes slate dates and kickoff times
- Must be seeded before first use
- Supports 2025-2030

---

## Database Tables Overview

### Extended Tables
- **weeks** - Add: `nfl_slate_date`, `status_override`, `is_locked`, `locked_at`, `metadata`

### New Tables
- **week_metadata** - Rich metadata (kickoff time, ESPN link, import status)
- **nfl_schedule** - NFL schedule seed data (week, date, time)
- **week_status_overrides** - Manual override tracking

**Location in spec.md:** Lines 216-480

---

## API Endpoints Summary

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | /api/weeks | Get all weeks with metadata |
| GET | /api/current-week | Get current week auto-detected |
| GET | /api/weeks/{id}/metadata | Get rich metadata for week |
| PUT | /api/weeks/{id}/status | Set manual status override |
| POST | /api/weeks/generate | Auto-generate season weeks |
| GET | /api/nfl-schedule | Get NFL schedule data |
| PUT | /api/weeks/{id}/lock | Lock week on import |
| PUT | /api/weeks/{id}/import-status | Update import status |

**Location in spec.md:** Lines 481-950

---

## React Components Summary

| Component | Location | Purpose | Breakpoint |
|-----------|----------|---------|-----------|
| WeekSelector | Header | Dropdown week selector | md+ |
| YearSelector | Header | Year dropdown | md+ |
| WeekCarousel | Content | Swipeable carousel | xs, sm |
| WeekMetadataPanel | Sidebar/Panel | Rich metadata | md+ |
| WeekStatusBadge | Various | Status indicator | All |

**Location in spec.md:** Lines 951-1200

---

## Responsive Breakpoints

| Name | Width | Components |
|------|-------|-----------|
| xs | <360px | WeekCarousel |
| sm | 361-600px | WeekCarousel |
| md | 601-960px | WeekSelector (tablet) |
| lg | 961-1280px | WeekSelector (desktop) |
| xl | >1280px | WeekSelector + metadata |

**Location in spec.md:** UI/UX Design section (lines 1201-1400)

---

## Implementation Timeline

| Phase | Hours | Focus |
|-------|-------|-------|
| 1 | 3h | Database setup |
| 2 | 2.5h | Backend services |
| 3 | 2h | API endpoints |
| 4 | 1.5h | Frontend state |
| 5 | 2h | Components |
| 6 | 1h | Integration |
| 7 | 1h | Testing |
| **Total** | **8-10h** | **Production-ready** |

**Location in spec.md:** Lines 2151-2500

---

## Acceptance Criteria Checklist

- [ ] Auto-generate weeks from NFL calendar
- [ ] Auto-status update + manual override
- [ ] Modern Material Design dropdown
- [ ] Mobile swipeable carousel
- [ ] Rich metadata display
- [ ] Material Design icons (no emojis)
- [ ] Week locking on import
- [ ] Dark mode optimized
- [ ] Fully responsive
- [ ] Performance targets (<200ms)

**Location in spec.md:** Lines 2851-3000

---

## File Locations

```
/Users/raybargas/Documents/Cortex/agent-os/specs/2025-10-27-week-management/
├── spec.md (1,747 lines) - Main technical specification
├── IMPLEMENTATION_NOTES.md (364 lines) - Quick reference
├── README.md (312 lines) - User guide
├── SPECIFICATION_INDEX.md (this file) - Navigation guide
└── planning/
    └── raw-idea.md - Original feature request
```

---

## Quick Start for Implementation

1. **Read this file** (2 min) - Get overview
2. **Read README.md** (5 min) - Understand scope
3. **Review Architecture section** (10 min) - Understand design
4. **Review Implementation Plan** (10 min) - Understand phases
5. **Pick a phase** - Start Phase 1 (database setup)
6. **Reference specific sections** - Use table of contents

**Total onboarding time:** ~30 minutes

---

**Document Status:** Complete and verified
**Created:** October 27, 2025
**Total Words:** ~20,000+
**Total Lines:** 2,423
**Ready for Implementation:** YES
