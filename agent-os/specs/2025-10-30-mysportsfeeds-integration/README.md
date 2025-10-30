# MySportsFeeds API Integration - Specification Package

## Overview

This specification package provides comprehensive documentation for integrating the MySportsFeeds v2.1 API to enhance the Smart Score Engine with real-time external data.

**Key Feature:** Daily automated data refresh at 5:00 AM EST providing:
- Player injury statuses for availability filtering
- Vegas Implied Team Totals (ITT) for Vegas Context calculations (W7)
- Team defensive rankings for matchup adjustments (W8)
- Daily player gamelogs for trend analysis (W5)

## Documents in This Package

### 1. spec.md (PRIMARY SPECIFICATION)

**Purpose:** Formal specification for development teams

**Contents:**
- Goal and objectives
- User stories and core requirements
- Visual design requirements
- Reusable components analysis
- Technical approach and architecture
- API endpoints and data structures
- Data flow pipeline
- Smart Score integration points
- Configuration and environment setup
- Database schema updates
- Testing & validation strategy
- Success criteria
- Out of scope items

**Audience:** Developers, tech leads, architects

**Key Sections:**
- Reusable Components: Identifies existing code patterns to leverage
- API Endpoints & Data Structure: Detailed specifications for each of 4 endpoints
- Smart Score Integration: How fetched data integrates into W5, W7, W8 calculations
- Error Handling: Resilience patterns for network failures and rate limiting

### 2. RESEARCH_FINDINGS.md (TECHNICAL ANALYSIS)

**Purpose:** Document research and analysis performed during spec creation

**Contents:**
- Summary of existing architecture analysis
- Backend technology stack review
- Database schema detailed breakdown
- Reusable service patterns with code examples
- Smart Score integration points explained
- API dependency review (httpx, python-dotenv)
- Background scheduling options (APScheduler vs Celery)
- Database schema design decisions
- Code organization recommendations
- Configuration management strategy
- Testing strategy overview
- Performance considerations
- Risk assessment

**Audience:** Architects, senior engineers, technical reviewers

**Key Findings:**
- Existing services to reuse: NFLScheduleService, HistoricalInsightsService, DataImporter
- httpx already in requirements.txt (suitable for API calls)
- Database tables ready for extension (player_pools, historical_stats)
- SmartScoreService has clear integration points (W5, W7, W8)
- APScheduler recommended over Celery (simpler for once-daily job)

### 3. IMPLEMENTATION_GUIDE.md (STEP-BY-STEP INSTRUCTIONS)

**Purpose:** Practical implementation roadmap with code examples

**Contents:**
- Quick start guide
- Phase 1: Core service implementation (MySortsFeedsService)
- Phase 2: Background scheduler
- Phase 3: Database schema updates
- Phase 4: Integration with SmartScoreService
- Phase 5: Testing strategy
- Phase 6: Configuration and deployment
- Monitoring and maintenance guidance
- Rollback procedures

**Audience:** Developers implementing the feature

**Key Phases:**
1. MySortsFeedsService with 6 core methods
2. Background scheduler (APScheduler integration)
3. Database migrations (add columns to player_pools)
4. SmartScoreService updates for W7 and W8
5. Unit and integration tests
6. Environment configuration and deployment

## Quick Reference

### File Locations

| Component | Location |
|-----------|----------|
| Service | `/Users/raybargas/Documents/Cortex/backend/services/mysportsfeeds_service.py` |
| Scheduler | `/Users/raybargas/Documents/Cortex/backend/scripts/scheduler.py` |
| Tests | `/Users/raybargas/Documents/Cortex/tests/unit/test_mysportsfeeds_service.py` |
| Configuration | `.env` and `.env.example` files |

### Key Dependencies (Existing)

- FastAPI (web framework)
- SQLAlchemy (ORM)
- httpx (async HTTP client) - in requirements.txt
- python-dotenv (environment config)
- APScheduler (background jobs) - may need to add

### Smart Score Integration Points

| Factor | Data Source | Implementation |
|--------|------------|-----------------|
| W5 (Trend) | Player gamelogs → historical_stats | Automatic (no code change) |
| W7 (Vegas) | Weekly games → implied_team_total | Query `player_pools.implied_team_total` |
| W8 (Matchup) | Team stats → defensive ranks | Query `team_defense_stats` table |
| Availability | Player injuries → injury_status | Filter out OUT/DOUBTFUL players |

### API Endpoints

| Data | URL | Key Fields |
|------|-----|-----------|
| Injuries | /nfl/injuries.json?season=current | playingProbability |
| Games | /nfl/{season}/week/{week}/games.json | implied_team_total |
| Team Stats | /nfl/{season}/team_stats_totals.json | pass_def_rank, rush_def_rank |
| Gamelogs | /nfl/{season}/date/{date}/player_gamelogs.json | snaps, targets, receptions |

## Development Workflow

### Recommended Implementation Order

1. **Start:** MySortsFeedsService implementation (Phase 1)
   - Implement HTTP client with error handling
   - Implement response parsing for each endpoint
   - Implement database storage methods
   - Write unit tests with mocked responses

2. **Next:** Background scheduler (Phase 2)
   - Create APScheduler integration
   - Add to main.py startup
   - Test with manual trigger

