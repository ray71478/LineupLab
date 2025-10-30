# Smart Score Engine - Requirements Documentation

**Feature:** Smart Score Engine  
**Phase:** Phase 1 - MVP  
**Status:** Requirements Gathered  
**Created:** October 30, 2025  
**Last Updated:** October 30, 2025

---

## Answers to Clarifying Questions

### 1. Smart Score Formula Implementation ✅ ANSWERED (Partially)

**Answer:** Formula and weights will be determined from past weeks' data analysis. No specific formula provided yet - will iterate based on data.

**Action Required:** Build flexible formula structure that can be adjusted based on historical performance analysis.

**Status:** Needs refinement through data analysis phase.

---

### 2. Weight Profile Default Values ✅ ANSWERED (Partially)

**Answer:** "Not sure about weights and correlations. I know they exist but no idea what the toggles would be"

**Action Required:** Create default "Base" profile with equal weights initially, allow user to adjust and save custom profiles. Default will be refined through data analysis.

**Status:** Will start with equal weights (W1-W8 = 0.125 each), refine through testing.

---

### 3. Projection Source Selection ✅ ANSWERED

**Answer:** 
- **Preferred:** Establish the Run (ETR) projections (published Thursdays, behind paywall, user has account)
- **Alternative:** Aggregate if possible (would need sample data format)
- **Note:** LineStar doesn't provide ranges like floors/ceilings

**Decision:** 
- Primary: Use ETR projections when available
- Secondary: Allow LineStar as fallback
- Future: Support aggregation if ETR data format provided

**Implementation:** 
- Default to ETR if available, else LineStar
- UI selection: Dropdown or toggle on Smart Score page
- Store selection per week

---

### 4. Vegas Context (ITT) Data Source ✅ ANSWERED

**Answer:** 
- Use separate `vegas_lines` table (changes frequently)
- League average: 22 or 22.5
- Table already designed to support multiple records per week for line movement tracking

**Decision:** 
- Use `vegas_lines` table (marked Phase 2 but needed now)
- Calculate league average ITT from all teams in `vegas_lines` for the week
- If no ITT data: use neutral/default value (22.5)

**Implementation:**
- Ensure `vegas_lines` table import is part of MVP (not deferred to Phase 2)
- Calculate: `Vegas Context = (Player's Team ITT / League Average ITT) × W7`

---

### 5. Opponent Defensive Rank ✅ ANSWERED

**Answer:** 
- "This is the one stat that I think really does not matter much"
- Just flag top 5, bottom 5 matchups
- Don't need granular ranking

**Decision:** 
- Store opponent rank as categorical: "top_5", "middle", "bottom_5"
- Add `opponent_rank_category` field to `player_pools` table
- Visual flag on UI (not heavy weight in calculation)

**Implementation:**
- Import `OppRank` from LineStar
- Categorize: Rank 1-5 = "top_5", Rank 28-32 = "bottom_5", else "middle"
- Weight W8 should be lower than other factors (user preference indicates minimal impact)

---

### 6. Trend Adjustment Calculation ✅ ANSWERED

**Answer:** 
- Rolling averages, last 4 weeks
- **Ideal:** Last 4 games played (accounting for bye weeks/injuries)
- **Filter:** Only count games with 20+ snaps
- **Display:** Show count of 20+ snap games as a column

**Decision:** 
- Calculate trend from last 4 games with 20+ snaps
- Use `historical_stats` table, filter by `snaps >= 20`
- Calculate percentage change in key metrics (target_share, snap_pct)

**Implementation:**
- Query: Get last 4 weeks where player had `snaps >= 20`
- Calculate trend: `(current_week_value - previous_week_value) / previous_week_value`
- If < 4 games available, use available games (minimum 2 for trend calculation)
- Show "20+ Snap Games" count column in player table

**Formula:** 
- For WR/TE: Target share trend
- For RB: Snap % trend
- For QB: Pass attempts trend (if available)

