# Spec Requirements: Testing & Verification Infrastructure

## Initial Description

The user has expressed concern about adding new features without proper visibility into what's actually working. The testing readiness assessment shows:
- 72+ pytest tests written but can't be run (missing requirements.txt)
- Frontend components built but not integrated (no App.tsx)
- Backend API implemented but hard to verify end-to-end
- No Docker setup for reproducible environment
- No E2E testing

**Core Problem Statement:**
"As we drive on more advanced functionality, I'm kind of sitting blind to what actually works, what doesn't, and I feel like we're starting to add code to something that I could have to unwind without proper visualization."

**Current State Context:**
- Backend: FastAPI with 12+ routes implemented, 7 database tables, multiple services
- Frontend: 40+ TypeScript files, Material-UI components, Zustand state management
- Tests: 72+ pytest tests (integration + feature tests), test fixtures ready
- Missing: requirements.txt, package.json, vite config, App component, E2E tests

## Requirements Discussion

### Testing Priority & Approach

**Q1:** What's your priority order for testing verification: Backend FIRST (database, API endpoints), Frontend SECOND (UI components, click flows), or E2E LAST (full workflow)?

**Answer:** Backend FIRST: Verify tables exist, data ingestion works, persistence works. User wants direct SQL database access to see data. Frontend SECOND: Click buttons, use dropdowns, see file import flow in action. E2E LAST: Full workflow verification.

**Q2:** Do you have Docker Desktop installed? Are you comfortable using Docker Compose to run PostgreSQL locally?

**Answer:** User has Docker Desktop installed but not familiar with Docker Compose. CRITICAL PAIN POINT: Last time, local dev worked great but cloud deployment had issues that didn't show up locally. User wants something that will translate to cloud deployment (not throwaway). RECOMMENDATION: Use Docker Compose to mirror cloud environment and prevent local-vs-cloud mismatches.

**Q3:** For backend verification, do you want direct SQL database access (like pgAdmin, DBeaver, or similar) to see the data yourself, or a simple web dashboard showing "Tables created, X records inserted"?

**Answer:** Direct SQL database access (pgAdmin, DBeaver, or similar). User is comfortable with SQL. Backend: Direct SQL database access. Frontend: Actual clickable UI - no fancy dashboard needed. User wants to SEE the data themselves, not rely on abstracted dashboards.

**Q4:** For the frontend, should we follow your existing design standards (dark mode, Material Design, mobile-first) or create a basic testing-focused MVP interface?

**Answer:** Dark mode, modern, sleek Material Design. Mobile-first (user will heavily use on mobile). ABSOLUTELY NO EMOJIS (user learned this lesson from last build). Not MVP-looking - build it properly from the start.

**Q5:** Is timeline a constraint? Should we prioritize speed (get testing running ASAP) or completeness (proper setup that scales)?

**Answer:** Not a constraint (AI-assisted development is fast). Build it properly from the start.

### Existing Code to Reference

**Similar Features Identified:**
User did not identify specific similar features to reference, as this is infrastructure setup rather than feature development.

### Follow-up Questions

No follow-up questions were needed. User provided comprehensive answers covering all critical decision points.

## Visual Assets

### Files Provided:
No visual assets provided.

### Visual Insights:
No visual assets to analyze.

## Requirements Summary

### Functional Requirements

#### Phase 1: Backend Verification Infrastructure
**Goal:** User can directly see database tables, verify data persistence, run tests

**Backend Testing Setup:**
- Create `backend/requirements.txt` with all Python dependencies
  - FastAPI, SQLAlchemy, Alembic, pytest, pandas, openpyxl, rapidfuzz, PuLP
  - Include version pinning for stability
- Ensure pytest tests are runnable
  - Verify all 72+ existing tests can execute
  - Fix any import or dependency issues
  - Provide clear test output showing pass/fail status
- Database verification tooling
  - Docker Compose setup for PostgreSQL (port 5432)
  - pgAdmin or DBeaver connection instructions
  - Database initialization scripts (create schema, run migrations)
  - Seed data scripts for testing (sample week, sample players)

**Direct Database Access:**
- User wants to run SQL queries directly against PostgreSQL
- View table schemas, row counts, data contents
- Verify data ingestion worked correctly (see actual player records, historical stats, etc.)
- Confirm relationships between tables (foreign keys working)

