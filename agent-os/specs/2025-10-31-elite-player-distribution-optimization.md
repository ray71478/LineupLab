# Elite Player Distribution Optimization System

**Date**: 2025-10-31  
**Status**: Draft  
**Priority**: Critical  
**Estimated Effort**: 8-12 hours

---

## Problem Statement

The current lineup optimizer generates lineups one-at-a-time and uses "bonuses" to try to influence elite player selection. This approach is fundamentally broken:

1. **Elite players don't appear with correct frequency** - Even with 500-point bonuses, top Smart Score players (Jonathan Taylor #1 RB, Ja'Marr Chase top WR) only appear in 2-3 lineups instead of 8-10
2. **Bonuses don't affect optimization** - Multiple attempts to add bonuses to objective function have had zero impact on results
3. **Research-driven targets aren't met** - Milly Winner research shows specific distribution patterns that our system doesn't achieve

### Current State Analysis

**What's Broken:**
- `prob +=` approach to adding bonuses doesn't work as intended
- One-at-a-time generation with diversity penalties creates unpredictable results
- Stacking constraints override elite player selection
- No way to guarantee distribution across multiple lineups

**What We've Tried (All Failed):**
- Adding elite bonuses to objective: 2.0 → 10.0 → 500.0 (no effect)
- Reducing diversity penalties for elite players (no effect)
- Increasing overlap limits from 6 to 7 (no effect)
- Applying bonuses before/after strategy mode (no effect)

---

## Research Foundation

### Milly Winner Analysis (8 weeks, 2025 season)

**Per Position Distribution:**
- **RB**: #1 RB in 8/8 lineups (100%), Top 4 = 16/21 slots (76%), none below 9th
- **WR**: Top 5 = 20/26 slots (77%), only 1/26 outside top 10, #1 WR in 6/8 lineups
- **QB**: Top 3 in 6/8 lineups (75%), none below 6th  
- **TE**: Top 5 in 7/8 lineups, none below 9th
- **DST**: #1 in 4/8 lineups (50%), Top 3 in 6/8 lineups (75%)

**Quality Indicators:**
- Only 4/64 players finished below median projection (94% accuracy)
- 30/64 beat projections, 30/64 beat ceiling (high performers)
- All had 28+ snaps (with 3 rare exceptions across all positions)
- Only 20/72 owned 20%+ (mostly RBs - chalk RB is OK)

**Key Insight:** Winners use players who **actually finish top** at their positions, not necessarily who were projected highest.

---

## Solution Architecture

### Core Concept: Portfolio Optimization

**Instead of:** Generate 10 lineups one-at-a-time with bonuses  
**New approach:** Generate all 10 lineups simultaneously with distribution constraints

### System Design

```
1. FILTER PHASE
   ↓ Remove low-quality players
   
2. IDENTIFICATION PHASE  
   ↓ Rank remaining players by Smart Score
   
3. PORTFOLIO OPTIMIZATION PHASE
   ↓ Generate all N lineups with distribution constraints
   
4. VALIDATION PHASE
   ↓ Verify distributions match research targets
```

---

## Detailed Requirements

### 1. Player Pool Filtering (NEW)

**Before optimization, filter players to match research quality thresholds:**

```python
def _filter_player_pool(players):
    filtered = []
    for player in players:
        # Snap count filter (28+ snaps in recent games)
        if player.position != 'DST':
            if player.games_with_20_plus_snaps < 3:
                continue  # Skip players without snap history
        
        # Projection quality filter
        position_players = [p for p in players if p.position == player.position]
        sorted_by_projection = sorted(position_players, key=lambda p: p.projection, reverse=True)
        player_rank = sorted_by_projection.index(player) + 1
        
        if player_rank > 15:  # Only top 15 per position
            continue
        
        filtered.append(player)
    
    return filtered
```

**Filter Rules:**
- ✅ Players with 3+ games of 20+ snaps (proxy for 28+)
- ✅ Top 15 by projection at each position  
- ✅ No OUT/DOUBTFUL injury status (already implemented)
- ✅ Valid salary and Smart Score (already implemented)

