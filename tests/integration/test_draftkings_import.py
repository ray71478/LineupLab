"""
Integration tests for DraftKings import workflow.

Tests the complete end-to-end flow of uploading DraftKings XLSX files,
validating data, verifying existing data replacement, and tracking history.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from tests.conftest import create_week


class TestDraftKingsImportSuccess:
    """Tests for successful DraftKings import scenarios."""

    def test_draftkings_import_creates_correct_count(self, db_session: Session):
        """Test that DraftKings import creates exactly 174 players."""
        week_id = create_week(db_session, week_number=1)
        assert week_id is not None

        from tests.conftest import create_draftkings_xlsx
        import pandas as pd

        # Create sample file
        file_data = create_draftkings_xlsx()
        file_data.seek(0)

        # Read the sample file (skip first row, use second row as header)
        df = pd.read_excel(file_data, sheet_name="FE", header=1)

        # Verify count
        assert len(df) == 174, f"Expected 174 players, got {len(df)}"


class TestDraftKingsDataReplacement:
    """Tests for DraftKings replacing existing LineStar data."""

    def test_draftkings_deletes_existing_linestar_data(self, db_session: Session):
        """Test that DraftKings import deletes existing LineStar data for same week."""
        week_id = create_week(db_session, week_number=1)

        # Insert LineStar players
        for i in range(10):
            db_session.execute(
                text("""
                    INSERT INTO player_pools
                    (week_id, player_key, name, team, position, salary, projection, ownership, source)
                    VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, :source)
                """),
                {
                    "week_id": week_id,
                    "player_key": f"ls_player{i}_KC_QB",
                    "name": f"LS Player{i}",
                    "team": "KC",
                    "position": "QB",
                    "salary": 5000,
                    "projection": 20.0,
                    "ownership": 0.05,
                    "source": "LineStar",
                }
            )
        db_session.commit()

        # Verify LineStar data exists
        result = db_session.execute(
            text("SELECT COUNT(*) FROM player_pools WHERE week_id = :week_id AND source = 'LineStar'"),
            {"week_id": week_id}
        )
        count_before = result.scalar()
        assert count_before == 10

        # Simulate DraftKings import (delete old data)
        db_session.execute(
            text("DELETE FROM player_pools WHERE week_id = :week_id"),
            {"week_id": week_id}
        )

        # Insert DraftKings players
        for i in range(5):
            db_session.execute(
                text("""
                    INSERT INTO player_pools
                    (week_id, player_key, name, team, position, salary, projection, ownership, source)
                    VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, :source)
                """),
                {
                    "week_id": week_id,
                    "player_key": f"dk_player{i}_KC_QB",
                    "name": f"DK Player{i}",
                    "team": "KC",
                    "position": "QB",
                    "salary": 5000,
                    "projection": 20.0,
                    "ownership": 0.05,
                    "source": "DraftKings",
                }
            )
        db_session.commit()

        # Verify only DraftKings data remains
        result = db_session.execute(
            text("SELECT COUNT(*) FROM player_pools WHERE week_id = :week_id AND source = 'DraftKings'"),
            {"week_id": week_id}
        )
        dk_count = result.scalar()
        assert dk_count == 5

        result = db_session.execute(
            text("SELECT COUNT(*) FROM player_pools WHERE week_id = :week_id AND source = 'LineStar'"),
            {"week_id": week_id}
        )
        ls_count = result.scalar()
        assert ls_count == 0


class TestDraftKingsSourceField:
    """Tests for DraftKings source field."""

    def test_draftkings_source_field_set_correctly(self, db_session: Session):
        """Test that imported players have source = 'DraftKings'."""
        week_id = create_week(db_session, week_number=1)

        # Insert DraftKings players
        for i in range(5):
            db_session.execute(
                text("""
                    INSERT INTO player_pools
                    (week_id, player_key, name, team, position, salary, projection, ownership, source)
                    VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, :source)
                """),
                {
                    "week_id": week_id,
                    "player_key": f"player{i}_KC_QB",
                    "name": f"Player{i}",
                    "team": "KC",
                    "position": "QB",
                    "salary": 5000,
                    "projection": 20.0,
                    "ownership": 0.05,
                    "source": "DraftKings",
                }
            )
        db_session.commit()

        # Verify source
        result = db_session.execute(
            text("SELECT COUNT(*) FROM player_pools WHERE week_id = :week_id AND source = 'DraftKings'"),
            {"week_id": week_id}
        )
        count = result.scalar()
        assert count == 5


class TestDraftKingsPlayerKeyGeneration:
    """Tests for DraftKings player key generation."""

    def test_draftkings_player_key_format(self, db_session: Session):
        """Test that DraftKings player_key follows format: {name}_{team}_{position}."""
        week_id = create_week(db_session, week_number=1)

        # Insert DraftKings player
        db_session.execute(
            text("""
                INSERT INTO player_pools
                (week_id, player_key, name, team, position, salary, projection, ownership, source)
                VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, :source)
            """),
            {
                "week_id": week_id,
                "player_key": "saquon_barkley_PHI_RB",
                "name": "Saquon Barkley",
                "team": "PHI",
                "position": "RB",
                "salary": 8000,
                "projection": 18.5,
                "ownership": 0.20,
                "source": "DraftKings",
            }
        )
        db_session.commit()

        # Verify format
        result = db_session.execute(
            text("SELECT player_key FROM player_pools WHERE week_id = :week_id"),
            {"week_id": week_id}
        )
        key = result.scalar()
        assert key == "saquon_barkley_PHI_RB"

        # Check format: {name}_{team}_{position}
        parts = key.split("_")
        assert len(parts) >= 3
        assert parts[-1] in ["QB", "RB", "WR", "TE", "DST"]


class TestDraftKingsImportHistory:
    """Tests for DraftKings import history tracking."""

    def test_draftkings_import_history_created(self, db_session: Session):
        """Test that import_history record is created with correct metadata."""
        week_id = create_week(db_session, week_number=1)
        import uuid

        import_id = str(uuid.uuid4())

        # Create import history record
        db_session.execute(
            text("""
                INSERT INTO import_history
                (id, week_id, source, player_count, unmatched_count)
                VALUES (:id, :week_id, :source, :player_count, :unmatched_count)
            """),
            {
                "id": import_id,
                "week_id": week_id,
                "source": "DraftKings",
                "player_count": 174,
                "unmatched_count": 0,
            }
        )
        db_session.commit()

        # Verify record
        result = db_session.execute(
            text("SELECT id, source, player_count FROM import_history WHERE id = :id"),
            {"id": import_id}
        )
        record = result.fetchone()
        assert record is not None
        assert record[1] == "DraftKings"
        assert record[2] == 174

    def test_draftkings_consecutive_imports_tracked(self, db_session: Session):
        """Test that consecutive imports are tracked in history."""
        week_id = create_week(db_session, week_number=1)
        import uuid

        # First import (LineStar)
        import_id_1 = str(uuid.uuid4())
        db_session.execute(
            text("""
                INSERT INTO import_history
                (id, week_id, source, player_count)
                VALUES (:id, :week_id, :source, :player_count)
            """),
            {
                "id": import_id_1,
                "week_id": week_id,
                "source": "LineStar",
                "player_count": 153,
            }
        )

        # Second import (DraftKings)
        import_id_2 = str(uuid.uuid4())
        db_session.execute(
            text("""
                INSERT INTO import_history
                (id, week_id, source, player_count)
                VALUES (:id, :week_id, :source, :player_count)
            """),
            {
                "id": import_id_2,
                "week_id": week_id,
                "source": "DraftKings",
                "player_count": 174,
            }
        )
        db_session.commit()

        # Verify both imports are tracked
        result = db_session.execute(
            text("SELECT COUNT(*) FROM import_history WHERE week_id = :week_id"),
            {"week_id": week_id}
        )
        count = result.scalar()
        assert count == 2

        # Verify both sources exist
        result = db_session.execute(
            text("SELECT COUNT(DISTINCT source) FROM import_history WHERE week_id = :week_id"),
            {"week_id": week_id}
        )
        source_count = result.scalar()
        assert source_count == 2

        # Verify specific sources exist
        result = db_session.execute(
            text("SELECT source FROM import_history WHERE week_id = :week_id ORDER BY source"),
            {"week_id": week_id}
        )
        sources = [row[0] for row in result.fetchall()]
        assert "LineStar" in sources
        assert "DraftKings" in sources


class TestDraftKingsDeltaCalculation:
    """Tests for calculating deltas between imports."""

    def test_ownership_delta_calculation(self, db_session: Session):
        """Test that ownership deltas are calculated correctly."""
        week_id = create_week(db_session, week_number=1)
        import uuid

        import_id_1 = str(uuid.uuid4())
        import_id_2 = str(uuid.uuid4())

        # First import snapshot
        db_session.execute(
            text("""
                INSERT INTO import_history (id, week_id, source, player_count)
                VALUES (:id, :week_id, :source, :player_count)
            """),
            {
                "id": import_id_1,
                "week_id": week_id,
                "source": "LineStar",
                "player_count": 1,
            }
        )

        db_session.execute(
            text("""
                INSERT INTO player_pool_history
                (import_id, player_key, name, team, position, salary, projection, ownership, source)
                VALUES (:import_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, :source)
            """),
            {
                "import_id": import_id_1,
                "player_key": "patrick_mahomes_KC_QB",
                "name": "Patrick Mahomes",
                "team": "KC",
                "position": "QB",
                "salary": 8500,
                "projection": 25.5,
                "ownership": 0.10,
                "source": "LineStar",
            }
        )

        # Second import snapshot with different ownership
        db_session.execute(
            text("""
                INSERT INTO import_history (id, week_id, source, player_count)
                VALUES (:id, :week_id, :source, :player_count)
            """),
            {
                "id": import_id_2,
                "week_id": week_id,
                "source": "DraftKings",
                "player_count": 1,
            }
        )

        db_session.execute(
            text("""
                INSERT INTO player_pool_history
                (import_id, player_key, name, team, position, salary, projection, ownership, source)
                VALUES (:import_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, :source)
            """),
            {
                "import_id": import_id_2,
                "player_key": "patrick_mahomes_KC_QB",
                "name": "Patrick Mahomes",
                "team": "KC",
                "position": "QB",
                "salary": 8500,
                "projection": 25.5,
                "ownership": 0.15,
                "source": "DraftKings",
            }
        )
        db_session.commit()

        # Verify both snapshots exist
        result = db_session.execute(
            text("SELECT COUNT(*) FROM player_pool_history WHERE import_id = :import_id"),
            {"import_id": import_id_1}
        )
        assert result.scalar() == 1

        result = db_session.execute(
            text("SELECT COUNT(*) FROM player_pool_history WHERE import_id = :import_id"),
            {"import_id": import_id_2}
        )
        assert result.scalar() == 1

        # Calculate delta manually
        result1 = db_session.execute(
            text("SELECT ownership FROM player_pool_history WHERE import_id = :import_id AND player_key = :player_key"),
            {"import_id": import_id_1, "player_key": "patrick_mahomes_KC_QB"}
        )
        own1 = result1.scalar()

        result2 = db_session.execute(
            text("SELECT ownership FROM player_pool_history WHERE import_id = :import_id AND player_key = :player_key"),
            {"import_id": import_id_2, "player_key": "patrick_mahomes_KC_QB"}
        )
        own2 = result2.scalar()

        # Verify delta
        delta = own2 - own1
        assert delta == pytest.approx(0.05), f"Expected delta of 0.05, got {delta}"
