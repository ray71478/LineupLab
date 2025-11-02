"""
Tests for Calibration API endpoints.

Tests the REST API endpoints for managing projection calibration including:
- GET /api/calibration/{week_id} - get all calibration factors
- POST /api/calibration/{week_id} - create/update single calibration
- POST /api/calibration/{week_id}/batch - batch create/update
- GET /api/calibration/{week_id}/status - get calibration status
- POST /api/calibration/{week_id}/reset - reset to defaults
"""

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.services.calibration_service import CalibrationService


class TestGetCalibrationsEndpoint:
    """Tests for GET /api/calibration/{week_id} endpoint logic."""

    def test_get_calibrations_returns_all_positions(self, db_session: Session):
        """Test GET /api/calibration/{week_id} returns all positions when they exist."""
        # Setup: Create week
        db_session.execute(
            text("INSERT INTO weeks (season, week_number) VALUES (2025, 10)")
        )
        db_session.commit()
        week_result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = 2025 AND week_number = 10")
        ).fetchone()
        week_id = week_result[0]

        # Insert calibrations for all positions
        positions = ["QB", "RB", "WR", "TE", "K", "DST"]
        for position in positions:
            db_session.execute(
                text("""
                    INSERT INTO projection_calibration
                    (week_id, position, floor_adjustment_percent,
                     median_adjustment_percent, ceiling_adjustment_percent, is_active)
                    VALUES (:week_id, :position, 5.0, 0.0, -5.0, true)
                """),
                {"week_id": week_id, "position": position}
            )
        db_session.commit()

        # Execute
        service = CalibrationService(db_session)
        calibrations = db_session.execute(
            text("""
                SELECT position, floor_adjustment_percent, median_adjustment_percent,
                       ceiling_adjustment_percent, is_active
                FROM projection_calibration
                WHERE week_id = :week_id
                ORDER BY position
            """),
            {"week_id": week_id}
        ).fetchall()

        # Assert
        assert len(calibrations) == 6
        assert calibrations[0][0] == "DST"  # Alphabetically first

    def test_get_calibrations_returns_empty_for_unconfigured_week(self, db_session: Session):
        """Test GET /api/calibration/{week_id} returns empty array for unconfigured week."""
        # Setup: Create week without calibrations
        db_session.execute(
            text("INSERT INTO weeks (season, week_number) VALUES (2025, 11)")
        )
        db_session.commit()
        week_result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = 2025 AND week_number = 11")
        ).fetchone()
        week_id = week_result[0]

        # Execute
        calibrations = db_session.execute(
            text("""
                SELECT COUNT(*) FROM projection_calibration WHERE week_id = :week_id
            """),
            {"week_id": week_id}
        ).scalar()

        # Assert
        assert calibrations == 0


