"""
Tests for Week Management API endpoints.

Tests the REST API endpoints for managing NFL weeks including:
- GET /api/weeks - retrieve weeks by year
- GET /api/current-week - get current active week
- GET /api/weeks/{id}/metadata - retrieve week metadata
- PUT /api/weeks/{id}/status - update week status
- POST /api/weeks/generate - generate weeks for a season
- PUT /api/weeks/{id}/lock - lock a week after import
- PUT /api/weeks/{id}/import-status - update import status
- GET /api/nfl-schedule - get NFL schedule
"""

import pytest
from datetime import datetime, date, time
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.services.week_management_service import (
    WeekManagementService,
    WeekLockedError,
    WeekNotFoundError,
    InvalidYearError,
)
from backend.services.nfl_schedule_service import NFLScheduleService


class TestGetWeeksEndpointLogic:
    """Tests for GET /api/weeks endpoint logic."""

    def test_get_weeks_returns_18_weeks(self, db_session: Session):
        """Test that GET /api/weeks?year=2025 returns 18 weeks."""
        # Setup: Create weeks for 2025
        service = WeekManagementService(db_session)
        service.create_weeks_for_season(2025)

        # Execute
        weeks = service.get_weeks_by_year(2025)

        # Assert
        assert len(weeks) == 18
        assert weeks[0]["week_number"] == 1
        assert weeks[-1]["week_number"] == 18

        # Verify structure matches API response
        for week in weeks:
            assert "id" in week
            assert "season" in week
            assert "week_number" in week
            assert "status" in week
            assert "nfl_slate_date" in week
            assert "metadata" in week

    def test_get_weeks_with_invalid_year_raises_error(self, db_session: Session):
        """Test that GET /api/weeks with invalid year raises InvalidYearError."""
        # Execute & Assert
        service = WeekManagementService(db_session)
        with pytest.raises(InvalidYearError):
            service.create_weeks_for_season(2000)


class TestGetCurrentWeekEndpointLogic:
    """Tests for GET /api/current-week endpoint logic."""

    def test_get_current_week_returns_current_week_correctly(self, db_session: Session):
        """Test that GET /api/current-week returns current week correctly."""
        # Setup: Create weeks for 2025
        service = WeekManagementService(db_session)
        service.create_weeks_for_season(2025)

        # Execute
        current_week_data = service.get_current_week()

        # Assert - the service returns a week dict directly
        assert "week_number" in current_week_data
        assert 1 <= current_week_data.get("week_number", 1) <= 18
        # Verify it has the expected week fields
        assert "id" in current_week_data
        assert "status" in current_week_data


class TestGetWeekMetadataEndpointLogic:
    """Tests for GET /api/weeks/{id}/metadata endpoint logic."""

    def test_get_week_metadata_returns_full_metadata(self, db_session: Session):
        """Test that GET /api/weeks/{id}/metadata returns full metadata."""
        # Setup: Create weeks for 2025
        service = WeekManagementService(db_session)
        service.create_weeks_for_season(2025)

        # Get week ID
        result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = :season AND week_number = :week"),
            {"season": 2025, "week": 1}
        )
        week_id = result.scalar()

        # Execute
        nfl_service = NFLScheduleService(db_session)
        metadata = nfl_service.get_week_metadata(week_id)

        # Assert
        assert metadata is not None
        assert "season" in metadata
        assert "week_number" in metadata
        assert "nfl_slate_date" in metadata
        assert "kickoff_time" in metadata
        assert "espn_link" in metadata
        assert "import_status" in metadata


class TestUpdateWeekStatusEndpointLogic:
    """Tests for PUT /api/weeks/{id}/status endpoint logic."""

    def test_update_week_status_updates_status_override(self, db_session: Session):
        """Test that PUT /api/weeks/{id}/status updates status_override."""
        # Setup: Create weeks for 2025
        service = WeekManagementService(db_session)
        service.create_weeks_for_season(2025)

        # Get week ID
        result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = :season AND week_number = :week"),
            {"season": 2025, "week": 1}
        )
        week_id = result.scalar()

        # Execute
        updated_week = service.update_week_status(week_id, "active", "Manual override")

        # Assert
        assert updated_week["status_override"] == "active"


class TestGenerateWeeksEndpointLogic:
    """Tests for POST /api/weeks/generate endpoint logic."""

    def test_generate_weeks_creates_weeks_for_new_year(self, db_session: Session):
        """Test that POST /api/weeks/generate creates weeks for new year."""
        # Execute
        service = WeekManagementService(db_session)
        weeks_created = service.create_weeks_for_season(2026)

        # Assert
        assert weeks_created == 18


class TestLockWeekEndpointLogic:
    """Tests for PUT /api/weeks/{id}/lock endpoint logic."""

    def test_lock_week_locks_week_and_updates_metadata(self, db_session: Session):
        """Test that PUT /api/weeks/{id}/lock locks week and updates metadata."""
        # Setup: Create weeks for 2025
        service = WeekManagementService(db_session)
        service.create_weeks_for_season(2025)

        # Get week ID
        result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = :season AND week_number = :week"),
            {"season": 2025, "week": 1}
        )
        week_id = result.scalar()

        # Execute
        updated_week = service.lock_week(week_id, "test-import-id", 153)

        # Assert
        assert updated_week["is_locked"] is True
        assert updated_week["locked_at"] is not None


class TestLockedWeeksPreventsModification:
    """Tests for locked week error handling."""

    def test_locked_weeks_prevent_modification_raises_error(self, db_session: Session):
        """Test that locked weeks prevent modification with 409 error."""
        # Setup: Create weeks and lock one
        service = WeekManagementService(db_session)
        service.create_weeks_for_season(2025)

        # Get week ID
        result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = :season AND week_number = :week"),
            {"season": 2025, "week": 1}
        )
        week_id = result.scalar()

        # Lock the week
        service.lock_week(week_id, "test-import-id", 153)

        # Try to update status - should fail
        with pytest.raises(WeekLockedError):
            service.validate_week_immutability(week_id)


class TestInvalidYearErrorLogic:
    """Tests for invalid year error handling."""

    def test_invalid_year_raises_error(self, db_session: Session):
        """Test that invalid year returns 400 error."""
        # Execute & Assert
        service = WeekManagementService(db_session)
        with pytest.raises(InvalidYearError):
            service.create_weeks_for_season(2000)
