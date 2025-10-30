"""
Tests for WeekManagementService.

Tests the core business logic for week management including:
- Creating weeks for a season
- Retrieving weeks by year with metadata
- Getting the current week
- Locking weeks
- Validating week immutability
- Updating week status
"""

import pytest
from datetime import datetime, date
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.services.week_management_service import WeekManagementService
from backend.exceptions import CortexException


class TestWeekManagementService:
    """Tests for WeekManagementService class."""

    @pytest.fixture
    def service(self, db_session: Session):
        """Create a WeekManagementService instance."""
        return WeekManagementService(db_session)

    def test_create_weeks_for_season_generates_18_weeks(self, db_session: Session, service: WeekManagementService):
        """Test that create_weeks_for_season() generates exactly 18 weeks."""
        # NFL schedule is already seeded in fixture for 2025
        # Create weeks for season 2025
        count = service.create_weeks_for_season(2025)

        # Verify 18 weeks were created
        assert count == 18

        # Verify all 18 weeks exist in database
        result = db_session.execute(
            text("SELECT COUNT(*) FROM weeks WHERE season = :season"),
            {"season": 2025}
        )
        assert result.scalar() == 18

    def test_get_weeks_by_year_returns_all_weeks_with_metadata(self, db_session: Session, service: WeekManagementService):
        """Test that get_weeks_by_year() returns all 18 weeks with metadata."""
        # Create weeks for 2025
        service.create_weeks_for_season(2025)

        # Get weeks by year
        weeks = service.get_weeks_by_year(2025)

        # Verify we have 18 weeks
        assert len(weeks) == 18

        # Verify weeks are sorted by week_number
        for i, week in enumerate(weeks, 1):
            assert week["week_number"] == i
            assert week["season"] == 2025
            assert "status" in week
            assert "nfl_slate_date" in week
            assert "metadata" in week

    def test_get_current_week_correctly_identifies_current_week(self, db_session: Session, service: WeekManagementService):
        """Test that get_current_week() correctly identifies the current week."""
        # Create weeks for 2025
        service.create_weeks_for_season(2025)

        # Get current week
        current_week = service.get_current_week()

        # Verify current_week is returned
        assert current_week is not None
        assert "week_number" in current_week
        assert "status" in current_week
        assert 1 <= current_week["week_number"] <= 18

    def test_lock_week_sets_is_locked_and_locked_at(self, db_session: Session, service: WeekManagementService):
        """Test that lock_week() sets is_locked=true and locked_at timestamp."""
        # Create a week
        db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status)
                VALUES (:season, :week_number, :status)
            """),
            {"season": 2025, "week_number": 1, "status": "active"}
        )
        db_session.commit()

        # Get the week ID
        result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = :season AND week_number = :week_number"),
            {"season": 2025, "week_number": 1}
        )
        week_id = result.scalar()

        # Create week_metadata entry (required by lock_week)
        db_session.execute(
            text("""
                INSERT INTO week_metadata (week_id, season, week_number, nfl_slate_date, kickoff_time)
                VALUES (:week_id, :season, :week_number, :nfl_slate_date, :kickoff_time)
            """),
            {
                "week_id": week_id,
                "season": 2025,
                "week_number": 1,
                "nfl_slate_date": "2025-09-07",
                "kickoff_time": "13:00",
            }
        )
        db_session.commit()

        # Lock the week
        locked_week = service.lock_week(week_id, "import-123", 153)

        # Verify is_locked is set
        assert locked_week["is_locked"] is True
        assert locked_week["locked_at"] is not None

        # Verify in database
        result = db_session.execute(
            text("SELECT is_locked, locked_at FROM weeks WHERE id = :id"),
            {"id": week_id}
        )
        row = result.fetchone()
        assert row[0] is True or row[0] == 1
        assert row[1] is not None

    def test_validate_week_immutability_raises_error_for_locked_weeks(self, db_session: Session, service: WeekManagementService):
        """Test that validate_week_immutability() raises error for locked weeks."""
        # Create and lock a week
        db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status, is_locked, locked_at)
                VALUES (:season, :week_number, :status, :is_locked, :locked_at)
            """),
            {
                "season": 2025,
                "week_number": 1,
                "status": "active",
                "is_locked": True,
                "locked_at": datetime.now(),
            }
        )
        db_session.commit()

        # Get the week ID
        result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = :season AND week_number = :week_number"),
            {"season": 2025, "week_number": 1}
        )
        week_id = result.scalar()

        # Verify exception is raised
        with pytest.raises(CortexException):
            service.validate_week_immutability(week_id)

    def test_update_week_status_updates_status_override_correctly(self, db_session: Session, service: WeekManagementService):
        """Test that update_week_status() updates status_override correctly."""
        # Create a week
        db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status)
                VALUES (:season, :week_number, :status)
            """),
            {"season": 2025, "week_number": 1, "status": "upcoming"}
        )
        db_session.commit()

        # Get the week ID
        result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = :season AND week_number = :week_number"),
            {"season": 2025, "week_number": 1}
        )
        week_id = result.scalar()

        # Create week_metadata entry (required for update_week_status return value)
        db_session.execute(
            text("""
                INSERT INTO week_metadata (week_id, season, week_number, nfl_slate_date, kickoff_time)
                VALUES (:week_id, :season, :week_number, :nfl_slate_date, :kickoff_time)
            """),
            {
                "week_id": week_id,
                "season": 2025,
                "week_number": 1,
                "nfl_slate_date": "2025-09-07",
                "kickoff_time": "13:00",
            }
        )
        db_session.commit()

        # Update week status
        updated_week = service.update_week_status(week_id, "active", "Testing override")

        # Verify status override is set
        assert updated_week["status_override"] == "active"

        # Verify in database
        result = db_session.execute(
            text("SELECT status_override FROM weeks WHERE id = :id"),
            {"id": week_id}
        )
        status_override = result.scalar()
        assert status_override == "active"

        # Verify week_status_overrides table has entry
        result = db_session.execute(
            text("SELECT override_status FROM week_status_overrides WHERE week_id = :week_id"),
            {"week_id": week_id}
        )
        override = result.scalar()
        assert override == "active"
