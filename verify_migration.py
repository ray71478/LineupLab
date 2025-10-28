#!/usr/bin/env python3
"""
Verification script for Data Import System database migration.

This script:
1. Checks if all 8 tables exist
2. Verifies all indexes are created
3. Tests constraints with sample invalid data
4. Confirms foreign key relationships work

Usage:
    python verify_migration.py

Prerequisites:
    - PostgreSQL running locally
    - Database 'cortex' created
    - Migration 001 applied: alembic upgrade head
"""

import sys
import psycopg2
from psycopg2 import sql

# Database connection settings
DB_CONFIG = {
    'dbname': 'cortex',
    'user': 'postgres',
    'password': '',  # Update if needed
    'host': 'localhost',
    'port': 5432
}

# Expected tables in correct order
EXPECTED_TABLES = [
    'weeks',
    'player_pools',
    'historical_stats',
    'historical_stats_backup',
    'player_aliases',
    'import_history',
    'player_pool_history',
    'unmatched_players'
]

# Expected indexes per table
EXPECTED_INDEXES = {
    'weeks': ['idx_weeks_week_number', 'idx_weeks_status'],
    'player_pools': [
        'idx_player_pools_week_id',
        'idx_player_pools_player_key',
        'idx_player_pools_position',
        'idx_player_pools_team',
        'idx_player_pools_source'
    ],
    'historical_stats': [
        'idx_historical_stats_player_key',
        'idx_historical_stats_week',
        'idx_historical_stats_season'
    ],
    'player_aliases': [
        'idx_player_aliases_alias_name',
        'idx_player_aliases_canonical_key'
    ],
    'import_history': [
        'idx_import_history_week_source',
        'idx_import_history_imported_at'
    ],
    'player_pool_history': [
        'idx_player_pool_history_import_id',
        'idx_player_pool_history_player_key'
    ],
    'unmatched_players': [
        'idx_unmatched_players_import_id',
        'idx_unmatched_players_status'
    ]
}


def connect_db():
    """Connect to PostgreSQL database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)


def verify_tables(conn):
    """Verify all expected tables exist."""
    print("\n1. Verifying tables...")
    cur = conn.cursor()

    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)

    existing_tables = [row[0] for row in cur.fetchall()]

    missing_tables = set(EXPECTED_TABLES) - set(existing_tables)
    extra_tables = set(existing_tables) - set(EXPECTED_TABLES) - {'alembic_version'}

    if missing_tables:
        print(f"   ❌ Missing tables: {', '.join(missing_tables)}")
        return False

    if extra_tables:
        print(f"   ⚠️  Unexpected tables: {', '.join(extra_tables)}")

    print(f"   ✅ All {len(EXPECTED_TABLES)} tables exist")
    for table in EXPECTED_TABLES:
        print(f"      - {table}")

    cur.close()
    return True


def verify_indexes(conn):
    """Verify all expected indexes are created."""
    print("\n2. Verifying indexes...")
    cur = conn.cursor()

    all_indexes_ok = True

    for table, expected_indexes in EXPECTED_INDEXES.items():
        cur.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = %s
            AND schemaname = 'public';
        """, (table,))

        existing_indexes = [row[0] for row in cur.fetchall()]

        missing_indexes = set(expected_indexes) - set(existing_indexes)

        if missing_indexes:
            print(f"   ❌ {table}: Missing indexes: {', '.join(missing_indexes)}")
            all_indexes_ok = False
        else:
            print(f"   ✅ {table}: All {len(expected_indexes)} indexes exist")

    cur.close()
    return all_indexes_ok


