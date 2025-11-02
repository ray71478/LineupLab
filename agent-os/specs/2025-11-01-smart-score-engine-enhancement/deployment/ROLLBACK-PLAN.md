# Projection Calibration System - Rollback Plan
**Task Group 12: Production Deployment**
**Feature:** Smart Score Engine Enhancement - Projection Calibration System
**Date:** 2025-11-01

---

## Rollback Overview

### When to Execute Rollback

Execute this rollback plan if any of the following conditions occur within 24 hours of deployment:

**CRITICAL Issues (Immediate Rollback Required):**
- Database corruption or data loss detected
- Application crashes or becomes unresponsive
- Import process fails completely and cannot recover
- Smart Score calculations produce NULL or invalid results
- Lineup generation fails for all users
- Security vulnerability discovered
- > 25% error rate in calibration API endpoints

**HIGH Issues (Rollback Within 1 Hour):**
- Import time increases > 20% (spec requirement is < 5%)
- Calibration applies incorrectly to > 10% of players
- Database query performance degrades > 50%
- Frontend completely broken (white screen, cannot load)
- User data loss or incorrect calculations affecting money lineups

**MEDIUM Issues (Consider Rollback or Hotfix):**
- Import time increases 5-20% (above spec but functional)
- Calibration missing for some positions but not all
- UI glitches affecting calibration display
- < 25% error rate in non-critical API endpoints
- Performance degradation 25-50%

**LOW Issues (Monitor, No Rollback):**
- Minor UI styling issues
- Calibration admin interface UX improvements needed
- Non-critical validation errors
- Documentation corrections needed

---

## Rollback Decision Matrix

| Issue Severity | User Impact | Data Risk | Performance Impact | Decision |
|----------------|-------------|-----------|-------------------|----------|
| CRITICAL | High | High | Any | **ROLLBACK IMMEDIATELY** |
| HIGH | Medium-High | Medium-High | > 50% | **ROLLBACK WITHIN 1 HOUR** |
| MEDIUM | Medium | Low-Medium | 25-50% | **ASSESS: Rollback or Hotfix** |
| LOW | Low | None | < 25% | **Monitor, Fix in Next Release** |

---

## Pre-Rollback Checklist

Before executing rollback, complete these steps:

- [ ] **Document the Issue**
  - Capture error messages, stack traces, logs
  - Screenshot UI issues
  - Record database query performance metrics
  - Document user reports and impact

- [ ] **Assess Severity** (Use Decision Matrix Above)
  - Determine severity level (CRITICAL, HIGH, MEDIUM, LOW)
  - Estimate user impact (number of users affected)
  - Assess data integrity risk
  - Measure performance degradation

- [ ] **Notify Stakeholders**
  - Alert development team
  - Inform product owner
  - Notify users if needed (for CRITICAL/HIGH issues)
  - Document rollback decision in incident log

- [ ] **Backup Current State Before Rollback**
  ```bash
  # Backup current production database
  pg_dump -h <host> -U <user> -d <database> -F c \
    -f cortex_pre_rollback_$(date +%Y%m%d_%H%M%S).dump

  # Document current application version
  git rev-parse HEAD > rollback_from_commit.txt

  # Save current calibration data
  psql -h <host> -U <user> -d <database> -c \
    "COPY projection_calibration TO '/tmp/calibration_backup.csv' CSV HEADER;"
  ```

- [ ] **Prepare Rollback Window**
  - Schedule maintenance window if needed
  - Prepare communication to users
  - Ensure rollback team available
  - Test rollback procedure in staging first (if time permits)

---

## Rollback Procedures

### Option 1: Database-Only Rollback (If Backend/Frontend OK)

**Use When:** Database migrations caused issues, but code is functional

**Estimated Time:** 5-10 minutes

**Steps:**

1. **Stop Application (Prevent New Writes)**
   ```bash
   # Stop application server
   sudo systemctl stop cortex-api

   # Or disable API endpoints
   # Set MAINTENANCE_MODE=true in environment
   ```

2. **Rollback Database Migrations**
   ```bash
   cd /Users/raybargas/Documents/Cortex

   # Rollback migration 021 (Seed default calibration values)
   alembic downgrade -1

   # Rollback migration 020 (Add calibrated columns to player_pools)
   alembic downgrade -1

   # Rollback migration 019 (Create projection_calibration table)
   alembic downgrade -1

   # Verify rollback
   alembic current
   ```

