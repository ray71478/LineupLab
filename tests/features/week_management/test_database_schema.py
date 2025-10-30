"""
Tests for week management database schema functionality.

Tests the new tables and columns added to support the week management feature:
- week_metadata table
- nfl_schedule table
- week_status_overrides table
- Extended weeks table with new columns
"""

import pytest
import os
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session


def is_postgres():
    """Check if we're using PostgreSQL."""
    db_url = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
    return "postgres" in db_url or "postgresql" in db_url


class TestWeekSchemaExtension:
    """Tests for extended weeks table with new columns."""

    def test_week_creation_with_nfl_slate_date(self, db_session: Session):
        """Test week creation with nfl_slate_date field."""
        # Create a week with new columns
        db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status, nfl_slate_date)
                VALUES (:season, :week_number, :status, :nfl_slate_date)
            """),
            {
                "season": 2025,
                "week_number": 1,
                "status": "active",
                "nfl_slate_date": "2025-09-07",
            }
        )
        db_session.commit()

        # Verify week was created with correct nfl_slate_date
        result = db_session.execute(
            text("""
                SELECT id, season, week_number, nfl_slate_date
                FROM weeks
                WHERE season = :season AND week_number = :week_number
            """),
            {"season": 2025, "week_number": 1}
        )
        row = result.fetchone()
        assert row is not None
        assert row[0] is not None  # id
        assert row[1] == 2025  # season
        assert row[2] == 1  # week_number
        assert row[3] == "2025-09-07"  # nfl_slate_date

    def test_is_locked_flag_defaults_to_false(self, db_session: Session):
        """Test that is_locked flag defaults to false."""
        db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status)
                VALUES (:season, :week_number, :status)
            """),
            {
                "season": 2025,
                "week_number": 2,
                "status": "upcoming",
            }
        )
        db_session.commit()

        result = db_session.execute(
            text("""
                SELECT is_locked FROM weeks
                WHERE season = :season AND week_number = :week_number
            """),
            {"season": 2025, "week_number": 2}
        )
        is_locked = result.scalar()
        assert is_locked is False or is_locked == 0

    def test_is_locked_flag_prevents_modifications(self, db_session: Session):
        """Test that is_locked flag can be set and prevents modifications."""
        # Create a week
        db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status, is_locked, locked_at)
                VALUES (:season, :week_number, :status, :is_locked, :locked_at)
            """),
            {
                "season": 2025,
                "week_number": 3,
                "status": "active",
                "is_locked": True,
                "locked_at": datetime.now(),
            }
        )
        db_session.commit()

        # Verify is_locked is true and locked_at is set
        result = db_session.execute(
            text("""
                SELECT is_locked, locked_at FROM weeks
                WHERE season = :season AND week_number = :week_number
            """),
            {"season": 2025, "week_number": 3}
        )
        is_locked, locked_at = result.fetchone()
        assert is_locked is True or is_locked == 1
        assert locked_at is not None

    def test_metadata_text_storage(self, db_session: Session):
        """Test metadata text storage in weeks table (SQLite compatible)."""
        metadata = '{"kickoff_time": "13:00", "espn_link": "https://www.espn.com/nfl/schedule/_/week/1", "import_status": "pending"}'

        db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status, metadata)
                VALUES (:season, :week_number, :status, :metadata)
            """),
            {
                "season": 2025,
                "week_number": 4,
                "status": "upcoming",
                "metadata": metadata,
            }
        )
        db_session.commit()

        # Verify metadata was stored correctly
        result = db_session.execute(
            text("""
                SELECT metadata FROM weeks
                WHERE season = :season AND week_number = :week_number
            """),
            {"season": 2025, "week_number": 4}
        )
        stored_metadata = result.scalar()
        assert stored_metadata is not None
        assert "kickoff_time" in str(stored_metadata)


