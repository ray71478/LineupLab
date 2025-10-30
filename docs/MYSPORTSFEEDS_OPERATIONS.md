# MySportsFeeds Operations Runbook

## Quick Reference

### Status Checks

```bash
# Check scheduler status
python -c "from backend.scheduler.scheduler_startup import get_scheduler; s = get_scheduler(); print('Running' if s.running else 'Stopped')"

# Check last refresh
tail -20 logs/cortex.log | grep "daily data refresh"

# Check data freshness
psql -U cortex cortex -c "SELECT COUNT(*) FROM player_pools WHERE injury_status IS NOT NULL;"
```

### Manual Operations

```bash
# Trigger immediate refresh
python -m backend.scripts.trigger_refresh

# View scheduler logs
tail -f logs/scheduler.log

# Pause scheduler
python -c "from backend.scheduler.scheduler_startup import get_scheduler; get_scheduler().pause()"

# Resume scheduler
python -c "from backend.scheduler.scheduler_startup import get_scheduler; get_scheduler().resume()"
```

---

## Daily Refresh Job

### Automatic Execution

The system runs a daily data refresh at **5:00 AM EST** (configurable).

**What it does:**
1. Fetches player injuries from MySportsFeeds
2. Updates `player_pools.injury_status`
3. Fetches weekly games and extracts ITT
4. Updates `vegas_lines.implied_team_total`
5. Fetches team defensive rankings
6. Updates `team_defense_stats`
7. Fetches daily player gamelogs
8. Backfills `historical_stats` with fresh game data
9. Logs summary of all operations
10. Handles errors gracefully (continues if individual steps fail)

### Monitoring Successful Refresh

```bash
# Check application logs
grep "daily data refresh" logs/cortex.log

# Expected output:
# INFO: Starting daily data refresh at 2024-10-30 05:00:00
# INFO: Refresh complete: 45 injuries, 16 games, 32 teams, 450 gamelogs
# INFO: Refresh completed in 18.3 seconds
```

### Monitoring Failed Refresh

```bash
# Check for errors
grep "ERROR\|WARNING" logs/cortex.log

# Check specific step failures
grep "Refresh error in" logs/cortex.log

# If visible errors:
tail -100 logs/cortex.log
```

---

## Troubleshooting Guide

### Problem: "Scheduler not running"

**Symptoms:**
- Refresh not happening at scheduled time
- No scheduler logs appearing
- `get_scheduler().running` returns False

**Diagnosis:**
```bash
# Check if scheduler is enabled
grep SCHEDULER_ENABLED .env

# Check for startup errors
grep "scheduler" logs/cortex.log | head -20

# Check if main.py loads scheduler
grep -n "scheduler_startup" backend/main.py
```

**Solution:**
```bash
# 1. Verify configuration
echo "SCHEDULER_ENABLED: $(grep SCHEDULER_ENABLED .env)"
echo "SCHEDULER_HOUR: $(grep SCHEDULER_HOUR .env)"

# 2. Restart application
systemctl restart cortex  # or docker-compose restart

# 3. Verify scheduler started
sleep 5
tail -20 logs/cortex.log | grep scheduler
```

---

### Problem: "API authentication failed (401)"

**Symptoms:**
- Refresh fails with "401 Unauthorized"
- MySportsFeeds API returns 401 in logs

**Diagnosis:**
```bash
# Check token is configured
grep "MYSPORTSFEEDS_TOKEN" .env | head -c 30

# Test token manually
python << 'EOF'
import httpx
import base64
import os

token = os.getenv("MYSPORTSFEEDS_TOKEN")
if not token:
    print("ERROR: Token not in environment")
    exit(1)

auth_string = f"{token}:MYSPORTSFEEDS"
auth_header = f"Basic {base64.b64encode(auth_string.encode()).decode()}"

response = httpx.get(
    "https://api.mysportsfeeds.com/v2.1/pull/nfl/injuries.json?season=current",
    headers={"Authorization": auth_header},
    timeout=10
)
print(f"Status: {response.status_code}")
if response.status_code != 200:
    print(f"Error: {response.text[:200]}")
EOF
```

