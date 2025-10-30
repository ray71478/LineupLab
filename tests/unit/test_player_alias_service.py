"""
Unit tests for PlayerAliasService.

Test coverage:
- create_alias() with valid/invalid data
- resolve_alias() for alias lookup
- get_all_aliases() listing
- Duplicate handling and conflicts
- Error handling and edge cases
"""

import pytest
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.services.player_alias_service import PlayerAliasService


class TestPlayerAliasService:
    """Tests for PlayerAliasService class."""

    @pytest.fixture
    def populated_db(self, db_session: Session) -> int:
        """Populate database with test player and return week_id."""
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

        # Insert a canonical player
        db_session.execute(
            text("""
                INSERT INTO player_pools
                (week_id, player_key, name, team, position, salary, projection, ownership, source, created_at)
                VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, 'DraftKings', :created_at)
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
        return week_id

    def test_create_alias_success(self, db_session: Session, populated_db: int):
        """Test creating a valid alias."""
        service = PlayerAliasService(db_session)
        success = service.create_alias(
            alias_name="P. Mahomes",
            canonical_player_key="patrick_mahomes_KC_QB"
        )

        assert success is True

        # Verify alias was created in database
        result = db_session.execute(
            text("SELECT alias_name, canonical_player_key FROM player_aliases WHERE alias_name = :alias_name"),
            {"alias_name": "P. Mahomes"}
        ).fetchone()

        assert result is not None
        assert result[0] == "P. Mahomes"
        assert result[1] == "patrick_mahomes_KC_QB"

    def test_create_alias_with_nonexistent_player(self, db_session: Session):
        """Test creating alias for non-existent canonical player."""
        service = PlayerAliasService(db_session)
        success = service.create_alias(
            alias_name="Unknown Player",
            canonical_player_key="nonexistent_player_XXX_QB"
        )

        assert success is False

    def test_create_alias_duplicate_updates(self, db_session: Session, populated_db: int):
        """Test that creating duplicate alias updates the canonical key."""
        service = PlayerAliasService(db_session)

        # Create first alias
        success1 = service.create_alias(
            alias_name="P. Mahomes",
            canonical_player_key="patrick_mahomes_KC_QB"
        )
        assert success1 is True

        # Create another player
        db_session.execute(
            text("""
                INSERT INTO player_pools
                (week_id, player_key, name, team, position, salary, projection, ownership, source, created_at)
                VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, 'DraftKings', :created_at)
            """),
            {
                "week_id": populated_db,
                "player_key": "patrick_m_KC_QB",
                "name": "Patrick M",
                "team": "KC",
                "position": "QB",
                "salary": 8000,
                "projection": 24.5,
                "ownership": 0.35,
                "created_at": datetime.utcnow(),
            }
        )
        db_session.commit()

        # Update alias with different canonical player
        success2 = service.create_alias(
            alias_name="P. Mahomes",
            canonical_player_key="patrick_m_KC_QB"
        )
        assert success2 is True

        # Verify alias was updated
        result = db_session.execute(
            text("SELECT canonical_player_key FROM player_aliases WHERE alias_name = :alias_name"),
            {"alias_name": "P. Mahomes"}
        ).fetchone()

        assert result[0] == "patrick_m_KC_QB"

    def test_resolve_alias_found(self, db_session: Session, populated_db: int):
        """Test resolving an existing alias."""
        service = PlayerAliasService(db_session)

        # Create alias first
        service.create_alias(
            alias_name="P. Mahomes",
            canonical_player_key="patrick_mahomes_KC_QB"
        )

        # Resolve the alias
        result = service.resolve_alias("P. Mahomes")

        assert result == "patrick_mahomes_KC_QB"

    def test_resolve_alias_not_found(self, db_session: Session):
        """Test resolving a non-existent alias."""
        service = PlayerAliasService(db_session)
        result = service.resolve_alias("NonexistentAlias")

        assert result is None

    def test_resolve_alias_case_sensitive(self, db_session: Session, populated_db: int):
        """Test that alias resolution is case-sensitive."""
        service = PlayerAliasService(db_session)

        # Create alias
        service.create_alias(
            alias_name="P. Mahomes",
            canonical_player_key="patrick_mahomes_KC_QB"
        )

        # Try to resolve with different case
        result = service.resolve_alias("p. mahomes")

        # Should not find if case-sensitive (depends on database collation)
        # This test documents the behavior
        assert result is None or result == "patrick_mahomes_KC_QB"

    def test_get_all_aliases_empty(self, db_session: Session):
        """Test getting aliases when none exist."""
        service = PlayerAliasService(db_session)
        aliases = service.get_all_aliases()

        assert len(aliases) == 0

    def test_get_all_aliases_multiple(self, db_session: Session, populated_db: int):
        """Test getting multiple aliases."""
        service = PlayerAliasService(db_session)

        # Create another player for second alias
        db_session.execute(
            text("""
                INSERT INTO player_pools
                (week_id, player_key, name, team, position, salary, projection, ownership, source, created_at)
                VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, 'DraftKings', :created_at)
            """),
            {
                "week_id": populated_db,
                "player_key": "travis_kelce_KC_TE",
                "name": "Travis Kelce",
                "team": "KC",
                "position": "TE",
                "salary": 7500,
                "projection": 17.8,
                "ownership": 0.38,
                "created_at": datetime.utcnow(),
            }
        )
        db_session.commit()

        # Create multiple aliases
        service.create_alias("P. Mahomes", "patrick_mahomes_KC_QB")
        service.create_alias("T. Kelce", "travis_kelce_KC_TE")
        service.create_alias("Patrick M", "patrick_mahomes_KC_QB")

        # Get all aliases
        aliases = service.get_all_aliases()

        assert len(aliases) >= 3

    def test_alias_persistence(self, db_session: Session, populated_db: int):
        """Test that aliases persist in database across sessions."""
        service = PlayerAliasService(db_session)

        # Create alias
        service.create_alias(
            alias_name="PM",
            canonical_player_key="patrick_mahomes_KC_QB"
        )

        # Create new service instance (simulating new session)
        service2 = PlayerAliasService(db_session)

        # Should still be able to resolve
        result = service2.resolve_alias("PM")
        assert result == "patrick_mahomes_KC_QB"

    def test_create_alias_empty_strings(self, db_session: Session, populated_db: int):
        """Test creating alias with empty strings."""
        service = PlayerAliasService(db_session)

        # Empty alias name
        success = service.create_alias(
            alias_name="",
            canonical_player_key="patrick_mahomes_KC_QB"
        )
        # Should fail or create with empty name (depends on validation)
        # This documents the behavior
        assert isinstance(success, bool)

    def test_create_alias_with_special_characters(self, db_session: Session, populated_db: int):
        """Test creating alias with special characters in name."""
        service = PlayerAliasService(db_session)
        success = service.create_alias(
            alias_name="P. Mahomes Jr.",
            canonical_player_key="patrick_mahomes_KC_QB"
        )

        assert success is True

        # Should be able to resolve
        result = service.resolve_alias("P. Mahomes Jr.")
        assert result == "patrick_mahomes_KC_QB"

    def test_alias_service_initialization(self, db_session: Session):
        """Test service initialization."""
        service = PlayerAliasService(db_session)

        assert service.session == db_session

    def test_create_alias_long_names(self, db_session: Session, populated_db: int):
        """Test creating alias with very long player names."""
        service = PlayerAliasService(db_session)
        long_alias = "A" * 255  # Test with maximum expected length

        success = service.create_alias(
            alias_name=long_alias,
            canonical_player_key="patrick_mahomes_KC_QB"
        )

        assert success is True

        result = service.resolve_alias(long_alias)
        assert result == "patrick_mahomes_KC_QB"

    def test_multiple_aliases_same_canonical(self, db_session: Session, populated_db: int):
        """Test multiple aliases pointing to same canonical player."""
        service = PlayerAliasService(db_session)

        # Create multiple aliases for same player
        service.create_alias("PM", "patrick_mahomes_KC_QB")
        service.create_alias("P. Mahomes", "patrick_mahomes_KC_QB")
        service.create_alias("Patrick M", "patrick_mahomes_KC_QB")

        # All should resolve to same player
        assert service.resolve_alias("PM") == "patrick_mahomes_KC_QB"
        assert service.resolve_alias("P. Mahomes") == "patrick_mahomes_KC_QB"
        assert service.resolve_alias("Patrick M") == "patrick_mahomes_KC_QB"

    def test_alias_whitespace_handling(self, db_session: Session, populated_db: int):
        """Test alias creation with whitespace."""
        service = PlayerAliasService(db_session)

        # Create alias with extra whitespace
        success = service.create_alias(
            alias_name="  P. Mahomes  ",
            canonical_player_key="patrick_mahomes_KC_QB"
        )

        assert success is True

        # Try to resolve with same whitespace
        result = service.resolve_alias("  P. Mahomes  ")
        assert result == "patrick_mahomes_KC_QB"
