# Cortex - PRFAQ (Press Release FAQ)

**Date:** October 26, 2025  
**Document Type:** Press Release + Frequently Asked Questions  
**Status:** Draft v1.0

---

## Press Release

### FOR IMMEDIATE RELEASE

**Cortex Launches: The DFS Lineup Optimizer That Puts You in Control**

*Local-first tool empowers serious DFS players with transparent, AI-assisted roster construction for DraftKings GPP tournaments*

---

**[Your City], [Launch Date]** — Today marks the launch of **Cortex**, an intelligent DFS lineup optimizer designed for players who refuse to accept black-box algorithms and demand complete control over their roster construction strategy.

Unlike commercial tools that hide their decision-making behind proprietary formulas, Cortex empowers users to define every aspect of their lineup generation process—from how projections are weighted to how ownership influences roster construction. Built for serious GPP (Guaranteed Prize Pool) tournament players, Cortex combines multiple data sources, historical trend analysis, and a configurable "Smart Score" algorithm to generate optimized DraftKings lineups with full transparency.

### The Problem: Opacity and Lack of Control

For years, DFS players have faced an impossible choice:

- **Manual spreadsheets:** Complete control, but painfully slow and error-prone. No way to explore thousands of lineup combinations or enforce complex constraints.

- **Commercial tools:** Fast optimization, but zero transparency. Players have no idea why certain lineups were built or how to adjust the underlying logic. Projections, ownership weighting, and stacking strategies are all fixed—take it or leave it.

"I was paying $50/month for a tool that I didn't understand," said Ray Bargas, creator of Cortex. "When I wanted to know why it was fading a high-ownership player or stacking a specific game, I had no answers. I needed a tool that let me define the strategy, not the other way around."

### The Solution: Transparent, Configurable Intelligence

Cortex solves this problem by putting the user in the driver's seat:

**Multi-Source Data Integration:**  
Import player data from LineStar (early week projections) and DraftKings (source of truth for ownership and salaries). Load comprehensive NFL historical stats to analyze trends, snap counts, target shares, and regression patterns. All data is stored locally in a PostgreSQL database with full historical context.

**Smart Score: Your Custom Formula:**  
Define an 8-factor scoring algorithm that weighs projections, ownership, ceiling/floor, value (points per $1K salary), historical trends, regression patterns (the 80-20 rule), Vegas implied team totals, and matchup quality. Adjust weights with sliders in real-time and see immediate impact on player rankings. Save multiple weight profiles ("Base," "Contrarian," "Trend-Heavy") and switch between them instantly.

**Lineup Optimizer with Constraints:**  
Generate 10 optimized lineups (or any number you choose) using linear programming that enforces DraftKings constraints: $50K salary cap, 9 roster positions (QB, RBx2, WRx3, TE, FLEX, DST), max players per team/game. Configure exposure limits ("include Patrick Mahomes in 3-7 lineups") and stacking rules ("QB + at least 1 WR from same team"). Choose your strategy: Chalk (high ownership), Balanced, or Contrarian (low ownership for tournament differentiation).

**Historical Replay:**  
Select any past week, load that week's player pool and projections as they were, then adjust your Smart Score weights with the benefit of hindsight. Re-optimize lineups to see what would have happened if you'd weighted ownership differently or trusted target share trends more. Learn from every week and refine your strategy over time.

**Dark Mode UI, Mobile-Friendly:**  
Built with Material Design 3, Cortex features a sleek dark mode interface optimized for both desktop and mobile browsers. Review player pools, adjust weights, and generate lineups on your phone 30 minutes before kickoff—no laptop required.

### Results Speak

Since launching internally four weeks ago, Cortex has delivered:

- **100% data import success rate** (zero parsing errors or broken uploads)
- **10 lineups generated in under 8 seconds** (faster than manual building)
- **Complete weekly workflow in under 15 minutes** (import → tune → optimize → export)
- **Zero caching or state confusion issues** (eliminated deployment friction)
- **3 profitable weeks out of 4** (historical replay identified weight improvements)