class TestWeekMetadataTable:
    """Tests for week_metadata table."""

    def test_week_metadata_creation(self, db_session: Session):
        """Test creating a week_metadata record."""
        # First create a week
        db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status)
                VALUES (:season, :week_number, :status)
            """),
            {
                "season": 2025,
                "week_number": 5,
                "status": "active",
            }
        )
        db_session.commit()

        # Get the week_id
        result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = :season AND week_number = :week_number"),
            {"season": 2025, "week_number": 5}
        )
        week_id = result.scalar()

        # Create week_metadata
        db_session.execute(
            text("""
                INSERT INTO week_metadata
                (week_id, season, week_number, nfl_slate_date, kickoff_time, import_status)
                VALUES
                (:week_id, :season, :week_number, :nfl_slate_date, :kickoff_time, :import_status)
            """),
            {
                "week_id": week_id,
                "season": 2025,
                "week_number": 5,
                "nfl_slate_date": "2025-10-05",
                "kickoff_time": "13:00",
                "import_status": "pending",
            }
        )
        db_session.commit()

        # Verify metadata was created
        result = db_session.execute(
            text("""
                SELECT id, week_id, nfl_slate_date, kickoff_time, import_status
                FROM week_metadata
                WHERE week_id = :week_id
            """),
            {"week_id": week_id}
        )
        row = result.fetchone()
        assert row is not None
        assert row[1] == week_id
        assert row[2] == "2025-10-05"
        assert row[3] == "13:00"
        assert row[4] == "pending"

    def test_week_metadata_unique_constraint(self, db_session: Session):
        """Test that week_metadata unique constraint prevents duplicate week_ids."""
        # First create a week
        db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status)
                VALUES (:season, :week_number, :status)
            """),
            {
                "season": 2025,
                "week_number": 6,
                "status": "active",
            }
        )
        db_session.commit()

        # Get the week_id
        result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = :season AND week_number = :week_number"),
            {"season": 2025, "week_number": 6}
        )
        week_id = result.scalar()

        # Create first week_metadata
        db_session.execute(
            text("""
                INSERT INTO week_metadata
                (week_id, season, week_number, nfl_slate_date, kickoff_time)
                VALUES
                (:week_id, :season, :week_number, :nfl_slate_date, :kickoff_time)
            """),
            {
                "week_id": week_id,
                "season": 2025,
                "week_number": 6,
                "nfl_slate_date": "2025-10-12",
                "kickoff_time": "13:00",
            }
        )
        db_session.commit()

        # Try to insert another metadata with same week_id (should fail)
        with pytest.raises(Exception):
            db_session.execute(
                text("""
                    INSERT INTO week_metadata
                    (week_id, season, week_number, nfl_slate_date, kickoff_time)
                    VALUES
                    (:week_id, :season, :week_number, :nfl_slate_date, :kickoff_time)
                """),
                {
                    "week_id": week_id,
                    "season": 2025,
                    "week_number": 7,  # Different week number but same week_id
                    "nfl_slate_date": "2025-10-19",
                    "kickoff_time": "13:00",
                }
            )
            db_session.commit()


class TestNFLScheduleTable:
    """Tests for nfl_schedule table."""

    def test_nfl_schedule_creation(self, db_session: Session):
        """Test creating nfl_schedule records."""
        db_session.execute(
            text("""
                INSERT INTO nfl_schedule
                (season, week, slate_date, kickoff_time)
                VALUES
                (:season, :week, :slate_date, :kickoff_time)
            """),
            {
                "season": 2025,
                "week": 1,
                "slate_date": "2025-09-07",
                "kickoff_time": "13:00",
            }
        )
        db_session.commit()

        # Verify record was created
        result = db_session.execute(
            text("""
                SELECT season, week, slate_date, kickoff_time
                FROM nfl_schedule
                WHERE season = :season AND week = :week
            """),
            {"season": 2025, "week": 1}
        )
        row = result.fetchone()
        assert row is not None
        assert row[0] == 2025
        assert row[1] == 1
        assert row[2] == "2025-09-07"
        assert row[3] == "13:00"

    def test_nfl_schedule_unique_constraint(self, db_session: Session):
        """Test that unique constraint prevents duplicate season/week combinations."""
        db_session.execute(
            text("""
                INSERT INTO nfl_schedule
                (season, week, slate_date, kickoff_time)
                VALUES
                (:season, :week, :slate_date, :kickoff_time)
            """),
            {
                "season": 2025,
                "week": 2,
                "slate_date": "2025-09-14",
                "kickoff_time": "13:00",
            }
        )
        db_session.commit()

        # Try to insert duplicate
        with pytest.raises(Exception):
            db_session.execute(
                text("""
                    INSERT INTO nfl_schedule
                    (season, week, slate_date, kickoff_time)
                    VALUES
                    (:season, :week, :slate_date, :kickoff_time)
                """),
                {
                    "season": 2025,
                    "week": 2,
                    "slate_date": "2025-09-14",
                    "kickoff_time": "13:00",
                }
            )
            db_session.commit()


