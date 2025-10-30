# Player Management Specification - Executive Summary

## Overview

A comprehensive 2,021-line specification document has been created for the **Player Management Feature** at `/Users/raybargas/Documents/Cortex/agent-os/specs/2025-10-29-player-management/spec.md`

This specification provides complete guidance for implementing a dedicated player review and management interface that allows users to handle unmatched players from data imports, create global aliases, and maintain player data consistency.

---

## Key Document Sections

### 1. Executive Summary & Goals
- **Phase:** Phase 1 (MVP)
- **Target:** Week of October 29, 2025
- **Core Objective:** Enable efficient unmatched player resolution and global alias management
- **Estimated Effort:** 145 hours (3.6 weeks for 1 developer)

### 2. User Stories & Acceptance Criteria (10 stories)
Comprehensive acceptance criteria for:
- Dashboard access and navigation
- Unmatched player visibility
- Player table with sorting/filtering
- Modal-based mapping workflow
- Mobile responsiveness
- Real-time status updates

### 3. Reusable Components (Extensive Analysis)

#### Frontend Components to Reuse
- **WeekStatusBadge:** Badge styling patterns
- **ImportDataButton:** Modal patterns, notifications
- **MainLayout:** Navigation, layout structure
- **Material-UI Theme:** Color scheme, typography

#### Frontend Hooks to Reuse
- **useWeekStore:** Week selection context
- **useDataImport:** State management patterns
- **Zustand persist middleware:** Filter state persistence

#### Backend Code to Reuse (CRITICAL)
- **unmatched_players_router.py:** Existing endpoints for mapping/ignoring players
  - GET `/api/unmatched-players?import_id={uuid}`
  - POST `/api/unmatched-players/map`
  - POST `/api/unmatched-players/ignore`
- **PlayerMatcher service:** Fuzzy matching (85% threshold) with similarity scoring
- **Database schema:** All required tables exist (player_pools, unmatched_players, player_aliases, weeks)

#### New Components Required (10 frontend, 4 backend)
**Frontend:**
1. PlayerManagementPage (page container)
2. UnmatchedPlayersSection (alert section)
3. UnmatchedPlayerCard (individual card)
4. PlayerTable (TanStack Table implementation)
5. PlayerTableFilters (multi-select controls)
6. PlayerTableRow (expandable row)
7. PlayerSearchBox (instant search)
8. PlayerMappingModal (mapping workflow)
9. FuzzyMatchSuggestions (suggestions list)
10. PlayerStatusBadge (matched/unmatched badge)

**Backend:**
1. PlayerManagementService (query orchestration)
2. PlayerAliasService (alias management)
3. GET /api/players/by-week/{week_id} (new endpoint)
4. GET /api/players/unmatched/{week_id} (new endpoint)

---

## Technical Architecture Highlights

### Frontend Stack
- **UI Framework:** React 18 + TypeScript
- **State Management:** Zustand (existing) + React Query (existing)
- **Table Library:** TanStack Table 8+ (NEW) + TanStack Virtual (NEW)
- **Component Library:** Material-UI 5 (existing)
- **Styling:** MUI sx prop + custom CSS for orange accent theme

### Backend Stack
- **Framework:** FastAPI (existing)
- **Database:** PostgreSQL 12+ with SQLAlchemy (existing)
- **Fuzzy Matching:** RapidFuzz (existing, reuse)
- **No new dependencies needed** for Phase 1

### Data Flow
1. Week selection triggers player fetch
2. React Query caches data (5 min stale time)
3. Local state manages filters/sorting
4. Unmatched section displays at top
5. Player table displays all with virtual scrolling
6. Modal for mapping unmatched players
7. Successful mapping invalidates cache + updates UI

---

## Design System