"Cortex gave me back control," Bargas said. "I understand exactly why each lineup was built, and I can test new strategies every week without being locked into someone else's algorithm. This is the tool I've been trying to build for three years."

### Availability and Pricing

**Cortex MVP is available now for local use (free, open-source).**  

**Phase 2 (early 2025):** API integrations for Vegas lines and injury reports, contest results import, variance analysis.

**Phase 3 (2025 season):** Cloud deployment with multi-user access, collaboration features, and optional paid tiers ($15/month for Pro, $50/month for Team).

For more information, visit [project repository] or contact Ray Bargas at [email].

### About Cortex

Cortex is a local-first, AI-assisted DFS lineup optimizer built by Ray Bargas with facilitation by Mary (agent-os/analyst). The tool focuses exclusively on DraftKings NFL Sunday Main Slate GPP tournaments, with plans to expand to other sports and platforms in future releases. Cortex is designed for serious DFS players who value transparency, control, and data-driven decision-making.

---

## Frequently Asked Questions (FAQ)

### General Questions

**Q1: What is Cortex, and who is it for?**

A: Cortex is an intelligent DFS lineup optimizer designed for serious DFS players who play DraftKings GPP (Guaranteed Prize Pool) tournaments. Unlike commercial tools that use hidden algorithms, Cortex gives you complete control over how lineups are constructed. You define the scoring formula (Smart Score), adjust weights for projections/ownership/trends, and generate optimized lineups with full transparency. It's for players who want to understand *why* lineups were built, not just *what* lineups to play.

**Q2: How is Cortex different from FantasyLabs, RotoGrinders, or other DFS tools?**

A: Three key differences:

1. **Transparency:** You define the Smart Score formula and can adjust 8 different weight factors. Commercial tools use proprietary algorithms you can't control or understand.

2. **Historical Learning:** Cortex lets you replay past weeks with different weight settings to see what would have worked better. This creates a feedback loop to improve your strategy over time.

3. **Local-First:** Your data stays on your machine (PostgreSQL database). No cloud subscription required for MVP. You control your data and never lose access if you stop paying.

**Q3: What sports and platforms does Cortex support?**

A: **MVP (Phase 1) supports:**
- **Sport:** NFL only
- **Platform:** DraftKings only
- **Contest Type:** GPP (large-field tournaments) only
- **Slate:** Sunday Main Slate only

**Future phases** may expand to other sports (NBA, MLB), platforms (FanDuel), and slates (Showdown, Thursday Night), but the initial focus is narrow to ensure quality.

**Q4: Do I need to know how to code to use Cortex?**

A: **No coding required for daily use.** You'll interact with a web-based UI (dark mode, responsive design) to:
- Upload XLSX files (LineStar, DraftKings, NFL Stats)
- Adjust Smart Score weight sliders
- Configure lineup generation settings
- Export lineups to CSV

**However, MVP requires local setup:**
- Install Python 3.11+, Node.js 20+, PostgreSQL 15
- Run backend (FastAPI) and frontend (React) locally
- Comfortable with terminal commands for installation

**Phase 3 (cloud deployment)** will eliminate setup requirements—just log in and use the tool via a web browser.

---

### Data & Smart Score Questions

**Q5: What data sources does Cortex use?**

A: Cortex imports data from three sources:

1. **LineStar_Football_WKX.xlsx** (early week):
   - Projections, ownership estimates, ceiling/floor, Vegas lines, opponent ranks
   - Available Sunday/Monday before DraftKings releases data

2. **DKSalaries Week X.xlsx** (mid-week onward, source of truth):
   - DraftKings salaries, projections (FE and ETR sheets), ownership (FE and ETR)
   - Vegas implied team totals (ITT sheet)
   - Updated 10-20 times per week as ownership changes

3. **NFL 2025 Stats.xlsx** (weekly historical update):
   - Actual weekly performance (DK points, snaps, targets, receptions, touchdowns)
   - Season aggregates (snap %, target share, rush share)
   - Ownership vs. results (for projection accuracy analysis)

