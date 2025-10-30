"""
Tests for Data Import System Integration with Week Management.

Tests the integration between the Data Import System and Week Management including:
- Week locking after successful import
- Import status badge updates
- Error handling during import
"""

import pytest
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.services.week_management_service import WeekManagementService


class TestImportIntegration:
    """Tests for Data Import System integration with Week Management."""

    @pytest.fixture
    def service(self, db_session: Session):
        """Create a WeekManagementService instance."""
        return WeekManagementService(db_session)

    def test_week_is_locked_after_successful_import(self, db_session: Session, service: WeekManagementService):
        """
        Test 10.1.1: Week is locked after successful import.

        When Data Import System completes import:
        1. Backend calls PUT /api/weeks/{week_id}/lock
        2. Pass import_id and player_count
        3. Backend sets is_locked=true, locked_at=NOW()
        """
        # Setup: Create a week
        db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status, nfl_slate_date)
                VALUES (:season, :week_number, :status, :nfl_slate_date)
            """),
            {
                "season": 2025,
                "week_number": 5,
                "status": "active",
                "nfl_slate_date": "2025-10-05"
            }
        )
        db_session.commit()

        # Get the week ID
        result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = :season AND week_number = :week_number"),
            {"season": 2025, "week_number": 5}
        )
        week_id = result.scalar()
        assert week_id is not None

        # Setup: Create week_metadata entry (required by lock_week)
        db_session.execute(
            text("""
                INSERT INTO week_metadata (week_id, season, week_number, nfl_slate_date, kickoff_time)
                VALUES (:week_id, :season, :week_number, :nfl_slate_date, :kickoff_time)
            """),
            {
                "week_id": week_id,
                "season": 2025,
                "week_number": 5,
                "nfl_slate_date": "2025-10-05",
                "kickoff_time": "13:00"
            }
        )
        db_session.commit()

        # Execute: Call lock_week with import_id and player_count
        import_id = "test-import-uuid-12345"
        player_count = 153

        locked_week = service.lock_week(week_id, import_id, player_count)

        # Assert: Week is locked
        assert locked_week["is_locked"] in (True, 1)
        assert locked_week["locked_at"] is not None

        # Verify in database
        result = db_session.execute(
            text("SELECT is_locked, locked_at FROM weeks WHERE id = :id"),
            {"id": week_id}
        )
        is_locked, locked_at = result.fetchone()
        assert is_locked in (True, 1)
        assert locked_at is not None

        # Verify metadata updated
        result = db_session.execute(
            text("""
                SELECT import_status, import_count, import_timestamp
                FROM week_metadata
                WHERE week_id = :week_id
            """),
            {"week_id": week_id}
        )
        import_status, import_count, import_timestamp = result.fetchone()
        assert import_status == "imported"
        assert import_count == player_count
        assert import_timestamp is not None

    def test_import_status_badge_updates(self, db_session: Session, service: WeekManagementService):
        """
        Test 10.1.2: Import status badge updates.

        When Data Import System calls PUT /api/weeks/{id}/import-status:
        1. Pass: status='imported', import_count, import_timestamp
        2. Backend updates week_metadata
        3. Frontend receives response and updates store
        """
        # Setup: Create a week
        db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status, nfl_slate_date)
                VALUES (:season, :week_number, :status, :nfl_slate_date)
            """),
            {
                "season": 2025,
                "week_number": 6,
                "status": "upcoming",
                "nfl_slate_date": "2025-10-12"
            }
        )
        db_session.commit()

        # Get the week ID
        result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = :season AND week_number = :week_number"),
            {"season": 2025, "week_number": 6}
        )
        week_id = result.scalar()
        assert week_id is not None

        # Setup: Create week_metadata entry with pending status
        db_session.execute(
            text("""
                INSERT INTO week_metadata (week_id, season, week_number, nfl_slate_date, kickoff_time, import_status, import_count)
                VALUES (:week_id, :season, :week_number, :nfl_slate_date, :kickoff_time, :import_status, :import_count)
            """),
            {
                "week_id": week_id,
                "season": 2025,
                "week_number": 6,
                "nfl_slate_date": "2025-10-12",
                "kickoff_time": "13:00",
                "import_status": "pending",
                "import_count": 0
            }
        )
        db_session.commit()

        # Execute: Update import status to 'imported'
        import_timestamp = datetime.utcnow().isoformat()
        import_count = 162

        db_session.execute(
            text("""
                UPDATE week_metadata
                SET import_status = :status,
                    import_count = :count,
                    import_timestamp = :timestamp,
                    updated_at = CURRENT_TIMESTAMP
                WHERE week_id = :week_id
            """),
            {
                "status": "imported",
                "count": import_count,
                "timestamp": import_timestamp,
                "week_id": week_id,
            }
        )
        db_session.commit()

        # Assert: Import status updated in database
        result = db_session.execute(
            text("""
                SELECT import_status, import_count, import_timestamp
                FROM week_metadata
                WHERE week_id = :week_id
            """),
            {"week_id": week_id}
        )
        status, count, timestamp = result.fetchone()
        assert status == "imported"
        assert count == import_count
        assert timestamp is not None

        # Verify that frontend can get the updated week
        weeks = service.get_weeks_by_year(2025)
        week_6 = next((w for w in weeks if w["week_number"] == 6), None)
        assert week_6 is not None
        assert week_6["metadata"]["import_status"] == "imported"
        assert week_6["metadata"]["import_count"] == import_count