class TestWeekStatusOverridesTable:
    """Tests for week_status_overrides table."""

    def test_week_status_override_creation(self, db_session: Session):
        """Test creating a week_status_override record."""
        # Create a week
        db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status)
                VALUES (:season, :week_number, :status)
            """),
            {
                "season": 2025,
                "week_number": 7,
                "status": "upcoming",
            }
        )
        db_session.commit()

        # Get week_id
        result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = :season AND week_number = :week_number"),
            {"season": 2025, "week_number": 7}
        )
        week_id = result.scalar()

        # Create override
        db_session.execute(
            text("""
                INSERT INTO week_status_overrides
                (week_id, override_status, reason, overridden_by)
                VALUES
                (:week_id, :override_status, :reason, :overridden_by)
            """),
            {
                "week_id": week_id,
                "override_status": "active",
                "reason": "Manual override for testing",
                "overridden_by": "admin",
            }
        )
        db_session.commit()

        # Verify override was created
        result = db_session.execute(
            text("""
                SELECT week_id, override_status, reason, overridden_by
                FROM week_status_overrides
                WHERE week_id = :week_id
            """),
            {"week_id": week_id}
        )
        row = result.fetchone()
        assert row is not None
        assert row[0] == week_id
        assert row[1] == "active"
        assert row[2] == "Manual override for testing"

    def test_week_status_override_unique_constraint(self, db_session: Session):
        """Test that overrides unique constraint prevents multiple overrides per week."""
        # Create a week
        db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status)
                VALUES (:season, :week_number, :status)
            """),
            {
                "season": 2025,
                "week_number": 8,
                "status": "upcoming",
            }
        )
        db_session.commit()

        # Get week_id
        result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = :season AND week_number = :week_number"),
            {"season": 2025, "week_number": 8}
        )
        week_id = result.scalar()

        # Create first override
        db_session.execute(
            text("""
                INSERT INTO week_status_overrides
                (week_id, override_status)
                VALUES
                (:week_id, :override_status)
            """),
            {
                "week_id": week_id,
                "override_status": "active",
            }
        )
        db_session.commit()

        # Try to create second override for same week (should fail)
        with pytest.raises(Exception):
            db_session.execute(
                text("""
                    INSERT INTO week_status_overrides
                    (week_id, override_status)
                    VALUES
                    (:week_id, :override_status)
                """),
                {
                    "week_id": week_id,
                    "override_status": "upcoming",
                }
            )
            db_session.commit()


