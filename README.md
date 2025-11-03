# LineupLab - DFS Lineup Optimizer

**Your DFS Intelligence Layer**

LineupLab is an intelligent DFS lineup optimizer built for serious GPP tournament players who demand complete control over their roster construction strategy. Unlike black-box commercial tools, LineupLab empowers you to define custom scoring algorithms, weigh multiple projection sources, incorporate historical trend analysis, and generate optimized DraftKings lineups with full transparency.

---

## Quick Start

### Prerequisites

- **Python 3.11+** (backend)
- **Node.js 18+** (frontend)
- **PostgreSQL 15** (database)
- **Docker Desktop** (recommended for local database)

### Backend Setup

1. **Create a virtual environment:**
   ```bash
   # Using venv
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # OR using conda
   conda create -n lineuplab python=3.11
   conda activate lineuplab
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   # Copy the example environment file
   cp .env.example .env

   # Edit .env with your configuration
   # For local development, the defaults should work fine
   ```

4. **Start the database (using Docker Compose):**
   ```bash
   docker-compose up -d
   ```

5. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

6. **Start the backend server:**
   ```bash
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

   The API will be available at:
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Frontend Setup

1. **Install Node.js dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm run dev
   ```

   The frontend will be available at: http://localhost:5173

### Running Tests

Run all backend tests:
```bash
pytest -v
```

Run specific test file:
```bash
pytest tests/integration/test_week_api_endpoints.py -v
```

Run with coverage report:
```bash
pytest --cov=backend --cov-report=html
```

---

## Environment Variables

Key environment variables (see `.env.example` for full list):

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://lineuplab:lineuplab@localhost:5432/lineuplab` |
| `SECRET_KEY` | Secret key for JWT tokens (Phase 3) | Generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `DEBUG` | Enable debug mode | `False` |
| `VITE_API_URL` | Backend API URL for frontend | `http://localhost:8000` |

---

## Project Structure

```
/LineupLab/
├── README.md (you are here)
├── .env.example                      # Environment configuration template
├── backend/
│   ├── requirements.txt              # Python dependencies
│   ├── main.py                       # FastAPI application entry point
│   ├── routers/                      # API route handlers
│   ├── services/                     # Business logic services
│   ├── models/                       # Database models
│   └── schemas/                      # Pydantic schemas
├── frontend/
│   ├── package.json                  # Node.js dependencies
│   ├── vite.config.ts                # Vite configuration
│   └── src/
│       ├── components/               # React components
│       ├── hooks/                    # Custom React hooks
│       ├── store/                    # Zustand state management
│       └── pages/                    # Route pages
├── tests/
│   ├── conftest.py                   # Pytest fixtures
│   ├── integration/                  # Integration tests
│   └── features/                     # Feature tests
├── alembic/                          # Database migrations
├── docs/                             # Documentation
└── discovery/                        # Product documentation
    ├── ProjectBrief.md               # Comprehensive project overview
    ├── PRFAQ.md                      # Press release FAQ
    └── components/                   # Component specifications
```

---

## Documentation

### Start Here:

1. **[ProjectBrief.md](./discovery/ProjectBrief.md)** - Comprehensive project overview including:
   - Executive Summary
   - Problem Statement
   - Proposed Solution
   - Target Users
   - MVP Scope (Phase 1, 2, 3)
   - Technical Stack
   - Risks & Open Questions

### Additional Documentation:

2. **[PRFAQ.md](./discovery/PRFAQ.md)** - Press Release FAQ (written as if LineupLab already exists and succeeded):
   - Headline & press release
   - Customer problem/solution narrative
   - Key features & benefits
   - FAQ addressing stakeholder questions

3. **[PRD.md](./discovery/PRD.md)** - Product Requirements Document (detailed specifications):
   - User stories
   - Functional requirements
   - Non-functional requirements (performance, security, scalability)
   - User experience flows
   - API requirements
   - Data models
   - Acceptance criteria

4. **[TechnicalArchitecture.md](./discovery/TechnicalArchitecture.md)** - System design & technical documentation:
   - Architecture diagrams
   - Database schemas (PostgreSQL models)
   - API endpoints (FastAPI routes)
   - Smart Score algorithm (detailed formula)
   - Lineup optimizer approach (linear programming)
   - Technology stack details

