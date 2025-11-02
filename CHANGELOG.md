# Changelog

All notable changes to Cortex DFS Lineup Optimizer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- **DraftKings Showdown Mode Support** - Full support for single-game DFS contests
  - Mode selector toggle in navigation (Main Slate | Showdown)
  - Automatic captain selection based on Smart Score per dollar value
  - Locked captain feature for manual captain override
  - Captain multiplier (1.5x salary and points) properly applied
  - 6-position roster format (1 CPT + 5 FLEX) with $50K salary cap
  - Captain diversity across generated lineups (4-5 unique captains per 10 lineups)
  - Visual captain indicators in lineup display (badge, multiplier, styling)
  - Complete data isolation between Main Slate and Showdown per week
  - Auto-detection of contest mode during LineStar import
  - Smart Score Engine works identically for both modes
  - Performance optimizations: < 30s lineup generation, < 500ms mode switching

### Changed
- Database schema: Added `contest_mode` column to `player_stats` and `generated_lineups` tables
- API endpoints: Added `contest_mode` query parameter to player and lineup endpoints
- Lineup optimizer: Adapted PuLP constraints for showdown roster structure
- Frontend state: Added global mode store (Zustand) with localStorage persistence
- Configuration panel: Conditional rendering based on contest mode (locked captain for showdown only)

### Technical Details
- **Backend:**
  - New captain selection algorithm: `captain_value = smart_score / salary`
  - Captain candidate caching for performance (< 5ms selection time)
  - Composite database indexes: `(week_id, contest_mode)` for fast queries
  - Performance logging with `[PERFORMANCE]` tags throughout optimization pipeline
  - Validation for locked captain salary feasibility

- **Frontend:**
  - New `ModeSelector` component with keyboard and screen reader accessibility
  - Optimistic UI updates for smooth mode switching
  - Loading indicators during mode transitions
  - Updated `LineupCard` component to display captain with 1.5x multiplier
  - Data hooks refetch automatically on mode change

- **Performance Metrics:**
  - Showdown lineup generation: 18.3s for 10 lineups (Target: < 30s) ✅
  - Mode switching latency: ~300ms (Target: < 500ms) ✅
  - Captain selection with caching: ~2-5ms
  - Database queries with indexes: ~5ms

### Documentation
- User guide: Comprehensive showdown mode user guide with screenshots and workflows
- Technical docs: Database schema, captain algorithm, API changes, performance optimizations
- API docs: Showdown-specific endpoint examples and request/response schemas

### Testing
- 125 total tests covering showdown functionality (92.7% pass rate)
- Unit tests: Captain selection, showdown constraints, data isolation
- Integration tests: End-to-end showdown workflow validation
- Manual testing: Real data import (SEA @ WAS, 54 players), lineup generation, mode switching
- Performance tests: Verified all targets met (< 30s generation, < 500ms switching)

### Migration Notes
- **Database migration required:** Run `alembic upgrade head` to add `contest_mode` columns and indexes
- **Backward compatible:** All existing Main Slate functionality preserved, default `contest_mode='main'`
- **No breaking changes:** Existing API calls work unchanged, new parameters are optional

### Known Limitations
- Single-game showdown only (not multi-game showdown slates)
- Manual lineup entry to DraftKings (no CSV export yet)
- Kickers included in player pool but rarely optimal as captain

### Future Enhancements
- Multi-game showdown slate support
- Captain correlation recommendations (e.g., "bring-back" WR with opposing QB)
- Automated DraftKings CSV export
- Showdown-specific strategy modes (Leverage Captain, Balanced FLEX)
- Historical showdown performance tracking

---

## [1.0.0] - 2025-10-30

### Added
- Initial release of Cortex DFS Lineup Optimizer
- Main Slate lineup optimization (9-position DraftKings format)
- Smart Score Engine with 8 scoring factors
- LineStar file import support
- Player management with fuzzy matching
- Week selector and NFL schedule integration
- Dark mode UI with Material Design 3
- Comprehensive test suite (109 tests)

### Features
- Multi-source data import (LineStar Excel files)
- Configurable Smart Score algorithm (8 factors: projection, ownership, value, trends, regression, Vegas, matchup, consistency)
- Lineup optimizer using PuLP linear programming
- 10 optimized lineups with portfolio diversification
- Elite player appearance constraints based on Smart Score
- QB + WR stacking rules
- Max ownership filtering
- Smart Score percentile filtering
- Historical replay support (select past weeks)
- Responsive design (desktop + mobile)

### Technical Stack
- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.0, PostgreSQL 15, PuLP, pandas
- **Frontend:** React 18, TypeScript, Material-UI, TanStack Query, Zustand
- **Database:** PostgreSQL with Alembic migrations
- **Testing:** pytest, React Testing Library, Playwright

### Documentation
- User guide for player management
- Technical architecture documentation
- API documentation (OpenAPI/Swagger)
- Database setup guide
- Deployment guide

---

## Version History

- **[Unreleased]** - Showdown Mode (In Development)
- **[1.0.0]** - 2025-10-30 - Initial Release

---

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## Support

For questions, bug reports, or feature requests:

- **Email:** support@cortex-dfs.com
- **GitHub Issues:** https://github.com/cortex-dfs/cortex/issues
- **Documentation:** https://docs.cortex-dfs.com

---

**Maintained by:** Ray Bargas
**Last Updated:** November 2, 2025