### 2. Elite Player Identification (EXISTING - Keep)

**Current implementation works correctly:**
- Identifies top 3-5 players by Smart Score at each position
- Logs elite players correctly
- Returns `elite_by_position` dict

**No changes needed to this component.**

### 3. Multi-Lineup Portfolio Optimization (NEW - Core Change)

**Replace current one-at-a-time generation with simultaneous optimization:**

```python
def generate_lineups_portfolio(
    self,
    week_id: int,
    players: List[PlayerScoreResponse],
    settings: OptimizationSettings,
) -> List[GeneratedLineup]:
    """
    Generate all N lineups simultaneously with distribution constraints.
    
    Key differences from current approach:
    1. Creates variables for ALL lineups at once
    2. Adds min/max appearance constraints for elite players
    3. Optimizes total Smart Score across all lineups
    4. Guarantees distribution matches research targets
    """
    
    num_lineups = settings.num_lineups
    
    # Create binary variables: player_vars[lineup_num][player_id]
    player_vars = {}
    for lineup_num in range(num_lineups):
        player_vars[lineup_num] = {}
        for player in opt_players:
            var_name = f"lineup_{lineup_num}_player_{player.player_id}"
            player_vars[lineup_num][player.player_id] = pulp.LpVariable(var_name, cat='Binary')
    
    # Objective: Maximize TOTAL Smart Score across all lineups
    prob += pulp.lpSum([
        player.smart_score * player_vars[lineup_num][player.player_id]
        for lineup_num in range(num_lineups)
        for player in opt_players
    ])
    
    # Add appearance constraints for elite players
    for position, elite_players in elite_by_position.items():
        targets = ELITE_APPEARANCE_TARGETS[position]  # e.g., {1: 8, 2: 6, ...}
        
        for rank, player in enumerate(elite_players, 1):
            if rank in targets:
                min_appearances = targets[rank]
                # This player must appear in at least min_appearances lineups
                prob += pulp.lpSum([
                    player_vars[lineup_num][player.player_id]
                    for lineup_num in range(num_lineups)
                ]) >= min_appearances
    
    # Add per-lineup constraints (positions, salary, etc.)
    for lineup_num in range(num_lineups):
        self._add_lineup_constraints(prob, player_vars[lineup_num], ...)
    
    # Solve once to get all lineups
    prob.solve()
    
    return self._extract_lineups_from_solution(player_vars, num_lineups)
```

### 4. Elite Appearance Targets (NEW)

**Based on research, define minimum appearances for elite players:**

```python
ELITE_APPEARANCE_TARGETS = {
    'RB': {
        1: 8,  # #1 RB must appear in 8+ of 10 lineups (100% in research)
        2: 6,  # #2 RB must appear in 6+ of 10 lineups  
        3: 5,  # #3 RB must appear in 5+ of 10 lineups
        4: 4,  # #4 RB must appear in 4+ of 10 lineups
        5: 3,  # #5 RB must appear in 3+ of 10 lineups
        # Total: 26 appearances across top 5 (target: 16/20 = 80%)
    },
    'WR': {
        1: 7,  # #1 WR must appear in 7+ of 10 lineups (75% in research)
        2: 6,  # #2-5 distribute to hit 20/30 target
        3: 5,
        4: 4,
        5: 4,
        # Total: 26 appearances across top 5 (target: 20/30 = 67%)
    },
    'QB': {
        1: 5,  # Top 3 QBs must total 6+ appearances
        2: 4,  
        3: 3,
        # Total: 12 appearances min (target: 6/10 = 60% for top 3)
    },
    'TE': {
        1: 6,  # Top 5 TEs dominate
        2: 4,
        3: 3,
        4: 2,
        5: 2,
        # Total: 17 appearances (target: 7/10 lineups with top 5)
    },
    'DST': {
        1: 4,  # #1 DST in 4+ lineups (50% in research)
        2: 3,  # Top 3 total 6+ appearances
        3: 2,
        # Total: 9 appearances (target: 6/10 = 60%)
    },
}
```

