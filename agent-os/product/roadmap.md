# Cortex Product Roadmap

**Last Updated:** October 27, 2025
**Status:** Active Development

---

## Overview

This roadmap outlines the phased development plan for Cortex, a DFS lineup optimizer for DraftKings NFL GPP tournaments. The roadmap is divided into three major phases, each with specific features, success metrics, and timelines.

---

## Phase 1: MVP (Local Development)

**Target Launch:** Week 12, 2024 NFL Season (4 weeks from now)
**Environment:** Local development (macOS, PostgreSQL)
**Users:** Ray (primary), collaborator (secondary)

### Goals
- Deliver a reliable, maintainable lineup optimizer
- Complete weekly workflow in under 20 minutes
- Zero data import errors or state confusion
- Mobile-friendly interface for on-the-go adjustments

### Core Features

#### 1. Week Management
- Create/select weeks 1-18 for current NFL season
- Week selector dropdown (persistent selection)
- Display current week prominently
- Navigate to past weeks for historical replay

#### 2. Data Import System ✅ COMPLETE
- [x] **Manual file selection** (LineStar vs. DraftKings)
- [x] **Multi-sheet support** (DKSalaries: FE, ETR, ITT sheets)
- [x] **User-prompted projection source** ("Which projections: FE or ETR?")
- [x] **User-prompted ownership source** ("Which ownership: FE or ETR?")
- [x] **Overwrite behavior** (latest upload replaces previous for that week)
- [x] **Historical stats import** (NFL 2025 Stats.xlsx - comprehensive replace with 1-week backup)
- [x] **Upload feedback** ("153 players imported from DKSalaries Week 9")
- [x] **Fuzzy name matching** (handle "Christian McCaffrey" vs. "C. McCaffrey")
- [x] **Alias mapping** (store name variations for future auto-resolution)
- [x] **Week mismatch detection** (warn if filename doesn't match selected week)
- [x] **Comprehensive validation** (salary range, projections, positions)
- [x] **Error handling** (clear, actionable error messages)
- [x] **Performance** (process 200+ players in <5 seconds)

#### 3. Player Management
- **Composite player key** (Name_Team_Position)
- **Fuzzy name matching** (handle "Christian McCaffrey" vs. "C. McCaffrey")
- **Manual mapping UI** (when auto-match confidence is low)
- **Alias registry** (store name variations for future auto-resolution)
- **Player table view** (sortable by Smart Score, salary, ownership, position)
- **Notes display** (show user notes from DKSalaries import)

#### 4. Smart Score Engine
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

#### 5. Lineup Optimizer
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

#### 6. Lineup Display & Export
- **In-App Table View:**
  - Show all 10 lineups side-by-side
  - Display: Position, Player Name, Team, Salary, Smart Score, Ownership
  - Calculate: Total Salary, Total Smart Score, Avg Ownership per lineup
  - Highlight: Salary cap violations (shouldn't happen), high-ownership stacks

- **CSV Export:**
  - DraftKings upload format
  - One-click download ("Download for DraftKings")
  - Save lineups to database (historical record)

#### 7. Historical Week Replay
- **Select Past Week:** Dropdown to Week 8, Week 7, etc.
- **Load Historical Data:** Pull that week's player pool (projections, ownership, salary as they were)
- **Adjust Weights:** Modify Smart Score formula with current knowledge
- **Re-Optimize:** Generate new lineups based on adjusted weights
- **Compare:** (Optional) Show original lineups vs. new lineups
- **Learn:** Save new weight profiles for future use

#### 8. User Interface (Dark Mode)
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
  - Dashboard: Week selector, data import status, Smart Score preview
  - Player Pool: Sortable table, filter by position/team, search by name
  - Smart Score Config: Weight sliders, profile management, 80-20 settings
  - Lineup Generator: Pre-generation settings, optimization button, progress indicator
  - Lineup Results: 10 lineups displayed, export button, save to history

#### 9. Data Persistence
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

#### 10. AI-Assisted Features (Subtle Integration)
- **Smart Defaults:** Pre-fill reasonable weight values based on historical performance
- **Projection Blending:** Offer to average FE + ETR projections if both exist
- **Anomaly Detection:** Flag players with unusual projection/ownership gaps
- **Exposure Suggestions:** "Based on ownership, recommend Lamar Jackson in 40% of lineups"
- **Post-Generation Insights:** "Lineup 3 is most contrarian (avg 8% ownership)"

### Success Metrics
- ✅ 100% data import success rate (no parsing errors)
- ✅ Generate 10 lineups in <10 seconds
- ✅ Complete workflow in <20 minutes
- ✅ Mobile UI fully functional
- ✅ Zero server resets required

### Out of Scope (MVP)
- ❌ API integrations (Vegas lines, injury reports)
- ❌ Contest results import
- ❌ Variance analysis
- ❌ Performance analytics
- ❌ Trend visualization
- ❌ Cloud deployment
- ❌ User authentication
- ❌ Multi-user access

---

## Phase 2: Historical Analysis & API Integration

**Target Launch:** Weeks 12-18, 2024 NFL Season (4-6 weeks after MVP)
**Environment:** Local development with API integrations
**Users:** Ray (primary), collaborator (secondary)

### Goals
- Automate data fetching (reduce manual imports)
- Enable deep learning from historical performance
- Validate Smart Score accuracy

### Features

#### 1. API Integrations
- **Vegas Lines API:** Auto-fetch ITT, spreads, over/unders (hourly updates)
- **Injury Report API:** Real-time injury status (ESPN, FantasyData, or Sleeper)
- **API Configuration:** User provides API keys, app handles authentication
- **Fallback to Manual:** If API fails, allow manual upload as backup

#### 2. Contest Results Import
- **Upload DraftKings Contest CSV:** Import actual contest results
- **Compare Actual vs. Projected FPTS:** Player-level variance analysis
- **Lineup Performance:** Show which lineups finished in top X%
- **Historical Record:** Store contest results for all weeks

#### 3. Variance Analysis Dashboard
- **Player-Level Analysis:**
  - "CMC projected 23, scored 31 (+8)"
  - "Lamar Jackson projected 28, scored 19 (-9)"
  - Show projection accuracy over time

- **Lineup-Level Analysis:**
  - "Lineup 3 scored 182 (top 5% finish)"
  - "Lineup 7 scored 143 (bottom 20%)"
  - Compare projected vs. actual total scores

- **Week-Level Analysis:**
  - "Week 9 projections were 12% high on average"
  - "FE projections outperformed ETR by 5%"
  - Identify systematic projection biases

#### 4. Performance Analytics
- **Weight Profile Performance:**
  - "Contrarian profile won 3 of 5 weeks"
  - "Base profile averaged top 15% finishes"
  - Recommend best-performing profiles

- **80-20 Rule Validation:**
  - "80-20 rule saved you from 14 busts"
  - "Players penalized scored 8% below projection on average"

- **Trend Analysis:**
  - "Target share trends correctly predicted 8 breakouts"
  - "Snap count increases correlated with 15% scoring boost"

#### 5. Trend Visualization
- **Line Charts:**
  - Player snap % over time
  - Target share progression
  - Ownership trends week-over-week

- **Scatter Plots:**
  - Projected vs. actual FPTS
  - Ownership vs. scoring (find value plays)

- **Heatmaps:**
  - Position-level performance by week
  - Team-level scoring trends

### Success Metrics
- Historical replay used 3+ times per season
- Variance analysis shows <10% projection error
- API data fetched in <2 seconds
- Contest results imported for 100% of weeks played
- Smart Score outperforms baseline projections by 5%+

---

## Phase 3: Cloud Deployment & Multi-User

**Target Launch:** 2025 Off-Season (ready before 2025 NFL season starts)
**Environment:** Cloud deployment (Railway or Render)
**Users:** Ray, collaborator, broader DFS community (10+ users)

### Goals
- Enable collaboration with partner
- Expand to broader DFS community
- Generate revenue (optional)

### Features

#### 1. Cloud Infrastructure
- **Deploy to Railway or Render:** PaaS with Python + PostgreSQL support
- **PostgreSQL Hosted Database:** Migrate from local to cloud database
- **Redis for Caching:** Session management, API response caching
- **Docker Containerization:** Consistent environments (local → cloud)
- **CI/CD Pipeline:** Automated testing and deployment

#### 2. User Authentication
- **Email/Password Login:** Auth0 or Supabase
- **OAuth:** Google, Apple
- **Session Management:** JWT tokens
- **Password Reset:** Email-based recovery
- **Account Management:** Profile settings, password change

#### 3. Multi-User Access
- **Invite Collaborator by Email:** Send invitation link
- **Role-Based Permissions:** Owner, Editor, Viewer
- **Private Player Pools:** Isolated per user (default)
- **Shared Player Pools:** Optional, for teams
- **User Dashboard:** See all users, manage permissions

#### 4. Collaboration Features
- **Shared Notes on Players:** Comment threads ("Watch the weather in Buffalo")
- **Lineup Comparison:** "Your lineup vs. mine" side-by-side view
- **Contest Result Sharing:** Who won this week? Leaderboard integration
- **Activity Feed:** See when collaborators upload data, generate lineups
- **Real-Time Updates:** WebSocket for live collaboration (optional)

#### 5. Monetization (Optional)
- **Free Tier:** Local use only (as in MVP)
- **Pro Tier ($15/month):**
  - Cloud access
  - Multi-user (up to 2 users)
  - API integrations included
  - Advanced analytics

- **Team Tier ($50/month):**
  - Up to 5 users
  - Shared player pools
  - Advanced analytics
  - Priority support

- **Payment Processing:** Stripe integration
- **Subscription Management:** Billing, invoices, cancellation

### Success Metrics
- 10+ active users (beyond Ray + collaborator)
- 99.5% uptime
- <500ms page load time
- $500+ MRR (if monetized)
- 90%+ user satisfaction (NPS score)

---

## Future Expansion (Post-Phase 3)

### Other Sports
- **NBA:** High demand, different optimization constraints (6-8 players, showdown slates)
- **MLB:** Moderate demand, pitcher-heavy strategy
- **NHL:** Lower demand, niche user base

### Other Platforms
- **FanDuel:** Moderate demand, different salary cap and scoring
- **Yahoo:** Lower demand, smaller user base

### Other Slates
- **Showdown:** Single-game slates (captain + flex players)
- **Thursday Night / Monday Night:** Smaller player pools
- **Weekend Slates:** Multi-day contests

### Other Contest Types
- **Cash Games:** Different strategy (safer plays, less contrarian)
- **Best Ball:** Season-long, no weekly lineup setting

---

## Development Timeline

### MVP (Phase 1): 4 Weeks
- **Week 1-2:** Component 1 (Data Ingestion & Player Management)
- **Week 2-3:** Component 2 (Smart Score Engine)
- **Week 3-4:** Component 3 (Lineup Optimizer)
- **Week 4:** Component 4 (UI/UX Front-End)
- **Week 4:** Component 5 (Export & Historical Replay)
- **Week 4:** Integration Testing & Launch (Week 12)

### Phase 2: 4-6 Weeks (Weeks 12-18, 2024)
- **Week 1-2:** API integrations (Vegas lines, injuries)
- **Week 2-3:** Contest results import & variance analysis
- **Week 3-4:** Performance analytics & trend visualization
- **Week 4-6:** Testing & refinement

### Phase 3: 2025 Off-Season (3-4 Months)
- **Month 1:** Cloud infrastructure setup (Railway/Render, Docker)
- **Month 2:** User authentication & multi-user access
- **Month 3:** Collaboration features & monetization
- **Month 4:** Beta testing, launch before 2025 NFL season

---

## Prioritization Framework

### Must-Have (MVP)
Features required for core workflow: import → Smart Score → optimize → export

### Should-Have (Phase 2)
Features that enhance learning and reduce manual work (APIs, analytics)

### Nice-to-Have (Phase 3)
Features that enable collaboration and scalability (cloud, multi-user)

### Won't-Have (Future)
Features deferred to post-Phase 3 (other sports, platforms, contest types)

---

## Risk Mitigation

### Feature Creep Risk (High)
- **Mitigation:** Strict scope discipline, defer anything not critical to MVP
- **Action:** Weekly scope review, ruthless prioritization

### Timeline Risk (Medium)
- **Mitigation:** Cut features aggressively if needed, focus on core workflow
- **Action:** Weekly progress check, adjust timeline if behind

### Technical Risk (Medium)
- **Mitigation:** Profile optimizer performance, use faster libraries if needed
- **Action:** Early performance testing, benchmark against 10-second target

### User Adoption Risk (Low)
- **Mitigation:** Build for Ray first (primary user), expand to collaborator, then community
- **Action:** Weekly user feedback, iterate based on real usage

---

## Document Status
✅ **Approved** - Ready for development