3. **Verify Database State**
   ```sql
   -- Verify projection_calibration table removed
   SELECT table_name
   FROM information_schema.tables
   WHERE table_name = 'projection_calibration';
   -- Should return 0 rows

   -- Verify player_pools columns removed
   SELECT column_name
   FROM information_schema.columns
   WHERE table_name = 'player_pools'
   AND column_name LIKE '%calibrat%';
   -- Should return 0 rows
   ```

4. **Restore Application**
   ```bash
   # Start application server
   sudo systemctl start cortex-api

   # Verify application running
   curl http://localhost:8000/health
   ```

5. **Verify Functionality**
   - Test import without calibration
   - Verify Smart Score calculations work
   - Test lineup generation
   - Check player detail views (should show single values)

---

### Option 2: Code Rollback (If Backend/Frontend Issues)

**Use When:** Backend services or frontend components causing issues

**Estimated Time:** 10-15 minutes

**Steps:**

1. **Identify Rollback Target Commit**
   ```bash
   # Find commit before calibration feature deployment
   git log --oneline --all | head -20

   # Identify commit hash (e.g., 3b2622d)
   # "Improve lineup generation progress indicator..."
   ```

2. **Rollback Backend Code**
   ```bash
   cd /Users/raybargas/Documents/Cortex

   # Create rollback branch
   git checkout -b rollback-calibration

   # Reset to pre-calibration commit
   git reset --hard <commit_hash>

   # Deploy rolled-back backend
   # (Deployment method varies: Docker, systemd, etc.)
   sudo systemctl restart cortex-api
   ```

3. **Rollback Frontend Code**
   ```bash
   cd /Users/raybargas/Documents/Cortex/frontend

   # Reset frontend to pre-calibration commit
   git reset --hard <commit_hash>

   # Rebuild production bundle
   npm run build

   # Deploy frontend assets
   # (Copy to web server, CDN, etc.)
   cp -r build/* /var/www/cortex/
   ```

4. **Verify Application Functionality**
   ```bash
   # Test health endpoint
   curl http://localhost:8000/health

   # Test import endpoint (without calibration)
   curl -X POST http://localhost:8000/api/import/draftkings/{week_id} \
     -F "file=@test_data.xlsx"

   # Verify frontend loads
   curl http://localhost:8000/ | grep "<!DOCTYPE html>"
   ```

5. **Rollback Database (If Needed)**
   - Follow "Option 1: Database-Only Rollback" steps
   - Only if database schema incompatible with rolled-back code

---

### Option 3: Full System Restore (If Data Corruption)

**Use When:** Database corruption, data loss, or catastrophic failure

**Estimated Time:** 30-60 minutes

**Steps:**

1. **Stop All Services**
   ```bash
   # Stop application
   sudo systemctl stop cortex-api

   # Stop frontend server (if separate)
   sudo systemctl stop nginx

   # Prevent user access
   # Set firewall rules or load balancer to maintenance mode
   ```

2. **Restore Database from Backup**
   ```bash
   # List available backups
   ls -lh /backups/cortex_backup_*.dump

   # Choose pre-deployment backup
   # Example: cortex_backup_20251101_080000.dump

   # Drop current database (DANGEROUS - ensure backup is valid!)
   psql -h <host> -U <user> -c "DROP DATABASE cortex;"

   # Create fresh database
   psql -h <host> -U <user> -c "CREATE DATABASE cortex;"

   # Restore from backup
   pg_restore -h <host> -U <user> -d cortex -F c \
     /backups/cortex_backup_20251101_080000.dump

   # Verify restoration
   psql -h <host> -U <user> -d cortex -c \
     "SELECT COUNT(*) FROM player_pools;"
   ```

3. **Rollback Code (Backend + Frontend)**
   - Follow "Option 2: Code Rollback" steps
   - Ensure code matches database schema

4. **Verify Data Integrity**
   ```sql
   -- Check player pools data
   SELECT COUNT(*) as total_players,
          COUNT(DISTINCT week_id) as weeks
   FROM player_pools;

   -- Check weeks table
   SELECT week_number, year, is_active
   FROM weeks
   ORDER BY year DESC, week_number DESC
   LIMIT 5;

   -- Verify no calibration columns exist
   SELECT column_name
   FROM information_schema.columns
   WHERE table_name = 'player_pools'
   AND column_name LIKE '%calibrat%';
   -- Should return 0 rows
   ```

