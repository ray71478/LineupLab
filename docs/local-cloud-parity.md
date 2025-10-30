# Local vs Cloud Parity Validation

This document ensures that local development environment matches cloud deployment (Railway/Render) to prevent "works locally but breaks in cloud" issues.

## Executive Summary

The Cortex DFS Lineup Optimizer must work identically in three environments:
- **Local**: Developer's machine with Docker Compose
- **Staging**: Cloud testing environment (Railway/Render)
- **Production**: Live cloud environment

This guide validates that environments are equivalent.

## Environment Checklist

### Local Environment Validation

#### Database Version Check

```bash
# Step 1: Connect to local PostgreSQL
psql postgresql://cortex:cortex@localhost:5432/cortex

# Step 2: Check version
SELECT version();

# Expected Output:
# PostgreSQL 15.4 (or any 15.x version)
# Should match cloud PostgreSQL version
```

**Validation:**
- Local PostgreSQL 15.x matches cloud (Railway/Render uses PostgreSQL 15)
- Version number should be similar (15.0 to 15.9 are all fine)
- If major version differs (e.g., 14.x or 16.x), update docker-compose.yml

#### Connection String Format

```bash
# Local connection string (from .env)
DATABASE_URL=postgresql://cortex:cortex@localhost:5432/cortex

# Cloud connection string format (from Railway/Render)
DATABASE_URL=postgresql://username:password@hostname.railway.app:5432/databasename

# Key parts that match:
# ✓ Protocol: postgresql://
# ✓ Format: user:password@host:port/database
# ✓ Port: 5432 (standard PostgreSQL)
```

**Validation:**
- Format is identical (`postgresql://` prefix)
- Port is consistent (5432)
- Credentials structure matches (user:password@host:port/db)

#### Database Tables and Schema

```bash
# Connect to local database
psql postgresql://cortex:cortex@localhost:5432/cortex

# List tables
\dt

# Expected output:
#              List of relations
#  Schema |           Name           | Type  | Owner
# --------+--------------------------+-------+-------
#  public | historical_stats         | table | cortex
#  public | import_history           | table | cortex
#  public | nfl_schedule             | table | cortex
#  public | player_aliases           | table | cortex
#  public | player_pools             | table | cortex
#  public | player_pool_history      | table | cortex
#  public | unmatched_players        | table | cortex
#  public | week_metadata            | table | cortex
#  public | week_status_overrides    | table | cortex
#  public | weeks                    | table | cortex

# Verify table structure
\d weeks

# Expected columns:
# id                   | integer
# season              | integer
# week_number         | integer
# status              | character varying
# nfl_slate_date      | date
# created_at          | timestamp
# updated_at          | timestamp
```

**Validation:**
- All 10 tables present
- Column names and types match across environments
- Foreign keys intact
- Constraints enforced

#### Alembic Migrations

```bash
# Check current migration version
alembic current

# Expected output:
# e1c2d3e4f5a6 (head)

# Check migration history
alembic history

# Expected: All migrations up to head
# 001_create_data_import_tables.py
# 002_extend_weeks_system.py
# 003_seed_nfl_schedule.py
```

**Validation:**
- All migrations applied (alembic current shows "head")
- Same migrations run on cloud
- No unapplied migrations

### Application Verification

#### Backend API Endpoints

```bash
# Verify backend running
curl -v http://localhost:8000/api/weeks

# Expected response:
# HTTP/1.1 200 OK
# Content-Type: application/json
# [
#   {
#     "id": 1,
#     "season": 2025,
#     "week_number": 1,
#     ...
#   }
# ]

# Test CORS headers (important for cloud)
curl -H "Origin: https://cortex.app" \
     -H "Access-Control-Request-Method: GET" \
     http://localhost:8000/api/weeks

# Should include:
# Access-Control-Allow-Origin: *
```

**Validation:**
- API returns correct response format
- CORS headers allow cross-origin requests
- All endpoints accessible
- Response structure matches cloud API

#### Frontend Build

