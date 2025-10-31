#!/usr/bin/env python
"""
Cleanup script to delete all weeks from seasons other than 2025.

This script:
- Deletes all weeks where season != 2025
- Due to CASCADE delete constraints, related data will be automatically deleted:
  - week_metadata
  - player_pools
  - import_history (where week_id is not null)
  - week_status_overrides
- Also deletes NFL schedule data for non-2025 seasons

Run with: python backend/scripts/cleanup_non_2025_seasons.py
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Database configuration
# Will use DATABASE_URL from environment or .env file, fallback to default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://cortex:cortex@localhost:5432/cortex"
)


def cleanup_non_2025_seasons():
    """Delete all weeks and related data for seasons other than 2025."""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # First, get counts of what will be deleted
        print("Checking current data...")
        
        # Count weeks by season
        weeks_result = session.execute(
            text("""
                SELECT season, COUNT(*) as count
                FROM weeks
                GROUP BY season
                ORDER BY season
            """)
        )
        weeks_by_season = weeks_result.fetchall()
        
        print("\nWeeks by season:")
        total_weeks_to_delete = 0
        for season, count in weeks_by_season:
            if season == 2025:
                print(f"  Season {season}: {count} weeks (KEEPING)")
            else:
                print(f"  Season {season}: {count} weeks (WILL DELETE)")
                total_weeks_to_delete += count
        
        if total_weeks_to_delete == 0:
            print("\n✅ No non-2025 weeks found. Nothing to delete.")
            return
        
        # Count related data that will be cascade deleted
        print("\nRelated data that will be cascade deleted:")
        
        # Count week_metadata
        metadata_result = session.execute(
            text("""
                SELECT COUNT(*) 
                FROM week_metadata wm
                INNER JOIN weeks w ON wm.week_id = w.id
                WHERE w.season != 2025
            """)
        )
        metadata_count = metadata_result.scalar()
        print(f"  week_metadata: {metadata_count} records")
        
        # Count player_pools
        pools_result = session.execute(
            text("""
                SELECT COUNT(*) 
                FROM player_pools pp
                INNER JOIN weeks w ON pp.week_id = w.id
                WHERE w.season != 2025
            """)
        )
        pools_count = pools_result.scalar()
        print(f"  player_pools: {pools_count} records")
        
        # Count import_history
        import_result = session.execute(
            text("""
                SELECT COUNT(*) 
                FROM import_history ih
                INNER JOIN weeks w ON ih.week_id = w.id
                WHERE w.season != 2025
            """)
        )
        import_count = import_result.scalar()
        print(f"  import_history: {import_count} records")
        
        # Count week_status_overrides
        override_result = session.execute(
            text("""
                SELECT COUNT(*) 
                FROM week_status_overrides wso
                INNER JOIN weeks w ON wso.week_id = w.id
                WHERE w.season != 2025
            """)
        )
        override_count = override_result.scalar()
        print(f"  week_status_overrides: {override_count} records")
        
        # Count NFL schedule data
        schedule_result = session.execute(
            text("SELECT COUNT(*) FROM nfl_schedule WHERE season != 2025")
        )
        schedule_count = schedule_result.scalar()
        print(f"  nfl_schedule: {schedule_count} records")
        
        print(f"\n⚠️  Total: {total_weeks_to_delete} weeks will be deleted")
        print(f"   Plus all related data listed above")
        
        # Confirm deletion
        response = input("\nProceed with deletion? (yes/no): ")
        if response.lower() != 'yes':
            print("Deletion cancelled.")
            return
        
        print("\nDeleting data...")
        
        # Delete NFL schedule data for non-2025 seasons first
        if schedule_count > 0:
            session.execute(
                text("DELETE FROM nfl_schedule WHERE season != 2025")
            )
            print(f"  ✅ Deleted {schedule_count} NFL schedule records")
        
        # Delete weeks (this will cascade delete related data)
        # Note: CASCADE delete will handle:
        # - week_metadata
        # - player_pools
        # - import_history (where week_id is not null)
        # - week_status_overrides
        delete_result = session.execute(
            text("DELETE FROM weeks WHERE season != 2025")
        )
        deleted_count = delete_result.rowcount
        session.commit()
        
        print(f"  ✅ Deleted {deleted_count} weeks")
        print(f"  ✅ Related data automatically deleted via CASCADE")
        
        # Verify deletion
        remaining_result = session.execute(
            text("SELECT COUNT(*) FROM weeks WHERE season != 2025")
        )
        remaining = remaining_result.scalar()
        
        if remaining == 0:
            print("\n✅ Successfully deleted all non-2025 weeks and related data!")
            
            # Show what remains
            remaining_2025 = session.execute(
                text("SELECT COUNT(*) FROM weeks WHERE season = 2025")
            )
            count_2025 = remaining_2025.scalar()
            print(f"\nRemaining: {count_2025} weeks for season 2025")
        else:
            print(f"\n⚠️  Warning: {remaining} non-2025 weeks still remain")
            
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    cleanup_non_2025_seasons()