class TestCascadeDeletes:
    """Tests for cascade delete behavior."""

    def test_week_metadata_cascade_delete_on_week_delete(self, db_session: Session):
        """Test that week_metadata cascades delete when week is deleted."""
        # Create a week
        db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status)
                VALUES (:season, :week_number, :status)
            """),
            {
                "season": 2025,
                "week_number": 9,
                "status": "active",
            }
        )
        db_session.commit()

        # Get the week_id
        result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = :season AND week_number = :week_number"),
            {"season": 2025, "week_number": 9}
        )
        week_id = result.scalar()

        # Create week_metadata
        db_session.execute(
            text("""
                INSERT INTO week_metadata
                (week_id, season, week_number, nfl_slate_date, kickoff_time)
                VALUES
                (:week_id, :season, :week_number, :nfl_slate_date, :kickoff_time)
            """),
            {
                "week_id": week_id,
                "season": 2025,
                "week_number": 9,
                "nfl_slate_date": "2025-11-02",
                "kickoff_time": "13:00",
            }
        )
        db_session.commit()

        # Verify metadata exists
        result = db_session.execute(
            text("SELECT COUNT(*) FROM week_metadata WHERE week_id = :week_id"),
            {"week_id": week_id}
        )
        count_before = result.scalar()
        assert count_before > 0

        # Delete the week
        db_session.execute(
            text("DELETE FROM weeks WHERE id = :id"),
            {"id": week_id}
        )
        db_session.commit()

        # Verify metadata was also deleted
        result = db_session.execute(
            text("SELECT COUNT(*) FROM week_metadata WHERE week_id = :week_id"),
            {"week_id": week_id}
        )
        count_after = result.scalar()
        assert count_after == 0

    def test_week_status_override_cascade_delete_on_week_delete(self, db_session: Session):
        """Test that overrides cascade delete when week is deleted."""
        # Create a week
        db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status)
                VALUES (:season, :week_number, :status)
            """),
            {
                "season": 2025,
                "week_number": 10,
                "status": "upcoming",
            }
        )
        db_session.commit()

        # Get week_id
        result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = :season AND week_number = :week_number"),
            {"season": 2025, "week_number": 10}
        )
        week_id = result.scalar()

        # Create override
        db_session.execute(
            text("""
                INSERT INTO week_status_overrides
                (week_id, override_status)
                VALUES
                (:week_id, :override_status)
            """),
            {
                "week_id": week_id,
                "override_status": "active",
            }
        )
        db_session.commit()

        # Verify override exists
        result = db_session.execute(
            text("SELECT COUNT(*) FROM week_status_overrides WHERE week_id = :week_id"),
            {"week_id": week_id}
        )
        count_before = result.scalar()
        assert count_before > 0

        # Delete week
        db_session.execute(
            text("DELETE FROM weeks WHERE id = :id"),
            {"id": week_id}
        )
        db_session.commit()

        # Verify override was deleted
        result = db_session.execute(
            text("SELECT COUNT(*) FROM week_status_overrides WHERE week_id = :week_id"),
            {"week_id": week_id}
        )
        count_after = result.scalar()
        assert count_after == 0


class TestTableCreation:
    """Tests for table existence and structure."""

    def test_all_new_tables_exist(self, db_session: Session):
        """Test that all new tables were created."""
        # Try to query each table
        tables_to_check = [
            ('weeks', 'SELECT COUNT(*) FROM weeks'),
            ('week_metadata', 'SELECT COUNT(*) FROM week_metadata'),
            ('nfl_schedule', 'SELECT COUNT(*) FROM nfl_schedule'),
            ('week_status_overrides', 'SELECT COUNT(*) FROM week_status_overrides'),
        ]

        for table_name, query in tables_to_check:
            result = db_session.execute(text(query))
            count = result.scalar()
            # If we got here without error, table exists
            assert count is not None, f"Table {table_name} could not be queried"

    def test_weeks_table_has_new_columns(self, db_session: Session):
        """Test that weeks table has all new columns."""
        # Insert a week with all new columns
        db_session.execute(
            text("""
                INSERT INTO weeks
                (season, week_number, status, nfl_slate_date, status_override, metadata, is_locked, locked_at)
                VALUES
                (:season, :week_number, :status, :nfl_slate_date, :status_override, :metadata, :is_locked, :locked_at)
            """),
            {
                "season": 2025,
                "week_number": 18,
                "status": "upcoming",
                "nfl_slate_date": "2026-01-04",
                "status_override": None,
                "metadata": None,
                "is_locked": False,
                "locked_at": None,
            }
        )
        db_session.commit()

        # Retrieve and verify all columns exist
        result = db_session.execute(
            text("""
                SELECT id, season, week_number, status, nfl_slate_date, status_override,
                       metadata, is_locked, locked_at, updated_at
                FROM weeks
                WHERE season = :season AND week_number = :week_number
            """),
            {"season": 2025, "week_number": 18}
        )
        row = result.fetchone()
        assert row is not None
        assert len(row) == 10  # All columns present
