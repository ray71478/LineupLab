# Cortex Tech Stack

**Last Updated:** October 27, 2025  
**Status:** Active Development

---

## Overview

This document outlines the complete technical stack for Cortex, a DFS lineup optimizer for DraftKings NFL GPP tournaments. The stack is designed to be local-first for MVP, with cloud-ready architecture for future deployment.

---

## Architecture Principles

### 1. **Local-First, Cloud-Ready**
- Start with local development (PostgreSQL, no deployment friction)
- Design stateless APIs for easy cloud migration
- Use environment-based configuration (local vs. cloud)

### 2. **API-First Design**
- Frontend and backend communicate only via REST API
- No tight coupling between layers
- Easy to swap frontend or backend independently

### 3. **Simplicity Over Complexity**
- Use proven, stable technologies
- Avoid over-engineering (no microservices, no Kubernetes)
- Minimize dependencies

### 4. **Performance First**
- Generate 10 lineups in <10 seconds
- Real-time Smart Score recalculation (<1 second)
- Mobile-friendly (responsive, fast page loads)

---

## Frontend Stack

### Core Framework
- **React 18** - Modern, widely supported, fast
- **Vite** - Lightning-fast build tool, HMR (Hot Module Replacement)
- **TypeScript** - Type safety, better developer experience

### UI Components & Styling
- **Material-UI (MUI) v5** - Material Design 3 components
  - Pre-built dark mode support
  - Responsive grid system
  - Extensive component library (tables, sliders, buttons, dialogs)
- **Tailwind CSS** (optional, if MUI is too heavy) - Utility-first CSS
- **Google Fonts** - Inter or Roboto for typography
- **Material Icons** - Clean, consistent iconography

### State Management
- **Zustand** - Lightweight state management (simpler than Redux)
  - Global state for: current week, Smart Score weights, player pool
  - Persistent state (localStorage integration)
- **React Context** (fallback) - For simpler state needs

### Data Fetching & Caching
- **TanStack Query (React Query) v5** - Server state management
  - Automatic caching, refetching, background updates
  - Optimistic updates for better UX
  - Error handling and retry logic

### Tables & Data Display
- **TanStack Table v8** - Headless table library
  - Sortable, filterable, paginated tables
  - Virtualization for large player pools (200+ players)
  - Mobile-responsive
- **AG Grid** (alternative, if TanStack Table is insufficient) - Enterprise-grade data grid

### Forms & Validation
- **React Hook Form** - Performant form handling
- **Zod** - TypeScript-first schema validation
  - Validate Smart Score weights, exposure limits, lineup settings

### Charts & Visualization (Phase 2)
- **Recharts** - React-friendly charting library
  - Line charts (player trends over time)
  - Scatter plots (projected vs. actual FPTS)
  - Bar charts (ownership distribution)
- **Chart.js** (alternative) - Lightweight, flexible

### Routing
- **React Router v6** - Client-side routing
  - `/dashboard` - Main dashboard
  - `/players` - Player pool view
  - `/smart-score` - Smart Score configuration
  - `/lineups` - Lineup generator & results
  - `/history` - Historical week replay

### Build & Development Tools
- **Vite** - Dev server, bundler, HMR
- **ESLint** - JavaScript/TypeScript linting
- **Prettier** - Code formatting
- **Vitest** - Unit testing (Vite-native)
- **Playwright** (Phase 3) - End-to-end testing

---

## Backend Stack

### Core Framework
- **FastAPI** - Modern Python web framework
  - Async support (fast API responses)
  - Automatic OpenAPI docs (Swagger UI)
  - Type hints with Pydantic (validation)
  - Easy to test and deploy

### Language & Runtime
- **Python 3.11+** - Latest stable Python
- **pyenv** - Python version management (macOS)
- **pip** + **requirements.txt** - Dependency management

### Database ORM & Migrations
- **SQLAlchemy 2.0** - Python ORM
  - Define models (weeks, player_pools, historical_stats, etc.)
  - Query builder (avoid raw SQL)
  - Support for PostgreSQL-specific features
- **Alembic** - Database migrations
  - Version control for schema changes
  - Auto-generate migrations from model changes

### Data Processing
- **pandas** - DataFrame manipulation
  - Parse XLSX files (LineStar, DraftKings, NFL Stats)
  - Data cleaning, normalization, aggregation
