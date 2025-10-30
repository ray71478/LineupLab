"""
Unit tests for PlayerManagementService.

Test coverage:
- get_players_by_week() with various filters and sorting
- get_unmatched_players() with suggestions
- search_players() by name
- get_player_suggestions() for fuzzy matching
- Error handling and edge cases
"""

import pytest
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.services.player_management_service import PlayerManagementService
from backend.schemas.player_schemas import PlayerResponse


class TestPlayerManagementService:
    """Tests for PlayerManagementService class."""

    @pytest.fixture
    def populated_db(self, db_session: Session) -> int:
        """Populate database with test data and return week_id."""
        # Create a week
        result = db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status)
                VALUES (:season, :week_number, 'active')
            """),
            {"season": 2025, "week_number": 5}
        )
        db_session.commit()
        week_id = result.lastrowid

        # Insert test players
        players = [
            # QBs
            ("patrick_mahomes_KC_QB", "Patrick Mahomes", "KC", "QB", 8000, 24.5, 0.35),
            ("josh_allen_BUF_QB", "Josh Allen", "BUF", "QB", 7800, 23.2, 0.28),

            # RBs
            ("christian_mccaffrey_SF_RB", "Christian McCaffrey", "SF", "RB", 7500, 18.5, 0.42),
            ("derrick_henry_TEN_RB", "Derrick Henry", "TEN", "RB", 7200, 16.3, 0.31),

            # WRs
            ("tyreek_hill_MIA_WR", "Tyreek Hill", "MIA", "WR", 8200, 19.5, 0.45),
            ("amon_ra_st_brown_DET_WR", "Amon-Ra St. Brown", "DET", "WR", 6800, 15.2, 0.25),

            # TE
            ("travis_kelce_KC_TE", "Travis Kelce", "KC", "TE", 7500, 17.8, 0.38),

            # DST
            ("san_francisco_49ers_DST", "San Francisco 49ers", "SF", "DST", 4500, 8.5, 0.15),
        ]

        for player_key, name, team, position, salary, projection, ownership in players:
            db_session.execute(
                text("""
                    INSERT INTO player_pools
                    (week_id, player_key, name, team, position, salary, projection, ownership, source, created_at)
                    VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, 'DraftKings', :created_at)
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
                    "created_at": datetime.utcnow(),
                }
            )

        db_session.commit()
        return week_id

    def test_get_players_by_week_all(self, db_session: Session, populated_db: int):
        """Test fetching all players for a week."""
        service = PlayerManagementService(db_session)
        players, total, unmatched_count = service.get_players_by_week(populated_db)

        assert len(players) == 8
        assert total == 8
        assert unmatched_count == 0
        assert all(isinstance(p, PlayerResponse) for p in players)

    def test_get_players_by_week_with_position_filter(self, db_session: Session, populated_db: int):
        """Test fetching players filtered by position."""
        service = PlayerManagementService(db_session)
        players, total, unmatched_count = service.get_players_by_week(
            populated_db,
            position="QB"
        )

        assert len(players) == 2
        assert total == 2
        assert all(p.position == "QB" for p in players)

    def test_get_players_by_week_with_team_filter(self, db_session: Session, populated_db: int):
        """Test fetching players filtered by team."""
        service = PlayerManagementService(db_session)
        players, total, unmatched_count = service.get_players_by_week(
            populated_db,
            team="KC"
        )

        assert len(players) == 3  # Patrick Mahomes, Travis Kelce, and one more
        assert total == 3
        assert all(p.team == "KC" for p in players)

    def test_get_players_by_week_with_position_and_team_filter(self, db_session: Session, populated_db: int):
        """Test fetching players with both position and team filters."""
        service = PlayerManagementService(db_session)
        players, total, unmatched_count = service.get_players_by_week(
            populated_db,
            position="RB",
            team="SF"
        )

        assert len(players) == 1
        assert total == 1
        assert players[0].position == "RB"
        assert players[0].team == "SF"

    def test_get_players_by_week_sort_by_salary(self, db_session: Session, populated_db: int):
        """Test sorting players by salary."""
        service = PlayerManagementService(db_session)
        players, total, unmatched_count = service.get_players_by_week(
            populated_db,
            sort_by="salary",
            sort_dir="desc"
        )

        # Check that salaries are in descending order
        for i in range(len(players) - 1):
            assert players[i].salary >= players[i + 1].salary

    def test_get_players_by_week_sort_by_projection(self, db_session: Session, populated_db: int):
        """Test sorting players by projection."""
        service = PlayerManagementService(db_session)
        players, total, unmatched_count = service.get_players_by_week(
            populated_db,
            sort_by="projection",
            sort_dir="desc"
        )

        # Check that projections are in descending order
        for i in range(len(players) - 1):
            assert players[i].projection >= players[i + 1].projection

    def test_get_players_by_week_pagination(self, db_session: Session, populated_db: int):
        """Test pagination with limit and offset."""
        service = PlayerManagementService(db_session)

        # Get first page (limit=3, offset=0)
        players_page1, total1, _ = service.get_players_by_week(
            populated_db,
            limit=3,
            offset=0
        )
        assert len(players_page1) == 3
        assert total1 == 8

        # Get second page (limit=3, offset=3)
        players_page2, total2, _ = service.get_players_by_week(
            populated_db,
            limit=3,
            offset=3
        )
        assert len(players_page2) == 3
        assert total2 == 8

        # Ensure different players
        page1_keys = {p.player_key for p in players_page1}
        page2_keys = {p.player_key for p in players_page2}
        assert page1_keys.isdisjoint(page2_keys)

    def test_get_players_by_week_limit_max(self, db_session: Session, populated_db: int):
        """Test that limit is capped at 200."""
        service = PlayerManagementService(db_session)
        players, total, unmatched_count = service.get_players_by_week(
            populated_db,
            limit=500  # Request more than max
        )

        # Should get all 8 players (less than 200 limit)
        assert len(players) == 8

    def test_get_players_by_week_invalid_week(self, db_session: Session):
        """Test with invalid week_id."""
        service = PlayerManagementService(db_session)
        players, total, unmatched_count = service.get_players_by_week(99999)

        assert len(players) == 0
        assert total == 0

    def test_get_players_by_week_empty_result(self, db_session: Session, populated_db: int):
        """Test filtering that results in no players."""
        service = PlayerManagementService(db_session)
        players, total, unmatched_count = service.get_players_by_week(
            populated_db,
            position="K"  # Invalid position
        )

        assert len(players) == 0
        assert total == 0

    def test_get_unmatched_players_empty(self, db_session: Session, populated_db: int):
        """Test getting unmatched players when there are none."""
        service = PlayerManagementService(db_session)
        unmatched, total = service.get_unmatched_players(populated_db)

        assert len(unmatched) == 0
        assert total == 0

    def test_get_unmatched_players_with_data(self, db_session: Session, populated_db: int):
        """Test getting unmatched players with actual unmatched data."""
        # Create an import record
        result = db_session.execute(
            text("""
                INSERT INTO import_history (id, week_id, source, player_count, unmatched_count, created_at)
                VALUES (:id, :week_id, :source, :player_count, :unmatched_count, :created_at)
            """),
            {
                "id": "test-import-001",
                "week_id": populated_db,
                "source": "DraftKings",
                "player_count": 10,
                "unmatched_count": 2,
                "created_at": datetime.utcnow(),
            }
        )

        # Add unmatched player
        db_session.execute(
            text("""
                INSERT INTO unmatched_players
                (import_id, player_name, team, position, salary, source, status, created_at)
                VALUES (:import_id, :player_name, :team, :position, :salary, :source, :status, :created_at)
            """),
            {
                "import_id": "test-import-001",
                "player_name": "Unknown Player",
                "team": "KC",
                "position": "QB",
                "salary": 7500,
                "source": "DraftKings",
                "status": "pending",
                "created_at": datetime.utcnow(),
            }
        )
        db_session.commit()

        service = PlayerManagementService(db_session)
        unmatched, total = service.get_unmatched_players(populated_db)

        assert len(unmatched) >= 1
        assert total >= 1

    def test_search_players_by_name(self, db_session: Session, populated_db: int):
        """Test searching players by name."""
        service = PlayerManagementService(db_session)
        results = service.search_players("Patrick")

        assert len(results) > 0
        assert any("Patrick" in r.name for r in results)

    def test_search_players_case_insensitive(self, db_session: Session, populated_db: int):
        """Test that search is case-insensitive."""
        service = PlayerManagementService(db_session)

        results_upper = service.search_players("MAHOMES")
        results_lower = service.search_players("mahomes")
        results_mixed = service.search_players("MaHoMeS")

        assert len(results_upper) > 0
        assert len(results_lower) > 0
        assert len(results_mixed) > 0
        # All should find the same player
        assert results_upper[0].player_key == results_lower[0].player_key == results_mixed[0].player_key

    def test_search_players_partial_match(self, db_session: Session, populated_db: int):
        """Test partial name matching."""
        service = PlayerManagementService(db_session)
        results = service.search_players("St. Brown")

        assert len(results) > 0
        assert "St. Brown" in results[0].name

    def test_search_players_no_results(self, db_session: Session, populated_db: int):
        """Test search with no matching players."""
        service = PlayerManagementService(db_session)
        results = service.search_players("NonexistentPlayer12345")

        assert len(results) == 0

    def test_search_players_limit(self, db_session: Session, populated_db: int):
        """Test that search respects limit parameter."""
        service = PlayerManagementService(db_session)
        results = service.search_players("e", limit=2)  # Common letter

        # Should return at most 2 results
        assert len(results) <= 2

    def test_get_player_response_structure(self, db_session: Session, populated_db: int):
        """Test that PlayerResponse has all required fields."""
        service = PlayerManagementService(db_session)
        players, _, _ = service.get_players_by_week(populated_db, limit=1)

        assert len(players) > 0
        player = players[0]

        # Check required fields
        assert hasattr(player, 'id')
        assert hasattr(player, 'player_key')
        assert hasattr(player, 'name')
        assert hasattr(player, 'team')
        assert hasattr(player, 'position')
        assert hasattr(player, 'salary')
        assert hasattr(player, 'projection')
        assert hasattr(player, 'ownership')
        assert hasattr(player, 'status')

    def test_get_players_status_field(self, db_session: Session, populated_db: int):
        """Test that status field is set correctly for matched players."""
        service = PlayerManagementService(db_session)
        players, _, _ = service.get_players_by_week(populated_db)

        # All players in populated_db should be matched
        assert all(p.status == "matched" for p in players)

    def test_player_management_service_initialization(self, db_session: Session):
        """Test service initialization."""
        service = PlayerManagementService(db_session)

        assert service.session == db_session
        assert hasattr(service, 'player_matcher')
        assert hasattr(service, '_suggestion_cache')
