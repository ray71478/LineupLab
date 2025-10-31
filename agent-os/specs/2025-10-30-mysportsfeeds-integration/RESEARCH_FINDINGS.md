# MySportsFeeds Integration - Research Findings

## Summary

Created comprehensive specification for MySportsFeeds API integration to enhance Smart Score Engine with real-time external data. The specification was developed based on:

1. Analysis of existing backend services and architectural patterns
2. Review of database schema and table structures
3. Understanding of Smart Score calculation requirements
4. Examination of current technology stack and dependencies

## Existing Architecture Analysis

### Backend Technology Stack

**Framework & HTTP:**
- FastAPI (web framework) - `/Users/raybargas/Documents/Cortex/backend/main.py`
- httpx (async HTTP client) - already in requirements.txt
- python-dotenv (environment configuration) - already in requirements.txt

**Database:**
- PostgreSQL (primary) or SQLite (testing)
- SQLAlchemy ORM for database operations
- Session-based queries using sqlalchemy.text() for raw SQL

**Core Tables Analyzed:**

```
player_pools
├── id (INTEGER PRIMARY KEY)
├── week_id (FK to weeks)
├── player_key (VARCHAR 255)
├── name, team, position, salary
├── projection, ownership, ceiling, floor
├── source, projection_source
├── opponent_rank_category (VARCHAR 20) - REUSABLE for W8
├── created_at, updated_at
└── UNIQUE(week_id, player_key)

historical_stats
├── id (INTEGER PRIMARY KEY)
├── week_id (FK to weeks)
├── player_name, team, position, week
├── opponent, snaps, snap_pct
├── rush_attempts, rush_yards, rush_tds
├── targets, target_share, receptions, rec_yards, rec_tds
├── total_tds, touches, actual_points
├── salary, created_at, updated_at
└── REUSABLE for W5 trend calculations

weeks
├── id (INTEGER PRIMARY KEY)
├── season, week_number
├── status (upcoming/active/completed)
├── nfl_slate_date, is_locked
└── created_at, updated_at

week_metadata
├── week_id (FK to weeks)
├── season, week_number
├── nfl_slate_date, kickoff_time
├── import_status (pending/imported/error)
├── import_count, import_timestamp
└── USEFUL for context (season, week_number)

nfl_schedule (referenced by NFLScheduleService)
├── season, week, slate_date, kickoff_time
├── game_count, is_playoff
└── USEFUL for determining current week
```

### Reusable Service Patterns

**1. NFLScheduleService** (`/Users/raybargas/Documents/Cortex/backend/services/nfl_schedule_service.py`)

Pattern for fetching external data and storing in database:
```python
def __init__(self, session: Session):
    """Initialize with database session"""
    self.session = session

def get_nfl_schedule(self, year: int) -> List[Dict[str, Any]]:
    """Query and return structured data"""
    result = self.session.execute(
        text("""SELECT ... FROM nfl_schedule WHERE season = :season"""),
        {"season": year}
    )
    # Parse results, convert data types, return list of dicts
```

**Key Takeaways:**
- Use `sqlalchemy.text()` for raw SQL queries
- Session passed to constructor
- Return data as List[Dict] or single Dict
- Comprehensive logging with logger.info() and logger.warning()
- Handle None/empty results gracefully

**2. HistoricalInsightsService** (`/Users/raybargas/Documents/Cortex/backend/services/historical_insights_service.py`)

Pattern for reading from historical_stats table:
```python
def get_player_consistency(
    self, player_key: str, season: int, weeks_back: int = 6
) -> Dict[str, float]:
    """Query historical_stats with filters"""
    query = text("""
        SELECT actual_points, week
        FROM historical_stats
        WHERE player_key = :player_key
          AND season = :season
          AND snaps >= 20
          AND actual_points IS NOT NULL
        ORDER BY week DESC
        LIMIT :weeks_back
    """)
    rows = self.session.execute(query, {...}).fetchall()
    # Process results, handle missing data, return dict with metrics
```

