## Database query best practices

### General Principles
- **Prevent SQL Injection**: Always use parameterized queries or ORM methods; never interpolate user input into SQL strings
- **Avoid N+1 Queries**: Use eager loading (`selectinload()`, `joinedload()`) to fetch related data in a single query
- **Select Only Needed Data**: Request only the columns you need rather than using `SELECT *` for better performance
- **Index Strategic Columns**: Index columns used in WHERE, JOIN, and ORDER BY clauses for query optimization
- **Use Transactions for Related Changes**: Wrap related database operations in transactions to maintain data consistency
- **Set Query Timeouts**: Implement timeouts to prevent runaway queries from impacting system performance
- **Cache Expensive Queries**: Cache results of complex or frequently-run queries when appropriate (Phase 3: Redis)

### Cortex Performance Requirements

**Critical Performance Targets:**
- **Lineup Generation**: Complete in <10 seconds for 10 lineups
- **Smart Score Calculation**: Complete in <1 second for real-time weight updates
- **Data Import**: Process 200+ players in <5 seconds
- **Player List Query**: Return filtered player list in <500ms

### SQLAlchemy 2.0 Query Patterns

#### Efficient Player Queries
```python
# BAD: N+1 query problem
players = session.execute(select(PlayerPool).where(PlayerPool.week_id == week_id)).scalars().all()
for player in players:
    # This triggers a separate query for each player's historical stats
    stats = player.historical_stats  

# GOOD: Eager loading with selectinload
from sqlalchemy.orm import selectinload

players = session.execute(
    select(PlayerPool)
    .where(PlayerPool.week_id == week_id)
    .options(selectinload(PlayerPool.historical_stats))
).scalars().all()
```

#### Filtered Queries with Indexes
```python
# Leverage indexes on week_id, position, team
players = session.execute(
    select(PlayerPool)
    .where(
        PlayerPool.week_id == week_id,
        PlayerPool.position.in_(["QB", "RB", "WR"])  # Use index on position
    )
    .order_by(PlayerPool.salary.desc())  # Consider index on salary if frequently sorted
).scalars().all()
```

#### Bulk Operations for Data Import
```python
# BAD: Individual inserts (slow for 200+ players)
for player_data in players_list:
    player = PlayerPool(**player_data)
    session.add(player)
session.commit()

# GOOD: Bulk insert (10-50x faster)
session.bulk_insert_mappings(PlayerPool, players_list)
session.commit()
```

#### Transactions for Data Consistency
```python
# Wrap related operations in a transaction
from sqlalchemy.exc import SQLAlchemyError

try:
    with session.begin():
        # Delete old player pool for this week
        session.execute(
            delete(PlayerPool).where(PlayerPool.week_id == week_id)
        )
        
        # Insert new player pool
        session.bulk_insert_mappings(PlayerPool, new_players)
        
        # Update week status
        session.execute(
            update(Week)
            .where(Week.id == week_id)
            .values(status=WeekStatus.ACTIVE, updated_at=datetime.utcnow())
        )
except SQLAlchemyError as e:
    # Transaction automatically rolled back
    raise ImportError(f"Failed to import player data: {str(e)}")
```

#### Optimized Aggregations
```python
# Calculate average ownership for lineup
from sqlalchemy import func

avg_ownership = session.execute(
    select(func.avg(PlayerPool.ownership))
    .where(PlayerPool.player_key.in_(lineup_player_keys))
).scalar()
```

### Query Optimization for Lineup Generation

**Pre-fetch All Required Data:**
```python
# Fetch all players with historical stats in one query
players_with_stats = session.execute(
    select(PlayerPool)
    .where(PlayerPool.week_id == week_id)
    .options(selectinload(PlayerPool.historical_stats))
).scalars().all()

# Convert to in-memory data structures for optimizer
# (PuLP optimizer works with Python dicts/lists, not ORM objects)
player_data = [
    {
        "player_key": p.player_key,
        "position": p.position,
        "salary": p.salary,
        "smart_score": calculate_smart_score(p),  # Calculate once
        "ownership": p.ownership,
        # ... other fields
    }
    for p in players_with_stats
]

# Run optimizer on in-memory data (no database queries during optimization)
lineups = run_optimizer(player_data, constraints)
```

### Indexing Strategy

**Required Indexes (MVP):**
- `player_pools`: `(week_id)`, `(player_key)`, `(week_id, position)`, `(week_id, team)`
- `historical_stats`: `(player_key)`, `(player_key, week, season)`
- `generated_lineups`: `(week_id)`, `(week_id, created_at)`
- `weight_profiles`: `(profile_name)`
- `player_aliases`: `(alias_name)`, `(canonical_player_key)`

**Composite Indexes:**
```python
# In Alembic migration
op.create_index(
    'ix_player_pools_week_position',
    'player_pools',
    ['week_id', 'position']
)
```

### Query Timeouts
```python
# Set statement timeout for long-running queries (PostgreSQL)
session.execute(text("SET statement_timeout = '10s'"))

# Or configure at connection level in SQLAlchemy
engine = create_engine(
    database_url,
    connect_args={"options": "-c statement_timeout=10000"}  # 10 seconds
)
```

### Caching Strategy (Phase 3)

**Cache Smart Score Calculations:**
- Key: `smart_score:{week_id}:{weight_profile_id}`
- TTL: Until weights change or new data imported
- Invalidate: On weight update or data re-import

**Cache Player Lists:**
- Key: `players:{week_id}:{position}:{team}`
- TTL: 1 hour (or until new data imported)
- Invalidate: On data re-import

### Common Query Patterns

**Get Player Pool for Week:**
```python
def get_player_pool(session, week_id: int, position: str = None):
    query = select(PlayerPool).where(PlayerPool.week_id == week_id)
    if position:
        query = query.where(PlayerPool.position == position)
    return session.execute(query).scalars().all()
```

**Get Historical Stats for Player:**
```python
def get_player_history(session, player_key: str, weeks: int = 5):
    return session.execute(
        select(HistoricalStats)
        .where(HistoricalStats.player_key == player_key)
        .order_by(HistoricalStats.week.desc())
        .limit(weeks)
    ).scalars().all()
```

**Get Latest Lineups for Week:**
```python
def get_latest_lineups(session, week_id: int):
    # Get most recent lineup generation for this week
    latest_created_at = session.execute(
        select(func.max(GeneratedLineup.created_at))
        .where(GeneratedLineup.week_id == week_id)
    ).scalar()
    
    if not latest_created_at:
        return []
    
    return session.execute(
        select(GeneratedLineup)
        .where(
            GeneratedLineup.week_id == week_id,
            GeneratedLineup.created_at == latest_created_at
        )
        .order_by(GeneratedLineup.lineup_number)
    ).scalars().all()
```