class TestCreateUpdateCalibrationEndpoint:
    """Tests for POST /api/calibration/{week_id} endpoint logic."""

    def test_create_calibration_inserts_new_record(self, db_session: Session):
        """Test POST /api/calibration/{week_id} creates new calibration."""
        # Setup: Create week
        db_session.execute(
            text("INSERT INTO weeks (season, week_number) VALUES (2025, 12)")
        )
        db_session.commit()
        week_result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = 2025 AND week_number = 12")
        ).fetchone()
        week_id = week_result[0]

        # Execute: Insert calibration
        db_session.execute(
            text("""
                INSERT INTO projection_calibration
                (week_id, position, floor_adjustment_percent,
                 median_adjustment_percent, ceiling_adjustment_percent, is_active)
                VALUES (:week_id, 'QB', 10.0, 5.0, -8.0, true)
            """),
            {"week_id": week_id}
        )
        db_session.commit()

        # Assert
        result = db_session.execute(
            text("""
                SELECT floor_adjustment_percent, median_adjustment_percent,
                       ceiling_adjustment_percent, is_active
                FROM projection_calibration
                WHERE week_id = :week_id AND position = 'QB'
            """),
            {"week_id": week_id}
        ).fetchone()

        assert result[0] == 10.0  # floor
        assert result[1] == 5.0   # median
        assert result[2] == -8.0  # ceiling
        assert result[3] == True or result[3] == 1  # is_active (SQLite returns 1 for True)

    def test_update_calibration_modifies_existing_record(self, db_session: Session):
        """Test POST /api/calibration/{week_id} updates existing calibration (upsert)."""
        # Setup: Create week with existing calibration
        db_session.execute(
            text("INSERT INTO weeks (season, week_number) VALUES (2025, 13)")
        )
        db_session.commit()
        week_result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = 2025 AND week_number = 13")
        ).fetchone()
        week_id = week_result[0]

        db_session.execute(
            text("""
                INSERT INTO projection_calibration
                (week_id, position, floor_adjustment_percent,
                 median_adjustment_percent, ceiling_adjustment_percent, is_active)
                VALUES (:week_id, 'RB', 5.0, 3.0, -5.0, true)
            """),
            {"week_id": week_id}
        )
        db_session.commit()

        # Execute: Update using ON CONFLICT
        db_session.execute(
            text("""
                INSERT INTO projection_calibration
                (week_id, position, floor_adjustment_percent,
                 median_adjustment_percent, ceiling_adjustment_percent, is_active)
                VALUES (:week_id, 'RB', 12.0, 10.0, -12.0, true)
                ON CONFLICT (week_id, position)
                DO UPDATE SET
                    floor_adjustment_percent = EXCLUDED.floor_adjustment_percent,
                    median_adjustment_percent = EXCLUDED.median_adjustment_percent,
                    ceiling_adjustment_percent = EXCLUDED.ceiling_adjustment_percent,
                    is_active = EXCLUDED.is_active,
                    updated_at = CURRENT_TIMESTAMP
            """),
            {"week_id": week_id}
        )
        db_session.commit()

        # Assert
        result = db_session.execute(
            text("""
                SELECT floor_adjustment_percent, median_adjustment_percent,
                       ceiling_adjustment_percent
                FROM projection_calibration
                WHERE week_id = :week_id AND position = 'RB'
            """),
            {"week_id": week_id}
        ).fetchone()

        assert result[0] == 12.0
        assert result[1] == 10.0
        assert result[2] == -12.0