class TestImportErrorHandling:
    """Tests for error handling during import process."""

    @pytest.fixture
    def service(self, db_session: Session):
        """Create a WeekManagementService instance."""
        return WeekManagementService(db_session)

    def test_import_error_status_displayed(self, db_session: Session, service: WeekManagementService):
        """
        Test that import error status is properly recorded and displayed.

        When Data Import System calls PUT /api/weeks/{id}/import-status with status='error':
        1. Pass: error_message
        2. Frontend shows orange warning icon
        3. Tooltip shows error message
        """
        # Setup: Create a week
        db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status, nfl_slate_date)
                VALUES (:season, :week_number, :status, :nfl_slate_date)
            """),
            {
                "season": 2025,
                "week_number": 7,
                "status": "upcoming",
                "nfl_slate_date": "2025-10-19"
            }
        )
        db_session.commit()

        # Get the week ID
        result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = :season AND week_number = :week_number"),
            {"season": 2025, "week_number": 7}
        )
        week_id = result.scalar()
        assert week_id is not None

        # Setup: Create week_metadata entry
        db_session.execute(
            text("""
                INSERT INTO week_metadata (week_id, season, week_number, nfl_slate_date, kickoff_time, import_status)
                VALUES (:week_id, :season, :week_number, :nfl_slate_date, :kickoff_time, :import_status)
            """),
            {
                "week_id": week_id,
                "season": 2025,
                "week_number": 7,
                "nfl_slate_date": "2025-10-19",
                "kickoff_time": "13:00",
                "import_status": "pending"
            }
        )
        db_session.commit()

        # Execute: Update import status to 'error' with message
        error_message = "Failed to match players: 5 players not found in database"

        db_session.execute(
            text("""
                UPDATE week_metadata
                SET import_status = :status,
                    import_error_message = :error_message,
                    updated_at = CURRENT_TIMESTAMP
                WHERE week_id = :week_id
            """),
            {
                "status": "error",
                "error_message": error_message,
                "week_id": week_id,
            }
        )
        db_session.commit()

        # Assert: Error status and message recorded
        result = db_session.execute(
            text("""
                SELECT import_status, import_error_message
                FROM week_metadata
                WHERE week_id = :week_id
            """),
            {"week_id": week_id}
        )
        status, stored_error = result.fetchone()
        assert status == "error"
        assert stored_error == error_message

        # Verify frontend can retrieve error details
        nfl_service = __import__('backend.services.nfl_schedule_service', fromlist=['NFLScheduleService']).NFLScheduleService(db_session)
        metadata = nfl_service.get_week_metadata(week_id)
        assert metadata is not None
        assert metadata["import_status"] == "error"
        assert metadata.get("error_message") == error_message
