# Player Management Feature - Quick Start Guide

## Documents Overview

This specification includes 4 comprehensive documents:

### 1. `spec.md` (2,021 lines) - MAIN SPECIFICATION
The complete, production-ready specification with all details:
- Executive summary
- 10 detailed user stories with acceptance criteria
- Complete technical requirements
- API endpoint specifications
- Component architecture
- Design specifications with color palette
- Performance requirements
- Mobile/responsive design details
- Testing strategy
- Dependencies and timelines

**Start here for:** Development implementation

### 2. `SPEC_SUMMARY.md` (500+ lines) - EXECUTIVE OVERVIEW
High-level summary of key sections:
- Overview and goals
- User stories summary
- Reusable components overview
- Technical architecture highlights
- Design system overview
- Performance targets
- Phase alignment
- Success criteria
- File structure
- 4-week implementation timeline

**Start here for:** Project planning, stakeholder communication

### 3. `REUSABLE_CODE_ANALYSIS.md` (600+ lines) - CODE REUSE GUIDE
Detailed analysis of existing code that can be reused:
- Frontend reusable components (8 items)
- Backend reusable code (4 items)
- Database patterns
- Testing patterns
- Code reduction estimates (~25% reuse)
- Time savings estimates (~16-20 hours)
- Integration checklist

**Start here for:** Technical team, developers, architects

### 4. `QUICK_START.md` (this file) - NAVIGATION GUIDE
Quick reference and navigation guide for developers.

---

## Key Information At a Glance

### The Ask
Build a Player Management feature that allows users to:
1. View all players from current week in a table
2. See unmatched players prominently at top
3. Search, sort, and filter player data
4. Manually map unmatched players to canonical players
5. Create global aliases for future imports
6. Access on mobile with touch optimization

### The Solution
- **Frontend:** React with TanStack Table + Material-UI
- **Backend:** FastAPI (mostly reuse existing unmatched_players_router)
- **Database:** All tables exist, no migrations needed
- **Timeline:** 4 weeks, 145 hours estimated effort
- **Phase:** Phase 1 MVP

### Critical Reuse Opportunities
1. **unmatched_players_router.py** - READY TO USE (POST /map endpoint)
2. **PlayerMatcher service** - READY TO USE (fuzzy_match method)
3. **Material-UI theme** - EXTEND with orange accent color
4. **Zustand store pattern** - ADAPT for filter state
5. **WeekStatusBadge** - ADAPT for player status badge

**Code Reuse Impact:** ~25% reduction in new code, ~16-20 hours saved

---

## For Different Roles

### Product Manager / Stakeholder
1. Read: `SPEC_SUMMARY.md` - Sections: Overview, User Stories, Success Criteria
2. Review: Design specifications for visual consistency
3. Check: Phase alignment and feature scope
4. Confirm: Success criteria and rollout strategy

**Time Needed:** 30 minutes

### Tech Lead / Architect
1. Read: `SPEC_SUMMARY.md` - Full document
2. Review: `REUSABLE_CODE_ANALYSIS.md` - All sections
3. Check: `spec.md` - Technical Approach, Dependencies, Component Architecture
4. Assess: Development timeline, effort estimate, team capacity
5. Identify: Integration points with existing systems

**Time Needed:** 1.5 hours

### Frontend Developer
1. Read: `spec.md` - Sections: User Stories, Component Architecture, API Specifications
2. Review: `REUSABLE_CODE_ANALYSIS.md` - Frontend section
3. Check: Design Specifications for styling details
4. Study: Component prop interfaces in appendices
5. Plan: Component structure and file organization

**Time Needed:** 2 hours

### Backend Developer
1. Read: `spec.md` - Sections: API Specifications, Data Model, Technical Approach
2. Review: `REUSABLE_CODE_ANALYSIS.md` - Backend section (CRITICAL)
3. Check: Database schema and existing tables
4. Study: API endpoint specifications and responses
5. Plan: New endpoints and services needed

**Time Needed:** 1.5 hours

