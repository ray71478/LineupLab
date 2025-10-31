# Spec Requirements: Elite Player Distribution Optimization System

## Initial Description

The current lineup optimizer generates lineups one-at-a-time and uses "bonuses" to try to influence elite player selection. This approach is fundamentally broken:

1. **Elite players don't appear with correct frequency** - Even with 500-point bonuses, top Smart Score players (Jonathan Taylor #1 RB, Ja'Marr Chase top WR) only appear in 2-3 lineups instead of 8-10
2. **Bonuses don't affect optimization** - Multiple attempts to add bonuses to objective function have had zero impact on results
3. **Research-driven targets aren't met** - Milly Winner research shows specific distribution patterns that our system doesn't achieve

### Research Foundation

8 weeks of Milly Winner analysis from 2025 season shows clear patterns:

**Per Position Distribution:**
- **RB**: #1 RB in 8/8 lineups (100%), Top 4 = 16/21 slots (76%), none below 9th
- **WR**: Top 5 = 20/26 slots (77%), only 1/26 outside top 10, #1 WR in 6/8 lineups
- **QB**: Top 3 in 6/8 lineups (75%), none below 6th
- **TE**: Top 5 in 7/8 lineups, none below 9th
- **DST**: #1 in 4/8 lineups (50%), Top 3 in 6/8 lineups (75%)

### Proposed Solution

**Instead of:** Generate 10 lineups one-at-a-time with bonuses

**New approach:** Generate all 10 lineups simultaneously with distribution constraints

Use portfolio optimization to ensure elite players by Smart Score appear with correct frequency across all lineups, matching research-backed distribution targets.

---

## Requirements Discussion

### First Round Questions

**Q1:** How should we handle situations where we can't meet all elite appearance targets while respecting salary cap and position constraints?

**Answer:** Progressive relaxation starting with lowest-ranked elite players. If targets can't be met, relax the constraint for players ranked 15th, 14th, 13th, etc. in their position, working downward from lowest-ranked elite players rather than abandoning the constraint entirely.

**Q2:** Should we scale this approach to different lineup counts (5, 15, 20), or focus optimization on exactly 10 lineups?

**Answer:** Focus only on 10 lineups. No scaling logic needed. The elite appearance targets are calibrated specifically for 10 lineups based on the Milly Winner research.

**Q3:** The spec mentions optional stacking constraints. Should we modify or enhance the existing stacking UI controls?

**Answer:** Keep existing UI controls unchanged. No modifications to stacking logic. The current stacking implementation remains as-is.

**Q4:** Should we handle mid-optimization changes to player injury status (e.g., a player gets injured while optimization is running)?

**Answer:** Don't handle mid-optimization changes. Leave injury handling unchanged. Injury status is captured at the time data is imported; we don't re-check during optimization.

**Q5:** For player filtering, should we apply different thresholds for elite players by position, or use a uniform top-N approach?

**Answer:** Top 15 by projection per position (uniform across all positions). Same threshold applied consistently across QB, RB, WR, TE, and DST.

**Q6:** The spec mentions optional "uniqueness constraints" beyond elite appearance. Should we implement additional diversity/uniqueness constraints?

**Answer:** No additional uniqueness constraints. Follow the spec as written. Only implement the elite appearance targets, not additional constraints for further diversity.

**Q7:** Should we implement special timeout handling for optimization runs that exceed the 10-second target?

**Answer:** No special timeout handling needed. The existing timeout behavior remains unchanged. If optimization takes longer than expected, no special intervention is required.

**Q8:** Should the "Best Score" and "Best Proj" baseline lineups be included in the portfolio optimization, or kept completely separate?

**Answer:** "Best Score" and "Best Proj" lineups remain completely unchanged and are not part of portfolio optimization. These baseline lineups are generated separately and not subject to elite appearance constraints.

**Q9:** Should we add validation reports to the UI showing whether elite appearance targets were met?

**Answer:** No distribution validation reports in UI. Backend calculation is sufficient. Users will see improved elite player representation in their lineups without explicit validation reports.

**Q10:** Should the elite appearance targets be configurable at runtime, or hardcoded in Python?

**Answer:** Keep ELITE_APPEARANCE_TARGETS hardcoded in Python. No runtime configuration needed. Targets remain fixed based on research findings.

**Q11:** Are there any features, enhancements, or scope items you want to explicitly exclude from this implementation?

**Answer:** Implement everything in the spec - no deferrals or simplifications. Full implementation of the 5-phase plan as written.

---

## Existing Code to Reference

**Similar Features Identified:**
- Existing lineup optimization logic in `backend/services/lineup_optimizer_service.py`
  - Current single-lineup generation patterns
  - Salary cap constraint enforcement
  - Position constraint handling
  - Bonus/weight application mechanisms
  - Existing optimization solver integration

**Backend Patterns to Follow:**
- Use existing constraint-building patterns from current lineup_optimizer_service.py
- Follow existing optimization solver patterns (PuLP/scipy integration)
- Maintain consistency with current error handling and logging

---

## Follow-up Questions

No follow-up questions were needed. All clarifications were provided in the initial set of answers.

---

## Visual Assets

### Files Provided

No visual assets provided. Not needed for backend-only work. The implementation is focused on optimizing Python backend logic without UI changes.

### Visual Insights

Not applicable. No visual assets to analyze.

---

## Requirements Summary

### Functional Requirements

**Core Elite Player Distribution System:**
- Optimize all 10 lineups simultaneously using portfolio optimization
- Enforce elite appearance targets from Milly Winner research across the complete lineup set
- Elite players identified as top 15 by Smart Score projection per position
- Distribution targets derived from 8-week analysis of winning GPP strategies