5. **Restart Services**
   ```bash
   # Start database (if stopped)
   sudo systemctl start postgresql

   # Start application
   sudo systemctl start cortex-api

   # Start frontend server
   sudo systemctl start nginx

   # Remove firewall/load balancer restrictions
   ```

6. **Comprehensive Functionality Testing**
   - Test all critical workflows
   - Verify data accuracy
   - Check user accounts and access
   - Test import, Smart Score, lineup generation
   - Monitor logs for errors

---

## Post-Rollback Procedures

### Immediate Post-Rollback (Within 1 Hour)

1. **Verify System Stability**
   ```bash
   # Monitor logs for errors
   tail -f /var/log/cortex/application.log | grep -i "error"

   # Check application health
   curl http://localhost:8000/health

   # Monitor database connections
   psql -h <host> -U <user> -d cortex -c \
     "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"
   ```

2. **Confirm User Impact Resolved**
   - Test critical user workflows
   - Verify import process works
   - Check Smart Score calculations
   - Test lineup generation
   - Monitor user reports/complaints

3. **Document Rollback**
   - Record rollback timestamp
   - Document what was rolled back (database, code, or both)
   - Capture final error logs before rollback
   - Note any data loss or impact
   - Update incident tracking system

4. **Communicate Status**
   - Notify stakeholders rollback complete
   - Inform users system is stable
   - Provide timeline for fix deployment
   - Set expectations for feature re-release

### Short-Term Post-Rollback (1-24 Hours)

5. **Root Cause Analysis**
   - Analyze error logs and stack traces
   - Review code changes that caused issue
   - Identify specific bug or design flaw
   - Document lessons learned
   - Create plan to prevent recurrence

6. **Plan Remediation**
   - Fix identified bugs in development
   - Add tests to prevent regression
   - Re-test in staging environment
   - Schedule new deployment (with fixes)
   - Prepare improved rollback procedures

7. **Monitor for Residual Issues**
   - Watch logs for 24 hours
   - Monitor user reports
   - Check performance metrics
   - Verify data integrity
   - Track system stability

### Long-Term Post-Rollback (1-7 Days)

8. **Prepare Re-Deployment**
   - Fix all identified issues
   - Add regression tests
   - Conduct thorough QA in staging
   - Plan more conservative deployment
   - Consider phased rollout (e.g., 10% of users first)

9. **Update Documentation**
   - Improve deployment procedures
   - Enhance monitoring and alerting
   - Update rollback plan with learnings
   - Document new edge cases discovered
   - Create incident post-mortem report

10. **Stakeholder Review**
    - Present root cause analysis
    - Review remediation plan
    - Get approval for re-deployment
    - Set new deployment timeline
    - Document deployment improvements

---

## Rollback Testing (Staging Environment)

**Before Production Deployment:** Test rollback procedures in staging

### Rollback Test Procedure

1. **Setup Staging Environment**
   ```bash
   # Deploy calibration feature to staging
   # Apply all migrations (019, 020, 021)
   # Deploy backend services
   # Deploy frontend components
   ```

2. **Test Database Rollback**
   ```bash
   # Execute rollback migrations
   alembic downgrade -3

   # Verify tables/columns removed
   # Verify application still functions

   # Re-apply migrations
   alembic upgrade head
   ```

3. **Test Code Rollback**
   ```bash
   # Reset to pre-calibration commit
   git reset --hard <previous_commit>

   # Rebuild and deploy
   # Verify application works

   # Re-deploy calibration feature
   git reset --hard <calibration_commit>
   ```

4. **Test Full System Restore**
   ```bash
   # Create staging backup
   # Simulate data corruption
   # Restore from backup
   # Verify data integrity
   ```

5. **Document Test Results**
   - Record rollback time for each method
   - Note any issues encountered
   - Validate procedures are accurate
   - Update rollback plan if needed

---

## Rollback Decision Authority

### Approval Required

| Severity Level | Who Can Approve Rollback | Response Time |
|----------------|--------------------------|---------------|
| CRITICAL | Any Senior Engineer or DevOps Lead | Immediate (0-5 min) |
| HIGH | Engineering Manager or Team Lead | Within 15 min |
| MEDIUM | Product Owner + Tech Lead | Within 1 hour |
| LOW | Product Owner Decision | Next Business Day |

### Emergency Contacts

```
Senior Engineer:     [Name] - [Phone] - [Email]
DevOps Lead:         [Name] - [Phone] - [Email]
Engineering Manager: [Name] - [Phone] - [Email]
Product Owner:       [Name] - [Phone] - [Email]
Database Admin:      [Name] - [Phone] - [Email]
```