### QA / Test Lead
1. Read: `spec.md` - Sections: User Stories, Testing Strategy, Success Criteria
2. Review: `SPEC_SUMMARY.md` - Testing section
3. Study: Acceptance criteria for each user story
4. Plan: Test cases, test data, test environments
5. Create: Test matrix for mobile/desktop/browsers

**Time Needed:** 1 hour

### Designer / UX Lead
1. Read: `spec.md` - Sections: Visual Design, Design Specifications, Mobile & Responsive Design
2. Review: Color palette, typography, spacing system
3. Check: Component-specific styles (buttons, modals, badges, etc.)
4. Verify: Responsive breakpoints and mobile optimization
5. Create: High-fidelity designs/components if needed

**Time Needed:** 1 hour

---

## Development Quickstart

### Step 1: Setup (Week 1, Days 1-2)
```bash
# 1. Create component directory structure
mkdir -p frontend/src/components/players
mkdir -p frontend/src/hooks/players
mkdir -p tests/components
mkdir -p tests/hooks

# 2. Install TanStack dependencies
npm install @tanstack/react-table@8.11.0 @tanstack/react-virtual@3.0.0

# 3. Update theme with orange accent color
# File: frontend/src/theme.ts
# Change: primary.main from #00d4ff to #ff8c42

# 4. Add /players route to MainLayout
# File: frontend/src/components/layout/MainLayout.tsx
# Add: Route path="/players" element={<PlayerManagementPage />}
```

### Step 2: Backend Endpoints (Week 1-2, Days 3-8)
```bash
# 1. Create players_router.py
# File: backend/routers/players_router.py
# Implement:
#   - GET /api/players/by-week/{week_id}
#   - GET /api/players/unmatched/{week_id}
#   - GET /api/players/search
#   - GET /api/players/suggestions/{player_id}

# 2. Create services
# Files: backend/services/player_management_service.py
#        backend/services/player_alias_service.py

# 3. Register router in main.py
# app.include_router(players_router.router)

# 4. Test endpoints with Postman/curl
```

### Step 3: Frontend Components (Week 2-3)
```bash
# Build in this order:

# 1. PlayerManagementPage (container)
# 2. UnmatchedPlayersSection + UnmatchedPlayerCard
# 3. PlayerTable (with TanStack Table)
# 4. PlayerTableFilters + PlayerSearchBox
# 5. PlayerTableRow (expand functionality)
# 6. PlayerMappingModal + FuzzyMatchSuggestions
# 7. PlayerStatusBadge (status indicator)
# 8. Hooks: usePlayerManagement, usePlayerMapping, usePlayerFiltering

# Reference existing code:
# - Modal pattern: ImportDataButton.tsx
# - Badge pattern: WeekStatusBadge.tsx
# - Store pattern: weekStore.ts
# - Hook pattern: useDataImport.ts
```

### Step 4: Styling & Mobile (Week 3)
```bash
# 1. Apply Material-UI sx prop styling
# Reference: Colors in theme.ts, spacing 8px units
#
# 2. Add responsive styles
# Mobile: < 768px
# Tablet: 768-1024px
# Desktop: > 1024px
#
# 3. Test on mobile devices
# Use Chrome DevTools device emulation
# Test horizontal scroll for tables
# Verify 44x44px tap targets
```

### Step 5: Testing & Polish (Week 4)
```bash
# 1. Unit tests for components and hooks
# Use: Vitest/Jest + React Testing Library
#
# 2. Integration tests for workflows
# Test: Filter + sort, mapping workflow, pagination
#
# 3. E2E tests with Playwright
# Test: Full user journeys, mobile interactions
#
# 4. Performance testing
# Lighthouse: target >= 90 score
# Page load: target < 3 seconds
# Virtual scroll: 60fps with 200 players
#
# 5. Accessibility testing
# WCAG 2.1 Level AA compliance
# Screen reader testing
# Keyboard navigation
```

---

## Key Decisions

### Why TanStack Table?
- Handles 150-200 players efficiently
- Built-in sorting, filtering, column management
- Virtual scrolling support
- Minimal bundle size impact
- Large community, well-documented

### Why React Query?
- Already used in project
- Excellent caching and invalidation
- Automatic retry logic
- DevTools integration
- Familiar to team