def verify_constraints(conn):
    """Test that constraints are working by attempting invalid inserts."""
    print("\n3. Verifying constraints...")
    cur = conn.cursor()

    tests_passed = 0
    tests_total = 5

    # Test 1: Invalid week_number (outside 1-18 range)
    try:
        cur.execute("""
            INSERT INTO weeks (season, week_number, status)
            VALUES (2024, 19, 'upcoming');
        """)
        conn.rollback()
        print("   ❌ Week number constraint not working (allowed 19)")
    except psycopg2.Error:
        conn.rollback()
        tests_passed += 1
        print("   ✅ Week number constraint working (rejected 19)")

    # Test 2: Invalid player position
    # First insert a valid week
    try:
        cur.execute("""
            INSERT INTO weeks (season, week_number, status)
            VALUES (2024, 1, 'upcoming')
            ON CONFLICT (season, week_number) DO NOTHING
            RETURNING id;
        """)
        result = cur.fetchone()
        if result:
            week_id = result[0]
        else:
            cur.execute("SELECT id FROM weeks WHERE season = 2024 AND week_number = 1;")
            week_id = cur.fetchone()[0]
        conn.commit()
    except psycopg2.Error as e:
        print(f"   ⚠️  Could not insert test week: {e}")
        conn.rollback()

    try:
        cur.execute("""
            INSERT INTO player_pools
            (week_id, player_key, name, team, position, salary, source)
            VALUES (%s, 'test_player', 'Test Player', 'TST', 'KICKER', 5000, 'LineStar');
        """, (week_id,))
        conn.rollback()
        print("   ❌ Position constraint not working (allowed KICKER)")
    except psycopg2.Error:
        conn.rollback()
        tests_passed += 1
        print("   ✅ Position constraint working (rejected KICKER)")

    # Test 3: Invalid salary (too low)
    try:
        cur.execute("""
            INSERT INTO player_pools
            (week_id, player_key, name, team, position, salary, source)
            VALUES (%s, 'test_player', 'Test Player', 'TST', 'QB', 2000, 'LineStar');
        """, (week_id,))
        conn.rollback()
        print("   ❌ Salary constraint not working (allowed $2000)")
    except psycopg2.Error:
        conn.rollback()
        tests_passed += 1
        print("   ✅ Salary constraint working (rejected $2000)")

    # Test 4: Invalid ownership (>1)
    try:
        cur.execute("""
            INSERT INTO player_pools
            (week_id, player_key, name, team, position, salary, ownership, source)
            VALUES (%s, 'test_player', 'Test Player', 'TST', 'QB', 5000, 1.5, 'LineStar');
        """, (week_id,))
        conn.rollback()
        print("   ❌ Ownership constraint not working (allowed 1.5)")
    except psycopg2.Error:
        conn.rollback()
        tests_passed += 1
        print("   ✅ Ownership constraint working (rejected 1.5)")

    # Test 5: Unique constraint (duplicate player_key for same week)
    try:
        # Insert valid player first
        cur.execute("""
            INSERT INTO player_pools
            (week_id, player_key, name, team, position, salary, source)
            VALUES (%s, 'christian_mccaffrey_SF_RB', 'Christian McCaffrey', 'SF', 'RB', 9000, 'LineStar')
            ON CONFLICT (week_id, player_key) DO NOTHING;
        """, (week_id,))
        conn.commit()

        # Try to insert duplicate
        cur.execute("""
            INSERT INTO player_pools
            (week_id, player_key, name, team, position, salary, source)
            VALUES (%s, 'christian_mccaffrey_SF_RB', 'Christian McCaffrey', 'SF', 'RB', 9000, 'LineStar');
        """, (week_id,))
        conn.rollback()
        print("   ❌ Unique constraint not working (allowed duplicate)")
    except psycopg2.Error:
        conn.rollback()
        tests_passed += 1
        print("   ✅ Unique constraint working (rejected duplicate)")

    print(f"\n   Constraint tests: {tests_passed}/{tests_total} passed")

    cur.close()
    return tests_passed == tests_total


def verify_foreign_keys(conn):
    """Test that foreign key relationships are enforced."""
    print("\n4. Verifying foreign key relationships...")
    cur = conn.cursor()

    tests_passed = 0
    tests_total = 2

    # Test 1: Cannot insert player_pool with non-existent week_id
    try:
        cur.execute("""
            INSERT INTO player_pools
            (week_id, player_key, name, team, position, salary, source)
            VALUES (99999, 'test_player', 'Test Player', 'TST', 'QB', 5000, 'LineStar');
        """)
        conn.rollback()
        print("   ❌ Foreign key not enforced (allowed invalid week_id)")
    except psycopg2.Error:
        conn.rollback()
        tests_passed += 1
        print("   ✅ Foreign key enforced (rejected invalid week_id)")

    # Test 2: CASCADE delete works
    try:
        # Insert test week
        cur.execute("""
            INSERT INTO weeks (season, week_number, status)
            VALUES (2099, 1, 'upcoming')
            RETURNING id;
        """)
        test_week_id = cur.fetchone()[0]

        # Insert test player
        cur.execute("""
            INSERT INTO player_pools
            (week_id, player_key, name, team, position, salary, source)
            VALUES (%s, 'test_cascade', 'Test Cascade', 'TST', 'QB', 5000, 'LineStar');
        """, (test_week_id,))

        # Delete week (should cascade to player_pools)
        cur.execute("DELETE FROM weeks WHERE id = %s;", (test_week_id,))

        # Check if player was deleted
        cur.execute("SELECT COUNT(*) FROM player_pools WHERE player_key = 'test_cascade';")
        count = cur.fetchone()[0]

        if count == 0:
            tests_passed += 1
            print("   ✅ CASCADE delete working (player deleted with week)")
        else:
            print("   ❌ CASCADE delete not working (player still exists)")

        conn.rollback()
    except psycopg2.Error as e:
        conn.rollback()
        print(f"   ❌ Error testing CASCADE: {e}")

    print(f"\n   Foreign key tests: {tests_passed}/{tests_total} passed")

    cur.close()
    return tests_passed == tests_total


def main():
    """Run all verification checks."""
    print("=" * 70)
    print("Data Import System - Database Migration Verification")
    print("=" * 70)

    conn = connect_db()

    try:
        results = {
            'tables': verify_tables(conn),
            'indexes': verify_indexes(conn),
            'constraints': verify_constraints(conn),
            'foreign_keys': verify_foreign_keys(conn)
        }

        print("\n" + "=" * 70)
        print("VERIFICATION SUMMARY")
        print("=" * 70)

        all_passed = all(results.values())

        for check, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} - {check.replace('_', ' ').title()}")

        print("=" * 70)

        if all_passed:
            print("\n✅ ALL CHECKS PASSED - Migration verified successfully!")
            return 0
        else:
            print("\n❌ SOME CHECKS FAILED - Please review the output above")
            return 1

    finally:
        conn.close()


if __name__ == '__main__':
    sys.exit(main())
