# Week Management Feature - Specification Package

## Overview

This package contains a comprehensive, production-ready specification for the Week Management feature of the Cortex DFS lineup optimization platform.

**Created:** October 27, 2025
**Status:** Ready for Implementation
**Estimated Effort:** 8-10 hours

---

## What's Included

### 1. Main Specification (`spec.md`)
**File Size:** 49 KB | **Lines:** 1,747

The primary technical specification document covering all aspects of the Week Management system:

- **Overview**: Purpose, objectives, success metrics
- **Architecture**: System design, technology stack, data flow diagrams
- **Database Schema**: Extended weeks table + 3 new tables with SQL
- **API Specifications**: 8 REST endpoints with request/response examples
- **Frontend Components**: 5 React components with detailed props/behavior
- **UI/UX Design**: Material Design v5, dark mode, responsiveness
- **State Management**: Zustand store and TanStack Query hooks
- **Data Flow**: Complete user workflows from selection to import
- **Mobile Considerations**: Swipeable carousel pattern with touch gestures
- **Validation Rules**: Input validation for weeks, years, statuses
- **Error Handling**: Custom exceptions and recovery strategies
- **Integration Points**: Connection with Data Import System
- **Implementation Plan**: 7 phases with deliverables (8-10 hours)
- **Test Cases**: 8 comprehensive test scenarios
- **Acceptance Criteria**: 10 must-have requirements
- **Appendix**: NFL schedule seed data, utilities, keyboard navigation

### 2. Implementation Notes (`IMPLEMENTATION_NOTES.md`)
**File Size:** 11 KB

Quick reference guide with:

- Specification overview summary
- Key features documented
- Reusable code patterns from Data Import System
- Critical implementation details
- Files created and next steps
- Success criteria checklist

---

## Key Deliverables

### Database
- Extend existing `weeks` table with 5 new columns
- Create `week_metadata` table (rich metadata)
- Create `nfl_schedule` table (NFL schedule seed data)
- Create `week_status_overrides` table (manual overrides)

### Backend (FastAPI)
- 3 services: WeekManagementService, StatusUpdateService, NFLScheduleService
- 8 REST API endpoints
- Integration with Data Import System (week locking)
- Complete validation and error handling

### Frontend (React)
- 5 new/enhanced components
  - WeekSelector (enhanced with year selector)
  - YearSelector (year dropdown)
  - WeekCarousel (mobile swipeable)
  - WeekMetadataPanel (rich metadata display)
  - WeekStatusBadge (status indicators)
- Zustand state management
- TanStack Query hooks
- Responsive CSS (Material-UI sx prop)
- Dark mode optimized

### Key Features
- **Dynamic Week Generation**: Not hardcoded, based on NFL calendar
- **Smart Status Management**: Auto-update (Active/Upcoming/Completed) + manual override
- **Professional Design**: Material Design v5, dark mode, glow effects
- **Mobile UX**: Swipeable carousel pattern for intuitive navigation
- **Rich Metadata**: NFL dates, kickoff times, ESPN links, import status
- **Data Immutability**: Weeks locked once player data imported
- **Seamless Integration**: Works with Data Import System

---

## Technology Stack

**Backend:**
- FastAPI (Python 3.11+)
- SQLAlchemy 2.0 ORM
- Alembic (migrations)
- PostgreSQL 15

**Frontend:**
- React 18 + TypeScript
- Material-UI v5
- Zustand (state management)
- TanStack Query (data fetching)
- React Swipeable (carousel)

---

## Responsive Design

| Breakpoint | Width | Component |
|-----------|-------|-----------|
| xs | <360px | WeekCarousel (mobile) |
| sm | 361-600px | WeekCarousel (mobile) |
| md | 601-960px | WeekSelector (tablet) |
| lg | 961-1280px | WeekSelector (desktop) |
| xl | >1280px | WeekSelector + metadata |

---

## Implementation Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| 1. Database Setup | 3h | Migrations, schema, seed data |
| 2. Backend Services | 2.5h | WeekManagement, Status, NFLSchedule |
| 3. API Endpoints | 2h | 8 REST endpoints, validation |
| 4. Frontend State | 1.5h | Zustand, hooks, TanStack Query |
| 5. Components | 2h | 5 React components |
| 6. Integration | 1h | Import locking, animations |
| 7. Testing | 1h | Unit, integration, E2E |
| **Total** | **8-10h** | **Production-ready system** |

---

## Critical Features

### 1. Week Status Auto-Detection
```
Active = current week (today matches nfl_slate_date)
Upcoming = future weeks (date > today)
Completed = past weeks (date < today)
Updates on page load + every 60 seconds
```