**Key Takeaways:**
- Pattern for accessing historical_stats table
- Use LIMIT and ORDER BY for most recent games
- Handle NULL values in calculations
- Return structured dict for missing data scenarios

**3. SmartScoreService** (`/Users/raybargas/Documents/Cortex/backend/services/smart_score_service.py`)

Integration points for W7 and W8:

**W7 Vegas Context:**
```python
def _calculate_w7_vegas_context(
    self, player: PlayerData, week_id: int,
    weight: float, defaults: Dict
) -> FactorResult:
    # Gets team_itt from database
    # Compares to DEFAULT_LEAGUE_AVG_ITT = 22.5
    # Calculates (team_itt / league_avg_itt) * weight
```

**W8 Matchup Adjustment:**
```python
def _calculate_w8_matchup_adjustment(
    self, player: PlayerData, weight: float
) -> FactorResult:
    # Uses player.opponent_rank_category
    # Maps to category values (top_5, middle, bottom_5)
    # Returns adjustment multiplied by weight
```

**W5 Trend Adjustment:**
```python
def _calculate_w5_trend_adjustment(
    self, player: PlayerData, week_id: int, weight: float
) -> Tuple[FactorResult, int]:
    # Uses HistoricalInsightsService to get recent stats
    # Analyzes trends in recent games
    # Returns trend_percentage * weight
```

### Data Import Pattern

**DataImporter** (`/Users/raybargas/Documents/Cortex/backend/services/data_importer.py`)

Pattern for data validation and bulk insertion:
```python
def validate_data(self, df: pd.DataFrame, source: str) -> pd.DataFrame:
    """Validate and convert data types"""
    # Convert to proper types
    # Check constraints (salary ranges, position valid values)
    # Fill missing values with defaults

def bulk_insert_to_database(
    self, df: pd.DataFrame, week_id: int, source: str
) -> Tuple[int, int]:
    """Insert validated data to database"""
    # Use raw SQL INSERT with VALUES lists
    # Handle unique constraint violations
    # Return (success_count, failure_count)
```

## Smart Score Integration Points

### Current W5 (Trend Adjustment) Implementation

From SmartScoreService:
- Queries historical_stats for recent games (6 weeks default)
- Filters for games with snaps >= 20
- Calculates percentage change in per-game metrics
- Returns trend_percentage * W5_weight

**MySportsFeeds Integration:** Daily gamelogs will populate historical_stats with recent game-by-game data, ensuring W5 has real data rather than projections.

### Current W7 (Vegas Context) Implementation

From SmartScoreService:
- Uses player.opponent_rank_category (currently from manual import)
- DEFAULT_LEAGUE_AVG_ITT = 22.5
- Calculates (team_itt / league_avg_itt) * W7_weight
- Falls back to 1.0 if team_itt missing

**MySportsFeeds Integration:** Weekly games endpoint provides ITT, eliminating manual import requirement.

### Current W8 (Matchup Adjustment) Implementation

From SmartScoreService:
- Uses opponent defensive ranking to categorize matchup quality
- Categories: top_5 (1.0), middle (0.0), bottom_5 (-1.0)
- Returns category_value * W8_weight

**MySportsFeeds Integration:** Team stats endpoint provides pass/rush defense rankings, enabling dynamic matchup categorization.

## API Dependencies Review

### httpx (Async HTTP Client)

Already in requirements.txt (version 0.25.1 - 0.26.0). Suitable for:
- Async HTTP GET/POST requests
- HTTP Basic authentication (built-in support)
- Retry mechanisms
- Timeout handling
- Error responses (4xx, 5xx)

**Usage Pattern:**
```python
import httpx

async def fetch_data():
    async with httpx.AsyncClient(
        auth=("token", "MYSPORTSFEEDS_TOKEN"),
        timeout=30
    ) as client:
        response = await client.get(
            "https://api.mysportsfeeds.com/v2.1/pull/nfl/injuries.json",
            params={"season": "current"}
        )
        if response.status_code == 429:  # Rate limit
            retry_after = response.headers.get("Retry-After")
        return response.json()
```

