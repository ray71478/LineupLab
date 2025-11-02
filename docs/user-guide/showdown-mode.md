# Showdown Mode User Guide

**Version:** 1.0
**Date:** November 2, 2025
**Feature:** DraftKings Showdown Contest Support

---

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Switching Contest Modes](#switching-contest-modes)
4. [Importing Showdown Data](#importing-showdown-data)
5. [Using Smart Score Engine](#using-smart-score-engine)
6. [Selecting Players](#selecting-players)
7. [Captain Selection](#captain-selection)
8. [Generating Showdown Lineups](#generating-showdown-lineups)
9. [Understanding Showdown Lineup Display](#understanding-showdown-lineup-display)
10. [Troubleshooting](#troubleshooting)
11. [FAQ](#faq)

---

## Overview

Showdown Mode enables you to optimize lineups for DraftKings single-game contests (Showdown slates). Unlike traditional Main Slate contests with 9 roster spots, Showdown contests feature:

- **6 Total Roster Spots**: 1 Captain (CPT) + 5 FLEX positions
- **$50,000 Salary Cap**: Same as Main Slate
- **Captain Multiplier**: Captain earns 1.5x points but costs 1.5x salary
- **Any Position Eligible**: QB, RB, WR, TE, K, and DST can fill any slot
- **Single Game**: All players from both teams in one game

### Key Concepts

**Main Slate:** Traditional DFS contests with multiple games, requiring 1 QB, 2 RB, 3 WR, 1 TE, 1 FLEX, 1 DST (9 positions).

**Showdown Slate:** Single-game contests with 1 CPT + 5 FLEX (6 positions), all players from one game.

**Captain (CPT):** Special roster position that multiplies both salary and points by 1.5x. The system automatically selects the optimal captain based on value, but you can lock a specific player as captain.

**FLEX:** Flexible roster position that can be filled by any eligible position (QB/RB/WR/TE/K/DST).

**Contest Mode:** The selected mode determines which data loads and which roster format applies. Each mode maintains independent datasets per week.

---

## Getting Started

### Accessing Showdown Mode

1. **Locate the Mode Selector**
   - Look for the toggle button group in the top navigation bar
   - It appears next to the Week Selector on all pages
   - Default mode is "Main Slate"

2. **Visual Identification**
   - Active mode displays with orange background (#ff6b35)
   - Inactive mode appears dimmed with gray background
   - Loading spinner appears during mode switches

### System Requirements

- Works on all pages: Home, Smart Score Engine, Player Selection, Lineup Generator
- Fully responsive: Desktop, tablet, and mobile
- Keyboard accessible: Tab to focus, Enter to select
- Screen reader compatible with ARIA labels

---

## Switching Contest Modes

### How to Switch Modes

**Desktop:**
1. Click the desired mode button ("Main Slate" or "Showdown")
2. Wait for the loading indicator (circular spinner)
3. Page data refreshes automatically within ~300ms
4. Active mode highlights in orange

**Mobile:**
1. Tap the desired mode button
2. Loading indicator appears next to buttons
3. Data reloads optimistically
4. Active mode updates immediately

### What Happens When You Switch Modes?

**Data Isolation:**
- Player selections cleared automatically
- Generated lineups cleared
- Data reloads for the selected mode
- Week selection preserved

**Performance:**
- Mode switch completes in < 500ms
- Optimistic UI updates for immediate feedback
- Data fetches happen asynchronously

**Example Workflow:**
```
1. User in Main Slate with Week 9 data
2. User clicks "Showdown"
3. Loading indicator appears (200ms minimum)
4. Player pool reloads with Showdown data for Week 9
5. Previous Main Slate selections cleared
6. Showdown mode ready to use
```

### When to Switch Modes

**Switch to Showdown when:**
- Building lineups for single-game DFS contests
- Analyzing Monday Night Football or Thursday Night Football
- Focusing on specific game matchups
- Leveraging captain strategy in GPP tournaments

**Switch to Main Slate when:**
- Building traditional multi-game lineups
- Optimizing Sunday main slate contests
- Using standard 9-position roster construction

---

## Importing Showdown Data

### Supported File Formats

Cortex supports **LineStar** Excel files (.xlsx) for showdown imports. The file structure is identical to Main Slate files, containing:

- Player Name
- Team
- Position (QB, RB, WR, TE, K, DST)
- Salary (base salary, not multiplied)
- Projection
- Ownership %
- Ceiling
- Floor

### Import Process

**Step 1: Select Showdown Mode**
```
1. Click "Showdown" in Mode Selector
2. Wait for mode switch to complete
```

**Step 2: Select Week**
```
1. Click Week Selector dropdown
2. Choose the week matching your LineStar file
3. Week determines which dataset stores the import
```

**Step 3: Import File**
```
1. Click "Import Linestar" button in navigation
2. Select your showdown Excel file
3. System validates file structure (auto-detects showdown format)
4. Import processes all players (~40-60 players expected)
5. Success message appears
```

**Step 4: Verify Import**
```
1. Navigate to Player Selection page
2. Verify player count matches file (both teams)
3. Check salaries and projections loaded correctly
4. Confirm positions include K if present in file
```

### File Requirements

**Valid Showdown File:**
- Single-game player pool (both teams)
- Approximately 40-60 players total
- Includes all eligible positions: QB, RB, WR, TE, K, DST
- Base salaries (not captain multiplied)
- LineStar standard column format

**Invalid File Triggers Error:**
- Multi-game slate (150+ players)
- Missing required columns
- Invalid position codes
- Corrupt Excel format

### Import Overwrites Previous Data

**Important:** Importing a showdown file for Week 9 will replace any existing showdown data for Week 9. You'll see a confirmation dialog:

```
⚠️ Import Confirmation
This will replace existing Showdown data for Week 9.
[Cancel] [Continue Import]
```

This design supports single-game-at-a-time usage. If you want to keep multiple games, import each to a different week number.

---

## Using Smart Score Engine

### Identical to Main Slate

The Smart Score Engine works **exactly the same** for showdown mode:

- Same 8 scoring factors (Projection, Value, Ownership, Vegas, Matchup, Trend, Regression, Consistency)
- Same weight profiles (Balanced, Contrarian, Projection-Heavy, Value-Heavy, Custom)
- Same customization sliders
- Same save/load functionality
- Same percentile filtering

### Workflow

**Step 1: Navigate to Smart Score Engine**
```
1. Ensure Showdown mode selected
2. Click "Smart Score" in navigation
3. Week selector shows current week
```

**Step 2: Select Weight Profile**
```
1. Choose from dropdown: Balanced, Contrarian, etc.
2. Or create custom profile with sliders
3. Adjust weights to match your showdown strategy
```

**Step 3: Calculate Scores**
```
1. Click "Calculate Smart Scores"
2. System applies formula to all showdown players
3. Scores appear in player table
4. Sort by Smart Score to see top values
```

**Step 4: Filter by Percentile (Optional)**
```
1. Use percentile slider to narrow player pool
2. Example: Top 50% only
3. Reduces lineup generation time
4. Focuses on high-value plays
```

### Showdown-Specific Strategies

**Contrarian Captain:**
- Use Contrarian profile (high ownership weight)
- Identify low-owned captain candidates
- Lock low-owned captain in lineup generator

**Projection-Heavy:**
- Use Projection-Heavy profile
- Emphasizes ceiling plays
- Good for GPP upside

**Value-Heavy:**
- Use Value-Heavy profile
- Finds salary-efficient players
- Maximizes FLEX value around expensive captain

**Tip:** The captain multiplier (1.5x) applies during lineup generation, not Smart Score calculation. Smart Scores reflect base player value.

---

## Selecting Players

### Player Selection Page in Showdown Mode

When in Showdown mode, the Player Selection page displays:

- All players from both teams in the single game
- Typically 40-60 players total
- All positions: QB, RB, WR, TE, K, DST
- Same filtering and sorting as Main Slate
- Smart Scores from Smart Score Engine

### Filtering Players

**Position Filter:**
- Select one or more: QB, RB, WR, TE, K, DST
- Useful for focusing on specific position strategies

**Team Filter:**
- Select one or both teams
- Example: Filter to home team only

**Smart Score Filter:**
- Use percentile slider from Smart Score Engine
- Shows only players above threshold

### Sorting Players

Click column headers to sort by:
- Smart Score (highest to lowest recommended)
- Salary (identify expensive/cheap options)
- Projection (find ceiling plays)
- Ownership (identify contrarian plays)

### Selection Workflow

**Tip:** In showdown mode, you don't manually select exactly 6 players. The optimizer generates full lineups based on constraints and Smart Scores. Use Player Selection to:

1. Review player pool
2. Identify captain candidates
3. Check salary distribution
4. Review ownership levels

---

## Captain Selection

### Automatic Captain Selection

By default, Cortex automatically selects the optimal captain for each lineup using a **value-based algorithm**:

```
Captain Value = (Smart Score × 1.5) / (Salary × 1.5)
```

This simplifies to:
```
Captain Value = Smart Score / Salary
```

**How it Works:**
1. Calculate captain value for all players
2. Select player with highest captain value
3. Ensure remaining salary supports 5 FLEX players under $50K cap
4. Generate lineup with optimal captain

**Captain Diversity:**
- System rotates through top 5 captain candidates
- Ensures lineup variety across 10 generated lineups
- Different captains create unique lineup constructions

### Locked Captain Feature

You can **lock a specific player as captain** if you have a strategic preference:

**Step 1: Navigate to Configuration Panel**
```
1. Go to Lineup Generator page
2. Locate Configuration Panel on right side
3. Find "Locked Captain" dropdown (Showdown mode only)
```

**Step 2: Select Captain**
```
1. Click "Locked Captain" dropdown
2. Dropdown populates with all players in your pool
3. Select your preferred captain (e.g., "Patrick Mahomes")
4. Dropdown displays: "Captain: Patrick Mahomes"
```

**Step 3: Generate Lineups**
```
1. Click "Generate Lineups"
2. All lineups use your locked captain
3. FLEX positions vary to maximize Smart Score
4. Salary constraint respects captain's 1.5x multiplier
```

**Step 4: Unlock Captain (Optional)**
```
1. Click "Locked Captain" dropdown
2. Select "None" to unlock
3. System reverts to automatic captain selection
```

### When to Lock Captain

**Lock Captain When:**
- You have strong conviction on a specific player
- Leveraging contrarian captain strategy
- Building around a game script (e.g., lock opposing QB in comeback game)
- Targeting specific player correlations (e.g., QB + bring-back WR)

**Use Automatic When:**
- Exploring optimal value across multiple captains
- Generating diverse lineup portfolio
- Unsure which captain to emphasize

### Captain Selection Edge Cases

**Scenario: No Valid Captain Found**
- **Error:** "Cannot fit any captain + 5 FLEX under $50k cap"
- **Cause:** Player pool salaries too high
- **Solution:** Adjust percentile filter to include cheaper players

**Scenario: Locked Captain Prevents Valid Lineups**
- **Error:** "Captain lock prevents valid lineup construction"
- **Cause:** Locked captain salary too high, insufficient remaining salary for 5 FLEX
- **Solution:** Unlock captain or select cheaper captain

---

## Generating Showdown Lineups

### Configuration Settings

**Showdown-Specific Settings:**

1. **Locked Captain** (optional)
   - Dropdown to select specific captain
   - Defaults to "None" (automatic selection)
   - Only visible in Showdown mode

2. **Number of Lineups**
   - Slider: 1-20 lineups
   - Recommended: 10 lineups for diversity

3. **Max Ownership %** (optional)
   - Filter out high-owned players
   - Useful for GPP contrarian strategy

4. **Smart Score Percentile Filter**
   - Carried over from Smart Score Engine
   - Example: Top 50% only

**Settings Not Applicable to Showdown:**
- **QB + WR Stacking**: Hidden in Showdown mode (single game makes stacking inherent)
- **Max Players Per Team**: Hidden (all players from same game)

### Generation Process

**Step 1: Configure Settings**
```
1. Open Configuration Panel
2. Set Number of Lineups (e.g., 10)
3. Optionally lock captain
4. Optionally set max ownership
5. Review settings summary
```

**Step 2: Generate Lineups**
```
1. Click "Generate Lineups" button
2. Progress bar appears
3. System optimizes each lineup sequentially:
   - Select captain (automatic or locked)
   - Apply 1.5x multiplier to captain
   - Select 5 FLEX positions
   - Enforce $50K salary cap
   - Maximize Smart Score
   - Ensure lineup uniqueness
4. Generation completes in < 30 seconds for 10 lineups
```

**Step 3: Review Results**
```
1. Lineups display in grid below
2. Each lineup shows:
   - 6 players (1 CPT + 5 FLEX)
   - Captain highlighted with badge
   - Captain multiplier displayed (1.5x)
   - Total salary (under $50K)
   - Total projected points
   - Total Smart Score
3. Review captain diversity across lineups
```

### Lineup Constraints

**Position Constraints:**
- Exactly 1 Captain (CPT)
- Exactly 5 FLEX
- Total: 6 positions

**Salary Constraint:**
- Total salary ≤ $50,000
- Captain salary = Base Salary × 1.5
- FLEX salaries = Base Salaries (no multiplier)
- Minimum salary: $48,000 (prevents unused salary)

**Scoring:**
- Captain points = Base Projection × 1.5
- FLEX points = Base Projections (no multiplier)
- Total lineup projection = CPT points + FLEX points

**Uniqueness:**
- Each lineup different from previous lineups
- Different captain or different FLEX combinations
- Prevents duplicate lineups

### Performance

**Expected Generation Time:**
- 10 lineups: ~18-20 seconds
- 5 lineups: ~9-10 seconds
- 20 lineups: ~36-40 seconds

**Progress Indicators:**
- Progress bar shows completion percentage
- Status text: "Generating lineup 3 of 10..."
- Loading spinner during generation

---

## Understanding Showdown Lineup Display

### Lineup Card Layout

Each generated lineup displays in a card format:

```
┌─────────────────────────────────────────┐
│ Lineup #1          Total: $49,800       │
│ Smart Score: 245   Proj: 127.5 pts      │
├─────────────────────────────────────────┤
│ [C] Patrick Mahomes   QB  KC  $12,000   │
│     (Captain 1.5x - Proj: 36.8 pts)     │
├─────────────────────────────────────────┤
│     Travis Kelce      TE  KC  $7,200    │
│     (Proj: 18.5 pts)                    │
├─────────────────────────────────────────┤
│     Tyreek Hill       WR  MIA $8,500    │
│     (Proj: 22.3 pts)                    │
├─────────────────────────────────────────┤
│     ... (3 more FLEX players)           │
└─────────────────────────────────────────┘
```

### Captain Visual Indicators

**Captain Badge:**
- [C] prefix before player name
- Bold font weight
- Larger font size
- Orange accent color (#ff6b35)

**Captain Multiplier Display:**
- Shows "Captain 1.5x" below name
- Displays multiplied projection
- Salary shown is already multiplied (1.5x base)

**Example:**
```
Patrick Mahomes (Base: $8,000 salary, 24.5 proj)
Displays as CPT: $12,000 salary, 36.8 proj
```

### FLEX Visual Indicators

**Standard Display:**
- No prefix badge
- Regular font weight and size
- White text color
- Shows base salary and projection

**Position Label:**
- Displays actual position (QB/RB/WR/TE/K/DST)
- Not labeled as "FLEX" (position shown instead)

### Lineup Metadata

**Top of Card:**
- Lineup number (e.g., "Lineup #1")
- Total salary: Sum of all 6 players (CPT multiplied, FLEX base)
- Total Smart Score: Sum of Smart Scores (base, not multiplied)
- Total projection: CPT projection (1.5x) + FLEX projections (1x)

**Bottom of Card (Optional):**
- Save lineup button
- Copy lineup button
- Lineup diversity indicators

### Reading Lineup Strategy

**High Captain, Low FLEX:**
- Expensive captain (e.g., $12K-$15K)
- Cheaper FLEX players to fit under cap
- Strategy: Leverage captain multiplier on elite player

**Balanced Captain:**
- Mid-range captain (e.g., $9K-$11K)
- Mix of mid-tier FLEX players
- Strategy: Spread value across roster

**Contrarian Captain:**
- Low-owned captain (ownership < 10%)
- Can afford higher-priced FLEX with salary savings
- Strategy: Differentiate from field

### Comparing Lineups

**Captain Diversity:**
- Review how many unique captains across 10 lineups
- Ideal: 4-5 unique captains
- Too many duplicates: Increase lineup count or unlock captain

**FLEX Overlap:**
- Note which FLEX players appear in multiple lineups
- High overlap = strong value plays
- Low overlap = deep player pool

**Salary Utilization:**
- Check how close to $50K cap
- $49.5K-$50K: Optimal (minimal waste)
- $48K-$49K: Acceptable
- < $48K: Review configuration (might be too restrictive)

---

## Troubleshooting

### Problem: Mode Selector Not Responding

**Possible Causes:**
1. Button disabled during loading
2. Browser issue
3. Network latency

**Solution:**
1. Wait for loading spinner to finish
2. Refresh browser page
3. Check browser console for errors

---

### Problem: Showdown Data Not Loading After Import

**Possible Causes:**
1. Import failed silently
2. Mode switched before import completed
3. Week mismatch

**Solution:**
1. Re-import file in Showdown mode
2. Verify Week Selector matches imported week
3. Check Player Selection page for player count
4. Review browser console for import errors

---

### Problem: No Players Showing in Player Selection

**Possible Causes:**
1. No data imported for selected week
2. Wrong mode selected
3. All players filtered out

**Solution:**
1. Verify Showdown mode selected
2. Check Week Selector matches imported week
3. Clear all filters (Position, Team, Smart Score)
4. Re-import data if no players found

---

### Problem: Captain Selection Fails

**Possible Causes:**
1. All players too expensive (can't fit CPT + 5 FLEX)
2. Percentile filter too restrictive
3. Locked captain salary too high

**Solution:**
1. Adjust Smart Score percentile filter (lower threshold)
2. Unlock captain and use automatic selection
3. Review player salaries in Player Selection
4. Import data with wider player pool

---

### Problem: Lineup Generation Stuck or Slow

**Possible Causes:**
1. Too many lineups requested (20+)
2. Very restrictive constraints
3. Small player pool

**Solution:**
1. Reduce number of lineups to 10
2. Relax max ownership constraint
3. Widen Smart Score percentile filter
4. Wait up to 60 seconds for large lineup sets

---

### Problem: All Lineups Have Same Captain

**Possible Causes:**
1. Captain locked in configuration
2. Only one viable captain in player pool
3. Constraints too restrictive

**Solution:**
1. Check Configuration Panel for locked captain (unlock if needed)
2. Increase player pool (widen percentile filter)
3. Generate more lineups (e.g., 15 instead of 10)
4. Adjust max ownership to include more captains

---

### Problem: Lineup Display Cut Off on Mobile

**Possible Causes:**
1. Mobile viewport too small
2. Browser zoom level incorrect
3. CSS rendering issue

**Solution:**
1. Rotate device to landscape
2. Reset browser zoom to 100%
3. Scroll within lineup card
4. Refresh page

---

### Problem: Main Slate Data Showing in Showdown Mode

**Possible Causes:**
1. Mode switch didn't complete
2. Cache issue
3. Data isolation bug

**Solution:**
1. Click Showdown button again
2. Refresh browser page
3. Clear browser cache
4. Hard refresh (Cmd+Shift+R or Ctrl+Shift+R)

---

## FAQ

### General Questions

**Q: What's the difference between Main Slate and Showdown mode?**

A: Main Slate is for traditional multi-game DFS contests with 9 roster spots (1 QB, 2 RB, 3 WR, 1 TE, 1 FLEX, 1 DST). Showdown is for single-game contests with 6 roster spots (1 CPT + 5 FLEX) where the captain earns 1.5x points but costs 1.5x salary.

---

**Q: Can I have both Main Slate and Showdown data for the same week?**

A: Yes! Each mode maintains independent datasets per week. For example, you can import Main Slate data for Week 9's Sunday games AND import Showdown data for Week 9's Monday Night Football game. Just switch modes before importing.

---

**Q: Do I need different LineStar files for Showdown vs Main Slate?**

A: Yes, but the file format is identical. LineStar provides separate exports for showdown slates. Cortex auto-detects the contest type based on player count and roster structure.

---

**Q: How does the captain multiplier work?**

A: The captain costs 1.5x their base salary and earns 1.5x their projected points. For example, a player with $8,000 salary and 20 projected points becomes $12,000 salary and 30 projected points as captain.

---

**Q: Should I manually pick my captain or use automatic?**

A: Automatic captain selection is recommended for most users. It uses value-based optimization (Smart Score / Salary) to find the optimal captain. Lock a captain when you have strong conviction on a specific player or contrarian strategy.

---

**Q: Why do my lineups all use expensive captains?**

A: The captain multiplier (1.5x points) often makes expensive players optimal captains because their increased projection outweighs the salary cost. This is expected. To explore cheaper captains, lock a mid-range captain or adjust ownership filters.

---

**Q: Can I use the same Smart Score weights for Showdown as Main Slate?**

A: Yes! Smart Score calculation is identical. However, you may want different strategies. For example, Contrarian profile works well for showdown GPPs to differentiate captain selection.

---

**Q: How many lineups should I generate for Showdown?**

A: Recommended 10 lineups. This provides good captain diversity and FLEX variety without taking too long. For larger GPP entries, generate 15-20 lineups.

---

**Q: Why can't I see stacking settings in Showdown mode?**

A: Stacking rules are hidden in Showdown mode because they're not applicable. Single-game contests inherently feature "stacking" since all players are from the same game. You can manually create game script stacks by locking specific captains.

---

**Q: What's a good captain diversity target?**

A: Across 10 lineups, aim for 4-5 unique captains. This provides differentiation without over-diversifying. If you see only 1-2 captains, generate more lineups or widen your player pool.

---

**Q: Can I export Showdown lineups to DraftKings?**

A: Currently, lineups display on screen. You'll need to manually enter them into DraftKings. Automated CSV export is planned for a future update.

---

**Q: How long does Showdown lineup generation take?**

A: Approximately 18-20 seconds for 10 lineups. This includes captain selection, FLEX optimization, and uniqueness checks. Performance may vary based on player pool size and constraints.

---

**Q: Why do I see kickers (K) in my Showdown player pool?**

A: Kickers are eligible in Showdown contests as FLEX players. They can also be selected as captain (though rarely optimal). Cortex treats them identically to other positions.

---

**Q: What happens if I switch modes mid-workflow?**

A: Player selections and generated lineups clear automatically. Week selection persists. Data reloads for the new mode. This prevents mixing Main Slate and Showdown players in the same lineup.

---

**Q: Can I save Showdown lineups?**

A: Yes! Use the "Save Lineup" button on lineup cards (same as Main Slate). Saved lineups store with contest_mode flag, so Showdown lineups remain separate from Main Slate lineups.

---

**Q: Are there keyboard shortcuts for mode switching?**

A: Not currently, but mode selector is keyboard accessible. Press Tab to focus the buttons, then Enter to activate. Arrow keys navigate between buttons.

---

### Technical Questions

**Q: Does Showdown mode affect my Main Slate data?**

A: No. Complete data isolation. Importing Showdown data for Week 9 does not affect Main Slate data for Week 9. Both modes maintain independent datasets.

---

**Q: What's the minimum/maximum salary for Showdown lineups?**

A: Maximum $50,000 (hard cap). Minimum $48,000 (prevents unused salary waste). The optimizer aims for $49,500-$50,000 for optimal salary utilization.

---

**Q: Can I generate more than 10 lineups?**

A: Yes, up to 20 lineups. Generation time scales linearly (20 lineups ≈ 36-40 seconds). For larger sets, generate in batches.

---

**Q: How does lineup uniqueness work?**

A: Each lineup must differ by either captain OR at least one FLEX player. The system prevents exact duplicates. Uniqueness checks use player IDs, not names.

---

**Q: Why does the loading spinner appear during mode switch?**

A: This provides visual feedback during asynchronous data fetching. The spinner shows for minimum 200ms even if data loads faster (better UX than flashing).

---

**Q: Can I run Showdown and Main Slate lineups simultaneously?**

A: Not in the same browser tab. Each tab maintains one active mode. Open multiple tabs to work on both simultaneously.

---

### Support

**Q: Where do I report a Showdown mode bug?**

A: Contact support with:
- Mode selected (Showdown)
- Week selected
- What you were doing when bug occurred
- Expected vs. actual behavior
- Screenshot or screen recording

---

**Q: How do I request Showdown mode enhancements?**

A: Submit feature requests through support portal. Common requests: Multi-game showdown support, captain correlation recommendations, automated DraftKings export.

---

**Q: Is there a limit to Showdown imports per week?**

A: No limit on number of imports. However, each import overwrites previous Showdown data for that week. To track multiple single-game slates, use different week numbers.

---

## Tips & Best Practices

### Data Management
1. **Import Showdown data right after LineStar publishes**
   - Single-game slates often have tight windows
   - Early import = more time for analysis

2. **Use descriptive week numbers**
   - Week 9 Monday Night → Import as Week 9
   - Week 10 Thursday Night → Import as Week 10 (different week)
   - Keeps data organized

3. **Verify import before building lineups**
   - Check player count (40-60 expected)
   - Spot-check salaries match LineStar file
   - Review all positions loaded (including K)

### Smart Score Strategy
4. **Adjust weights for single-game context**
   - Vegas/Matchup factors less relevant (all same game)
   - Projection and Value factors more important
   - Ownership matters for GPP differentiation

5. **Use Contrarian profile for captain leverage**
   - Low-owned captains differentiate lineups
   - High-owned captains are "chalky"
   - Mix both for balanced portfolio

### Captain Selection
6. **Start with automatic captain selection**
   - Let optimizer find value-optimal captain
   - Review captain diversity in results
   - Lock specific captain only if needed

7. **Lock captain for game script plays**
   - Example: Lock opposing team QB in shootout
   - Example: Lock RB in run-heavy game script
   - Example: Lock contrarian WR for leverage

8. **Understand captain multiplier impact**
   - 1.5x points makes high projections valuable
   - 1.5x salary makes cheap players risky as CPT
   - Sweet spot often $9K-$12K captains

### Lineup Generation
9. **Generate 10 lineups for most contests**
   - Good balance of diversity and speed
   - 4-5 unique captains expected
   - Review and manually adjust if needed

10. **Use max ownership filter for GPPs**
    - Filter out chalk plays (> 20-25% owned)
    - Creates contrarian lineups
    - Increases win equity in large fields

11. **Widen player pool for more diversity**
    - Lower Smart Score percentile threshold
    - Includes more captain candidates
    - Generates more unique lineup constructions

### Lineup Review
12. **Check salary utilization**
    - $49.5K-$50K: Excellent
    - $48K-$49K: Good
    - < $48K: Too restrictive, widen filters

13. **Review FLEX overlap patterns**
    - High overlap = value consensus
    - Low overlap = deep player pool
    - Target 2-3 "core" FLEX players across lineups

14. **Verify captain logic**
    - Does captain choice align with projections?
    - Is captain leveraging game script?
    - Does lineup construction support captain?

### Mobile Usage
15. **Use landscape orientation**
    - Full lineup card visibility
    - Easier captain vs FLEX distinction
    - Better table scrolling

16. **Tap to expand lineup details**
    - Full player names (not truncated)
    - Detailed projection breakdowns
    - Copy/save actions

---

**User Guide Complete**
**Last Updated:** November 2, 2025
**For Support:** Contact Cortex support team
**Version:** 1.0 (Initial Release)