---

## What is LineupLab?

**The Problem:**
Existing DFS tools are either too simplistic (manual spreadsheets) or too opaque (proprietary algorithms you can't control). You need a tool that gives you full control over the "brain" of the optimizer.

**The Solution:**
LineupLab combines multiple data sources (LineStar, DraftKings, historical NFL stats) with a configurable "Smart Score" algorithm to generate optimized DraftKings lineups. You define the formula, adjust weights in real-time, and understand exactly why each lineup was constructed.

**Key Features:**
- Multi-source data import (LineStar, DraftKings, NFL historical stats)
- Configurable Smart Score (8-factor formula: projection, ownership, value, trends, regression, Vegas, matchup)
- Lineup optimizer (10 lineups, DraftKings constraints, exposure controls, stacking rules)
- Historical replay (select past weeks, adjust weights, re-optimize with hindsight)
- Dark mode UI (Material Design 3, responsive desktop + mobile)
- Local-first development, cloud-ready architecture

---

## Tech Stack

**Front-End:**
- React 18 + Vite
- Material Design 3 (dark mode)
- TanStack Table (player grids)
- TanStack Query (API calls)
- Zustand (state management)
- TypeScript

**Back-End:**
- FastAPI (Python 3.11+)
- SQLAlchemy 2.0 (PostgreSQL ORM)
- Alembic (database migrations)
- pandas + openpyxl (XLSX processing)
- PuLP (linear programming for lineup optimization)
- pytest (testing framework)

**Database:**
- PostgreSQL 15 (local development via Docker)

**Deployment (Phase 3):**
- Railway or Render (cloud hosting)
- Docker + Docker Compose

---

## Project Status

**Current Phase:** Phase 1 - Testing & Verification Infrastructure
**Status:** Backend verification in progress
**Next Milestone:** Complete backend testing infrastructure

**Timeline:**
- **Phase 1 (Current):** Testing & Verification Infrastructure
- **Phase 2:** Frontend Integration & Verification
- **Phase 3:** End-to-End Testing & Cloud Deployment

---

## Vision

### Phase 1 (MVP - Local):
- Complete weekly workflow: import → Smart Score tuning → lineup generation → export
- Historical replay (adjust weights for past weeks)
- Dark mode UI (desktop + mobile)

### Phase 2 (Historical Analysis):
- API integrations (Vegas lines, injury reports)
- Contest results import (actual vs. projected comparison)
- Variance analysis & performance analytics

### Phase 3 (Cloud + Multi-User):
- Cloud deployment (Railway/Render)
- User authentication
- Collaborator access
- Shared player pools

---

## Design Philosophy

**Visual Identity:**
- **Dark mode primary** (deep navy/black backgrounds)
- **Material Design 3** principles
- **Google Fonts** (Inter or Roboto)
- **Material Icons** (clean, no emojis)
- **Color Palette:**
  - Background: `#0f0f1a` (deep navy)
  - Primary: `#00d4ff` (cyan - data emphasis)
  - Accent: `#7c3aed` (purple - AI features)
  - Text: `#e5e7eb` (light gray)

**UX Principles:**
- Minimal clicks (smart defaults, keyboard shortcuts, batch actions)
- AI-assisted (suggestions, auto-detect, predictive inputs)
- Data-dense but readable (good typography, not overwhelming)
- Mobile-first responsive

---

## Troubleshooting

### Common Issues

**Database connection errors:**
- Ensure PostgreSQL is running: `docker-compose ps`
- Check DATABASE_URL in .env file
- Verify migrations are up to date: `alembic current`

**Import errors in Python:**
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r backend/requirements.txt`

**Frontend can't connect to backend:**
- Check VITE_API_URL in .env
- Ensure backend server is running on port 8000
- Verify CORS settings in backend/main.py

---

## Contact

**Product Owner:** Ray Bargas
**Business Analyst:** Mary (agent-os/analyst)

**Questions?** Review [ProjectBrief.md](./discovery/ProjectBrief.md) first, then reach out.

---

**This is not a rebuild. This is the first real launch.**

Let's build LineupLab.
