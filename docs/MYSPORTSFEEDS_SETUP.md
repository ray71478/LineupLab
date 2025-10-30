# MySportsFeeds API Integration Setup Guide

## Overview

This guide covers the complete setup and configuration of MySportsFeeds v2.1 API integration for the Cortex DFS Lineup Optimizer.

The integration provides:
- Real-time player injury data (PROBABLE, QUESTIONABLE, DOUBTFUL, OUT)
- Vegas Implied Team Total (ITT) for Vegas Context calculations
- Team defensive rankings for matchup adjustments
- Daily player gamelogs for trend analysis

## Getting Started

### Step 1: Sign Up for MySportsFeeds

1. Go to https://www.mysportsfeeds.com/
2. Click "Get Started" or "Sign Up"
3. Create an account with your email
4. Verify your email address
5. Select "Free Tier" or upgrade to Professional plan as needed

### Step 2: Get Your API Token

1. Log in to MySportsFeeds
2. Go to https://www.mysportsfeeds.com/account/api-access
3. Copy your API token (looks like: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
4. Store it securely (never commit to git!)

### Step 3: Configure Environment Variables

1. Copy the example configuration:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your token:
   ```bash
   MYSPORTSFEEDS_TOKEN=your_actual_token_here
   ```

3. Verify other MySportsFeeds settings:
   ```
   SCHEDULER_ENABLED=true              # Enable daily refresh
   SCHEDULER_TIMEZONE=US/Eastern       # Timezone for scheduling
   SCHEDULER_HOUR=5                    # 5:00 AM daily
   SCHEDULER_MINUTE=0
   MAX_RETRIES=3                       # Retry failed API calls
   ```

### Step 4: Verify Installation

Run the verification script:

```bash
python -m backend.scripts.verify_mysportsfeeds_setup
```

Expected output:
```
MySportsFeeds API Setup Verification
====================================
[OK] MYSPORTSFEEDS_TOKEN found in environment
[OK] Token format valid (32+ characters)
[OK] Scheduler configured (US/Eastern, 5:00 AM)
[OK] Database migrations applied
[OK] Connection to api.mysportsfeeds.com successful
[OK] Authentication valid (200 OK response)
[OK] Ready for daily refresh!
```

## Configuration

### Environment Variables

All MySportsFeeds configuration is in the `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `MYSPORTSFEEDS_TOKEN` | (required) | API authentication token |
| `SCHEDULER_ENABLED` | true | Enable/disable daily refresh job |
| `SCHEDULER_TIMEZONE` | US/Eastern | Timezone for scheduling |
| `SCHEDULER_HOUR` | 5 | Hour of day for refresh (0-23) |
| `SCHEDULER_MINUTE` | 0 | Minute of hour for refresh (0-59) |
| `MAX_RETRIES` | 3 | Retry attempts for failed API calls |

### Retry Strategy

The service uses exponential backoff for retries:
- Attempt 1: Immediate
- Attempt 2: Wait 5 seconds
- Attempt 3: Wait 10 seconds
- Attempt 4: Wait 20 seconds (max)

Rate limits (429 status) are respected using the `Retry-After` header.

## API Endpoints

The service fetches from 4 MySportsFeeds endpoints:

### 1. Player Injuries
- **Endpoint**: `/injuries.json?season=current`
- **Frequency**: Daily at configured time
- **Data**: Player name, position, team, injury status
- **Storage**: `player_pools.injury_status`

### 2. Weekly Games (ITT)
- **Endpoint**: `/{season}/week/{week}/games.json`
- **Frequency**: Daily at configured time
- **Data**: Game schedule, scores, Vegas lines (ITT)
- **Storage**: `vegas_lines.implied_team_total`

### 3. Team Defensive Stats
- **Endpoint**: `/{season}/team_stats_totals.json`
- **Frequency**: Daily at configured time
- **Data**: Pass/rush defense rankings by team
- **Storage**: `team_defense_stats.pass_defense_rank, rush_defense_rank`

### 4. Player Gamelogs
- **Endpoint**: `/{season}/date/{date}/player_gamelogs.json`
- **Frequency**: Daily (previous day's games)
- **Data**: Snaps, targets, receptions, yards
- **Storage**: `historical_stats` (backfill for trend calculations)

## Database Schema

Three tables store MySportsFeeds data:

### player_pools (existing table, add column)
```sql
ALTER TABLE player_pools ADD COLUMN injury_status VARCHAR(20);
-- Values: PROBABLE, QUESTIONABLE, DOUBTFUL, OUT, NULL
```

### vegas_lines (existing table, add column)
```sql
ALTER TABLE vegas_lines ADD COLUMN implied_team_total FLOAT;
-- Stores ITT for each team/week
```

### team_defense_stats (new table)
```sql
CREATE TABLE team_defense_stats (
    id SERIAL PRIMARY KEY,
    season INTEGER,
    team_abbr VARCHAR(10),
    pass_defense_rank INTEGER,
    rush_defense_rank INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(season, team_abbr)
);
```

## Running Migrations

Apply all database migrations:

```bash
# Apply migrations
alembic upgrade head

# Verify schema
python -c "
from backend.database import get_db
from sqlalchemy import inspect
db = next(get_db())
inspector = inspect(db.bind)
tables = inspector.get_columns('player_pools')
for col in tables:
    if col['name'] == 'injury_status':
        print('OK: injury_status column exists')
"
```

## Testing the Integration

### Manual Refresh

Trigger a data refresh manually:

```python
from backend.database import SessionLocal
from backend.scheduler.daily_refresh_job import DailyDataRefreshJob
import asyncio

async def test_refresh():
    db = SessionLocal()
    job = DailyDataRefreshJob(db)
    result = await job.execute()
    print(result)

asyncio.run(test_refresh())
```

Expected output:
```json
{
  "success": true,
  "start_time": "2024-10-30T10:15:32",
  "end_time": "2024-10-30T10:15:48",
  "duration_seconds": 16.2,
  "injuries": {
    "fetched": 45,
    "stored": 43,
    "errors": 2
  },
  "games": {
    "fetched": 16,
    "stored": 16,
    "errors": 0
  },
  "team_stats": {
    "fetched": 32,
    "stored": 32,
    "errors": 0
  },
  "gamelogs": {
    "fetched": 450,
    "stored": 445,
    "errors": 5
  }
}
```

### Verify Data in Database

```bash
# Check injuries
psql -U cortex cortex -c "
  SELECT team, COUNT(*) as count,
         array_agg(DISTINCT injury_status) as statuses
  FROM player_pools
  WHERE injury_status IS NOT NULL
  GROUP BY team;
"

# Check ITT values
psql -U cortex cortex -c "
  SELECT team, implied_team_total, updated_at
  FROM vegas_lines
  WHERE week_id = 1
  ORDER BY team;
"

# Check defensive stats
psql -U cortex cortex -c "
  SELECT team_abbr, pass_defense_rank, rush_defense_rank
  FROM team_defense_stats
  WHERE season = 2024;
"

# Check gamelogs
psql -U cortex cortex -c "
  SELECT player_key, week, snaps, targets, receptions
  FROM historical_stats
  WHERE source = 'MYSPORTSFEEDS'
  LIMIT 10;
"
```

## Smart Score Integration

The Smart Score Engine automatically uses MySportsFeeds data:

### Player Availability (Task 4.1)
- Players with `injury_status = 'OUT'` or `'DOUBTFUL'` are excluded
- Logged with reason for exclusion

### W7 - Vegas Context (Task 4.2)
- Uses real `implied_team_total` from `vegas_lines` table
- Falls back to league average if missing
- Formula: `(team_itt / league_avg_itt) × W7`

### W8 - Matchup Adjustment (Task 4.3)
- Uses real defensive ranks from `team_defense_stats`
- Categorizes: top_5 (+1.0), middle (0.0), bottom_5 (-1.0)
- Stored in `player_pools.opponent_rank_category`

### W5 - Trend Adjustment (Task 4.4)
- Uses fresh gamelogs in `historical_stats`
- Snaps, targets, receptions from MySportsFeeds
- Position-specific trend calculation

## Monitoring

### Check Scheduler Status

```bash
# View scheduled jobs
python -c "
from backend.scheduler.scheduler_startup import get_scheduler
scheduler = get_scheduler()
for job in scheduler.get_jobs():
    print(f'Job: {job.id}')
    print(f'  Trigger: {job.trigger}')
    print(f'  Next run: {job.next_run_time}')
"
```

### View Logs

```bash
# Tail application logs
tail -f logs/cortex.log | grep MySportsFeeds

# Show last refresh status
grep "daily data refresh" logs/cortex.log | tail -5
```

### Verify Recent Refresh

```bash
# Check last update time for each data source
psql -U cortex cortex << EOF
SELECT 'injuries' as source, COUNT(*) as count, MAX(updated_at) as last_updated
FROM player_pools WHERE injury_status IS NOT NULL
UNION ALL
SELECT 'vegas_lines', COUNT(*), MAX(updated_at)
FROM vegas_lines
UNION ALL
SELECT 'team_defense_stats', COUNT(*), MAX(updated_at)
FROM team_defense_stats
UNION ALL
SELECT 'gamelogs', COUNT(*), MAX(updated_at)
FROM historical_stats
WHERE source = 'MYSPORTSFEEDS';
EOF
```

## Troubleshooting

### Issue: "MYSPORTSFEEDS_TOKEN not found in environment"

**Solution**:
```bash
# Check .env file exists
ls -la .env

# Verify token is set
grep MYSPORTSFEEDS_TOKEN .env

# Make sure .env is loaded
echo $MYSPORTSFEEDS_TOKEN
```

### Issue: "401 Unauthorized" from API

**Solution**:
```bash
# Verify token is correct
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
token = os.getenv('MYSPORTSFEEDS_TOKEN')
print(f'Token: {token[:10]}...')
print(f'Length: {len(token)}')
"

# Test token with curl
curl -u "TOKEN:MYSPORTSFEEDS" https://api.mysportsfeeds.com/v2.1/pull/nfl/injuries.json?season=current
```

### Issue: "Connection timeout" from API

**Solution**:
```bash
# Check network connectivity
ping api.mysportsfeeds.com

# Increase timeout in environment
HTTPX_TIMEOUT=60
```

### Issue: Scheduler not running

**Solution**:
```bash
# Check if scheduler is enabled
grep SCHEDULER_ENABLED .env

# Verify scheduler is started
tail -20 logs/cortex.log | grep "scheduler"

# Manual trigger to test
python -c "
from backend.scheduler.daily_refresh_job import DailyDataRefreshJob
from backend.database import SessionLocal
import asyncio

async def test():
    db = SessionLocal()
    job = DailyDataRefreshJob(db)
    result = await job.execute()
    print(result)

asyncio.run(test())
"
```

### Issue: Partial data updates

**Solution**:
- System continues when individual API calls fail
- Check logs for which step failed
- Failed data will be retried on next refresh cycle
- Manual refresh always available

## Performance Optimization

### API Call Duration (Target: <30 seconds)

Typical timings:
- Injuries: 2-3 seconds
- Games: 1-2 seconds
- Team stats: 2-3 seconds
- Gamelogs: 8-12 seconds
- Database storage: 3-5 seconds
- **Total**: 16-25 seconds (within 30s target)

### Caching

- Smart Score calculations cached for 5 minutes
- League average defaults cached per week
- Cache invalidated on data refresh

### Database Indexes

Required indexes for performance:
```sql
CREATE INDEX idx_player_pools_injury_status ON player_pools(injury_status);
CREATE INDEX idx_vegas_lines_week_team ON vegas_lines(week_id, team);
CREATE INDEX idx_team_defense_stats_season_team ON team_defense_stats(season, team_abbr);
CREATE INDEX idx_historical_stats_player_week ON historical_stats(player_key, week, season);
```

## Maintenance

### Weekly Tasks
- Monitor log files for errors
- Verify data freshness
- Check for API changes in MySportsFeeds docs

### Monthly Tasks
- Review refresh job success rate
- Update documentation if API changes
- Test manual refresh procedure

### Quarterly Tasks
- Verify API rate limits not exceeded
- Check for deprecated API fields
- Review performance metrics

## API Documentation

For complete MySportsFeeds API documentation:
- https://www.mysportsfeeds.com/docs/api/
- https://www.mysportsfeeds.com/data-dictionary/

## Support

For issues:
1. Check logs: `tail -f logs/cortex.log`
2. Verify token: `grep MYSPORTSFEEDS_TOKEN .env`
3. Test manually: Run verification script
4. Contact MySportsFeeds support if API issue

## Next Steps

1. Complete environment setup (.env)
2. Run migrations: `alembic upgrade head`
3. Verify setup: `python -m backend.scripts.verify_mysportsfeeds_setup`
4. Test manual refresh
5. Monitor first scheduled refresh (5:00 AM)
6. Check Smart Score calculations use real data