---

### 7. Regression Penalty (80-20 Rule) ✅ ANSWERED

**Answer:** 
- Only apply to WRs (not TEs, not RBs)
- If no historical data exists: Show error message "can't pull" or similar
- For now: Just highlight/flag, not sure about penalty/affect on smart score

**Decision:** 
- Apply 80-20 rule to WRs only
- Check last week's `actual_points` from `historical_stats`
- If `actual_points >= 20`: Flag player (visual indicator)
- **MVP:** Visual flag only, no penalty calculation initially
- **Future:** May add penalty adjustment based on user feedback

**Implementation:**
- Query: Get WR's `actual_points` from `historical_stats` for previous week
- If `actual_points >= 20`: Add visual flag/badge
- If no historical data: Show message "Historical data unavailable"
- Store flag in player data: `regression_risk: boolean`

**Configuration:**
- Threshold: 20 DK points (configurable, default 20)
- Toggle: Enable/disable 80-20 rule per lineup generation

---

### 8. Value Score Calculation ✅ ANSWERED

**Answer:** 
- Salary is in dollars (e.g., 8000 = $80)
- Formula: `Projection / Salary × 1000`
- **Note:** "Points per dollar which isn't historically a reliable stat outside of cash games"

**Decision:** 
- Confirmed: `Value Score = (Projection / Salary) × 1000`
- Weight W4 should be lower (user indicates it's not highly reliable)
- Example: Projection 20, Salary 8000 → Value = (20 / 80) × 1000 = 250

**Implementation:**
- Verify salary storage format (currently stored as integer cents: 8000 = $80)
- Calculation: `(projection / (salary / 100)) × 1000`
- Or: `(projection × 1000) / (salary / 100)` = `(projection × 100000) / salary`

---

### 9. Real-Time Recalculation Performance ✅ ANSWERED

**Answer:** 
- Recalculation: Once all adjustments are made (not on slider change)
- Want snapshot/baseline feature: "here's what the score was, here's what it is now, keep changes? button"

**Decision:** 
- **UI Flow:**
  1. User adjusts weight sliders
  2. User clicks "Apply" or "Recalculate" button
  3. Show snapshot: Previous scores vs. New scores
  4. User clicks "Keep Changes" or "Revert"
  5. Player table updates with new Smart Scores

**Implementation:**
- Store previous Smart Scores before recalculation
- Show delta indicators: `+2.5`, `-1.3` next to scores
- Highlight rows with biggest changes
- "Keep Changes" button applies changes, "Revert" restores previous

**Performance:**
- Recalculate all ~150-200 players on "Apply" click
- Target: <500ms for recalculation
- Show loading indicator during calculation

---

### 10. Weight Profile Storage Schema ⚠️ PARTIALLY ANSWERED

**Answer:** "no idea"

**Decision:** Use JSONB approach (matches existing schema design)
- Store weights as JSONB: `{W1: 0.3, W2: 0.15, W3: 0.2, W4: 0.1, W5: 0.15, W6: 0.05, W7: 0.05, W8: 0.0}`
- Also store configuration: `{projection_source: "ETR", eighty_twenty_enabled: true, eighty_twenty_threshold: 20}`

**Implementation:**
- Follow existing schema: `weight_profiles.weights` as JSONB
- Add `config` JSONB field for formula settings
- Update seed script to match schema

---

### 11. Visual Feedback for Weight Changes ✅ ANSWERED

**Answer:** Change amount and delta indicators

**Decision:**
- Show delta indicators: `+2.5`, `-1.3` next to Smart Score
- Sort by change amount (biggest increases first)
- Color coding: Green for increases, Red for decreases (subtle)

**Implementation:**
- Display format: `Smart Score: 45.2 (+2.5)` or `Smart Score: 38.7 (-1.3)`
- Sort option: "Sort by Score Change"
- Color: `rgba(76, 175, 80, 0.3)` for positive, `rgba(244, 67, 54, 0.3)` for negative

---

### 12. Missing Data Handling ✅ ANSWERED

**Answer:** Use default/neutral values

**Decision:**
- **Missing Projection:** Use 0 (or exclude from calculation)
- **Missing Ceiling/Floor:** Use projection as both ceiling and floor
- **Missing Ownership:** Use league average ownership (calculate from player_pools)
- **Missing Historical Stats:** Use neutral trend (0 change)
- **Missing ITT:** Use league average (22.5)
- **Missing Opponent Rank:** Use "middle" category

**Implementation:**
- Calculate defaults dynamically:
  - League average ownership: `AVG(ownership) FROM player_pools WHERE week_id = X`
  - League average ITT: `AVG(implied_team_total) FROM vegas_lines WHERE week_id = X`
- Show indicator when using defaults (tooltip or badge)

---

## Additional Requirements from Conversation

### 13. Outlier Week Handling ⚠️ OPEN QUESTION

**Question:** How do we overcome outlier weeks (e.g., 5 backup QBs starting, all sim data is flawed)?

**Status:** Open question - no definitive answer yet  
**Consideration:** This affects all systems, not just ours. May need manual override or weighting adjustment.

**Action Required:** Design flexible system that allows manual weight adjustments for outlier weeks.

---

### 14. Minimum Snap Threshold ✅ ANSWERED

**Answer:** 
- Count only games with 20+ snaps for trend calculations
- Show count of 20+ snap games as a column
- Filter out players below certain salary threshold (noted in user notes)

**Decision:**
- Filter historical stats: `snaps >= 20` for trend calculations
- Display "20+ Snap Games" count in player table
- Consider minimum salary threshold (user notes indicate demarcation line)

**Implementation:**
- Add column: "20+ Snap Games" count
- Query: `COUNT(*) FROM historical_stats WHERE player_key = X AND snaps >= 20`
- Visual indicator: Highlight players with < 4 games (insufficient data)

---

### 15. Backup Players (Cheap RBs) ✅ ANSWERED

**Answer:** 
- Weeks with multiple cheap backup RBs below $5K often provide best value
- These players may not have 20+ snap data (they're backups)
- "Historically those provide the best value, but not always ceiling"

**Decision:**
- Don't exclude backup players from Smart Score calculation
- Handle missing snap data gracefully (use projection/ownership as primary factors)
- Consider value score more heavily for sub-$5K players

**Implementation:**
- If < 2 games with 20+ snaps: Use projection and ownership as primary factors
- Trend adjustment: Use neutral value (0) if insufficient data
- Value score: More heavily weighted for salary < $5000

---

### 16. Establish The Run (ETR) Data Import ⚠️ REQUIRES INVESTIGATION

**Answer:** ETR projections preferred, published Thursdays, behind paywall

**Action Required:** 
- Need sample ETR data file format
- Build import functionality for ETR data
- Determine if ETR provides ceilings/floors (user mentioned LineStar doesn't)

**Status:** Pending - requires sample data file

---

## Summary of Decisions

### Formula Structure
- 8-factor additive formula (with subtractions for penalties)
- Weights are independent multipliers (not normalized to sum to 1.0)
- Default weights: Equal (0.125 each) initially, refine through data analysis

### Data Sources
- **Projections:** ETR preferred, LineStar fallback
- **ITT:** Separate `vegas_lines` table (not deferred to Phase 2)
- **Opponent Rank:** Categorical (top_5, middle, bottom_5)
- **Trends:** Last 4 games with 20+ snaps from `historical_stats`

### Special Rules
- **80-20 Rule:** WRs only, visual flag initially (no penalty)
- **Value Score:** Lower weight (not highly reliable)
- **Opponent Rank:** Lower weight (user indicates minimal impact)

### UI/UX
- Recalculate on "Apply" button (not real-time slider changes)
- Snapshot/baseline feature: Show before/after scores
- Delta indicators: Show change amount (+2.5, -1.3)
- Sort by change amount option

### Missing Data
- Use defaults/neutral values
- Calculate league averages dynamically
- Show indicators when defaults used

---

## Follow-up Questions Answered ✅

### 1. ETR Data Format ✅ ANSWERED
**Answer:** Assume same format as DraftKings data (will receive sample soon but proceed with this assumption)

**Decision:** Build ETR import using same structure as DraftKings import, adapt when sample received

---

### 2. Snapshot/Baseline Feature ✅ ANSWERED
**Answer:** 
- After clicking "Apply", modal pops up showing all players whose score changed
- Show before and after scores
- Highlight top 10 biggest changes
- Baseline does NOT persist after "Keep Changes"

**Decision:**
- Modal displays: Player name, Previous Score, New Score, Delta (change amount)
- Top 10 biggest changes highlighted (orange border or background)
- "Keep Changes" button applies changes and closes modal
- "Revert" button restores previous scores and closes modal
- No baseline persistence needed

---

### 3. Trend Calculation - Position-Specific Metrics ✅ ANSWERED
**Answer:**
- WR/TE: Target share trend
- RB: Snap % trend  
- QB: Passing attempts trend
- DST: Skip trend calculation

**Decision:**
- Query position-specific metrics from `historical_stats`
- WR/TE: `target_share` trend
- RB: `snap_pct` trend
- QB: `pass_attempts` trend (or derive from pass_yards if attempts not available)
- DST: Skip factor entirely (set to 0 or neutral)

---

### 4. Ceiling Factor Calculation ✅ ANSWERED
**Answer:** If ceiling/floor missing, estimate based on projection volatility (don't skip factor, don't use projection as both)

**Decision:**
- Normal: `Ceiling Factor = Ceiling - Floor`
- If missing: Estimate based on projection volatility
  - Calculate historical volatility: `std_dev(projections)` from `historical_stats`
  - Estimate: `Ceiling Factor = projection × volatility_multiplier`
  - Or use position-based defaults (e.g., WR: ±5 points, RB: ±4 points)

**Implementation:**
- If both ceiling and floor exist: Use `Ceiling - Floor`
- If missing: Calculate volatility from last 4-8 weeks of projections
- If insufficient historical data: Use position-based default ranges

---

### 5. Salary Threshold for "Punt" Players ✅ ANSWERED
**Answer:** Add field to mark players below certain salary as "punt", filter out below Smart Score threshold from lineup generation

**Decision:**
- Add `is_punt` boolean field to `player_pools` table (or store in notes)
- Add Smart Score threshold setting (e.g., "Exclude players below Smart Score: 35")
- Filter out players below threshold from lineup optimizer input
- Still show in player table, but exclude from optimization

**Implementation:**
- UI: Toggle or checkbox to mark player as "punt"
- UI: Smart Score threshold input field (default: 0 = no filter)
- Backend: Filter player pool before sending to optimizer: `WHERE smart_score >= threshold`

---

### 6. Ownership Penalty Calculation ✅ ANSWERED
**Answer:** Option A - `Penalty = Ownership × W3` (higher ownership = higher penalty)

**Decision:**
- Ownership stored as 0-1 (decimal, e.g., 0.35 = 35%)
- Penalty: `Ownership × W3`
- In formula: `Smart Score = ... - (Ownership × W3) + ...`
- Higher ownership = larger penalty (subtracted from score)

**Example:**
- Player with 35% ownership, W3 = 0.5
- Penalty = 0.35 × 0.5 = 0.175
- Applied as subtraction: `... - 0.175 + ...`

---

### 7. Vegas Context Formula ✅ ANSWERED
**Answer:** Should be additive (not multiplier)

**Decision:**
- Formula: `Vegas Context = (Player's Team ITT / League Average ITT) × W7`
- Applied as: `Smart Score = ... + Vegas Context + ...`
- If ITT > league avg: Positive adjustment
- If ITT < league avg: Negative adjustment

**Example:**
- Player's team ITT: 27.5
- League average ITT: 22.5
- Ratio: 27.5 / 22.5 = 1.222
- Vegas Context = 1.222 × W7 (e.g., 0.05) = 0.0611
- Added to Smart Score

---

### 8. Minimum Games for Trend Calculation ✅ ANSWERED
**Answer:** Use available games (minimum 2), developer determines rest

**Decision:**
- Minimum 2 games required for trend calculation
- If 2-3 games available: Use all available games
- If < 2 games: Use neutral trend (0 change)
- Calculate trend from available games: `(most_recent - oldest) / oldest`

**Implementation:**
- Query: Get last N games with 20+ snaps (up to 4, minimum 2)
- If >= 2 games: Calculate trend
- If < 2 games: Set trend to 0 (neutral)

---

### 9. 80-20 Rule Configuration ✅ ANSWERED
**Answer:** Threshold (20 points) is global, rule applies only to WRs

**Decision:**
- Global threshold: 20 DK points
- Position filter: WR only (not TE, not RB, not QB, not DST)
- Visual flag only (no penalty calculation in MVP)
- Future: May add penalty adjustment

**Implementation:**
- Query: `SELECT actual_points FROM historical_stats WHERE player_key = X AND week = previous_week`
- Filter: Only check if `position = 'WR'`
- If `actual_points >= 20`: Flag `regression_risk = true`
- Display visual badge/icon on player card

---

### 10. Outlier Week Handling ✅ ANSWERED
**Answer:** Defer to post-MVP

**Decision:** 
- Not included in MVP scope
- Design flexible system that allows manual weight adjustments
- Can be addressed in Phase 2 or future enhancement

---

## Final Requirements Summary

### Formula Structure
- **8-Factor Additive Formula:**
  1. Projection × W1
  2. + (Ceiling Factor × W2) [Ceiling - Floor, or volatility estimate]
  3. - (Ownership × W3) [Penalty]
  4. + (Value Score × W4) [(Projection / (Salary/100)) × 1000]
  5. + (Trend Adjustment × W5) [Position-specific: target_share/snap_pct/pass_attempts]
  6. - (Regression Penalty × W6) [WR only, visual flag in MVP]
  7. + (Vegas Context × W7) [(Team ITT / League Avg ITT) × W7]
  8. + (Matchup Adjustment × W8) [Opponent rank category]

### Data Sources
- **Projections:** ETR preferred (same format as DraftKings), LineStar fallback
- **ITT:** `vegas_lines` table (MVP, not Phase 2)
- **Opponent Rank:** Categorical (top_5, middle, bottom_5) from LineStar
- **Trends:** Last 2-4 games with 20+ snaps from `historical_stats`

### UI/UX Features
- **Recalculation:** "Apply" button (not real-time)
- **Snapshot Modal:** Shows all changed players, highlights top 10 biggest changes
- **Delta Indicators:** Show before/after scores with change amount
- **Baseline:** Does not persist after "Keep Changes"

### Smart Score Threshold
- Configurable threshold to exclude players from lineup generation
- Players below threshold still visible in table, but excluded from optimizer
- Default: 0 (no filter)

### Missing Data Handling
- **Ceiling/Floor:** Estimate based on projection volatility or position defaults
- **Trends:** Use available games (min 2) or neutral (0) if insufficient
- **ITT:** Use league average (22.5)
- **Ownership:** Use league average
- **Opponent Rank:** Use "middle" category

---

## Open Questions / Follow-ups Needed

✅ **All questions answered!**

---

## Next Steps

1. ✅ Requirements fully documented
2. ✅ ETR import design (assume DraftKings format)
3. ✅ All follow-up questions resolved
4. ✅ Ready for formal spec writing

**Status:** Spec shaping complete - ready for `/write-spec` command
