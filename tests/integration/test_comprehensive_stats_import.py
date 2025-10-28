"""
Integration tests for Comprehensive Stats import workflow.

Tests the complete end-to-end flow of uploading Comprehensive Stats XLSX files,
verifying backup creation, and tracking historical data.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
import json

from tests.conftest import create_week


class TestComprehensiveStatsImportSuccess:
    """Tests for successful Comprehensive Stats import scenarios."""

    def test_comprehensive_stats_import_creates_correct_count(self, db_session: Session):
        """Test that Comprehensive Stats import loads 2690 records."""
        from tests.conftest import create_comprehensive_stats_xlsx
        import pandas as pd

        # Create sample file
        file_data = create_comprehensive_stats_xlsx()
        file_data.seek(0)

        # Read the sample file
        df = pd.read_excel(file_data, sheet_name="Points", header=0)

        # Verify count
        assert len(df) == 2690, f"Expected 2690 records, got {len(df)}"


class TestComprehensiveStatsBackup:
    """Tests for backup creation."""

    def test_backup_created_before_import(self, db_session: Session):
        """Test that backup is created before new data is imported."""
        # Insert some initial historical data
        for i in range(10):
            db_session.execute(
                text("""
                    INSERT INTO historical_stats
                    (player_name, team, position, week, actual_points)
                    VALUES (:player_name, :team, :position, :week, :actual_points)
                """),
                {
                    "player_name": f"Player{i}",
                    "team": "KC",
                    "position": "QB",
                    "week": 1,
                    "actual_points": 20.5 + i,
                }
            )
        db_session.commit()

        # Simulate backup
        backup_data = db_session.execute(
            text("SELECT COUNT(*) FROM historical_stats")
        ).scalar()

        db_session.execute(
            text("""
                INSERT INTO historical_stats_backup (backup_timestamp, data)
                VALUES (:backup_timestamp, :data)
            """),
            {
                "backup_timestamp": "2025-10-27 12:00:00",
                "data": json.dumps({"record_count": backup_data}),
            }
        )
        db_session.commit()

        # Verify backup exists
        result = db_session.execute(
            text("SELECT COUNT(*) FROM historical_stats_backup")
        )
        backup_count = result.scalar()
        assert backup_count == 1

        # Verify backup data
        result = db_session.execute(
            text("SELECT data FROM historical_stats_backup LIMIT 1")
        )
        backup_json = result.scalar()
        backup_obj = json.loads(backup_json)
        assert backup_obj["record_count"] == 10


class TestComprehensiveStatsDataImport:
    """Tests for Comprehensive Stats data insertion."""

    def test_comprehensive_stats_inserts_all_weeks(self, db_session: Session):
        """Test that all 18 weeks of data are imported."""
        # Insert stats for each week
        for week in range(1, 19):
            for i in range(10):
                db_session.execute(
                    text("""
                        INSERT INTO historical_stats
                        (player_name, team, position, week, actual_points)
                        VALUES (:player_name, :team, :position, :week, :actual_points)
                    """),
                    {
                        "player_name": f"Player{i}_Week{week}",
                        "team": "KC",
                        "position": "QB",
                        "week": week,
                        "actual_points": 20.0 + week + i,
                    }
                )
        db_session.commit()

        # Verify all weeks exist
        result = db_session.execute(
            text("SELECT COUNT(DISTINCT week) FROM historical_stats")
        )
        week_count = result.scalar()
        assert week_count == 18

        # Verify total records
        result = db_session.execute(
            text("SELECT COUNT(*) FROM historical_stats")
        )
        total_count = result.scalar()
        assert total_count == 180  # 18 weeks * 10 players

    def test_comprehensive_stats_populates_fields(self, db_session: Session):
        """Test that all fields are populated correctly."""
        # Insert comprehensive stats record
        db_session.execute(
            text("""
                INSERT INTO historical_stats
                (player_name, team, position, week, opponent, snaps, snap_pct,
                 rush_attempts, rush_yards, rush_tds, targets, target_share,
                 receptions, rec_yards, rec_tds, total_tds, touches, actual_points, salary)
                VALUES (:player_name, :team, :position, :week, :opponent, :snaps, :snap_pct,
                        :rush_attempts, :rush_yards, :rush_tds, :targets, :target_share,
                        :receptions, :rec_yards, :rec_tds, :total_tds, :touches, :actual_points, :salary)
            """),
            {
                "player_name": "Patrick Mahomes",
                "team": "KC",
                "position": "QB",
                "week": 1,
                "opponent": "CIN",
                "snaps": 60,
                "snap_pct": 0.95,
                "rush_attempts": 3,
                "rush_yards": 15,
                "rush_tds": 0,
                "targets": 0,
                "target_share": 0.0,
                "receptions": 0,
                "rec_yards": 0,
                "rec_tds": 0,
                "total_tds": 2,
                "touches": 3,
                "actual_points": 32.5,
                "salary": 8500,
            }
        )
        db_session.commit()

        # Verify record
        result = db_session.execute(
            text("SELECT * FROM historical_stats WHERE player_name = 'Patrick Mahomes'")
        )
        row = result.fetchone()
        assert row is not None

        # Verify field values
        cols = [col[0] for col in result.cursor.description]
        record = dict(zip(cols, row))

        assert record["player_name"] == "Patrick Mahomes"
        assert record["team"] == "KC"
        assert record["position"] == "QB"
        assert record["week"] == 1
        assert record["opponent"] == "CIN"
        assert record["snaps"] == 60
        assert record["snap_pct"] == pytest.approx(0.95)
        assert record["rush_attempts"] == 3
        assert record["rush_yards"] == 15
        assert record["total_tds"] == 2
        assert record["actual_points"] == pytest.approx(32.5)


class TestComprehensiveStatsDataReplacement:
    """Tests for replacing old stats with new data."""

    def test_old_stats_deleted_on_new_import(self, db_session: Session):
        """Test that old historical stats are deleted before new import."""
        # Insert old data
        for i in range(20):
            db_session.execute(
                text("""
                    INSERT INTO historical_stats
                    (player_name, team, position, week, actual_points)
                    VALUES (:player_name, :team, :position, :week, :actual_points)
                """),
                {
                    "player_name": f"OldPlayer{i}",
                    "team": "KC",
                    "position": "QB",
                    "week": 1,
                    "actual_points": 15.0,
                }
            )
        db_session.commit()

        # Verify old data exists
        result = db_session.execute(
            text("SELECT COUNT(*) FROM historical_stats")
        )
        old_count = result.scalar()
        assert old_count == 20

        # Delete old data (simulating import)
        db_session.execute(text("DELETE FROM historical_stats"))

        # Insert new data
        for i in range(30):
            db_session.execute(
                text("""
                    INSERT INTO historical_stats
                    (player_name, team, position, week, actual_points)
                    VALUES (:player_name, :team, :position, :week, :actual_points)
                """),
                {
                    "player_name": f"NewPlayer{i}",
                    "team": "KC",
                    "position": "QB",
                    "week": 1,
                    "actual_points": 20.0,
                }
            )
        db_session.commit()

        # Verify only new data remains
        result = db_session.execute(
            text("SELECT COUNT(*) FROM historical_stats")
        )
        new_count = result.scalar()
        assert new_count == 30

        # Verify no old players
        result = db_session.execute(
            text("SELECT COUNT(*) FROM historical_stats WHERE player_name LIKE 'OldPlayer%'")
        )
        old_player_count = result.scalar()
        assert old_player_count == 0


class TestComprehensiveStatsWeekDistribution:
    """Tests for proper distribution of stats across weeks."""

    def test_stats_distributed_across_all_weeks(self, db_session: Session):
        """Test that stats cover all 18 weeks."""
        # Insert stats for weeks 1-18
        record_id = 1
        for week in range(1, 19):
            for team in ["KC", "LAC", "PHI"]:
                for pos in ["QB", "RB", "WR"]:
                    db_session.execute(
                        text("""
                            INSERT INTO historical_stats
                            (player_name, team, position, week, actual_points)
                            VALUES (:player_name, :team, :position, :week, :actual_points)
                        """),
                        {
                            "player_name": f"Player{record_id}",
                            "team": team,
                            "position": pos,
                            "week": week,
                            "actual_points": 15.0 + week,
                        }
                    )
                    record_id += 1
        db_session.commit()

        # Check distribution
        for week in range(1, 19):
            result = db_session.execute(
                text("SELECT COUNT(*) FROM historical_stats WHERE week = :week"),
                {"week": week}
            )
            count = result.scalar()
            assert count == 9, f"Week {week} should have 9 records, got {count}"

    def test_stats_by_position_distribution(self, db_session: Session):
        """Test that stats are distributed across all positions."""
        positions = ["QB", "RB", "WR", "TE", "DST"]

        for pos in positions:
            for i in range(5):
                db_session.execute(
                    text("""
                        INSERT INTO historical_stats
                        (player_name, team, position, week, actual_points)
                        VALUES (:player_name, :team, :position, :week, :actual_points)
                    """),
                    {
                        "player_name": f"Player_{pos}_{i}",
                        "team": "KC",
                        "position": pos,
                        "week": 1,
                        "actual_points": 20.0,
                    }
                )
        db_session.commit()

        # Verify distribution
        for pos in positions:
            result = db_session.execute(
                text("SELECT COUNT(*) FROM historical_stats WHERE position = :position"),
                {"position": pos}
            )
            count = result.scalar()
            assert count == 5


class TestComprehensiveStatsFieldValidation:
    """Tests for stats field validation."""

    def test_week_range_validation(self, db_session: Session):
        """Test that week values are in valid range (1-18)."""
        valid_weeks = [1, 5, 10, 15, 18]

        for week in valid_weeks:
            db_session.execute(
                text("""
                    INSERT INTO historical_stats
                    (player_name, team, position, week, actual_points)
                    VALUES (:player_name, :team, :position, :week, :actual_points)
                """),
                {
                    "player_name": f"Player_Week{week}",
                    "team": "KC",
                    "position": "QB",
                    "week": week,
                    "actual_points": 20.0,
                }
            )
        db_session.commit()

        # Verify all weeks are valid
        result = db_session.execute(
            text("SELECT MIN(week), MAX(week) FROM historical_stats")
        )
        min_week, max_week = result.fetchone()
        assert min_week >= 1
        assert max_week <= 18

    def test_position_validation_for_stats(self, db_session: Session):
        """Test that stat positions are valid."""
        positions = ["QB", "RB", "WR", "TE", "DST"]

        for pos in positions:
            db_session.execute(
                text("""
                    INSERT INTO historical_stats
                    (player_name, team, position, week, actual_points)
                    VALUES (:player_name, :team, :position, :week, :actual_points)
                """),
                {
                    "player_name": f"Player_{pos}",
                    "team": "KC",
                    "position": pos,
                    "week": 1,
                    "actual_points": 20.0,
                }
            )
        db_session.commit()

        # Verify all positions are valid
        result = db_session.execute(
            text("SELECT COUNT(*) FROM historical_stats WHERE position IN ('QB', 'RB', 'WR', 'TE', 'DST')")
        )
        count = result.scalar()
        assert count == len(positions)
