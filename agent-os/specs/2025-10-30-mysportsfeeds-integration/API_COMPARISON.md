# API Comparison: MySportsFeeds vs TheOddsAPI

## Overview

You have two complementary APIs available for integration. This document compares them to determine the optimal strategy.

| Aspect | MySportsFeeds | TheOddsAPI |
|--------|---------------|-----------|
| **Primary Purpose** | Comprehensive sports data (injuries, stats, gamelogs, schedules) | Betting odds and lines only |
| **API Key Available** | ✅ Yes (in .env as MySportsFeed=...) | ✅ Yes (in .env as TheOddsAPI=...) |
| **Cost** | Subscription-based (you already have it) | Free tier (500 req/month) |
| **Request Limit** | Depends on subscription | 500 requests/month |
| **Authentication** | HTTP Basic Auth (token:MYSPORTSFEEDS) | Query parameter (?apiKey=...) |
| **Response Format** | JSON, CSV, XML | JSON only |

## Data Coverage Comparison

### Vegas Odds & Lines (ITT, Spreads)

| Data | MySportsFeeds | TheOddsAPI | Recommendation |
|------|---------------|-----------|-----------------|
| **Source** | Weekly Games endpoint | Betting odds endpoint | **MySportsFeeds** (primary) |
| **ITT (Implied Team Total)** | ✅ Available in game schedule | ✅ Available as "totals" | Primary: MySportsFeeds |
| **Spreads** | ✅ Available | ✅ Available | Either (same data) |
| **Multiple Sportsbooks** | ❌ Limited | ✅ DraftKings, FanDuel, BetMGM, Caesars, etc. | TheOddsAPI if book comparison needed |
| **Real-time Updates** | Daily | Multiple times per day | TheOddsAPI for real-time |
| **Fresh Data** | 5:00 AM EST daily | Hourly/On-demand | TheOddsAPI for freshness |

### Player Injuries

| Data | MySportsFeeds | TheOddsAPI |
|------|---------------|-----------|
| **Injury Data** | ✅ Current status + probability | ❌ Not available |
| **Update Frequency** | Daily | N/A |
| **Use Case** | Flag OUT/DOUBTFUL players | N/A |

**Recommendation:** MySportsFeeds only (no alternative)

### Player Gamelogs & Stats

| Data | MySportsFeeds | TheOddsAPI |
|------|---------------|-----------|
| **Game-by-game stats** | ✅ Snaps, targets, receptions, etc. | ❌ Not available |
| **Seasonal stats** | ✅ Team totals available | ❌ Not available |
| **Use for Trend (W5)** | ✅ Perfect fit | ❌ Not available |

**Recommendation:** MySportsFeeds only (no alternative)

### Defensive Rankings & Context

| Data | MySportsFeeds | TheOddsAPI |
|------|---------------|-----------|
| **Team defensive stats** | ✅ Pass defense rank, rush defense rank | ❌ Not available |
| **Use for Matchup (W8)** | ✅ Perfect fit | ❌ Not available |

**Recommendation:** MySportsFeeds only (no alternative)

## Smart Score Integration Strategy

### W5: Trend Adjustment
- **Data Source:** MySportsFeeds (Daily Player Gamelogs)
- **Data Required:** snaps, targets, receptions per game
- **Update Frequency:** Daily
- **Alternative:** None available
- **Implementation:** PRIMARY (MySportsFeeds)

### W7: Vegas Context
- **Data Source 1:** MySportsFeeds (Weekly Games) - PRIMARY
  - Contains ITT in game schedule
  - Updates daily at 5:00 AM EST
  - Reliable for week-level odds

- **Data Source 2:** TheOddsAPI (Odds endpoint) - OPTIONAL ALTERNATIVE
  - Multiple sportsbooks comparison
  - Real-time updates
  - Lower request budget (500/month)

- **Implementation Strategy:**
  - PRIMARY: Use MySportsFeeds ITT
  - FALLBACK: Use TheOddsAPI if MySportsFeeds fails
  - BONUS: Compare ITT across books (DraftKings vs FanDuel)

