# Raw Idea: MySportsFeeds API Integration

Integrate MySportsFeeds API to provide real-time data for Smart Score Engine. This includes:
1. Player Injuries - fetch current injury status to exclude unavailable players
2. Weekly Games - fetch weekly schedule and final scores for opponent context
3. Seasonal Team Stats - fetch defensive rankings and performance metrics
4. Daily Player Gamelogs - fetch historical game-by-game stats for trend calculations

Data fetching will occur once daily (morning) via background job. The integration will enhance Smart Score calculations with accurate:
- Injury-aware player availability
- Vegas Context (ITT from weekly games)
- Defensive matchup data for Matchup Adjustment factor (W8)
- Historical stats for Trend Adjustment factor (W5)

Authentication: HTTP Basic Auth with MySportsFeeds token (v2.1 API)
Endpoints:
- Player Injuries: https://api.mysportsfeeds.com/v2.1/pull/nfl/injuries.json
- Weekly Games: https://api.mysportsfeeds.com/v2.1/pull/nfl/{season}/week/{week}/games.json (contains ITT/spreads)
- Seasonal Team Stats: https://api.mysportsfeeds.com/v2.1/pull/nfl/{season}/team_stats_totals.json
- Daily Player Gamelogs: https://api.mysportsfeeds.com/v2.1/pull/nfl/{season}/date/{date}/player_gamelogs.json

This is Phase 1.5 of the roadmap - external data integration for MVP Smart Score Engine enhancement.