**Infeasibility Handling:**
- Implement progressive relaxation algorithm starting with lowest-ranked elite players
- When targets cannot be met, relax constraints for rank-15 players first, then 14, 13, etc.
- Continue relaxation until feasible solution found or all elite constraints exhausted

**Optimization Scope:**
- Focus exclusively on exactly 10 lineups (no scaling to other lineup counts)
- Only apply elite appearance optimization to primary optimized lineups
- Keep "Best Score" and "Best Proj" baseline lineups completely separate and unchanged

**Stacking Constraints:**
- Maintain existing stacking UI and constraint logic without modification
- Integrate elite player distribution with existing stacking rules (they must work together)

**Injury Handling:**
- Use player injury status as captured at data import time
- Do not re-check or update injury status during optimization runs
- Treat injury status as static during the optimization process

**Player Filtering:**
- Identify top 15 players by projection for each position uniformly
- Apply same threshold (top 15) consistently across all positions (QB, RB, WR, TE, DST)
- These top-15 lists form the eligible pool for elite appearance targets

**Diversity Approach:**
- Implement elite appearance targets as specified (no additional uniqueness constraints)
- Elite distribution serves as primary diversity mechanism
- No supplementary constraints for further lineup differentiation

**Timeout Behavior:**
- Use existing timeout mechanisms without special handling
- No interruption or fallback logic if optimization exceeds expected duration
- Maintain current error handling for timeout scenarios

**Baseline Lineups:**
- "Best Score" lineup remains completely unchanged (no elite distribution applied)
- "Best Proj" lineup remains completely unchanged (no elite distribution applied)
- These baselines are generated via existing single-lineup optimization, separate from portfolio optimization

**Reporting:**
- No UI components for distribution validation
- No reports showing target achievement or constraint relaxation details
- Backend optimization produces improved elite player representation visible in final lineups

**Configuration:**
- Store elite appearance targets in `ELITE_APPEARANCE_TARGETS` constant in Python code
- Targets hardcoded based on research findings
- No runtime configuration interface or dynamic adjustment

### Implementation Scope

**In Scope:**
- Portfolio optimization algorithm for 10 lineups with elite appearance constraints
- Progressive relaxation mechanism for infeasible scenarios
- Integration with existing lineup optimization infrastructure
- Backend service modifications to support simultaneous multi-lineup optimization
- Constraint modeling for elite appearance targets
- Python-level configuration of elite targets
- Full 5-phase implementation plan as specified

**Out of Scope:**
- Frontend UI modifications or new components
- Runtime configuration interface for elite targets
- Validation reports or distribution visualization
- Modifications to stacking logic or UI
- Changes to "Best Score" and "Best Proj" baseline generation
- Special timeout handling or interruption logic
- Injury status updates during optimization
- Multi-lineup count support (only 10 lineups)
- Additional uniqueness constraints beyond elite distribution

### Technical Considerations

**Integration Points:**
- Modify `backend/services/lineup_optimizer_service.py` to support portfolio-level optimization
- Maintain compatibility with existing API endpoints that return lineups
- Ensure no breaking changes to frontend expectations

**Existing System Constraints:**
- Salary cap enforcement ($50,000 per lineup)
- Position constraints (QB, RB×2, WR×3, TE, FLEX, DST)
- Multi-position player eligibility handling
- Existing stacking constraint integration

**Technology and Patterns:**
- Use existing optimization solver (PuLP or scipy integration)
- Follow existing constraint-building patterns in lineup_optimizer_service.py
- Maintain consistency with current error handling and validation
- Use existing logging patterns for debugging and monitoring

**Code Patterns to Follow:**
- Constraint-building approach from current lineup generator
- Optimization solver initialization and configuration
- Result processing and validation patterns
- Error handling and edge case management from existing service

---

## Implementation Roadmap (5-Phase Plan)

### Phase 1: Core Data Structures
- Define elite player identification logic
- Create elite appearance target configuration
- Build constraint representation objects

### Phase 2: Portfolio Optimization Foundation
- Refactor optimizer to support multi-lineup simultaneous optimization
- Implement objective function for portfolio-level scoring
- Add constraint enforcement for all 10 lineups

### Phase 3: Elite Appearance Constraints
- Implement elite player identification (top 15 per position)
- Add constraint generation for appearance targets
- Integrate with portfolio objective function

### Phase 4: Progressive Relaxation
- Implement infeasibility detection
- Build relaxation algorithm starting with lowest-ranked elite players
- Test constraint relaxation sequence

### Phase 5: Integration and Testing
- Integrate with existing API endpoints
- Verify backward compatibility with frontend
- Comprehensive testing of all scenarios and edge cases

---

## Clarifications Applied

The following user clarifications have been incorporated into this requirements document:

1. ✅ Infeasibility handling: Progressive relaxation starting with lowest-ranked elite players
2. ✅ Lineup count: Focus only on 10 lineups (no scaling logic)
3. ✅ Stacking: Keep existing UI controls unchanged (no modifications)
4. ✅ Injury status: Don't handle mid-optimization changes (leave unchanged)
5. ✅ Player filtering: Top 15 by projection per position (uniform)
6. ✅ Diversity: No additional uniqueness constraints (follow spec as written)
7. ✅ Timeout: No special timeout handling needed
8. ✅ Baselines: "Best Score" and "Best Proj" unchanged, not part of portfolio optimization
9. ✅ Reports: No distribution validation reports in UI
10. ✅ Configuration: Keep ELITE_APPEARANCE_TARGETS hardcoded in Python
11. ✅ Scope: Implement everything in the spec (no deferrals or simplifications)

---

## Document Status

✅ **Complete** - All requirements gathered and documented
✅ **Ready for Specification Creation** - Ready to proceed with technical specification