```bash
# Build frontend (same as cloud deployment)
cd frontend
npm run build

# Check build output
ls -la dist/

# Expected structure:
# dist/
#   index.html          (main entry point)
#   assets/
#     index-*.js        (compiled JavaScript)
#     index-*.css       (compiled styles)
#   assets/vite/        (Vite manifest)

# Verify dark theme in HTML
grep -i "background\|color" dist/index.html
# Should have dark theme colors

# Size check (should be < 500KB)
du -sh dist/
```

**Validation:**
- Build completes without errors
- Static files generated (HTML, JS, CSS)
- Size reasonable and matches cloud deployment
- No emojis in output files

#### TypeScript Compilation

```bash
# Verify TypeScript types are correct
npm run type-check

# Should complete with NO errors
# Output: "... (no errors)"

# If errors, they should match cloud CI/CD results
```

**Validation:**
- No TypeScript errors
- Same type-checking as cloud build
- Frontend ready for production

### Database Functionality Parity

#### Data Import Flow

```bash
# Test complete data import workflow

# 1. Create a week (if not exists)
curl -X POST http://localhost:8000/api/weeks \
  -H "Content-Type: application/json" \
  -d '{"season": 2025, "week_number": 10, "status": "active"}'

# 2. Verify in database
psql postgresql://cortex:cortex@localhost:5432/cortex
SELECT * FROM weeks WHERE week_number = 10;

# 3. Import data (using test file)
# Would need actual file upload test

# 4. Verify import created records
SELECT COUNT(*) FROM player_pools WHERE week_id = <week_id>;
SELECT COUNT(*) FROM import_history WHERE week_id = <week_id>;
```

**Validation:**
- Data import endpoint works
- Data persisted in database
- Import history recorded
- Same functionality as cloud

#### Data Integrity

```bash
# Check constraints are enforced
psql postgresql://cortex:cortex@localhost:5432/cortex

# Try invalid insert (should fail)
INSERT INTO weeks (season, week_number, status)
VALUES (2025, 19, 'invalid_status');

# Expected: ERROR - violates check constraint

# Check foreign keys
SELECT COUNT(*) FROM player_pools
WHERE week_id NOT IN (SELECT id FROM weeks);

# Expected: 0 (no orphaned records)

# Check unique constraints
SELECT season, week_number, COUNT(*)
FROM weeks
GROUP BY season, week_number
HAVING COUNT(*) > 1;

# Expected: 0 rows (no duplicates)
```

**Validation:**
- Constraints enforced locally and in cloud
- Data integrity maintained
- No orphaned records

### Environment Variable Parity

#### Local .env Setup

```bash
# Check local .env has all required variables
cat .env

# Required variables:
# DATABASE_URL=postgresql://cortex:cortex@localhost:5432/cortex
# SECRET_KEY=dev-secret-key (different in prod)
# DEBUG=True (False in cloud)
# VITE_API_URL=http://localhost:8000
```

**Validation:**
- All variables defined
- Format matches cloud requirements
- No hardcoded values that won't work in cloud

#### Cloud Environment Variables

Check that cloud deployment has equivalent:
```bash
# Railway/Render dashboard should have:
DATABASE_URL=postgresql://...  # From service
SECRET_KEY=<production-key>
DEBUG=False
VITE_API_URL=https://cortex-api.app  # Cloud API URL
```

**Validation:**
- Cloud has all required variables
- Values appropriate for environment (DEBUG=False in prod)
- API URLs point to correct endpoints

## Deployment Readiness Checks

### Docker Compatibility

```bash
# Docker image should build consistently
docker build -t cortex-backend ./backend

# Should complete with no errors
# Image should be < 500MB
docker images cortex-backend
# REPOSITORY  TAG  IMAGE_ID  SIZE
# cortex-backend  latest  abc123...  450MB
```

**Validation:**
- Dockerfile builds successfully
- Same base image as cloud (Python 3.11+)
- No hardcoded paths or secrets

### Network Connectivity

```bash
# Simulate cloud network requirements

# 1. Backend → Database (standard cloud setup)
psql postgresql://cortex:cortex@localhost:5432/cortex -c "SELECT 1;"
# Should return: 1

# 2. Frontend → Backend (CORS must work)
curl -H "Origin: http://localhost:5173" \
     http://localhost:8000/api/weeks
# Should return data (CORS working)

# 3. Database → External (if needed for features)
# N/A for current phase
```