- **openpyxl** - Excel file reading (multi-sheet support)
- **numpy** - Numerical operations (Smart Score calculations)

### Optimization & Linear Programming
- **PuLP** - Linear programming library
  - Solve lineup optimization problem
  - Enforce DraftKings constraints (salary cap, positions, exposure)
  - Maximize Smart Score across lineups
- **Gurobi** (optional, if PuLP is too slow) - Commercial optimizer (free academic license)
- **scipy.optimize** (fallback) - Python's built-in optimization

### Fuzzy Matching
- **fuzzywuzzy** or **rapidfuzz** - String similarity matching
  - Handle player name variations ("Christian McCaffrey" vs. "C. McCaffrey")
  - Calculate similarity scores (0-100)
  - Suggest best matches for manual mapping

### API Integrations (Phase 2)
- **httpx** - Async HTTP client
  - Fetch Vegas lines (implied team totals, spreads)
  - Fetch injury reports (ESPN, FantasyData, Sleeper)
  - Handle rate limits, retries, timeouts

### Testing
- **pytest** - Unit and integration testing
  - Test data import, Smart Score calculation, lineup optimizer
  - Mock external APIs (Phase 2)
- **pytest-cov** - Code coverage reporting

### Code Quality
- **Ruff** - Fast Python linter (replaces Flake8, Black, isort)
- **mypy** - Static type checking

---

## Database

### Primary Database
- **PostgreSQL 15** - Relational database
  - Local: Installed via Homebrew or Docker
  - Cloud (Phase 3): Hosted on Railway or Render
  - JSONB support (store flexible data like weight profiles, lineup JSON)

### Schema Overview

#### `weeks` Table
- `id` (PK, auto-increment)
- `season` (e.g., 2024)
- `week_number` (1-18)
- `status` (enum: upcoming, active, completed)
- `created_at`, `updated_at`

#### `player_pools` Table
- `id` (PK, auto-increment)
- `week_id` (FK → weeks.id)
- `player_key` (composite: name_team_position, unique per week)
- `name`, `team`, `position`
- `salary`, `projection`, `ownership`
- `ceiling`, `floor`, `notes`
- `source` (enum: LineStar, DraftKings)
- `uploaded_at`

#### `historical_stats` Table
- `id` (PK, auto-increment)
- `player_key` (composite: name_team_position)
- `week`, `season`, `team`
- `actual_points` (DK FPTS scored)
- `snaps`, `snap_pct`
- `targets`, `target_share`
- `receptions`, `rec_yards`, `rec_tds`
- `rush_attempts`, `rush_yards`, `rush_tds`
- `ownership` (actual ownership from contest results)

#### `vegas_lines` Table (Phase 2)
- `id` (PK, auto-increment)
- `week_id` (FK → weeks.id)
- `team`, `opponent`
- `implied_team_total` (ITT)
- `spread`, `over_under`
- `updated_at`

#### `generated_lineups` Table
- `id` (PK, auto-increment)
- `week_id` (FK → weeks.id)
- `lineup_number` (1-10)
- `players` (JSONB: array of player objects)
- `total_salary`, `projected_score`, `avg_ownership`
- `strategy_mode` (enum: Chalk, Balanced, Contrarian)
- `weight_profile_id` (FK → weight_profiles.id, nullable)
- `created_at`

#### `weight_profiles` Table
- `id` (PK, auto-increment)
- `profile_name` (unique, e.g., "Base", "Contrarian")
- `weights` (JSONB: W1-W8 values)
- `created_at`, `updated_at`

#### `player_aliases` Table
- `id` (PK, auto-increment)
- `alias_name` (e.g., "C. McCaffrey")
- `canonical_player_key` (e.g., "christian_mccaffrey_SF_RB")
- `created_at`

### Backup Strategy
- **Automated Backup:** Before historical stats import (keep 1 previous version)
- **Manual Backup:** Export entire database to SQL dump (pg_dump)
- **Cloud Backups (Phase 3):** Daily automated backups via Railway/Render

---

## Caching (Phase 3)

### Redis
- **Session Management:** Store JWT tokens, user sessions
- **API Response Caching:** Cache Vegas lines, injury reports (TTL: 1 hour)
- **Smart Score Caching:** Cache calculated Smart Scores per week (invalidate on weight change)

