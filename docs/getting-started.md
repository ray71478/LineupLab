# Getting Started with Cortex DFS Lineup Optimizer

This guide walks through the complete setup process for local development of Cortex.

## Prerequisites

Before starting, ensure you have:

1. **Docker Desktop** (macOS/Windows)
   - Download: https://www.docker.com/products/docker-desktop
   - Status: `docker --version` should show Docker 20.10+
   - Running: Docker Desktop app must be open

2. **Python 3.11+**
   - Check: `python3 --version`
   - Required for backend and database migrations
   - macOS: `brew install python@3.11`

3. **Node.js 18+**
   - Check: `node --version`
   - Required for frontend development
   - Download: https://nodejs.org/
   - macOS: `brew install node@18`

4. **PostgreSQL Client** (optional but recommended)
   - pgAdmin: https://www.pgadmin.org/download/
   - DBeaver: https://dbeaver.io/download/
   - Or use `psql` command line tool

5. **Git**
   - Check: `git --version`
   - Clone the repository

## Step 1: Clone Repository

```bash
# Clone the repository
git clone https://github.com/your-org/cortex.git
cd cortex

# Verify structure
ls -la
# Should show: backend/, frontend/, tests/, alembic/, docker-compose.yml, etc.
```

## Step 2: Backend Setup

### 2.1 Create Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Verify activation
which python  # Should show path in venv/
```

### 2.2 Install Python Dependencies

```bash
# Install all backend dependencies
pip install -r backend/requirements.txt

# Verify installation
python -c "import fastapi; print(fastapi.__version__)"
```

### 2.3 Setup Environment Variables

```bash
# Copy example file
cp .env.example .env

# Edit .env with your settings
nano .env  # or use your editor

# Verify key variables
echo "DATABASE_URL: $DATABASE_URL"
echo "DEBUG: $DEBUG"
```

Example `.env` file:
```bash
# Database
DATABASE_URL=postgresql://cortex:cortex@localhost:5432/cortex

# Backend
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True

# Frontend
VITE_API_URL=http://localhost:8000
```

## Step 3: Database Setup

### 3.1 Start PostgreSQL Container

```bash
# Start PostgreSQL in Docker
docker-compose up -d

# Verify it's running
docker-compose ps
# Should show: cortex-postgres  RUNNING

# Wait for healthy status (30 seconds)
docker-compose logs postgres
# Should see: "database system is ready to accept connections"
```

### 3.2 Run Database Migrations

```bash
# Activate Python venv if not already
source venv/bin/activate

# Run migrations
alembic upgrade head

# Verify current migration
alembic current
# Should show latest migration version
```

### 3.3 Verify Database Setup

#### Option A: Using SQL Command Line

```bash
# Connect to database
psql postgresql://cortex:cortex@localhost:5432/cortex

# Check tables exist
\dt
# Should list: weeks, player_pools, historical_stats, etc.

# Check weeks table
SELECT COUNT(*) FROM weeks;
# Should show number of seeded weeks

# Check foreign keys
SELECT * FROM weeks LIMIT 1;
# Should show week data structure

