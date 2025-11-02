# Projection Calibration System - Monitoring Plan
**Task Group 12: Production Deployment**
**Feature:** Smart Score Engine Enhancement - Projection Calibration System
**Date:** 2025-11-01

---

## Monitoring Overview

### Monitoring Objectives

1. **System Health:** Ensure calibration feature doesn't degrade application performance
2. **Data Integrity:** Verify calibration applies correctly to all players
3. **User Experience:** Track user engagement and satisfaction with calibration
4. **Business Impact:** Measure lineup quality and projection accuracy improvements
5. **Error Detection:** Identify and alert on calibration-related errors

### Monitoring Timeline

- **First 24 Hours:** Intensive monitoring every 15 minutes
- **Days 2-7:** Regular monitoring every 1 hour
- **Week 2+:** Standard monitoring (daily health checks)

---

## Technical Monitoring

### 12.6.1 Application Log Monitoring

#### Critical Log Patterns to Monitor

**Error Patterns:**
```bash
# Monitor calibration-related errors in real-time
tail -f /var/log/cortex/application.log | grep -iE "calibration.*(error|exception|failed)"

# Count error frequency (run every 15 min for first 24 hours)
grep -i "calibration.*error" /var/log/cortex/application.log | wc -l

# Alert if > 10 errors per hour
```

**Success Patterns:**
```bash
# Monitor successful calibration applications
grep -i "calibration.*applied successfully" /var/log/cortex/application.log | tail -20

# Track calibration application rate
grep -i "calibration applied to" /var/log/cortex/application.log | \
  awk '{print $1, $2}' | uniq -c
```

**Performance Patterns:**
```bash
# Monitor import time with calibration
grep -i "import completed in" /var/log/cortex/application.log | \
  awk '{print $(NF-1)}' | \
  awk '{sum+=$1; count++} END {print "Avg:", sum/count, "seconds"}'

# Alert if average > 5% increase from baseline
# Baseline: ~2.0 seconds for 500 players
# Alert threshold: > 2.1 seconds
```

#### Log Monitoring Queries

**PostgreSQL Query Log:**
```sql
-- Monitor slow calibration queries (run every hour)
SELECT query, calls, total_time, mean_time, max_time
FROM pg_stat_statements
WHERE query LIKE '%projection_calibration%'
   OR query LIKE '%calibration_applied%'
ORDER BY mean_time DESC
LIMIT 10;

-- Alert if mean_time > 100ms
```

**Database Error Log:**
```bash
# Monitor database constraint violations
tail -f /var/log/postgresql/postgresql.log | \
  grep -iE "constraint|duplicate|foreign key"

# Check for calibration-specific errors
grep -i "projection_calibration" /var/log/postgresql/postgresql.log | \
  grep -iE "error|constraint"
```

#### Log Monitoring Alerts

| Alert Condition | Threshold | Severity | Action |
|-----------------|-----------|----------|--------|
| Calibration errors | > 10/hour | CRITICAL | Investigate immediately, consider rollback |
| API endpoint errors (500) | > 5/hour | HIGH | Review stack traces, hotfix if needed |
| Validation errors (400) | > 20/hour | MEDIUM | Review user input patterns, improve validation |
| Slow queries | mean_time > 100ms | MEDIUM | Optimize queries, add indexes |
| Import time increase | > 5% baseline | HIGH | Review calibration performance |
| Database constraint violations | > 0 | CRITICAL | Investigate data integrity issue |

---

### 12.6.2 API Endpoint Performance

#### Endpoint Response Time Monitoring

**Calibration API Endpoints:**
```bash
# Monitor /api/calibration/{week_id} response time
# Use application performance monitoring (APM) tool or custom script

# Example: Parse nginx access log
tail -f /var/log/nginx/access.log | \
  grep "/api/calibration" | \
  awk '{print $7, $NF}' | \
  column -t

# Calculate p50, p95, p99 percentiles every hour
tail -10000 /var/log/nginx/access.log | \
  grep "/api/calibration" | \
  awk '{print $NF}' | \
  sort -n | \
  awk '{
    values[NR] = $1
  }
  END {
    print "p50:", values[int(NR*0.5)]
    print "p95:", values[int(NR*0.95)]
    print "p99:", values[int(NR*0.99)]
  }'
```

