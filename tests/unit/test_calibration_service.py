"""
Unit tests for CalibrationService.

Tests calibration calculation logic, NULL handling, and batch processing.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.services.calibration_service import CalibrationService


class TestCalibrationService:
    """Test suite for CalibrationService."""

    def test_calibration_calculation_formula_positive_adjustment(self, db_session: Session):
        """Test calibration calculation formula with positive adjustment."""
        service = CalibrationService(db_session)

        # Test formula: calibrated = original * (1 + adjustment% / 100)
        # Example: 12.0 with +5% = 12.0 * 1.05 = 12.6
        result = service.calculate_calibrated_value(12.0, 5.0)
        assert result == 12.6

        # Example: 10.0 with +10% = 10.0 * 1.10 = 11.0
        result = service.calculate_calibrated_value(10.0, 10.0)
        assert result == 11.0

    def test_calibration_calculation_formula_negative_adjustment(self, db_session: Session):
        """Test calibration calculation formula with negative adjustment."""
        service = CalibrationService(db_session)

        # Test formula with negative adjustments
        # Example: 25.0 with -10% = 25.0 * 0.90 = 22.5
        result = service.calculate_calibrated_value(25.0, -10.0)
        assert result == 22.5

        # Example: 20.0 with -5% = 20.0 * 0.95 = 19.0
        result = service.calculate_calibrated_value(20.0, -5.0)
        assert result == 19.0

    def test_calibration_calculation_formula_zero_adjustment(self, db_session: Session):
        """Test calibration calculation formula with zero adjustment."""
        service = CalibrationService(db_session)

        # Test formula with 0% adjustment (no change)
        # Example: 15.0 with 0% = 15.0 * 1.0 = 15.0
        result = service.calculate_calibrated_value(15.0, 0.0)
        assert result == 15.0

    def test_handling_null_original_values(self, db_session: Session):
        """Test handling of NULL original values (should remain NULL)."""
        service = CalibrationService(db_session)

        # Insert calibration for week 1
        db_session.execute(
            text("""
                INSERT INTO projection_calibration
                (week_id, position, floor_adjustment_percent, median_adjustment_percent,
                 ceiling_adjustment_percent, is_active)
                VALUES (1, 'QB', 5.0, 0.0, -5.0, true)
            """)
        )
        db_session.commit()

        # Test with player data containing NULL values
        players = [
            {
                'position': 'QB',
                'floor': None,
                'projection': 12.0,
                'ceiling': None
            }
        ]

        result = service.apply_calibration(players, 1, db_session)

        # NULL original values should remain NULL in calibrated
        assert result[0]['projection_floor_original'] is None
        assert result[0]['projection_floor_calibrated'] is None
        assert result[0]['projection_ceiling_original'] is None
        assert result[0]['projection_ceiling_calibrated'] is None

        # Non-NULL values should be calibrated
        assert result[0]['projection_median_original'] == 12.0
        assert result[0]['projection_median_calibrated'] == 12.0  # 0% adjustment

    def test_handling_missing_calibration_factors_for_position(self, db_session: Session):
        """Test handling of missing calibration factors for position."""
        service = CalibrationService(db_session)

        # Insert calibration only for QB (not RB)
        db_session.execute(
            text("""
                INSERT INTO projection_calibration
                (week_id, position, floor_adjustment_percent, median_adjustment_percent,
                 ceiling_adjustment_percent, is_active)
                VALUES (1, 'QB', 5.0, 0.0, -5.0, true)
            """)
        )
        db_session.commit()

        # Test with RB player (no calibration exists)
        players = [
            {
                'position': 'RB',
                'floor': 8.0,
                'projection': 15.0,
                'ceiling': 22.0
            }
        ]

        result = service.apply_calibration(players, 1, db_session)

        # Should copy original to calibrated (no adjustment)
        assert result[0]['projection_floor_original'] == 8.0
        assert result[0]['projection_floor_calibrated'] == 8.0
        assert result[0]['projection_median_original'] == 15.0
        assert result[0]['projection_median_calibrated'] == 15.0
        assert result[0]['projection_ceiling_original'] == 22.0
        assert result[0]['projection_ceiling_calibrated'] == 22.0
        assert result[0]['calibration_applied'] is False

    def test_negative_projection_handling_set_to_zero(self, db_session: Session):
        """Test negative projection handling (set to 0 if result < 0)."""
        service = CalibrationService(db_session)

        # Test with large negative adjustment that produces negative result
        # Example: 5.0 with -150% would be 5.0 * -0.5 = -2.5, should become 0
        result = service.calculate_calibrated_value(5.0, -150.0)
        assert result == 0.0

        # Test edge case: exactly reaches zero
        # Example: 10.0 with -100% = 10.0 * 0.0 = 0
        result = service.calculate_calibrated_value(10.0, -100.0)
        assert result == 0.0

        # Test normal case that doesn't go negative
        # Example: 10.0 with -50% = 10.0 * 0.5 = 5.0
        result = service.calculate_calibrated_value(10.0, -50.0)
        assert result == 5.0

    def test_batch_calibration_application_to_player_list(self, db_session: Session):
        """Test batch calibration application to player list."""
        service = CalibrationService(db_session)

        # Insert calibration for multiple positions
        positions_calibration = [
            ('QB', 5.0, 0.0, -5.0),
            ('RB', 10.0, 8.0, -10.0),
            ('WR', 8.0, 5.0, -12.0),
        ]

        for position, floor_adj, median_adj, ceiling_adj in positions_calibration:
            db_session.execute(
                text("""
                    INSERT INTO projection_calibration
                    (week_id, position, floor_adjustment_percent, median_adjustment_percent,
                     ceiling_adjustment_percent, is_active)
                    VALUES (1, :position, :floor_adj, :median_adj, :ceiling_adj, true)
                """),
                {
                    "position": position,
                    "floor_adj": floor_adj,
                    "median_adj": median_adj,
                    "ceiling_adj": ceiling_adj
                }
            )
        db_session.commit()

        # Test with multiple players
        players = [
            {
                'position': 'QB',
                'floor': 10.0,
                'projection': 20.0,
                'ceiling': 30.0
            },
            {
                'position': 'RB',
                'floor': 8.0,
                'projection': 15.0,
                'ceiling': 25.0
            },
            {
                'position': 'WR',
                'floor': 5.0,
                'projection': 12.0,
                'ceiling': 22.0
            },
        ]

        result = service.apply_calibration(players, 1, db_session)

        # Verify QB calibration (floor +5%, median 0%, ceiling -5%)
        assert result[0]['projection_floor_calibrated'] == 10.5  # 10.0 * 1.05
        assert result[0]['projection_median_calibrated'] == 20.0  # 20.0 * 1.0
        assert result[0]['projection_ceiling_calibrated'] == 28.5  # 30.0 * 0.95
        assert result[0]['calibration_applied'] is True

        # Verify RB calibration (floor +10%, median +8%, ceiling -10%)
        assert result[1]['projection_floor_calibrated'] == 8.8  # 8.0 * 1.10
        assert result[1]['projection_median_calibrated'] == 16.2  # 15.0 * 1.08
        assert result[1]['projection_ceiling_calibrated'] == 22.5  # 25.0 * 0.90
        assert result[1]['calibration_applied'] is True

        # Verify WR calibration (floor +8%, median +5%, ceiling -12%)
        assert result[2]['projection_floor_calibrated'] == 5.4  # 5.0 * 1.08
        assert result[2]['projection_median_calibrated'] == 12.6  # 12.0 * 1.05
        assert result[2]['projection_ceiling_calibrated'] == 19.36  # 22.0 * 0.88
        assert result[2]['calibration_applied'] is True

    def test_get_calibration_for_week_returns_mapping(self, db_session: Session):
        """Test get_calibration_for_week returns position -> tuple mapping."""
        service = CalibrationService(db_session)

        # Insert calibration for week 1
        db_session.execute(
            text("""
                INSERT INTO projection_calibration
                (week_id, position, floor_adjustment_percent, median_adjustment_percent,
                 ceiling_adjustment_percent, is_active)
                VALUES (1, 'QB', 5.0, 0.0, -5.0, true),
                       (1, 'RB', 10.0, 8.0, -10.0, true)
            """)
        )
        db_session.commit()

        # Get calibration mapping
        result = service.get_calibration_for_week(1, db_session)

        # Verify mapping structure: position -> (floor_adj, median_adj, ceiling_adj)
        assert 'QB' in result
        assert result['QB'] == (5.0, 0.0, -5.0)

        assert 'RB' in result
        assert result['RB'] == (10.0, 8.0, -10.0)

        # Positions without calibration should not be in mapping
        assert 'WR' not in result
        assert 'TE' not in result
