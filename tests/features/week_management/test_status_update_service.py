"""
Tests for StatusUpdateService.

Tests the status update logic including:
- Determining week status based on NFL slate dates
- Handling timezone-aware date comparisons (ET)
- Applying manual status overrides
- Updating all week statuses for a season
"""

import pytest
from datetime import datetime, date, time
from pytz import timezone
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.services.status_update_service import StatusUpdateService


class TestStatusUpdateService:
    """Tests for StatusUpdateService class."""

    @pytest.fixture
    def service(self, db_session: Session):
        """Create a StatusUpdateService instance."""
        return StatusUpdateService(db_session)

    @pytest.fixture
    def setup_weeks_for_status_testing(self, db_session: Session):
        """Set up weeks with various NFL slate dates for status testing."""
        # Use ET timezone for comparisons
        et = timezone('America/New_York')

        # Create test weeks with different slate dates
        # Week 1: Past (2025-09-07)
        # Week 5: Current (2025-10-05) - assuming current date is around 10-05
        # Week 10: Future (2025-11-09)

        weeks_data = [
            (1, 2025, date(2025, 9, 7), "upcoming"),  # Past week
            (5, 2025, date(2025, 10, 5), "upcoming"),  # Current week (approx)
            (10, 2025, date(2025, 11, 9), "upcoming"),  # Future week
        ]

        week_ids = []
        for week_num, season, slate_date, status in weeks_data:
            # Create week
            result = db_session.execute(
                text("""
                    INSERT INTO weeks (season, week_number, status, nfl_slate_date, status_override)
                    VALUES (:season, :week_number, :status, :nfl_slate_date, NULL)
                    RETURNING id
                """),
                {
                    "season": season,
                    "week_number": week_num,
                    "status": status,
                    "nfl_slate_date": slate_date,
                }
            )
            db_session.commit()
            week_id = result.scalar()
            week_ids.append(week_id)

            # Create week_metadata entry
            db_session.execute(
                text("""
                    INSERT INTO week_metadata
                    (week_id, season, week_number, nfl_slate_date, kickoff_time, import_status)
                    VALUES (:week_id, :season, :week_number, :nfl_slate_date, :kickoff_time, :import_status)
                """),
                {
                    "week_id": week_id,
                    "season": season,
                    "week_number": week_num,
                    "nfl_slate_date": slate_date,
                    "kickoff_time": "13:00",  # Use string format for SQLite compatibility
                    "import_status": "pending",
                }
            )
            db_session.commit()

        return week_ids, weeks_data

    def test_determine_week_status_returns_completed_for_past_weeks(
        self, db_session: Session, service: StatusUpdateService, setup_weeks_for_status_testing
    ):
        """Test that determine_week_status() returns 'completed' for past weeks."""
        week_ids, weeks_data = setup_weeks_for_status_testing

        # Use a current date that's after the first week's slate date
        past_date = date(2025, 9, 15)  # After 2025-09-07

        # Get week 1 (2025-09-07)
        result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = :season AND week_number = :week_number"),
            {"season": 2025, "week_number": 1}
        )
        week_id = result.scalar()

        # Determine status for past week
        status = service.determine_week_status(week_id, past_date)

        assert status == "completed", f"Expected 'completed' for past week, got '{status}'"

    def test_determine_week_status_returns_active_for_current_week(
        self, db_session: Session, service: StatusUpdateService, setup_weeks_for_status_testing
    ):
        """Test that determine_week_status() returns 'active' for current week."""
        week_ids, weeks_data = setup_weeks_for_status_testing

        # Use the current date matching the week's slate date
        current_date = date(2025, 10, 5)

        # Get week 5 (2025-10-05)
        result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = :season AND week_number = :week_number"),
            {"season": 2025, "week_number": 5}
        )
        week_id = result.scalar()

        # Determine status for current week
        status = service.determine_week_status(week_id, current_date)

        assert status == "active", f"Expected 'active' for current week, got '{status}'"

    def test_determine_week_status_returns_upcoming_for_future_weeks(
        self, db_session: Session, service: StatusUpdateService, setup_weeks_for_status_testing
    ):
        """Test that determine_week_status() returns 'upcoming' for future weeks."""
        week_ids, weeks_data = setup_weeks_for_status_testing

        # Use a current date that's before the future week's slate date
        future_date = date(2025, 10, 1)  # Before 2025-11-09

        # Get week 10 (2025-11-09)
        result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = :season AND week_number = :week_number"),
            {"season": 2025, "week_number": 10}
        )
        week_id = result.scalar()

        # Determine status for future week
        status = service.determine_week_status(week_id, future_date)

        assert status == "upcoming", f"Expected 'upcoming' for future week, got '{status}'"

    def test_apply_manual_overrides_respects_status_override_column(
        self, db_session: Session, service: StatusUpdateService, setup_weeks_for_status_testing
    ):
        """Test that apply_manual_overrides() respects status_override column."""
        week_ids, weeks_data = setup_weeks_for_status_testing

        # Get week 1 and set a manual override
        result = db_session.execute(
            text("SELECT id, nfl_slate_date FROM weeks WHERE season = :season AND week_number = :week_number"),
            {"season": 2025, "week_number": 1}
        )
        row = result.fetchone()
        week_id, nfl_slate_date = row

        # Set a manual override in the database
        db_session.execute(
            text("""
                UPDATE weeks
                SET status_override = :override_status
                WHERE id = :week_id
            """),
            {
                "week_id": week_id,
                "override_status": "active"
            }
        )
        db_session.commit()

        # Create the override record in week_status_overrides
        db_session.execute(
            text("""
                INSERT INTO week_status_overrides (week_id, override_status, reason)
                VALUES (:week_id, :override_status, :reason)
            """),
            {
                "week_id": week_id,
                "override_status": "active",
                "reason": "Manual override for testing"
            }
        )
        db_session.commit()

        # Apply manual overrides with a date that would normally make this "completed"
        past_date = date(2025, 9, 15)
        final_status = service.apply_manual_overrides(week_id, nfl_slate_date, past_date)

        # Should return the override status, not the auto-calculated status
        assert final_status == "active", f"Expected override 'active', got '{final_status}'"