**Solution:**
```bash
# 1. Get new token from https://www.mysportsfeeds.com/account/api-access
# 2. Update .env
echo "MYSPORTSFEEDS_TOKEN=new_token_here" >> .env

# 3. Restart
systemctl restart cortex

# 4. Test
python -m backend.scripts.verify_mysportsfeeds_setup
```

---

### Problem: "Rate limited (429)"

**Symptoms:**
- Refresh fails with "Rate limit exceeded"
- MySportsFeeds returns 429 status
- Errors include "Retry-After: 60"

**Diagnosis:**
```bash
# Check recent API calls
grep "429\|Rate limit" logs/cortex.log

# Count API calls in last hour
grep "Requesting" logs/cortex.log | \
  grep "$(date --iso-8601=hours)" | wc -l
```

**Solution:**
```bash
# 1. Wait for rate limit window (usually 60-3600 seconds)
sleep 60

# 2. Trigger manual refresh
python -m backend.scripts.trigger_refresh

# 3. If frequent, check for duplicate jobs
python -c "
from backend.scheduler.scheduler_startup import get_scheduler
for job in get_scheduler().get_jobs():
    print(f'{job.id}: {job.trigger}')
"

# 4. If multiple same jobs, remove duplicates
python << 'EOF'
from backend.scheduler.scheduler_startup import get_scheduler
s = get_scheduler()
jobs = s.get_jobs()
seen = {}
for job in jobs:
    if job.id in seen:
        print(f"Removing duplicate: {job.id}")
        s.remove_job(job.id)
    else:
        seen[job.id] = True
EOF
```

---

### Problem: "API timeout"

**Symptoms:**
- Refresh fails with "Connection timeout" or "Read timeout"
- API calls take >30 seconds
- Error mentions "httpx.TimeoutException"

**Diagnosis:**
```bash
# Check API response times in logs
grep "Requesting\|Timeout" logs/cortex.log | tail -20

# Check network connectivity
ping api.mysportsfeeds.com

# Check DNS resolution
nslookup api.mysportsfeeds.com
```

**Solution:**
```bash
# 1. Increase timeout in .env
echo "HTTPX_TIMEOUT=60" >> .env

# 2. Or increase retry wait time
echo "MAX_RETRIES=5" >> .env

# 3. Restart application
systemctl restart cortex

# 4. Monitor next refresh
tail -f logs/cortex.log | grep "Timeout\|Requesting"
```

---

### Problem: "Database connection failed"

**Symptoms:**
- Refresh fails with "Unable to connect to database"
- PostgreSQL connection error in logs

**Diagnosis:**
```bash
# Check database is running
psql -U cortex cortex -c "SELECT 1;"

# Check connection string
echo $DATABASE_URL | head -c 50

# Check database tables exist
psql -U cortex cortex -c "
  \dt player_pools vegas_lines team_defense_stats historical_stats
"
```

**Solution:**
```bash
# 1. Start database if stopped
docker-compose up -d postgres  # or appropriate command

# 2. Verify connection
psql -U cortex cortex -c "SELECT COUNT(*) FROM player_pools;"

# 3. Check migrations are applied
alembic upgrade head

# 4. Restart application
systemctl restart cortex
```

---

### Problem: "Partial data updates (some players missing injury status)"

**Symptoms:**
- Refresh succeeds but only 30/45 players have injury status
- Some teams missing vegas lines
- Gamelogs incomplete

**Diagnosis:**
```bash
# Check which step had errors
grep "Refresh error in\|stored" logs/cortex.log | tail -10

# Count stored vs fetched
grep "Fetched.*stored" logs/cortex.log | tail -5

# Check for database constraint errors
grep "unique constraint\|duplicate" logs/cortex.log
```

**Solution:**
This is normal and expected behavior:
- System continues if some records fail validation
- Next refresh cycle will retry failed records
- Check logs for which records failed validation

To force complete update:
```bash
# 1. Clear potentially stale data (optional)
# psql -U cortex cortex -c "UPDATE player_pools SET injury_status = NULL WHERE updated_at < now() - interval '1 day';"

# 2. Trigger manual refresh
python -m backend.scripts.trigger_refresh

# 3. Monitor output for specific errors
tail -f logs/cortex.log | grep "Error parsing\|Skipping"
```

