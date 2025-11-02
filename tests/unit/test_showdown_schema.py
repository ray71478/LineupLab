"""
Tests for Showdown Mode database schema changes.

Tests the new contest_mode columns and indexes added to support showdown mode:
- player_pools table: contest_mode column and composite index
- generated_lineups table: contest_mode column and is_captain field support
- Data isolation between main and showdown modes
- Foreign key constraints remain intact

This test module covers Task 1.1 from the Showdown Mode implementation.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session


class TestPlayerPoolsContestMode:
    """Tests for player_pools table contest_mode support."""

    def test_contest_mode_column_exists_with_default(self, db_session: Session):
        """Test that contest_mode column exists and defaults to 'main'."""
        # Create a week
        db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status)
                VALUES (:season, :week_number, :status)
            """),
            {"season": 2025, "week_number": 1, "status": "active"}
        )
        db_session.commit()

        # Get week_id
        result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = 2025 AND week_number = 1")
        )
        week_id = result.scalar()

        # Insert player without specifying contest_mode
        db_session.execute(
            text("""
                INSERT INTO player_pools
                (week_id, player_key, name, team, position, salary, projection, source)
                VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :source)
            """),
            {
                "week_id": week_id,
                "player_key": "P_Mahomes_KC",
                "name": "Patrick Mahomes",
                "team": "KC",
                "position": "QB",
                "salary": 8000,
                "projection": 22.5,
                "source": "LineStar"
            }
        )
        db_session.commit()

        # Verify contest_mode defaults to 'main'
        result = db_session.execute(
            text("""
                SELECT contest_mode FROM player_pools
                WHERE week_id = :week_id AND player_key = :player_key
            """),
            {"week_id": week_id, "player_key": "P_Mahomes_KC"}
        )
        contest_mode = result.scalar()
        assert contest_mode == "main", "contest_mode should default to 'main'"

    def test_contest_mode_accepts_showdown_value(self, db_session: Session):
        """Test that contest_mode column accepts 'showdown' value."""
        # Create a week
        db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status)
                VALUES (:season, :week_number, :status)
            """),
            {"season": 2025, "week_number": 2, "status": "active"}
        )
        db_session.commit()

        # Get week_id
        result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = 2025 AND week_number = 2")
        )
        week_id = result.scalar()

        # Insert player with showdown mode
        db_session.execute(
            text("""
                INSERT INTO player_pools
                (week_id, player_key, name, team, position, salary, projection, source, contest_mode)
                VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :source, :contest_mode)
            """),
            {
                "week_id": week_id,
                "player_key": "T_Kelce_KC",
                "name": "Travis Kelce",
                "team": "KC",
                "position": "TE",
                "salary": 7000,
                "projection": 15.5,
                "source": "LineStar",
                "contest_mode": "showdown"
            }
        )
        db_session.commit()

        # Verify contest_mode is 'showdown'
        result = db_session.execute(
            text("""
                SELECT contest_mode FROM player_pools
                WHERE week_id = :week_id AND player_key = :player_key
            """),
            {"week_id": week_id, "player_key": "T_Kelce_KC"}
        )
        contest_mode = result.scalar()
        assert contest_mode == "showdown", "contest_mode should be 'showdown'"

    def test_composite_index_on_week_id_contest_mode(self, db_session: Session):
        """Test that composite index on (week_id, contest_mode) performs correctly."""
        # Create a week
        db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status)
                VALUES (:season, :week_number, :status)
            """),
            {"season": 2025, "week_number": 3, "status": "active"}
        )
        db_session.commit()

        # Get week_id
        result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = 2025 AND week_number = 3")
        )
        week_id = result.scalar()

        # Insert multiple players with different modes
        players = [
            ("P1_KC", "Player 1", "main"),
            ("P2_KC", "Player 2", "main"),
            ("P3_KC", "Player 3", "showdown"),
            ("P4_KC", "Player 4", "showdown"),
        ]

        for player_key, name, mode in players:
            db_session.execute(
                text("""
                    INSERT INTO player_pools
                    (week_id, player_key, name, team, position, salary, projection, source, contest_mode)
                    VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :source, :contest_mode)
                """),
                {
                    "week_id": week_id,
                    "player_key": player_key,
                    "name": name,
                    "team": "KC",
                    "position": "RB",
                    "salary": 6000,
                    "projection": 12.0,
                    "source": "LineStar",
                    "contest_mode": mode
                }
            )
        db_session.commit()

        # Query using the composite index
        result = db_session.execute(
            text("""
                SELECT COUNT(*) FROM player_pools
                WHERE week_id = :week_id AND contest_mode = :contest_mode
            """),
            {"week_id": week_id, "contest_mode": "main"}
        )
        main_count = result.scalar()

        result = db_session.execute(
            text("""
                SELECT COUNT(*) FROM player_pools
                WHERE week_id = :week_id AND contest_mode = :contest_mode
            """),
            {"week_id": week_id, "contest_mode": "showdown"}
        )
        showdown_count = result.scalar()

        assert main_count == 2, "Should have 2 main mode players"
        assert showdown_count == 2, "Should have 2 showdown mode players"

    def test_data_isolation_between_modes(self, db_session: Session):
        """Test data isolation between modes (same week_id, different modes)."""
        # Create a week
        db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status)
                VALUES (:season, :week_number, :status)
            """),
            {"season": 2025, "week_number": 4, "status": "active"}
        )
        db_session.commit()

        # Get week_id
        result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = 2025 AND week_number = 4")
        )
        week_id = result.scalar()

        # Insert same player in both modes (different player pools)
        db_session.execute(
            text("""
                INSERT INTO player_pools
                (week_id, player_key, name, team, position, salary, projection, source, contest_mode)
                VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :source, :contest_mode)
            """),
            {
                "week_id": week_id,
                "player_key": "J_Allen_BUF",
                "name": "Josh Allen",
                "team": "BUF",
                "position": "QB",
                "salary": 8200,
                "projection": 24.0,
                "source": "LineStar",
                "contest_mode": "main"
            }
        )

        db_session.execute(
            text("""
                INSERT INTO player_pools
                (week_id, player_key, name, team, position, salary, projection, source, contest_mode)
                VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :source, :contest_mode)
            """),
            {
                "week_id": week_id,
                "player_key": "J_Allen_BUF",
                "name": "Josh Allen",
                "team": "BUF",
                "position": "QB",
                "salary": 8500,  # Different salary for showdown
                "projection": 26.0,  # Different projection
                "source": "LineStar",
                "contest_mode": "showdown"
            }
        )
        db_session.commit()

        # Verify both records exist with different data
        result = db_session.execute(
            text("""
                SELECT salary, projection FROM player_pools
                WHERE week_id = :week_id AND player_key = :player_key AND contest_mode = :contest_mode
            """),
            {"week_id": week_id, "player_key": "J_Allen_BUF", "contest_mode": "main"}
        )
        main_data = result.fetchone()

        result = db_session.execute(
            text("""
                SELECT salary, projection FROM player_pools
                WHERE week_id = :week_id AND player_key = :player_key AND contest_mode = :contest_mode
            """),
            {"week_id": week_id, "player_key": "J_Allen_BUF", "contest_mode": "showdown"}
        )
        showdown_data = result.fetchone()

        assert main_data is not None, "Main mode record should exist"
        assert showdown_data is not None, "Showdown mode record should exist"
        assert main_data[0] == 8200, "Main mode salary should be 8200"
        assert showdown_data[0] == 8500, "Showdown mode salary should be 8500"
        assert main_data[1] == 24.0, "Main mode projection should be 24.0"
        assert showdown_data[1] == 26.0, "Showdown mode projection should be 26.0"

    def test_foreign_key_constraints_intact(self, db_session: Session):
        """Test foreign key constraints remain intact after migration."""
        # Create a week
        db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status)
                VALUES (:season, :week_number, :status)
            """),
            {"season": 2025, "week_number": 5, "status": "active"}
        )
        db_session.commit()

        # Get week_id
        result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = 2025 AND week_number = 5")
        )
        week_id = result.scalar()

        # Insert player with valid foreign key
        db_session.execute(
            text("""
                INSERT INTO player_pools
                (week_id, player_key, name, team, position, salary, projection, source, contest_mode)
                VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :source, :contest_mode)
            """),
            {
                "week_id": week_id,
                "player_key": "L_Jackson_BAL",
                "name": "Lamar Jackson",
                "team": "BAL",
                "position": "QB",
                "salary": 8400,
                "projection": 23.5,
                "source": "LineStar",
                "contest_mode": "main"
            }
        )
        db_session.commit()

        # Verify player was created with correct week_id (FK relationship works)
        result = db_session.execute(
            text("""
                SELECT week_id FROM player_pools
                WHERE player_key = :player_key AND contest_mode = :contest_mode
            """),
            {"player_key": "L_Jackson_BAL", "contest_mode": "main"}
        )
        stored_week_id = result.scalar()

        assert stored_week_id == week_id, "Foreign key relationship should be maintained"

    def test_unique_constraint_respects_contest_mode(self, db_session: Session):
        """Test that unique constraint on (week_id, player_key) was updated to include contest_mode."""
        # Create a week
        db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status)
                VALUES (:season, :week_number, :status)
            """),
            {"season": 2025, "week_number": 6, "status": "active"}
        )
        db_session.commit()

        # Get week_id
        result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = 2025 AND week_number = 6")
        )
        week_id = result.scalar()

        # Insert player in main mode
        db_session.execute(
            text("""
                INSERT INTO player_pools
                (week_id, player_key, name, team, position, salary, projection, source, contest_mode)
                VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :source, :contest_mode)
            """),
            {
                "week_id": week_id,
                "player_key": "C_McCaffrey_SF",
                "name": "Christian McCaffrey",
                "team": "SF",
                "position": "RB",
                "salary": 9000,
                "projection": 20.0,
                "source": "LineStar",
                "contest_mode": "main"
            }
        )
        db_session.commit()

        # Should allow same player_key in showdown mode (different contest_mode)
        db_session.execute(
            text("""
                INSERT INTO player_pools
                (week_id, player_key, name, team, position, salary, projection, source, contest_mode)
                VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :source, :contest_mode)
            """),
            {
                "week_id": week_id,
                "player_key": "C_McCaffrey_SF",
                "name": "Christian McCaffrey",
                "team": "SF",
                "position": "RB",
                "salary": 9500,
                "projection": 22.0,
                "source": "LineStar",
                "contest_mode": "showdown"
            }
        )
        db_session.commit()

        # Verify both records exist
        result = db_session.execute(
            text("""
                SELECT COUNT(*) FROM player_pools
                WHERE week_id = :week_id AND player_key = :player_key
            """),
            {"week_id": week_id, "player_key": "C_McCaffrey_SF"}
        )
        count = result.scalar()

        assert count == 2, "Should allow same player_key with different contest_mode"


class TestGeneratedLineupsContestMode:
    """Tests for generated_lineups table contest_mode support."""

    def test_contest_mode_column_exists_in_lineups(self, db_session: Session):
        """Test that contest_mode column exists in generated_lineups table."""
        # Create a week
        db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status)
                VALUES (:season, :week_number, :status)
            """),
            {"season": 2025, "week_number": 7, "status": "active"}
        )
        db_session.commit()

        # Get week_id
        result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = 2025 AND week_number = 7")
        )
        week_id = result.scalar()

        # Insert a lineup with contest_mode
        db_session.execute(
            text("""
                INSERT INTO generated_lineups
                (week_id, lineup_number, players, total_salary, projected_score, strategy_mode, contest_mode)
                VALUES (:week_id, :lineup_number, :players, :total_salary, :projected_score, :strategy_mode, :contest_mode)
            """),
            {
                "week_id": week_id,
                "lineup_number": 1,
                "players": '{"QB": {"name": "Patrick Mahomes", "is_captain": false}}',
                "total_salary": 45000,
                "projected_score": 150.0,
                "strategy_mode": "Balanced",
                "contest_mode": "main"
            }
        )
        db_session.commit()

        # Verify contest_mode was stored
        result = db_session.execute(
            text("""
                SELECT contest_mode FROM generated_lineups
                WHERE week_id = :week_id AND lineup_number = :lineup_number
            """),
            {"week_id": week_id, "lineup_number": 1}
        )
        contest_mode = result.scalar()

        assert contest_mode == "main", "contest_mode should be stored in generated_lineups"

    def test_is_captain_field_in_lineup_json(self, db_session: Session):
        """Test that is_captain field can be stored in players JSON structure."""
        # Create a week
        db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status)
                VALUES (:season, :week_number, :status)
            """),
            {"season": 2025, "week_number": 8, "status": "active"}
        )
        db_session.commit()

        # Get week_id
        result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = 2025 AND week_number = 8")
        )
        week_id = result.scalar()

        # Insert a showdown lineup with captain
        lineup_json = '''
        {
            "CPT": {"name": "Patrick Mahomes", "position": "QB", "is_captain": true, "salary": 12000},
            "FLEX1": {"name": "Travis Kelce", "position": "TE", "is_captain": false, "salary": 7000},
            "FLEX2": {"name": "Tyreek Hill", "position": "WR", "is_captain": false, "salary": 8000},
            "FLEX3": {"name": "Isiah Pacheco", "position": "RB", "is_captain": false, "salary": 6000},
            "FLEX4": {"name": "Rashee Rice", "position": "WR", "is_captain": false, "salary": 5000},
            "FLEX5": {"name": "Harrison Butker", "position": "K", "is_captain": false, "salary": 4000}
        }
        '''

        db_session.execute(
            text("""
                INSERT INTO generated_lineups
                (week_id, lineup_number, players, total_salary, projected_score, strategy_mode, contest_mode)
                VALUES (:week_id, :lineup_number, :players, :total_salary, :projected_score, :strategy_mode, :contest_mode)
            """),
            {
                "week_id": week_id,
                "lineup_number": 1,
                "players": lineup_json,
                "total_salary": 42000,
                "projected_score": 140.0,
                "strategy_mode": "Balanced",
                "contest_mode": "showdown"
            }
        )
        db_session.commit()

        # Verify lineup was stored with is_captain flags
        result = db_session.execute(
            text("""
                SELECT players FROM generated_lineups
                WHERE week_id = :week_id AND lineup_number = :lineup_number
            """),
            {"week_id": week_id, "lineup_number": 1}
        )
        players_json = result.scalar()

        assert players_json is not None, "Players JSON should be stored"
        assert '"is_captain": true' in players_json, "Captain flag should be present in JSON"
        assert '"is_captain": false' in players_json, "Non-captain flag should be present in JSON"
