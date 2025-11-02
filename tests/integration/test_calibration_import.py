"""
Integration tests for calibration application during data import.

Tests cover:
- Import with active calibration applies correctly
- Import with inactive calibration skips application
- Import with partial calibration (some positions missing)
- Import with NULL projection values
- Original values preserved alongside calibrated
- Calibration_applied flag set correctly
"""

import pytest
from sqlalchemy import text
from backend.services.data_importer import DataImporter
from backend.services.calibration_service import CalibrationService


@pytest.fixture
def test_week(db_session):
    """Create or retrieve a test week for calibration tests."""
    # Get the first week from the seeded NFL schedule
    result = db_session.execute(
        text("""
            SELECT w.id FROM weeks w
            WHERE w.season = 2025 AND w.week_number = 1
            LIMIT 1
        """)
    ).fetchone()

    if result:
        return result[0]

    # If no week found, create one
    db_session.execute(
        text("""
            INSERT INTO weeks (season, week_number, status)
            VALUES (2025, 1, 'active')
        """)
    )
    db_session.commit()

    result = db_session.execute(
        text("SELECT id FROM weeks WHERE season = 2025 AND week_number = 1")
    ).fetchone()

    return result[0]


class TestImportCalibration:
    """Test calibration integration in import pipeline."""

    def test_import_with_active_calibration_applies_correctly(self, db_session, test_week):
        """Test import with active calibration applies correctly to all players."""
        # Arrange: Create active calibration for QB and RB
        db_session.execute(
            text("""
                INSERT INTO projection_calibration
                (week_id, position, floor_adjustment_percent,
                 median_adjustment_percent, ceiling_adjustment_percent, is_active)
                VALUES
                (:week_id, 'QB', 5.0, 0.0, -5.0, true),
                (:week_id, 'RB', 10.0, 8.0, -10.0, true)
            """),
            {"week_id": test_week}
        )
        db_session.commit()

        # Create test players
        players = [
            {
                "name": "Patrick Mahomes",
                "team": "KC",
                "position": "QB",
                "salary": 8000,
                "floor": 10.0,
                "projection": 25.0,
                "ceiling": 40.0,
                "ownership": 0.15,
                "player_key": "patrick_mahomes_kc_qb",
                "projection_source": "LineStar"
            },
            {
                "name": "Christian McCaffrey",
                "team": "SF",
                "position": "RB",
                "salary": 9000,
                "floor": 8.0,
                "projection": 20.0,
                "ceiling": 35.0,
                "ownership": 0.25,
                "player_key": "christian_mccaffrey_sf_rb",
                "projection_source": "LineStar"
            }
        ]

        # Act: Apply calibration
        calibration_service = CalibrationService(db_session)
        calibrated_players = calibration_service.apply_calibration(
            players, test_week, db_session
        )

        # Assert: QB calibration applied
        qb = calibrated_players[0]
        assert qb["projection_floor_original"] == 10.0
        assert qb["projection_floor_calibrated"] == 10.5  # 10.0 * 1.05
        assert qb["projection_median_original"] == 25.0
        assert qb["projection_median_calibrated"] == 25.0  # 25.0 * 1.00
        assert qb["projection_ceiling_original"] == 40.0
        assert qb["projection_ceiling_calibrated"] == 38.0  # 40.0 * 0.95
        assert qb["calibration_applied"] is True

        # Assert: RB calibration applied
        rb = calibrated_players[1]
        assert rb["projection_floor_original"] == 8.0
        assert rb["projection_floor_calibrated"] == 8.8  # 8.0 * 1.10
        assert rb["projection_median_original"] == 20.0
        assert rb["projection_median_calibrated"] == 21.6  # 20.0 * 1.08
        assert rb["projection_ceiling_original"] == 35.0
        assert rb["projection_ceiling_calibrated"] == 31.5  # 35.0 * 0.90
        assert rb["calibration_applied"] is True

    def test_import_with_inactive_calibration_skips_application(
        self, db_session, test_week
    ):
        """Test import with inactive calibration skips calibration application."""
        # Arrange: Create inactive calibration
        db_session.execute(
            text("""
                INSERT INTO projection_calibration
                (week_id, position, floor_adjustment_percent,
                 median_adjustment_percent, ceiling_adjustment_percent, is_active)
                VALUES (:week_id, 'QB', 5.0, 0.0, -5.0, false)
            """),
            {"week_id": test_week}
        )
        db_session.commit()

        players = [
            {
                "name": "Patrick Mahomes",
                "team": "KC",
                "position": "QB",
                "salary": 8000,
                "floor": 10.0,
                "projection": 25.0,
                "ceiling": 40.0,
                "ownership": 0.15,
                "player_key": "patrick_mahomes_kc_qb",
                "projection_source": "LineStar"
            }
        ]

        # Act: Apply calibration (should skip due to inactive)
        calibration_service = CalibrationService(db_session)
        calibrated_players = calibration_service.apply_calibration(
            players, test_week, db_session
        )

        # Assert: Values copied, not calibrated
        qb = calibrated_players[0]
        assert qb["projection_floor_original"] == 10.0
        assert qb["projection_floor_calibrated"] == 10.0  # Same as original
        assert qb["projection_median_original"] == 25.0
        assert qb["projection_median_calibrated"] == 25.0  # Same as original
        assert qb["projection_ceiling_original"] == 40.0
        assert qb["projection_ceiling_calibrated"] == 40.0  # Same as original
        assert qb["calibration_applied"] is False

    def test_import_with_partial_calibration(self, db_session, test_week):
        """Test import with partial calibration (some positions missing)."""
        # Arrange: Create calibration for QB only, not WR
        db_session.execute(
            text("""
                INSERT INTO projection_calibration
                (week_id, position, floor_adjustment_percent,
                 median_adjustment_percent, ceiling_adjustment_percent, is_active)
                VALUES (:week_id, 'QB', 5.0, 0.0, -5.0, true)
            """),
            {"week_id": test_week}
        )
        db_session.commit()

        players = [
            {
                "name": "Patrick Mahomes",
                "team": "KC",
                "position": "QB",
                "salary": 8000,
                "floor": 10.0,
                "projection": 25.0,
                "ceiling": 40.0,
                "ownership": 0.15,
                "player_key": "patrick_mahomes_kc_qb",
                "projection_source": "LineStar"
            },
            {
                "name": "Tyreek Hill",
                "team": "MIA",
                "position": "WR",
                "salary": 8500,
                "floor": 6.0,
                "projection": 18.0,
                "ceiling": 32.0,
                "ownership": 0.20,
                "player_key": "tyreek_hill_mia_wr",
                "projection_source": "LineStar"
            }
        ]

        # Act: Apply calibration
        calibration_service = CalibrationService(db_session)
        calibrated_players = calibration_service.apply_calibration(
            players, test_week, db_session
        )

        # Assert: QB calibrated
        qb = calibrated_players[0]
        assert qb["calibration_applied"] is True
        assert qb["projection_floor_calibrated"] == 10.5

        # Assert: WR not calibrated (values copied)
        wr = calibrated_players[1]
        assert wr["calibration_applied"] is False
        assert wr["projection_floor_calibrated"] == 6.0  # Same as original
        assert wr["projection_median_calibrated"] == 18.0  # Same as original
        assert wr["projection_ceiling_calibrated"] == 32.0  # Same as original

    def test_import_with_null_projection_values(self, db_session, test_week):
        """Test import with NULL projection values."""
        # Arrange: Create calibration
        db_session.execute(
            text("""
                INSERT INTO projection_calibration
                (week_id, position, floor_adjustment_percent,
                 median_adjustment_percent, ceiling_adjustment_percent, is_active)
                VALUES (:week_id, 'QB', 5.0, 0.0, -5.0, true)
            """),
            {"week_id": test_week}
        )
        db_session.commit()

        players = [
            {
                "name": "Patrick Mahomes",
                "team": "KC",
                "position": "QB",
                "salary": 8000,
                "floor": None,  # NULL floor
                "projection": 25.0,
                "ceiling": None,  # NULL ceiling
                "ownership": 0.15,
                "player_key": "patrick_mahomes_kc_qb",
                "projection_source": "LineStar"
            }
        ]

        # Act: Apply calibration
        calibration_service = CalibrationService(db_session)
        calibrated_players = calibration_service.apply_calibration(
            players, test_week, db_session
        )

        # Assert: NULL values remain NULL
        qb = calibrated_players[0]
        assert qb["projection_floor_original"] is None
        assert qb["projection_floor_calibrated"] is None
        assert qb["projection_median_original"] == 25.0
        assert qb["projection_median_calibrated"] == 25.0  # 25.0 * 1.00
        assert qb["projection_ceiling_original"] is None
        assert qb["projection_ceiling_calibrated"] is None
        # Still marked as calibration_applied = True because position has calibration
        assert qb["calibration_applied"] is True

    def test_original_values_preserved_alongside_calibrated(
        self, db_session, test_week
    ):
        """Test original values preserved alongside calibrated values."""
        # Arrange: Create calibration
        db_session.execute(
            text("""
                INSERT INTO projection_calibration
                (week_id, position, floor_adjustment_percent,
                 median_adjustment_percent, ceiling_adjustment_percent, is_active)
                VALUES (:week_id, 'RB', 10.0, 8.0, -10.0, true)
            """),
            {"week_id": test_week}
        )
        db_session.commit()

        players = [
            {
                "name": "Christian McCaffrey",
                "team": "SF",
                "position": "RB",
                "salary": 9000,
                "floor": 8.0,
                "projection": 20.0,
                "ceiling": 35.0,
                "ownership": 0.25,
                "player_key": "christian_mccaffrey_sf_rb",
                "projection_source": "LineStar"
            }
        ]

        # Act: Apply calibration
        calibration_service = CalibrationService(db_session)
        calibrated_players = calibration_service.apply_calibration(
            players, test_week, db_session
        )

        # Assert: Original values preserved
        rb = calibrated_players[0]
        assert rb["projection_floor_original"] == 8.0
        assert rb["projection_median_original"] == 20.0
        assert rb["projection_ceiling_original"] == 35.0

        # Assert: Calibrated values different from original
        assert rb["projection_floor_calibrated"] == 8.8
        assert rb["projection_median_calibrated"] == 21.6
        assert rb["projection_ceiling_calibrated"] == 31.5

        # Assert: Both sets of values present
        assert "projection_floor_original" in rb
        assert "projection_floor_calibrated" in rb
        assert "projection_median_original" in rb
        assert "projection_median_calibrated" in rb
        assert "projection_ceiling_original" in rb
        assert "projection_ceiling_calibrated" in rb

    def test_calibration_applied_flag_set_correctly(self, db_session, test_week):
        """Test calibration_applied flag set correctly for calibrated and non-calibrated players."""
        # Arrange: Create calibration for QB only
        db_session.execute(
            text("""
                INSERT INTO projection_calibration
                (week_id, position, floor_adjustment_percent,
                 median_adjustment_percent, ceiling_adjustment_percent, is_active)
                VALUES (:week_id, 'QB', 5.0, 0.0, -5.0, true)
            """),
            {"week_id": test_week}
        )
        db_session.commit()

        players = [
            {
                "name": "Patrick Mahomes",
                "team": "KC",
                "position": "QB",
                "salary": 8000,
                "floor": 10.0,
                "projection": 25.0,
                "ceiling": 40.0,
                "ownership": 0.15,
                "player_key": "patrick_mahomes_kc_qb",
                "projection_source": "LineStar"
            },
            {
                "name": "Tyreek Hill",
                "team": "MIA",
                "position": "WR",
                "salary": 8500,
                "floor": 6.0,
                "projection": 18.0,
                "ceiling": 32.0,
                "ownership": 0.20,
                "player_key": "tyreek_hill_mia_wr",
                "projection_source": "LineStar"
            },
            {
                "name": "Travis Kelce",
                "team": "KC",
                "position": "TE",
                "salary": 7000,
                "floor": 5.0,
                "projection": 15.0,
                "ceiling": 28.0,
                "ownership": 0.18,
                "player_key": "travis_kelce_kc_te",
                "projection_source": "LineStar"
            }
        ]

        # Act: Apply calibration
        calibration_service = CalibrationService(db_session)
        calibrated_players = calibration_service.apply_calibration(
            players, test_week, db_session
        )

        # Assert: QB has calibration_applied = True
        assert calibrated_players[0]["calibration_applied"] is True

        # Assert: WR has calibration_applied = False (no calibration)
        assert calibrated_players[1]["calibration_applied"] is False

        # Assert: TE has calibration_applied = False (no calibration)
        assert calibrated_players[2]["calibration_applied"] is False

    def test_end_to_end_import_with_calibration_integration(
        self, db_session, test_week
    ):
        """Test end-to-end import flow with calibration integration."""
        # Arrange: Create active calibration
        db_session.execute(
            text("""
                INSERT INTO projection_calibration
                (week_id, position, floor_adjustment_percent,
                 median_adjustment_percent, ceiling_adjustment_percent, is_active)
                VALUES
                (:week_id, 'QB', 5.0, 0.0, -5.0, true),
                (:week_id, 'RB', 10.0, 8.0, -10.0, true),
                (:week_id, 'WR', 8.0, 5.0, -12.0, true)
            """),
            {"week_id": test_week}
        )
        db_session.commit()

        # Create test players
        players = [
            {
                "name": "Patrick Mahomes",
                "team": "KC",
                "position": "QB",
                "salary": 8000,
                "floor": 10.0,
                "projection": 25.0,
                "ceiling": 40.0,
                "ownership": 0.15,
                "player_key": "patrick_mahomes_kc_qb",
                "projection_source": "LineStar"
            },
            {
                "name": "Christian McCaffrey",
                "team": "SF",
                "position": "RB",
                "salary": 9000,
                "floor": 8.0,
                "projection": 20.0,
                "ceiling": 35.0,
                "ownership": 0.25,
                "player_key": "christian_mccaffrey_sf_rb",
                "projection_source": "LineStar"
            },
            {
                "name": "Tyreek Hill",
                "team": "MIA",
                "position": "WR",
                "salary": 8500,
                "floor": 6.0,
                "projection": 18.0,
                "ceiling": 32.0,
                "ownership": 0.20,
                "player_key": "tyreek_hill_mia_wr",
                "projection_source": "LineStar"
            }
        ]

        # Act: Apply calibration and insert
        calibration_service = CalibrationService(db_session)
        calibrated_players = calibration_service.apply_calibration(
            players, test_week, db_session
        )

        # Insert players into database
        for player in calibrated_players:
            db_session.execute(
                text("""
                    INSERT INTO player_pools
                    (week_id, player_key, name, team, position, salary, projection,
                     ownership, ceiling, floor, source, projection_source,
                     projection_floor_original, projection_floor_calibrated,
                     projection_median_original, projection_median_calibrated,
                     projection_ceiling_original, projection_ceiling_calibrated,
                     calibration_applied)
                    VALUES (:week_id, :player_key, :name, :team, :position, :salary,
                            :projection, :ownership, :ceiling, :floor, :source,
                            :projection_source, :projection_floor_original,
                            :projection_floor_calibrated, :projection_median_original,
                            :projection_median_calibrated, :projection_ceiling_original,
                            :projection_ceiling_calibrated, :calibration_applied)
                """),
                {
                    "week_id": test_week,
                    "player_key": player["player_key"],
                    "name": player["name"],
                    "team": player["team"],
                    "position": player["position"],
                    "salary": player["salary"],
                    "projection": player.get("projection"),
                    "ownership": player.get("ownership"),
                    "ceiling": player.get("ceiling"),
                    "floor": player.get("floor"),
                    "source": "LineStar",
                    "projection_source": player.get("projection_source"),
                    "projection_floor_original": player.get("projection_floor_original"),
                    "projection_floor_calibrated": player.get("projection_floor_calibrated"),
                    "projection_median_original": player.get("projection_median_original"),
                    "projection_median_calibrated": player.get("projection_median_calibrated"),
                    "projection_ceiling_original": player.get("projection_ceiling_original"),
                    "projection_ceiling_calibrated": player.get("projection_ceiling_calibrated"),
                    "calibration_applied": player.get("calibration_applied"),
                }
            )
        db_session.commit()

        # Assert: Query database to verify calibrated values persisted
        result = db_session.execute(
            text("""
                SELECT position, projection_floor_original, projection_floor_calibrated,
                       projection_median_original, projection_median_calibrated,
                       projection_ceiling_original, projection_ceiling_calibrated,
                       calibration_applied
                FROM player_pools
                WHERE week_id = :week_id
                ORDER BY position
            """),
            {"week_id": test_week}
        ).fetchall()

        # Verify 3 players inserted
        assert len(result) == 3

        # Verify QB (position order: QB, RB, WR)
        qb = result[0]
        assert qb[0] == "QB"
        assert qb[1] == 10.0  # floor_original
        assert qb[2] == 10.5  # floor_calibrated
        assert qb[3] == 25.0  # median_original
        assert qb[4] == 25.0  # median_calibrated
        assert qb[5] == 40.0  # ceiling_original
        assert qb[6] == 38.0  # ceiling_calibrated
        assert qb[7] == 1 or qb[7] is True  # calibration_applied (SQLite stores as 1)

        # Verify RB
        rb = result[1]
        assert rb[0] == "RB"
        assert rb[1] == 8.0  # floor_original
        assert rb[2] == 8.8  # floor_calibrated
        assert rb[7] == 1 or rb[7] is True  # calibration_applied

        # Verify WR
        wr = result[2]
        assert wr[0] == "WR"
        assert wr[1] == 6.0  # floor_original
        assert wr[2] == 6.48  # floor_calibrated (6.0 * 1.08)
        assert wr[7] == 1 or wr[7] is True  # calibration_applied
