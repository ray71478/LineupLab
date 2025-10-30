# Player Management Feature - Requirements & Design Decisions

**Date:** October 29, 2025
**Status:** Spec Shaping Complete
**Target Phase:** MVP Phase 1

---

## Design Direction

### Color Palette & Aesthetic
Inspired by **Factory.ai**, **Stripe**, and **21st.dev**:
- **Primary Dark Background:** Black (#0a0a0a or similar)
- **Accent Color:** Orange (#ff6b35 or #ff8c42) for interactive elements and CTAs
- **Secondary Surfaces:** Dark gray/charcoal (#1a1a1a) for cards and panels
- **Text:** White (#ffffff) for primary text, light gray (#e5e7eb) for secondary
- **Borders:** Orange accents on cards, subtle dark borders
- **Overall Aesthetic:** Clean minimalism with orange focal points, tight spacing, modern sans-serif typography

### Inspiration Sources
1. **Factory.ai**: Dark-mode-first, orange accents, tight typography, clean grid layouts
2. **Stripe**: Information hierarchy, card designs, smooth transitions, responsive breakpoints
3. **21st.dev**: Dark/light mode implementation, component organization, smooth scrolling

---

## Key Decisions - Core Flow

### 1. Fuzzy Matching Timing (Answered)
**Decision:** Fuzzy matching happens **during import**, with unmatched players flagged for manual review.
- Auto-match occurs during Data Import with high-confidence threshold
- Low-confidence matches go to `unmatched_players` table
- Users review and manually map unmatched players in Player Management page

**Rationale:** Minimizes friction—most players auto-match during import, users only need to fix outliers.

### 2. Unmatched Players Visibility (Answered)
**Decision:** Unmatched players displayed **prominently**.
- Separate "Unmatched Players" section at top of Player Management page
- Red/orange alert badge to draw attention
- Clear count: "5 players need manual mapping"
- Users must map all unmatched before lineup generation

**Rationale:** You need visibility into data quality issues immediately.

### 3. Navigation Structure (Answered)
**Decision:** Player Management lives on **separate `/players` page**.
- Not integrated into import flow
- Accessible from main navigation
- Route: `/players?week_id={week_id}`
- Week selector at top to switch between weeks

**Rationale:** Dedicated space for detailed player review and mapping work.

### 4. Unmatched Players Workflow (Answered)
**Decision:** Manual mapping happens in **dedicated modal**.
- Click player row or "Fix" button → modal opens
- Modal shows:
  - Unmatched player name, team, position, salary
  - Suggested fuzzy matches with confidence scores
  - Option to select best match or create new alias
  - Approve → player moves to matched section
- No inline editing; modal keeps focus clear

**Rationale:** Modal workflow prevents accidental edits and maintains focus.

---

## Player Table - Columns & Data

### Minimum Columns (Answered)
1. **Player Name** (with fuzzy match confidence indicator if applicable)
2. **Team**
3. **Position**
4. **Salary**
5. **Projection** (source: FE or ETR, from import data)
6. **Ownership %** (from import data)
7. **Notes** (from DKSalaries import)
8. **Smart Score** (calculated, will be added in Phase 2)
9. **Implied Team Total (ITT)** - NEW COLUMN
   - Data source: Vegas Lines API (coming in Phase 2)
   - Placeholder for now; will populate when API integrated
   - Shows implied total for player's team

10. **Last Week Comparison** - HISTORICAL DATA
    - Last week's salary (if available)
    - Last week's projection (if available)
    - Last week's ownership (if available)
    - Displayed as small secondary columns or expandable detail

11. **80-20 Rule Indicator** - NEW COLUMN
    - Pass catchers only (WR, TE, RB)
    - Checkbox or checkmark if scored ≥20 points in previous week
    - Empty if not applicable (e.g., QB, DST)
    - Used to identify regression risk in Smart Score

### Table Features
- **Sorting:** Clickable column headers (name, team, position, salary, projection, ownership, last week's data)
- **Filtering:** By position, team, unmatched status
- **Virtual Scrolling:** For 150-200 players per week; smooth performance on mobile
- **Expandable Rows:** Click row to see more details (ceiling, floor, all historical data)
- **Mobile Optimized:** Virtual scrolling, touch-friendly buttons, horizontal scroll for less critical columns

---

## Unmatched Players Section

### Location & Design
- **Top of page** before main player table
- **Prominent alert styling:** Orange/red alert box with count ("5 players need mapping")
- **Unmatched players list:** Cards or compact table rows with:
  - Player name, team, position, salary
  - "Fix" button → opens mapping modal
  - Confidence score if partial match detected

### Mapping Modal
- **Title:** "Map Player: [Unmatched Name]"
- **Player Info:** Name, team, position, salary
- **Suggestions:** List of fuzzy-matched candidates with similarity scores
- **Actions:**
  - Select suggested match → confirm
  - Create new alias (rare case)
  - Skip for now (comes back next time)
- **Submit:** "Confirm Mapping" button
- **Result:** Player moves to matched players table, real-time UI update

---

## Alias Management (Answered)

### Strategy: Global + Week-Specific
- **Global aliases:** Store across all weeks (e.g., "C. McCaffrey" → "Christian McCaffrey")
  - Apply to all future imports of that player
  - Reduce redundant mapping work over season
  - Table: `player_aliases` (original_name, matched_name, source, confidence_score)

- **Week-specific handling:** If same player appears in multiple weeks with different names
  - Use global alias if exists
  - If not, require mapping once per new variation

**Implementation:**
- On import: Check `player_aliases` for existing mappings
- If found: Auto-match with 100% confidence
- If not found: Use fuzzy matching; store result in `player_aliases` if user confirms

---

## Performance & Mobile (Answered)

### Virtual Scrolling
- **TanStack Table** with virtual scrolling for 150-200 players
- Renders only visible rows (~10-15 at a time)
- Smooth scrolling on mobile (390x844 viewport)
- No pagination; single scrollable view
- Touch-optimized (larger tap targets, smooth gestures)

### Mobile Layout
- **Responsive table:** Horizontal scroll for non-critical columns on mobile
- **Critical columns always visible:** Name, Team, Position, Salary
- **Optional columns (swipe to see):** Projection, Ownership, Last Week's Data, ITT
- **Modals:** Full-width on mobile, centered dialog on desktop
- **Virtual scrolling:** Especially important on mobile for performance

---

## Data Flow & Dependencies

### From Week Management
- Week ID, week number, season
- Week status (upcoming, active, completed)

### From Data Import System
- `player_pools` table: name, team, position, salary, projection, ownership, ceiling, floor, notes, source
- `unmatched_players` table: unmatched player records
- `player_aliases` table: existing mappings

### For Future Integration (Phase 2)
- **Vegas Lines API:** ITT data to populate implied team total column
- **Historical Stats API:** Last week's actual performance for 80-20 rule
- **Smart Score Engine:** Calculated smart_score column

### Database Tables Used
- `player_pools` (read/write)
- `unmatched_players` (read/write)
- `player_aliases` (read/write)
- `weeks` (read)
- `historical_stats` (read for last week's data once available)

---

## UI/UX Patterns

### Color Usage
- **Orange (#ff8c42):** Interactive elements, buttons, "Fix" buttons, alerts for unmatched
- **Black (#0a0a0a):** Primary background
- **Dark Gray (#1a1a1a):** Card backgrounds, table rows
- **White (#ffffff):** Primary text
- **Light Gray (#e5e7eb):** Secondary text, borders
- **Red accent (optional):** For 80-20 rule highlight or error states

### Typography
- **Headings:** Bold, large sans-serif (Factory.ai / Stripe style)
- **Body text:** Regular weight, light gray
- **Table headers:** Semibold, light gray
- **Interactive text:** Orange for links/buttons
- **Spacing:** Tight padding (Factory.ai style), consistent 4-8-12-16px scale

### Interactive Elements
- **Buttons:** Orange background with white text on hover, smooth transition
- **Links:** Orange text with underline animation (Factory.ai style)
- **Table rows:** Hover state with slight background lightening
- **Modals:** Dark background with orange accent border, smooth slide-in animation
- **Checkmarks:** For 80-20 rule indicator and mapping confirmations

### Cards & Surfaces
- **Player cards:** Dark gray background, subtle border (optional orange accent)
- **Unmatched alert:** Orange/red border, urgent styling
- **Modal cards:** Dark background, orange accent top or left border
- **Spacing:** Consistent padding, generous whitespace between sections

---

## Next Steps
1. Finalize visual mockups based on Factory.ai / Stripe / 21st.dev inspiration
2. Create detailed spec document with acceptance criteria
3. Implement Player Management page with all columns and features
4. Create mapping modal workflow
5. Integrate with existing Week Management and Data Import systems
