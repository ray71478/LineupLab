# Cortex Product Mission

**Last Updated:** October 27, 2025  
**Status:** Active Development

---

## Product Vision

**Cortex is the DFS player's "second brain"**—an intelligent lineup optimizer that empowers serious GPP tournament players with complete transparency, control, and data-driven decision-making for DraftKings NFL contests.

Unlike black-box commercial tools that hide their algorithms, Cortex puts users in the driver's seat by allowing them to define custom scoring formulas, weigh multiple projection sources, incorporate historical trends, and generate optimized lineups with full understanding of why each roster was constructed.

---

## Mission Statement

**Empower serious DFS players to build smarter lineups through transparent, configurable, AI-assisted optimization that combines multiple data sources, historical intelligence, and user-defined strategy.**

---

## Core Problem We Solve

DFS players face an impossible choice:

- **Manual spreadsheets**: Complete control but painfully slow, error-prone, and unable to explore thousands of lineup combinations
- **Commercial tools**: Fast optimization but zero transparency—players have no idea why lineups were built or how to adjust the underlying logic

**Cortex solves this by providing:**
1. **Transparency**: See exactly how Smart Score is calculated and why each player was selected
2. **Control**: Define your own 8-factor scoring formula with adjustable weights
3. **Intelligence**: Leverage historical trends, regression patterns, and Vegas context
4. **Speed**: Generate 10 optimized lineups in under 10 seconds
5. **Learning**: Replay past weeks with different strategies to improve over time

---

## Target Users

### Primary User: Ray Bargas
- Experienced DFS player (5+ years)
- Plays high-stakes GPP tournaments (large-field contests)
- Sunday Main Slate specialist
- Data-driven decision maker
- Values control and understanding over simplicity

### Secondary User: Collaborator
- Ray's DFS partner
- Less technical, prefers simple UI
- Needs access to shared data and lineups
- Occasional user (not daily)

### Future Users (Phase 3)
- Serious DFS players seeking advanced tools
- Willing to learn complex workflows for competitive edge
- Play GPP tournaments regularly
- Value transparency over simplicity

---

## Product Principles

### 1. **Transparency Over Opacity**
Users should understand exactly why each lineup was constructed. No black boxes, no proprietary secrets.

### 2. **Control Over Automation**
Users define the strategy, not the tool. Every weight, constraint, and rule is configurable.

### 3. **Focus Over Feature Creep**
Master one use case (DraftKings NFL Sunday Main Slate GPPs) before expanding. Quality over quantity.

### 4. **Speed Over Perfection**
Complete weekly workflow in under 20 minutes. Fast iteration beats perfect optimization.

### 5. **Learning Over Static Analysis**
Enable historical replay and strategy refinement. Build a feedback loop for continuous improvement.

### 6. **Local-First, Cloud-Ready**
Start with local development (no deployment friction), but architect for future cloud deployment.

---

## Key Differentiators

### vs. Commercial Tools (FantasyLabs, RotoGrinders)
- ✅ **Full transparency** in scoring algorithm
- ✅ **User-defined formulas** vs. fixed proprietary algorithms
- ✅ **Historical learning** through week replay
- ✅ **Local-first** data control (no vendor lock-in)

### vs. Manual Spreadsheets
- ✅ **Instant optimization** using linear programming
- ✅ **Constraint solving** (salary cap, positions, exposure limits)
- ✅ **Multi-source data integration** (LineStar, DraftKings, NFL Stats)
- ✅ **Collaboration-ready** (Phase 3)

### vs. Previous Version
- ✅ **Focused scope** (no feature creep)
- ✅ **Clean architecture** (maintainable, understandable)
- ✅ **Reliable data imports** (zero parsing errors)
- ✅ **Mobile-friendly** (responsive design)

---

## Success Metrics

### MVP Success Criteria
- ✅ 100% data import success rate (no parsing errors)
- ✅ Generate 10 lineups in <10 seconds
- ✅ Complete workflow in <20 minutes
- ✅ Mobile UI fully functional
- ✅ Zero server resets required

### Phase 2 Success Criteria
- Historical replay used 3+ times per season
- Variance analysis shows <10% projection error
- API data fetched in <2 seconds

### Phase 3 Success Criteria
- 10+ active users (beyond Ray + collaborator)
- 99.5% uptime
- <500ms page load time
- $500+ MRR (if monetized)

---

## Product Scope

### In Scope
- **Sport**: NFL only
- **Platform**: DraftKings only
- **Contest Type**: GPP (large-field tournaments) only
- **Slate**: Sunday Main Slate only

### Out of Scope (MVP)
- ❌ Other sports (NBA, MLB, NHL)
- ❌ Other platforms (FanDuel, Yahoo)
- ❌ Cash game strategies
- ❌ Non-Sunday slates (Showdown, Thursday Night)
- ❌ Automated contest entry

---

## Product Roadmap Summary

### Phase 1: MVP (Local Development) - Week 12, 2024
Core workflow: Import data → Calculate Smart Score → Optimize lineups → Export CSV

### Phase 2: Historical Analysis & APIs - Weeks 12-18, 2024
Add API integrations (Vegas lines, injuries), contest results import, variance analysis, performance analytics

### Phase 3: Cloud Deployment & Multi-User - 2025 Season
Deploy to cloud, add authentication, enable collaboration, optional monetization

---

## Core Value Proposition

**"Cortex gives you back control. Understand exactly why each lineup was built, and test new strategies every week without being locked into someone else's algorithm."**

---

## Long-Term Vision

Cortex will become the go-to tool for serious DFS players who refuse to accept black-box algorithms. By combining transparent optimization, historical learning, and collaborative features, Cortex will help players:

1. **Build smarter lineups** through data-driven insights
2. **Learn faster** by replaying past weeks with new strategies
3. **Compete better** by staying contrarian in GPP tournaments
4. **Collaborate effectively** with partners and teams

**This is not a rebuild. This is the first real launch.** 🧠

---

## Document Status
✅ **Approved** - Ready for development