# Exit
\q
```

#### Option B: Using pgAdmin (GUI)

```bash
# pgAdmin setup (if installed locally)
1. Open pgAdmin (http://localhost:5050 if running in Docker)
2. Right-click Servers → Create → Server
3. Name: "Cortex Local"
4. Connection Tab:
   - Host: localhost
   - Port: 5432
   - Username: cortex
   - Password: cortex
   - Database: cortex
5. Save and expand server
6. Databases → cortex → Schemas → public → Tables
   Should see: weeks, player_pools, historical_stats, etc.
```

#### Option C: Using DBeaver (GUI)

```bash
# DBeaver setup (if installed)
1. Database → New Database Connection
2. Select PostgreSQL
3. Settings:
   - Server Host: localhost
   - Port: 5432
   - Database: cortex
   - Username: cortex
   - Password: cortex
4. Test Connection
5. Finish
6. Expand database connection
   Should see public schema with tables
```

## Step 4: Start Backend Server

### 4.1 Run Backend

```bash
# Activate Python venv
source venv/bin/activate

# Start FastAPI server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Verify startup
# Should see: "Uvicorn running on http://0.0.0.0:8000"
```

### 4.2 Verify Backend Health

```bash
# In new terminal, test API
curl http://localhost:8000/api/weeks
# Should return JSON array of weeks

# Check Swagger UI
open http://localhost:8000/docs
# Should show all API endpoints documented
```

## Step 5: Frontend Setup

### 5.1 Install Node Dependencies

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Verify installation (should complete without errors)
npm list react
# Should show react version
```

### 5.2 Start Frontend Dev Server

```bash
# In frontend directory
npm run dev

# Should see:
# VITE v5.0.8  ready in 234 ms
# Local:    http://localhost:5173/
```

### 5.3 Verify Frontend

```bash
# In browser, open
open http://localhost:5173

# Should see:
# - Dark mode UI
# - "Cortex" logo in header
# - WeekSelector dropdown
# - Main content area
# NO white flashes (dark theme applied correctly)
# NO EMOJIS visible anywhere
```

## Step 6: Verify Everything Works

### 6.1 Test API Integration

```bash
# Get weeks from backend
curl http://localhost:8000/api/weeks?year=2025

# Expected response:
[
  {
    "id": 1,
    "season": 2025,
    "week_number": 1,
    "status": "upcoming",
    ...
  },
  ...
]
```

### 6.2 Test Database Persistence

```bash
# In browser, go to http://localhost:5173
# Click WeekSelector dropdown
# Select Week 9
# Note: No data imported yet, so just verify UI works

# In psql, verify week exists
psql postgresql://cortex:cortex@localhost:5432/cortex
SELECT * FROM weeks WHERE week_number = 9 LIMIT 1;
# Should show week data
```

### 6.3 Test UI Navigation

```bash
# In browser at http://localhost:5173

# 1. Verify redirect to dashboard
open http://localhost:5173/
# Should go to /dashboard

# 2. Navigate to /players
# Should show "Player Pool" heading

# 3. Navigate to /smart-score
# Should show "Smart Score" heading

# 4. Navigate to /lineups
# Should show "Lineup Generator" heading

# 5. Navigate to /invalid
# Should show "404" or "Not Found"
```

### 6.4 Run Backend Tests

```bash
# In project root, activate venv
source venv/bin/activate

# Run all tests
pytest -v

# Expected:
# - 90%+ tests pass
# - No import errors
# - Clear pass/fail for each test
```

## Step 7: Verify Mobile Responsiveness

### 7.1 Chrome DevTools Mobile Emulation

```bash
# In browser at http://localhost:5173

# 1. Open DevTools (F12 or Cmd+Option+I)
# 2. Click mobile device icon (Cmd+Shift+M)
# 3. Select "iPhone SE" or "iPhone 12"
# 4. Verify:
#    - WeekSelector visible and clickable
#    - No horizontal scrolling
#    - Text readable
#    - Touch targets properly sized
```

### 7.2 Tablet View

```bash
# In DevTools device emulation
# Select "iPad" or custom 1024x768
# Verify same checks as mobile
```

## Step 8: Verify Theme Colors

### 8.1 Check Dark Mode

```bash
# In browser at http://localhost:5173
# Open DevTools → Elements

# Check body background color:
# Should be approximately #121212 or similar dark color

# Check text color:
# Should be light gray (#e5e7eb or similar)

# Verify NO white flashes on navigation:
# Click between pages - should stay dark throughout
```

### 8.2 Verify Color Palette

```bash
# In DevTools → Console
# Paste this to see colors:
document.querySelector('body').style.backgroundColor
# Should be dark (#121212)

// Check primary color
document.querySelector('[class*="MuiButton-primary"]')?.style.color
# Should be cyan-like (#00d4ff)
```

## Step 9: Run E2E Tests

### 9.1 Setup E2E Testing

```bash
# In frontend directory
cd frontend

# Ensure Playwright is installed
npx playwright --version

# Install browsers if needed
npx playwright install chromium
```

### 9.2 Run E2E Tests

```bash
# In frontend directory
npm run test:e2e

# Expected output:
# ✓ week-selection.spec.ts (1 test)
# ✓ navigation.spec.ts (1 test)
# ✓ mobile-responsive.spec.ts (3 tests)
# Total: 5 tests passed
```

### 9.3 View Test Report

```bash
npm run test:e2e:report

# Should open HTML report showing:
# - Test results summary
# - Pass/fail status for each test
# - Screenshots on failure
```

## Local-vs-Cloud Parity Validation

### Database Version

```bash
# Check local PostgreSQL version
psql postgresql://cortex:cortex@localhost:5432/cortex
SELECT version();
# Should show: PostgreSQL 15.x

# Expected: Matches cloud deployment version (Railway/Render)
```

### Connection String Format

```bash
# Local format (should match cloud)
postgresql://cortex:cortex@localhost:5432/cortex

# Cloud format (same pattern)
postgresql://user:password@hostname.railway.app:5432/railway
```

### Environment Variables

```bash
# Local .env format matches cloud env vars:
DATABASE_URL=...     # Cloud also uses DATABASE_URL
VITE_API_URL=...     # Frontend also uses VITE_API_URL
SECRET_KEY=...       # Cloud also uses SECRET_KEY
```

### Frontend Build

```bash
# Verify frontend builds (same as cloud deployment)
cd frontend
npm run build

# Should output:
# dist/index.html (static file)
# dist/assets/*.js (JavaScript bundles)
# dist/assets/*.css (Styles)
```

## Troubleshooting Quick Reference

### Backend won't start
```bash
# Error: "Address already in use"
# Solution: Port 8000 is in use
lsof -i :8000  # Find process using port
kill -9 <PID>  # Kill it
# Or use different port:
uvicorn backend.main:app --port 8001
```

### Database connection fails
```bash
# Error: "could not translate host name to address"
# Solution: PostgreSQL not running
docker-compose up -d postgres
docker-compose logs postgres  # Check for errors
```

### Frontend won't compile
```bash
# Error: "Module not found"
# Solution: Dependencies not installed
cd frontend
npm install
npm run type-check  # Check for TS errors
```

### Tests fail with timeouts
```bash
# Error: "Timeout 30000ms exceeded"
# Solution: Frontend/backend not responding
# Make sure both are running:
curl http://localhost:8000/api/weeks  # Backend
open http://localhost:5173            # Frontend
```

## Next Steps

Now that you have everything running:

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Try the UI**: Click around http://localhost:5173
3. **Read the code**: Start with `frontend/src/App.tsx` and `backend/main.py`
4. **Run tests**: Execute `pytest -v` and `npm run test:e2e`
5. **Make changes**: Edit components and see HMR (Hot Module Reload) in action

## Common Development Tasks

### View Database Tables
```bash
psql postgresql://cortex:cortex@localhost:5432/cortex
SELECT * FROM weeks;
SELECT COUNT(*) FROM player_pools;
```

### Stop Services
```bash
# Stop frontend (Ctrl+C in terminal)
# Stop backend (Ctrl+C in terminal)
# Stop database
docker-compose down
```

### Reset Database
```bash
# Stop container with volume deletion
docker-compose down -v

# Start fresh
docker-compose up -d
alembic upgrade head
```

### View Backend Logs
```bash
# In backend terminal (should be running with --reload)
# Logs show each request
GET /api/weeks HTTP/1.1" 200
```

### View Frontend Build Errors
```bash
# Check TypeScript errors
npm run type-check

# Check ESLint issues
npm run lint
```

## Further Documentation

- **API Documentation**: http://localhost:8000/docs
- **Backend Setup**: See `/docs/database-setup.md`
- **E2E Testing**: See `/docs/e2e-testing.md`
- **Running Tests**: See `/docs/running-tests.md`
- **Component Guide**: See `/frontend/src/components/README.md`

## Support

For issues:
1. Check troubleshooting section above
2. Check relevant documentation file
3. Review error messages carefully
4. Ensure all prerequisites are installed
5. Try stopping and restarting services
6. Check logs in each service terminal

Welcome to Cortex development!