You manually upload these files. **Phase 2** will integrate APIs to auto-fetch Vegas lines and injury reports.

**Q6: How does the Smart Score work?**

A: The Smart Score is an 8-factor formula that evaluates each player's value for lineup inclusion. You configure the weights (W1-W8) for each factor:

**Formula:**
```
Smart Score = 
  (Projection × W1)          // DK or LineStar projection
  + (Ceiling Factor × W2)    // Ceiling - Floor (upside potential)
  - (Ownership Penalty × W3) // High ownership reduces score (GPP strategy)
  + (Value Score × W4)       // Projection / (Salary / 1000)
  + (Trend Adjustment × W5)  // Target share, snap % increasing?
  - (Regression Penalty × W6) // 80-20 rule: scored 20+ last week? Penalize
  + (Vegas Context × W7)     // Implied Team Total / league average
  + (Matchup Adjustment × W8) // Opponent defensive rank
```

**Example:** If you want to build contrarian lineups, increase W3 (ownership penalty). If you trust Vegas projections, increase W7 (Vegas context). Save multiple profiles and switch between them for different strategies.

**Q7: What is the "80-20 rule," and how does it work in Cortex?**

A: The 80-20 rule is a DFS heuristic: **80% of the time, a player who scores 20+ DK points regresses the following week.**

In Cortex:
- The system checks each player's **last week's DK points** (from NFL Stats historical data)
- If they exceeded a configurable threshold (default: 20 points), apply a **penalty percentage** (default: 10% reduction to Smart Score)
- This reduces their ranking, making them less likely to appear in lineups

**You can configure:**
- Threshold (e.g., 20, 25, 30 points)
- Penalty percentage (e.g., 5%, 10%, 15%)
- Toggle on/off per lineup generation

**Q8: How do I handle player name mismatches across data sources?**

A: Cortex uses three strategies:

1. **Composite Key:** Each player gets a unique identifier: `Name_Team_Position` (e.g., `christian_mccaffrey_SF_RB`)

2. **Fuzzy Matching:** If a name doesn't match exactly (e.g., "Christian McCaffrey" vs. "C. McCaffrey"), Cortex uses similarity scoring to find the best match.

3. **Manual Mapping UI:** If fuzzy matching confidence is low (<85%), Cortex prompts you to confirm or correct the match. Once mapped, the alias is stored for future auto-resolution.

**Example:** First time you import "C. McCaffrey," Cortex asks: "Is this Christian McCaffrey (SF, RB)?" You confirm. Next time, it auto-resolves.

---

### Lineup Optimization Questions

**Q9: How does the lineup optimizer work?**

A: Cortex uses **linear programming** (PuLP library) to solve a constrained optimization problem:

**Objective:** Maximize total Smart Score across all generated lineups.

**Constraints:**
- $50,000 salary cap per lineup
- 9 roster positions: QB, RB×2, WR×3, TE, FLEX (RB/WR/TE), DST
- Max 4 players from one team (configurable)
- Max 5 players from one game (configurable)
- Player exposure limits (e.g., "Patrick Mahomes in 3-7 lineups")
- Lineup diversity (minimize player overlap across lineups)

**Performance:** Generates 10 lineups in under 10 seconds on standard hardware.

**Q10: Can I control which players appear in lineups?**

A: Yes, multiple ways:

1. **Player Pool Curation:** Only upload players you're willing to roster (pre-filter in XLSX before import).

2. **Smart Score Weights:** Adjust weights to favor/penalize certain player types (e.g., increase ownership penalty to fade chalk, increase ceiling factor to favor upside plays).

3. **Exposure Limits:** Set min/max lineup counts per player:
   - "Lamar Jackson: 3-7 lineups" (appears in 30-70% of lineups)
   - "Christian McCaffrey: 0-2 lineups" (limited exposure due to high ownership)

4. **Manual Exclusion (Future):** Lock/exclude specific players (Phase 2 feature).

**Q11: What lineup diversity strategies does Cortex support?**