### Why Fuzzy Matching at 85%?
- Balances precision vs. recall
- Matches common name variations
- Manual mapping for edge cases
- Prevents false positives

### Why Global Aliases?
- Consistent player matching across all weeks
- No need to re-map same player variations
- Improves data quality over time
- Week-agnostic approach

### Why Orange Accent?
- Specified in design requirements
- High contrast on dark background
- Consistent with Factory.ai / 21st.dev aesthetic
- Used for alerts (high visibility)

---

## Critical Implementation Notes

### DO's ✓
- ✓ Reuse unmatched_players_router endpoints directly
- ✓ Reuse PlayerMatcher.fuzzy_match() for suggestions
- ✓ Use existing Material-UI components and patterns
- ✓ Follow existing error handling patterns
- ✓ Use parameterized SQL queries
- ✓ Implement virtual scrolling for performance
- ✓ Test on real mobile devices
- ✓ Follow TypeScript strict mode

### DON'Ts ✗
- ✗ Don't modify existing table schemas
- ✗ Don't create new database tables (all exist)
- ✗ Don't bypass the fuzzy matching system
- ✗ Don't implement duplicate alias creation
- ✗ Don't render 200+ rows without virtual scroll
- ✗ Don't use hover-only interactions on mobile
- ✗ Don't ignore accessibility requirements
- ✗ Don't commit style changes to theme.ts without review

---

## Common Questions & Answers

### Q: What if unmatched_players_router needs changes?
A: It shouldn't. The router is production-ready. If you need different behavior, create a wrapper service that calls the existing endpoints.

### Q: Do I need to create new database tables?
A: No. All required tables exist: player_pools, unmatched_players, player_aliases, weeks.

### Q: Should I add database indexes?
A: Optional for Phase 1. Performance indexes can be added in Phase 2 if needed (non-blocking change).

### Q: What about offline support?
A: Out of scope for Phase 1. Service worker caching can be added in Phase 2.

### Q: How do I handle the orange accent theme?
A: Update theme.ts primary.main from #00d4ff to #ff8c42. Use theme colors in MUI sx props.

### Q: Can I use Redux instead of Zustand?
A: Use Zustand - it's already in the project. Consistency matters.

### Q: What TanStack Table version?
A: @tanstack/react-table@8.11.0+ (latest is fine, ensure compatibility with project versions)

### Q: Do I need pagination or just virtual scroll?
A: Virtual scroll handles 150-200 players fine. Pagination can be added in Phase 2 if needed.

### Q: What about search debounce?
A: 300ms recommended. Prevents excessive re-renders and API calls.

### Q: How do I handle player photo avatars?
A: Phase 2 feature. Use generic icon/initial for Phase 1.

### Q: Should I cache player data?
A: Yes - React Query with 5 minute stale time. Invalidate on successful mapping.

### Q: What about Excel export?
A: Out of scope. Can be added as Phase 2 feature (no backend changes needed).

---

## File Locations Reference

### Specification Files
- **Main spec:** `/Users/raybargas/Documents/Cortex/agent-os/specs/2025-10-29-player-management/spec.md`
- **Summary:** `/Users/raybargas/Documents/Cortex/agent-os/specs/2025-10-29-player-management/SPEC_SUMMARY.md`
- **Code reuse:** `/Users/raybargas/Documents/Cortex/agent-os/specs/2025-10-29-player-management/REUSABLE_CODE_ANALYSIS.md`

### Existing Code to Reference
- **Unmatched players router:** `/backend/routers/unmatched_players_router.py`
- **Player matcher service:** `/backend/services/player_matcher.py`
- **Week store:** `/frontend/src/store/weekStore.ts`
- **Material-UI theme:** `/frontend/src/theme.ts`
- **Badge component:** `/frontend/src/components/weeks/WeekStatusBadge.tsx`
- **Import button:** `/frontend/src/components/import/ImportDataButton.tsx`

