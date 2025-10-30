# Player Management User Guide

**Version:** 1.0
**Date:** October 29, 2025
**Scope:** Task 9.2 - User Documentation

---

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Main Features](#main-features)
4. [Step-by-Step Guides](#step-by-step-guides)
5. [Mobile Usage](#mobile-usage)
6. [Troubleshooting](#troubleshooting)
7. [FAQ](#faq)

---

## Overview

The Player Management feature allows you to review, filter, search, and manage player data from your DFS imports. Use this page to:

- View all players for a selected week
- Resolve unmatched players (who didn't match during import)
- Create global aliases for consistent player matching
- Filter and sort players by various criteria
- Search for specific players

### Key Concepts

**Matched Player:** A player whose imported name matched a canonical player in the system.

**Unmatched Player:** A player whose imported name did not match due to name variations or data inconsistencies. Requires manual mapping.

**Global Alias:** A mapping rule (e.g., "P. Mahomes" → "Patrick Mahomes") that will apply to all future imports.

---

## Getting Started

### Accessing Player Management

1. Navigate to your application dashboard
2. Click "Players" in the main navigation menu
3. The page loads with players from your currently selected week
4. View the week selector at the top to change weeks if needed

### Page Layout

```
┌─────────────────────────────────────────────┐
│  Player Management      [Week Selector ▼]   │
├─────────────────────────────────────────────┤
│                                             │
│  ⚠️  3 Unmatched Players                    │
│  ┌─────────────────────────────────────────┐│
│  │ P. Mahomes      KC  QB   $8000  [Fix]   ││
│  │ T. Hill         MIA WR   $7200  [Fix]   ││
│  │ J. Jefferson    MIN WR   $9000  [Fix]   ││
│  └─────────────────────────────────────────┘│
│                                             │
│  All Players (153)                          │
│  [🔍 Search] [Position ▼] [Team ▼]         │
│  ┌─────────────────────────────────────────┐│
│  │ Name   Team Pos  Salary  Proj  Own %    ││
│  │─────────────────────────────────────────││
│  │ Patrick KC  QB   $8000   24.5  35%   ▶  ││
│  │ Travis  KC  TE   $7500   18.2  28%   ▶  ││
│  │ ...                                     ││
│  └─────────────────────────────────────────┘│
└─────────────────────────────────────────────┘
```

---

## Main Features

### 1. Unmatched Players Alert

At the top of the page, you'll see an alert box if any players are unmatched:

- **Alert Color:** Orange/red for high visibility
- **Count Display:** Shows number of unmatched players
- **Action:** Click "Fix" on any card to open the mapping modal

**When Alert Disappears:** All players have been mapped

### 2. Player Table

The main table displays all players for the selected week with columns:

| Column | Description |
|--------|-------------|
| Name | Player's name |
| Team | 2-3 letter team abbreviation |
| Position | QB, RB, WR, TE, or DST |
| Salary | DFS salary in dollars |
| Projection | Projected fantasy points |
| Ownership | Expected ownership percentage |
| Status | Matched/Unmatched badge |
| Source | Import source (DraftKings, LineStar, etc.) |
| Last Updated | Import timestamp |

**Expand Row:** Click the chevron (>) to see additional details:
- Ceiling (best-case projection)
- Floor (worst-case projection)
- Full notes/comments
- Historical context

### 3. Search Players

To find a specific player:

1. Click the search box at the top of the table
2. Type the player's name (first name, last name, or partial match)
3. Results filter in real-time as you type
4. Click "X" button to clear search

**Example Searches:**
- "Patrick" → Finds Patrick Mahomes, Patrick Surtain, etc.
- "Mahomes" → Finds Patrick Mahomes
- "KC" → Searches in team column

### 4. Filter Players

Use filter controls to narrow down the player list:

**Position Filter:**
- Click "Position" dropdown
- Select one or more: QB, RB, WR, TE, DST
- Apply filter automatically

**Team Filter:**
- Click "Team" dropdown
- Select one or more NFL teams
- Applies across all positions

**Unmatched Filter:**
- Shows only unmatched players
- Useful for focusing mapping work

**Combine Filters:** All filters work together (e.g., QB + KC = QBs from Kansas City)

### 5. Sort Players

Sort by any column header:

- **Click Column Header:** Toggles sort order (A→Z or Z→A)
- **Sort Indicator:** Arrow shows current sort direction
- **Multi-Column Sort:** Not supported; sorting replaces previous sort

**Sortable Columns:**
- Name (alphabetical)
- Team (alphabetical)
- Position (QB > RB > WR > TE > DST)
- Salary (ascending/descending)
- Projection (ascending/descending)
- Ownership (ascending/descending)

---

## Step-by-Step Guides

### Guide 1: Map an Unmatched Player

**Scenario:** You see "3 Unmatched Players" alert. You want to fix one.

**Steps:**

1. **See the Alert**
   - Unmatched player cards display at top of page
   - Each shows: Name, Team, Position, Salary, [Fix] button

2. **Click Fix Button**
   - Opens "Map Player" modal dialog
   - Shows unmatched player details at top

3. **Review Suggestions**
   - Modal displays fuzzy-matched candidates with similarity scores
   - Usually the top suggestion is correct (85%+ match)
   - Scores range from 0% (no match) to 100% (perfect match)

4. **Select a Match**
   - Click the player name in the suggestions list
   - Selected player highlights in blue
   - Confirm selection displays player details

5. **Confirm Mapping**
   - Click "Confirm Mapping" button
   - System creates global alias (e.g., "P. Mahomes" → "Patrick Mahomes")
   - Modal closes automatically

6. **Verify Update**
   - Player moves from unmatched to matched section
   - Unmatched count decreases
   - Table updates in real-time

**Time Estimate:** 15-30 seconds per player

### Guide 2: Handle Players with Multiple Suggestions

**Scenario:** Unmatched player has several similar names in suggestions.

**Steps:**

1. **Open Mapping Modal** (see Guide 1, steps 1-2)

2. **Review All Suggestions**
   - List shows up to 5 matches with similarity scores
   - Higher scores = more confident matches
   - Read player names carefully

3. **Use Manual Search if Needed**
   - Search box at bottom of suggestions
   - Type player name to narrow results
   - Useful if top suggestions don't look right

4. **Select Best Match**
   - Click correct player name
   - Verify details match imported player
   - Check team, position match expectations

5. **Confirm**
   - Click "Confirm Mapping"
   - Alias created for future imports

### Guide 3: Skip Mapping (Optional)

**Scenario:** You're not sure which player is correct, and want to map later.

**Steps:**

1. **In Mapping Modal**
   - Click "Skip" button (bottom of modal)
   - Modal closes without creating alias
   - Player stays in unmatched list

2. **Later When Ready**
   - Re-open modal for same player
   - Map when you have more information

### Guide 4: Filter to Specific Position

**Scenario:** You only want to view QBs and TEs.

**Steps:**

1. **Click Position Filter Dropdown**

2. **Select Positions**
   - Check: QB
   - Check: TE
   - Uncheck: Others

3. **Apply**
   - Table updates automatically
   - Shows only selected positions

4. **Reset**
   - Click "Clear Filters" button
   - All positions shown again

### Guide 5: Find Highest Salary Players

**Scenario:** You want to see which QBs have the highest salary.

**Steps:**

1. **Filter by Position**
   - Select QB only

2. **Sort by Salary**
   - Click "SALARY" column header
   - Click again to toggle descending order
   - Highest salaries appear first

3. **Review List**
   - See top-paid QBs
   - Can expand rows for ceiling/floor details

### Guide 6: Create a Lineup (Post-Mapping)

**Scenario:** All players are mapped. Now you want to create a lineup.

**Steps:**

1. **Ensure All Mapped**
   - Unmatched alert should be gone
   - All players show "Matched" status

2. **Navigate to Lineup Builder**
   - Click "Lineups" in navigation
   - Select your week
   - Start building lineups using player data

3. **Use Player Info**
   - Reference salaries from player table
   - Use projections for player value
   - Check ownership for contrarian picks

---

## Mobile Usage

### Mobile Layout

The player management page is fully responsive on mobile devices:

**What Changes on Mobile:**
- Table columns compress for small screens
- Critical columns always visible: Name, Team, Position, Salary
- Additional columns accessible via horizontal scroll
- Filters appear as dropdown menus instead of inline
- Unmatched player cards stack vertically

### Mobile Workflows

#### View Players on Mobile

1. Open Player Management page
2. Swipe horizontally to see additional columns (Projection, Ownership, etc.)
3. Tap player name to expand row details
4. Scroll down to see all players

#### Map Unmatched Players on Mobile

1. **Unmatched Alert**
   - Appears as full-width card at top
   - Shows unmatched player cards stacked vertically

2. **Open Mapping Modal**
   - Tap "Fix" button on player card
   - Modal opens full-screen on mobile
   - Scroll within modal to see all content

3. **Select & Confirm**
   - Tap suggestion to select
   - Scroll down to find "Confirm Mapping" button
   - Tap to confirm

4. **Close Modal**
   - Tap "Back" or "X" button
   - Returns to main view

#### Filter on Mobile

1. **Tap Filter Buttons**
   - Position dropdown
   - Team dropdown
   - Filters apply immediately

2. **Clear Filters**
   - Tap "Clear All" button
   - Resets to showing all players

### Touch Optimization

All interactive elements on mobile meet accessibility standards:

- **Button Size:** Minimum 44x44 pixels (easy to tap)
- **Spacing:** 8+ pixels between elements
- **No Hover Interactions:** All features work by tapping
- **Full-Width Modals:** Easy to interact with
- **Large Text:** Readable without zoom

### Performance on Mobile

- Page loads quickly (< 3 seconds on 4G)
- Scrolling smooth and responsive
- Filtering updates in real-time
- No lag when mapping players

---

## Troubleshooting

### Problem: Unmatched Alert Stays Even After Mapping

**Possible Causes:**
1. Another player just imported
2. Page needs refresh
3. Mapping didn't save properly

**Solution:**
1. Click browser refresh button
2. Navigate away and back to Player Management
3. Try mapping again if still showing

### Problem: Can't Find Player in Search

**Possible Causes:**
1. Typo in search query
2. Different name in system vs. import
3. Player not in current week

**Solution:**
1. Check spelling of player name
2. Try searching by team abbreviation
3. Select different week from dropdown
4. Expand suggestions in mapping modal

### Problem: Mapping Suggestions Look Wrong

**Possible Causes:**
1. Player has common name (e.g., "Smith")
2. Imported name very different from canonical
3. Data inconsistency

**Solution:**
1. Use manual search in modal
2. Check multiple suggestions carefully
3. Skip for now and map when you have more info
4. Contact support if issue persists

### Problem: Table Not Showing All Columns

**Possible Causes:**
1. Mobile device with small screen
2. Browser window too narrow
3. Column visibility toggled off

**Solution:**
1. Widen browser window on desktop
2. Rotate phone to landscape (mobile)
3. Check column visibility toggle
4. Scroll table horizontally

### Problem: Filter Not Working

**Possible Causes:**
1. Wrong filter combination
2. No players match filter
3. Filter needs to be applied

**Solution:**
1. Click "Clear Filters" to reset
2. Apply one filter at a time
3. Check if results are empty (all players filtered out)

### Problem: Modal Scrolling Issues on Mobile

**Possible Causes:**
1. Modal content taller than screen
2. Need to scroll within modal, not page

**Solution:**
1. Scroll within the modal dialog
2. Don't try to scroll page behind modal
3. Close modal if content unreachable
4. Try landscape orientation

---

## FAQ

### General Questions

**Q: What's the difference between "matched" and "unmatched" players?**

A: Matched players had their imported name automatically matched to a player in the system. Unmatched players need manual review and mapping because their imported name didn't match closely enough.

**Q: Do I have to map all unmatched players?**

A: Recommended yes. Unmapped players can't be used in lineups. However, you can skip mapping temporarily and return later.

**Q: What happens after I map a player?**

A: A global alias is created. Future imports with the same name will automatically match to the mapped player.

**Q: Can I undo a mapping?**

A: Not directly in this feature. Contact support if you need to change a mapping.

**Q: How long does mapping take?**

A: Each player takes 15-30 seconds. A week with 5 unmatched players typically takes 2-5 minutes.

### Feature Questions

**Q: Can I search multiple players at once?**

A: No, search filters one at a time. Use filters to narrow by position/team instead.

**Q: Can I sort by multiple columns?**

A: No, clicking a column header replaces the previous sort.

**Q: Can I export player data?**

A: Not yet. That's planned for a future update.

**Q: Are there keyboard shortcuts?**

A: Tab navigates between interactive elements. Enter confirms. Escape closes modals.

### Technical Questions

**Q: Why does my search take so long?**

A: The system searches 150+ players. If search seems slow, try typing more characters.

**Q: What if the page doesn't load?**

A: Try refreshing. If problem persists, check your internet connection.

**Q: Can I use Player Management on multiple weeks?**

A: Yes, select a different week from the week selector dropdown.

**Q: Are my mappings saved if I close the browser?**

A: Yes, all mappings are saved to the server immediately.

### Support

**Q: Where do I report a bug?**

A: Contact support with:
- What you were doing when bug occurred
- Screenshot or video
- Your username
- What you expected to happen vs. what happened

**Q: How do I request a new feature?**

A: Submit feature request through support portal or email support team.

**Q: Is there a limit to how many players I can map?**

A: No, you can map as many as needed.

---

## Tips & Best Practices

1. **Map Unmatched Players Early**
   - Do it right after import
   - Easier to remember player names fresh

2. **Review Suggestions Carefully**
   - High similarity scores (85%+) are usually correct
   - Verify team and position match expectations

3. **Use Search for Common Names**
   - If multiple "Smith" or "Jones" suggestions
   - Search to narrow down

4. **Check Salary Reasonably**
   - Ensure mapped salary matches import
   - Prevents confusion later

5. **Expand Rows for Details**
   - Check ceiling/floor for risk assessment
   - Review notes from import source

6. **Use Filters to Focus**
   - Filter by position/team to reduce noise
   - Makes patterns easier to spot

7. **Mobile Tips**
   - Use landscape orientation for full table view
   - Tap player names to expand details
   - Scroll within modals, not page

---

**User Guide Complete**
**Last Updated:** October 29, 2025
**For Support:** Contact support team
