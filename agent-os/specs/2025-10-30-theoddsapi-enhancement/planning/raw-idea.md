# Raw Idea: TheOddsAPI Integration for Enhanced Vegas Odds

Integrate TheOddsAPI to supplement MySportsFeeds with real-time Vegas odds and line comparison across multiple sportsbooks (DraftKings, FanDuel, BetMGM, Caesars). This Phase 2 enhancement provides advanced Vegas Context calculations with:

1. Real-time ITT updates (multiple times per day vs MySportsFeeds once daily)
2. Multi-sportsbook line comparison (identify sharp action across books)
3. Spread/total movement tracking (detect early line movement)
4. Consensus odds calculation (weighted average across books)

API: The Odds API v4
Endpoint: https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds
Auth: Query parameter apiKey
Free Tier: 500 requests/month (plenty for daily refresh + monitoring)

Smart Score Impact:
- W7 (Vegas Context): Use real-time ITT instead of daily MySportsFeeds
- Advanced Strategy: Different weights for different sportsbooks
- Smart Exposure: Adjust lineup counts based on line movement

This is Phase 1.5B of the roadmap - optional enhancement to Smart Score Vegas Context calculations. Complements MySportsFeeds with real-time data. Can be built after MySportsFeeds foundation is complete.