**Success Criteria:**
- User can run `docker-compose up` and PostgreSQL starts
- User can connect via pgAdmin/DBeaver and see all 7 tables
- User can run `pytest` and see all tests pass
- User can execute SQL queries to inspect data directly

#### Phase 2: Frontend Integration & Verification
**Goal:** User can click through a working UI, see components render, interact with forms

**Frontend Integration:**
- Create `frontend/package.json` with all dependencies
  - React 18, Material-UI v5, Zustand, TanStack Query, React Router v6
  - Vite, TypeScript, ESLint, Prettier
  - Include version pinning for stability
- Create `frontend/vite.config.ts` for dev server and build configuration
- Create `frontend/src/App.tsx` as main application component
  - Integrate React Router with routes for dashboard, players, smart score, lineups
  - Material-UI dark theme configuration
  - Zustand store integration
  - Layout structure with WeekSelector, MainLayout, navigation
- Wire up existing components
  - Connect ImportDataButton to backend API
  - Connect WeekSelector to week management API
  - Create placeholder pages for each route

**Design Standards:**
- Material Design 3 components (MUI v5)
- Dark mode (background: `#0f0f1a`, surface: `#1a1a2e`, primary: `#00d4ff`, accent: `#7c3aed`)
- Mobile-first responsive layout
- NO EMOJIS anywhere in UI
- Clean, modern, professional aesthetic (not MVP-looking)

**Success Criteria:**
- User can run `npm install && npm run dev` and see UI at localhost:5173
- User can click Week Selector dropdown and see weeks 1-18
- User can click Import Data button and select file (triggers API call)
- User can navigate between routes (dashboard, players, lineups, etc.)
- UI renders correctly on mobile viewport (390x844)

#### Phase 3: End-to-End Testing Setup
**Goal:** Automated verification of complete user workflows

**E2E Testing Framework:**
- Install Playwright for end-to-end tests
- Create test scenarios for core workflows:
  - Week selection and persistence
  - File upload (DKSalaries, LineStar, NFL Stats)
  - Player data viewing and filtering
  - Smart Score calculation
  - Lineup generation and export
- Headless browser tests that can run in CI/CD
- Screenshot capture on test failures for debugging

**Success Criteria:**
- User can run `npm run test:e2e` and see full workflow tests pass
- Tests verify data flows from upload → database → UI display
- Test failures provide clear error messages and screenshots

### Reusability Opportunities

**Existing Infrastructure to Leverage:**
- Backend routers and services are already implemented
- Database schema is defined (7 tables via Alembic migrations)
- Frontend components are built (WeekSelector, ImportDataButton, etc.)
- Test fixtures and database setup utilities exist in `tests/conftest.py`

**Docker Compose Strategy:**
- Mirror cloud deployment architecture (Phase 3 roadmap uses Railway/Render)
- PostgreSQL container configuration should match cloud PostgreSQL version
- Environment variable management (`.env` file) should match cloud setup
- This prevents "works locally but breaks in cloud" scenarios from last build

### Scope Boundaries

**In Scope:**
- Backend: requirements.txt, pytest execution, Docker Compose, database access tooling
- Frontend: package.json, vite.config.ts, App.tsx, routing, component integration
- E2E: Playwright setup, core workflow tests
- Documentation: Setup instructions, testing guide, verification checklist
- Docker: PostgreSQL container, development environment setup
- Database tooling: pgAdmin/DBeaver connection guide