**Validation:**
- Services can communicate
- Database accessible from app
- CORS configured for web requests

## Validation Testing Plan

### Phase 1: Database Parity (Done)

```bash
✓ PostgreSQL version verified (15.x)
✓ Connection string format matches
✓ All tables and schemas exist
✓ Alembic migrations applied
✓ Constraints enforced
```

### Phase 2: API Parity (Done)

```bash
✓ Backend API running
✓ Endpoints respond with correct format
✓ CORS headers present
✓ Response structure consistent
```

### Phase 3: Frontend Parity (Done)

```bash
✓ Frontend dev server working
✓ TypeScript compiles without errors
✓ Dark theme applied
✓ Responsive layout works
```

### Phase 4: E2E Testing Parity (Done)

```bash
✓ E2E tests pass locally
✓ Tests can run against staging URL
✓ Tests can run against production URL
✓ Same tests, different BASE_URL
```

## Pre-Deployment Checklist

Before deploying to cloud, verify:

```bash
# 1. All tests pass locally
pytest -v
npm run test:e2e

# 2. Frontend builds
npm run build

# 3. No console errors
npm run type-check

# 4. Database is consistent
psql postgresql://cortex:cortex@localhost:5432/cortex
SELECT COUNT(*) FROM weeks;

# 5. Backend responds
curl http://localhost:8000/api/weeks

# 6. E2E tests pass with prod URL
BASE_URL=https://cortex-staging.app npm run test:e2e
```

## Production Validation

### After Deploying to Production

```bash
# Run same E2E tests against production
BASE_URL=https://cortex.app npm run test:e2e

# Verify API responses
curl https://cortex.app/api/weeks

# Check database consistency
# (connect via cloud SQL client)
SELECT COUNT(*) FROM weeks;
```

## Troubleshooting Parity Issues

### Issue: Tests pass locally, fail in cloud

**Causes:**
- Base URL wrong
- Database connection string incorrect
- Environment variables not set
- CORS not configured

**Solution:**
```bash
# Check BASE_URL environment variable
echo $BASE_URL

# Test with explicit URL
BASE_URL=https://cortex-staging.app npm run test:e2e:headed

# Verify API accessible
curl https://cortex-staging.app/api/weeks
```

### Issue: Database schema mismatch

**Causes:**
- Migrations not run on cloud
- Different PostgreSQL version
- Schema drift from local

**Solution:**
```bash
# Verify migrations on cloud
ssh user@cloud-host
alembic current

# If not at head, run migrations
alembic upgrade head

# Verify schema matches
psql postgresql://...
\dt
```

### Issue: CORS errors in cloud

**Causes:**
- Frontend URL not in CORS whitelist
- Missing Access-Control headers
- Domain mismatch

**Solution:**
```bash
# Check CORS in backend
grep -r "CORS\|cors" backend/main.py

# Should allow frontend domain:
allow_origins=["https://cortex.app", "http://localhost:5173"]
```

## Continuous Validation

### Monthly Checks

```bash
# 1. Run E2E tests against production
BASE_URL=https://cortex.app npm run test:e2e

# 2. Verify database
psql postgresql://...
SELECT COUNT(*) FROM weeks;
SELECT COUNT(*) FROM player_pools;

# 3. Check API health
curl https://cortex.app/api/weeks

# 4. Spot check recent imports
SELECT * FROM import_history ORDER BY created_at DESC LIMIT 5;
```

### Before Each Deployment

```bash
# 1. Local tests pass
pytest -v && npm run test:e2e

# 2. Build succeeds
npm run build

# 3. Database migrations ready
alembic heads  # Show which migrations are at head

# 4. No breaking changes to API
# Review API changes before deployment
```

## Summary

Local development environment should be identical to cloud deployment in:

- Database version (PostgreSQL 15)
- Connection string format (postgresql://...)
- Table schemas and constraints
- API endpoint behavior
- Response formats and CORS
- Environment variable names
- Frontend build output
- TypeScript compilation

This parity ensures that "works locally" means "will work in cloud" and prevents deployment surprises.