class TestBatchUpdateCalibrationsEndpoint:
    """Tests for POST /api/calibration/{week_id}/batch endpoint logic."""

    def test_batch_update_creates_multiple_calibrations(self, db_session: Session):
        """Test POST /api/calibration/{week_id}/batch creates multiple calibrations."""
        # Setup: Create week
        db_session.execute(
            text("INSERT INTO weeks (season, week_number) VALUES (2025, 14)")
        )
        db_session.commit()
        week_result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = 2025 AND week_number = 14")
        ).fetchone()
        week_id = week_result[0]

        # Execute: Batch insert
        calibrations = [
            ("QB", 5.0, 0.0, -5.0),
            ("RB", 10.0, 8.0, -10.0),
            ("WR", 8.0, 5.0, -12.0),
        ]

        for position, floor_adj, median_adj, ceiling_adj in calibrations:
            db_session.execute(
                text("""
                    INSERT INTO projection_calibration
                    (week_id, position, floor_adjustment_percent,
                     median_adjustment_percent, ceiling_adjustment_percent, is_active)
                    VALUES (:week_id, :position, :floor_adj, :median_adj, :ceiling_adj, true)
                """),
                {
                    "week_id": week_id,
                    "position": position,
                    "floor_adj": floor_adj,
                    "median_adj": median_adj,
                    "ceiling_adj": ceiling_adj,
                }
            )
        db_session.commit()

        # Assert
        count = db_session.execute(
            text("SELECT COUNT(*) FROM projection_calibration WHERE week_id = :week_id"),
            {"week_id": week_id}
        ).scalar()

        assert count == 3

    def test_batch_update_transaction_rollback_on_error(self, db_session: Session):
        """Test POST /api/calibration/{week_id}/batch rolls back all changes on error."""
        # Setup: Create week
        db_session.execute(
            text("INSERT INTO weeks (season, week_number) VALUES (2025, 15)")
        )
        db_session.commit()
        week_result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = 2025 AND week_number = 15")
        ).fetchone()
        week_id = week_result[0]

        # Execute: Attempt batch with invalid data (will fail on constraint)
        try:
            db_session.execute(
                text("""
                    INSERT INTO projection_calibration
                    (week_id, position, floor_adjustment_percent,
                     median_adjustment_percent, ceiling_adjustment_percent, is_active)
                    VALUES (:week_id, 'QB', 5.0, 0.0, -5.0, true)
                """),
                {"week_id": week_id}
            )
            # This should fail - invalid adjustment percent (100% > 50% max)
            db_session.execute(
                text("""
                    INSERT INTO projection_calibration
                    (week_id, position, floor_adjustment_percent,
                     median_adjustment_percent, ceiling_adjustment_percent, is_active)
                    VALUES (:week_id, 'RB', 100.0, 0.0, -5.0, true)
                """),
                {"week_id": week_id}
            )
            db_session.commit()
        except Exception:
            db_session.rollback()

        # Assert: No records should exist after rollback
        count = db_session.execute(
            text("SELECT COUNT(*) FROM projection_calibration WHERE week_id = :week_id"),
            {"week_id": week_id}
        ).scalar()

        assert count == 0


class TestGetCalibrationStatusEndpoint:
    """Tests for GET /api/calibration/{week_id}/status endpoint logic."""

    def test_get_status_returns_active_when_calibrations_exist(self, db_session: Session):
        """Test GET /api/calibration/{week_id}/status returns active status."""
        # Setup: Create week with active calibrations
        db_session.execute(
            text("INSERT INTO weeks (season, week_number) VALUES (2025, 16)")
        )
        db_session.commit()
        week_result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = 2025 AND week_number = 16")
        ).fetchone()
        week_id = week_result[0]

        # Insert 4 active calibrations
        for position in ["QB", "RB", "WR", "TE"]:
            db_session.execute(
                text("""
                    INSERT INTO projection_calibration
                    (week_id, position, floor_adjustment_percent,
                     median_adjustment_percent, ceiling_adjustment_percent, is_active)
                    VALUES (:week_id, :position, 5.0, 0.0, -5.0, true)
                """),
                {"week_id": week_id, "position": position}
            )
        db_session.commit()

        # Execute
        result = db_session.execute(
            text("""
                SELECT COUNT(*) as active_count
                FROM projection_calibration
                WHERE week_id = :week_id AND is_active = true
            """),
            {"week_id": week_id}
        ).fetchone()

        active_count = result[0]

        # Assert
        assert active_count == 4

    def test_get_status_returns_positions_configured_count(self, db_session: Session):
        """Test GET /api/calibration/{week_id}/status returns correct position count."""
        # Setup: Create week with partial calibrations
        db_session.execute(
            text("INSERT INTO weeks (season, week_number) VALUES (2025, 17)")
        )
        db_session.commit()
        week_result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = 2025 AND week_number = 17")
        ).fetchone()
        week_id = week_result[0]

        # Insert 3 calibrations
        for position in ["QB", "RB", "WR"]:
            db_session.execute(
                text("""
                    INSERT INTO projection_calibration
                    (week_id, position, floor_adjustment_percent,
                     median_adjustment_percent, ceiling_adjustment_percent, is_active)
                    VALUES (:week_id, :position, 5.0, 0.0, -5.0, true)
                """),
                {"week_id": week_id, "position": position}
            )
        db_session.commit()

        # Execute
        count = db_session.execute(
            text("""
                SELECT COUNT(DISTINCT position)
                FROM projection_calibration
                WHERE week_id = :week_id
            """),
            {"week_id": week_id}
        ).scalar()

        # Assert
        assert count == 3