### python-dotenv (Environment Configuration)

Already in requirements.txt. Used for loading environment variables:
```python
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("MYSPORTSFEEDS_TOKEN")
```

## Background Scheduling Options

### APScheduler (Lightweight)

Pros:
- Single package, no broker needed
- Simpler to set up and debug
- Sufficient for once-daily jobs
- Already used in similar DFS tools

Implementation:
```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = BackgroundScheduler()
scheduler.add_job(
    refresh_mysportsfeeds_data,
    CronTrigger(hour=5, minute=0, timezone="US/Eastern")
)
scheduler.start()
```

### Celery + Redis (Enterprise)

Pros:
- Distributed task queue
- Better for multiple scheduled jobs
- Scales horizontally

Cons:
- Requires Redis or other broker
- More complex setup
- Overkill for once-daily refresh

**Recommendation:** APScheduler for Phase 1; can migrate to Celery if needs grow

## Database Schema Decisions

### Option A: Extend player_pools with MySportsFeeds Data

Add columns to existing player_pools table:
- `injury_status VARCHAR(20)` (PROBABLE, QUESTIONABLE, DOUBTFUL, OUT)
- `implied_team_total FLOAT` (from weekly games)
- `opponent_rank_category VARCHAR(20)` (already exists)

**Pros:**
- Minimal schema changes
- Uses existing table structure
- Simplifies queries (single table joins)

**Cons:**
- Couples injury/Vegas data with player pool
- Can't track historical defensive rankings by season

### Option B: New Tables for Each Data Type

Create dedicated tables:
- `player_injuries(player_key, current_injury, playing_probability, updated_at)`
- `team_defense_stats(season, team_abbr, pass_def_rank, rush_def_rank, updated_at)`
- `vegas_lines(week_id, team, implied_team_total, updated_at)`

**Pros:**
- Clean separation of concerns
- Enables historical tracking
- Flexible for future enhancements

**Cons:**
- More schema complexity
- More database migrations needed
- More join queries

**Recommendation:** Option A for MVP (simpler); can refactor to Option B later if needed

## Code Organization Recommendations

### File Structure

```
backend/
├── services/
│   ├── mysportsfeeds_service.py (NEW)
│   │   ├── MySportsFeedsService class
│   │   └── Methods: fetch_injuries, fetch_games, fetch_stats, fetch_gamelogs
│   ├── smart_score_service.py (EXISTING - integrate with)
│   └── ... (other services)
├── scripts/
│   ├── scheduler.py (NEW)
│   │   └── Background job initialization
│   └── ... (other scripts)
├── routers/
│   ├── mysportsfeeds_router.py (OPTIONAL)
│   │   └── Endpoints: GET /api/mysportsfeeds/refresh (manual trigger)
│   └── ... (other routers)
├── main.py (EXISTING - modify)
│   └── Initialize scheduler at startup
└── requirements.txt (EXISTING - modify)
    └── Add APScheduler if not present
```

## Configuration Management

