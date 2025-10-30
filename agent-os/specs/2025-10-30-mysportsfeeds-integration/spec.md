# Specification: MySportsFeeds API Integration

## Goal

Integrate the MySportsFeeds v2.1 API to provide real-time external data sources that enhance Smart Score Engine calculations. This integration enables accurate injury awareness, Vegas context calculations, defensive matchup analysis, and historical performance trend tracking for improved DFS lineup optimization.

## User Stories

- As a lineup optimizer, I want real-time injury data so that I can exclude unavailable players from optimization
- As an analyst, I want Vegas Implied Team Total (ITT) data so that I can calculate Vegas Context factors in Smart Score
- As a trend analyst, I want daily player gamelogs so that I can calculate recent performance trends (W5)
- As a matchup strategist, I want opponent defensive rankings so that I can apply matchup adjustments (W8)

## Core Requirements

- Fetch real-time player injury data to flag unavailable players
- Extract Vegas Implied Team Total (ITT) from weekly games for Vegas Context calculations
- Retrieve seasonal team defensive rankings for matchup adjustment factors
- Backfill historical player gamelogs for trend calculation datasets
- Execute daily background refresh job at 5:00 AM EST
- Handle authentication using HTTP Basic Auth with MySportsFeeds token
- Gracefully degrade functionality if API requests fail, using stale data as fallback
- Store fetched data in existing database tables with minimal schema changes

## Visual Design

No UI changes required. This is a backend data integration with indirect visual impact through improved Smart Score calculations displayed in existing UI components.

## Reusable Components

### Existing Code to Leverage

**Services & Patterns:**
- `NFLScheduleService` (backend/services/nfl_schedule_service.py): Pattern for fetching external schedule data, database session management, logging
- `HistoricalInsightsService` (backend/services/historical_insights_service.py): Pattern for analyzing historical_stats table, building queries with sqlalchemy.text
- `DataImporter` (backend/services/data_importer.py): Pattern for data validation, bulk insertion to database, error handling
- `SmartScoreService` (backend/services/smart_score_service.py): Integration point for Vegas Context (W7) and Matchup Adjustment (W8) factors

**Database Tables (existing, reusable):**
- `player_pools`: Add injury_status VARCHAR(20) column (optional, can use dedicated table)
- `historical_stats`: Already stores snaps, targets, receptions for trend calculations
- `weeks`: Links to current NFL week for context
- `week_metadata`: Metadata for week context including season and week_number

**Dependencies (available):**
- FastAPI (framework) - already in use
- SQLAlchemy (ORM) - for database queries
- httpx (async HTTP client) - in requirements.txt, suitable for API calls
- python-dotenv - for environment variable configuration
- logging - standard library for diagnostic logging

### New Components Required

**New Service: `MySportsFeedsService`**
- Location: `backend/services/mysportsfeeds_service.py`
- Cannot reuse existing services because:
  - Requires HTTP API client calls (not file import like DataImporter)
  - Multiple distinct API endpoints with different response structures
  - Needs credential handling (HTTP Basic Auth)
  - Requires error handling for network failures and rate limiting

**New Background Job Scheduler**
- Location: `backend/scripts/scheduler.py` or integrate into main.py
- Purpose: Execute daily refresh at 5:00 AM EST
- Cannot reuse existing code because this is new infrastructure requirement
- Options: APScheduler (simpler) or Celery (more robust)

**Optional: New Database Table for Team Defense Stats**
- Location: Database migrations
- Purpose: Store defensive ranking data per season/team
- Reason: Creates explicit schema for team defensive metrics, decouples from player_pools table

## Technical Approach

### API Integration Architecture

**MySortsFeedsService Class:**
- Constructor: Accept database session, API token from environment
- Method: `fetch_current_week_injuries()` - returns array of injuries with playing probability
- Method: `fetch_weekly_games(season, week)` - returns games with schedule and scores, extracts ITT
- Method: `fetch_team_defensive_stats(season)` - returns team stats with defensive rankings
- Method: `fetch_player_gamelogs(season, date, team_filter=None)` - returns gamelogs filtered by date/team
- Method: `refresh_all_data()` - orchestrates all four fetch methods, stores in database, handles errors
- Error handling: Log failures, return None/empty list, allow calling code to proceed with cached data

**Background Scheduler:**
- Run MySportsFeedsService.refresh_all_data() daily at 5:00 AM EST
- Log execution status (success/failure) to application logs
- Skip execution if previous run still in progress (prevent overlapping jobs)
- Use APScheduler for simplicity (no Celery broker needed)