---

## Deployment & Infrastructure

### Local Development (MVP)
- **Docker Compose** - Run PostgreSQL locally
- **Vite Dev Server** - Frontend (port 5173)
- **Uvicorn** - FastAPI backend (port 8000)
- **PostgreSQL** - Database (port 5432)

### Cloud Deployment (Phase 3)
- **Platform:** Railway or Render
  - PaaS (no Kubernetes complexity)
  - Built-in PostgreSQL hosting
  - Automatic HTTPS, custom domains
  - CI/CD integration (GitHub Actions)

- **Docker Containers:**
  - `frontend` - React app (Nginx serving static files)
  - `backend` - FastAPI app (Uvicorn ASGI server)
  - `database` - PostgreSQL (managed by Railway/Render)
  - `redis` - Redis (optional, for caching)

- **Environment Variables:**
  - `DATABASE_URL` - PostgreSQL connection string
  - `REDIS_URL` - Redis connection string (Phase 3)
  - `SECRET_KEY` - JWT signing key (Phase 3)
  - `API_KEYS` - Vegas lines, injury reports (Phase 2)

---

## CI/CD Pipeline (Phase 3)

### GitHub Actions
- **On Push to `main`:**
  - Run linters (Ruff, ESLint)
  - Run tests (pytest, Vitest)
  - Build Docker images
  - Deploy to Railway/Render (if tests pass)

- **On Pull Request:**
  - Run linters and tests
  - Block merge if tests fail

---

## Authentication & Authorization (Phase 3)

### Auth Provider
- **Auth0** or **Supabase** - Managed authentication
  - Email/password login
  - OAuth (Google, Apple)
  - JWT token issuance
  - Password reset, email verification

### Authorization
- **Role-Based Access Control (RBAC):**
  - Owner: Full access (create, edit, delete)
  - Editor: Can upload data, generate lineups, export
  - Viewer: Read-only access

---

## API Design

### REST API Endpoints (MVP)

#### Week Management
- `GET /api/weeks` - List all weeks
- `POST /api/weeks` - Create new week
- `GET /api/weeks/{week_id}` - Get week details
- `PATCH /api/weeks/{week_id}` - Update week status

#### Data Import
- `POST /api/import/linestar` - Upload LineStar XLSX
- `POST /api/import/draftkings` - Upload DraftKings XLSX
- `POST /api/import/nfl-stats` - Upload NFL Stats XLSX
- `GET /api/import/status/{week_id}` - Check import status

#### Player Management
- `GET /api/players?week_id={week_id}` - List players for week
- `GET /api/players/{player_key}` - Get player details
- `POST /api/players/map-alias` - Manually map player alias
- `GET /api/players/aliases` - List all aliases

#### Smart Score
- `POST /api/smart-score/calculate` - Calculate Smart Scores for week
- `GET /api/smart-score/weights` - Get current weights
- `PATCH /api/smart-score/weights` - Update weights
- `GET /api/smart-score/profiles` - List saved profiles
- `POST /api/smart-score/profiles` - Save new profile
- `DELETE /api/smart-score/profiles/{profile_id}` - Delete profile

#### Lineup Optimization
- `POST /api/lineups/generate` - Generate lineups
  - Request body: `{ week_id, num_lineups, strategy_mode, exposure_limits, stacking_rules }`
  - Response: Array of 10 lineups
- `GET /api/lineups?week_id={week_id}` - List generated lineups for week
- `GET /api/lineups/{lineup_id}` - Get lineup details

#### Export
- `GET /api/export/draftkings?week_id={week_id}` - Export lineups to DraftKings CSV
- `GET /api/export/database` - Export entire database (SQL dump)

---

## Development Tools

### Version Control
- **Git** - Version control
- **GitHub** - Code hosting, collaboration
- **Branch Strategy:**
  - `main` - Production-ready code
  - `develop` - Integration branch
  - `feature/*` - Feature branches
  - `bugfix/*` - Bug fix branches

### Code Quality
- **Ruff** - Python linting (backend)
- **ESLint** - JavaScript/TypeScript linting (frontend)
- **Prettier** - Code formatting (frontend)
- **mypy** - Python type checking (backend)

