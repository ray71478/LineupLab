# Migration Rollback Procedure for Showdown Mode

## Overview
This document describes how to rollback the database migrations for Showdown Mode support (migrations 022 and 023).

## Migrations Added
- **022_add_contest_mode_to_player_pools.py** - Adds contest_mode support to player_pools table
- **023_add_contest_mode_to_generated_lineups.py** - Adds contest_mode support to generated_lineups table

## Rollback Commands

### To rollback both migrations (back to migration 021):
```bash
# Rollback to the version before showdown mode changes
alembic downgrade 021

# This will:
# 1. Remove contest_mode column from generated_lineups
# 2. Remove contest_mode column from player_pools
# 3. Restore original unique constraint on player_pools (week_id, player_key)
```

### To rollback only the generated_lineups migration (back to migration 022):
```bash
# Rollback just the lineup changes
alembic downgrade 022
```

## Verification After Rollback

### Check player_pools table structure:
```sql
-- PostgreSQL
\d player_pools

-- Should NOT have contest_mode column
-- Should have UNIQUE constraint on (week_id, player_key)
```

### Check generated_lineups table structure:
```sql
-- PostgreSQL
\d generated_lineups

-- Should NOT have contest_mode column
```

### Verify data integrity:
```sql
-- Check that existing main slate data is preserved
SELECT COUNT(*) FROM player_pools;
SELECT COUNT(*) FROM generated_lineups;

-- All data should remain intact
```

## Re-applying Migrations

### To re-apply the migrations:
```bash
# Upgrade to latest
alembic upgrade head

# This will re-apply migrations 022 and 023
```

## Important Notes

1. **Data Preservation**: Both upgrade and downgrade migrations preserve existing data
   - Upgrade: Existing records default to contest_mode='main'
   - Downgrade: Removes column but keeps all rows (data in contest_mode column is lost)

2. **Unique Constraint Changes**:
   - Migration 022 changes the unique constraint from (week_id, player_key) to (week_id, player_key, contest_mode)
   - This allows the same player to exist in both modes for the same week
   - Rollback restores the original constraint

3. **Foreign Key Constraints**: All foreign key relationships remain intact through both upgrade and downgrade

4. **Indexes**:
   - Migration creates composite indexes on (week_id, contest_mode)
   - These are automatically dropped during rollback

## Testing Rollback

Before rolling back production, test in development:

```bash
# 1. Create a database backup
pg_dump cortex > cortex_backup_$(date +%Y%m%d).sql

# 2. Apply showdown migrations
alembic upgrade head

# 3. Add some test data with contest_mode='showdown'

# 4. Rollback
alembic downgrade 021

# 5. Verify data
# - All main slate data should be preserved
# - Showdown data will be lost (expected)
# - Schema should match pre-showdown state

# 6. Re-apply if needed
alembic upgrade head
```

## Emergency Rollback

If issues are detected in production:

```bash
# 1. Immediate rollback
alembic downgrade 021

# 2. Verify application still works with old schema
# 3. Investigate issues
# 4. Fix and re-deploy when ready
alembic upgrade head
```

## Support

For issues with migrations, contact the development team or refer to:
- Alembic documentation: https://alembic.sqlalchemy.org/
- Migration files in `/alembic/versions/`
- Test files in `/tests/unit/test_showdown_schema.py`
