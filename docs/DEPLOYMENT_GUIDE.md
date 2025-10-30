# Deployment Guide - Week Management Feature

**Version:** 1.0
**Last Updated:** October 28, 2025
**Status:** Ready for Production Deployment

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Setup](#environment-setup)
3. [Database Deployment](#database-deployment)
4. [Backend Deployment](#backend-deployment)
5. [Frontend Deployment](#frontend-deployment)
6. [Post-Deployment Verification](#post-deployment-verification)
7. [Rollback Procedures](#rollback-procedures)
8. [Monitoring & Alerts](#monitoring--alerts)

---

## Pre-Deployment Checklist

### Code Quality

- [ ] All tests passing (55+ tests)
  ```bash
  pytest tests/ -v --cov=backend --cov=frontend
  ```
- [ ] No console errors or warnings
  ```bash
  npm run lint
  # and
  flake8 backend/
  ```
- [ ] No hardcoded values or secrets
  ```bash
  grep -r "password\|api_key\|secret" backend/ frontend/
  ```
- [ ] All dependencies up to date
  ```bash
  pip list
  npm list
  ```

### Security Review

- [ ] CORS properly configured (only allowed origins)
- [ ] SQL injection protection verified (using parameterized queries)
- [ ] No sensitive data in logs
- [ ] API authentication configured (if required)
- [ ] Environment variables properly set
- [ ] Database user has minimal required permissions

### Documentation Review

- [ ] API documentation complete
- [ ] Component documentation complete
- [ ] Service documentation complete
- [ ] Deployment guide ready
- [ ] Troubleshooting guide ready
- [ ] Performance guide available

### Performance Verification

- [ ] Database queries <100ms
- [ ] API responses <200ms
- [ ] Frontend bundle <100KB gzipped
- [ ] Animations 60fps consistent
- [ ] No memory leaks detected
- [ ] Lighthouse score >90

---

## Environment Setup

### Backend Environment Variables

Create `.env` file in backend directory:

```bash
# Database Configuration
DATABASE_URL=postgresql://cortex:password@localhost:5432/cortex_prod
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# FastAPI Configuration
FASTAPI_ENV=production
API_TITLE=Cortex DFS API
API_VERSION=1.0.0
DEBUG=False

# CORS Configuration
ALLOWED_ORIGINS=https://cortex.example.com,https://app.cortex.example.com

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/cortex/cortex.log

# Feature Flags
ENABLE_WEEK_MANAGEMENT=true
ENABLE_IMPORT_SYSTEM=true
AUTO_GENERATE_WEEKS=true

# Scheduled Tasks
SCHEDULE_ENABLED=true
SCHEDULE_UPDATE_STATUSES=0 0 * * *  # Cron: midnight UTC
```

### Frontend Environment Variables

Create `.env.production` in frontend directory:

```bash
# API Configuration
VITE_API_URL=https://api.cortex.example.com/api
VITE_API_TIMEOUT=30000

# Feature Flags
VITE_ENABLE_WEEK_MANAGEMENT=true
VITE_ENABLE_DARK_MODE=true

# Analytics (optional)
VITE_ANALYTICS_KEY=your_key_here

# Environment
VITE_ENV=production
```

### Database Configuration

```bash
# Create PostgreSQL user
sudo -u postgres createuser cortex -P

# Create database
sudo -u postgres createdb -O cortex cortex_prod

# Set permissions
sudo -u postgres psql -c "ALTER USER cortex WITH CREATEDB;"
sudo -u postgres psql -c "GRANT USAGE ON SCHEMA public TO cortex;"
```

---

## Database Deployment

### Run Migrations

```bash
# Navigate to backend directory
cd backend/

# Verify current database state
alembic current

# Run all pending migrations
alembic upgrade head

# Verify final state
alembic current

# Check migration history
alembic history --verbose
```

### Migration Files Deployed

The following migrations are part of the Week Management feature:

1. **002_extend_weeks_system.py** (Dependencies: 001)
   - Create week_metadata table
   - Create nfl_schedule table
   - Create week_status_overrides table
   - Extend weeks table with new columns
   - Create all necessary indexes

2. **003_seed_nfl_schedule.py** (Dependencies: 002)
   - Seed NFL schedule data for 2025-2030
   - Load 18 weeks per season (108 weeks total)
   - Verify Thanksgiving week (week 12) correct date
   - Verify week 18 spans to January

### Verify Database Schema

```bash
# Connect to PostgreSQL
psql postgresql://cortex:password@localhost:5432/cortex_prod

# Check weeks table extensions
\d weeks
# Should show: nfl_slate_date, status_override, metadata, is_locked, locked_at, updated_at

# Check new tables
\dt week_*
# Should show: week_metadata, week_status_overrides

# Check indexes
\di
# Should show all indexes created

# Verify NFL schedule data
SELECT COUNT(*) FROM nfl_schedule;  # Should be 108 (6 years * 18 weeks)
SELECT * FROM nfl_schedule WHERE season = 2025 LIMIT 5;
```

### Backup Database Before Migration

```bash
# Create backup
pg_dump postgresql://cortex:password@localhost:5432/cortex_prod \
  > cortex_backup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup
du -h cortex_backup_*.sql
```

---

## Backend Deployment

### Install Dependencies

```bash
# Navigate to backend directory
cd backend/

# Create virtual environment (if not already created)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installations
pip list | grep -E "fastapi|sqlalchemy|alembic|psycopg"
```

### Build & Package

```bash
# Build package
python setup.py sdist bdist_wheel

# Verify wheel created
ls -la dist/

# Test installation
pip install dist/cortex-1.0.0-py3-none-any.whl
```

### Deploy to Production Server

```bash
# Copy application files
scp -r backend/ deploy@server.example.com:/opt/cortex/

# SSH into server
ssh deploy@server.example.com

# Setup service file
sudo cp /opt/cortex/cortex.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable cortex
sudo systemctl start cortex

# Verify service running
sudo systemctl status cortex
```

### Systemd Service File

Create `/opt/cortex/cortex.service`:

```ini
[Unit]
Description=Cortex DFS API
After=network.target postgresql.service

[Service]
Type=notify
User=cortex
WorkingDirectory=/opt/cortex
Environment="PATH=/opt/cortex/venv/bin"
ExecStart=/opt/cortex/venv/bin/uvicorn \
  backend.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Verify Backend Deployment

```bash
# Check API health endpoint
curl https://api.cortex.example.com/health

# Expected response:
# {"status": "healthy", "database": "connected"}

# Check API documentation
curl https://api.cortex.example.com/docs

# Test week endpoint
curl https://api.cortex.example.com/api/weeks?year=2025
```

---

## Frontend Deployment

### Build for Production

```bash
# Navigate to frontend directory
cd frontend/

# Install dependencies
npm install

# Run linter
npm run lint

# Build production bundle
npm run build

# Verify bundle size
du -h dist/
# Should be <5MB total, <100KB gzipped
```

### Deploy to CDN/Web Server

#### Option 1: GitHub Pages (for static hosting)

```bash
# Build with base path (if needed)
npm run build -- --base=/cortex/

# Deploy using gh-pages
npm run deploy
```

#### Option 2: AWS S3 + CloudFront

```bash
# Build
npm run build

# Deploy to S3
aws s3 sync dist/ s3://cortex-app/

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id E1234ABCD \
  --paths "/*"
```

#### Option 3: Traditional Web Server (Nginx)

```bash
# Build
npm run build

# Copy to web server
scp -r dist/* deploy@server.example.com:/var/www/cortex/

# Nginx configuration
server {
    listen 443 ssl http2;
    server_name cortex.example.com;

    ssl_certificate /etc/ssl/certs/cortex.crt;
    ssl_certificate_key /etc/ssl/private/cortex.key;

    root /var/www/cortex;
    index index.html;

    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api {
        proxy_pass https://api.cortex.example.com;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # No caching for HTML
    location ~* \.html?$ {
        expires -1;
        add_header Cache-Control "public, must-revalidate, proxy-revalidate";
    }
}
```

### Verify Frontend Deployment

```bash
# Check application loads
curl https://cortex.example.com/

# Check API connectivity
curl https://cortex.example.com/api/health

# Verify in browser
# Open https://cortex.example.com
# Check browser console for errors
# Verify week selection works
```

---

## Post-Deployment Verification

### Run Deployment Checklist

#### Database Verification
```bash
# Check connections
psql -U cortex -d cortex_prod -c "SELECT version();"

# Verify tables
psql -U cortex -d cortex_prod -c "\dt"

# Verify NFL schedule seeded
psql -U cortex -d cortex_prod -c "SELECT COUNT(*) FROM nfl_schedule;"

# Sample data
psql -U cortex -d cortex_prod -c "SELECT * FROM nfl_schedule LIMIT 5;"
```

#### Backend Verification
```bash
# Health check
curl -X GET https://api.cortex.example.com/health

# Get weeks for 2025
curl -X GET "https://api.cortex.example.com/api/weeks?year=2025"

# Get current week
curl -X GET https://api.cortex.example.com/api/current-week

# Get NFL schedule
curl -X GET https://api.cortex.example.com/api/nfl-schedule
```

#### Frontend Verification
```bash
# Page load test
time curl -o /dev/null -s -w "%{time_total}s\n" https://cortex.example.com

# Bundle size check
curl -I https://cortex.example.com/assets/main.js | grep -i "content-length"

# Manual testing checklist:
# - [ ] Page loads without errors
# - [ ] Week selector displays all 18 weeks
# - [ ] Current week highlighted with glow
# - [ ] Can select different week
# - [ ] Metadata displays correctly
# - [ ] Year selector shows 2025-2030
# - [ ] Can select different year
# - [ ] Mobile responsive (test on mobile device)
# - [ ] Carousel swipes correctly on mobile
# - [ ] Dark mode looks good
# - [ ] ESPN links work
# - [ ] No console errors
```

### Performance Baseline

```bash
# Database query performance
time psql -U cortex -d cortex_prod -c "SELECT * FROM weeks WHERE season = 2025;"
# Should be <100ms

# API response time
time curl -X GET "https://api.cortex.example.com/api/weeks?year=2025" > /dev/null
# Should be <200ms

# Frontend performance
# Open Lighthouse in Chrome DevTools
# Check performance score (target >90)
```

### Smoke Tests

```bash
# Create test script
cat > smoke_tests.sh << 'EOF'
#!/bin/bash

echo "Running smoke tests..."

# Test 1: Health check
echo "1. Health check..."
curl -f https://api.cortex.example.com/health || exit 1

# Test 2: Get weeks
echo "2. Get weeks..."
curl -f "https://api.cortex.example.com/api/weeks?year=2025" || exit 1

# Test 3: Get current week
echo "3. Get current week..."
curl -f https://api.cortex.example.com/api/current-week || exit 1

# Test 4: Get NFL schedule
echo "4. Get NFL schedule..."
curl -f https://api.cortex.example.com/api/nfl-schedule || exit 1

echo "All smoke tests passed!"
EOF

chmod +x smoke_tests.sh
./smoke_tests.sh
```

---

## Rollback Procedures

### If Backend Deployment Fails

```bash
# Stop current service
sudo systemctl stop cortex

# Revert to previous version
git checkout <previous_commit>

# Rebuild and redeploy
cd backend/
pip install -r requirements.txt
./deploy.sh

# Verify
sudo systemctl start cortex
sudo systemctl status cortex
```

### If Database Migration Fails

```bash
# Rollback migration
alembic downgrade -1

# OR rollback to specific revision
alembic downgrade <revision_id>

# Verify rollback
alembic current

# Restore from backup if needed
psql -U cortex -d cortex_prod < cortex_backup_YYYYMMDD_HHMMSS.sql
```

### If Frontend Deployment Fails

```bash
# Check deployment logs
npm run build 2>&1 | tee build.log

# Clear cache
rm -rf dist/ node_modules/.vite/

# Rebuild
npm install
npm run build

# Redeploy
npm run deploy

# If needed, revert to previous CDN version
aws s3 sync s3://cortex-app-backup/previous-build/ s3://cortex-app/
```

---

## Monitoring & Alerts

### Backend Monitoring

```python
# Add monitoring middleware to FastAPI app
from prometheus_client import Counter, Histogram

request_count = Counter(
    'cortex_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint']
)

request_duration = Histogram(
    'cortex_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    request_count.labels(
        method=request.method,
        endpoint=request.url.path
    ).inc()

    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    return response
```

### Key Metrics to Monitor

**Backend:**
- API response time (target: <200ms)
- Error rate (target: <1%)
- Database connection pool usage
- CPU and memory usage
- Request volume

**Frontend:**
- Page load time (target: <3s)
- JavaScript errors
- API request failures
- User session duration

**Database:**
- Query execution time (target: <100ms)
- Connection count
- Disk usage
- Lock waits
- Replication lag (if applicable)

### Alert Rules

```yaml
# Prometheus alert rules
groups:
- name: cortex_alerts
  rules:
  - alert: HighAPIErrorRate
    expr: rate(cortex_requests_total{status=~"5.."}[5m]) > 0.01
    for: 5m
    annotations:
      summary: "High API error rate detected"

  - alert: SlowDatabaseQueries
    expr: histogram_quantile(0.95, cortex_db_query_duration) > 0.1
    for: 10m
    annotations:
      summary: "Database queries running slowly"

  - alert: LowDiskSpace
    expr: node_filesystem_avail_bytes / node_filesystem_size_bytes < 0.1
    for: 5m
    annotations:
      summary: "Low disk space on database server"
```

### Logging Configuration

```python
# Configure structured logging
import logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger()
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

# Log all API requests
logger.info("API Request", extra={
    "method": "GET",
    "endpoint": "/api/weeks",
    "year": 2025,
    "response_time": 0.123,
    "status_code": 200,
})
```

---

## Deployment Checklist Summary

```
Pre-Deployment:
- [ ] Tests passing
- [ ] No console errors
- [ ] No hardcoded secrets
- [ ] Security review complete

Environment:
- [ ] .env files created
- [ ] Database user configured
- [ ] Permissions set

Database:
- [ ] Backup created
- [ ] Migrations run
- [ ] Schema verified
- [ ] Data seeded

Backend:
- [ ] Dependencies installed
- [ ] Service configured
- [ ] Health check passes
- [ ] API endpoints working

Frontend:
- [ ] Build successful
- [ ] Bundle size verified
- [ ] Deployed to CDN/server
- [ ] Page loads correctly

Post-Deployment:
- [ ] All endpoints tested
- [ ] Performance baseline established
- [ ] Smoke tests pass
- [ ] Monitoring configured
- [ ] Alerts enabled
- [ ] Documentation updated
```

---

**End of Deployment Guide**