**Out of Scope:**
- New feature development (stick to infrastructure only)
- UI redesign or component refactoring (use existing components as-is)
- Performance optimization (focus on making it work first)
- Advanced testing (load tests, security tests, performance benchmarks)
- CI/CD pipeline setup (that's Phase 3 per roadmap)
- Cloud deployment (that's Phase 3 per roadmap)
- Authentication/authorization (that's Phase 3 per roadmap)

**Future Enhancements (Mentioned but Deferred):**
- GitHub Actions CI/CD pipeline
- Automated database backups
- Performance monitoring and logging
- Advanced E2E test coverage beyond core workflows

### Technical Considerations

**Critical Constraint: Local-vs-Cloud Parity**
- Last build had major issues where local dev worked but cloud deployment failed
- Docker Compose MUST mirror cloud environment to prevent this
- PostgreSQL version in Docker should match Railway/Render's PostgreSQL version
- Environment variable patterns should match cloud deployment patterns
- Database connection strings should use same format locally and in cloud

**Technology Stack (from tech-stack.md):**
- Backend: Python 3.11+, FastAPI, SQLAlchemy 2.0, Alembic, pytest
- Frontend: React 18, TypeScript, Vite, Material-UI v5, Zustand, TanStack Query, React Router v6
- Database: PostgreSQL 15
- Containerization: Docker, Docker Compose
- Testing: pytest (backend), Vitest (frontend unit), Playwright (E2E)

**Development Environment:**
- macOS (Darwin 24.6.0)
- Docker Desktop installed
- Git repository at `/Users/raybargas/Documents/Cortex`
- Current branch: main

**Database Schema (7 Tables):**
1. `weeks` - Week management (season, week_number, status)
2. `player_pools` - Player data per week (salary, projections, ownership)
3. `historical_stats` - NFL stats by player and week
4. `vegas_lines` - Implied team totals, spreads, over/unders
5. `generated_lineups` - Saved lineup configurations
6. `weight_profiles` - Smart Score weight configurations
7. `player_aliases` - Fuzzy name matching resolution

**Existing Test Coverage:**
- 72+ pytest tests already written
- Integration tests for week management, data import, NFL schedule
- Feature tests for week system behavior
- Test fixtures in `tests/conftest.py` for database setup

**Integration Points:**
- Backend API endpoints: 12+ routes across week_router, import routes, player routes
- Frontend-backend communication via REST API (FastAPI serves, React consumes)
- Database migrations via Alembic (2 existing migrations: weeks system, NFL schedule seed)
- File upload handling: XLSX parsing with pandas/openpyxl

**Performance Targets (from mission.md):**
- Generate 10 lineups in <10 seconds
- Complete workflow in <20 minutes
- Smart Score recalculation in <1 second
- Mobile UI fully functional and responsive

**Design System Requirements:**
- Material Design 3 (MUI v5)
- Dark mode ONLY (no light mode needed)
- Color palette:
  - Background: `#0f0f1a` (deep navy/black)
  - Surface: `#1a1a2e` (panels)
  - Primary: `#00d4ff` (cyan - data emphasis)
  - Accent: `#7c3aed` (purple - AI features)
  - Text: `#e5e7eb` (light gray)
- Mobile-first responsive (390x844 mobile, 1024x768 tablet, 1920x1080 desktop)
- NO EMOJIS (critical user requirement)

**Similar Code Patterns to Follow:**
- Week management implementation (completed feature) shows good patterns for:
  - Backend service architecture (WeekManagementService)
  - API router design (week_router.py)
  - Frontend component structure (WeekSelector, WeekNavigation)
  - Zustand state management (weekStore.ts)
  - Material-UI styling patterns (dark theme, responsive layout)

## Phased Implementation Approach

### Phase 1: Backend Verification (Week 1)
**What Will Be Built:**
1. `backend/requirements.txt` - Complete Python dependency manifest
2. `docker-compose.yml` - PostgreSQL container setup (port 5432)
3. `.env.example` - Template for environment variables
4. Database setup scripts - Automated schema creation and sample data
5. Test execution fixes - Ensure all 72+ pytest tests run successfully
6. pgAdmin/DBeaver connection guide - Step-by-step database access instructions

**Tools Used:**
- Docker Compose (PostgreSQL 15 container)
- pgAdmin or DBeaver (user's choice for SQL client)
- pytest (Python test framework)
- PostgreSQL client libraries

**User Verification Steps:**
1. Run `docker-compose up -d` → PostgreSQL container starts
2. Connect pgAdmin/DBeaver to localhost:5432 → See 7 database tables
3. Run SQL query `SELECT COUNT(*) FROM weeks;` → See row counts
4. Run `pytest -v` → See all tests pass with detailed output
5. Run `pytest tests/integration/test_week_api_endpoints.py -v` → See specific test module results
6. Inspect database schema → Verify foreign keys, indexes, constraints

**How This Prevents Local-vs-Cloud Mismatch:**
- Docker Compose uses same PostgreSQL version as Railway/Render (PostgreSQL 15)
- Environment variables pattern matches cloud deployment (DATABASE_URL format)
- Connection string format identical to cloud (postgresql://user:pass@host:port/db)
- Database initialization scripts can be reused in cloud deployment

### Phase 2: Frontend Integration (Week 2)
**What Will Be Built:**
1. `frontend/package.json` - Complete Node.js dependency manifest
2. `frontend/vite.config.ts` - Vite configuration (dev server, build settings, proxy to backend)
3. `frontend/src/App.tsx` - Main application component with routing
4. `frontend/src/main.tsx` - Entry point with MUI theme provider
5. `frontend/src/theme.ts` - Material-UI dark theme configuration
6. Route components - Placeholder pages for dashboard, players, smart score, lineups
7. API integration - Connect existing components to FastAPI backend

**Tools Used:**
- Vite (dev server, HMR, build tool)
- Material-UI v5 (component library, dark theme)
- React Router v6 (client-side routing)
- TanStack Query (API data fetching)
- Zustand (state management)

**User Verification Steps:**
1. Run `npm install` → Dependencies install successfully
2. Run `npm run dev` → Vite dev server starts at localhost:5173
3. Open browser to localhost:5173 → See dark mode UI render
4. Click Week Selector dropdown → See weeks 1-18, select Week 9
5. Navigate to /players route → See placeholder player pool page
6. Click Import Data button → File picker opens, select XLSX file
7. Test on mobile viewport (Chrome DevTools) → UI responsive at 390x844

**How This Prevents Local-vs-Cloud Mismatch:**
- Vite build output is static files (same as what's deployed to cloud)
- API proxy configuration in vite.config.ts shows how frontend will call backend
- Environment variable management (VITE_API_URL) matches cloud deployment pattern
- Material-UI SSR preparation (if needed in Phase 3 for Next.js migration)

### Phase 3: E2E Testing (Week 3)
**What Will Be Built:**
1. Playwright configuration and installation
2. E2E test suite covering core workflows:
   - Week selection persistence test
   - DKSalaries file upload and parsing test
   - Player data display and filtering test
   - Smart Score calculation test
   - Lineup generation and export test
3. Test fixtures for sample data files (test XLSX files)
4. Screenshot capture on failure for debugging
5. Headless browser execution for CI/CD readiness

**Tools Used:**
- Playwright (E2E testing framework)
- Chromium (headless browser)
- Test data fixtures (sample XLSX files)

**User Verification Steps:**
1. Run `npm run test:e2e` → Playwright launches, runs all E2E tests
2. Watch browser automation (optional headed mode) → See clicks, navigation, file uploads
3. Review test results → See pass/fail status for each workflow
4. If test fails → See screenshot in test-results folder showing exact failure point
5. Run specific workflow test → `npm run test:e2e -- week-selection.spec.ts`

**How This Prevents Local-vs-Cloud Mismatch:**
- E2E tests verify full stack integration (frontend → backend → database)
- Tests can run against localhost OR cloud URL (environment variable)
- Same tests that verify local setup can verify cloud deployment
- Screenshots provide visual proof that UI renders correctly

## Success Criteria Summary

### Phase 1 Success Criteria
- [x] User can start PostgreSQL with one command (`docker-compose up`)
- [x] User can connect SQL client to localhost:5432 and query tables directly
- [x] User can run `pytest` and see all 72+ tests pass
- [x] User can inspect database schema, see 7 tables with correct structure
- [x] User can verify data persistence (upload data, query to confirm it's saved)

### Phase 2 Success Criteria
- [x] User can start frontend dev server with `npm run dev`
- [x] User can open browser to localhost:5173 and see dark mode UI
- [x] User can interact with Week Selector (dropdown, select week, persist selection)
- [x] User can click Import Data button (file picker opens, API call triggers)
- [x] User can navigate between routes (dashboard, players, lineups)
- [x] UI renders correctly on mobile viewport (responsive design verified)
- [x] NO EMOJIS appear anywhere in UI

### Phase 3 Success Criteria
- [x] User can run `npm run test:e2e` and see workflow tests pass
- [x] Tests verify data flows from upload → database → UI display
- [x] Test failures provide screenshots for debugging
- [x] Core workflows automated (week selection, file upload, lineup generation)

### Overall Success Criteria
- User has full visibility into what works at each layer (backend, frontend, E2E)
- User can confidently add new features knowing tests will catch regressions
- Local development environment mirrors cloud deployment (no surprises when deploying)
- All verification can be done by user directly (SQL queries, browser clicks, test output)