**Data Flow Pipeline:**
1. Query current week from weeks table
2. Fetch Player Injuries → Parse response → Update player_pools or injury_status table
3. Fetch Weekly Games (current week) → Extract ITT and opponent info → Update vegas_lines or player_pools
4. Fetch Team Stats (current season) → Extract pass/rush defense ranks → Store in team_defense_stats or player_pools
5. Fetch Player Gamelogs (yesterday's date) → Parse stats → Backfill historical_stats for recent week
6. Log each step's status (success/failure) with error details
7. If any step fails, log but continue with remaining steps

### Integration with Smart Score

**W5 (Trend Adjustment):** Uses historical_stats.snaps, targets, receptions
- MySportsFeeds gamelogs backfill historical_stats with recent game-by-game data
- SmartScoreService queries historical_stats directly (no new integration needed)

**W7 (Vegas Context):** Uses vegas_lines.implied_team_total or player_pools field
- MySportsFeeds weekly games provides ITT for each team
- Store ITT in existing player_pools row or dedicated vegas_lines table
- SmartScoreService queries this field when calculating W7

**W8 (Matchup Adjustment):** Uses opponent defensive ranking
- MySportsFeeds team stats provides pass_defense_rank, rush_defense_rank
- Store in team_defense_stats(team, season, pass_def_rank, rush_def_rank)
- SmartScoreService joins opponent team to fetch defensive rank, maps to category (top_5, middle, bottom_5)

**Player Availability:** Uses injury_status from player_pools
- MySportsFeeds injuries provides playingProbability (PROBABLE, QUESTIONABLE, DOUBTFUL, OUT)
- Store in player_pools.injury_status or dedicated injury table
- Lineup optimization filters OUT/DOUBTFUL players from available pool

### API Endpoints & Response Handling

**1. Player Injuries**
- URL: `https://api.mysportsfeeds.com/v2.1/pull/nfl/injuries.json?season=current`
- Auth: HTTP Basic with format `token:MYSPORTSFEEDS_TOKEN`
- Response: `{players: [{player: {lastName, firstName, position, team}, currentInjury: {playingProbability}}]}`
- Key data: player.team, player.position, currentInjury.playingProbability (OUT/DOUBTFUL/QUESTIONABLE/PROBABLE)
- Error handling: If request fails, use last cached injury status from database

**2. Weekly Games**
- URL: `https://api.mysportsfeeds.com/v2.1/pull/nfl/{season}/week/{week}/games.json`
- Auth: HTTP Basic
- Response: `{games: [{schedule: {startTime, awayTeam, homeTeam}, score: {awayScore, homeScore}}]}`
- Key data: awayTeam.abbr, homeTeam.abbr, schedule.startTime, and look for implied_team_total in references section
- Error handling: If fails, skip ITT updates; Smart Score will use DEFAULT_LEAGUE_AVG_ITT fallback

**3. Seasonal Team Stats**
- URL: `https://api.mysportsfeeds.com/v2.1/pull/nfl/{season}/team_stats_totals.json`
- Auth: HTTP Basic
- Response: `{teamStatTotals: [{team: {abbr}, stats: {pass_defense_rank, rush_defense_rank, ...}}]}`
- Key data: team.abbr, stats.pass_defense_rank, stats.rush_defense_rank
- Error handling: If fails, opponent_rank_category stays NULL; SmartScoreService will use average adjustment

**4. Daily Player Gamelogs**
- URL: `https://api.mysportsfeeds.com/v2.1/pull/nfl/{season}/date/{date}/player_gamelogs.json`
- Auth: HTTP Basic
- Request params: Must include at least one of ?team=, ?player=, ?game= filter
- Response: `{gamelogs: [{player: {firstName, lastName, position, team}, game: {date}, stats: {snaps, targets, receptions, ...}}]}`
- Key data: player.firstName, player.lastName, stats.snaps, stats.targets, stats.receptions
- Error handling: If fails, skip updating historical_stats; trend calculations will use existing data

### Configuration & Environment

**Environment Variables:**
- `MYSPORTSFEEDS_TOKEN`: API authentication token (required)
- `SCHEDULER_TIMEZONE`: Timezone for background job (default: US/Eastern)
- `SCHEDULER_HOUR`: Hour for daily refresh (default: 5 for 5:00 AM)
- `SCHEDULER_ENABLED`: Boolean to enable/disable scheduler (default: true)

**API Token Storage:**
- Load from .env file via python-dotenv
- Do NOT commit tokens to version control
- Document in .env.example

### Database Schema Updates

**player_pools table (existing):**
- Add optional column: `injury_status VARCHAR(20)` (values: PROBABLE, QUESTIONABLE, DOUBTFUL, OUT, NULL)
- Add optional column: `implied_team_total FLOAT` (for Vegas Context)
- Add optional column: `opponent_rank_category VARCHAR(20)` (already exists, reuse for storing top_5/middle/bottom_5)

**Alternative: New table team_defense_stats (optional):**
```
team_defense_stats(
  id INTEGER PRIMARY KEY,
  season INTEGER NOT NULL,
  team_abbr VARCHAR(10) NOT NULL,
  pass_def_rank INTEGER,
  rush_def_rank INTEGER,
  pass_yards_allowed_rank INTEGER,
  rush_yards_allowed_rank INTEGER,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  UNIQUE(season, team_abbr)
)
```
Reason: Cleaner schema if defensive stats grow; allows historical tracking by season

**historical_stats table (existing):**
- Already has: snaps, targets, receptions
- Verify columns exist and are properly typed (INTEGER for counts, FLOAT for stats)
- Use as-is for gamelogs backfill

## Error Handling & Resilience

**Network Errors:**
- Retry failed API request with exponential backoff (5s, 10s, 20s max)
- Log error with timestamp and endpoint
- If all retries fail, log warning and continue with remaining steps
- Next scheduled job will retry

**Invalid Response Structure:**
- Catch JSON parsing errors, log details
- Continue with remaining endpoints
- Return empty list to caller; Smart Score will use defaults

**Rate Limiting (429 Status):**
- Read Retry-After header from response
- Wait specified duration before retrying
- Log rate limit event
- If multiple rate limits occur, increase wait time for subsequent jobs

**Missing Data:**
- If ITT missing from games response, use None; SmartScoreService will calculate with default league average
- If defensive ranks missing, use None; SmartScoreService will use average adjustment
- If gamelogs empty, skip historical_stats update; trend calculations use existing data

**Database Errors:**
- Catch unique constraint violations (duplicate injury_status update)
- Log with context, skip problematic record, continue with others
- Allow partial updates (some players updated, others skipped due to errors)

## Testing & Validation

**Unit Tests:**
- Mock MySportsFeeds API responses for each endpoint
- Test response parsing (extract correct fields from JSON)
- Test error handling (network error, invalid JSON, rate limit)
- Test database operations (insert/update player_pools, historical_stats)

**Integration Tests:**
- Use test API credentials (if available) or mock HTTP responses
- Full workflow: fetch → parse → validate → store → verify in database
- Test daily refresh job with mocked time/scheduler

**E2E Tests:**
- Verify Smart Score calculations use fetched data correctly
- Confirm W5 uses latest gamelogs from historical_stats
- Confirm W7 uses ITT from vegas_lines
- Confirm W8 uses defensive rank from team_defense_stats
- Test player availability filtering with injury_status

**Validation Checklist:**
- API responses parse without errors
- All required fields present in responses
- Data types match database schema (INT for counts, VARCHAR for strings)
- Duplicate keys handled (update existing, don't insert duplicates)
- Timestamps recorded correctly (UTC)

## Success Criteria

- Data fetched successfully 99%+ of scheduled refresh cycles
- Refresh completes in under 30 seconds (all 4 API calls combined)
- Zero data loss: If fetch fails, previous data remains in database (no destructive updates)
- Zero Smart Score calculation failures due to missing API data
- Trend calculations (W5) use real historical data from gamelogs 95%+ of the time
- Player availability reflects current injury status accurately (OUT/DOUBTFUL players excluded)
- No application errors logged related to API integration
- Background job logs indicate successful execution or specific failure reason

## Out of Scope

- Real-time injury updates (currently once daily; future enhancement to every 30 minutes)
- Multiple Vegas line updates per day (currently once daily with weekly games)
- Contest results integration (post-game actual scores from DFS sites)
- Advanced defensive metrics beyond pass/rush defense rankings
- Player prop tracking or advanced statistical modeling
- API webhook integration (polling only; synchronous requests)
- Database archival or historical snapshots of API data
- Mobile app support for viewing API data
- API documentation generation or playground UI
