# Specification: Elite Player Distribution Optimization System

## Goal

Replace one-at-a-time lineup generation with portfolio optimization that generates all 10 lineups simultaneously, ensuring elite players appear with research-backed frequency across the complete lineup set.

## User Stories

- As a DFS player, I want top Smart Score players to appear in most of my lineups so I can capitalize on proven winners
- As a tournament player, I want my lineups to match Milly Winner distribution patterns so I increase my winning probability
- As a user with salary cap constraints, I want the optimizer to find feasible solutions even when elite targets conflict with other constraints
- As a user optimizing 10 lineups, I want consistent elite player distribution without manual tweaking

## Core Requirements

### Portfolio Optimization
- Generate all 10 user-requested lineups simultaneously (not one-at-a-time)
- Apply elite appearance constraints across entire portfolio
- Maximize total Smart Score across all 10 lineups while meeting distribution targets
- Maintain backward compatibility with existing API endpoints

### Elite Player Identification
- Identify top 15 players by projection per position (QB, RB, WR, TE, DST)
- Apply uniform threshold (top 15) consistently across all positions
- Use projection ranking to determine elite status (not Smart Score)
- Elite players form the pool subject to appearance targets

### Elite Appearance Targets
- Hardcoded `ELITE_APPEARANCE_TARGETS` constant in Python based on 8-week Milly Winner research
- Target distribution per position:
  - **RB**: #1 RB in 10/10 lineups (100%), Top 4 = 16/21 slots (76%), none below rank 9
  - **WR**: Top 5 = 20/26 slots (77%), only 1/26 outside top 10, #1 WR in 8/10 lineups
  - **QB**: Top 3 in 8/10 lineups (75%), none below rank 6
  - **TE**: Top 5 in 9/10 lineups, none below rank 9
  - **DST**: #1 in 5/10 lineups (50%), Top 3 in 8/10 lineups (75%)
- Constraints specify minimum/maximum appearances per elite player across 10 lineups