### Where to Create New Files
```
frontend/src/
├─ pages/
│  └─ PlayerManagementPage.tsx (NEW)
├─ components/players/ (NEW)
│  ├─ PlayerTable.tsx
│  ├─ PlayerMappingModal.tsx
│  ├─ UnmatchedPlayersSection.tsx
│  └─ ... (other components)
└─ hooks/
   ├─ usePlayerManagement.ts (NEW)
   ├─ usePlayerMapping.ts (NEW)
   └─ ... (other hooks)

backend/
├─ routers/
│  └─ players_router.py (NEW)
├─ services/
│  ├─ player_management_service.py (NEW)
│  └─ player_alias_service.py (NEW)
└─ schemas/
   └─ player_schemas.py (NEW - optional)
```

---

## Success Metrics

### Development Metrics
- All 10 user stories completed
- > 80% unit test coverage
- 0 console errors on page load
- 0 TypeScript type errors (strict mode)
- All E2E test scenarios passing

### User Experience Metrics
- Page load < 3 seconds
- Virtual scroll maintains 60fps with 200 players
- Sorting/filtering responds < 100ms
- Mapping unmatched player < 2 minutes
- Mobile Lighthouse score >= 90

### Quality Metrics
- WCAG 2.1 Level AA accessibility
- Responsive on mobile (< 768px), tablet, desktop
- 44x44px minimum tap targets on mobile
- No data loss during mapping
- All aliases persist globally

---

## Getting Help

### Technical Questions
- Review `spec.md` section: [Topic you're asking about]
- Check `REUSABLE_CODE_ANALYSIS.md` for code examples
- Look at referenced existing components
- Search codebase for similar patterns

### Design Questions
- Review `spec.md` section: "Design Specifications"
- Check color palette for hex values
- Review responsive breakpoints
- Check component-specific styles

### API Questions
- Review `spec.md` section: "API Specifications"
- Check endpoint request/response examples
- Verify error handling patterns
- Look at existing router for patterns

### Architecture Questions
- Review `spec.md` section: "Technical Approach"
- Check component architecture diagram
- Look at data flow description
- Review dependency list

---

## Next Steps

1. **Review Phase:** Read appropriate sections based on your role (see "For Different Roles" above)
2. **Clarification:** Ask questions about requirements before starting development
3. **Planning:** Create detailed task breakdown in your project management tool
4. **Setup:** Follow "Development Quickstart" section
5. **Development:** Build features in recommended order
6. **Testing:** Test early and often, especially mobile
7. **Review:** Get code review and design review before merge
8. **Deploy:** Follow rollout strategy in spec

---

## Quick Links Within Spec.md

### For Frontend Developers:
- User Stories (line ~150)
- Component Architecture (line ~900)
- API Specifications (line ~1100)
- Design Specifications (line ~1200)
- Performance Considerations (line ~1400)
- Mobile & Responsive Design (line ~1600)

### For Backend Developers:
- Core Requirements (line ~400)
- Data Model & Database Changes (line ~700)
- API Endpoints (line ~1050)
- Technical Approach (line ~550)
- Dependencies (line ~1750)

### For QA/Test:
- Testing Strategy (line ~1500)
- Success Criteria (line ~1900)
- User Stories with Acceptance Criteria (line ~150)

---

## Version & Status

- **Spec Version:** 1.0 - Initial Specification
- **Created:** 2025-10-29
- **Status:** Ready for Development
- **Total Lines:** 3,690 (across 4 documents)
- **Estimated Implementation:** 145 hours (4 weeks)

---

## Sign-Off Checklist

Before starting development, ensure:

- [ ] Product Manager approved user stories and success criteria
- [ ] Tech Lead reviewed technical approach and dependencies
- [ ] Design Lead approved color palette and component styling
- [ ] QA Lead reviewed testing strategy and acceptance criteria
- [ ] Team leads allocated resources (145 hours, 4 weeks)
- [ ] Dependencies verified (TanStack packages available)
- [ ] Database verified (all tables exist)
- [ ] Existing code reviewed (unmatched_players_router, PlayerMatcher)
- [ ] Questions answered and clarifications recorded
- [ ] Development timeline agreed upon

---

**Happy Building! This specification provides everything needed for successful implementation.**