### W8: Matchup Adjustment
- **Data Source:** MySportsFeeds (Team Stats)
- **Data Required:** Opponent defensive ranking
- **Update Frequency:** Daily
- **Alternative:** None available
- **Implementation:** PRIMARY (MySportsFeeds)

### Player Availability
- **Data Source:** MySportsFeeds (Injuries)
- **Data Required:** Current injury status, playing probability
- **Update Frequency:** Daily
- **Alternative:** None available
- **Implementation:** PRIMARY (MySportsFeeds)

## Recommended Implementation Approach

### Phase 1: Core Integration (REQUIRED)
**Focus:** MySportsFeeds only
- Injuries (W5 player availability)
- Weekly Games (W7 Vegas Context via ITT)
- Seasonal Team Stats (W8 matchup data)
- Daily Player Gamelogs (W5 trend data)

**Effort:** 15-23 hours
**Timeline:** 2-3 weeks
**Value:** Critical for MVP Smart Score accuracy

### Phase 2: Vegas Enhancement (OPTIONAL)
**Focus:** TheOddsAPI supplementation
- Fetch real-time odds from multiple sportsbooks
- Compare ITT across DraftKings, FanDuel, BetMGM, Caesars
- Use highest/lowest ITT for conservative/aggressive strategies
- Identify line movement patterns

**Effort:** 4-6 hours
**Timeline:** 1 week (after Phase 1)
**Value:** Advanced analytics, sportsbook comparison
**Cost:** Free (within 500 req/month budget)

### Phase 3: Contest Results (FUTURE)
**Focus:** Post-game analysis
- Both APIs can provide historical data
- Compare projected vs actual performance
- Validate Smart Score accuracy

## Request Budget Analysis

### MySportsFeeds
- **Available:** Depends on subscription (you already have it)
- **Expected Daily Calls:** ~4-5 (injuries, games, team stats, gamelogs)
- **Monthly Estimate:** 120-150 requests
- **Status:** Sustainable (included in your plan)

### TheOddsAPI
- **Free Tier:** 500 requests/month
- **Current Plan:** Not yet integrated
- **Proposed Daily Calls:** 1-2 (real-time odds fetch)
- **Monthly Estimate:** 30-60 requests
- **Status:** Plenty of budget available

## Decision Matrix

| Feature | Need for MVP? | Complexity | Value | Priority |
|---------|---------------|-----------|-------|----------|
| MySportsFeeds Integration | ✅ YES | Medium | High | P0 |
| TheOddsAPI Real-time Odds | ❌ NO | Low | Medium | P2 |
| Multi-book Line Comparison | ❌ NO | Medium | Medium | P3 |
| Vegas Movement Tracking | ❌ NO | Medium | Low | P4 |

## Recommendation Summary

**For MVP Smart Score Engine:**
- ✅ **Implement MySportsFeeds** (all 4 endpoints)
  - Injuries: Player availability filtering
  - Weekly Games: ITT for Vegas Context (W7)
  - Team Stats: Defensive rankings for Matchup (W8)
  - Gamelogs: Trend calculations (W5)

**Optional Enhancement (Phase 2):**
- ⚠️ **Add TheOddsAPI** (real-time odds)
  - Supplement MySportsFeeds ITT with real-time data
  - Compare sportsbooks for advanced strategy
  - Budget allows up to 500 req/month

**Not Needed:**
- ❌ Daily contest results import (future phase)
- ❌ Historical odds archive (nice-to-have)

## Implementation Sequencing

1. **Week 1-2:** MySportsFeeds full integration (Phase 1)
2. **Week 3:** Testing, validation, Smart Score integration
3. **Week 4+:** TheOddsAPI enhancement (Phase 2, optional)

## Next Steps

1. Proceed with MySportsFeeds spec/tasks (already created)
2. Create TheOddsAPI spec for Phase 2
3. Begin Phase 1 implementation with implementer agent
