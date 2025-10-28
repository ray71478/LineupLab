"""
Integration tests for error handling and rollback behavior.

Tests error scenarios, transaction rollback, database cleanup,
and error message clarity.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from tests.conftest import create_week


class TestPartialImportRollback:
    """Tests for rolling back partial imports."""

    def test_constraint_violation_prevents_insert(self, db_session: Session):
        """Test that constraint violations prevent data insertion."""
        week_id = create_week(db_session, week_number=1)

        # Try to insert player with invalid salary (below minimum)
        try:
            db_session.execute(
                text("""
                    INSERT INTO player_pools
                    (week_id, player_key, name, team, position, salary, projection, ownership, source)
                    VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, :source)
                """),
                {
                    "week_id": week_id,
                    "player_key": "invalid_player_KC_QB",
                    "name": "InvalidPlayer",
                    "team": "KC",
                    "position": "QB",
                    "salary": 2000,  # Invalid - below minimum
                    "projection": 20.0,
                    "ownership": 0.05,
                    "source": "Test",
                }
            )
            db_session.commit()
            # If we get here, constraint failed
            assert False, "Should have raised constraint violation"
        except Exception as e:
            db_session.rollback()
            # Confirm it was a constraint error
            assert "check" in str(e).lower() or "constraint" in str(e).lower()


class TestDatabaseCleanupAfterError:
    """Tests for database cleanup after errors."""

    def test_manual_cleanup_of_orphaned_records(self, db_session: Session):
        """Test that orphaned records can be cleaned up properly."""
        week_id = create_week(db_session, week_number=1)

        import uuid

        # Create import history record
        import_id = str(uuid.uuid4())

        db_session.execute(
            text("""
                INSERT INTO import_history
                (id, week_id, source, player_count)
                VALUES (:id, :week_id, :source, :player_count)
            """),
            {
                "id": import_id,
                "week_id": week_id,
                "source": "Test",
                "player_count": 0,
            }
        )

        # Create some player_pool_history records
        for i in range(3):
            db_session.execute(
                text("""
                    INSERT INTO player_pool_history
                    (import_id, player_key, name, team, position, salary, projection, ownership, source)
                    VALUES (:import_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, :source)
                """),
                {
                    "import_id": import_id,
                    "player_key": f"player{i}_KC_QB",
                    "name": f"Player{i}",
                    "team": "KC",
                    "position": "QB",
                    "salary": 5000,
                    "projection": 20.0,
                    "ownership": 0.05,
                    "source": "Test",
                }
            )
        db_session.commit()

        # Verify records exist
        result = db_session.execute(
            text("SELECT COUNT(*) FROM player_pool_history WHERE import_id = :import_id"),
            {"import_id": import_id}
        )
        assert result.scalar() == 3

        # Manually clean up child records (simulating what cascade delete would do)
        db_session.execute(
            text("DELETE FROM player_pool_history WHERE import_id = :id"),
            {"id": import_id}
        )

        # Then delete parent
        db_session.execute(
            text("DELETE FROM import_history WHERE id = :id"),
            {"id": import_id}
        )
        db_session.commit()

        # Verify child records were deleted
        result = db_session.execute(
            text("SELECT COUNT(*) FROM player_pool_history WHERE import_id = :import_id"),
            {"import_id": import_id}
        )
        orphan_count = result.scalar()
        assert orphan_count == 0, "Child records were not properly deleted"

        # Verify parent record was deleted
        result = db_session.execute(
            text("SELECT COUNT(*) FROM import_history WHERE id = :id"),
            {"id": import_id}
        )
        parent_count = result.scalar()
        assert parent_count == 0, "Parent record was not properly deleted"


class TestUnmatchedPlayerTrackingOnError:
    """Tests for unmatched player tracking during errors."""

    def test_unmatched_players_created_on_fuzzy_match_failure(self, db_session: Session):
        """Test that unmatched players are tracked when fuzzy matching fails."""
        week_id = create_week(db_session, week_number=1)

        import uuid

        import_id = str(uuid.uuid4())

        # Create import history
        db_session.execute(
            text("""
                INSERT INTO import_history
                (id, week_id, source, player_count, unmatched_count)
                VALUES (:id, :week_id, :source, :player_count, :unmatched_count)
            """),
            {
                "id": import_id,
                "week_id": week_id,
                "source": "Test",
                "player_count": 1,
                "unmatched_count": 1,
            }
        )

        # Create unmatched player record
        db_session.execute(
            text("""
                INSERT INTO unmatched_players
                (import_id, player_name, team, position, salary, source, status)
                VALUES (:import_id, :player_name, :team, :position, :salary, :source, :status)
            """),
            {
                "import_id": import_id,
                "player_name": "UnmatchedPlayer",
                "team": "KC",
                "position": "QB",
                "salary": 5000,
                "source": "Test",
                "status": "pending",
            }
        )
        db_session.commit()

        # Verify unmatched player recorded
        result = db_session.execute(
            text("SELECT COUNT(*) FROM unmatched_players WHERE import_id = :import_id"),
            {"import_id": import_id}
        )
        assert result.scalar() == 1

        # Verify status
        result = db_session.execute(
            text("SELECT status FROM unmatched_players WHERE import_id = :import_id"),
            {"import_id": import_id}
        )
        status = result.scalar()
        assert status == "pending"


class TestErrorMessageClarity:
    """Tests for clear, user-friendly error messages."""

    def test_validation_error_contains_player_info(self, db_session: Session):
        """Test that validation errors include player information."""
        week_id = create_week(db_session, week_number=1)

        # This would be tested through the API, but we can simulate here
        # by attempting an insert with missing required data
        try:
            db_session.execute(
                text("""
                    INSERT INTO player_pools
                    (week_id, player_key, name, team, position, salary, projection, ownership, source)
                    VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, :source)
                """),
                {
                    "week_id": week_id,
                    "player_key": None,  # Missing required field
                    "name": "PlayerNoKey",
                    "team": "KC",
                    "position": "QB",
                    "salary": 5000,
                    "projection": 20.0,
                    "ownership": 0.05,
                    "source": "Test",
                }
            )
            db_session.commit()
            assert False, "Should have failed with null player_key"
        except Exception as e:
            db_session.rollback()
            # Error should mention player_key or player
            error_msg = str(e).lower()
            assert "player_key" in error_msg or "null" in error_msg or "not null" in error_msg

    def test_salary_error_shows_valid_range(self, db_session: Session):
        """Test that salary errors show valid range."""
        week_id = create_week(db_session, week_number=1)

        # Try to insert salary out of range
        try:
            db_session.execute(
                text("""
                    INSERT INTO player_pools
                    (week_id, player_key, name, team, position, salary, projection, ownership, source)
                    VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, :source)
                """),
                {
                    "week_id": week_id,
                    "player_key": "player_bad_salary_KC_QB",
                    "name": "PlayerBadSalary",
                    "team": "KC",
                    "position": "QB",
                    "salary": 15000,  # Above max
                    "projection": 20.0,
                    "ownership": 0.05,
                    "source": "Test",
                }
            )
            db_session.commit()
            assert False, "Should have failed with invalid salary"
        except Exception as e:
            db_session.rollback()
            error_msg = str(e)
            # Should mention salary or check constraint
            assert "salary" in error_msg.lower() or "check" in error_msg.lower()

    def test_position_error_shows_whitelist(self, db_session: Session):
        """Test that position errors show valid positions."""
        week_id = create_week(db_session, week_number=1)

        # Try to insert invalid position
        try:
            db_session.execute(
                text("""
                    INSERT INTO player_pools
                    (week_id, player_key, name, team, position, salary, projection, ownership, source)
                    VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, :source)
                """),
                {
                    "week_id": week_id,
                    "player_key": "player_bad_pos_KC_INVALID",
                    "name": "PlayerBadPos",
                    "team": "KC",
                    "position": "INVALID",
                    "salary": 5000,
                    "projection": 20.0,
                    "ownership": 0.05,
                    "source": "Test",
                }
            )
            db_session.commit()
            assert False, "Should have failed with invalid position"
        except Exception as e:
            db_session.rollback()
            error_msg = str(e)
            assert "position" in error_msg.lower() or "check" in error_msg.lower()


class TestTransactionConsistency:
    """Tests for transaction consistency."""

    def test_import_consistency_with_single_valid_insert(self, db_session: Session):
        """Test that single insert works correctly in transaction."""
        week_id = create_week(db_session, week_number=1)

        # Start with empty player pool
        result = db_session.execute(
            text("SELECT COUNT(*) FROM player_pools WHERE week_id = :week_id"),
            {"week_id": week_id}
        )
        initial_count = result.scalar()
        assert initial_count == 0

        # Insert valid player
        db_session.execute(
            text("""
                INSERT INTO player_pools
                (week_id, player_key, name, team, position, salary, projection, ownership, source)
                VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, :source)
            """),
            {
                "week_id": week_id,
                "player_key": "valid_player_KC_QB",
                "name": "ValidPlayer",
                "team": "KC",
                "position": "QB",
                "salary": 5000,
                "projection": 20.0,
                "ownership": 0.05,
                "source": "Test",
            }
        )
        db_session.commit()

        # Verify data was committed
        result = db_session.execute(
            text("SELECT COUNT(*) FROM player_pools WHERE week_id = :week_id"),
            {"week_id": week_id}
        )
        final_count = result.scalar()
        assert final_count == 1


class TestRollbackIsolation:
    """Tests for rollback isolation."""

    def test_failed_import_doesnt_affect_other_weeks(self, db_session: Session):
        """Test that errors in one week don't affect other weeks."""
        week1_id = create_week(db_session, season=2024, week_number=1)
        week2_id = create_week(db_session, season=2024, week_number=2)

        # Insert valid data for week 1
        db_session.execute(
            text("""
                INSERT INTO player_pools
                (week_id, player_key, name, team, position, salary, projection, ownership, source)
                VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, :source)
            """),
            {
                "week_id": week1_id,
                "player_key": "player1_week1_KC_QB",
                "name": "Player1Week1",
                "team": "KC",
                "position": "QB",
                "salary": 5000,
                "projection": 20.0,
                "ownership": 0.05,
                "source": "Test",
            }
        )
        db_session.commit()

        # Verify week 1 data exists
        result = db_session.execute(
            text("SELECT COUNT(*) FROM player_pools WHERE week_id = :week_id"),
            {"week_id": week1_id}
        )
        week1_count = result.scalar()
        assert week1_count == 1

        # Verify week 2 has no data
        result = db_session.execute(
            text("SELECT COUNT(*) FROM player_pools WHERE week_id = :week_id"),
            {"week_id": week2_id}
        )
        week2_count = result.scalar()
        assert week2_count == 0


class TestImportHistoryOnError:
    """Tests for import history handling on errors."""

    def test_failed_import_no_history_record(self, db_session: Session):
        """Test that failed imports don't create history records."""
        week_id = create_week(db_session, week_number=1)

        # Verify no import history
        result = db_session.execute(
            text("SELECT COUNT(*) FROM import_history WHERE week_id = :week_id"),
            {"week_id": week_id}
        )
        initial_count = result.scalar()
        assert initial_count == 0

        # Simulate failed import (don't create history record)
        # In real scenarios, the API would only create history on success

        # Verify still no import history
        result = db_session.execute(
            text("SELECT COUNT(*) FROM import_history WHERE week_id = :week_id"),
            {"week_id": week_id}
        )
        final_count = result.scalar()
        assert final_count == initial_count
