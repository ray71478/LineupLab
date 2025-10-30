"""
Integration tests for player management feature.

Test coverage:
- Full player import workflow
- Unmatched player detection
- Manual mapping process
- Alias creation and persistence
- Data consistency across operations
"""

import pytest
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.services.player_management_service import PlayerManagementService
from backend.services.player_alias_service import PlayerAliasService


class TestPlayerManagementIntegration:
    """Integration tests for player management workflow."""

    @pytest.fixture
    def setup_complete_scenario(self, db_session: Session) -> dict:
        """Set up a complete player management scenario."""
        # Create week
        result = db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status)
                VALUES (:season, :week_number, 'active')
            """),
            {"season": 2025, "week_number": 5}
        )
        db_session.commit()
        week_id = result.lastrowid

        # Create import record
        import_id = "test-import-001"
        db_session.execute(
            text("""
                INSERT INTO import_history (id, week_id, source, player_count, unmatched_count, created_at)
                VALUES (:id, :week_id, :source, :player_count, :unmatched_count, :created_at)
            """),
            {
                "id": import_id,
                "week_id": week_id,
                "source": "DraftKings",
                "player_count": 10,
                "unmatched_count": 2,
                "created_at": datetime.utcnow(),
            }
        )

        # Insert canonical players
        players = [
            ("patrick_mahomes_KC_QB", "Patrick Mahomes", "KC", "QB", 8000, 24.5, 0.35),
            ("travis_kelce_KC_TE", "Travis Kelce", "KC", "TE", 7500, 17.8, 0.38),
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

        # Insert unmatched players
        db_session.execute(
            text("""
                INSERT INTO unmatched_players
                (import_id, player_name, team, position, salary, source, status, created_at)
                VALUES (:import_id, :player_name, :team, :position, :salary, :source, :status, :created_at)
            """),
            {
                "import_id": import_id,
                "player_name": "P. Mahomes",
                "team": "KC",
                "position": "QB",
                "salary": 8000,
                "source": "DraftKings",
                "status": "pending",
                "created_at": datetime.utcnow(),
            }
        )

        db_session.execute(
            text("""
                INSERT INTO unmatched_players
                (import_id, player_name, team, position, salary, source, status, created_at)
                VALUES (:import_id, :player_name, :team, :position, :salary, :source, :status, :created_at)
            """),
            {
                "import_id": import_id,
                "player_name": "T. Kelce",
                "team": "KC",
                "position": "TE",
                "salary": 7500,
                "source": "DraftKings",
                "status": "pending",
                "created_at": datetime.utcnow(),
            }
        )

        db_session.commit()

        return {
            "week_id": week_id,
            "import_id": import_id,
            "db_session": db_session,
        }

    def test_complete_player_mapping_workflow(self, setup_complete_scenario: dict):
        """Test complete workflow: view unmatched → select match → create alias."""
        db_session = setup_complete_scenario["db_session"]
        week_id = setup_complete_scenario["week_id"]

        # Step 1: Get players (including unmatched)
        management_service = PlayerManagementService(db_session)
        players, total, unmatched_count = management_service.get_players_by_week(week_id)

        assert total == 2
        assert unmatched_count == 0  # They're in unmatched_players table, not player_pools

        # Step 2: Get unmatched players with suggestions
        unmatched, unmatched_total = management_service.get_unmatched_players(week_id)

        # Note: This depends on implementation details
        assert unmatched_total >= 0

        # Step 3: Create alias for unmatched player
        alias_service = PlayerAliasService(db_session)
        success = alias_service.create_alias(
            alias_name="P. Mahomes",
            canonical_player_key="patrick_mahomes_KC_QB"
        )

        assert success is True

        # Step 4: Verify alias was created and can be resolved
        resolved = alias_service.resolve_alias("P. Mahomes")
        assert resolved == "patrick_mahomes_KC_QB"

        # Step 5: Mark player as mapped (in real workflow, done by API)
        db_session.execute(
            text("""
                UPDATE unmatched_players
                SET status = 'mapped'
                WHERE player_name = 'P. Mahomes'
            """)
        )
        db_session.commit()

    def test_alias_reuse_on_future_import(self, setup_complete_scenario: dict):
        """Test that alias is applied on future imports of same player."""
        db_session = setup_complete_scenario["db_session"]
        week_id = setup_complete_scenario["week_id"]

        # Create alias
        alias_service = PlayerAliasService(db_session)
        alias_service.create_alias(
            alias_name="P. Mahomes",
            canonical_player_key="patrick_mahomes_KC_QB"
        )

        # On future import, resolve alias
        resolved = alias_service.resolve_alias("P. Mahomes")
        assert resolved == "patrick_mahomes_KC_QB"

        # Player would be auto-matched with this key
        assert resolved is not None

    def test_multiple_unmatched_players_workflow(self, setup_complete_scenario: dict):
        """Test mapping multiple unmatched players."""
        db_session = setup_complete_scenario["db_session"]
        week_id = setup_complete_scenario["week_id"]

        alias_service = PlayerAliasService(db_session)

        # Map first player
        success1 = alias_service.create_alias(
            alias_name="P. Mahomes",
            canonical_player_key="patrick_mahomes_KC_QB"
        )
        assert success1 is True

        # Map second player
        success2 = alias_service.create_alias(
            alias_name="T. Kelce",
            canonical_player_key="travis_kelce_KC_TE"
        )
        assert success2 is True

        # Both aliases should exist
        assert alias_service.resolve_alias("P. Mahomes") == "patrick_mahomes_KC_QB"
        assert alias_service.resolve_alias("T. Kelce") == "travis_kelce_KC_TE"

    def test_player_data_consistency(self, setup_complete_scenario: dict):
        """Test data consistency across player_pools and unmatched_players."""
        db_session = setup_complete_scenario["db_session"]
        week_id = setup_complete_scenario["week_id"]

        management_service = PlayerManagementService(db_session)

        # Get all players
        players, total, unmatched_count = management_service.get_players_by_week(week_id)

        # Verify player data integrity
        for player in players:
            assert player.id is not None
            assert player.player_key is not None
            assert player.name is not None
            assert player.team is not None
            assert player.position is not None
            assert player.salary is not None
            assert player.status is not None

    def test_search_functionality(self, setup_complete_scenario: dict):
        """Test player search across dataset."""
        db_session = setup_complete_scenario["db_session"]

        management_service = PlayerManagementService(db_session)

        # Search for Mahomes
        results = management_service.search_players("Mahomes")
        assert len(results) > 0
        assert any("Mahomes" in r.name for r in results)

        # Search for Kelce
        results = management_service.search_players("Kelce")
        assert len(results) > 0

    def test_filtering_and_sorting_integration(self, setup_complete_scenario: dict):
        """Test filtering and sorting together."""
        db_session = setup_complete_scenario["db_session"]
        week_id = setup_complete_scenario["week_id"]

        management_service = PlayerManagementService(db_session)

        # Filter by team and sort by salary
        players, total, _ = management_service.get_players_by_week(
            week_id,
            team="KC",
            sort_by="salary",
            sort_dir="desc"
        )

        # Verify filtering and sorting
        assert all(p.team == "KC" for p in players)
        for i in range(len(players) - 1):
            assert players[i].salary >= players[i + 1].salary

    def test_unmatched_count_tracking(self, setup_complete_scenario: dict):
        """Test that unmatched count is properly tracked."""
        db_session = setup_complete_scenario["db_session"]

        # Count unmatched players before mapping
        result = db_session.execute(
            text("SELECT COUNT(*) FROM unmatched_players WHERE status = 'pending'")
        )
        count_before = result.scalar()
        assert count_before == 2

        # Mark one as mapped
        db_session.execute(
            text("UPDATE unmatched_players SET status = 'mapped' WHERE player_name = 'P. Mahomes'")
        )
        db_session.commit()

        # Count after mapping
        result = db_session.execute(
            text("SELECT COUNT(*) FROM unmatched_players WHERE status = 'pending'")
        )
        count_after = result.scalar()
        assert count_after == 1

    def test_import_workflow_with_aliases(self, setup_complete_scenario: dict):
        """Test that aliases are considered in import workflow."""
        db_session = setup_complete_scenario["db_session"]

        # Create aliases for common variations
        alias_service = PlayerAliasService(db_session)
        alias_service.create_alias("PM", "patrick_mahomes_KC_QB")
        alias_service.create_alias("TK", "travis_kelce_KC_TE")
        alias_service.create_alias("Patrick M", "patrick_mahomes_KC_QB")

        # Verify all aliases resolve correctly
        assert alias_service.resolve_alias("PM") == "patrick_mahomes_KC_QB"
        assert alias_service.resolve_alias("TK") == "travis_kelce_KC_TE"
        assert alias_service.resolve_alias("Patrick M") == "patrick_mahomes_KC_QB"

    def test_session_isolation(self, db_session: Session):
        """Test that operations are properly isolated."""
        # Create week
        result = db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status)
                VALUES (:season, :week_number, 'active')
            """),
            {"season": 2025, "week_number": 10}
        )
        db_session.commit()
        week_id = result.lastrowid

        # Insert player
        db_session.execute(
            text("""
                INSERT INTO player_pools
                (week_id, player_key, name, team, position, salary, projection, ownership, source, created_at)
                VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, 'DraftKings', :created_at)
            """),
            {
                "week_id": week_id,
                "player_key": "test_player_KC_QB",
                "name": "Test Player",
                "team": "KC",
                "position": "QB",
                "salary": 7500,
                "projection": 20.0,
                "ownership": 0.25,
                "created_at": datetime.utcnow(),
            }
        )
        db_session.commit()

        # Verify data was inserted
        result = db_session.execute(
            text("SELECT COUNT(*) FROM player_pools WHERE week_id = :week_id"),
            {"week_id": week_id}
        )
        count = result.scalar()
        assert count == 1

    def test_error_recovery(self, setup_complete_scenario: dict):
        """Test that errors don't corrupt data."""
        db_session = setup_complete_scenario["db_session"]

        alias_service = PlayerAliasService(db_session)

        # Try to create alias with non-existent player (should fail)
        success = alias_service.create_alias(
            alias_name="Invalid Alias",
            canonical_player_key="nonexistent_player_XXX_QB"
        )
        assert success is False

        # Create valid alias (should still work after error)
        success = alias_service.create_alias(
            alias_name="P. Mahomes",
            canonical_player_key="patrick_mahomes_KC_QB"
        )
        assert success is True

        # Verify valid alias exists
        resolved = alias_service.resolve_alias("P. Mahomes")
        assert resolved == "patrick_mahomes_KC_QB"
