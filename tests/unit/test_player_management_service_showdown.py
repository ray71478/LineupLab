"""
Unit tests for PlayerManagementService - Showdown Mode Support.

Test coverage for Task Group 3:
- Importing players with showdown mode flag
- Fetching players filtered by contest mode
- Mode isolation (main slate doesn't return showdown data)
- Overwrite behavior when re-importing same mode/week
"""

import pytest
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.services.player_management_service import PlayerManagementService
from backend.schemas.player_schemas import PlayerResponse


class TestPlayerManagementServiceShowdown:
    """Tests for PlayerManagementService showdown mode functionality."""

    @pytest.fixture
    def week_with_both_modes(self, db_session: Session) -> int:
        """Create a week with both main and showdown data."""
        # Create a week
        result = db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status)
                VALUES (:season, :week_number, 'active')
            """),
            {"season": 2025, "week_number": 10}
        )
        db_session.commit()
        week_id = result.lastrowid

        # Insert main slate players
        main_players = [
            ("patrick_mahomes_KC_QB", "Patrick Mahomes", "KC", "QB", 8000, 24.5, 0.35, "main"),
            ("josh_allen_BUF_QB", "Josh Allen", "BUF", "QB", 7800, 23.2, 0.28, "main"),
            ("christian_mccaffrey_SF_RB", "Christian McCaffrey", "SF", "RB", 7500, 18.5, 0.42, "main"),
        ]

        # Insert showdown players (SEA @ WAS)
        showdown_players = [
            ("jayden_daniels_WAS_QB", "Jayden Daniels", "WAS", "QB", 11600, 19.84, 0.776, "showdown"),
            ("sam_darnold_SEA_QB", "Sam Darnold", "SEA", "QB", 10600, 17.54, 0.762, "showdown"),
            ("jaxon_smith_njigba_SEA_WR", "Jaxon Smith-Njigba", "SEA", "WR", 12000, 19.69, 0.609, "showdown"),
            ("jason_myers_SEA_K", "Jason Myers", "SEA", "K", 5000, 11.49, 0.410, "showdown"),
            ("matt_gay_WAS_K", "Matt Gay", "WAS", "K", 4800, 8.76, 0.216, "showdown"),
        ]

        all_players = main_players + showdown_players

        for player_key, name, team, position, salary, projection, ownership, contest_mode in all_players:
            db_session.execute(
                text("""
                    INSERT INTO player_pools
                    (week_id, player_key, name, team, position, salary, projection, ownership,
                     source, contest_mode, created_at)
                    VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection,
                            :ownership, 'LineStar', :contest_mode, :created_at)
                """),
                {
                    "week_id": week_id,
                    "player_key": player_key,
                    "name": name,
                    "team": team,
                    "position": position,
                    "salary": salary,
                    "projection": projection,
                    "ownership": ownership,
                    "contest_mode": contest_mode,
                    "created_at": datetime.utcnow(),
                }
            )

        db_session.commit()
        return week_id

    def test_fetch_players_main_mode_only(self, db_session: Session, week_with_both_modes: int):
        """Test fetching players with main mode filter returns only main slate players."""
        service = PlayerManagementService(db_session)
        players, total, unmatched_count = service.get_players_by_week(
            week_with_both_modes,
            contest_mode="main"
        )

        assert len(players) == 3, "Should return 3 main slate players"
        assert total == 3
        assert all(p.contest_mode == "main" for p in players), "All players should be main mode"

        # Verify no showdown players returned
        player_names = {p.name for p in players}
        assert "Jayden Daniels" not in player_names
        assert "Jason Myers" not in player_names

    def test_fetch_players_showdown_mode_only(self, db_session: Session, week_with_both_modes: int):
        """Test fetching players with showdown mode filter returns only showdown players."""
        service = PlayerManagementService(db_session)
        players, total, unmatched_count = service.get_players_by_week(
            week_with_both_modes,
            contest_mode="showdown"
        )

        assert len(players) == 5, "Should return 5 showdown players"
        assert total == 5
        assert all(p.contest_mode == "showdown" for p in players), "All players should be showdown mode"

        # Verify showdown players present
        player_names = {p.name for p in players}
        assert "Jayden Daniels" in player_names
        assert "Jason Myers" in player_names
        assert "Matt Gay" in player_names

    def test_mode_isolation_main_slate_no_showdown_data(self, db_session: Session, week_with_both_modes: int):
        """Test that main slate query does not return showdown data."""
        service = PlayerManagementService(db_session)
        players, total, _ = service.get_players_by_week(
            week_with_both_modes,
            contest_mode="main"
        )

        # Verify no kickers in main slate (showdown has kickers)
        assert not any(p.position == "K" for p in players), "Main slate should not have kickers from showdown"

        # Verify teams are different
        main_teams = {p.team for p in players}
        assert "SEA" not in main_teams, "SEA is showdown only in this test"
        assert "WAS" not in main_teams, "WAS is showdown only in this test"

    def test_mode_isolation_showdown_no_main_data(self, db_session: Session, week_with_both_modes: int):
        """Test that showdown query does not return main slate data."""
        service = PlayerManagementService(db_session)
        players, total, _ = service.get_players_by_week(
            week_with_both_modes,
            contest_mode="showdown"
        )

        # Verify SF RB (main slate) not in showdown
        player_keys = {p.player_key for p in players}
        assert "christian_mccaffrey_SF_RB" not in player_keys, "Main slate player should not be in showdown"

        # Verify showdown teams only
        showdown_teams = {p.team for p in players}
        assert showdown_teams == {"SEA", "WAS"}, "Showdown should only have SEA and WAS teams"

    def test_fetch_players_default_mode_is_main(self, db_session: Session, week_with_both_modes: int):
        """Test that default contest_mode parameter is 'main'."""
        service = PlayerManagementService(db_session)

        # Call without contest_mode parameter
        players, total, _ = service.get_players_by_week(week_with_both_modes)

        # Should default to main mode
        assert len(players) == 3, "Should return main slate players by default"
        assert all(p.contest_mode == "main" for p in players)

    def test_overwrite_showdown_data_same_week(self, db_session: Session):
        """Test that re-importing showdown data for same week overwrites previous data."""
        # Create a week
        result = db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status)
                VALUES (:season, :week_number, 'active')
            """),
            {"season": 2025, "week_number": 15}
        )
        db_session.commit()
        week_id = result.lastrowid

        # First import: Monday Night showdown
        db_session.execute(
            text("""
                INSERT INTO player_pools
                (week_id, player_key, name, team, position, salary, projection, ownership,
                 source, contest_mode, created_at)
                VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection,
                        :ownership, 'LineStar', 'showdown', :created_at)
            """),
            {
                "week_id": week_id,
                "player_key": "joe_burrow_CIN_QB",
                "name": "Joe Burrow",
                "team": "CIN",
                "position": "QB",
                "salary": 11000,
                "projection": 20.5,
                "ownership": 0.80,
                "created_at": datetime.utcnow(),
            }
        )
        db_session.commit()

        # Verify first import
        service = PlayerManagementService(db_session)
        players_before, _, _ = service.get_players_by_week(week_id, contest_mode="showdown")
        assert len(players_before) == 1
        assert players_before[0].name == "Joe Burrow"

        # Second import: Delete and re-import (simulating overwrite)
        db_session.execute(
            text("""
                DELETE FROM player_pools
                WHERE week_id = :week_id AND contest_mode = 'showdown'
            """),
            {"week_id": week_id}
        )

        db_session.execute(
            text("""
                INSERT INTO player_pools
                (week_id, player_key, name, team, position, salary, projection, ownership,
                 source, contest_mode, created_at)
                VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection,
                        :ownership, 'LineStar', 'showdown', :created_at)
            """),
            {
                "week_id": week_id,
                "player_key": "lamar_jackson_BAL_QB",
                "name": "Lamar Jackson",
                "team": "BAL",
                "position": "QB",
                "salary": 12000,
                "projection": 25.0,
                "ownership": 0.85,
                "created_at": datetime.utcnow(),
            }
        )
        db_session.commit()

        # Verify overwrite
        players_after, _, _ = service.get_players_by_week(week_id, contest_mode="showdown")
        assert len(players_after) == 1
        assert players_after[0].name == "Lamar Jackson", "Should have new player after overwrite"
        assert players_after[0].player_key == "lamar_jackson_BAL_QB"

    def test_main_slate_unchanged_after_showdown_import(self, db_session: Session):
        """Test that importing showdown data doesn't affect main slate data."""
        # Create a week with main slate data
        result = db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status)
                VALUES (:season, :week_number, 'active')
            """),
            {"season": 2025, "week_number": 12}
        )
        db_session.commit()
        week_id = result.lastrowid

        # Import main slate
        db_session.execute(
            text("""
                INSERT INTO player_pools
                (week_id, player_key, name, team, position, salary, projection, ownership,
                 source, contest_mode, created_at)
                VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection,
                        :ownership, 'LineStar', 'main', :created_at)
            """),
            {
                "week_id": week_id,
                "player_key": "patrick_mahomes_KC_QB",
                "name": "Patrick Mahomes",
                "team": "KC",
                "position": "QB",
                "salary": 8000,
                "projection": 24.5,
                "ownership": 0.35,
                "created_at": datetime.utcnow(),
            }
        )
        db_session.commit()

        service = PlayerManagementService(db_session)

        # Get main slate before showdown import
        main_before, _, _ = service.get_players_by_week(week_id, contest_mode="main")
        assert len(main_before) == 1
        assert main_before[0].name == "Patrick Mahomes"

        # Import showdown data
        db_session.execute(
            text("""
                INSERT INTO player_pools
                (week_id, player_key, name, team, position, salary, projection, ownership,
                 source, contest_mode, created_at)
                VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection,
                        :ownership, 'LineStar', 'showdown', :created_at)
            """),
            {
                "week_id": week_id,
                "player_key": "josh_allen_BUF_QB",
                "name": "Josh Allen",
                "team": "BUF",
                "position": "QB",
                "salary": 11800,
                "projection": 23.0,
                "ownership": 0.78,
                "created_at": datetime.utcnow(),
            }
        )
        db_session.commit()

        # Verify main slate unchanged
        main_after, _, _ = service.get_players_by_week(week_id, contest_mode="main")
        assert len(main_after) == 1, "Main slate should still have 1 player"
        assert main_after[0].name == "Patrick Mahomes", "Main slate player should be unchanged"
        assert main_after[0].contest_mode == "main"

        # Verify showdown data exists separately
        showdown, _, _ = service.get_players_by_week(week_id, contest_mode="showdown")
        assert len(showdown) == 1
        assert showdown[0].name == "Josh Allen"

    def test_showdown_file_with_kickers(self, db_session: Session):
        """Test that showdown import correctly handles kickers (Position = K)."""
        # Create a week
        result = db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status)
                VALUES (:season, :week_number, 'active')
            """),
            {"season": 2025, "week_number": 13}
        )
        db_session.commit()
        week_id = result.lastrowid

        # Import showdown with kickers
        showdown_with_kickers = [
            ("jayden_daniels_WAS_QB", "Jayden Daniels", "WAS", "QB", 11600, 19.84),
            ("jason_myers_SEA_K", "Jason Myers", "SEA", "K", 5000, 11.49),
            ("matt_gay_WAS_K", "Matt Gay", "WAS", "K", 4800, 8.76),
        ]

        for player_key, name, team, position, salary, projection in showdown_with_kickers:
            db_session.execute(
                text("""
                    INSERT INTO player_pools
                    (week_id, player_key, name, team, position, salary, projection, ownership,
                     source, contest_mode, created_at)
                    VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection,
                            :ownership, 'LineStar', 'showdown', :created_at)
                """),
                {
                    "week_id": week_id,
                    "player_key": player_key,
                    "name": name,
                    "team": team,
                    "position": position,
                    "salary": salary,
                    "projection": projection,
                    "ownership": 0.50,
                    "created_at": datetime.utcnow(),
                }
            )
        db_session.commit()

        # Verify kickers are imported and accessible
        service = PlayerManagementService(db_session)
        players, total, _ = service.get_players_by_week(week_id, contest_mode="showdown")

        assert len(players) == 3, "Should have 3 showdown players including kickers"

        kickers = [p for p in players if p.position == "K"]
        assert len(kickers) == 2, "Should have 2 kickers"

        kicker_names = {k.name for k in kickers}
        assert "Jason Myers" in kicker_names
        assert "Matt Gay" in kicker_names
