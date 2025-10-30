# Database Verification Guide

This guide provides SQL queries and procedures to verify the Cortex database schema, data persistence, and integrity.

## Prerequisites

- PostgreSQL running (either local Docker container or cloud instance)
- SQL client connected to database (pgAdmin, DBeaver, or `psql` CLI)
- Database URL: `postgresql://cortex:cortex@localhost:5432/cortex` (local) or cloud instance

## Table 1: Verify All 7 Core Tables Exist

### Query: List all tables in public schema

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

**Expected output (7 tables minimum):**
```
                 table_name
─────────────────────────────────
 generated_lineups
 historical_stats
 import_history
 nfl_schedule
 player_aliases
 player_pools
 player_pool_history
 unmatched_players
 week_metadata
 week_status_overrides
 weeks
```

### Verification checklist:

- [ ] `weeks` - Week management (season, week_number, status)
- [ ] `player_pools` - Player data per week (salary, projections, ownership)
- [ ] `historical_stats` - NFL stats by player and week
- [ ] `import_history` - Import audit trail
- [ ] `player_aliases` - Fuzzy name matching resolution
- [ ] Additional tables: `week_metadata`, `nfl_schedule`, `week_status_overrides` (extended for week management)

---

## Table 2: Verify Weeks Table Schema

### Query: Describe weeks table structure

```sql
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'weeks'
ORDER BY ordinal_position;
```

**Expected columns:**
- `id` - INTEGER PRIMARY KEY
- `season` - INTEGER NOT NULL
- `week_number` - INTEGER NOT NULL (CHECK constraint: BETWEEN 1 AND 18)
- `status` - VARCHAR(20) (CHECK constraint: active, upcoming, completed)
- `nfl_slate_date` - DATE
- `status_override` - VARCHAR(20)
- `metadata` - TEXT
- `is_locked` - BOOLEAN DEFAULT 0
- `locked_at` - TIMESTAMP
- `created_at` - TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- `updated_at` - TIMESTAMP DEFAULT CURRENT_TIMESTAMP

### Verification checklist:

- [ ] All expected columns exist
- [ ] Data types match specification
- [ ] NOT NULL constraints applied correctly
- [ ] Default values set appropriately

---

## Table 3: Verify Player Pools Table Schema

### Query: Describe player_pools table

```sql
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'player_pools'
ORDER BY ordinal_position;
```

**Expected columns:**
- `id` - INTEGER PRIMARY KEY
- `week_id` - INTEGER NOT NULL (FOREIGN KEY references weeks.id)
- `player_key` - VARCHAR(255) NOT NULL (Unique: week_id + player_key)
- `name` - VARCHAR(255) NOT NULL
- `team` - VARCHAR(10) NOT NULL
- `position` - VARCHAR(10) NOT NULL (CHECK: QB, RB, WR, TE, DST)
- `salary` - INTEGER NOT NULL (CHECK: BETWEEN 3000 AND 10000)
- `projection` - FLOAT (CHECK: >= 0)
- `ownership` - FLOAT (CHECK: BETWEEN 0 AND 1)
- `ceiling` - FLOAT
- `floor` - FLOAT
- `source` - VARCHAR(50) NOT NULL
- `created_at`, `updated_at` - TIMESTAMP

### Verification checklist:

- [ ] Foreign key constraint: `player_pools.week_id` -> `weeks.id`
- [ ] Salary range constraint: 3000-10000
- [ ] Position whitelist: QB, RB, WR, TE, DST
- [ ] Unique constraint on (week_id, player_key)

---

## Table 4: Verify Historical Stats Table Schema

### Query: Describe historical_stats table

```sql
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'historical_stats'
ORDER BY ordinal_position;
```

**Expected columns:**
- `id` - INTEGER PRIMARY KEY
- `week_id` - INTEGER (FOREIGN KEY references weeks.id)
- `player_name` - VARCHAR(255) NOT NULL
- `team` - VARCHAR(10) NOT NULL
- `position` - VARCHAR(10) NOT NULL
- `week` - INTEGER (CHECK: BETWEEN 1 AND 18)
- `opponent` - VARCHAR(10)
- `snaps` - INTEGER
- `snap_pct` - FLOAT
- `rush_attempts`, `rush_yards`, `rush_tds` - INTEGER
- `targets`, `target_share` - Numeric
- `receptions`, `rec_yards`, `rec_tds` - INTEGER
- `total_tds`, `touches` - INTEGER
- `actual_points` - FLOAT
- `salary` - INTEGER
- `created_at`, `updated_at` - TIMESTAMP

---

## Table 5: Check Foreign Key Relationships

### Query: Verify foreign key constraints