### Progressive Relaxation
- Detect infeasibility when optimization cannot find solution meeting all constraints
- Relax elite appearance constraints progressively starting with lowest-ranked elite players
- Relaxation sequence: rank 15 → 14 → 13 → ... → 2 (never relax #1 players)
- Continue relaxation until feasible solution found or all elite constraints removed
- Log relaxation decisions for debugging and analysis

### Baseline Lineup Exclusion
- "Best Smart Score" (lineup_number = -1) remains unchanged, generated separately
- "Best Proj" (lineup_number = -2) remains unchanged, generated separately
- Only the 10 user-requested lineups (lineup_number 1-10) use portfolio optimization
- Baseline lineups generated via existing single-lineup optimization with no elite constraints

### Constraint Integration
- Elite appearance constraints work alongside existing constraints:
  - Salary cap ($49K-$50K per lineup)
  - Position requirements (1 QB, 2 RB, 3 WR, 1 TE, 1 FLEX, 1 DST)
  - Team limits (max players per team)
  - Game limits (max players per game)
  - Existing stacking rules (QB+WR/TE, bring-back)
  - Exposure limits
- All existing constraint logic remains unchanged
- Elite constraints added as additional layer

### No UI Changes
- Frontend displays optimized lineups automatically with no modifications
- No distribution validation reports or UI components
- No configuration interface for elite targets
- Backend improvements transparent to frontend
- Existing LineupDisplay.tsx and related components unchanged

## Visual Design

No visual assets provided. Backend-only implementation with no UI changes required.

## Reusable Components

### Existing Code to Leverage

**Core Optimization Infrastructure:**
- `backend/services/lineup_optimizer_service.py` - Current single-lineup optimization
  - `_generate_single_lineup()` - PuLP problem setup, constraint building, solver invocation
  - `_add_position_constraints()` - Position requirement enforcement
  - `_add_team_constraints()` - Team limit constraints
  - `_add_game_constraints()` - Game limit constraints
  - `_add_stacking_constraints()` - QB+WR/TE stacking logic
  - `_add_exposure_constraints()` - Player exposure limits
  - `_validate_lineup()` - Lineup validation logic
  - PuLP integration patterns with CBC solver

**Data Structures:**
- `PlayerOptimizationData` dataclass - Player data for optimization
- `GeneratedLineup` schema - Lineup response format
- `OptimizationSettings` schema - User settings input

**Player Filtering:**
- `_prepare_players()` - Player filtering by Smart Score threshold, Tournament mode filters
- `_filter_by_threshold()` - Smart Score threshold filtering
- `_group_by_position()` and `_group_by_team()` - Player grouping utilities

**Elite Player Logic (partially reusable):**
- `_identify_elite_players()` - Currently identifies top 3-5 by Smart Score per position
- `_get_elite_player_ids()` - Returns set of elite player IDs
- Note: Will need modification to use projection-based ranking and top 15 threshold

**Baseline Generation:**
- `_generate_baseline_lineup()` - Pure optimization without diversity penalties
- Baseline patterns for "Best Smart Score" and "Best Proj" lineups

### New Components Required

**Portfolio Optimization Engine:**
- Multi-lineup simultaneous optimization problem
- Portfolio-level objective function maximizing total Smart Score across 10 lineups
- Decision variables: 10 sets of player selection variables (one per lineup)
- Why new: Existing code generates one lineup at a time; portfolio approach requires simultaneous solving

**Elite Appearance Constraint Builder:**
- Translate `ELITE_APPEARANCE_TARGETS` into PuLP constraints
- Constraints like "RB #1 must appear in >= 10 lineups" and "<= 10 lineups"
- Constraints like "Top 4 RBs must fill >= 16 of 21 RB slots across 10 lineups"
- Why new: Current system has no multi-lineup constraint logic; this is portfolio-level

**Progressive Relaxation Algorithm:**
- Infeasibility detection after optimization attempt
- Constraint relaxation sequence logic
- Iterative re-optimization with relaxed constraints
- Logging of which constraints were relaxed
- Why new: No existing relaxation logic; current system fails on infeasibility

**Elite Target Configuration:**
- `ELITE_APPEARANCE_TARGETS` constant defining per-position targets
- Data structure mapping position → rank → (min_appearances, max_appearances)
- Based on Milly Winner research findings
- Why new: No equivalent configuration exists; targets are research-driven

## Technical Approach

### Phase 1: Core Data Structures

**Elite Target Configuration:**
- Define `ELITE_APPEARANCE_TARGETS` constant at module level
- Structure: Dict[position, List[Tuple[min_appearances, max_appearances]]]
- Example for RB: [(10, 10), (8, 10), (7, 9), (6, 8), (5, 7), ...]
- Covers ranks 1-15 for each position based on research

**Modified Elite Player Identification:**
- Update `_identify_elite_players()` to use projection ranking instead of Smart Score
- Change threshold from top 3-5 to top 15 per position
- Return List[PlayerOptimizationData] sorted by projection rank
- Maintain existing logging for debugging

### Phase 2: Portfolio Optimization Foundation

**Multi-Lineup Problem Setup:**
- Create PuLP problem with 10 × N decision variables (10 lineups × N players)
- Variable naming: `lineup_{i}_player_{player_id}` for lineup i, player p
- Portfolio objective: Maximize sum of Smart Scores across all 10 lineups
- Apply per-lineup constraints (salary, positions, team limits) to each lineup independently

**Constraint Reuse:**
- Invoke existing `_add_position_constraints()` 10 times (once per lineup)
- Invoke existing `_add_team_constraints()` 10 times
- Invoke existing `_add_game_constraints()` 10 times
- Invoke existing `_add_stacking_constraints()` 10 times
- Invoke existing `_add_exposure_constraints()` across portfolio (cumulative exposure)

**Replace Diversity Penalties:**
- Remove `_add_diversity_penalty()` logic (no longer needed)
- Elite appearance constraints provide diversity via distribution requirements
- No overlap penalties between lineups

### Phase 3: Elite Appearance Constraints

**Constraint Generation:**
- For each position, iterate through ranks 1-15
- For each elite player at rank r, add constraint: `sum(lineup_i_player_p for i in 1..10) >= min_appearances[r]`
- For each elite player at rank r, add constraint: `sum(lineup_i_player_p for i in 1..10) <= max_appearances[r]`
- Example: RB #1 gets `sum >= 10` and `sum <= 10` (must appear exactly 10 times)

**Aggregate Constraints:**
- For position-level targets like "Top 4 RBs = 16/21 slots":
- Sum all appearances of top 4 RBs across all RB slots in 10 lineups
- Add constraint: `sum(lineup_i_player_p for i in 1..10, p in top_4_RBs) >= 16`
- Handle FLEX slot: RB in FLEX counts toward RB slot total

**Integration with Existing Constraints:**
- Elite constraints added after per-lineup constraints
- No modification to existing constraint functions
- Portfolio-level constraints supplement lineup-level constraints

### Phase 4: Progressive Relaxation

**Infeasibility Detection:**
- After `prob.solve()`, check `prob.status != pulp.LpStatusOptimal`
- If infeasible, trigger relaxation algorithm
- Log infeasibility and begin relaxation sequence

**Relaxation Algorithm:**
- Initialize relaxation_rank = 15 (start with lowest elite players)
- Loop: Remove constraints for players at rank relaxation_rank
- Re-solve optimization
- If still infeasible, decrement relaxation_rank and repeat
- If relaxation_rank reaches 1, all elite constraints removed (fallback to baseline optimization)
- If feasible, return solution with logging of relaxed ranks

**Constraint Removal:**
- Maintain list of active elite constraints with rank metadata
- Remove constraints from problem when rank is relaxed
- PuLP allows constraint removal via constraint name/reference

**Fallback:**
- If all elite constraints relaxed and still infeasible, fall back to single-lineup generation
- Generate 10 lineups one-at-a-time using existing `_generate_single_lineup()` logic
- Log warning that portfolio optimization failed entirely

### Phase 5: Integration and Testing

**API Endpoint Integration:**
- Modify `generate_lineups()` method to call new portfolio optimizer for lineups 1-10
- Keep `_generate_baseline_lineup()` calls unchanged for lineup_number -1 and -2
- Return combined list: [baseline_smart_score, baseline_proj, lineup_1, ..., lineup_10]
- Ensure response schema matches existing `List[GeneratedLineup]`

**Backward Compatibility:**
- Frontend expects `List[GeneratedLineup]` with lineup_number, players, total_salary, projected_score, projected_points, avg_ownership
- No changes to response schema or field types
- Lineup ordering: baselines first (negative numbers), then regular lineups by Smart Score DESC
- No breaking changes to existing endpoints

**Comprehensive Testing:**
- Unit tests for elite player identification (top 15 by projection)
- Unit tests for constraint generation from `ELITE_APPEARANCE_TARGETS`
- Unit tests for progressive relaxation logic
- Integration tests for portfolio optimization with various player pools
- Edge case tests: insufficient players, infeasible constraints, all relaxations exhausted
- Performance tests: ensure 10-lineup optimization completes in reasonable time (<30 seconds)

## Out of Scope

### Explicitly Excluded

**Multi-Lineup Count Support:**
- No scaling logic for 5, 15, 20, or other lineup counts
- Hardcoded to exactly 10 lineups
- Research calibrated for 10 lineups specifically

**Frontend Modifications:**
- No UI components for distribution validation
- No reports showing elite appearance target achievement
- No visualization of constraint relaxation
- No configuration interface for elite targets

**Runtime Configuration:**
- Elite appearance targets remain hardcoded in Python
- No API endpoints to modify targets dynamically
- No user-facing settings for elite distribution

**Additional Uniqueness Constraints:**
- No diversity constraints beyond elite appearance targets
- No additional uniqueness penalties or bonuses
- No supplementary differentiation mechanisms

**Mid-Optimization Handling:**
- No special timeout handling beyond existing behavior
- No interruption or cancellation logic
- No injury status updates during optimization runs

**Stacking Modifications:**
- No changes to existing stacking UI controls
- No enhancements to stacking logic
- QB+WR/TE and bring-back rules remain unchanged

**Baseline Lineup Changes:**
- "Best Smart Score" and "Best Proj" lineups remain completely unchanged
- No elite distribution applied to baselines
- Baselines generated separately via existing logic

### Future Enhancements (Not This Implementation)

- Dynamic elite appearance targets based on user preferences
- Scaling to other lineup counts (5, 15, 20+)
- UI reports showing distribution achievement and constraint relaxation details
- Machine learning to optimize elite targets per week/slate
- Integration with live injury feeds for mid-optimization updates
- Advanced diversity constraints (correlation limits, unique game stacks)

## Success Criteria

### Elite Player Distribution Accuracy
- Top Smart Score RB appears in 90%+ of generated lineups (target: 100%, allow 10% tolerance)
- Top 5 WRs fill 70%+ of WR slots across 10 lineups (target: 77%)
- Top 3 QBs appear in 70%+ of lineups (target: 75%)
- Elite players consistently appear at research-backed frequencies

### Optimization Performance
- Portfolio optimization completes in under 30 seconds for typical player pool (100-150 players)
- Progressive relaxation converges to feasible solution within 5 relaxation iterations
- 95%+ of optimization runs succeed without falling back to single-lineup generation

### Constraint Satisfaction
- All generated lineups meet salary cap ($49K-$50K)
- All generated lineups meet position requirements (1 QB, 2 RB, 3 WR, 1 TE, 1 FLEX, 1 DST)
- Existing stacking rules (QB+WR/TE) satisfied when enabled
- Team and game limits respected

### Backward Compatibility
- Frontend displays optimized lineups without errors
- API response schema unchanged (List[GeneratedLineup])
- Baseline lineups ("Best Smart Score", "Best Proj") unaffected
- No breaking changes to existing endpoints or data formats

### User Experience
- Lineups show improved elite player representation without manual intervention
- Smart Score totals remain competitive or improved vs. one-at-a-time generation
- No user-visible errors or degraded performance
- Transparent backend improvement with no learning curve

## Implementation Roadmap

### Phase 1: Core Data Structures (2-3 hours)
- Define `ELITE_APPEARANCE_TARGETS` constant with research-backed targets
- Structure: Dict[position, List[Tuple[min_appearances, max_appearances]]] for ranks 1-15
- Update `_identify_elite_players()` to use projection ranking and top 15 threshold
- Add helper function to parse targets into constraint-ready format
- Unit tests for elite player identification and target parsing

### Phase 2: Portfolio Optimization Foundation (3-4 hours)
- Create new method `_generate_portfolio_lineups()` for simultaneous 10-lineup optimization
- Set up PuLP problem with 10 × N decision variables (`lineup_i_player_p`)
- Implement portfolio objective: maximize sum of Smart Scores across all lineups
- Apply per-lineup constraints by invoking existing constraint methods 10 times
- Initial solve without elite appearance constraints (baseline portfolio optimization)
- Unit tests for multi-lineup problem setup and constraint application

### Phase 3: Elite Appearance Constraints (2-3 hours)
- Implement constraint generation from `ELITE_APPEARANCE_TARGETS`
- Add per-player appearance constraints (min/max appearances for each elite player)
- Add aggregate constraints (e.g., "Top 4 RBs = 16/21 slots")
- Handle FLEX slot counting toward position totals
- Integrate elite constraints into portfolio problem
- Unit tests for constraint generation and elite appearance enforcement

### Phase 4: Progressive Relaxation (2-3 hours)
- Implement infeasibility detection after portfolio optimization attempt
- Build relaxation algorithm: remove constraints for rank 15, 14, 13, ..., 2 sequentially
- Add logging for relaxation decisions (which ranks relaxed, why)
- Implement fallback to single-lineup generation if all relaxations fail
- Unit tests for relaxation sequence and fallback behavior

### Phase 5: Integration and Testing (1-2 hours)
- Modify `generate_lineups()` to call `_generate_portfolio_lineups()` for lineups 1-10
- Keep baseline lineup generation unchanged (`_generate_baseline_lineup()`)
- Combine baselines and portfolio lineups in response
- Comprehensive integration tests with real player data
- Edge case testing: insufficient players, infeasible constraints, various player pools
- Performance testing: measure optimization time for typical slates

**Total Estimated Effort:** 10-15 hours (aligns with initial 8-12 hour estimate, adjusted upward for comprehensive testing)

## Risk Mitigation

### Risk: Infeasibility Due to Conflicting Constraints
- **Mitigation:** Progressive relaxation algorithm relaxes elite constraints until feasible solution found
- **Fallback:** Single-lineup generation if all relaxations fail
- **Testing:** Edge case tests with minimal player pools and strict constraints

### Risk: Performance Degradation
- **Mitigation:** Portfolio optimization solves one problem (10 lineups) instead of 10 sequential problems
- **Expected:** Similar or better performance vs. iterative generation
- **Testing:** Performance benchmarks with typical player pools (100-150 players)

### Risk: Breaking Frontend Compatibility
- **Mitigation:** No changes to response schema or API endpoints
- **Testing:** Integration tests verify response format matches existing `List[GeneratedLineup]`
- **Verification:** Frontend displays lineups without errors

### Risk: Elite Targets Don't Match Research
- **Mitigation:** Targets hardcoded from 8-week Milly Winner analysis
- **Validation:** Compare generated lineup distributions to research findings
- **Adjustment:** Targets can be refined in code based on validation results

### Risk: Progressive Relaxation Degrades Elite Distribution
- **Mitigation:** Relaxation starts with lowest-ranked players (15 → 14 → 13), preserving top players
- **Monitoring:** Log relaxation decisions to track which constraints are frequently relaxed
- **Future:** Adjust targets if relaxation is too frequent

## Appendix: Research Foundation

### Milly Winner Analysis (8-Week 2025 Season)

**RB Distribution:**
- #1 RB appeared in 8/8 analyzed lineups (100%)
- Top 4 RBs filled 16/21 RB slots (76% of slots)
- No RB outside top 9 by ranking appeared
- Key insight: Elite RB dominance is absolute in winning lineups

**WR Distribution:**
- Top 5 WRs filled 20/26 WR slots (77% of slots)
- Only 1/26 WR slots filled by player outside top 10
- #1 WR appeared in 6/8 lineups (75%)
- Key insight: WR elite concentration slightly lower than RB but still dominant

**QB Distribution:**
- Top 3 QBs appeared in 6/8 lineups (75%)
- No QB outside top 6 by ranking appeared
- Key insight: QB position more concentrated at top than WR/TE

**TE Distribution:**
- Top 5 TEs appeared in 7/8 lineups
- No TE outside top 9 by ranking appeared
- Key insight: TE position shows clear elite tier

**DST Distribution:**
- #1 DST appeared in 4/8 lineups (50%)
- Top 3 DSTs appeared in 6/8 lineups (75%)
- Key insight: DST less concentrated than skill positions but top 3 still dominant

### Portfolio Optimization Rationale

**Problem with One-at-a-Time Generation:**
- Bonuses to elite players in objective function don't guarantee appearance frequency
- Diversity penalties conflict with elite player bonuses
- No mechanism to enforce "RB #1 in 8/10 lineups" constraint
- Elite players only appear 2-3 times despite 500-point bonuses

**Portfolio Solution:**
- Simultaneous optimization enforces appearance targets as hard constraints
- Elite appearance guaranteed via constraint satisfaction
- Diversity achieved through distribution requirements, not penalties
- Research-backed targets built directly into optimization problem

### Technical Implementation Notes

**PuLP Solver Considerations:**
- CBC solver (default) handles mixed integer programs efficiently
- Expected solve time: <30 seconds for 10 lineups × 100-150 players
- Decision variables: 10 × N binary variables (1000-1500 total)
- Constraints: ~500-1000 (per-lineup + portfolio-level)
- Memory: Minimal (standard PuLP problem size)

**Constraint Complexity:**
- Per-lineup constraints: 10 × (salary, positions, team, game, stacking) ≈ 10 × 20 = 200 constraints
- Elite appearance constraints: 5 positions × 15 ranks × 2 (min/max) = 150 constraints
- Aggregate constraints: 5 positions × 1-2 = 5-10 constraints
- Total: ~350-400 constraints (well within PuLP capacity)

**Expected Behavior Changes:**
- Elite players appear much more frequently (8-10 times vs. 2-3 times)
- Lineups more correlated at top (same elite players across lineups)
- Increased differentiation at mid-tier (different flex/DST selections)
- Overall Smart Score totals similar or improved vs. one-at-a-time generation