### Color Palette (Orange Accent Theme)
- **Background:** Black (#0a0a0a)
- **Surface:** Dark Gray (#1a1a2e)
- **Accent:** Orange (#ff8c42)
- **Alert:** Orange-Red (#ff5722)
- **Success:** Green (#4caf50)
- **Text Primary:** White (#ffffff)
- **Text Secondary:** Light Gray (#e5e7eb)

### Key Design Elements
- **Unmatched Alert Box:** Orange border, 10% opacity background
- **Player Cards:** Dark gray with orange accent border on hover
- **Table Styling:** Striped rows, orange hover state, unmatched highlighted
- **Buttons:** Orange background, rounded 8px, 44x44px minimum (mobile)
- **Modal:** Dark container, orange accent header, full-width on mobile

### Responsive Design
- **Mobile (< 768px):** Single column, critical columns only, full-width modals
- **Tablet (768-1024px):** 2-3 columns, horizontal scroll for extras
- **Desktop (> 1024px):** Full multi-column experience, all features

---

## Performance Specifications

### Frontend Performance Targets
- Page Load: < 3 seconds
- Filter/Sort: < 100ms
- Search Debounce: 300ms
- Virtual Scroll: 60fps with 200 players
- Bundle Size: < 100KB gzipped

### Backend Performance Targets
- GET /api/players/by-week: < 500ms
- GET /api/players/unmatched: < 300ms
- POST /api/unmatched-players/map: < 200ms
- Database query (p99): < 300ms

### Performance Techniques
- **Virtual Scrolling:** TanStack Virtual for 150-200 players
- **Component Memoization:** React.memo for expensive renders
- **Code Splitting:** Lazy load PlayerMappingModal
- **Caching:** React Query with stale-while-revalidate pattern
- **Debouncing:** 300ms search input debounce
- **Database Indexes:** Existing indexes on player_pools, optional additions

---

## Database Schema (No Changes Required)

### Existing Tables Used
```
player_pools: id, week_id, player_key, name, team, position, salary, projection, ownership, ceiling, floor, notes, source, uploaded_at
unmatched_players: id, import_id, imported_name, team, position, salary, suggested_player_key, similarity_score, status
player_aliases: id, alias_name, canonical_player_key, created_at, updated_at
weeks: id, season, week_number, status, created_at, updated_at
```

### Optional Performance Indexes
- `player_pools (team, position)`
- `player_pools (name)`
- `unmatched_players (import_id, status)`
- `player_aliases (alias_name)`

**Note:** All required tables exist. No migrations needed for Phase 1.

---

## API Endpoints Summary

### New Endpoints
- **GET /api/players/by-week/{week_id}** - Fetch players with filters/sorting
- **GET /api/players/unmatched/{week_id}** - Fetch unmatched with suggestions
- **GET /api/players/search** - Search players by name
- **GET /api/players/suggestions/{player_id}** - Get fuzzy match suggestions

### Reused Endpoints
- **POST /api/unmatched-players/map** - Map player to canonical (existing)
- **POST /api/unmatched-players/ignore** - Mark as ignored (existing)
- **GET /api/unmatched-players** - List unmatched (existing)

---

## Mobile & Responsive Optimization

### Responsive Breakpoints
- **Mobile (< 768px):** Full-width, critical columns, card-based unmatched
- **Tablet (768-1024px):** Mixed layout, horizontal scroll for extras
- **Desktop (> 1024px):** Full feature set, all columns visible

### Touch Optimization
- 44x44px minimum tap targets
- Full-width modals on mobile
- Horizontal scroll for tables
- No hover-only interactions
- Large input fields (44px min height)

### Mobile Navigation
- Sticky header with week selector
- Breadcrumb or simple title display
- Back button to parent page
- Bottom action buttons for modals

---

## Testing Strategy

### Test Coverage
- **Unit Tests:** > 80% code coverage
  - Components: PlayerTable, Modal, Filters
  - Hooks: usePlayerManagement, usePlayerMapping
  - Services: PlayerManagementService, PlayerAliasService

- **Integration Tests:** All critical paths
  - Filter + sort + search together
  - Modal workflow: open → select → confirm
  - Unmatched card → modal → update

- **E2E Tests:** User stories verified
  - View players page
  - Map unmatched player
  - Filter by position/team
  - Search by name

- **Performance Tests:** All targets met
  - Load test with 200 players
  - Filter/sort response times
  - Virtual scroll 60fps

- **Mobile Tests:** Responsive design
  - Touch targets >= 44x44
  - Modals full-width
  - All interactions work

### Testing Tools
- Frontend: Vitest/Jest, React Testing Library, Playwright
- Backend: pytest with fixtures
- Performance: Lighthouse, Web Vitals
- Accessibility: axe DevTools, WAVE

---

## Phase Alignment

### Phase 0 Completed (Foundations)
- Data Import System + Fuzzy Matching
- Week Management System
- Database schema (all tables)

### Phase 1 (Current)
- **Player Management UI** (this feature)
- Manual player mapping
- Global alias creation
- Player review interface

### Phase 2 (Future)
- Smart Score Engine
- Vegas Lines API
- Historical Stats API
- Advanced analytics (80-20 rule)
- Alias management UI
- Player photos
- Mobile enhancements

---

## Dependencies

### New Frontend Dependencies
```json
{
  "@tanstack/react-table": "^8.11.0",
  "@tanstack/react-virtual": "^3.0.0"
}
```

### Existing Frontend Dependencies (Reused)
- React 18+
- React Router 6+
- Zustand 4+
- TanStack React Query 5+
- Material-UI 5+
- Axios 1+

### Backend Dependencies
- **No new dependencies required for Phase 1**
- Existing: FastAPI, SQLAlchemy, RapidFuzz, etc.

---

## Implementation Timeline

| Week | Dates | Tasks | Hours |
|------|-------|-------|-------|
| 1 | Oct 29 - Nov 4 | Components, routing, backend endpoints | 40 |
| 2 | Nov 5 - Nov 11 | Modal, hooks, integration, unit tests | 40 |
| 3 | Nov 12 - Nov 18 | Mobile, accessibility, performance, E2E | 35 |
| 4 | Nov 19 - Nov 25 | Bug fixes, UAT, deployment | 30 |
| **Total** | | **4 weeks** | **145 hours** |

---

## Success Criteria

### User Experience
- Players page accessible within 1 click
- Unmatched players visible on load
- Mapping takes < 2 minutes
- Mobile fully functional

### Functional
- 100% of unmatched players resolvable
- All aliases persist globally
- No data loss on mapping
- All table features work

### Performance
- Page loads < 3 seconds
- 200 players at 60fps
- Sorting < 100ms
- Filtering < 50ms
- Mapping < 1 second

### Quality
- Zero console errors
- No TypeScript errors
- WCAG 2.1 Level AA accessibility
- All user stories tested
- Mobile Lighthouse >= 90

---

## Key Decisions & Rationale

### Why Reuse unmatched_players_router.py?
- Already implements mapping workflow perfectly
- Handles database transactions and validation
- Fuzzy match suggestions built-in
- No need to reinvent

### Why TanStack Table + Virtual?
- Handles 150-200 players efficiently
- Column sorting/filtering out of box
- Virtual scrolling prevents DOM bloat
- Well-documented, active community

### Why Zustand for filter state?
- Already used in codebase (week store)
- Lighter than Redux
- Simple API, TypeScript support
- Can persist to localStorage if needed

### Why React Query for server state?
- Already used in codebase
- Built-in caching, retry logic
- Sync with backend on invalidation
- Handles loading/error states

### Why Material-UI?
- Already used in codebase
- Dark theme ready
- Accessible components
- Icon library built-in

### Why Fuzzy Matching at 85% threshold?
- Matches spec requirement
- Balances precision vs. recall
- Manual mapping for edge cases
- Aliases prevent future matches

---

## Out of Scope for Phase 1

- Smart Score calculations
- Vegas Lines API integration
- Historical stats display
- Advanced analytics (80-20 rule)
- Alias management interface (view/edit/delete)
- Player photos/avatars
- Full-text search with operators
- Offline support via service workers

---

## Known Constraints

### Technical
- Cannot modify existing table schema (backward compatibility)
- Must work with PostgreSQL 12+
- Must maintain React 18+ compatibility
- No IE11 support

### Performance
- Page must load < 3 seconds
- Table limited to 200 players
- Database queries < 500ms
- No real-time collaboration in Phase 1

### Business
- Must preserve existing import workflows
- No breaking changes to existing APIs
- Maintain data integrity during mapping

---

## File Structure

### Frontend Components (10 new)
```
frontend/src/components/players/
├─ PlayerManagementPage.tsx
├─ UnmatchedPlayersSection.tsx
├─ UnmatchedPlayerCard.tsx
├─ PlayerTable.tsx
├─ PlayerTableFilters.tsx
├─ PlayerTableRow.tsx
├─ PlayerSearchBox.tsx
├─ PlayerMappingModal.tsx
├─ FuzzyMatchSuggestions.tsx
├─ PlayerStatusBadge.tsx
└─ index.ts
```

### Frontend Hooks (4 new)
```
frontend/src/hooks/
├─ usePlayerManagement.ts
├─ usePlayerFiltering.ts
├─ usePlayerSorting.ts
├─ usePlayerMapping.ts
└─ index.ts (updated)
```

### Backend Services (2 new)
```
backend/
├─ services/
│  ├─ player_management_service.py
│  └─ player_alias_service.py
├─ routers/
│  └─ players_router.py
└─ schemas/
   └─ player_schemas.py
```

### Tests (8 new test files)
```
tests/
├─ components/ (3 files)
├─ hooks/ (2 files)
├─ integration/ (1 file)
├─ e2e/ (1 file)
└─ features/ (1 file)
```

---

## Recommended Next Steps

1. **Technical Review:** Review specification with tech lead for feasibility
2. **Design Review:** Confirm orange accent theme and component styling
3. **Dependency Check:** Verify TanStack Table and Virtual are compatible with project
4. **Database Review:** Confirm indexes exist, assess performance impact
5. **Schedule Planning:** Allocate 145 hours across 4-week timeline
6. **Setup:** Create component/hook structure and route configuration
7. **Development:** Build features in priority order (table → modal → filters)
8. **Testing:** Implement tests alongside development

---

## Revision History

| Version | Date | Author | Status |
|---------|------|--------|--------|
| 1.0 | 2025-10-29 | AI Assistant (Claude Code) | Ready for Development |

---

## Contact & Support

For questions about this specification:
- Review the detailed spec.md document (2,021 lines)
- Check individual section headers for deep dives
- Refer to code examples in appendices
- Contact tech lead for architectural decisions

