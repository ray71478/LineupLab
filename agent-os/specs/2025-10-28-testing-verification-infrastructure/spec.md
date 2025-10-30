# Specification: Testing & Verification Infrastructure

## Goal

Build a comprehensive testing and verification infrastructure that gives the developer complete visibility into what's working at every layer (backend, frontend, end-to-end) of the Cortex DFS Lineup Optimizer application, preventing the "works locally but breaks in cloud" issues from previous deployments.

## User Stories

- As a developer, I want to start the entire application stack with one Docker command so I can verify the full system works together
- As a developer, I want to connect directly to PostgreSQL with a SQL client so I can see actual data and verify persistence without abstractions
- As a developer, I want to run all 72+ pytest tests successfully so I can verify backend logic and data processing is correct
- As a developer, I want to start the frontend dev server and click through a working UI so I can verify components integrate properly
- As a developer, I want to run end-to-end tests that verify complete workflows so I can catch integration issues before deployment
- As a developer, I want local development to mirror cloud deployment architecture so deployment surprises are eliminated

## Core Requirements

### Phase 1: Backend Verification Infrastructure (Priority: Highest)

**Database Environment:**
- Docker Compose configuration with PostgreSQL 15 container matching cloud deployment version
- Direct SQL database access via pgAdmin or DBeaver connection guide
- Database initialization scripts that create schema and run Alembic migrations
- Sample seed data scripts for testing (weeks, player pools, historical stats)
- Environment variable management using .env file pattern matching cloud setup

**Python Dependencies:**
- Complete requirements.txt file with all backend dependencies pinned to specific versions:
  - FastAPI, Uvicorn, SQLAlchemy 2.0, Alembic
  - pytest, pytest-cov for testing
  - pandas, openpyxl for data processing
  - rapidfuzz for player name matching
  - PuLP for lineup optimization
  - python-dotenv for environment variables
- Dependencies organized by category (web framework, database, data processing, testing, optimization)

**Test Execution:**
- All 72+ existing pytest tests runnable with single `pytest` command
- Clear test output showing pass/fail status with verbose mode
- Test fixtures from conftest.py working correctly (db_engine, db_session, sample data files)
- Integration tests verifying week management, data import, NFL schedule services
- Feature tests verifying week system behavior and data persistence