### 2. Week Locking on Import
```
When: Data Import System successfully imports player data
How: Call PUT /api/weeks/{week_id}/lock
Result: Week becomes immutable, locked_at recorded
```

### 3. Mobile Swipeable Carousel
```
Recommended pattern for mobile (<600px)
Swipe left: next week
Swipe right: previous week
Tap: open metadata modal
Double-tap: jump to current week
```

### 4. Material Design Without Emojis
```
Status badges use Material-UI icons:
- Completed: green checkmark icon
- Pending: gray dash icon
- Error: orange warning icon
Professional appearance, strictly no emojis
```

---

## Integration with Data Import System

The Week Management feature works seamlessly with the existing Data Import System:

1. **User selects week** → WeekSelector stores in Zustand
2. **User initiates import** → ImportDataButton uses selected week
3. **Week mismatch** → Show WeekMismatchDialog
4. **Import succeeds** → Backend calls `PUT /api/weeks/{week_id}/lock`
5. **Frontend updates** → Week locked, status badge shows green checkmark
6. **Week becomes immutable** → Cannot be edited/deleted

---

## Success Criteria

Implementation is complete when all of these are met:

- [ ] All 8 API endpoints working correctly
- [ ] All 5 React components rendering and interactive
- [ ] Mobile carousel smooth (60fps)
- [ ] Dropdown opens in <200ms
- [ ] Week data loads in <500ms
- [ ] Dark mode fully optimized
- [ ] Week locking prevents editing
- [ ] Week status auto-updates correctly
- [ ] All 8 test cases passing
- [ ] Zero known bugs

---

## Phase 2+ Features (Out of Scope)

The following features are intentionally excluded and will be added in Phase 2:

- Replay weeks / view historical lineups
- Calendar view of entire season
- Vegas line integration
- Automated external API fetching
- CSV import support
- Drag-and-drop file upload
- Multiple simultaneous file upload
- Advanced week filtering

---

## File Structure

```
/Users/raybargas/Documents/Cortex/agent-os/specs/2025-10-27-week-management/
├── spec.md                         # Main technical specification (1,747 lines)
├── IMPLEMENTATION_NOTES.md         # Quick reference guide
├── README.md                       # This file
└── planning/
    └── raw-idea.md                 # Original feature request
```

---

## How to Use This Specification

### For Developers
1. Read `spec.md` Overview section (understand purpose)
2. Read Architecture section (understand system design)
3. Read API Specifications section (understand endpoints)
4. Read Frontend Components section (understand UI)
5. Follow Implementation Plan phases in order

### For Designers
1. Read UI/UX Design section
2. Review component specifications with props
3. Check responsive breakpoints
4. Review dark mode guidelines
5. Validate Material Design compliance

### For QA/Testing
1. Read Test Cases section
2. Read Acceptance Criteria section
3. Use as basis for test plan
4. Cross-reference with implementation

### For Project Management
1. Review Implementation Timeline
2. Use Phase breakdown for sprint planning
3. Check Success Criteria for completion definition
4. Reference estimated effort (8-10 hours)

---

## Questions & Clarifications

### Mobile UX Decision
The spec recommends a **swipeable carousel** for mobile as the primary navigation pattern. This is:
- Most intuitive (modern app pattern)
- Smooth and responsive (60fps)
- Accessible (WCAG 2.1 AA)
- Easier to implement than alternatives

Alternative considered: Bottom sheet modal. Current recommendation is better UX.

### Week Generation
Weeks are **dynamically generated** based on NFL calendar data in `nfl_schedule` table:
- NOT hardcoded 1-18 values in code
- Generated from external seed data
- Supports future years (2025-2030)
- Easily updatable without code change

### Data Immutability
Once a week has imported player data:
- `is_locked = true` flag set
- Week becomes read-only
- Cannot be edited or deleted
- Cannot be unlocked by user
- Provides data integrity guarantee

### Dark Mode
- Specification is **dark mode optimized**
- Primary use case is dark theme
- Light mode can be added later if needed
- Material-UI v5 supports both themes

---

## Support & Updates

This specification is **complete and ready for implementation**. If clarifications are needed during development:

1. Refer to this specification first
2. Check IMPLEMENTATION_NOTES.md for quick answers
3. Review relevant section in spec.md for details
4. For conflicts, the Architecture and API Specifications sections are canonical

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-27 | Initial comprehensive specification |

---

**Created by:** Spec Writing Agent
**Status:** Ready for Implementation
**Next Action:** Begin Phase 1 implementation