---

## Scheduler Management

### View Scheduled Jobs

```bash
python << 'EOF'
from backend.scheduler.scheduler_startup import get_scheduler

scheduler = get_scheduler()
for job in scheduler.get_jobs():
    print(f"Job ID: {job.id}")
    print(f"  Trigger: {job.trigger}")
    print(f"  Next run: {job.next_run_time}")
    print(f"  Status: {'Running' if scheduler.running else 'Stopped'}")
    print()
EOF
```

### Pause Scheduler (temporarily stop refresh)

```bash
python << 'EOF'
from backend.scheduler.scheduler_startup import get_scheduler

scheduler = get_scheduler()
scheduler.pause()
print("Scheduler paused. Refresh jobs will not run.")
EOF

# Verify paused
tail logs/cortex.log | grep "Pause"
```

### Resume Scheduler

```bash
python << 'EOF'
from backend.scheduler.scheduler_startup import get_scheduler

scheduler = get_scheduler()
scheduler.resume()
print("Scheduler resumed. Refresh jobs will run normally.")
EOF

# Verify running
python -c "from backend.scheduler.scheduler_startup import get_scheduler; print('Running' if get_scheduler().running else 'Stopped')"
```

### Trigger Manual Refresh

```bash
# Immediate refresh (same as scheduled)
python -m backend.scripts.trigger_refresh

# With verbose output
python -m backend.scripts.trigger_refresh --verbose

# Refresh specific components only
python << 'EOF'
from backend.database import SessionLocal
from backend.scheduler.daily_refresh_job import DailyDataRefreshJob
import asyncio

async def refresh_injuries_only():
    db = SessionLocal()
    service = MySportsFeedsService(db)
    injuries = await service.fetch_current_week_injuries()
    print(f"Fetched {len(injuries)} injuries")

asyncio.run(refresh_injuries_only())
EOF
```

---

## Data Verification

### Check Data Freshness

```bash
# Injuries updated in last hour
psql -U cortex cortex -c "
  SELECT COUNT(*) as injury_count, MAX(updated_at) as last_updated
  FROM player_pools
  WHERE injury_status IS NOT NULL
    AND updated_at > now() - interval '1 hour';
"

# Vegas lines updated in last hour
psql -U cortex cortex -c "
  SELECT COUNT(*) as line_count, MAX(updated_at) as last_updated
  FROM vegas_lines
  WHERE implied_team_total IS NOT NULL
    AND updated_at > now() - interval '1 hour';
"

# Team stats updated in last hour
psql -U cortex cortex -c "
  SELECT COUNT(*) as stat_count, MAX(updated_at) as last_updated
  FROM team_defense_stats
  WHERE updated_at > now() - interval '1 hour';
"

# Gamelogs updated in last hour
psql -U cortex cortex -c "
  SELECT COUNT(*) as gamelog_count, MAX(updated_at) as last_updated
  FROM historical_stats
  WHERE source = 'MYSPORTSFEEDS'
    AND updated_at > now() - interval '1 hour';
"
```

### Verify Smart Score Uses Real Data

```bash
# Check injuries are being excluded
psql -U cortex cortex -c "
  SELECT COUNT(*) as excluded_count
  FROM player_pools
  WHERE injury_status IN ('OUT', 'DOUBTFUL');
"
# These players should NOT appear in Smart Score results

# Check ITT values are being used
python << 'EOF'
from backend.database import SessionLocal
from backend.services.smart_score_service import SmartScoreService
from backend.schemas.smart_score_schemas import WeightProfile, ScoreConfig

db = SessionLocal()
service = SmartScoreService(db)

# Get scores for week 1
weights = WeightProfile(W1=0.5, W2=0.3, W3=0.2, W4=0.4, W5=0.3, W6=0.0, W7=0.3, W8=0.3)
config = ScoreConfig()
results = service.calculate_for_all_players(1, weights, config)

print(f"Calculated scores for {len(results)} players")
for r in results[:3]:
    print(f"  {r.name}: W7={r.score_breakdown.W7_value:.2f}")
EOF
```