**Performance Baselines:**
| Endpoint | Baseline (p95) | Alert Threshold | Max Acceptable |
|----------|----------------|-----------------|----------------|
| GET /api/calibration/{week_id} | < 50ms | > 100ms | 200ms |
| POST /api/calibration/{week_id} | < 100ms | > 200ms | 500ms |
| POST /api/calibration/{week_id}/batch | < 200ms | > 400ms | 1000ms |
| GET /api/calibration/{week_id}/status | < 30ms | > 75ms | 150ms |
| POST /api/calibration/{week_id}/reset | < 150ms | > 300ms | 600ms |

**Monitoring Script:**
```bash
#!/bin/bash
# monitor_calibration_api.sh
# Run every 5 minutes for first 24 hours

WEEK_ID=$(curl -s http://localhost:8000/api/weeks/current | jq '.id')

echo "=== Calibration API Health Check $(date) ==="

# Test GET calibration
START=$(date +%s%N)
curl -s -o /dev/null -w "%{http_code} %{time_total}s" \
  http://localhost:8000/api/calibration/$WEEK_ID
END=$(date +%s%N)
echo "GET /api/calibration/$WEEK_ID: $(( (END - START) / 1000000 ))ms"

# Test GET status
START=$(date +%s%N)
curl -s -o /dev/null -w "%{http_code} %{time_total}s" \
  http://localhost:8000/api/calibration/$WEEK_ID/status
END=$(date +%s%N)
echo "GET /api/calibration/$WEEK_ID/status: $(( (END - START) / 1000000 ))ms"

echo "======================================"
```

#### API Error Rate Monitoring

```bash
# Track 4xx and 5xx error rates
grep "/api/calibration" /var/log/nginx/access.log | \
  awk '{print $9}' | \
  sort | uniq -c | sort -rn

# Calculate error rate percentage
TOTAL=$(grep "/api/calibration" /var/log/nginx/access.log | wc -l)
ERRORS=$(grep "/api/calibration" /var/log/nginx/access.log | grep -E " (4[0-9]{2}|5[0-9]{2}) " | wc -l)
ERROR_RATE=$(echo "scale=2; $ERRORS / $TOTAL * 100" | bc)
echo "API Error Rate: $ERROR_RATE%"

# Alert if error rate > 5%
```

---

### 12.6.3 Database Query Performance

#### Query Performance Baselines

```sql
-- Create baseline metrics before monitoring
CREATE TABLE IF NOT EXISTS calibration_query_baselines (
    query_name VARCHAR(100),
    baseline_mean_time_ms DECIMAL(10,2),
    baseline_p95_time_ms DECIMAL(10,2),
    baseline_calls_per_hour INT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Record baselines (run after deployment stabilizes)
INSERT INTO calibration_query_baselines (query_name, baseline_mean_time_ms, baseline_p95_time_ms, baseline_calls_per_hour)
VALUES
    ('get_calibration_for_week', 5.0, 10.0, 100),
    ('get_player_pools_with_calibration', 50.0, 100.0, 500),
    ('apply_calibration_during_import', 200.0, 400.0, 10),
    ('smart_score_with_calibration', 150.0, 300.0, 200);
```

#### Query Monitoring Queries

```sql
-- Monitor calibration query performance (run every hour)
SELECT
    substring(query from 1 for 60) as query_snippet,
    calls,
    total_time,
    mean_time,
    max_time,
    stddev_time
FROM pg_stat_statements
WHERE query LIKE '%projection_calibration%'
   OR query LIKE '%calibration_applied%'
   OR query LIKE '%projection_%_calibrated%'
ORDER BY mean_time DESC
LIMIT 20;

-- Alert if any query mean_time > 2x baseline
```