A: Cortex offers three strategy modes:

1. **Chalk (High Ownership):**
   - Favor players with high projected ownership
   - Build "safe" lineups for cash games (though Cortex focuses on GPPs)
   - Minimize diversity (overlap is okay)

2. **Balanced (Mixed Ownership):**
   - Blend chalk and contrarian plays
   - Moderate diversity (some overlap, some unique builds)
   - Default strategy for most users

3. **Contrarian (Low Ownership):**
   - Penalize high-ownership players aggressively
   - Maximize diversity (minimize overlap across lineups)
   - Target unique roster constructions for large-field GPPs

You select the strategy before generating lineups. Cortex adjusts the optimization algorithm accordingly.

**Q12: Does Cortex support stacking (QB + WR from same team)?**

A: **Yes (configurable).** You can define stacking rules before lineup generation:

- **QB + WR Stack:** "Include at least 1 WR from QB's team in 70% of lineups"
- **Game Stack:** "Include players from both teams in the same game"
- **Bring-Back Stack:** "If QB is from Team A, include at least 1 player from Team B (opposing team)"

**MVP (Phase 1)** supports basic stacking (QB + WR). **Phase 2** will add advanced stacking strategies (game stacks, bring-backs, mini-game stacks).

---

### Workflow & Usage Questions

**Q13: What does a typical weekly workflow look like?**

A: Here's the recommended workflow:

**Monday (Early Week):**
1. Export LineStar data → upload to Cortex
2. Review player pool, adjust Smart Score weights (initial setup)
3. Generate test lineups (optional, just to see early rankings)

**Wednesday (Mid-Week):**
4. Export DraftKings salaries → upload to Cortex (overwrites LineStar)
5. Select which projections to use (FE or ETR)
6. Select which ownership to use (FE or ETR)
7. Adjust Smart Score weights based on matchups, weather, news

**Friday-Sunday (Refinement):**
8. Re-export DraftKings data (ownership updates) → upload 5-10 times
9. Fine-tune weights, test different strategy modes (Chalk, Balanced, Contrarian)
10. Review player notes, check injury reports

**Sunday (30 min before kickoff):**
11. Final DraftKings upload
12. Configure lineup generation settings:
    - 10 lineups, Contrarian mode
    - Exposure limits (e.g., "Fade Christian McCaffrey: 0-2 lineups")
    - Stacking rules (QB + WR stack enabled)
13. Click "Generate Lineups" → Wait 8 seconds
14. Review lineups (check salary cap, ownership, stacks)
15. Export to DraftKings CSV format
16. Upload to DraftKings contest

