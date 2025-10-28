## Tech stack

This document defines Cortex's technical stack. All development must follow these technology choices for consistency and maintainability.

### Framework & Runtime
- **Backend Framework:** FastAPI (Python 3.11+)
- **Frontend Framework:** React 18 + Vite
- **Language/Runtime:** Python 3.11+ (via pyenv), Node.js 20+ (via nvm)
- **Package Manager:** pip + requirements.txt (backend), npm (frontend)

### Frontend
- **JavaScript Framework:** React 18 with TypeScript
- **Build Tool:** Vite (fast HMR, optimized builds)
- **CSS Framework:** Material-UI (MUI) v5 - Material Design 3
- **UI Components:** Material-UI (MUI) component library
- **State Management:** Zustand (lightweight, simple)
- **Data Fetching:** TanStack Query (React Query) v5
- **Tables:** TanStack Table v8 (sortable, filterable, virtualized)
- **Forms:** React Hook Form + Zod validation
- **Routing:** React Router v6
- **Charts (Phase 2):** Recharts

### Backend
- **Framework:** FastAPI (async Python web framework)
- **ORM:** SQLAlchemy 2.0
- **Migrations:** Alembic
- **Data Processing:** pandas + openpyxl (XLSX parsing)
- **Optimization:** PuLP (linear programming for lineup generation)
- **Fuzzy Matching:** rapidfuzz (player name normalization)
- **API Client (Phase 2):** httpx (async HTTP for Vegas/injury APIs)

### Database & Storage
- **Database:** PostgreSQL 15
- **Local Setup:** Homebrew or Docker
- **Cloud (Phase 3):** Railway or Render hosted PostgreSQL
- **Caching (Phase 3):** Redis (session management, API responses)

### Testing & Quality
- **Backend Tests:** pytest + pytest-cov
- **Frontend Tests:** Vitest (unit tests)
- **E2E Tests (Phase 3):** Playwright
- **Backend Linting:** Ruff (fast Python linter)
- **Backend Type Checking:** mypy
- **Frontend Linting:** ESLint + Prettier

### Deployment & Infrastructure
- **Local Development:** Docker Compose (PostgreSQL)
- **Cloud Hosting (Phase 3):** Railway or Render
- **Containerization:** Docker (frontend + backend containers)
- **CI/CD (Phase 3):** GitHub Actions

### Third-Party Services
- **Authentication (Phase 3):** Auth0 or Supabase
- **Vegas Lines API (Phase 2):** TBD (third-party sports data provider)
- **Injury Reports API (Phase 2):** ESPN, FantasyData, or Sleeper
- **Monitoring (Phase 3):** Sentry (error tracking, performance)
- **Uptime Monitoring (Phase 3):** UptimeRobot or Pingdom

### Design System
- **Typography:** Google Fonts (Inter or Roboto)
- **Icons:** Material Icons (no emojis)
- **Color Palette (Dark Mode):**
  - Background: `#0f0f1a` (deep navy/black)
  - Surface: `#1a1a2e` (panels)
  - Primary: `#00d4ff` (cyan - data emphasis)
  - Accent: `#7c3aed` (purple - AI features)
  - Text: `#e5e7eb` (light gray)

### Performance Requirements
- **Lineup Generation:** <10 seconds for 10 lineups
- **Smart Score Recalculation:** <1 second for real-time updates
- **Data Import:** Zero parsing errors, complete feedback
- **Mobile Performance:** Responsive UI on iPhone/iPad (390x844 to 1024x768)
