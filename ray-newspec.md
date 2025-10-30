# Historical Stats Insights for Lineup Generation

## Current Usage (Smart Score)
- **W5: Trend Adjustment** - Uses target share, snap % trends
- **W6: Regression Risk** - 80-20 rule detection
- **Games with 20+ snaps count** - Shown in table

## Additional Insights for Lineup Generation

### 1. Consistency & Reliability Metrics
**Per-position:**
- **Consistency Score**: Coefficient of variation (stddev/mean) of actual_points
- **Floor/Ceiling Ranges**: Min/max actual_points over last 4-6 weeks
- **Hit Rate**: % of games with 20+ points (for GPP upside)

**Use Case:** Filter optimizer to prioritize players with consistent floors OR high upside variance

### 2. Stack Correlation Analysis
**Team-level:**
- **QB-WR Correlation**: Historical correlation of QB points vs. WR points from same team
- **Game Stack Value**: Performance when stacking both teams in same game
- **RB-WR Correlation**: Negative correlation (RB gets targets when WR regresses)

**Use Case:** Weight stack scoring in optimizer; favor QB-WR pairs with high correlation

### 3. Opponent-Specific Performance
**Per-player:**
- **vs. Top 5 Defenses**: Avg points vs top-5 ranked defenses
- **vs. Bottom 5 Defenses**: Avg points vs bottom-5 defenses  
- **Opponent Matchup History**: Player performance vs this week's specific opponent

**Use Case:** Boost Smart Score for players with strong matchup history

### 4. Usage Pattern Trends
**Position-specific:**
- **RB**: Touch trend (increasing/decreasing touches over last 4 weeks)
- **WR/TE**: Target share trend (rising/falling)
- **QB**: Pass attempt trend (proxy via targets thrown)
- **Snap % Trend**: Positive/negative momentum

**Use Case:** Already used in W5, but could be surfaced as visual indicator

### 5. Salary Efficiency Patterns
**Per-player:**
- **Historical Value Score**: Avg(actual_points / salary * 1000) over last 6 weeks
- **Salary-based Consistency**: Do they outperform salary consistently?
- **Value Regression**: Players who scored 20+ at low salary then regress

**Use Case:** Filter optimizer to prioritize players with consistent salary efficiency

### 6. Game Script Indicators
**Game-level:**
- **High-scoring Games**: Players who perform better in games with high ITT
- **Low-scoring Games**: Players who perform better in defensive games
- **Blowout Indicators**: RB performances in games where team leads by 14+

**Use Case:** Weight players based on projected game script (high/low ITT)

### 7. Workload & Injury Indicators
**Per-player:**
- **Snap Count Trend**: Declining snaps = injury risk
- **Touch Count Trend**: Sharp decline = workload concern
- **Recent Workload**: Avg touches over last 2 weeks vs season avg

**Use Case:** Flag players with declining usage as risky plays

### 8. Positional Stacking Insights
**Global:**
- **RB Correlation**: Negative correlation between RB1 and RB2 on same team
- **TE Regression**: TEs who score 15+ tend to regress next week
- **DST Correlation**: Negative correlation with high-scoring offenses

**Use Case:** Constraint rules: avoid RB1+RB2 same team, favor TE after down week

---

## Implementation Priority

### Phase 1: Quick Wins (Add to Smart Score Table)
1. ✅ **Consistency Indicator** - Show coefficient of variation next to player name
2. ✅ **Opponent Matchup History** - Show avg points vs this week's opponent
3. ✅ **Value Trend** - Show if player is trending up/down in value

### Phase 2: Lineup Optimizer Features
1. ✅ **Stack Correlation Metadata** - Show stack correlation as metadata (does NOT affect Smart Score)
2. ✅ **Consistency Filter** - Exclude players with CV > 1.5 (too volatile)
3. ✅ **Salary Efficiency Filter** - Prioritize players with value score > 5.0 historically

### Phase 3: Advanced Analytics
1. **Game Script Analysis** - Weight players based on projected game flow
2. ✅ **Usage Pattern Warnings** - Flag players with declining snap/touch trends
3. **Stack Optimizer** - Suggest optimal QB-WR-TE combinations based on correlation

---

## Implementation Details

### Backend Changes

#### New Service: `HistoricalInsightsService`
- `get_player_consistency(player_key, season, weeks_back=6)` → CV, floor, ceiling
- `get_opponent_matchup_history(player_key, opponent, season)` → avg points vs opponent
- `get_salary_efficiency_trend(player_key, season, weeks_back=6)` → value score trend
- `get_usage_pattern_warnings(player_key, season, current_week)` → snap/touch trend warnings
- `get_stack_correlation(qb_player_key, wr_player_key, season)` → correlation coefficient

#### New API Endpoints
- `GET /api/insights/player/{player_key}/consistency` - Get consistency metrics
- `GET /api/insights/player/{player_key}/matchup-history` - Get opponent history
- `GET /api/insights/player/{player_key}/salary-efficiency` - Get value trends
- `GET /api/insights/player/{player_key}/usage-warnings` - Get usage pattern warnings
- `GET /api/insights/stack-correlation` - Get QB-WR correlation

#### Smart Score Enhancements
- Add consistency score to `PlayerScoreResponse`
- Add opponent matchup history to `PlayerScoreResponse`
- Add usage warnings to `PlayerScoreResponse`
- Add stack correlation metadata to `PlayerScoreResponse` (metadata only - does NOT affect Smart Score calculation)

### Frontend Changes

#### Smart Score Table Enhancements
- Add "Consistency" column (CV score with color coding)
- Add "vs Opponent" column (avg points vs this week's opponent)
- Add "Usage Trend" indicator (▲/▼/→ with warning badge)
- Add "Stack Potential" column (shows top stack correlation partners - metadata only)
- Add filters for consistency (min CV threshold)
- Add filters for salary efficiency (min value score)

#### New Components
- `ConsistencyIndicator` - Visual consistency score
- `MatchupHistoryBadge` - Opponent performance indicator
- `UsageWarningBadge` - Snap/touch decline warnings
- `StackPotentialBadge` - Shows stack correlation metadata (does NOT affect Smart Score)

#### Lineup Optimizer Integration
- Add consistency filter option
- Add salary efficiency filter option
- Use stack correlation data when building lineups (boost lineup score when correlated pairs are selected together)
- Add usage warning exclusions (flag risky players)

---

## Data Schema Updates

### New Columns (if needed)
- `player_pools`: Add computed columns for consistency, matchup history (cached)
- Consider materialized view for performance

### Database Queries
- Materialize consistency scores per week
- Cache opponent matchup histories
- Pre-compute stack correlations for common QB-WR pairs

---

## Technical Notes

### Performance Considerations
- Cache consistency scores (calculate once per week)
- Use materialized views for frequently accessed correlations
- Batch load insights for all players in Smart Score calculation

### Edge Cases
- Handle players with < 3 games of history
- Handle missing opponent data
- Handle players who changed teams
- Handle position changes (WR → RB, etc.)