**Local-vs-Cloud Parity:**
- PostgreSQL version matches Railway/Render cloud deployment (PostgreSQL 15)
- Database connection string format identical to cloud (postgresql://user:pass@host:port/db)
- Environment variable patterns match cloud deployment (DATABASE_URL)
- Database initialization approach reusable in cloud deployment

### Phase 2: Frontend Integration & Verification (Priority: High)

**Node.js Dependencies:**
- Complete package.json with all frontend dependencies:
  - React 18, React DOM
  - Material-UI v5 (core, icons, lab components)
  - Zustand for state management
  - TanStack Query v5 for API data fetching
  - React Router v6 for client-side routing
  - TypeScript, Vite, ESLint, Prettier for development
- Scripts for dev server, build, preview, lint, type-check

**Vite Configuration:**
- vite.config.ts with TypeScript plugin, React plugin
- API proxy configuration pointing to FastAPI backend (localhost:8000)
- Build output directory configuration
- Dev server port configuration (5173)
- HMR (Hot Module Replacement) enabled

**Application Entry Point:**
- main.tsx as entry point rendering App component with React.StrictMode
- Material-UI ThemeProvider with dark theme configuration
- TanStack QueryClient provider for API data fetching
- React Router BrowserRouter for routing

**Main Application Component:**
- App.tsx integrating existing components into cohesive application
- React Router routes for:
  - /dashboard - Main dashboard (placeholder)
  - /players - Player pool view (placeholder)
  - /smart-score - Smart Score configuration (placeholder)
  - /lineups - Lineup generator (placeholder)
  - / - Redirect to dashboard
- MainLayout component with header containing WeekSelector
- Integration of existing Zustand weekStore for state management
- Error boundary for graceful error handling

**Material-UI Dark Theme:**
- Background color: #0f0f1a (deep navy/black)
- Surface color: #1a1a2e (panels and cards)
- Primary color: #00d4ff (cyan - data emphasis)
- Secondary color: #7c3aed (purple - AI features)
- Text color: #e5e7eb (light gray)
- Dark mode ONLY (no light mode toggle)
- NO EMOJIS anywhere in UI (critical requirement)

**Responsive Design:**
- Mobile-first approach with breakpoints:
  - Mobile: 390x844 (primary viewport, user will heavily use mobile)
  - Tablet: 1024x768
  - Desktop: 1920x1080
- Material-UI responsive grid system (Grid, Container)
- Responsive typography scaling
- Touch-friendly UI elements (minimum 44px touch targets)

**Component Integration:**
- Wire existing WeekSelector component to header
- Connect ImportDataButton to backend API endpoints
- Integrate existing week management components (WeekNavigation, WeekStatusBadge)
- Use existing Zustand weekStore for global state
- TanStack Query hooks for API calls to backend

### Phase 3: End-to-End Testing Infrastructure (Priority: Medium)

**Playwright Setup:**
- Install Playwright with Chromium browser
- playwright.config.ts configuration:
  - Base URL configurable via environment variable (local or cloud)
  - Headless mode for CI/CD, headed mode for debugging
  - Screenshot on failure for debugging
  - Video recording on test failure
  - Multiple browser support (Chromium, Firefox, WebKit)

**E2E Test Scenarios:**
- Week selection and persistence test:
  - Select week from dropdown
  - Verify Zustand state updates
  - Verify selection persists across page navigation
- File upload workflow test:
  - Select week
  - Click Import Data button
  - Select DKSalaries XLSX file
  - Verify API call triggered
  - Verify data appears in database (backend query)
  - Verify player count displayed in UI
- Player data viewing test:
  - Navigate to /players route
  - Verify player table renders
  - Test filtering and sorting
  - Verify data matches backend response
- Smart Score calculation test (future):
  - Navigate to /smart-score route
  - Adjust weight sliders
  - Verify Smart Score recalculates
  - Verify recalculation takes <1 second
- Lineup generation workflow test (future):
  - Navigate to /lineups route
  - Configure lineup generation settings
  - Click generate button
  - Verify 10 lineups generated in <10 seconds
  - Verify lineups exportable to CSV

**Test Fixtures:**
- Sample XLSX files for testing (DKSalaries, LineStar, NFL Stats)
- Reuse fixtures from backend conftest.py (create_draftkings_xlsx, create_linestar_xlsx, create_comprehensive_stats_xlsx)
- Database seed data for predictable test scenarios

## Visual Design

No mockups provided. Follow existing design standards from completed features:

**Design References:**
- WeekSelector component: Dark theme, Material-UI Select, status badges, tooltips
- WeekNavigation component: Navigation patterns, mobile-responsive layout
- Existing week management UI: Professional, clean, no emojis

**Color Scheme:**
- Background: #0f0f1a
- Surface: #1a1a2e
- Primary: #00d4ff
- Secondary: #7c3aed
- Text: #e5e7eb

**Typography:**
- Font family: Roboto (Material-UI default)
- Headings: Roboto, weight 500-700
- Body: Roboto, weight 400
- No decorative fonts or emojis

## Reusable Components

### Existing Code to Leverage

**Backend Infrastructure:**
- main.py: FastAPI app setup, CORS middleware, router registration, database session management
- routers: week_router, import_router, import_history_router, unmatched_players_router
- services: week_management_service, nfl_schedule_service, status_update_service, data_importer, player_matcher, validation_service
- Database schema: 7 tables defined via Alembic migrations (weeks, player_pools, historical_stats, import_history, etc.)
- Test fixtures: conftest.py with db_engine, db_session fixtures and sample data generators

**Frontend Components:**
- WeekSelector: Dropdown for selecting current week (1-18) with metadata tooltips
- WeekStatusBadge: Status indicator badges for weeks (active, upcoming, completed)
- WeekNavigation: Navigation UI for week management
- ImportDataButton: File upload button component
- Zustand weekStore: Global state management for current year, current week, weeks list
- TanStack Query patterns: API data fetching hooks (useWeeks, useCurrentWeek)

**Database Patterns:**
- PostgreSQL connection via SQLAlchemy engine
- Session management with SessionLocal factory
- Database URL from environment variable (DATABASE_URL)
- Connection pooling configuration (pool_size=10, max_overflow=20)

**Testing Patterns:**
- pytest fixtures for database setup/teardown
- SQLite in-memory database for fast test execution
- Sample XLSX file generators (create_linestar_xlsx, create_draftkings_xlsx, create_comprehensive_stats_xlsx)
- verify_import_success helper for asserting database state

### New Components Required

**Docker Compose Configuration:**
- docker-compose.yml defining PostgreSQL 15 service
- Reason: No existing containerization setup; needed for reproducible environment and local-vs-cloud parity

**Backend Requirements File:**
- requirements.txt with complete dependency manifest
- Reason: File doesn't exist; tests can't run without it

**Frontend Package Configuration:**
- package.json with complete Node.js dependency manifest
- Reason: File doesn't exist; frontend can't be built or run

**Frontend Build Configuration:**
- vite.config.ts for Vite build tool configuration
- Reason: File doesn't exist; frontend dev server can't start

**Frontend Entry Points:**
- main.tsx as application entry point with providers
- App.tsx as main application component with routing
- Reason: Files don't exist; no way to render and integrate existing components

**Frontend Theme Configuration:**
- theme.ts defining Material-UI dark theme with specified color palette
- Reason: Need centralized theme matching design standards

**E2E Test Configuration:**
- playwright.config.ts for Playwright test runner
- Reason: No E2E testing infrastructure exists

**Database Setup Scripts:**
- init_db.sh or similar for automated database initialization
- Reason: Need convenient way to create schema and seed data for development

**Environment Configuration:**
- .env.example template showing required environment variables
- Reason: Document environment setup for local and cloud deployment

## Technical Approach

### Architecture Decisions

**Docker Compose for PostgreSQL:**
- Use official PostgreSQL 15 Docker image matching cloud version
- Expose port 5432 for direct SQL client access (pgAdmin, DBeaver)
- Volume mount for data persistence between container restarts
- Environment variables for database credentials (POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB)
- Health check to verify database ready before running migrations

**Python Dependency Management:**
- Use requirements.txt (not Poetry or Pipenv) for simplicity
- Pin all major versions, allow patch updates (e.g., fastapi>=0.104.0,<0.105.0)
- Organize dependencies by category with comments
- Include both runtime and development dependencies in single file

**Frontend Build Tool:**
- Use Vite (not Create React App or Next.js) for fast HMR and build performance
- TypeScript for type safety
- ESLint + Prettier for code quality
- Proxy API requests to FastAPI backend during development

**State Management:**
- Zustand for global state (already established pattern)
- TanStack Query for server state (already established pattern)
- React Context for UI state (theme, layout preferences)

**Testing Strategy:**
- Unit tests: pytest for backend logic, Vitest for frontend components (Phase 3)
- Integration tests: pytest testing full API endpoints with database
- E2E tests: Playwright testing complete user workflows
- Test pyramid: Many unit tests, some integration tests, few E2E tests

**Local-vs-Cloud Parity Strategy:**
- Same PostgreSQL version (15) locally and in cloud
- Same connection string format (postgresql://...)
- Same environment variable names (DATABASE_URL)
- Docker Compose mirrors cloud architecture (separate containers for DB, backend, frontend)
- Use same Alembic migrations locally and in cloud

### Database Initialization Approach

1. Start PostgreSQL container via Docker Compose
2. Wait for database to be healthy (health check)
3. Run Alembic migrations to create schema: `alembic upgrade head`
4. Optionally run seed script to populate initial data (weeks, NFL schedule)
5. Verify tables created: Connect with SQL client and query `SELECT * FROM weeks;`

### Frontend Architecture

**File Structure:**
```
frontend/
├── src/
│   ├── main.tsx              # Entry point with providers
│   ├── App.tsx               # Main app component with routing
│   ├── theme.ts              # Material-UI dark theme
│   ├── components/           # Existing components
│   │   ├── layout/           # Layout components (WeekSelector, MainLayout)
│   │   ├── import/           # Import components (ImportDataButton)
│   │   ├── weeks/            # Week components (WeekStatusBadge)
│   │   └── index.ts          # Component exports
│   ├── pages/                # Route pages (new)
│   │   ├── DashboardPage.tsx
│   │   ├── PlayersPage.tsx
│   │   ├── SmartScorePage.tsx
│   │   └── LineupsPage.tsx
│   ├── hooks/                # Custom hooks (existing)
│   ├── store/                # Zustand stores (existing weekStore)
│   └── utils/                # Utility functions
├── vite.config.ts            # Vite configuration
├── package.json              # Dependencies and scripts
└── tsconfig.json             # TypeScript configuration
```

**Routing Strategy:**
- Use React Router v6 with BrowserRouter
- Define routes in App.tsx using <Routes> and <Route> components
- Lazy load route components for code splitting: `const DashboardPage = React.lazy(() => import('./pages/DashboardPage'))`
- Use Suspense for loading states during lazy loading
- 404 page for unknown routes

**API Integration Pattern:**
- TanStack Query hooks for all API calls
- Example: `useWeeks()` hook fetching weeks from `/api/weeks`
- Query keys for cache invalidation (e.g., ['weeks', year])
- Mutations for data modification (e.g., `useMutation` for file upload)
- Automatic retry on failure, stale-while-revalidate caching

### Testing Strategy Details

**Backend Testing:**
- Run tests in isolated environment using SQLite in-memory database
- Each test function gets fresh database via db_engine and db_session fixtures
- Verify API endpoints return correct status codes and response structure
- Verify database state changes (row counts, foreign keys, data integrity)
- Test error handling (invalid input, missing data, database errors)

**Frontend Testing (Phase 3):**
- Vitest for unit testing React components
- React Testing Library for rendering and interacting with components
- Mock API responses using MSW (Mock Service Worker)
- Test user interactions (clicks, form input, navigation)
- Snapshot tests for component UI stability

**E2E Testing:**
- Playwright for full browser automation
- Tests run against running frontend and backend
- Use test database (separate from development database)
- Clean database before each test for isolation
- Capture screenshots and videos on failure for debugging

## Success Criteria

### Phase 1 Success Criteria (Backend Verification)

- Developer can run `docker-compose up -d` and PostgreSQL container starts successfully
- Developer can connect pgAdmin or DBeaver to localhost:5432 with credentials from .env file
- Developer can query database and see all 7 tables (weeks, player_pools, historical_stats, vegas_lines, generated_lineups, weight_profiles, player_aliases)
- Developer can run `pip install -r requirements.txt` and all dependencies install without errors
- Developer can run `pytest -v` and see all 72+ tests pass with detailed output
- Developer can run `pytest tests/integration/test_week_api_endpoints.py -v` and see specific test module pass
- Developer can inspect database schema with SQL client and verify foreign keys, indexes, constraints match Alembic migrations
- Developer can run Alembic migrations with `alembic upgrade head` and schema is created correctly
- Developer can seed NFL schedule data and query to verify 54 rows (18 weeks × 3 years)

### Phase 2 Success Criteria (Frontend Integration)

- Developer can run `npm install` and all dependencies install without errors
- Developer can run `npm run dev` and Vite dev server starts at http://localhost:5173
- Developer can open browser to localhost:5173 and see dark mode UI render correctly
- Dark theme colors match specification (#0f0f1a background, #00d4ff primary, #7c3aed secondary)
- NO EMOJIS appear anywhere in UI (critical requirement)
- Developer can click Week Selector dropdown and see weeks 1-18 with status badges
- Developer can select a week and verify Zustand state updates (check with React DevTools)
- Developer can navigate between routes (/dashboard, /players, /smart-score, /lineups) and see placeholder pages render
- Developer can click Import Data button and file picker opens (API call not required to pass yet, just UI interaction)
- UI renders correctly on mobile viewport (390x844) using Chrome DevTools mobile emulation
- All Material-UI components render correctly with dark theme
- Week selector tooltips display metadata (kickoff time, import status, player count)

### Phase 3 Success Criteria (E2E Testing)

- Developer can run `npm run test:e2e` and Playwright launches browser and runs tests
- Week selection E2E test passes: selects week, verifies state, navigates, verifies persistence
- File upload E2E test passes: selects week, uploads file, verifies API call, verifies database update
- Tests can run in headless mode for CI/CD compatibility
- Test failures generate screenshot in test-results/ directory showing exact failure point
- Developer can run specific test file: `npm run test:e2e -- week-selection.spec.ts`
- Tests verify data flows end-to-end: frontend → API → database → frontend display
- E2E tests can run against localhost OR cloud URL by changing environment variable (BASE_URL)

### Overall Success Criteria

- Developer has full visibility into what works at each layer (database, backend API, frontend UI, end-to-end workflows)
- Developer can confidently add new features knowing tests will catch regressions
- Local development environment mirrors cloud deployment architecture (same PostgreSQL version, same connection patterns, same environment variables)
- All verification can be done by developer directly without abstractions (SQL queries, pytest output, browser clicks, test reports)
- Developer can start entire stack with minimal commands: `docker-compose up -d`, `alembic upgrade head`, `uvicorn backend.main:app --reload`, `npm run dev`
- Documentation exists for: Docker setup, database connection, running tests, starting dev servers

## Out of Scope

**Not Included in This Spec:**
- New feature development (Smart Score V2, lineup optimizer improvements, player analysis)
- UI redesign or component refactoring beyond integration (existing components used as-is)
- Performance optimization (focus on making it work first, optimize later)
- Advanced testing (load tests, security tests, performance benchmarks, mutation testing)
- CI/CD pipeline setup (GitHub Actions, automated deployments - that's Phase 3 per roadmap)
- Cloud deployment (Railway, Render setup - that's Phase 3 per roadmap)
- Authentication/authorization (login, user management - that's Phase 3 per roadmap)
- Monitoring and logging infrastructure (Sentry, log aggregation - that's Phase 3)
- Database backups and disaster recovery (automated backups - future enhancement)
- API documentation generation (Swagger UI customization - nice-to-have)
- Frontend unit tests with Vitest (component testing - future enhancement)
- Advanced E2E test scenarios beyond core workflows (edge cases, error paths - future enhancement)
- Multi-user support (currently single developer local-first)
- Data validation beyond existing validation (new validation rules)
- Storybook for component documentation (nice-to-have, not critical)

**Future Enhancements (Mentioned but Deferred):**
- GitHub Actions CI/CD pipeline for automated testing on push
- Automated database backups before destructive operations
- Performance monitoring and logging (response times, error rates)
- Advanced E2E test coverage (all edge cases, error scenarios, accessibility)
- Frontend unit tests for all components with high coverage (>80%)
- Visual regression testing (Percy, Chromatic)
- API load testing (simulate high request volume)
- Security testing (vulnerability scanning, penetration testing)

## Implementation Considerations

### Database Connection String Formats

**Local Development:**
```
DATABASE_URL=postgresql://cortex:cortex@localhost:5432/cortex
```

**Cloud Deployment (Railway):**
```
DATABASE_URL=postgresql://postgres:password@hostname.railway.app:5432/railway
```

Both use same format, only hostname and credentials differ.

### Environment Variables

**.env file structure:**
```
# Database
DATABASE_URL=postgresql://cortex:cortex@localhost:5432/cortex

# Backend
SECRET_KEY=your-secret-key-here  # For JWT signing (Phase 3)
DEBUG=True  # Enable debug mode for development

# Frontend (Vite)
VITE_API_URL=http://localhost:8000  # Backend API URL
```

**.env.example file structure:**
```
# Database
DATABASE_URL=postgresql://user:password@host:5432/database

# Backend
SECRET_KEY=generate-a-secure-key
DEBUG=False

# Frontend (Vite)
VITE_API_URL=http://localhost:8000
```

### Docker Compose Service Definition

**PostgreSQL service:**
- Image: postgres:15
- Container name: cortex-postgres
- Environment: POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
- Ports: 5432:5432 (expose for SQL client access)
- Volume: ./data:/var/lib/postgresql/data (persist data)
- Health check: pg_isready command
- Restart policy: unless-stopped

### Alembic Migration Strategy

**Migration execution order:**
1. 001_create_data_import_tables.py (existing)
2. 002_extend_weeks_system.py (existing)
3. 003_seed_nfl_schedule.py (existing)

**Running migrations:**
```bash
# Upgrade to latest
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current version
alembic current

# Show migration history
alembic history
```

### File Upload Testing

**Backend file processing flow:**
1. Frontend sends multipart/form-data POST request with file
2. FastAPI endpoint receives file via UploadFile parameter
3. File read into BytesIO buffer
4. pandas reads XLSX from buffer: `pd.read_excel(BytesIO(await file.read()))`
5. DataImporter service processes DataFrame
6. Data inserted into player_pools table
7. Import history record created
8. Response returns success with player count

**E2E test verification:**
1. Upload test XLSX file (153 players for LineStar, 174 for DraftKings, 2690 for Stats)
2. Wait for API response (status 200)
3. Query database: `SELECT COUNT(*) FROM player_pools WHERE week_id = X AND source = 'LineStar'`
4. Assert count matches expected (153 for LineStar)
5. Verify import_history record exists
6. Verify UI updates to show import count

### Material-UI Theme Structure

**theme.ts structure:**
```typescript
import { createTheme } from '@mui/material/styles';

export const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    background: {
      default: '#0f0f1a',
      paper: '#1a1a2e',
    },
    primary: {
      main: '#00d4ff',
    },
    secondary: {
      main: '#7c3aed',
    },
    text: {
      primary: '#e5e7eb',
      secondary: '#9ca3af',
    },
  },
  typography: {
    fontFamily: 'Roboto, Arial, sans-serif',
    // NO EMOJIS in typography
  },
  components: {
    // Component overrides for consistent styling
  },
});
```

### API Proxy Configuration

**vite.config.ts proxy setup:**
```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

This allows frontend to call `/api/weeks` which proxies to `http://localhost:8000/api/weeks`.

### Test Execution Commands

**Backend tests:**
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/integration/test_week_api_endpoints.py -v

# Run specific test function
pytest tests/integration/test_week_api_endpoints.py::test_create_week -v

# Run with coverage report
pytest --cov=backend --cov-report=html

# Run tests matching keyword
pytest -k "week" -v
```

**E2E tests:**
```bash
# Run all E2E tests
npm run test:e2e

# Run in headed mode (see browser)
npm run test:e2e -- --headed

# Run specific test file
npm run test:e2e -- week-selection.spec.ts

# Debug mode with Playwright Inspector
npm run test:e2e -- --debug

# Generate test report
npm run test:e2e -- --reporter=html
```

### Verification Checklist Format

**Phase 1 Checklist (Backend):**
- [ ] Docker Compose starts PostgreSQL without errors
- [ ] Connect to database with SQL client (pgAdmin/DBeaver)
- [ ] Query `SELECT * FROM weeks;` returns rows (or empty table)
- [ ] All 7 tables exist (verify with `\dt` in psql or table list in GUI)
- [ ] Run `pytest -v` and all tests pass
- [ ] Run `alembic current` shows latest migration version
- [ ] Upload test file via API and verify data in database

**Phase 2 Checklist (Frontend):**
- [ ] `npm install` completes without errors
- [ ] `npm run dev` starts Vite at http://localhost:5173
- [ ] Open browser, see dark mode UI (no white flashes)
- [ ] Week Selector dropdown shows weeks 1-18
- [ ] Select different week, verify Zustand state updates
- [ ] Navigate to /players route, see placeholder page
- [ ] Test mobile viewport (390x844), UI responsive
- [ ] NO EMOJIS visible anywhere
- [ ] Theme colors match spec (inspect with DevTools)

**Phase 3 Checklist (E2E):**
- [ ] `npm run test:e2e` launches Playwright
- [ ] Week selection test passes
- [ ] File upload test passes
- [ ] Tests generate screenshots on failure
- [ ] Headless mode works (CI/CD compatible)
- [ ] Can run against different BASE_URL (local or cloud)

### PostgreSQL Connection from SQL Client

**pgAdmin connection setup:**
1. Open pgAdmin
2. Right-click Servers → Create → Server
3. General tab: Name = "Cortex Local"
4. Connection tab:
   - Host: localhost
   - Port: 5432
   - Username: cortex (or from .env POSTGRES_USER)
   - Password: cortex (or from .env POSTGRES_PASSWORD)
   - Database: cortex (or from .env POSTGRES_DB)
5. Save
6. Expand server, see "cortex" database, expand Schemas → public → Tables
7. Right-click table → View/Edit Data → All Rows to see data

**DBeaver connection setup:**
1. Database → New Database Connection
2. Select PostgreSQL
3. Host: localhost, Port: 5432
4. Database: cortex
5. Username: cortex, Password: cortex
6. Test Connection
7. Finish
8. Expand connection, see tables in public schema
9. Right-click table → View Data to see rows

**Direct psql connection:**
```bash
psql postgresql://cortex:cortex@localhost:5432/cortex

# Inside psql:
\dt                    # List tables
\d weeks               # Describe weeks table
SELECT * FROM weeks;   # Query data
\q                     # Quit
```

### Running the Complete Stack

**Step-by-step startup:**
```bash
# Terminal 1: Start PostgreSQL
docker-compose up -d
docker-compose logs -f postgres  # Watch logs

# Terminal 2: Run migrations and start backend
alembic upgrade head
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 3: Start frontend
cd frontend
npm run dev

# Open browser to http://localhost:5173
# Backend API docs at http://localhost:8000/docs
```

**Shutdown:**
```bash
# Ctrl+C in terminal 2 and 3 to stop backend and frontend
# Stop PostgreSQL container
docker-compose down

# Or keep PostgreSQL running and just stop backend/frontend
```

### Local-vs-Cloud Parity Validation

**Verify parity:**
1. Check PostgreSQL version matches cloud:
   ```sql
   SELECT version();
   -- Should show: PostgreSQL 15.x
   ```
2. Check connection string format matches cloud pattern (postgresql://...)
3. Check Alembic migrations run successfully (same as cloud deployment)
4. Check environment variables use same names (DATABASE_URL)
5. Check API endpoints return same response structure
6. Check frontend builds with `npm run build` (same output as cloud deployment)

**Testing cloud deployment readiness:**
- Run E2E tests against cloud URL by setting `BASE_URL` environment variable
- Verify API endpoints accessible via HTTPS
- Verify database migrations applied on cloud PostgreSQL
- Verify frontend static files served correctly (Nginx or similar)
