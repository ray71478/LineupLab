# Elite Player Distribution Optimization System

**Date**: 2025-10-31
**Status**: Research Phase
**Priority**: Critical
**Estimated Effort**: 8-12 hours

---

## Initial Idea

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