---

## Performance Monitoring

### Check Refresh Duration

```bash
# Extract refresh durations
grep "Refresh completed in" logs/cortex.log | tail -7 | awk '{print $NF}'

# Average duration (requires awk)
grep "Refresh completed in" logs/cortex.log | \
  awk '{sum += $(NF-1); count++} END {print "Average: " sum/count " seconds"}'
```

### Target Performance

- Injuries: 2-3 seconds
- Games: 1-2 seconds
- Team stats: 2-3 seconds
- Gamelogs: 8-12 seconds
- Database storage: 3-5 seconds
- **Total: <30 seconds** (acceptable range: 16-25 seconds)

If exceeding 30 seconds:
1. Check network latency to MySportsFeeds API
2. Check database performance (CPU/disk I/O)
3. Reduce timeout value to fail faster on slow calls

---

## Log Analysis

### Useful Log Patterns

```bash
# Show all MySportsFeeds operations
grep "MySports\|refresh\|Injury\|games\|gamelogs" logs/cortex.log

# Show only errors
grep "ERROR" logs/cortex.log | grep -i "mysports\|refresh"

# Show timing information
grep "start\|completed" logs/cortex.log

# Follow real-time logs
tail -f logs/cortex.log | grep --line-buffered "refresh\|error"

# Summary of last refresh
grep "Starting daily\|Refresh complete" logs/cortex.log | tail -2
```

### Log Rotation

Logs are automatically rotated (usually daily). To clear old logs:

```bash
# Remove logs older than 30 days
find logs/ -name "*.log" -mtime +30 -delete

# Archive instead of delete
find logs/ -name "*.log" -mtime +7 -exec gzip {} \;
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] All tests passing: `pytest tests/ -v`
- [ ] Database migrations tested: `alembic current`
- [ ] Token in .env: `grep MYSPORTSFEEDS_TOKEN .env`
- [ ] Scheduler configuration verified
- [ ] API connectivity tested
- [ ] Backups created

### Deployment Steps

1. Stop application: `systemctl stop cortex`
2. Apply migrations: `alembic upgrade head`
3. Verify schema: `psql -U cortex cortex -c "\dt"`
4. Start application: `systemctl start cortex`
5. Verify startup: `tail -20 logs/cortex.log`

### Post-Deployment

- [ ] Application is running
- [ ] Scheduler is running
- [ ] First refresh completes successfully
- [ ] Data appears in database
- [ ] Smart Score calculations use real data
- [ ] No errors in logs
- [ ] Performance within targets

---

## Emergency Procedures

### Stop All Refresh Operations

```bash
# Pause scheduler (jobs won't run)
python << 'EOF'
from backend.scheduler.scheduler_startup import get_scheduler
get_scheduler().pause()
print("All refresh operations paused")
EOF

# To resume
python << 'EOF'
from backend.scheduler.scheduler_startup import get_scheduler
get_scheduler().resume()
print("All refresh operations resumed")
EOF
```

### Rollback Bad Data

```bash
# If corrupted injury status
UPDATE player_pools SET injury_status = NULL WHERE week_id = ?;

# If corrupted ITT
UPDATE vegas_lines SET implied_team_total = NULL WHERE week_id = ?;

# Then trigger manual refresh
python -m backend.scripts.trigger_refresh
```

### Disable MySportsFeeds (use defaults only)

```bash
# Set scheduler to disabled
sed -i 's/SCHEDULER_ENABLED=true/SCHEDULER_ENABLED=false/' .env

# Smart Score will fall back to defaults
# - Injuries: treat all as available (PROBABLE)
# - ITT: use league average (22.5)
# - Defense: use middle category (0.0)
# - Trends: use existing historical data
```

---

## Contact & Support

For issues:
1. Check this runbook
2. View logs: `tail -100 logs/cortex.log`
3. Test manually: `python -m backend.scripts.trigger_refresh --verbose`
4. Contact MySportsFeeds support: https://www.mysportsfeeds.com/contact/

For database issues:
- PostgreSQL logs: `journalctl -u postgres -n 50`
- Connection string: `echo $DATABASE_URL`