```sql
-- Monitor table bloat for calibration tables
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) -
                   pg_relation_size(schemaname||'.'||tablename)) as index_size
FROM pg_tables
WHERE tablename IN ('projection_calibration', 'player_pools')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

```sql
-- Monitor index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE tablename IN ('projection_calibration', 'player_pools')
ORDER BY idx_scan DESC;

-- Alert if calibration indexes have 0 scans (not being used)
```

#### Database Connection Monitoring

```sql
-- Monitor active database connections (run every 5 min)
SELECT
    COUNT(*) FILTER (WHERE state = 'active') as active_connections,
    COUNT(*) FILTER (WHERE state = 'idle') as idle_connections,
    COUNT(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction,
    COUNT(*) as total_connections
FROM pg_stat_activity
WHERE datname = 'cortex';

-- Alert if active_connections > 50 or idle_in_transaction > 10
```

---

### 12.6.4 System Resource Monitoring

#### CPU and Memory Usage

```bash
# Monitor application CPU usage
ps aux | grep -E "(uvicorn|gunicorn)" | awk '{sum+=$3} END {print "CPU:", sum "%"}'

# Monitor application memory usage
ps aux | grep -E "(uvicorn|gunicorn)" | awk '{sum+=$4} END {print "Memory:", sum "%"}'

# Alert if CPU > 80% or Memory > 85% sustained for 5 minutes
```

```bash
# Monitor database CPU and memory
ps aux | grep postgres | awk '{cpu+=$3; mem+=$4} END {print "PostgreSQL - CPU:", cpu "%, Memory:", mem "%"}'

# Alert if CPU > 70% or Memory > 90%
```

#### Disk I/O Monitoring

```bash
# Monitor disk I/O for database partition
iostat -x 5 | grep -A1 "Device"

# Alert if %util > 90% (disk saturated)
```

#### Application Resource Limits

```bash
# Check application file descriptor usage
lsof -p $(pgrep -f uvicorn) | wc -l

# Get file descriptor limit
ulimit -n

# Alert if usage > 80% of limit
```

---

## Data Integrity Monitoring

### 12.6.5 Calibration Application Verification

#### Real-Time Calibration Checks

```sql
-- Monitor calibration application rate during imports (run every import)
SELECT
    position,
    COUNT(*) as total_players,
    COUNT(CASE WHEN calibration_applied = true THEN 1 END) as calibrated_count,
    ROUND(COUNT(CASE WHEN calibration_applied = true THEN 1 END)::NUMERIC / COUNT(*) * 100, 2) as calibrated_percentage
FROM player_pools
WHERE week_id = (SELECT id FROM weeks WHERE is_active = true)
GROUP BY position
ORDER BY position;

-- Alert if any position has calibrated_percentage < 95% (when calibration active)
```

```sql
-- Verify calibrated values match formula (spot check)
SELECT
    name,
    position,
    projection_median_original as original,
    projection_median_calibrated as calibrated,
    ROUND((projection_median_calibrated / NULLIF(projection_median_original, 0) - 1) * 100, 2) as actual_adjustment,
    pc.median_adjustment_percent as expected_adjustment,
    CASE
        WHEN ABS(ROUND((projection_median_calibrated / NULLIF(projection_median_original, 0) - 1) * 100, 2) - pc.median_adjustment_percent) < 0.1
        THEN 'OK'
        ELSE 'MISMATCH'
    END as validation_status
FROM player_pools pp
JOIN weeks w ON pp.week_id = w.id
JOIN projection_calibration pc ON w.id = pc.week_id AND pp.position = pc.position
WHERE w.is_active = true
AND pp.projection_median_original IS NOT NULL
AND pp.calibration_applied = true
LIMIT 20;

-- Alert if any validation_status = 'MISMATCH'
```

#### Data Consistency Checks

```sql
-- Check for NULL calibrated values when calibration_applied = true (data integrity issue)
SELECT
    COUNT(*) as integrity_violations
FROM player_pools
WHERE calibration_applied = true
AND (projection_floor_calibrated IS NULL
  OR projection_median_calibrated IS NULL
  OR projection_ceiling_calibrated IS NULL);

-- Alert if integrity_violations > 0 (CRITICAL)
```

```sql
-- Check for orphaned calibration records (weeks that don't exist)
SELECT
    pc.id,
    pc.week_id,
    pc.position
FROM projection_calibration pc
LEFT JOIN weeks w ON pc.week_id = w.id
WHERE w.id IS NULL;

-- Alert if any orphaned records found (should not happen due to FK constraint)
```

```sql
-- Check for duplicate calibration records (should be prevented by unique constraint)
SELECT
    week_id,
    position,
    COUNT(*) as duplicate_count
FROM projection_calibration
GROUP BY week_id, position
HAVING COUNT(*) > 1;

-- Alert if duplicate_count > 0 (CRITICAL - constraint failure)
```

---

## User Experience Monitoring

### 12.6.6 User Engagement Tracking

#### Calibration Feature Usage

```sql
-- Track calibration admin interface access (requires application logging)
-- This would typically be tracked in an events table or APM tool

-- Example query if events logged:
SELECT
    DATE(created_at) as date,
    COUNT(*) as admin_accesses,
    COUNT(DISTINCT user_id) as unique_users
FROM user_events
WHERE event_type = 'calibration_admin_opened'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

```sql
-- Track calibration factor updates
SELECT
    DATE(updated_at) as date,
    position,
    COUNT(*) as update_count
FROM projection_calibration
WHERE updated_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(updated_at), position
ORDER BY date DESC, position;
```

```sql
-- Track calibration activation/deactivation
SELECT
    week_id,
    position,
    is_active,
    updated_at
FROM projection_calibration
WHERE updated_at > NOW() - INTERVAL '7 days'
ORDER BY updated_at DESC;
```

#### User Feedback Collection

**Feedback Tracking Template:**
```markdown
## Calibration User Feedback Log

### Date: [DATE]
**User:** [USER_ID/NAME]
**Feedback Type:** [ ] Bug  [ ] Confusion  [ ] Suggestion  [ ] Positive

**Feedback:**
[USER FEEDBACK TEXT]

**Context:**
- Week: [WEEK NUMBER]
- Feature Area: [ ] Admin Interface  [ ] Dual-Value Display  [ ] Status Chip  [ ] Calibration Effect
- Severity: [ ] Low  [ ] Medium  [ ] High  [ ] Critical

**Action Taken:**
[RESPONSE/FIX]

**Follow-up Required:** [ ] Yes  [ ] No
```

---

## Business Metrics Monitoring

### 12.6.7 Lineup Quality Metrics

#### Calibration Effectiveness Tracking

```sql
-- Compare lineup scores with/without calibration (requires historical data)
-- This query would need to be adapted based on actual lineup tracking schema

WITH calibrated_lineups AS (
    SELECT
        AVG(actual_points) as avg_points_calibrated,
        AVG(projected_points) as avg_projected_calibrated,
        COUNT(*) as lineup_count_calibrated
    FROM lineups
    WHERE week_id IN (
        SELECT DISTINCT week_id
        FROM player_pools
        WHERE calibration_applied = true
    )
),
non_calibrated_lineups AS (
    SELECT
        AVG(actual_points) as avg_points_non_calibrated,
        AVG(projected_points) as avg_projected_non_calibrated,
        COUNT(*) as lineup_count_non_calibrated
    FROM lineups
    WHERE week_id IN (
        SELECT DISTINCT week_id
        FROM player_pools
        WHERE calibration_applied = false
    )
)
SELECT
    c.avg_points_calibrated,
    n.avg_points_non_calibrated,
    ROUND((c.avg_points_calibrated / n.avg_points_non_calibrated - 1) * 100, 2) as improvement_percentage
FROM calibrated_lineups c, non_calibrated_lineups n;

-- Target: 5-10% improvement (spec line 419)
```

#### Projection Accuracy Tracking

```sql
-- Calculate projection accuracy metrics (RMSE - Root Mean Square Error)
-- Requires actual points data after games complete

WITH projection_errors AS (
    SELECT
        pp.position,
        pp.calibration_applied,
        POWER(pp.projection_median_calibrated - p.actual_points, 2) as squared_error_calibrated,
        POWER(pp.projection_median_original - p.actual_points, 2) as squared_error_original
    FROM player_pools pp
    JOIN players p ON pp.player_id = p.id
    WHERE pp.week_id = [COMPLETED_WEEK_ID]
    AND p.actual_points IS NOT NULL
)
SELECT
    position,
    SQRT(AVG(squared_error_calibrated)) as rmse_calibrated,
    SQRT(AVG(squared_error_original)) as rmse_original,
    ROUND((1 - SQRT(AVG(squared_error_calibrated)) / SQRT(AVG(squared_error_original))) * 100, 2) as improvement_percentage
FROM projection_errors
WHERE calibration_applied = true
GROUP BY position;

-- Target: 8-12% RMSE reduction (spec line 423)
```

#### Projection Range Compression

```sql
-- Measure floor/ceiling range compression for RB/TE/WR
WITH range_metrics AS (
    SELECT
        position,
        calibration_applied,
        AVG(projection_ceiling_calibrated - projection_floor_calibrated) as avg_range_calibrated,
        AVG(projection_ceiling_original - projection_floor_original) as avg_range_original
    FROM player_pools
    WHERE week_id = (SELECT id FROM weeks WHERE is_active = true)
    AND position IN ('RB', 'TE', 'WR')
    GROUP BY position, calibration_applied
)
SELECT
    position,
    avg_range_original,
    avg_range_calibrated,
    ROUND((1 - avg_range_calibrated / avg_range_original) * 100, 2) as compression_percentage
FROM range_metrics
WHERE calibration_applied = true;

-- Target: 15-25% compression for RB/TE/WR (spec line 420)
```

---

## Monitoring Dashboards

### 12.6.8 Recommended Dashboard Metrics

#### Dashboard 1: Calibration Health Overview

**Metrics to Display:**
- Calibration Active Status (Current Week)
- Positions Configured (6/6 expected)
- Calibration Application Rate (% of players calibrated)
- API Error Rate (last 24 hours)
- Import Time Trend (with/without calibration comparison)
- Database Query Performance (p95 response times)

**Refresh Rate:** Every 5 minutes

#### Dashboard 2: Data Integrity Monitor

**Metrics to Display:**
- Data Integrity Violations (should be 0)
- Calibration Formula Accuracy (spot check results)
- NULL Value Count (calibrated columns)
- Duplicate Calibration Records (should be 0)
- Foreign Key Constraint Violations (should be 0)

**Refresh Rate:** Every 15 minutes

#### Dashboard 3: User Engagement

**Metrics to Display:**
- Admin Interface Access Count (daily)
- Calibration Factor Update Frequency
- Active/Inactive Toggle Events
- User Feedback Sentiment (positive/neutral/negative)
- Calibration Status Chip Clicks

**Refresh Rate:** Hourly

#### Dashboard 4: Business Impact

**Metrics to Display:**
- Lineup Quality Improvement (%)
- Projection Accuracy (RMSE before/after)
- Range Compression (RB/TE/WR)
- User Adoption Rate (% weeks with calibration active)
- Smart Score Distribution Quality

**Refresh Rate:** Daily (after week completion)

---

## Alert Configuration

### 12.6.9 Alert Rules and Escalation

#### CRITICAL Alerts (Page On-Call Engineer)

| Alert | Condition | Action |
|-------|-----------|--------|
| Database Corruption | integrity_violations > 0 | Immediate investigation, consider rollback |
| API Error Spike | error_rate > 25% | Immediate investigation, rollback if needed |
| Import Failure | import_failure_count > 0 | Check logs, verify data integrity |
| Calibration Formula Mismatch | validation_status = 'MISMATCH' > 10 records | Investigate calculation bug |
| Database Down | connection_failed | Restore database service immediately |

**Escalation:** Notify Senior Engineer and DevOps Lead within 5 minutes

#### HIGH Alerts (Notify Team Channel)

| Alert | Condition | Action |
|-------|-----------|--------|
| Performance Degradation | response_time > 2x baseline | Investigate slow queries, optimize |
| Import Time Increase | import_time > 5% baseline | Review calibration performance |
| High Error Rate | error_rate > 5% but < 25% | Review logs, prepare hotfix |
| Slow Queries | mean_time > 100ms | Optimize query, add index if needed |
| Resource Saturation | cpu > 80% or memory > 85% | Scale resources or optimize code |

**Escalation:** Review within 1 hour, escalate if unresolved in 2 hours

#### MEDIUM Alerts (Log and Review)

| Alert | Condition | Action |
|-------|-----------|--------|
| Moderate Error Rate | error_rate > 1% but < 5% | Monitor trend, review in daily standup |
| Calibration Partial Application | calibrated_percentage < 95% | Investigate missing positions |
| User Feedback (Negative) | negative_feedback_count > 5/day | Review usability, plan improvements |
| API Response Slow | response_time > 1.5x baseline | Monitor trend, optimize if persistent |

**Escalation:** Review in daily standup, plan fix for next sprint

---

## Monitoring Checklist

### First 24 Hours Post-Deployment

- [ ] **Hour 1:** Intensive monitoring every 15 minutes
  - [ ] Check application logs for errors
  - [ ] Monitor API response times
  - [ ] Verify database query performance
  - [ ] Test import with calibration
  - [ ] Check calibration application rate

- [ ] **Hour 6:** First comprehensive health check
  - [ ] Review all alert thresholds
  - [ ] Verify no CRITICAL or HIGH alerts triggered
  - [ ] Check data integrity (run all validation queries)
  - [ ] Test user workflows (import, Smart Score, lineup generation)
  - [ ] Review user feedback (if any)

- [ ] **Hour 12:** Mid-day assessment
  - [ ] Analyze error trends
  - [ ] Review performance metrics vs baselines
  - [ ] Check system resource usage
  - [ ] Verify monitoring dashboards accurate
  - [ ] Document any issues encountered

- [ ] **Hour 24:** End of Day 1 review
  - [ ] Comprehensive system health check
  - [ ] Review all monitoring data collected
  - [ ] Calculate performance vs spec requirements
  - [ ] Document deployment success or issues
  - [ ] Plan next steps (continued monitoring or rollback)

### Days 2-7: Regular Monitoring

- [ ] **Daily Health Checks** (run once per day)
  - [ ] Review error logs (no CRITICAL issues)
  - [ ] Check API performance (within baselines)
  - [ ] Verify data integrity (all validation queries)
  - [ ] Monitor user engagement metrics
  - [ ] Review user feedback

- [ ] **End of Week Review** (Day 7)
  - [ ] Calculate weekly metrics:
    - Total imports with calibration
    - Average calibration application rate
    - API error rate trend
    - Performance vs baselines
    - User adoption rate
  - [ ] Business impact assessment:
    - Lineup quality improvement (if data available)
    - Projection accuracy (after week completes)
    - User feedback sentiment
  - [ ] Decision: Continue monitoring or move to standard schedule

### Week 2+: Standard Monitoring

- [ ] **Daily:** Review monitoring dashboards
- [ ] **Weekly:** Run comprehensive health checks
- [ ] **Monthly:** Business impact analysis
- [ ] **Quarterly:** Performance optimization review

---

**Monitoring Plan Status:** ✅ COMPLETE
**Last Updated:** 2025-11-01
**Monitoring Tools Required:**
- Application logging (existing)
- Database monitoring (PostgreSQL pg_stat_statements)
- APM tool (optional but recommended)
- Custom dashboard (Grafana, Datadog, or similar)
- Alert system (PagerDuty, Slack, email)
