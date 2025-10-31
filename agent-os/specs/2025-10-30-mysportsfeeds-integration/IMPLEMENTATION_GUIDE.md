# MySportsFeeds Integration - Implementation Guide

## Quick Start

This guide provides step-by-step instructions for implementing the MySportsFeeds API integration specification.

## Phase 1: Core Service Implementation

### Step 1.1: Create MySportsFeedsService

**File:** `/Users/raybargas/Documents/Cortex/backend/services/mysportsfeeds_service.py`

**Responsibilities:**
- HTTP API client for MySportsFeeds endpoints
- Response parsing and validation
- Database storage of fetched data
- Error handling and logging

**Key Methods to Implement:**

1. `__init__(session: Session, api_token: str)`
   - Store database session
   - Store API token
   - Initialize httpx.AsyncClient
   - Set up logging

2. `fetch_injuries() -> Optional[List[Dict]]`
   - GET /nfl/injuries.json?season=current
   - Parse players array
   - Extract: player.team, player.position, currentInjury.playingProbability
   - Return: [{"player_key": "...", "injury_status": "OUT|DOUBTFUL|QUESTIONABLE|PROBABLE"}, ...]

3. `fetch_weekly_games(season: str, week: int) -> Optional[List[Dict]]`
   - GET /nfl/{season}/week/{week}/games.json
   - Parse games array
   - Extract: awayTeam.abbr, homeTeam.abbr, implied_team_total (from references)
   - Return: [{"team": "KC", "implied_team_total": 25.5}, ...]

4. `fetch_team_stats(season: str) -> Optional[List[Dict]]`
   - GET /nfl/{season}/team_stats_totals.json
   - Parse teamStatTotals array
   - Extract: team.abbr, stats.pass_defense_rank, stats.rush_defense_rank
   - Return: [{"team": "KC", "pass_def_rank": 5, "rush_def_rank": 12}, ...]

5. `fetch_gamelogs(season: str, date: str, team: str = None) -> Optional[List[Dict]]`
   - GET /nfl/{season}/date/{date}/player_gamelogs.json?team={team}
   - Parse gamelogs array
   - Extract: player.firstName, player.lastName, stats.snaps, stats.targets, stats.receptions
   - Return: [{"player_name": "Patrick Mahomes", "snaps": 45, "targets": 0, ...}, ...]

6. `refresh_all_data() -> Dict[str, bool]`
   - Orchestrate all fetch methods
   - Store results in database
   - Return: {"injuries": True, "games": True, "stats": True, "gamelogs": True}

**Error Handling Strategy:**

```python
def _fetch_with_retry(self, method, *args, max_retries=3):
    """Fetch with exponential backoff retry"""
    for attempt in range(max_retries):
        try:
            return method(*args)
        except httpx.NetworkError as e:
            if attempt < max_retries - 1:
                wait_time = 5 * (2 ** attempt)  # 5s, 10s, 20s
                logger.warning(f"Network error, retry in {wait_time}s: {e}")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Max retries exceeded for {method.__name__}")
                return None
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                retry_after = e.response.headers.get("Retry-After", "30")
                logger.warning(f"Rate limited, waiting {retry_after}s")
                await asyncio.sleep(int(retry_after))
            else:
                logger.error(f"HTTP {e.response.status_code}: {e}")
                return None
```

### Step 1.2: Database Operations

**File:** Same as above (MySportsFeedsService)

**Methods to Implement:**