**Weekly (Post-Monday Night Football):**
17. Export updated NFL Stats (includes last week's actuals) → upload to Cortex
18. Historical data now available for next week's Smart Score calculations

**Total time:** 15-20 minutes per week (after initial setup).

**Q14: Can I use Cortex for multiple weeks in the same season?**

A: **Yes, that's the core use case.** Cortex stores data for all 18 NFL weeks:

- **Week selector dropdown:** Choose Week 1, Week 2, ..., Week 18
- **Historical data persistence:** All uploads are saved (player pools, historical stats, generated lineups)
- **Replay past weeks:** Select Week 8 → Load that week's data → Adjust weights → Re-optimize

**Example use case:**  
You're in Week 10. You realize your ownership weighting was too conservative in Week 8 (you faded too many chalk plays). Select Week 8, increase ownership tolerance (reduce W3), regenerate lineups. Compare new lineups to what you actually played. Save new weight profile for future use.

**Q15: What file format does Cortex export for DraftKings?**

A: Cortex exports a **CSV file** in DraftKings' required upload format. Exact column structure is TBD (Ray will provide sample during development), but typically includes:

- Player ID (DraftKings player ID)
- Player Name
- Position
- Team
- Salary
- Roster Position (QB, RB, WR, TE, FLEX, DST)

You download the CSV from Cortex, then upload it directly to your DraftKings contest entry.

---

### Technical & Setup Questions

**Q16: What are the system requirements to run Cortex MVP?**

A: **Hardware:**
- macOS (primary development platform)
- 8GB RAM minimum (16GB recommended)
- 5GB free disk space (database + application files)

**Software (must install):**
- Python 3.11+ (via pyenv)
- Node.js 20+ (via nvm)
- PostgreSQL 15 (via Homebrew or Docker)
- Git

**Browser:**
- Chrome, Safari, or Firefox (desktop)
- Safari or Chrome (mobile)

**Phase 3 (cloud deployment)** will eliminate all setup requirements—just log in via a browser.

**Q17: Is my data secure? Where is it stored?**

A: **MVP (Phase 1):**  
All data is stored **locally on your machine** in a PostgreSQL database. No cloud storage, no external servers. Your player pools, historical stats, Smart Score weights, and generated lineups never leave your computer.

**Phase 2 (API integrations):**  
Vegas lines and injury reports are fetched from third-party APIs (temporary network calls), but data is still stored locally.

**Phase 3 (cloud deployment):**  
If you opt for cloud access, data will be stored on Railway or Render (PostgreSQL hosted database). You'll have full control over your account, and data is encrypted in transit (HTTPS) and at rest (database encryption). You can delete your account and all data at any time.

**Q18: Can I back up my data?**

A: **Yes, two ways:**

1. **Automated Backup:** Before importing new historical stats (NFL Stats.xlsx), Cortex automatically creates a backup of the current database (keeps 1 previous version).

2. **Manual Backup:** Click "Export Database" button → Downloads a SQL dump file → Store wherever you like (external drive, cloud storage).

**Restoring:** Import the SQL dump to recreate your database at any point in time.

**Q19: Will Cortex work offline?**

A: **MVP (Phase 1): Yes, mostly.**

- Data import, Smart Score calculation, lineup optimization, and CSV export all work **100% offline** (no internet required).
- APIs for Vegas lines and injury reports (Phase 2) require internet.

**Phase 3 (cloud deployment): No, internet required** (web-based application).

---

### Pricing & Availability Questions

**Q20: How much does Cortex cost?**

A: **MVP (Phase 1): Free (open-source).**  
Run Cortex locally on your machine. No subscription, no license fees.

**Phase 2 (API integrations): Free + optional API costs.**  
Cortex remains free, but you'll need API subscriptions for Vegas lines ($20-50/month) and injury reports (varies by provider). These are third-party services, not Cortex fees.

**Phase 3 (cloud deployment):**  
- **Free tier:** Local use only (as in Phase 1)
- **Pro tier ($15/month):** Cloud access, multi-user, API integrations included
- **Team tier ($50/month):** 5 users, shared player pools, advanced analytics

**Note:** Pricing is tentative and will be finalized before Phase 3 launch.

**Q21: When will Cortex be available?**

A: **Phase 1 (MVP):** Week 12, 2024 NFL season (target: ~4 weeks from now)  
**Phase 2 (Historical Analysis & APIs):** Before end of 2024 NFL season (Weeks 12-18)  
**Phase 3 (Cloud + Multi-User):** 2025 off-season (ready for 2025 NFL season kickoff)

**Q22: Will Cortex be open-source?**

A: **Yes, MVP (Phase 1) will be open-source** (license TBD—likely MIT or Apache 2.0). You can:
- View all code (frontend and backend)
- Modify for personal use
- Contribute improvements (pull requests welcome)

**Phase 3 (cloud version)** may include proprietary components (authentication, payment processing), but the core optimizer logic will remain open-source.

---

### Future Features & Roadmap Questions

**Q23: What's coming in Phase 2?**

A: **Phase 2 (Historical Analysis & API Integration):**

1. **Vegas Lines API:** Auto-fetch implied team totals, spreads, over/unders (hourly updates)
2. **Injury Report API:** Real-time injury status (ESPN, FantasyData, or Sleeper)
3. **Contest Results Import:** Upload DraftKings contest CSV → Compare actual vs. projected FPTS
4. **Variance Analysis:**
   - Player-level: "CMC projected 23, scored 31 (+8)"
   - Lineup-level: "Lineup 3 scored 182 (top 5% finish)"
   - Week-level: "Week 9 projections were 12% high on average"
5. **Performance Analytics:**
   - "Contrarian profile won 3 of 5 weeks"
   - "80-20 rule saved you from 14 busts"
   - "Target share trends correctly predicted 8 breakouts"
6. **Trend Visualization:** Line charts for player snap %, target share, ownership over time

**Target:** Before end of 2024 NFL season (4-6 weeks after MVP launch).

**Q24: What's coming in Phase 3?**

A: **Phase 3 (Cloud Deployment & Multi-User):**

1. **Cloud Infrastructure:** Deploy to Railway or Render (no local setup required)
2. **User Authentication:** Email/password login, OAuth (Google, Apple)
3. **Multi-User Access:** Invite collaborators, role-based permissions (owner, editor, viewer)
4. **Collaboration Features:**
   - Shared player pools (optional)
   - Shared notes and comments on players
   - Lineup comparison ("Your lineup vs. mine")
   - Contest result sharing (who won this week?)
5. **Monetization:** Free tier (local use), Pro tier ($15/month), Team tier ($50/month)

**Target:** 2025 off-season (ready before 2025 NFL season starts).

**Q25: Will Cortex support other sports or platforms?**

A: **Not in MVP.** Cortex is laser-focused on **DraftKings NFL Sunday Main Slate GPP tournaments** to ensure quality and reliability.

**Future expansion (post-Phase 3):**
- **Other sports:** NBA, MLB, NHL (high demand, likely)
- **Other platforms:** FanDuel, Yahoo (moderate demand)
- **Other slates:** Showdown, Thursday Night, Monday Night (moderate demand)
- **Other contest types:** Cash games (lower priority, different strategy)

**Philosophy:** Master one use case first (NFL GPPs), then expand carefully to avoid feature creep.

---

### Support & Community Questions

**Q26: Where can I get help or report bugs?**

A: **MVP (Phase 1):**
- GitHub Issues (if open-source)
- Direct contact with Ray Bargas (email TBD)
- Documentation (ProjectBrief, PRD, user guides)

**Phase 3 (cloud version):**
- Help center (knowledge base, FAQs)
- In-app support chat
- Community Discord or Slack (optional)

**Q27: Can I contribute to Cortex development?**

A: **Yes! (If you're technical.)**

**MVP** will be open-source, so you can:
- Submit bug reports (GitHub Issues)
- Suggest features (GitHub Discussions or Issues)
- Contribute code (pull requests welcome)
- Improve documentation

**Areas where contributions are especially valuable:**
- Lineup optimizer performance improvements
- Fuzzy matching algorithm enhancements
- UI/UX design feedback
- Additional Smart Score factors (e.g., weather, rest days, coaching changes)

**Q28: Who built Cortex?**

A: **Cortex was created by:**

- **Ray Bargas** (Product Owner, Developer) - Experienced DFS player and software engineer who wanted full control over his lineup optimizer.

- **Mary** (Business Analyst, agent-os/analyst) - Facilitated discovery, requirements gathering, and product specification using structured elicitation techniques.

**Development:** Cortex is built using agent-os workflow, breaking the project into component specifications and systematically implementing each piece.

**Philosophy:** This is not a rebuild—it's the first real launch. We learned from previous attempts and built Cortex with focus, discipline, and a clear vision.

---

## Closing Thoughts

Cortex exists because **serious DFS players deserve better tools**—tools that respect their intelligence, give them control, and help them learn over time.

If you're tired of black-box algorithms and want to understand *why* lineups are built, not just *what* lineups to play, **Cortex is for you.**

**This is not a rebuild. This is the first real launch.**

Let's build smarter lineups. 🧠

---

**Document Status:** Draft v1.0 → Ready for Ray's review

**Next Document:** [PRD.md](./PRD.md) (Product Requirements Document)