---

## Rollback Success Criteria

### ✅ Rollback Complete When:

- [ ] Application is stable and responsive
- [ ] No errors in application logs (except expected warnings)
- [ ] Import process completes successfully without calibration
- [ ] Smart Score calculations produce valid results
- [ ] Lineup generation works for all users
- [ ] Database queries perform at baseline levels
- [ ] Frontend loads without errors
- [ ] User workflows function correctly
- [ ] No data loss or corruption detected
- [ ] Monitoring shows healthy system metrics

### ✅ System Health Metrics (Post-Rollback)

**Application Metrics:**
- ✅ Error rate < 1% (baseline level)
- ✅ API response time < 200ms (p95)
- ✅ Application uptime 100% for 1 hour post-rollback
- ✅ No database connection errors
- ✅ No timeout errors

**Data Integrity:**
- ✅ Player pools data intact and accurate
- ✅ Smart Score values valid
- ✅ Lineup generation produces valid lineups
- ✅ No NULL values where data expected
- ✅ Foreign key constraints satisfied

**User Experience:**
- ✅ Import completes in < 2 minutes (baseline)
- ✅ Player Pool screen loads in < 3 seconds
- ✅ No user-reported data issues
- ✅ All critical workflows functional
- ✅ No UI errors or white screens

---

## Incident Log Template

```
ROLLBACK INCIDENT LOG
=====================

Incident ID: _____________________
Date/Time: _____________________
Severity: [ ] CRITICAL  [ ] HIGH  [ ] MEDIUM  [ ] LOW

ISSUE DESCRIPTION
-----------------
What went wrong: _____________________
When discovered: _____________________
User impact: _____________________
Systems affected: _____________________

ERROR DETAILS
-------------
Error messages: _____________________
Stack traces: _____________________
Affected users: _____________________
Data impact: _____________________

ROLLBACK DECISION
-----------------
Decision maker: _____________________
Approval time: _____________________
Rollback method: [ ] Database  [ ] Code  [ ] Full Restore
Estimated downtime: _____________________

ROLLBACK EXECUTION
------------------
Rollback started: _____________________
Database rollback: _____________________
Code rollback: _____________________
Services restarted: _____________________
Rollback completed: _____________________

POST-ROLLBACK VALIDATION
------------------------
System stability verified: _____________________
User impact resolved: _____________________
Data integrity confirmed: _____________________
No residual errors: _____________________

ROOT CAUSE ANALYSIS
-------------------
Primary cause: _____________________
Contributing factors: _____________________
Code/config issue: _____________________
Missed in testing: _____________________

REMEDIATION PLAN
----------------
Fixes required: _____________________
Additional testing: _____________________
Re-deployment timeline: _____________________
Prevention measures: _____________________

LESSONS LEARNED
---------------
What went well: _____________________
What could improve: _____________________
Process changes: _____________________
Documentation updates: _____________________

Sign-off: _____________________
Date/Time: _____________________
```

---

## Rollback Communication Templates

### Internal Team Notification (CRITICAL/HIGH)

```
Subject: [URGENT] Calibration Feature Rollback in Progress

Team,

We are executing a rollback of the Projection Calibration System deployment due to [ISSUE DESCRIPTION].

Severity: [CRITICAL/HIGH]
Impact: [USER IMPACT]
Rollback Method: [Database/Code/Full Restore]
Estimated Completion: [TIME]

Current Status:
- [X] Rollback initiated
- [ ] Database restored
- [ ] Code reverted
- [ ] Services restarted
- [ ] Validation complete

Please standby for updates. Do not deploy any changes during rollback window.

Next update in 15 minutes.

[YOUR NAME]
```

### User Communication (If Needed)

```
Subject: System Maintenance - Temporary Feature Removal

Dear Users,

We have temporarily removed the new Projection Calibration feature to ensure system stability and data accuracy.

What this means for you:
- Your player pools and lineups are safe
- Import process continues to work normally
- Smart Score calculations remain accurate
- No action required on your part

We are working on improvements and will re-release the feature soon.

Thank you for your patience.

[TEAM NAME]
```

---

**Rollback Plan Status:** ✅ COMPLETE
**Last Updated:** 2025-11-01
**Rollback Test Status:** [ ] Tested in Staging  [ ] Not Yet Tested
**Approval:** Pending Production Deployment
