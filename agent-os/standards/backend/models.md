## Database model best practices

### General Principles
- **Clear Naming**: Use singular names for SQLAlchemy models, plural for table names (e.g., `Week` model → `weeks` table)
- **Timestamps**: Include `created_at` and `updated_at` timestamps on all tables for auditing and debugging
- **Data Integrity**: Use database constraints (NOT NULL, UNIQUE, foreign keys) to enforce data rules at the database level
- **Appropriate Data Types**: Choose data types that match the data's purpose and size requirements
- **Indexes on Foreign Keys**: Index foreign key columns and other frequently queried fields for performance
- **Validation at Multiple Layers**: Implement validation at both Pydantic (API) and database (constraints) levels
- **Relationship Clarity**: Define relationships clearly with appropriate cascade behaviors and naming conventions
- **Avoid Over-Normalization**: Balance normalization with practical query performance needs

### Cortex Database Schema

#### Core Tables

**`weeks` Table**
- `id` (Integer, PK, auto-increment)
- `season` (Integer, NOT NULL) - e.g., 2024
- `week_number` (Integer, NOT NULL) - 1-18
- `status` (Enum: upcoming, active, completed)
- `created_at` (DateTime, NOT NULL)
- `updated_at` (DateTime, NOT NULL)
- **Unique Constraint**: `(season, week_number)`
- **Index**: `week_number`, `status`

**`player_pools` Table**
- `id` (Integer, PK, auto-increment)
- `week_id` (Integer, FK → weeks.id, NOT NULL)
- `player_key` (String, NOT NULL) - Composite: `name_team_position` (e.g., `christian_mccaffrey_SF_RB`)
- `name` (String, NOT NULL)
- `team` (String, NOT NULL)
- `position` (String, NOT NULL) - QB, RB, WR, TE, DST
- `salary` (Integer, NOT NULL) - DraftKings salary
- `projection` (Float, nullable) - Projected FPTS
- `ownership` (Float, nullable) - Projected ownership %
- `ceiling` (Float, nullable) - Upside projection
- `floor` (Float, nullable) - Downside projection
- `notes` (Text, nullable) - User notes from import
- `source` (Enum: LineStar, DraftKings, NOT NULL)
- `uploaded_at` (DateTime, NOT NULL)
- **Unique Constraint**: `(week_id, player_key)`
- **Indexes**: `week_id`, `player_key`, `position`, `team`

**`historical_stats` Table**
- `id` (Integer, PK, auto-increment)
- `player_key` (String, NOT NULL)
- `week` (Integer, NOT NULL)
- `season` (Integer, NOT NULL)
- `team` (String, NOT NULL)
- `actual_points` (Float, nullable) - Actual DK FPTS scored
- `snaps` (Integer, nullable)
- `snap_pct` (Float, nullable)
- `targets` (Integer, nullable)
- `target_share` (Float, nullable)
- `receptions` (Integer, nullable)
- `rec_yards` (Integer, nullable)
- `rec_tds` (Integer, nullable)
- `rush_attempts` (Integer, nullable)
- `rush_yards` (Integer, nullable)
- `rush_tds` (Integer, nullable)
- `ownership` (Float, nullable) - Actual ownership from contest results
- **Unique Constraint**: `(player_key, week, season)`
- **Indexes**: `player_key`, `week`, `season`

**`vegas_lines` Table** (Phase 2)
- `id` (Integer, PK, auto-increment)
- `week_id` (Integer, FK → weeks.id, NOT NULL)
- `team` (String, NOT NULL)
- `opponent` (String, NOT NULL)
- `implied_team_total` (Float, nullable) - ITT
- `spread` (Float, nullable)
- `over_under` (Float, nullable)
- `updated_at` (DateTime, NOT NULL)
- **Unique Constraint**: `(week_id, team)`
- **Index**: `week_id`, `team`

**`generated_lineups` Table**
- `id` (Integer, PK, auto-increment)
- `week_id` (Integer, FK → weeks.id, NOT NULL)
- `lineup_number` (Integer, NOT NULL) - 1-10
- `players` (JSONB, NOT NULL) - Array of player objects: `[{ position, player_key, name, team, salary, smart_score, ownership }, ...]`
- `total_salary` (Integer, NOT NULL)
- `projected_score` (Float, NOT NULL) - Sum of Smart Scores
- `avg_ownership` (Float, nullable) - Average ownership %
- `strategy_mode` (Enum: Chalk, Balanced, Contrarian, NOT NULL)
- `weight_profile_id` (Integer, FK → weight_profiles.id, nullable)
- `created_at` (DateTime, NOT NULL)
- **Unique Constraint**: `(week_id, lineup_number, created_at)`
- **Indexes**: `week_id`, `created_at`

**`weight_profiles` Table**
- `id` (Integer, PK, auto-increment)
- `profile_name` (String, UNIQUE, NOT NULL) - e.g., "Base", "Contrarian"
- `weights` (JSONB, NOT NULL) - `{ W1: 1.0, W2: 0.5, ..., W8: 0.3 }`
- `created_at` (DateTime, NOT NULL)
- `updated_at` (DateTime, NOT NULL)
- **Index**: `profile_name`

**`player_aliases` Table**
- `id` (Integer, PK, auto-increment)
- `alias_name` (String, NOT NULL) - e.g., "C. McCaffrey"
- `canonical_player_key` (String, NOT NULL) - e.g., "christian_mccaffrey_SF_RB"
- `created_at` (DateTime, NOT NULL)
- **Unique Constraint**: `alias_name`
- **Index**: `alias_name`, `canonical_player_key`

### SQLAlchemy 2.0 Conventions
- **Declarative Base**: Use SQLAlchemy's declarative base for model definitions
- **Type Annotations**: Use Python type hints with SQLAlchemy's `Mapped` type
- **Relationships**: Define relationships using `relationship()` with clear `back_populates`
- **Cascade Behavior**: Use `cascade="all, delete-orphan"` for dependent records (e.g., player_pools when week is deleted)
- **JSONB Fields**: Use PostgreSQL's JSONB type for flexible data (weights, lineup players)
- **Enums**: Define Python Enums for status fields (week status, strategy mode, source)

### Example Model Pattern
```python
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum

class WeekStatus(enum.Enum):
    UPCOMING = "upcoming"
    ACTIVE = "active"
    COMPLETED = "completed"

class Week(Base):
    __tablename__ = "weeks"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    season: Mapped[int] = mapped_column(Integer, nullable=False)
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[WeekStatus] = mapped_column(SQLEnum(WeekStatus), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    player_pools: Mapped[list["PlayerPool"]] = relationship(back_populates="week", cascade="all, delete-orphan")
```

### Performance Considerations
- **Composite Keys**: Use `player_key` (name_team_position) instead of separate lookups for better query performance
- **JSONB Indexing**: Add GIN indexes on JSONB columns if querying nested fields (Phase 2)
- **Bulk Inserts**: Use SQLAlchemy's `bulk_insert_mappings()` for large data imports (200+ players)
- **Eager Loading**: Use `selectinload()` or `joinedload()` to avoid N+1 queries when fetching relationships