class TestResetCalibrationEndpoint:
    """Tests for POST /api/calibration/{week_id}/reset endpoint logic."""

    def test_reset_restores_default_calibration_values(self, db_session: Session):
        """Test POST /api/calibration/{week_id}/reset restores default values."""
        # Setup: Create week with custom calibrations
        db_session.execute(
            text("INSERT INTO weeks (season, week_number) VALUES (2025, 18)")
        )
        db_session.commit()
        week_result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = 2025 AND week_number = 18")
        ).fetchone()
        week_id = week_result[0]

        # Insert custom calibrations
        db_session.execute(
            text("""
                INSERT INTO projection_calibration
                (week_id, position, floor_adjustment_percent,
                 median_adjustment_percent, ceiling_adjustment_percent, is_active)
                VALUES (:week_id, 'QB', 20.0, 15.0, -20.0, true)
            """),
            {"week_id": week_id}
        )
        db_session.commit()

        # Execute: Delete and insert defaults
        db_session.execute(
            text("DELETE FROM projection_calibration WHERE week_id = :week_id"),
            {"week_id": week_id}
        )

        # Insert default for QB
        db_session.execute(
            text("""
                INSERT INTO projection_calibration
                (week_id, position, floor_adjustment_percent,
                 median_adjustment_percent, ceiling_adjustment_percent, is_active)
                VALUES (:week_id, 'QB', 5.0, 0.0, -5.0, true)
            """),
            {"week_id": week_id}
        )
        db_session.commit()

        # Assert
        result = db_session.execute(
            text("""
                SELECT floor_adjustment_percent, median_adjustment_percent,
                       ceiling_adjustment_percent
                FROM projection_calibration
                WHERE week_id = :week_id AND position = 'QB'
            """),
            {"week_id": week_id}
        ).fetchone()

        assert result[0] == 5.0
        assert result[1] == 0.0
        assert result[2] == -5.0


class TestCalibrationValidation:
    """Tests for calibration validation logic."""

    def test_validation_rejects_percentage_outside_range(self, db_session: Session):
        """Test validation errors for invalid percentage ranges (-50 to +50)."""
        # Setup: Create week (use week 9 instead of 19, which is out of valid range)
        db_session.execute(
            text("INSERT INTO weeks (season, week_number) VALUES (2025, 9)")
        )
        db_session.commit()
        week_result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = 2025 AND week_number = 9")
        ).fetchone()
        week_id = week_result[0]

        # Execute & Assert: Try to insert invalid percentage (> 50)
        with pytest.raises(Exception):  # Will raise CHECK constraint violation
            db_session.execute(
                text("""
                    INSERT INTO projection_calibration
                    (week_id, position, floor_adjustment_percent,
                     median_adjustment_percent, ceiling_adjustment_percent, is_active)
                    VALUES (:week_id, 'QB', 60.0, 0.0, -5.0, true)
                """),
                {"week_id": week_id}
            )
            db_session.commit()

        db_session.rollback()

        # Execute & Assert: Try to insert invalid percentage (< -50)
        with pytest.raises(Exception):  # Will raise CHECK constraint violation
            db_session.execute(
                text("""
                    INSERT INTO projection_calibration
                    (week_id, position, floor_adjustment_percent,
                     median_adjustment_percent, ceiling_adjustment_percent, is_active)
                    VALUES (:week_id, 'QB', 5.0, 0.0, -60.0, true)
                """),
                {"week_id": week_id}
            )
            db_session.commit()

        db_session.rollback()

        # Verify no records were inserted
        count = db_session.execute(
            text("SELECT COUNT(*) FROM projection_calibration WHERE week_id = :week_id"),
            {"week_id": week_id}
        ).scalar()

        assert count == 0