1. `_update_injury_status(injuries: List[Dict]) -> int`
   - Input: [{"player_key": "mahomes_p", "injury_status": "PROBABLE"}, ...]
   - For each injury:
     - Query player_pools for matching player_key
     - UPDATE injury_status column (or create new row if column doesn't exist)
   - Return: count of updated rows
   - Handle: Graceful degradation if column doesn't exist (log warning, skip)

2. `_store_team_stats(stats: List[Dict]) -> int`
   - Input: [{"team": "KC", "pass_def_rank": 5, "rush_def_rank": 12}, ...]
   - For each stat:
     - UPSERT into team_defense_stats table
     - Use: season (from current week), team_abbr, ranks
   - Return: count of upserted rows

3. `_store_implied_totals(games: List[Dict]) -> int`
   - Input: [{"team": "KC", "implied_team_total": 25.5}, ...]
   - For each game:
     - UPDATE player_pools for team = "KC", week_id = current_week_id
     - Set: implied_team_total = 25.5
   - Return: count of updated rows

4. `_store_gamelogs(gamelogs: List[Dict]) -> int`
   - Input: [{"player_name": "Mahomes, P", "snaps": 45, ...}, ...]
   - For each gamelog:
     - Query historical_stats for matching player_name
     - INSERT new row with week = yesterday's week number, season, stats
   - Handle: Duplicate detection (skip if game already recorded)
   - Return: count of inserted rows

### Step 1.3: Validation & Parsing

**Implement Data Validation:**

```python
def _validate_injury(self, raw_injury: Dict) -> Optional[Dict]:
    """Validate injury record has required fields"""
    required_fields = ["player", "currentInjury"]
    if not all(field in raw_injury for field in required_fields):
        logger.warning(f"Missing fields in injury: {raw_injury}")
        return None

    try:
        player = raw_injury["player"]
        injury = raw_injury["currentInjury"]

        if "playingProbability" not in injury:
            return None

        # Validate playing probability value
        valid_statuses = ["OUT", "DOUBTFUL", "QUESTIONABLE", "PROBABLE"]
        if injury["playingProbability"] not in valid_statuses:
            logger.warning(f"Invalid probability: {injury['playingProbability']}")
            return None

        return {
            "player_key": f"{player['lastName']}_{player['firstName'][:1]}",
            "position": player.get("position"),
            "team": player.get("team", {}).get("abbr"),
            "injury_status": injury["playingProbability"]
        }
    except (KeyError, TypeError) as e:
        logger.error(f"Failed to parse injury: {e}")
        return None
```

## Phase 2: Background Scheduler

### Step 2.1: Create Scheduler Module

**File:** `/Users/raybargas/Documents/Cortex/backend/scripts/scheduler.py`

```python
"""Background scheduler for MySportsFeeds daily refresh."""

import logging
import os
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from backend.main import SessionLocal
from backend.services.mysportsfeeds_service import MySportsFeedsService

logger = logging.getLogger(__name__)

def refresh_mysportsfeeds_data():
    """Daily refresh job for MySportsFeeds data."""
    session = SessionLocal()
    try:
        token = os.getenv("MYSPORTSFEEDS_TOKEN")
        if not token:
            logger.error("MYSPORTSFEEDS_TOKEN not configured")
            return

        service = MySportsFeedsService(session, token)
        result = service.refresh_all_data()

        logger.info(f"MySportsFeeds refresh completed: {result}")
    except Exception as e:
        logger.error(f"MySportsFeeds refresh failed: {e}", exc_info=True)
    finally:
        session.close()

def start_scheduler():
    """Initialize and start background scheduler."""
    scheduler = BackgroundScheduler()

    # Get configuration from environment
    enabled = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"
    timezone = os.getenv("SCHEDULER_TIMEZONE", "US/Eastern")
    hour = int(os.getenv("SCHEDULER_HOUR", "5"))
    minute = int(os.getenv("SCHEDULER_MINUTE", "0"))

    if not enabled:
        logger.info("Scheduler disabled via SCHEDULER_ENABLED")
        return None

    # Add daily job at specified time
    scheduler.add_job(
        refresh_mysportsfeeds_data,
        CronTrigger(hour=hour, minute=minute, timezone=timezone),
        id="mysportsfeeds_refresh",
        name="MySportsFeeds daily refresh",
        replace_existing=True
    )

    scheduler.start()
    logger.info(f"Scheduler started: runs daily at {hour:02d}:{minute:02d} {timezone}")
    return scheduler
```

### Step 2.2: Integrate Scheduler into Main App

**File:** `/Users/raybargas/Documents/Cortex/backend/main.py`

Add after app initialization:
```python
# Import scheduler
from backend.scripts.scheduler import start_scheduler

# Initialize scheduler at app startup
scheduler = start_scheduler()

# Add shutdown hook
@app.on_event("shutdown")
async def shutdown_event():
    """Stop scheduler on app shutdown."""
    if scheduler:
        scheduler.shutdown()
        logger.info("Scheduler shut down")
```

## Phase 3: Database Schema Updates

### Step 3.1: Extend Existing Tables (Option A - Recommended for MVP)

**File:** Database migration (Alembic)

```sql
-- Add injury_status to player_pools
ALTER TABLE player_pools ADD COLUMN injury_status VARCHAR(20);

-- Add implied_team_total to player_pools
ALTER TABLE player_pools ADD COLUMN implied_team_total FLOAT;

-- No change needed for opponent_rank_category (already exists)
```

### Step 3.2: Create New Team Defense Stats Table (Option B - Future)

```sql
CREATE TABLE team_defense_stats (
    id SERIAL PRIMARY KEY,
    season INTEGER NOT NULL,
    team_abbr VARCHAR(10) NOT NULL,
    pass_def_rank INTEGER,
    rush_def_rank INTEGER,
    pass_yards_allowed_rank INTEGER,
    rush_yards_allowed_rank INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(season, team_abbr)
);

CREATE INDEX idx_team_defense_stats_season_team
ON team_defense_stats(season, team_abbr);
```

## Phase 4: Integration with Smart Score

### Step 4.1: Modify SmartScoreService for Fetched Data

**File:** `/Users/raybargas/Documents/Cortex/backend/services/smart_score_service.py`

**W5 Integration (No changes needed):**
- SmartScoreService already queries historical_stats
- MySportsFeeds gamelogs will populate historical_stats
- trend_adjustment will automatically use real data

**W7 Integration:**
```python
def _calculate_w7_vegas_context(self, player, week_id, weight, defaults):
    """Calculate Vegas Context factor using real ITT from MySportsFeeds."""
    # Query team ITT from player_pools or vegas_lines
    itt = self._get_team_implied_total(player.team, week_id)

    if itt is None:
        # Fallback to default if no ITT available
        itt = defaults.get("team_itt_fallback", self.DEFAULT_LEAGUE_AVG_ITT)

    league_avg = self.DEFAULT_LEAGUE_AVG_ITT
    itt_ratio = itt / league_avg if league_avg > 0 else 1.0
    value = itt_ratio * weight

    return FactorResult(
        value=value,
        used_default=itt is None,
        breakdown_info=f"ITT: {itt}/{league_avg} = {itt_ratio:.2f}"
    )

def _get_team_implied_total(self, team, week_id):
    """Get implied team total from MySportsFeeds data."""
    result = self.session.execute(
        text("""
            SELECT implied_team_total FROM player_pools
            WHERE team = :team AND week_id = :week_id
            LIMIT 1
        """),
        {"team": team, "week_id": week_id}
    )
    row = result.scalar()
    return row if row else None
```

**W8 Integration:**
```python
def _calculate_w8_matchup_adjustment(self, player, weight):
    """Calculate Matchup Adjustment using real defensive ranks from MySportsFeeds."""
    # Query opponent defensive rank
    opponent_rank_category = self._get_opponent_rank_category(player.opponent)

    # Map to adjustment value (moved from hardcoded column)
    category_value = {
        "top_5": 1.0,
        "middle": 0.0,
        "bottom_5": -1.0
    }.get(opponent_rank_category, 0.0)

    value = category_value * weight

    return FactorResult(
        value=value,
        breakdown_info=f"Opponent rank: {opponent_rank_category} = {category_value}"
    )

def _get_opponent_rank_category(self, opponent):
    """Get opponent defensive rank category from MySportsFeeds data."""
    result = self.session.execute(
        text("""
            SELECT pass_def_rank, rush_def_rank FROM team_defense_stats
            WHERE team_abbr = :team
            ORDER BY season DESC LIMIT 1
        """),
        {"team": opponent}
    )
    row = result.fetchone()
    if not row:
        return "middle"  # Default

    pass_rank, rush_rank = row
    avg_rank = (pass_rank + rush_rank) / 2 if pass_rank and rush_rank else None

    if avg_rank is None:
        return "middle"
    elif avg_rank <= 10:
        return "top_5"
    elif avg_rank >= 22:
        return "bottom_5"
    else:
        return "middle"
```

### Step 4.2: Update Player Availability Filtering

**Location:** Lineup optimization code

```python
def _is_player_available(self, player_pool_row):
    """Check if player is available for optimization."""
    injury_status = player_pool_row.get("injury_status")

    # Exclude OUT and DOUBTFUL players
    if injury_status in ["OUT", "DOUBTFUL"]:
        return False

    # Include PROBABLE and QUESTIONABLE (personal decision)
    return True
```

## Phase 5: Testing

### Step 5.1: Create Unit Tests

**File:** `/Users/raybargas/Documents/Cortex/tests/unit/test_mysportsfeeds_service.py`

```python
import pytest
from unittest.mock import Mock, AsyncMock, patch
from backend.services.mysportsfeeds_service import MySportsFeedsService

@pytest.fixture
def service(db_session):
    """Create service instance with mocked session."""
    return MySportsFeedsService(db_session, "test_token")

def test_parse_injuries_response(service):
    """Test injury response parsing."""
    response = {
        "players": [
            {
                "player": {
                    "firstName": "Patrick",
                    "lastName": "Mahomes",
                    "position": "QB",
                    "team": {"abbr": "KC"}
                },
                "currentInjury": {
                    "playingProbability": "PROBABLE"
                }
            }
        ]
    }

    result = service._parse_injuries(response)
    assert len(result) == 1
    assert result[0]["injury_status"] == "PROBABLE"
    assert result[0]["team"] == "KC"

def test_handle_rate_limit(service):
    """Test rate limit handling."""
    # Mock httpx response with 429 status
    response = Mock()
    response.status_code = 429
    response.headers = {"Retry-After": "30"}

    # Should log warning and return None
    result = service._handle_http_error(response)
    assert result is None
```

### Step 5.2: Create Integration Tests

**File:** `/Users/raybargas/Documents/Cortex/tests/integration/test_mysportsfeeds_integration.py`

```python
import pytest
from backend.services.mysportsfeeds_service import MySportsFeedsService

@pytest.mark.asyncio
async def test_end_to_end_refresh(db_session):
    """Test full refresh workflow."""
    with patch("httpx.AsyncClient") as mock_client:
        # Mock all API endpoints
        mock_client.get = AsyncMock(return_value=Mock(json=...))

        service = MySportsFeedsService(db_session, "test_token")
        result = await service.refresh_all_data()

        assert result["injuries"] is True
        assert result["games"] is True

        # Verify data was stored in database
        # Query player_pools.injury_status
        # Query implied_team_total
```

## Phase 6: Configuration & Deployment

### Step 6.1: Environment Configuration

**File:** `.env` (add to project)

```ini
# MySportsFeeds API Configuration
MYSPORTSFEEDS_TOKEN=your_actual_token_here
MYSPORTSFEEDS_API_BASE=https://api.mysportsfeeds.com/v2.1

# Scheduler Configuration
SCHEDULER_ENABLED=true
SCHEDULER_TIMEZONE=US/Eastern
SCHEDULER_HOUR=5
SCHEDULER_MINUTE=0

# Feature Flags
MYSPORTSFEEDS_FETCH_INJURIES=true
MYSPORTSFEEDS_FETCH_GAMES=true
MYSPORTSFEEDS_FETCH_STATS=true
MYSPORTSFEEDS_FETCH_GAMELOGS=true
```

**File:** `.env.example` (document for team)

```ini
# MySportsFeeds API Configuration
# Get token from https://www.mysportsfeeds.com/
MYSPORTSFEEDS_TOKEN=your_token_here
MYSPORTSFEEDS_API_BASE=https://api.mysportsfeeds.com/v2.1

# Scheduler Configuration
# Time (EST) when daily refresh runs
SCHEDULER_ENABLED=true
SCHEDULER_TIMEZONE=US/Eastern
SCHEDULER_HOUR=5
SCHEDULER_MINUTE=0

# Feature Flags (enable/disable individual data fetches)
MYSPORTSFEEDS_FETCH_INJURIES=true
MYSPORTSFEEDS_FETCH_GAMES=true
MYSPORTSFEEDS_FETCH_STATS=true
MYSPORTSFEEDS_FETCH_GAMELOGS=true
```

### Step 6.2: Deployment Checklist

- [ ] MySortsFeedsService implemented and tested
- [ ] Scheduler module created and integrated into main.py
- [ ] Database migrations applied (schema updates)
- [ ] SmartScoreService updated to use fetched data (W7, W8)
- [ ] Environment variables configured in production
- [ ] Unit tests passing (>90% coverage)
- [ ] Integration tests passing
- [ ] E2E tests verify Smart Score calculations
- [ ] Logging configured for monitoring
- [ ] Documentation updated with API integration details
- [ ] Manual refresh endpoint tested (optional)
- [ ] Rollback plan documented (if needed)

## Monitoring & Maintenance

### Key Metrics to Monitor

1. **Refresh Success Rate:** % of scheduled jobs that complete without error
2. **API Response Times:** Time to fetch each endpoint (target <30s total)
3. **Data Freshness:** Age of data in database (should be <24h old)
4. **Database Write Performance:** Time to insert/update records
5. **Smart Score Calculation Time:** Impact of additional data lookups

### Logging & Alerting

```python
# Log refresh success
logger.info("MySportsFeeds refresh completed", extra={
    "refresh_duration_seconds": elapsed,
    "injuries_updated": injury_count,
    "games_updated": game_count,
    "stats_updated": stat_count,
    "gamelogs_inserted": gamelog_count
})

# Log failures prominently
logger.error("MySportsFeeds refresh failed", extra={
    "endpoint": "injuries",
    "error": str(e),
    "attempt": attempt_number
})
```

### Maintenance Tasks

1. **Weekly:** Review logs for errors or rate limiting issues
2. **Monthly:** Verify API token is still valid, check documentation for changes
3. **Quarterly:** Analyze data quality (missing fields, unexpected values)
4. **Annually:** Review refresh timing, consider performance optimizations

## Rollback Plan

If issues arise during deployment:

1. **Stop Scheduler:** Set SCHEDULER_ENABLED=false in environment
2. **Revert Code:** Roll back MySportsFeedsService changes
3. **Restore Behavior:** Smart Score will use defaults (no data loss)
4. **Manual Refresh:** Can fetch data manually via endpoint if needed

**No data loss:** All changes are additive; reverting only stops new updates.
