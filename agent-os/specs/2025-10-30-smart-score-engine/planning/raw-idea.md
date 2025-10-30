# Smart Score Engine - Raw Idea

**Feature:** Smart Score Engine  
**Phase:** Phase 1 - MVP  
**Priority:** High (Core feature for lineup optimization)  
**Created:** October 30, 2025

---

## Overview

The Smart Score Engine calculates a custom score for each player that combines multiple factors including projections, ownership, value, trends, and matchup context. This score serves as the foundation for the lineup optimizer.

---

## Key Requirements (from Roadmap)

### 8-Factor Formula:
1. **Projection** (DK or LineStar, user-selected)
2. **Ceiling Factor** (upside potential: Ceiling - Floor)
3. **Ownership Penalty** (reduce score for high ownership)
4. **Value Score** (Projection / Salary × 1000)
5. **Trend Adjustment** (target share, snap % increasing?)
6. **Regression Penalty** (80-20 rule if scored 20+ last week)
7. **Vegas Context** (ITT / league average)
8. **Matchup Adjustment** (opponent defensive rank)

### Configurable Weights (W1-W8):
- Sliders or input fields for each weight
- Real-time recalculation (update Smart Scores instantly)
- Visual feedback (show which players' scores changed most)

### Weight Profiles:
- Save current weights as named profile ("Base", "Contrarian", "Trend-Heavy")
- Load saved profiles from dropdown
- Default profile: "Base" (balanced weights)

### 80-20 Rule Configuration:
- Threshold input (default: 20 DK points)
- Penalty percentage input (default: 10% reduction)
- Toggle on/off per lineup generation

---

## Dependencies

- ✅ Player Management (completed)
- ✅ Data Import System (completed)
- ✅ Week Management (completed)
- Historical stats data (should be available from data import)

---

## Questions to Resolve

1. What is the exact formula for combining the 8 factors?
2. How are weights normalized (sum to 100? Independent multipliers?)
3. What data sources are needed for each factor?
4. How should the UI be organized (single page? modal? sidebar?)
5. What are the default weight values for "Base" profile?
6. How should trend data be calculated (compare to previous week? rolling average?)
7. Where should defensive rank data come from (manual import? API in Phase 2?)