3. **Then:** Database updates (Phase 3)
   - Run schema migrations
   - Add columns or create new tables
   - Verify schema with test data

4. **Integrate:** SmartScoreService updates (Phase 4)
   - Update W7 calculation to use fetched ITT
   - Update W8 calculation to use defensive ranks
   - Verify Smart Score calculations work correctly

5. **Test:** Comprehensive testing (Phase 5)
   - Unit tests for service layer
   - Integration tests with database
   - E2E tests of Smart Score calculations

6. **Deploy:** Configuration and rollout (Phase 6)
   - Configure environment variables
   - Test in staging environment
   - Deploy to production with monitoring

### Testing Checklist

- [ ] Service fetches all 4 endpoints without errors
- [ ] API responses parsed correctly
- [ ] Error handling works (network, rate limits, invalid data)
- [ ] Data stored correctly in database
- [ ] Smart Score calculations use fetched data
- [ ] W5 uses real gamelogs (not just projections)
- [ ] W7 uses real ITT (not just defaults)
- [ ] W8 uses real defensive ranks
- [ ] Player availability filtering works
- [ ] No performance degradation (refresh < 30s)
- [ ] Scheduler runs at correct time (5:00 AM EST)
- [ ] Logs show execution success/failure

## Success Metrics

Once implemented, the integration should achieve:

- **Availability:** 99%+ successful refresh cycles
- **Performance:** Refresh completes in <30 seconds
- **Data Quality:** 95%+ of calculations use real external data
- **Reliability:** Zero Smart Score failures due to missing data
- **Resilience:** Graceful degradation if APIs unavailable

## Configuration Example

```ini
# .env file
MYSPORTSFEEDS_TOKEN=your_actual_token_from_api
MYSPORTSFEEDS_API_BASE=https://api.mysportsfeeds.com/v2.1
SCHEDULER_ENABLED=true
SCHEDULER_TIMEZONE=US/Eastern
SCHEDULER_HOUR=5
SCHEDULER_MINUTE=0
```

## Key Design Decisions

1. **Reuse existing infrastructure:** Leverage SQLAlchemy patterns, FastAPI framework, httpx client
2. **Minimal schema changes:** Add columns to existing tables (player_pools) rather than many new tables
3. **Graceful degradation:** If API fails, Smart Score uses defaults; no data loss
4. **Once-daily refresh:** Simpler implementation than real-time polling; APScheduler sufficient
5. **HTTP Basic Auth:** Standard approach for MySportsFeeds API; credentials in environment
6. **Comprehensive error handling:** Network retries, rate limit respect, partial failure handling

## Maintenance & Operations

### Daily Operations
- Monitor scheduler logs for successful execution
- Check for API authentication failures
- Verify data freshness in database

### Weekly Review
- Check error logs for patterns
- Monitor API response times
- Verify Smart Score calculations use fetched data

### Monthly Maintenance
- Review MySportsFeeds API documentation for changes
- Verify token still valid
- Analyze data quality metrics

### Performance Tuning
- Monitor API response times (target <30s total)
- Analyze database query performance
- Consider caching if needed

## Documentation Files Referenced

From analysis of codebase:
- `/Users/raybargas/Documents/Cortex/backend/main.py` - FastAPI setup
- `/Users/raybargas/Documents/Cortex/backend/requirements.txt` - Dependencies
- `/Users/raybargas/Documents/Cortex/backend/services/nfl_schedule_service.py` - Service pattern
- `/Users/raybargas/Documents/Cortex/backend/services/smart_score_service.py` - Integration points
- `/Users/raybargas/Documents/Cortex/tests/conftest.py` - Database schema

## External Resources

- MySportsFeeds API Documentation: https://www.mysportsfeeds.com/api/docs
- FastAPI: https://fastapi.tiangolo.com/
- SQLAlchemy: https://docs.sqlalchemy.org/
- httpx: https://www.python-httpx.org/
- APScheduler: https://apscheduler.readthedocs.io/

## Questions & Clarifications

### Q: What happens if the API is unavailable?
A: The scheduler logs the error and continues with stale data. Smart Score uses defaults (e.g., league average ITT). No data is deleted or overwritten.

### Q: Can we fetch data more frequently?
A: Yes, the implementation allows configuring refresh frequency. Start with once daily; future enhancement to real-time possible.

### Q: What if we exceed API rate limits?
A: Implementation respects Retry-After header and uses exponential backoff. If rate limited, next day's refresh will retry.

### Q: How do we test without API credentials?
A: Unit tests use mocked httpx responses. Integration tests can use test API credentials if available from MySportsFeeds.

### Q: Can we make refresh manual?
A: Yes, Phase 5 (Implementation Guide) includes optional endpoint for manual refresh.

## Next Steps

1. Review this specification package with team
2. Assign developer to Phase 1 (MySortsFeedsService)
3. Set up test environment with MySportsFeeds API credentials
4. Begin implementation following IMPLEMENTATION_GUIDE.md
5. Create pull request with code changes
6. Perform code review against specification
7. Deploy to staging for testing
8. Monitor first week of production data

## Document Version

- **Created:** October 30, 2025
- **Status:** Specification Complete - Ready for Development
- **Author:** Claude Code (Specification Writer)
- **Specification Type:** Backend Service Integration
- **Scope:** MySportsFeeds API integration for Smart Score enhancement