**Adjustable based on num_lineups:**
If generating 5 lineups instead of 10, scale proportionally:
- RB #1: 8/10 → 4/5
- WR #1: 7/10 → 3.5/5 (round to 3 or 4)

### 5. Constraint Modifications

**Remove/Relax constraints that prevent elite players:**

```python
# REMOVE: Stacking constraint (or make it optional/soft)
# This was preventing elite players from appearing due to team/game conflicts

# KEEP: Position constraints (1 QB, 2 RB, 3 WR, 1 TE, 1 FLEX, 1 DST)
# KEEP: Salary constraints ($49K-$50K)
# KEEP: Team limits (max 4 per team)

# MODIFY: Diversity constraints
# Instead of preventing overlap between lineups, use distribution targets
# Elite players SHOULD overlap heavily across lineups
```

### 6. Baseline Lineups

**Keep existing baseline approach:**
- "Best Score" lineup: Pure Smart Score optimization (unconstrained)
- "Best Proj" lineup: Pure projection optimization (unconstrained)

These serve as reference points and don't need distribution constraints.

---

## Implementation Plan

### Phase 1: Player Pool Filtering (2 hours)
1. Add `_filter_player_pool()` method
2. Implement snap count filtering (28+ snap proxy)
3. Implement projection rank filtering (top 15)
4. Add logging for filtered players
5. Test with current player pool

**Files Modified:**
- `backend/services/lineup_optimizer_service.py`

**Testing:**
- Verify filter reduces pool by 40-60%
- Verify elite players pass filter
- Check logs show why players were filtered

### Phase 2: Portfolio Optimization Core (4 hours)
1. Create `generate_lineups_portfolio()` method
2. Implement multi-lineup variable creation
3. Add distribution constraint logic
4. Modify objective function for total score
5. Extract lineups from solution

**Files Modified:**
- `backend/services/lineup_optimizer_service.py`

**Testing:**
- Generate 10 lineups simultaneously
- Verify all lineups are feasible
- Check that constraints are satisfied

### Phase 3: Elite Distribution Targets (2 hours)
1. Define `ELITE_APPEARANCE_TARGETS` constants
2. Implement appearance counting
3. Add min/max appearance constraints
4. Scale targets based on num_lineups

**Files Modified:**
- `backend/services/lineup_optimizer_service.py`

**Testing:**
- Verify #1 RB appears 8+ times
- Verify top 5 WRs fill 20/30 slots
- Check all targets are met

### Phase 4: Constraint Cleanup (2 hours)
1. Remove/disable stacking constraints
2. Modify diversity penalty approach
3. Adjust team/game constraints for portfolio
4. Update salary bonus logic

**Files Modified:**
- `backend/services/lineup_optimizer_service.py`

**Testing:**
- Verify lineups still valid
- Check salary usage $49K-$50K
- Ensure team limits respected

### Phase 5: Integration & Testing (2 hours)
1. Update `generate_lineups()` to call new method
2. Keep baseline generation separate
3. Add comprehensive logging
4. Test with real player data

**Files Modified:**
- `backend/services/lineup_optimizer_service.py`

**Testing:**
- Generate full lineup set
- Verify distributions match targets
- Compare Smart Scores to old approach
- Check frontend display

---

## Success Criteria

### Must Have
- ✅ #1 RB by Smart Score appears in 8+ of 10 lineups
- ✅ Top 5 RBs fill 16+ of 20 RB slots (80%)
- ✅ Top 5 WRs fill 20+ of 30 WR slots (67%)
- ✅ All lineups are valid (positions, salary, team limits)
- ✅ Lineups maintain some diversity (not all identical)

### Should Have
- ✅ Top 3 QBs fill 6+ of 10 QB slots
- ✅ Top 5 TEs appear in 7+ lineups
- ✅ Top 3 DSTs fill 6+ of 10 DST slots
- ✅ Salary usage consistently $49K-$50K
- ✅ Smart Scores remain high (within 5% of baseline)

