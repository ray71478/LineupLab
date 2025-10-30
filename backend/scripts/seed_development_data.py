#!/usr/bin/env python
"""
Seed development data for Cortex DFS Lineup Optimizer.

This script is idempotent - it can be run multiple times safely.
It creates:
- NFL schedule for 3 seasons (2023, 2024, 2025) - 54 weeks total
- Sample week (Week 9, 2024) with active status
- Sample weight profile (Balanced: all weights 0.20)

Run with: python backend/scripts/seed_development_data.py
"""

import os
import sys
from datetime import date, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://cortex:cortex@localhost:5432/cortex"
)


def get_base_dates(year: int) -> list:
    """Get NFL schedule dates for a given year."""
    if year == 2023:
        return [
            '2023-09-07', '2023-09-14', '2023-09-21', '2023-09-28',
            '2023-10-05', '2023-10-12', '2023-10-19', '2023-10-26',
            '2023-11-02', '2023-11-09', '2023-11-16', '2023-11-23',
            '2023-11-30', '2023-12-07', '2023-12-14', '2023-12-21',
            '2023-12-28', '2024-01-04',
        ]
    elif year == 2024:
        return [
            '2024-09-05', '2024-09-12', '2024-09-19', '2024-09-26',
            '2024-10-03', '2024-10-10', '2024-10-17', '2024-10-24',
            '2024-10-31', '2024-11-07', '2024-11-14', '2024-11-21',
            '2024-11-28', '2024-12-05', '2024-12-12', '2024-12-19',
            '2024-12-26', '2025-01-02',
        ]
    elif year == 2025:
        return [
            '2025-09-04', '2025-09-11', '2025-09-18', '2025-09-25',
            '2025-10-02', '2025-10-09', '2025-10-16', '2025-10-23',
            '2025-10-30', '2025-11-06', '2025-11-13', '2025-11-20',
            '2025-11-27', '2025-12-04', '2025-12-11', '2025-12-18',
            '2025-12-25', '2026-01-01',
        ]
    else:
        # Generic 18 weeks for other years (Sunday dates)
        first_sept = date(year, 9, 1)
        first_sunday = first_sept + timedelta(days=(6 - first_sept.weekday()))
        return [(first_sunday + timedelta(weeks=i)).isoformat() for i in range(18)]


def seed_nfl_schedule(session, year: int = 2024) -> int:
    """Seed NFL schedule for a year. Returns number of weeks inserted."""
    base_dates = get_base_dates(year)
    count = 0

    for week_num in range(1, 19):
        kickoff_time = '12:30' if week_num == 12 else '13:00'  # Thanksgiving Week 12

        try:
            # Check if already exists
            result = session.execute(
                text("""
                    SELECT id FROM nfl_schedule
                    WHERE season = :season AND week = :week
                """),
                {"season": year, "week": week_num}
            )

            if result.fetchone() is None:
                # Insert new record
                session.execute(
                    text("""
                        INSERT INTO nfl_schedule (season, week, slate_date, kickoff_time, game_count, is_playoff)
                        VALUES (:season, :week, :slate_date, :kickoff_time, :game_count, :is_playoff)
                    """),
                    {
                        "season": year,
                        "week": week_num,
                        "slate_date": base_dates[week_num - 1],
                        "kickoff_time": kickoff_time,
                        "game_count": 16,
                        "is_playoff": False,
                    }
                )
                count += 1
        except Exception as e:
            print(f"  Warning: Could not insert week {week_num} for {year}: {e}")

    return count


def seed_sample_week(session) -> bool:
    """Seed sample week (Week 9, 2024) with active status. Returns True if inserted."""
    try:
        # Check if already exists
        result = session.execute(
            text("""
                SELECT id FROM weeks
                WHERE season = :season AND week_number = :week_number
            """),
            {"season": 2024, "week_number": 9}
        )

        if result.fetchone() is not None:
            print("  Week 9, 2024 already exists")
            return False

        # Insert new week
        session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status)
                VALUES (:season, :week_number, 'active')
            """),
            {"season": 2024, "week_number": 9}
        )
        print("  Created Week 9, 2024 with active status")
        return True
    except Exception as e:
        print(f"  Warning: Could not create sample week: {e}")
        return False


def seed_sample_weight_profile(session) -> bool:
    """Seed sample weight profile (Balanced: all weights 0.20). Returns True if inserted."""
    try:
        # Check if already exists
        result = session.execute(
            text("""
                SELECT id FROM weight_profiles
                WHERE name = 'Balanced'
            """)
        )

        if result.fetchone() is not None:
            print("  Weight profile 'Balanced' already exists")
            return False

        # Check if table exists first
        try:
            session.execute(text("SELECT 1 FROM weight_profiles LIMIT 1"))
        except Exception:
            print("  Note: weight_profiles table does not exist yet")
            return False

        # Insert new profile
        session.execute(
            text("""
                INSERT INTO weight_profiles
                (name, projection_weight, value_weight, ownership_weight, vegas_weight, consistency_weight)
                VALUES (:name, :proj, :value, :own, :vegas, :consist)
            """),
            {
                "name": "Balanced",
                "proj": 0.20,
                "value": 0.20,
                "own": 0.20,
                "vegas": 0.20,
                "consist": 0.20,
            }
        )
        print("  Created 'Balanced' weight profile")
        return True
    except Exception as e:
        print(f"  Warning: Could not create weight profile: {e}")
        return False


def main():
    """Main seeding function."""
    print("Starting development data seeding...")

    # Create engine and session
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Seed NFL schedule for 3 seasons
        total_weeks = 0
        for year in [2023, 2024, 2025]:
            print(f"\nSeeding NFL schedule for {year}...")
            count = seed_nfl_schedule(session, year)
            total_weeks += count
            if count > 0:
                print(f"  Inserted {count} weeks")
            session.commit()

        print(f"\nTotal weeks inserted: {total_weeks}")

        # Seed sample week
        print("\nSeeding sample week...")
        seed_sample_week(session)
        session.commit()

        # Seed sample weight profile
        print("\nSeeding weight profile...")
        seed_sample_weight_profile(session)
        session.commit()

        print("\nData seeding completed successfully!")

        # Verification queries
        print("\nVerification:")
        result = session.execute(text("SELECT COUNT(*) FROM nfl_schedule"))
        week_count = result.scalar()
        print(f"  Total weeks in nfl_schedule: {week_count} (expected 54)")

        result = session.execute(text("SELECT COUNT(*) FROM weeks"))
        sample_week_count = result.scalar()
        print(f"  Total weeks in weeks table: {sample_week_count}")

    except Exception as e:
        print(f"Error during seeding: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
