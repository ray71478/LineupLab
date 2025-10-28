# Cortex - DFS Lineup Optimizer

**Your DFS Intelligence Layer**

Cortex is an intelligent DFS lineup optimizer built for serious GPP tournament players who demand complete control over their roster construction strategy. Unlike black-box commercial tools, Cortex empowers you to define custom scoring algorithms, weigh multiple projection sources, incorporate historical trend analysis, and generate optimized DraftKings lineups with full transparency.

---

## 📁 Project Structure

```
/NewApp/
├── README.md (you are here)
└── discovery/
    ├── ProjectBrief.md           ✅ COMPLETE - Comprehensive project overview
    ├── PRFAQ.md                  🚧 IN PROGRESS - Press release + FAQ
    ├── PRD.md                    ⏳ PENDING - Product requirements document
    ├── TechnicalArchitecture.md  ⏳ PENDING - System design & data models
    ├── COMPONENT_DEPENDENCIES.md ⏳ PENDING - Build order & dependencies
    └── components/               ⏳ PENDING - Component specifications (micro-PRDs)
```

---

## 🧠 What is Cortex?

**The Problem:**  
Existing DFS tools are either too simplistic (manual spreadsheets) or too opaque (proprietary algorithms you can't control). You need a tool that gives you full control over the "brain" of the optimizer.

**The Solution:**  
Cortex combines multiple data sources (LineStar, DraftKings, historical NFL stats) with a configurable "Smart Score" algorithm to generate optimized DraftKings lineups. You define the formula, adjust weights in real-time, and understand exactly why each lineup was constructed.

**Key Features:**
- 📊 Multi-source data import (LineStar, DraftKings, NFL historical stats)
- 🧮 Configurable Smart Score (8-factor formula: projection, ownership, value, trends, regression, Vegas, matchup)
- 🎯 Lineup optimizer (10 lineups, DraftKings constraints, exposure controls, stacking rules)
- 🕒 Historical replay (select past weeks, adjust weights, re-optimize with hindsight)
- 🎨 Dark mode UI (Material Design 3, responsive desktop + mobile)
- 🚀 Local-first development, cloud-ready architecture

---

## 📖 Documentation

### **Start Here:**

1. **[ProjectBrief.md](./discovery/ProjectBrief.md)** ✅  
   Read this first. Comprehensive project overview including:
   - Executive Summary
   - Problem Statement
   - Proposed Solution
   - Target Users
   - MVP Scope (Phase 1, 2, 3)
   - Technical Stack
   - Risks & Open Questions

### **Coming Next:**

2. **[PRFAQ.md](./discovery/PRFAQ.md)** 🚧  
   Press Release FAQ (written as if Cortex already exists and succeeded):
   - Headline & press release
   - Customer problem/solution narrative
   - Key features & benefits
   - FAQ addressing stakeholder questions

3. **[PRD.md](./discovery/PRD.md)** ⏳  
   Product Requirements Document (detailed specifications):
   - User stories
   - Functional requirements
   - Non-functional requirements (performance, security, scalability)
   - User experience flows
   - API requirements
   - Data models
   - Acceptance criteria

4. **[TechnicalArchitecture.md](./discovery/TechnicalArchitecture.md)** ⏳  
   System design & technical documentation:
   - Architecture diagrams
   - Database schemas (PostgreSQL models)
   - API endpoints (FastAPI routes)
   - Smart Score algorithm (detailed formula)
   - Lineup optimizer approach (linear programming)
   - Technology stack details

5. **[COMPONENT_DEPENDENCIES.md](./discovery/COMPONENT_DEPENDENCIES.md)** ⏳  
   Build order & dependency mapping:
   - Component breakdown (Data Ingestion, Smart Score Engine, Lineup Optimizer, UI, etc.)
   - Dependency graph (which components depend on others)
   - Critical path to MVP
   - Parallel work opportunities

6. **[components/*.md](./discovery/components/)** ⏳  
   Individual component specifications (micro-PRDs):
   - `01-data-ingestion-prd.md` - XLSX parsing, player normalization, database storage
   - `02-smart-score-engine-prd.md` - 8-factor calculation, weight management, profiles
   - `03-lineup-optimizer-prd.md` - Linear programming, constraints, diversity algorithm
   - `04-ui-frontend-prd.md` - React app, dark mode UI, responsive design
   - `05-export-replay-prd.md` - CSV export, historical week replay
   - `06-historical-analysis-prd.md` - (Phase 2) API integrations, variance analysis

---

## 🎯 Project Status

**Current Phase:** Discovery & Requirements  
**Status:** Project Brief Complete, PRFAQ in progress  
**Next Milestone:** Complete PRD & component sharding (ready for agent-os handoff)

**Timeline:**
- **Week 1-2:** Discovery (Project Brief, PRFAQ, PRD, Component Sharding) ← YOU ARE HERE
- **Week 3-6:** Development (build components, integrate, test)
- **Week 7-8:** Testing & refinement
- **Week 12 (2024 NFL Season):** Launch MVP

---

## 🛠️ Tech Stack

**Front-End:**
- React 18 + Vite
- Material Design 3 (dark mode)
- TanStack Table (player grids)
- TanStack Query (API calls)
- Tailwind CSS + Headless UI

**Back-End:**
- FastAPI (Python 3.11+)
- SQLAlchemy (PostgreSQL ORM)
- pandas + openpyxl (XLSX processing)
- PuLP (linear programming for lineup optimization)

**Database:**
- PostgreSQL 15 (local, Docker or Homebrew)

**Deployment (Phase 3):**
- Railway or Render (cloud hosting)
- Docker + Docker Compose

---

## 🚀 Vision

### Phase 1 (MVP - Local):
- Complete weekly workflow: import → Smart Score tuning → lineup generation → export
- Historical replay (adjust weights for past weeks)
- Dark mode UI (desktop + mobile)

### Phase 2 (Historical Analysis):
- API integrations (Vegas lines, injury reports)
- Contest results import (actual vs. projected comparison)
- Variance analysis & performance analytics

### Phase 3 (Cloud + Multi-User):
- Cloud deployment (Railway/Render)
- User authentication
- Collaborator access
- Shared player pools

---

## 🎨 Design Philosophy

**Visual Identity:**
- **Dark mode primary** (deep navy/black backgrounds)
- **Material Design 3** principles
- **Google Fonts** (Inter or Roboto)
- **Material Icons** (clean, no emojis)
- **Color Palette:**
  - Background: `#0f0f1a` (deep navy)
  - Primary: `#00d4ff` (cyan - data emphasis)
  - Accent: `#7c3aed` (purple - AI features)
  - Text: `#e5e7eb` (light gray)

**UX Principles:**
- Minimal clicks (smart defaults, keyboard shortcuts, batch actions)
- AI-assisted (suggestions, auto-detect, predictive inputs)
- Data-dense but readable (good typography, not overwhelming)
- Mobile-first responsive

---

## 📞 Contact

**Product Owner:** Ray Bargas  
**Business Analyst:** Mary (agent-os/analyst)  

**Questions?** Review [ProjectBrief.md](./discovery/ProjectBrief.md) first, then reach out.

---

**This is not a rebuild. This is the first real launch.** 🧠

Let's build Cortex.