### Nice to Have
- ✅ User-adjustable distribution targets
- ✅ Visualization of player distributions
- ✅ Comparison report vs. research targets

---

## Risks & Mitigation

### Risk 1: Infeasibility
**Problem:** Too many constraints make problem unsolvable  
**Mitigation:** 
- Use minimum targets, not exact counts
- Make some constraints "soft" with penalties
- Start with loose targets and tighten gradually

### Risk 2: Performance
**Problem:** Optimizing 10 lineups at once is much slower  
**Mitigation:**
- Implement player pool filtering to reduce problem size
- Use CBC solver with time limits
- Cache elite identification across lineups
- Consider generating 5 lineups if 10 is too slow

### Risk 3: Quality Drop
**Problem:** Forcing distributions might lower Smart Scores  
**Mitigation:**
- Compare total Smart Score to current approach
- Allow user to adjust strictness of targets
- Keep baseline lineups as reference
- Accept small score drop for better distribution

### Risk 4: Stacking Strategy Loss
**Problem:** Removing stacking might hurt tournament strategy  
**Mitigation:**
- Make stacking optional, not disabled
- Implement "soft" stacking (bonus, not requirement)
- Test with/without stacking to measure impact
- Let user toggle stacking on/off

---

## Open Questions

1. **How strict should distribution targets be?**
   - Option A: Hard minimums (must hit exactly)
   - Option B: Soft targets (bonus for hitting)
   - **Recommendation:** Start with hard minimums, add soft option later

2. **Should we support custom distribution targets?**
   - Allow users to override research-based targets
   - **Recommendation:** Yes, add to OptimizationSettings

3. **What if Smart Score disagrees with research?**
   - E.g., Smart Score ranks Player X as #1 but he never wins
   - **Answer:** Trust Smart Score - we tune weights to make it accurate

4. **How to handle FLEX position distribution?**
   - Research shows 5x 3RB, 2x 4WR, 1x 2TE across 8 winners
   - **Recommendation:** Don't constrain FLEX, let optimizer choose

---

## Future Enhancements

### V2 Features (Post-Launch)
- User-adjustable distribution targets in UI
- Historical tracking: which players actually won
- Auto-tune: adjust targets based on your league's winners
- Exposure limits: cap player appearances (opposite of minimums)
- Correlation stacking: enforce QB+WR from same team when both elite

### V3 Features (Later)
- Multi-objective optimization: Smart Score + Ownership leverage
- Scenario analysis: "What if Player X is out?"
- Monte Carlo simulation: test lineup sets against random outcomes
- Machine learning: predict who will finish top based on features

---

## Appendix

### Current Code Issues

**Problem code (lines 669-677 in lineup_optimizer_service.py):**
```python
prob += pulp.lpSum([
    player.smart_score * player_vars[player.player_id]
    + elite_bonuses.get(player.player_id, 0) * player_vars[player.player_id]
    + (player.salary / 1000) * 0.6 * player_vars[player.player_id]
    for player in opt_players
]) + (salary_sum - MIN_SALARY) * salary_bonus_multiplier
```

**Why it doesn't work:**
- Applied once per lineup generation
- Other methods use `prob +=` which may override or conflict
- No guarantee bonuses actually affect solver
- One-at-a-time generation prevents distribution control

**Solution:**
- Remove bonus approach entirely
- Use hard constraints for distribution
- Generate all lineups simultaneously

### Research Data Summary

| Position | Slots | Top 5 Fill | Top 1 Freq | None Below |
|----------|-------|------------|------------|------------|
| RB       | 21    | 16 (76%)   | 8/8 (100%) | 9th        |
| WR       | 26    | 20 (77%)   | 6/8 (75%)  | 10th       |
| QB       | 10    | -          | -          | 6th        |
| TE       | 10    | 7 (70%)    | -          | 9th        |
| DST      | 10    | 6 (60%)    | 4/8 (50%)  | -          |

---

**End of Specification**