```sql
SELECT
  constraint_name,
  table_name,
  column_name,
  referenced_table_name,
  referenced_column_name
FROM information_schema.key_column_usage
WHERE table_schema = 'public'
  AND referenced_table_name IS NOT NULL
ORDER BY table_name, constraint_name;
```

**Expected relationships:**
- `player_pools.week_id` -> `weeks.id` (ON DELETE CASCADE)
- `historical_stats.week_id` -> `weeks.id` (ON DELETE CASCADE)
- `import_history.week_id` -> `weeks.id` (ON DELETE CASCADE)
- `unmatched_players.import_id` -> `import_history.id` (ON DELETE CASCADE)

### Verification checklist:

- [ ] All foreign keys exist and point to correct tables
- [ ] ON DELETE CASCADE rules prevent orphaned records
- [ ] Can query player_pools and see non-null week_id values

---

## Table 6: Verify Data Integrity with Sample Data

### Query: Count rows by table

```sql
SELECT
  'weeks' as table_name, COUNT(*) as row_count FROM weeks
UNION ALL
SELECT
  'player_pools', COUNT(*) FROM player_pools
UNION ALL
SELECT
  'historical_stats', COUNT(*) FROM historical_stats
UNION ALL
SELECT
  'import_history', COUNT(*) FROM import_history
UNION ALL
SELECT
  'player_aliases', COUNT(*) FROM player_aliases
ORDER BY table_name;
```

### Expected counts (after seeding):

```
      table_name      | row_count
──────────────────────┼───────────
 import_history       |         0 (until first import)
 historical_stats     |         0 (until first import)
 player_aliases       |         0 (until players are matched)
 player_pools         |         0 (until first import)
 weeks                |        1+ (sample week)
```

---

## Table 7: Verify NFL Schedule Seed Data

### Query: Count weeks by year

```sql
SELECT season, COUNT(*) as week_count
FROM nfl_schedule
GROUP BY season
ORDER BY season;
```

**Expected output (after seeding):**
```
 season | week_count
────────┼────────────
   2023 |         18
   2024 |         18
   2025 |         18
```

**Total: 54 weeks across 3 seasons**

### Query: Check Week 9, 2024 details

```sql
SELECT id, season, week, slate_date, kickoff_time
FROM nfl_schedule
WHERE season = 2024 AND week = 9;
```

**Expected output (2024):**
```
 id | season | week | slate_date | kickoff_time
────┼────────┼──────┼────────────┼──────────────
 .. |   2024 |    9 | 2024-10-31 |     13:00
```

### Query: Verify Thanksgiving Week (Week 12)

```sql
SELECT id, season, week, slate_date, kickoff_time
FROM nfl_schedule
WHERE week = 12
ORDER BY season;
```

**Expected output:**
```
 id | season | week | slate_date | kickoff_time
────┼────────┼──────┼────────────┼──────────────
 .. |   2023 |   12 | 2023-11-23 |     12:30
 .. |   2024 |   12 | 2024-11-21 |     12:30
 .. |   2025 |   12 | 2025-11-20 |     12:30
```

---

## Table 8: Verify Sample Data After Seeding

### Query: View all seeded weeks

```sql
SELECT season, week_number, status, created_at
FROM weeks
ORDER BY season, week_number;
```

**Expected output:**
```
 season | week_number | status  | created_at
────────┼─────────────┼─────────┼────────────────────
   2024 |           9 | active  | 2024-XX-XX XX:XX:XX
```

### Query: Check weight profiles (if table exists)

```sql
SELECT name, projection_weight, value_weight, ownership_weight, vegas_weight, consistency_weight
FROM weight_profiles;
```

**Expected output:**
```
   name   | projection_weight | value_weight | ownership_weight | vegas_weight | consistency_weight
──────────┼──────────────────┼──────────────┼──────────────────┼──────────────┼──────────────────
 Balanced |              0.2 |          0.2 |              0.2 |          0.2 |                0.2
```

---

## Table 9: Data Persistence Test

### Procedure: Verify data survives container restart

**Step 1: Insert test data**

```sql
INSERT INTO weeks (season, week_number, status)
VALUES (2024, 15, 'upcoming');

-- Verify insert
SELECT * FROM weeks WHERE season = 2024 AND week_number = 15;
```

**Step 2: Stop and restart Docker container**

```bash
# Stop container
docker-compose stop postgres

# Restart container (WITHOUT -v flag to preserve data)
docker-compose start postgres

# Wait 10 seconds for PostgreSQL to start
sleep 10
```

**Step 3: Verify data persists**

```sql
-- Connect to database again
psql postgresql://cortex:cortex@localhost:5432/cortex

-- Query test data
SELECT * FROM weeks WHERE season = 2024 AND week_number = 15;
```

**Expected result:** Row still exists with same values

### Verification checklist:

- [ ] Data persists across container restart
- [ ] No data loss occurs
- [ ] Timestamps remain unchanged
- [ ] Foreign key relationships intact

---

## Table 10: Database Reset Procedure

### Complete Reset (Delete all data)

```bash
# Stop and remove container + volume
docker-compose down -v

# Start fresh
docker-compose up -d

# Wait for PostgreSQL to be healthy
sleep 15

# Run migrations to create schema
alembic upgrade head

# Optional: Seed development data
python backend/scripts/seed_development_data.py
```

### Partial Reset (Keep container, drop tables)

```bash
# Connect to database
psql postgresql://cortex:cortex@localhost:5432/cortex

-- Drop all tables (careful: all data lost)
DROP TABLE IF EXISTS player_pool_history CASCADE;
DROP TABLE IF EXISTS unmatched_players CASCADE;
DROP TABLE IF EXISTS player_aliases CASCADE;
DROP TABLE IF EXISTS historical_stats_backup CASCADE;
DROP TABLE IF EXISTS historical_stats CASCADE;
DROP TABLE IF EXISTS import_history CASCADE;
DROP TABLE IF EXISTS player_pools CASCADE;
DROP TABLE IF EXISTS week_status_overrides CASCADE;
DROP TABLE IF EXISTS week_metadata CASCADE;
DROP TABLE IF EXISTS nfl_schedule CASCADE;
DROP TABLE IF EXISTS weeks CASCADE;

-- Verify all dropped
SELECT table_name FROM information_schema.tables WHERE table_schema='public';
```

### Soft Reset (Clear data but keep schema)

```bash
-- Delete all rows from tables (preserves schema and foreign keys)
DELETE FROM player_pool_history;
DELETE FROM unmatched_players;
DELETE FROM player_aliases;
DELETE FROM historical_stats;
DELETE FROM import_history;
DELETE FROM player_pools;
DELETE FROM week_status_overrides;
DELETE FROM week_metadata;
DELETE FROM nfl_schedule;
DELETE FROM weeks;

-- Verify all empty
SELECT COUNT(*) FROM weeks;
SELECT COUNT(*) FROM nfl_schedule;
```

---

## Troubleshooting Common Issues

### Issue: "No such table" or table not found

**Cause:** Migrations not run yet

**Solution:**
```bash
alembic upgrade head
```

### Issue: Foreign key constraint violation

**Cause:** Trying to insert data into child table without parent

**Solution:**
```sql
-- Insert parent first
INSERT INTO weeks (season, week_number, status) VALUES (2024, 1, 'upcoming');

-- Then insert child
INSERT INTO player_pools (week_id, player_key, name, ...) VALUES (...);
```

### Issue: Unique constraint violation

**Cause:** Trying to insert duplicate (season, week_number) or (week_id, player_key)

**Solution:**
```sql
-- Check existing data
SELECT season, week_number FROM weeks WHERE season = 2024;

-- Check existing players for week
SELECT COUNT(*) FROM player_pools WHERE week_id = 1;
```

### Issue: Data appears in PostgreSQL but not in application

**Cause:** Application using different database connection string or schema

**Solution:**
```bash
# Verify DATABASE_URL
echo $DATABASE_URL

# Verify correct schema
SELECT current_schema();
SELECT * FROM information_schema.schemata;
```

---

## Quick Verification Script

Run this bash script to verify entire database setup:

```bash
#!/bin/bash

DATABASE_URL="postgresql://cortex:cortex@localhost:5432/cortex"

echo "=== Cortex Database Verification ==="
echo ""

echo "1. Checking table count..."
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';"

echo ""
echo "2. Listing all tables..."
psql "$DATABASE_URL" -c "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;"

echo ""
echo "3. Checking row counts..."
psql "$DATABASE_URL" -c "
SELECT 'weeks' as table_name, COUNT(*) FROM weeks
UNION ALL
SELECT 'player_pools', COUNT(*) FROM player_pools
UNION ALL
SELECT 'historical_stats', COUNT(*) FROM historical_stats
UNION ALL
SELECT 'import_history', COUNT(*) FROM import_history
UNION ALL
SELECT 'nfl_schedule', COUNT(*) FROM nfl_schedule
ORDER BY table_name;
"

echo ""
echo "4. Verifying NFL schedule..."
psql "$DATABASE_URL" -c "SELECT season, COUNT(*) FROM nfl_schedule GROUP BY season ORDER BY season;"

echo ""
echo "=== Verification Complete ==="
```

Save as `verify_db.sh`, make executable, and run:

```bash
chmod +x verify_db.sh
./verify_db.sh
```

---

## References

- [PostgreSQL information_schema](https://www.postgresql.org/docs/current/information-schema.html)
- [Alembic Migration Guide](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Constraints](https://docs.sqlalchemy.org/en/20/core/constraints.html)