**Environment Variables (.env):**
```
# MySportsFeeds API Configuration
MYSPORTSFEEDS_TOKEN=your_token_here
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

**Documentation (.env.example):**
- List all required variables
- Provide example values
- Document defaults
- Link to MySportsFeeds API documentation

## Testing Strategy

### Unit Tests Location

`/Users/raybargas/Documents/Cortex/tests/unit/`

Tests for MySortsFeedsService:
```
test_mysportsfeeds_service.py
├── test_parse_injuries_response()
├── test_parse_games_response()
├── test_parse_team_stats_response()
├── test_parse_gamelogs_response()
├── test_handle_rate_limit()
├── test_handle_network_error()
├── test_database_insert_injury_status()
├── test_database_insert_team_stats()
└── test_refresh_all_data()
```

### Integration Tests Location

`/Users/raybargas/Documents/Cortex/tests/integration/`

Tests with database:
```
test_mysportsfeeds_integration.py
├── test_end_to_end_refresh()
├── test_partial_failure_handling()
├── test_smart_score_uses_fetched_data()
├── test_w5_trend_with_real_gamelogs()
├── test_w7_vegas_with_real_itt()
└── test_w8_matchup_with_real_defensive_ranks()
```

## Performance Considerations

### API Response Sizes

- Injuries endpoint: ~500 players * ~50 bytes = ~25 KB
- Games endpoint: ~16 games * ~200 bytes = ~3.2 KB
- Team stats endpoint: ~32 teams * ~100 bytes = ~3.2 KB
- Gamelogs endpoint: ~500 players * ~150 bytes = ~75 KB

**Total:** ~106 KB per daily refresh (negligible)

### Database Operations

- Injury updates: ~500 rows, 1 BATCH UPDATE query
- ITT updates: ~32 rows, 1 BATCH UPDATE query
- Team stats: ~32 rows, 1 UPSERT query
- Gamelogs: ~500 rows, 1 BATCH INSERT query

**Total:** ~4 database queries, <1 second execution time

### Scheduled Refresh Timing

- API call overhead: ~5 seconds (network latency + parsing)
- Database operations: ~1 second (4 queries)
- Total: ~6 seconds per refresh
- Target: Complete in <30 seconds
- Safety margin: Plenty

## Risk Assessment

### Potential Issues

1. **API Rate Limiting**
   - Risk: 429 responses during high volume
   - Mitigation: Respect Retry-After header, implement exponential backoff
   - Impact: Low (once daily, low request volume)

2. **Data Inconsistency**
   - Risk: Partial updates if job crashes mid-execution
   - Mitigation: Use transactions, validate data before commit
   - Impact: Medium (could affect single calculation cycle)

3. **Stale Data Fallback**
   - Risk: Smart Score uses old data if API fails
   - Mitigation: Document defaults, use NULL for missing data
   - Impact: Low (graceful degradation)

4. **Authentication Failure**
   - Risk: Token invalid or expired
   - Mitigation: Log auth errors prominently, alert admin
   - Impact: Medium (requires manual intervention)

5. **Dependency Deadlock**
   - Risk: Historical_stats table locked during gamelogs insert
   - Mitigation: Use READ COMMITTED isolation, keep transactions short
   - Impact: Low (isolated to once-daily job)

## Future Enhancement Opportunities

1. **Real-Time Injury Updates:** Polling every 30 minutes instead of once daily
2. **Multiple Vegas Line Updates:** Fetch updated lines before key game times
3. **Contest Results Integration:** Pull final scores from DFS sites post-game
4. **Advanced Defensive Metrics:** Pass yards allowed rank, red zone defense %, etc.
5. **Webhook Support:** If MySportsFeeds offers push notifications
6. **Data Retention Policy:** Archive weekly/monthly snapshots for historical analysis
7. **Manual Refresh Endpoint:** Allow users to trigger refresh via API

## References

### Key Files Analyzed

- `/Users/raybargas/Documents/Cortex/backend/main.py` - FastAPI app setup
- `/Users/raybargas/Documents/Cortex/backend/requirements.txt` - Dependencies
- `/Users/raybargas/Documents/Cortex/backend/services/nfl_schedule_service.py` - Service pattern
- `/Users/raybargas/Documents/Cortex/backend/services/historical_insights_service.py` - Query pattern
- `/Users/raybargas/Documents/Cortex/backend/services/smart_score_service.py` - Integration points
- `/Users/raybargas/Documents/Cortex/backend/services/data_importer.py` - Data validation pattern
- `/Users/raybargas/Documents/Cortex/tests/conftest.py` - Database schema reference

### External Documentation

- MySportsFeeds API v2.1: https://www.mysportsfeeds.com/api/docs
- FastAPI: https://fastapi.tiangolo.com/
- SQLAlchemy: https://docs.sqlalchemy.org/
- httpx: https://www.python-httpx.org/
- APScheduler: https://apscheduler.readthedocs.io/