### Testing
- **pytest** - Backend unit/integration tests
- **Vitest** - Frontend unit tests
- **Playwright** (Phase 3) - End-to-end tests

### Containerization
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration (local dev)

---

## Monitoring & Logging (Phase 3)

### Application Monitoring
- **Sentry** - Error tracking, performance monitoring
  - Frontend errors (React component crashes)
  - Backend errors (API exceptions)
  - Performance metrics (API response times)

### Logging
- **Python `logging` module** - Backend logs
  - Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
  - Log to stdout (Railway/Render captures logs)
- **Frontend Console** - Browser console logs (development only)

### Uptime Monitoring
- **UptimeRobot** or **Pingdom** - Monitor API uptime
  - Alert if API is down >5 minutes
  - Track uptime % (target: 99.5%)

---

## Security Considerations

### MVP (Local Development)
- No authentication required (single user, local machine)
- Database credentials stored in `.env` file (not committed to Git)

### Phase 3 (Cloud Deployment)
- **HTTPS Only:** Enforce SSL/TLS (Railway/Render provides free certs)
- **JWT Tokens:** Secure session management (short expiration, refresh tokens)
- **Password Hashing:** bcrypt or Argon2 (via Auth0/Supabase)
- **CORS:** Restrict API access to frontend domain only
- **Rate Limiting:** Prevent abuse (e.g., 100 requests/minute per user)
- **SQL Injection Prevention:** Use SQLAlchemy ORM (parameterized queries)
- **XSS Prevention:** Sanitize user inputs (React escapes by default)

---

## Performance Optimization

### Backend
- **Database Indexing:** Index `player_key`, `week_id`, `lineup_id` for fast queries
- **Query Optimization:** Use SQLAlchemy `select()` with joins, avoid N+1 queries
- **Async API Endpoints:** Use FastAPI's async/await for non-blocking I/O
- **Caching (Phase 3):** Redis for Smart Score calculations, API responses

### Frontend
- **Code Splitting:** Lazy load routes (React.lazy, Suspense)
- **Image Optimization:** Compress images, use WebP format
- **Virtualization:** TanStack Table virtual scrolling for large player pools
- **Memoization:** React.memo, useMemo, useCallback for expensive computations

### Optimization Algorithm
- **PuLP Solver:** Use CBC solver (fast, open-source)
- **Gurobi (if needed):** Commercial solver (10x faster than PuLP)
- **Parallel Processing:** Generate lineups in parallel (Python multiprocessing)

---

## Cost Estimates

### MVP (Local Development)
- **Total Cost:** $0/month
  - PostgreSQL: Free (local install)
  - Python/Node.js: Free
  - No cloud hosting

### Phase 2 (APIs)
- **Vegas Lines API:** $20-50/month (depends on provider)
- **Injury Reports API:** $10-30/month (depends on provider)
- **Total Cost:** $30-80/month

### Phase 3 (Cloud Deployment)
- **Railway/Render:** $20-50/month (Hobby plan, includes PostgreSQL)
- **Redis:** $10-20/month (optional, for caching)
- **Auth0/Supabase:** $0-25/month (free tier up to 7,500 users)
- **Sentry:** $0-26/month (free tier up to 5,000 events/month)
- **Total Cost:** $30-120/month (scales with users)

---

## Alternative Technologies Considered

### Frontend Alternatives
- **Vue.js** - Simpler than React, but smaller ecosystem
- **Svelte** - Fastest, but less mature ecosystem
- **Next.js** - React framework with SSR, overkill for local-first app

### Backend Alternatives
- **Django** - Heavier than FastAPI, slower API responses
- **Flask** - Lighter than FastAPI, but lacks async support
- **Node.js (Express)** - JavaScript backend, but Python better for data processing

### Database Alternatives
- **SQLite** - Too limited for multi-user (Phase 3)
- **MySQL** - Less feature-rich than PostgreSQL (no JSONB)
- **MongoDB** - NoSQL, but relational data fits better in PostgreSQL

### Optimization Alternatives
- **Google OR-Tools** - More powerful than PuLP, but steeper learning curve
- **CPLEX** - Commercial solver, expensive
- **Manual Greedy Algorithm** - Faster but less optimal

---

## Document Status
✅ **Approved** - Ready for development

