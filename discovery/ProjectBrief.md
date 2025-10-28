# Cortex - DFS Lineup Optimizer
## Project Brief

**Date:** October 26, 2025  
**Author:** Ray Bargas (with Mary, Business Analyst)  
**Status:** Discovery Phase  
**Version:** 1.0

---

## Executive Summary

**Cortex** is an intelligent DFS (Daily Fantasy Sports) lineup optimizer built for serious GPP (Guaranteed Prize Pool) tournament players who demand complete control over their roster construction strategy. Unlike black-box commercial tools, Cortex empowers users to define custom scoring algorithms (Smart Score), weigh multiple projection sources, incorporate historical trend analysis, and generate optimized DraftKings lineups with full transparency and configurability.

**The Core Problem:** Existing DFS tools are either too simplistic (manual spreadsheets) or too opaque (proprietary algorithms you can't control). Previous attempts to build a custom solution resulted in scope creep, technical debt, and an unusable application.

**The Solution:** A focused, maintainable, AI-assisted lineup optimizer that:
- Imports weekly player data from multiple sources (LineStar, DraftKings)
- Leverages comprehensive historical performance data (season-long trends, regression patterns)
- Calculates a configurable "Smart Score" weighing projections, ownership, value, trends, and Vegas context
- Generates optimized lineups using linear programming with user-defined constraints
- Provides a clean, dark-mode UI optimized for both desktop and mobile browsers
- Remains local-first for development, but architected for future cloud deployment

**Target Users:** Initially, Ray and one collaborator. Future: DFS players seeking advanced, customizable roster construction tools.

**Success Criteria:**
- Generate 10 optimized lineups in under 10 seconds
- Complete weekly workflow (data import → Smart Score tuning → lineup generation) in under 20 minutes
- Zero data import errors or state confusion
- Historical week replay with weight adjustments works flawlessly
- Mobile-friendly interface for on-the-go adjustments

**Key Differentiator:** Full control over the "brain" of the optimizer—users define the formula, adjust weights in real-time, and understand exactly why each lineup was constructed.

---

## Problem Statement

### Current State

The previous DFS optimizer attempt suffered from critical failures:

1. **Unresolved Data Import Errors**  
   - XLSX parsing broke after code changes
   - Unable to see calculations or roster outputs
   - App became completely unusable mid-season

2. **Lost Mental Model**  
   - Scope expanded beyond original vision
   - Too many features added without clear prioritization
   - Maintainer lost understanding of codebase architecture

3. **Technical Friction**  
   - Cloud deployment introduced mysterious caching issues
   - Server resets required after each push
   - Uncertainty about data state (was data loaded correctly?)
   - Debugging became time-consuming and frustrating

4. **Lack of Focus**  
   - App tried to support too many use cases
   - Core value (Smart Score + lineup generation) was buried
   - UI became cluttered and hard to navigate

5. **Mobile Unfriendly**  
   - Desktop-only design made it hard to use on phone
   - No responsive layout for checking lineups before kickoff

### Pain Points

- **Time wasted debugging** instead of focusing on DFS strategy
- **No confidence in data integrity** (is this week's data loaded correctly?)
- **Can't iterate quickly** on Smart Score formulas mid-week
- **Manual lineup building fallback** when optimizer failed
- **Lost historical context** (can't replay past weeks with new knowledge)
- **No collaboration** with partner (each person isolated)

### User Impact

Ray and his collaborator play high-stakes GPP tournaments every Sunday. When the optimizer fails:
- Fall back to less sophisticated commercial tools (lose competitive edge)
- Spend hours manually building lineups (time sink)
- Miss kickoff deadlines due to technical issues (lost entry fees)
- Can't learn from past weeks (no feedback loop to improve strategy)

### Urgency

**Week 9 of the 2024 NFL season is approaching.** A working optimizer is needed NOW to capture the remaining 10 weeks of the season and validate the approach before 2025.

---

## Proposed Solution

### Vision

**Cortex is the DFS player's "second brain"**—a focused, reliable, AI-assisted tool that combines multiple data sources, historical intelligence, and user-defined strategy into optimized lineups. It prioritizes simplicity, speed, transparency, and control.

### Core Concept

**Three-Layer Intelligence:**

1. **Data Layer (Input)**  
   - Import LineStar projections (early week)
   - Import DraftKings salaries + projections (mid-week, source of truth)
   - Import NFL season stats (historical brain: actual performance, trends)
   - Import Vegas lines + injury reports (context)

2. **Intelligence Layer (Smart Score)**  
   - Configurable formula weighing 8+ factors:
     - Projection (DK or LineStar)
     - Ownership (stay contrarian in GPPs)
     - Ceiling/Floor (upside potential)
     - Value (points per $1K salary)
     - Historical trends (target share increasing? Snap count up?)
     - Regression patterns (80-20 rule: if scored 20+ last week, regress)
     - Vegas context (implied team totals)
     - Matchup quality (opponent defense rank)
   - Save/load weight profiles ("Base", "Contrarian", "Trend-Heavy")
   - Real-time adjustments with instant recalculation

3. **Optimization Layer (Output)**  
   - Linear programming algorithm (DraftKings constraints)
   - Generate 10 diverse lineups (configurable count)
   - Exposure controls (min/max per player)
   - Stacking rules (QB + WR from same team)
   - Strategy modes (Chalk, Balanced, Contrarian)
   - Export to DraftKings CSV format

### Key Features

**Phase 1 (MVP - Local Development):**
- ✅ Week selector (1-18, navigate forward/backward)
- ✅ Multi-source data import (LineStar, DraftKings, NFL Stats)
- ✅ Player name normalization (composite key + fuzzy matching + manual mapping)
- ✅ Smart Score calculator (8-factor formula, configurable weights, save profiles)
- ✅ 80-20 regression rule (configurable threshold + penalty)
- ✅ Lineup optimizer (10 lineups, DK constraints, exposure controls)
- ✅ Dark mode UI (Material Design 3, Google Fonts/Icons)
- ✅ Responsive layout (desktop + mobile browser)
- ✅ Historical week replay (select past week, adjust weights, re-optimize)
- ✅ CSV export (DraftKings upload format)
- ✅ Local PostgreSQL database (persistent storage)

**Phase 2 (Historical Analysis & APIs):**
- API integrations (Vegas lines, injury reports)
- Contest results import (actual FPTS vs. projections)
- Variance analysis (how accurate were projections?)
- Performance analytics (which weight profiles performed best?)
- Trend visualization (charts for player progression/regression)

**Phase 3 (Cloud Deployment & Multi-User):**
- Deploy to Railway/Render
- User authentication
- Collaborator access (invite coworker)
- Shared player pools (optional)
- Contest result tracking (leaderboard integration)

### Differentiators

**vs. Commercial Tools (FantasyLabs, RotoGrinders, etc.):**
- ❌ Commercial: Black-box algorithms, no control  
  ✅ Cortex: Full transparency, define your own formula

- ❌ Commercial: Fixed projections, take it or leave it  
  ✅ Cortex: Blend multiple sources, weight as you see fit

- ❌ Commercial: No historical learning  
  ✅ Cortex: Season-long trends, replay past weeks

**vs. Manual Spreadsheets:**
- ❌ Spreadsheets: Slow, error-prone, no optimization  
  ✅ Cortex: Instant lineup generation, constraint solving

- ❌ Spreadsheets: Hard to collaborate  
  ✅ Cortex: Cloud-ready for team access

**vs. Previous Version:**
- ❌ Previous: Scope creep, technical debt, unusable  
  ✅ Cortex: Focused scope, clean architecture, reliable

---

## Target Users

### Primary User: Ray Bargas

**Profile:**
- Experienced DFS player (5+ years)
- Plays high-stakes GPP tournaments (large-field contests)
- Sunday Main Slate specialist (focus on one contest type)
- Data-driven decision maker (analyzes projections, ownership, trends)
- Tech-savvy (comfortable with Python, APIs, spreadsheets)
- Values control over tools (wants to understand "why" behind decisions)

**Goals:**
- Generate competitive lineups quickly (under 20 min per week)
- Stay contrarian (low ownership plays for tournament upside)
- Learn from historical data (what strategies worked?)
- Iterate rapidly (test different Smart Score weights)
- Access on desktop and mobile (finalize lineups pre-kickoff)

**Pain Points:**
- Commercial tools are too rigid (can't control the formula)
- Manual building is too slow (can't explore enough combinations)
- Previous optimizer was unreliable (data import failures)
- No way to validate strategies historically (replay past weeks)

**Success Looks Like:**
- Confidently load data each week (no import errors)
- Adjust Smart Score weights in real-time (see immediate impact)
- Generate 10 lineups in under 10 seconds
- Export to DraftKings and enter contest before kickoff
- Review past weeks to improve formula

---

### Secondary User: Collaborator

**Profile:**
- Ray's DFS partner (plays same contests)
- Provides alternative projections/analysis
- Less technical (prefers simple UI over code)
- Uses app occasionally (not daily)

**Goals:**
- Access Ray's player pool and lineups
- Understand Ray's Smart Score logic
- Generate own lineups with different weights
- Share notes on players (injury concerns, weather, etc.)

**Needs:**
- Simple, intuitive UI (no coding required)
- Read-only access to Ray's data (unless granted edit)
- Export lineups independently

---

### Future Users (Phase 3)

**Profile:**
- Serious DFS players seeking advanced tools
- Willing to learn complex workflows for competitive edge
- Comfortable with data imports (XLSX, CSV)
- Play GPP tournaments regularly
- Value transparency over simplicity

**Monetization Potential (Future):**
- Freemium model (free for local use, paid for cloud/multi-user)
- Subscription ($10-20/month for advanced features)
- One-time purchase (lifetime license)

---

## Goals & Metrics

### Business Goals

1. **Usability:** Ray completes full weekly workflow (import → tune → optimize → export) without errors
2. **Speed:** Lineup generation takes under 10 seconds
3. **Reliability:** Zero data import failures over 4-week test period
4. **Learning:** Historical replay enables strategy refinement (measurable improvement in contest results)
5. **Scalability (Future):** Cloud deployment supports 10+ concurrent users

### Key Performance Indicators (KPIs)

**MVP Success Metrics:**
- ✅ 100% data import success rate (no parsing errors)
- ✅ Generate 10 lineups in <10 seconds (performance target)
- ✅ Complete workflow in <20 minutes (time efficiency)
- ✅ Mobile UI fully functional (responsive design validation)
- ✅ Zero server resets required (eliminate caching issues)

**Phase 2 Metrics:**
- Historical replay used 3+ times per season (learning loop)
- Variance analysis shows <10% projection error (accuracy)
- API data fetched in <2 seconds (speed)

**Phase 3 Metrics:**
- 2+ active users (Ray + collaborator)
- Cloud uptime >99.5% (reliability)
- <500ms page load time (performance)

### Definition of Done (MVP)

**Cortex MVP is complete when:**
1. Ray can import Week 9 data (LineStar, DraftKings, NFL Stats) without errors
2. Smart Score calculates correctly for all players in pool
3. Ray can adjust 8 weight sliders and see updated Smart Scores in <1 second
4. Ray can save "Base" weight profile and load it later
5. Lineup optimizer generates 10 valid DraftKings lineups in <10 seconds
6. Ray can configure exposure limits (e.g., "Lamar Jackson in 3-7 lineups")
7. Ray can export lineups to DraftKings CSV format
8. Ray can select Week 8 (past week), adjust weights, and regenerate lineups
9. UI looks great on desktop (1920x1080) and mobile (iPhone 15 Pro)
10. App runs locally with PostgreSQL, no cloud deployment required

---

## MVP Scope

### Must-Have Features (Phase 1)

**1. Week Management**
- Create/select weeks 1-18 for current NFL season
- Week selector dropdown (persistent selection)
- Display current week prominently
- Navigate to past weeks for historical replay

**2. Data Import System**
- **Manual file selection** (user chooses LineStar vs. DraftKings)
- **Multi-sheet support** (DKSalaries: FE, ETR, ITT sheets)
- **User-prompted projection source** ("Which projections: FE or ETR?")
- **User-prompted ownership source** ("Which ownership: FE or ETR?")
- **Overwrite behavior** (latest upload replaces previous for that week)
- **Historical stats import** (NFL 2025 Stats.xlsx - comprehensive replace with 1-week backup)
- **Upload feedback** ("153 players imported from DKSalaries Week 9")

**3. Player Management**
- **Composite player key** (Name_Team_Position)
- **Fuzzy name matching** (handle "Christian McCaffrey" vs. "C. McCaffrey")
- **Manual mapping UI** (when auto-match confidence is low)
- **Alias registry** (store name variations for future auto-resolution)
- **Player table view** (sortable by Smart Score, salary, ownership, position)
- **Notes display** (show user notes from DKSalaries import)

**4. Smart Score Engine**
- **8-Factor Formula:**
  1. Projection (DK or LineStar, user-selected)
  2. Ceiling Factor (upside potential: Ceiling - Floor)
  3. Ownership Penalty (reduce score for high ownership)
  4. Value Score (Projection / Salary × 1000)
  5. Trend Adjustment (target share, snap % increasing?)
  6. Regression Penalty (80-20 rule if scored 20+ last week)
  7. Vegas Context (ITT / league average)
  8. Matchup Adjustment (opponent defensive rank)

- **Configurable Weights (W1-W8):**
  - Sliders or input fields for each weight
  - Real-time recalculation (update Smart Scores instantly)
  - Visual feedback (show which players' scores changed most)

- **Weight Profiles:**
  - Save current weights as named profile ("Base", "Contrarian", "Trend-Heavy")
  - Load saved profiles from dropdown
  - Default profile: "Base" (balanced weights)

- **80-20 Rule Configuration:**
  - Threshold input (default: 20 DK points)
  - Penalty percentage input (default: 10% reduction)
  - Toggle on/off per lineup generation

**5. Lineup Optimizer**
- **DraftKings Constraints:**
  - 9 positions: QB, RB×2, WR×3, TE, FLEX (RB/WR/TE), DST
  - $50,000 salary cap
  - Position eligibility (handle multi-position players)

- **User-Configurable Settings:**
  - Number of lineups (default: 10)
  - Strategy mode: Chalk / Balanced / Contrarian
  - Max players from single team (default: 4)
  - Max players from single game (default: 5)
  - Player exposure limits (optional: "Patrick Mahomes: 3-7 lineups")
  - Stacking rules (optional: "QB + at least 1 WR from same team")

- **Optimization Algorithm:**
  - Linear programming (PuLP or scipy.optimize)
  - Maximize total Smart Score across lineups
  - Enforce diversity (minimize player overlap between lineups)
  - Run in <10 seconds for 10 lineups

**6. Lineup Display & Export**
- **In-App Table View:**
  - Show all 10 lineups side-by-side
  - Display: Position, Player Name, Team, Salary, Smart Score, Ownership
  - Calculate: Total Salary, Total Smart Score, Avg Ownership per lineup
  - Highlight: Salary cap violations (shouldn't happen), high-ownership stacks

- **CSV Export:**
  - DraftKings upload format (TBD: exact column structure)
  - One-click download ("Download for DraftKings")
  - Save lineups to database (historical record)

**7. Historical Week Replay**
- **Select Past Week:** Dropdown to Week 8, Week 7, etc.
- **Load Historical Data:** Pull that week's player pool (projections, ownership, salary as they were)
- **Adjust Weights:** Modify Smart Score formula with current knowledge
- **Re-Optimize:** Generate new lineups based on adjusted weights
- **Compare:** (Optional) Show original lineups vs. new lineups
- **Learn:** Save new weight profiles for future use

**8. User Interface (Dark Mode)**
- **Design System:** Material Design 3
- **Typography:** Google Fonts (Inter or Roboto)
- **Icons:** Material Icons (clean, no emojis)
- **Color Palette:**
  - Background: `#0f0f1a` (deep navy/black)
  - Surface: `#1a1a2e` (panels)
  - Primary: `#00d4ff` (cyan - data emphasis)
  - Accent: `#7c3aed` (purple - AI features)
  - Text: `#e5e7eb` (light gray)
  - Success/Warning/Error: Green/Amber/Red

- **Responsive Layout:**
  - Desktop (1920x1080): Multi-column layout, side-by-side panels
  - Tablet (1024x768): Stacked panels, collapsible sidebar
  - Mobile (390x844): Single column, bottom navigation, touch-optimized

- **Key Screens:**
  - **Dashboard:** Week selector, data import status, Smart Score preview
  - **Player Pool:** Sortable table, filter by position/team, search by name
  - **Smart Score Config:** Weight sliders, profile management, 80-20 settings
  - **Lineup Generator:** Pre-generation settings, optimization button, progress indicator
  - **Lineup Results:** 10 lineups displayed, export button, save to history

**9. Data Persistence**
- **PostgreSQL Database (Local):**
  - `weeks` table (week ID, season, status)
  - `player_pools` table (week_id, player_name, team, position, salary, projection, ownership, ceiling, floor, notes, uploaded_at)
  - `historical_stats` table (player_name, week, team, actual_points, snaps, targets, etc.)
  - `vegas_lines` table (week_id, team, opponent, ITT, spread)
  - `generated_lineups` table (week_id, lineup_number, players JSON, total_salary, projected_score, created_at)
  - `weight_profiles` table (profile_name, weights JSON, created_at)
  - `player_aliases` table (alias_name, canonical_name_key)

- **Backup Strategy:**
  - Automated backup before historical stats import (keep 1 previous version)
  - Manual backup button (export entire database to SQL dump)

**10. AI-Assisted Features (Subtle Integration)**
- **Smart Defaults:** Pre-fill reasonable weight values based on historical performance
- **Projection Blending:** Offer to average FE + ETR projections if both exist
- **Anomaly Detection:** Flag players with unusual projection/ownership gaps
- **Exposure Suggestions:** "Based on ownership, recommend Lamar Jackson in 40% of lineups"
- **Post-Generation Insights:** "Lineup 3 is most contrarian (avg 8% ownership)"

---

### Out of Scope (MVP)

**Phase 2 Features (Deferred):**
- ❌ API integrations (Vegas lines, injury reports - use manual imports for now)
- ❌ Contest results import (actual FPTS comparison)
- ❌ Variance analysis (projection accuracy charts)
- ❌ Performance analytics (which weight profiles won most?)
- ❌ Trend visualization (line charts for player progression)
- ❌ Automated data refresh (manual uploads only in MVP)

**Phase 3 Features (Future):**
- ❌ Cloud deployment
- ❌ User authentication
- ❌ Multi-user access
- ❌ Shared player pools
- ❌ Real-time collaboration
- ❌ Contest leaderboard integration
- ❌ Payment processing (if monetized)

**Never in Scope:**
- ❌ Support for non-DraftKings platforms (FanDuel, Yahoo, etc.)
- ❌ Non-NFL sports (NBA, MLB, NHL)
- ❌ Cash game strategies (focus is GPP only)
- ❌ Non-Sunday slates (Thursday Night, Monday Night, Showdown)
- ❌ Automated contest entry (user exports CSV, uploads manually)

---

## Post-MVP Vision

### Phase 2: Historical Analysis & API Integration (Weeks 12-16, 2024)

**Goals:**
- Automate data fetching (reduce manual imports)
- Enable deep learning from historical performance
- Validate Smart Score accuracy

**Features:**
- **Vegas Lines API:** Auto-fetch ITT, spreads (update hourly)
- **Injury Report API:** Real-time injury status (ESPN or FantasyData)
- **Contest Results Import:** Upload DraftKings contest CSV, compare actual vs. projected
- **Variance Analysis Dashboard:**
  - Player-level: "CMC projected 23, scored 31 (+8)"
  - Lineup-level: "Lineup 3 scored 182 (top 5%)"
  - Week-level: "Week 9 projections were 12% high on average"
- **Performance Analytics:**
  - "Contrarian profile won 3 of 5 weeks"
  - "80-20 rule saved you from 14 busts"
  - "Target share trends correctly predicted 8 breakouts"
- **Trend Visualization:** Line charts for player snap %, target share, ownership over time

**Success Metrics:**
- API data fetched in <2 seconds
- Contest results imported for 100% of weeks played
- Variance analysis shows Smart Score outperforms baseline projections by 5%+

---

### Phase 3: Cloud Deployment & Multi-User (2025 Season)

**Goals:**
- Enable collaboration with partner
- Expand to broader DFS community
- Generate revenue (optional)

**Features:**
- **Cloud Infrastructure:**
  - Deploy to Railway or Render
  - PostgreSQL hosted database
  - Redis for caching (solve previous caching issues)
  - Docker containerization (consistent environments)

- **User Authentication:**
  - Email/password login (Auth0 or Supabase)
  - OAuth (Google, Apple)
  - Session management (JWT tokens)

- **Multi-User Access:**
  - Invite collaborator by email
  - Role-based permissions (owner, editor, viewer)
  - Private player pools (isolated per user)
  - Shared player pools (optional, for teams)

- **Collaboration Features:**
  - Shared notes on players
  - Comment threads ("Watch the weather in Buffalo")
  - Lineup comparison ("Your lineup vs. mine")
  - Contest result sharing (who won this week?)

- **Monetization (Optional):**
  - Free tier: Local use only
  - Pro tier ($15/month): Cloud access, multi-user, API integrations
  - Team tier ($50/month): 5 users, shared pools, advanced analytics

**Success Metrics:**
- 10+ active users (beyond Ray + collaborator)
- 99.5% uptime
- <500ms page load time
- $500+ MRR (if monetized)

---

## Technical Considerations

### Technology Stack

**Front-End:**
- **Framework:** React 18 + Vite (fast, modern, widely supported)
- **UI Library:** Material-UI (MUI) or Tailwind CSS + Headless UI
- **State Management:** Zustand or React Context (lightweight, no Redux complexity)
- **Data Fetching:** TanStack Query (React Query) for API calls and caching
- **Tables:** TanStack Table or AG Grid (sortable, filterable, performant)
- **Forms:** React Hook Form + Zod (validation)
- **Charts (Phase 2):** Recharts or Chart.js (trend visualization)

**Back-End:**
- **Framework:** FastAPI (Python 3.11+)
- **ORM:** SQLAlchemy (PostgreSQL models)
- **Migrations:** Alembic (database versioning)
- **XLSX Processing:** pandas + openpyxl (multi-sheet Excel imports)
- **Optimization:** PuLP or scipy.optimize (linear programming for lineup generation)
- **APIs (Phase 2):** httpx (async HTTP client for Vegas/injury APIs)

**Database:**
- **Local:** PostgreSQL 15 (via Homebrew or Docker)
- **Cloud (Phase 3):** PostgreSQL on Railway/Render (same schema, easy migration)
- **Caching (Phase 3):** Redis (session management, API response caching)

**Development Tools:**
- **Version Control:** Git + GitHub
- **Code Quality:** Ruff (Python linting), ESLint (JavaScript)
- **Testing:** pytest (backend), Vitest (frontend)
- **Containerization:** Docker + Docker Compose (local development, cloud deployment)

---

### Architecture Overview

**Local-First Design:**

```
┌─────────────────────────────────────────────────────┐
│                   FRONT-END (React)                  │
│  - Dashboard, Player Pool, Smart Score Config       │
│  - Lineup Generator, Results Display                │
│  - Responsive UI (Desktop + Mobile)                 │
└─────────────────────────────────────────────────────┘
                          ↓ HTTP/REST API
┌─────────────────────────────────────────────────────┐
│                 BACK-END (FastAPI)                   │
│                                                      │
│  ┌────────────────────────────────────────────┐   │
│  │  API Endpoints                              │   │
│  │  - /weeks (list, create, select)           │   │
│  │  - /import (LineStar, DK, NFL Stats)       │   │
│  │  - /players (list, filter, map aliases)    │   │
│  │  - /smart-score (calculate, update weights)│   │
│  │  - /optimize (generate lineups)            │   │
│  │  - /export (DraftKings CSV)                │   │
│  └────────────────────────────────────────────┘   │
│                                                      │
│  ┌────────────────────────────────────────────┐   │
│  │  Core Services                              │   │
│  │  - DataImporter (parse XLSX, normalize)    │   │
│  │  - PlayerMatcher (fuzzy match, aliases)    │   │
│  │  - SmartScoreCalculator (8-factor formula) │   │
│  │  - LineupOptimizer (PuLP, constraints)     │   │
│  │  - HistoricalAnalyzer (trends, regression) │   │
│  └────────────────────────────────────────────┘   │
│                                                      │
└─────────────────────────────────────────────────────┘
                          ↓ SQLAlchemy ORM
┌─────────────────────────────────────────────────────┐
│              DATABASE (PostgreSQL)                   │
│  - weeks, player_pools, historical_stats            │
│  - generated_lineups, weight_profiles               │
│  - player_aliases, vegas_lines                      │
└─────────────────────────────────────────────────────┘
```

**Cloud-Ready Principles:**
- Stateless API (no server-side sessions in MVP)
- Environment-based configuration (local vs. cloud database URLs)
- Docker containerization (same code runs locally and in cloud)
- API-first design (front-end and back-end communicate only via REST)

---

### Platform Requirements

**Development Environment:**
- macOS (Ray's primary machine)
- Python 3.11+ (via pyenv)
- Node.js 20+ (via nvm)
- PostgreSQL 15 (via Homebrew or Docker)
- Git + GitHub

**Deployment (Phase 3):**
- Railway or Render (PaaS, Python + PostgreSQL support)
- Docker images (front-end + back-end)
- PostgreSQL hosted database (included with Railway/Render)
- Redis (for caching, optional)

---

### Data Flow

**Weekly Workflow (MVP):**

1. **Monday (Early Week):**
   - User uploads `LineStar_Football_WK9.xlsx`
   - App parses, stores in `player_pools` (week_id=9, source="LineStar")
   - Smart Score calculates using LineStar projections

2. **Wednesday (Mid-Week):**
   - User uploads `DKSalaries Week 9.xlsx` (FE, ETR, ITT sheets)
   - App prompts: "Which projections: FE or ETR?" → User selects "FE"
   - App prompts: "Which ownership: FE or ETR?" → User selects "FE"
   - App parses, **overwrites** LineStar data (same week_id=9, now source="DraftKings")
   - Smart Score recalculates using DK projections

3. **Friday-Sunday (Refinement):**
   - User uploads DKSalaries again (10-20 times as ownership updates)
   - Each upload overwrites previous (always latest data)
   - User adjusts Smart Score weights, tests lineup outputs

4. **Sunday (Pre-Kickoff):**
   - Final DKSalaries upload (30 min before kickoff)
   - User configures lineup generation settings (10 lineups, contrarian, exposure limits)
   - User clicks "Generate Lineups" → Optimizer runs (<10 sec)
   - User reviews lineups, exports CSV, uploads to DraftKings

5. **Weekly (Historical Update):**
   - User uploads `NFL 2025 Stats.xlsx` (now includes Week 8 actual results)
   - App backs up previous version, replaces entire `historical_stats` table
   - Smart Score now has Week 8 data for trend analysis (Week 9 projections)

**Historical Replay Workflow:**

1. User selects "Week 8" from dropdown
2. App loads Week 8 player pool (projections, ownership, salary from that week)
3. App loads NFL Stats through Week 7 (historical context as it was)
4. User adjusts Smart Score weights ("What if I weighted ownership more?")
5. User clicks "Generate Lineups" → Optimizer runs with new weights
6. App shows 10 new lineups (compare vs. what was actually generated Week 8)
7. User saves new weight profile ("Hindsight 2024")

---

## Constraints & Assumptions

### Constraints

**Budget:**
- MVP: $0 (local development only, no cloud costs)
- Phase 2: ~$50-100/month (API subscriptions for Vegas lines, injuries)
- Phase 3: ~$50-200/month (Railway/Render hosting, database, Redis)

**Timeline:**
- MVP Target: 4 weeks (ready by Week 12 of 2024 NFL season)
- Phase 2: 4 additional weeks (before 2024 season ends)
- Phase 3: 2025 off-season (before 2025 NFL season starts)

**Platform:**
- Must run on macOS (Ray's primary machine)
- Must work in Chrome/Safari (desktop and mobile browsers)
- No native mobile app (web-only for now)

**Data Sources:**
- LineStar, DraftKings, and NFL Stats files are **manually curated** (no automated scraping)
- Ray has access to necessary APIs (Vegas lines, injuries) but not integrated in MVP
- No live odds or real-time data feeds (static weekly imports)

**Scope:**
- **DraftKings only** (no FanDuel, Yahoo, etc.)
- **NFL only** (no NBA, MLB, NHL)
- **Sunday Main Slate only** (no Showdown, Thursday Night, Monday Night)
- **GPP only** (no cash game strategies)

---

### Assumptions

**User Behavior:**
- Ray will upload data weekly (no automation required in MVP)
- Ray will manually curate player pools (pre-filter before upload)
- Ray will catch his own data errors (no extensive validation in MVP)
- Ray keeps local file backups (app doesn't need long-term historical file storage)

**Data Quality:**
- LineStar and DraftKings files have consistent column structures week-to-week
- NFL Stats file always contains cumulative season data (Weeks 1-N)
- Player names are reasonably consistent (fuzzy matching + manual mapping will handle 95%+ of cases)

**Technical:**
- PostgreSQL performs adequately for local use (100s of players, 18 weeks, 10 lineups per week)
- Linear programming optimizer can solve 10 lineups in <10 seconds on Ray's machine
- React app performs smoothly on Ray's iPhone (no performance bottlenecks)

**Future:**
- Cloud deployment (Phase 3) won't require major architectural changes (stateless API design)
- Collaborator will have similar technical comfort level (can handle XLSX uploads)
- DFS community would pay for advanced tools ($15/month range)

---

## Risks & Questions

### Risks

**Technical Risks:**

1. **Lineup Optimization Performance**  
   - Risk: Generating 10 diverse lineups with exposure constraints might take >10 seconds
   - Mitigation: Profile optimizer, use Gurobi (faster than PuLP) if needed, simplify constraints
   - Severity: Medium

2. **Player Name Normalization Accuracy**  
   - Risk: Fuzzy matching fails for edge cases (e.g., "Jr." vs. "III"), manual mapping becomes tedious
   - Mitigation: Build robust alias registry, improve fuzzy algorithm, accept manual mapping for <5% of players
   - Severity: Low

3. **Historical Data Integrity**  
   - Risk: NFL Stats file has missing weeks or incorrect data, Smart Score calculations break
   - Mitigation: User reviews data before upload, accepts responsibility for errors (no validation in MVP)
   - Severity: Low

4. **Mobile Browser Performance**  
   - Risk: Large player tables (200+ players) lag on mobile
   - Mitigation: Virtualize table rows (TanStack Table), paginate, filter by position
   - Severity: Medium

**User Experience Risks:**

5. **Cognitive Overload**  
   - Risk: 8-factor Smart Score with weight sliders is too complex for new users
   - Mitigation: Provide sensible defaults, offer "Simple Mode" (fewer weights), include tooltips/help text
   - Severity: Medium

6. **Manual Upload Fatigue**  
   - Risk: Uploading DKSalaries 20 times per week becomes tedious
   - Mitigation: Accept trade-off in MVP, prioritize API integration in Phase 2
   - Severity: Low (Ray is motivated, used to manual workflows)

**Scope/Timeline Risks:**

7. **Feature Creep (Again)**  
   - Risk: New "nice-to-have" ideas expand MVP scope, delay launch
   - Mitigation: Strict scope discipline, defer anything not critical to Week 12 launch
   - Severity: High (this killed the previous version)

8. **Week 12 Deadline Pressure**  
   - Risk: MVP not ready by Week 12, miss rest of 2024 season
   - Mitigation: Cut features aggressively if needed, focus on core workflow (import → Smart Score → optimize → export)
   - Severity: Medium

---

### Open Questions

**Product Questions:**

1. **DraftKings CSV Export Format:**  
   - What columns are required? Player ID, Name, Position, Salary?
   - Is there a header row? Specific order?
   - **Action:** Ray will provide sample DraftKings upload CSV before development starts

2. **Smart Score Weight Defaults:**  
   - What are reasonable starting values for W1-W8?
   - Should weights sum to 1.0, or be independent multipliers?
   - **Action:** Ray will define initial "Base" profile during testing

3. **Player Exposure UI:**  
   - How should users set exposure limits? Per-player sliders? Table with min/max inputs?
   - Should there be presets ("Spread evenly," "Concentrate on chalk")?
   - **Action:** Prototype 2-3 UI options, Ray selects preferred approach

4. **Lineup Diversity Algorithm:**  
   - Should optimizer maximize diversity (fewest overlaps) or score-based diversity (keep high-scoring players in multiple lineups)?
   - **Action:** Implement simple diversity first (minimize player overlap), iterate based on Ray's feedback

**Technical Questions:**

5. **PostgreSQL Backup Strategy:**  
   - Manual backup button only, or automated daily backups?
   - Store backups locally (SQL dumps) or cloud (S3)?
   - **Action:** Manual button for MVP, automated backups in Phase 3

6. **Multi-Sheet Import UX:**  
   - If DKSalaries has FE, ETR, ITT, should app prompt for each sheet? Or assume defaults (FE for projections, FE for ownership, ITT always imported)?
   - **Action:** Prompt user for projection + ownership source, always import ITT (Vegas data)

7. **Fuzzy Matching Threshold:**  
   - What similarity score (0-100) triggers manual mapping prompt? 80? 90?
   - **Action:** Start at 85, tune based on false positive/negative rate during testing

**Future Questions (Phase 2/3):**

8. **API Rate Limits:**  
   - Do Vegas/injury APIs have rate limits? How often can we fetch?
   - **Action:** Research API docs before Phase 2 development

9. **Cloud Hosting Costs:**  
   - What's realistic monthly cost for 10 users on Railway/Render?
   - **Action:** Estimate during Phase 2, finalize before Phase 3 deployment

10. **Monetization Strategy:**  
    - If we charge, what's competitive pricing? $10/month? $20? One-time $100?
    - **Action:** Defer until Phase 3, focus on building great product first

---

## Next Steps

### Immediate (Week 1-2)

1. ✅ **Complete Project Brief** (this document) → Ray reviews and approves
2. ✅ **Create PRFAQ** → Press release + FAQ to validate product vision
3. ✅ **Create PRD** → Detailed product requirements document
4. ✅ **Shard PRD into Components** → Break into buildable specs (Data Ingestion, Smart Score Engine, Lineup Optimizer, UI, etc.)

### Development (Week 3-6)

5. **Component 1: Data Ingestion & Player Management**
   - XLSX parsing (pandas, openpyxl)
   - Player name normalization (fuzzy matching, alias registry)
   - PostgreSQL schema + SQLAlchemy models
   - Basic API endpoints (upload, list players)

6. **Component 2: Smart Score Engine**
   - 8-factor calculation logic
   - Weight configuration API
   - Profile management (save/load)
   - Historical trend analysis (from NFL Stats)

7. **Component 3: Lineup Optimizer**
   - PuLP linear programming setup
   - DraftKings constraints (salary cap, positions, roster size)
   - Diversity algorithm (minimize overlap)
   - Exposure controls (min/max per player)

8. **Component 4: UI/UX (Front-End)**
   - React + Vite project setup
   - Material Design 3 theming (dark mode)
   - Dashboard, Player Pool, Smart Score Config, Lineup Generator screens
   - Responsive layout (desktop + mobile)

9. **Component 5: Export & Historical Replay**
   - DraftKings CSV export
   - Week selector (load past weeks)
   - Historical replay (adjust weights, re-optimize)

### Testing & Launch (Week 7-8)

10. **Integration Testing**
    - End-to-end workflow (import → calculate → optimize → export)
    - Edge case testing (missing columns, duplicate names, invalid salaries)
    - Performance testing (10 lineups in <10 seconds)
    - Mobile browser testing (iPhone, iPad)

11. **Week 12 Launch**
    - Ray imports Week 12 data
    - Generates lineups for Sunday Main Slate
    - Exports to DraftKings
    - Monitors for errors

12. **Iterate**
    - Collect feedback from Ray + collaborator
    - Fix bugs, refine UX
    - Plan Phase 2 features

---

## Conclusion

**Cortex represents a fresh start** built on lessons learned from the previous optimizer's failures. By focusing ruthlessly on the core workflow—**import data, calculate Smart Score, optimize lineups, export results**—and deferring nice-to-have features to Phase 2/3, we can deliver a reliable, maintainable tool in time for Week 12 of the 2024 NFL season.

**Success means:**
- Ray confidently generates competitive lineups every Sunday
- No data import errors or caching mysteries
- Fast iteration (adjust weights, see impact immediately)
- Historical learning (replay past weeks to improve strategy)
- Scalable foundation for future cloud deployment

**This is not a rebuild. This is the first real launch.**

Let's build Cortex. 🧠

---

**Document Status:** Draft v1.0 → Ready for Ray's review

**Next Document:** [PRFAQ.md](./PRFAQ.md) (Press Release + FAQ)

