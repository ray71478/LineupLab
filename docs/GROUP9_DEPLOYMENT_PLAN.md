# Player Management Deployment Plan

**Version:** 1.0
**Date:** October 29, 2025
**Scope:** Task 9.4 - Deployment & Rollout Plan

---

## Table of Contents

1. [Deployment Checklist](#deployment-checklist)
2. [Environment Setup](#environment-setup)
3. [Database Migrations](#database-migrations)
4. [Pre-Deployment Verification](#pre-deployment-verification)
5. [Deployment Steps](#deployment-steps)
6. [Post-Deployment Verification](#post-deployment-verification)
7. [Rollback Plan](#rollback-plan)
8. [Rollout Strategy](#rollout-strategy)

---

## Deployment Checklist

### Pre-Deployment (1-2 Days Before)

- [ ] All code merged to main branch
- [ ] All tests passing (unit, integration, E2E)
- [ ] Code review completed and approved
- [ ] Database migrations tested in staging
- [ ] Environment variables prepared
- [ ] Deployment plan reviewed by tech lead
- [ ] Team notified of deployment window
- [ ] Backup of current production database created
- [ ] Documentation updated and reviewed
- [ ] Rollback plan prepared and tested

### Deployment Day (During Window)

- [ ] Production database backed up
- [ ] Maintenance page deployed (optional)
- [ ] Database migrations executed
- [ ] Backend code deployed
- [ ] Frontend code deployed
- [ ] Health checks pass
- [ ] Smoke tests executed
- [ ] Monitor error logs
- [ ] Monitor API response times
- [ ] Monitor user feedback

### Post-Deployment (30 Days)

- [ ] Monitor for errors and issues
- [ ] Track feature usage metrics
- [ ] Gather user feedback
- [ ] Document lessons learned
- [ ] Plan Phase 2 improvements

---

## Environment Setup

### Staging Environment

**Configuration:**
- Database: Copy of production data (anonymized if needed)
- API URL: https://staging-api.example.com
- Frontend URL: https://staging.example.com
- Features: All enabled for testing

**Setup Steps:**
```bash
# 1. Create staging database from production backup
pg_dump production_db | psql staging_db

# 2. Deploy staging code
git checkout main
git pull origin main
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# 3. Run migrations
alembic upgrade head

# 4. Seed test data if needed
python scripts/seed_test_data.py

# 5. Run health checks
curl https://staging-api.example.com/health
```

### Production Environment

**Configuration:**
- Database: PostgreSQL 12+ with backups
- API URL: https://api.example.com
- Frontend URL: https://example.com
- Features: Gradually enabled via feature flags

**Monitoring:**
- New Relic or similar APM
- CloudWatch or ELK logs
- Datadog or Prometheus metrics
- PagerDuty for alerts

---

## Database Migrations

### Migration Strategy

**Timing:** Execute migrations before deploying new code

**Migrations for Phase 1 (Group 9):**
- `001_initial_schema.py` - Already applied (Phase 0)
- `002-009_*.py` - Already applied (Phase 0-1)
- `010_final_verification.py` - Run during deployment (verification only)

### Running Migrations

**Staging:**
```bash
cd /Users/raybargas/Documents/Cortex
alembic upgrade head

# Verify migration
psql $DATABASE_URL -c "SELECT * FROM alembic_version;"
```

**Production:**
```bash
# During maintenance window
ssh production-server
cd /var/app/cortex
alembic upgrade head

# Verify
psql production_db -c "SELECT * FROM alembic_version;"

# If issues, rollback
alembic downgrade -1
```

### Rollback Migrations

If migrations fail:

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade 002_extend_weeks_system

# Check current version
alembic current
```

### Data Verification

After migrations, verify data integrity:

```bash
# Check player_pools table
SELECT COUNT(*) FROM player_pools; -- Should match production count

# Check unmatched_players
SELECT COUNT(*) FROM unmatched_players;

# Check player_aliases
SELECT COUNT(*) FROM player_aliases;

# Verify indexes
SELECT * FROM pg_indexes WHERE tablename = 'player_pools';
```

---

## Pre-Deployment Verification

### Code Quality

```bash
# Backend
cd backend
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
pylint backend/ --disable=all --enable=E,F

# Frontend
cd ../frontend
npx eslint src/
npx tsc --noEmit
```

### Test Results

```bash
# Backend tests (must pass)
pytest tests/ -v --tb=short

# Frontend tests (must pass)
npm test -- --coverage

# E2E tests (must pass)
npx playwright test
```

### Performance Baseline

```bash
# Measure current performance
# GET /api/players/by-week/42
ab -n 100 -c 10 https://staging-api.example.com/api/players/by-week/42

# Expected: Response time < 500ms
# Expected: Success rate 100%
```

### Security Audit

```bash
# Check for vulnerabilities
npm audit
pip-audit

# Check for hardcoded secrets
git log --oneline | grep -i "secret\|password\|key"
grep -r "password\|secret\|api_key" backend/ --include="*.py" --include="*.env*"
```

---

## Deployment Steps

### Phase 1: Prepare (30 minutes)

1. **Notify Team**
   ```
   Slack message: "Starting Player Management v1.0 deployment. Expected duration: 1 hour. Updates to follow."
   ```

2. **Backup Production Database**
   ```bash
   pg_dump production_db -Fc > /backups/production_db_backup_$(date +%Y%m%d_%H%M%S).sql
   ```

3. **Tag Release**
   ```bash
   git tag -a v1.0-player-management -m "Player Management v1.0 Release"
   git push origin v1.0-player-management
   ```

4. **Enable Maintenance Mode** (Optional)
   - Deploy maintenance page
   - Show "System maintenance in progress" message
   - Estimated completion time

### Phase 2: Backend Deployment (15 minutes)

1. **Deploy Code**
   ```bash
   cd /var/app/cortex
   git fetch origin
   git checkout v1.0-player-management

   # Install dependencies
   pip install -r requirements.txt

   # Run migrations
   alembic upgrade head

   # Restart service
   systemctl restart cortex-backend
   ```

2. **Verify Deployment**
   ```bash
   # Health check
   curl https://api.example.com/health

   # Check logs
   tail -f /var/log/cortex/backend.log

   # Verify endpoints
   curl https://api.example.com/api/players/by-week/1
   ```

3. **Monitor Errors**
   - Check error logs
   - Monitor APM dashboard
   - Alert on error rate > 1%

### Phase 3: Frontend Deployment (15 minutes)

1. **Build & Deploy**
   ```bash
   cd /var/app/cortex/frontend
   git fetch origin
   git checkout v1.0-player-management
   npm ci
   npm run build

   # Deploy to CDN/static server
   aws s3 sync dist/ s3://cortex-frontend-bucket/

   # Invalidate CloudFront cache
   aws cloudfront create-invalidation --distribution-id XXXXX --paths "/*"
   ```

2. **Verify Deployment**
   - Check frontend loads at https://example.com
   - Verify player management page accessible
   - Test key workflows

3. **Monitor Performance**
   - Check Core Web Vitals
   - Monitor JavaScript errors
   - Check API response times

### Phase 4: Smoke Tests (10 minutes)

Run critical user workflows:

```bash
# Test 1: Load player management page
curl -I https://example.com/players

# Test 2: Fetch players
curl https://api.example.com/api/players/by-week/1

# Test 3: Get unmatched players
curl https://api.example.com/api/players/unmatched/1

# Test 4: Search players
curl "https://api.example.com/api/players/search?q=Mahomes"

# Test 5: Get suggestions
curl https://api.example.com/api/players/suggestions/1
```

### Phase 5: Cleanup & Notify (5 minutes)

1. **Remove Maintenance Mode**
   - Deploy normal application
   - Verify all pages accessible

2. **Document Deployment**
   ```
   Deployment Log:
   - Completed at: [timestamp]
   - Duration: [minutes]
   - Issues: [none/list]
   - Rollbacks: [none/list]
   - Performance: [metrics]
   ```

3. **Notify Stakeholders**
   ```
   Slack: "Player Management v1.0 deployed successfully!
   - All systems operational
   - Feature available at /players
   - Monitor dashboard: [link]"
   ```

---

## Post-Deployment Verification

### Immediate Checks (First 30 Minutes)

```bash
# 1. Check error logs
tail -f /var/log/cortex/backend.log | grep -i "error"

# 2. Monitor API response times
watch 'curl -w "@curl_format.txt" https://api.example.com/api/players/by-week/1'

# 3. Monitor error rate
curl https://api.example.com/metrics | grep error_rate

# 4. Check database performance
psql production_db -c "SELECT * FROM pg_stat_statements LIMIT 10;"

# 5. Test key workflows
- Load /players page
- Filter by position
- Search for player
- View unmatched players
- Map a player
```

### Dashboard Monitoring (First 24 Hours)

Monitor these metrics on your APM dashboard:

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| API Response Time (p95) | < 500ms | > 1000ms |
| Error Rate | < 0.1% | > 1% |
| HTTP 5xx Status Code | < 1% | > 5% |
| Database CPU | < 70% | > 85% |
| Memory Usage | < 80% | > 90% |
| Request Volume | Baseline | +200% |

### Verification Tests

**Manual Testing Checklist:**

- [ ] Players page loads in < 2 seconds
- [ ] Table displays all players
- [ ] Unmatched alert appears if unmatched players exist
- [ ] Filtering by position works
- [ ] Filtering by team works
- [ ] Sorting by column works
- [ ] Search finds players
- [ ] Modal opens for unmatched player
- [ ] Suggestions display with scores
- [ ] Can select suggestion
- [ ] Can confirm mapping
- [ ] Player moves to matched after mapping
- [ ] Unmatched count decreases
- [ ] Mobile layout responsive
- [ ] Touch targets adequately sized

---

## Rollback Plan

### When to Rollback

Rollback immediately if:
- Error rate > 5% for > 5 minutes
- Response time > 5 seconds
- Database connection failures
- Critical user-facing bugs
- Data integrity issues

### Rollback Steps

**Step 1: Decide to Rollback** (2 minutes)
```
Decision criteria:
- Error rate > 5%
- Critical bug preventing usage
- Data loss detected
- Cannot resolve in < 15 minutes
```

**Step 2: Notify Team** (1 minute)
```
Slack: "@here Initiating rollback of Player Management v1.0.
Reason: [specific reason]. ETA: 10 minutes."
```

**Step 3: Rollback Backend** (5 minutes)
```bash
# Get previous version
git checkout v0.9-previous-version

# Stop service
systemctl stop cortex-backend

# Rollback database (if migrations changed schema)
alembic downgrade -1
alembic downgrade -1  # etc.

# Redeploy previous code
pip install -r requirements.txt
systemctl start cortex-backend

# Verify
curl https://api.example.com/health
```

**Step 4: Rollback Frontend** (5 minutes)
```bash
# Redeploy previous version
aws s3 sync s3://cortex-frontend-bucket/versions/v0.9/ s3://cortex-frontend-bucket/

# Invalidate cache
aws cloudfront create-invalidation --distribution-id XXXXX --paths "/*"

# Verify
curl -I https://example.com/players
```

**Step 5: Verify Rollback** (3 minutes)
- [ ] API endpoints responding
- [ ] Frontend loads
- [ ] Workflows functional
- [ ] Error rate normal
- [ ] Database consistent

**Step 6: Post-Mortem** (Next day)
- Root cause analysis
- Timeline of events
- Prevention measures
- Communication summary

### Rollback Communication

```
Slack: "Rollback of Player Management v1.0 complete.
Previous version v0.9 restored and operational.
RCA scheduled for [time].
Updates to follow."

Email to stakeholders:
Subject: Player Management Rollback - Incident Report

We rolled back the Player Management v1.0 release due to [reason].
Previous version is now active.
We will investigate and deploy a fix [when].
Please report any issues.
```

---

## Rollout Strategy

### Phased Rollout (Recommended)

**Phase 1: Internal Testing (Week 1)**
- Deploy to staging environment
- Internal team testing
- Fix any issues found
- Measure performance

**Phase 2: Limited Beta (Week 2)**
- Deploy to production for 5% of users
- Monitor error rates
- Gather feedback
- Performance analysis

**Phase 3: Extended Beta (Week 3)**
- Deploy to 25% of users
- Monitor usage patterns
- Collect analytics
- Identify edge cases

**Phase 4: Full Release (Week 4)**
- Deploy to 100% of users
- Monitor closely for 24 hours
- Be ready to rollback if needed
- Celebrate launch

### Feature Flags (Optional)

Use feature flags for controlled rollout:

```python
# In backend code
if feature_flag_enabled('player_management_v1'):
    return render_player_management_page()
else:
    return render_old_page()
```

### Metrics to Track During Rollout

| Metric | Target |
|--------|--------|
| Error Rate | < 0.5% |
| Response Time (p95) | < 1000ms |
| Feature Adoption | Increasing trend |
| User Satisfaction | > 4/5 stars |
| Bug Reports | < 5 per day |

---

## Environment Variables

### Production (.env)

```bash
# Database
DATABASE_URL=postgresql://user:pass@prod-db.rds.amazonaws.com/cortex

# API
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Security
JWT_SECRET=[32-char-random-string]
ALLOWED_ORIGINS=https://example.com,https://www.example.com

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Monitoring
SENTRY_DSN=https://...@sentry.io/...
DATADOG_API_KEY=[key]

# Features
DEBUG=false
MAINTENANCE_MODE=false
```

### Staging (.env.staging)

```bash
# Database
DATABASE_URL=postgresql://user:pass@staging-db.rds.amazonaws.com/cortex_staging

# API
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=2

# Security
JWT_SECRET=[different-32-char-string]
ALLOWED_ORIGINS=https://staging.example.com

# Logging
LOG_LEVEL=DEBUG
LOG_FORMAT=text

# Monitoring
SENTRY_DSN=https://...@sentry.io/...

# Features
DEBUG=true
MAINTENANCE_MODE=false
```

### Frontend (.env.production)

```bash
VITE_API_URL=https://api.example.com
VITE_API_TIMEOUT=5000
VITE_LOG_LEVEL=warn
VITE_SENTRY_DSN=https://...@sentry.io/...
```

---

## Success Criteria

### Deployment Success Checklist

- [ ] Zero data loss
- [ ] All endpoints responding (200 status)
- [ ] Error rate < 0.1% after 1 hour
- [ ] API response time < 500ms (p95)
- [ ] Frontend loads in < 2 seconds
- [ ] All user workflows functional
- [ ] Database migrations successful
- [ ] No security vulnerabilities introduced
- [ ] Team notified with status
- [ ] Documentation updated

### User Success Metrics

After 1 week:
- [ ] Player Management page views > 100
- [ ] Unmatched players mapped > 90%
- [ ] User feedback positive (> 4/5)
- [ ] Bug reports < 5
- [ ] Performance metrics stable

---

**Deployment Plan Complete**
**Status:** Ready for Deployment
**Last Updated:** October 29, 2025
