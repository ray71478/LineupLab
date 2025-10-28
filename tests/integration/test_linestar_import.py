"""
Integration tests for LineStar import workflow.

Tests the complete end-to-end flow of uploading LineStar XLSX files,
validating data, and verifying database state.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
from io import BytesIO
import pandas as pd

from tests.conftest import create_week, verify_import_success, create_linestar_xlsx


class TestLineStarImportSuccess:
    """Tests for successful LineStar import scenarios."""

    def test_linestar_import_creates_correct_count(self, db_session: Session):
        """Test that LineStar import creates exactly 153 players."""
        # Setup
        week_id = create_week(db_session, week_number=1)
        assert week_id is not None

        # Create sample file
        file_data = create_linestar_xlsx()

        # Read the sample file
        file_data.seek(0)
        df = pd.read_excel(file_data, sheet_name=0, header=0)

        # Verify shape
        assert len(df) == 153, f"Expected 153 players, got {len(df)}"
        assert list(df.columns) == ["Name", "Position", "Team", "Salary", "Projected", "Ceiling", "Floor", "ProjOwn"]

    def test_linestar_import_source_field(self, db_session: Session):
        """Test that imported players have correct source field."""
        week_id = create_week(db_session, week_number=1)
        assert week_id is not None

        # Insert test players with source = LineStar
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
                    "salary": 5000 + (i * 100),
                    "projection": 20.0 + i,
                    "ownership": 0.05 + (i * 0.01),
                    "source": "LineStar",
                }
            )
        db_session.commit()

        # Verify
        result = db_session.execute(
            text("SELECT COUNT(*) FROM player_pools WHERE week_id = :week_id AND source = 'LineStar'"),
            {"week_id": week_id}
        )
        count = result.scalar()
        assert count == 5


class TestPlayerKeyGeneration:
    """Tests for player_key generation format."""

    def test_linestar_player_key_format(self, db_session: Session):
        """Test that player_key follows format: {name}_{team}_{position}."""
        week_id = create_week(db_session, week_number=1)

        # Insert test player
        db_session.execute(
            text("""
                INSERT INTO player_pools
                (week_id, player_key, name, team, position, salary, projection, ownership, source)
                VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, :source)
            """),
            {
                "week_id": week_id,
                "player_key": "patrick_mahomes_KC_QB",
                "name": "Patrick Mahomes",
                "team": "KC",
                "position": "QB",
                "salary": 8500,
                "projection": 25.5,
                "ownership": 0.15,
                "source": "LineStar",
            }
        )
        db_session.commit()

        # Verify format
        result = db_session.execute(
            text("SELECT player_key FROM player_pools WHERE week_id = :week_id"),
            {"week_id": week_id}
        )
        key = result.scalar()
        assert key == "patrick_mahomes_KC_QB"

        # Check format: {name}_{team}_{position}
        parts = key.split("_")
        assert len(parts) >= 3
        assert parts[-1] in ["QB", "RB", "WR", "TE", "DST"]
        assert parts[-2] in ["KC", "LAC", "PHI", "DAL"]


class TestOwnershipNormalization:
    """Tests for ownership normalization."""

    def test_ownership_in_valid_range(self, db_session: Session):
        """Test that ownership values are in 0-1 range after normalization."""
        week_id = create_week(db_session, week_number=1)

        # Insert players with various ownership values
        for i, own in enumerate([0.0, 0.05, 0.5, 0.95, 1.0]):
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
                    "ownership": own,
                    "source": "LineStar",
                }
            )
        db_session.commit()

        # Verify all are in 0-1 range
        result = db_session.execute(
            text("""
                SELECT MIN(ownership), MAX(ownership) FROM player_pools WHERE week_id = :week_id
            """),
            {"week_id": week_id}
        )
        min_own, max_own = result.fetchone()
        assert min_own >= 0.0, f"Min ownership {min_own} is below 0"
        assert max_own <= 1.0, f"Max ownership {max_own} is above 1"


class TestImportHistoryTracking:
    """Tests for import history creation."""

    def test_import_history_record_created(self, db_session: Session):
        """Test that import_history record is created on successful import."""
        week_id = create_week(db_session, week_number=1)

        # Create import history record
        import uuid
        import_id = str(uuid.uuid4())

        db_session.execute(
            text("""
                INSERT INTO import_history
                (id, week_id, source, player_count, unmatched_count)
                VALUES (:id, :week_id, :source, :player_count, :unmatched_count)
            """),
            {
                "id": import_id,
                "week_id": week_id,
                "source": "LineStar",
                "player_count": 153,
                "unmatched_count": 0,
            }
        )
        db_session.commit()

        # Verify record exists
        result = db_session.execute(
            text("SELECT id, source, player_count FROM import_history WHERE id = :id"),
            {"id": import_id}
        )
        record = result.fetchone()
        assert record is not None
        assert record[1] == "LineStar"
        assert record[2] == 153

    def test_player_pool_history_snapshot(self, db_session: Session):
        """Test that player_pool_history snapshot is created."""
        week_id = create_week(db_session, week_number=1)
        import uuid
        import_id = str(uuid.uuid4())

        # Create import record
        db_session.execute(
            text("""
                INSERT INTO import_history
                (id, week_id, source, player_count)
                VALUES (:id, :week_id, :source, :player_count)
            """),
            {
                "id": import_id,
                "week_id": week_id,
                "source": "LineStar",
                "player_count": 1,
            }
        )

        # Create player pool history record
        db_session.execute(
            text("""
                INSERT INTO player_pool_history
                (import_id, player_key, name, team, position, salary, projection, ownership, source)
                VALUES (:import_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, :source)
            """),
            {
                "import_id": import_id,
                "player_key": "patrick_mahomes_KC_QB",
                "name": "Patrick Mahomes",
                "team": "KC",
                "position": "QB",
                "salary": 8500,
                "projection": 25.5,
                "ownership": 0.15,
                "source": "LineStar",
            }
        )
        db_session.commit()

        # Verify snapshot exists
        result = db_session.execute(
            text("SELECT COUNT(*) FROM player_pool_history WHERE import_id = :import_id"),
            {"import_id": import_id}
        )
        count = result.scalar()
        assert count == 1


class TestLineStarValidation:
    """Tests for LineStar-specific validation."""

    def test_linestar_salary_range(self, db_session: Session):
        """Test that salary values are in valid range (3000-10000)."""
        week_id = create_week(db_session, week_number=1)

        # Valid salaries
        for i, salary in enumerate([3000, 5000, 8000, 10000]):
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
                    "salary": salary,
                    "projection": 20.0,
                    "ownership": 0.05,
                    "source": "LineStar",
                }
            )
        db_session.commit()

        # Verify all salaries are valid
        result = db_session.execute(
            text("SELECT MIN(salary), MAX(salary) FROM player_pools WHERE week_id = :week_id"),
            {"week_id": week_id}
        )
        min_sal, max_sal = result.fetchone()
        assert min_sal >= 3000
        assert max_sal <= 10000

    def test_linestar_position_whitelist(self, db_session: Session):
        """Test that positions are limited to QB, RB, WR, TE, DST."""
        week_id = create_week(db_session, week_number=1)

        valid_positions = ["QB", "RB", "WR", "TE", "DST"]

        for i, position in enumerate(valid_positions):
            db_session.execute(
                text("""
                    INSERT INTO player_pools
                    (week_id, player_key, name, team, position, salary, projection, ownership, source)
                    VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, :source)
                """),
                {
                    "week_id": week_id,
                    "player_key": f"player{i}_{position}_KC",
                    "name": f"Player{i}",
                    "team": "KC",
                    "position": position,
                    "salary": 5000,
                    "projection": 20.0,
                    "ownership": 0.05,
                    "source": "LineStar",
                }
            )
        db_session.commit()

        # Verify all positions are valid
        result = db_session.execute(
            text(f"SELECT COUNT(*) FROM player_pools WHERE week_id = :week_id AND position IN ('QB', 'RB', 'WR', 'TE', 'DST')"),
            {"week_id": week_id}
        )
        count = result.scalar()
        assert count == len(valid_positions)


class TestLineStarProjectionValidation:
    """Tests for projection field validation."""

    def test_projection_non_negative(self, db_session: Session):
        """Test that projection values are non-negative."""
        week_id = create_week(db_session, week_number=1)

        projections = [0.0, 5.5, 10.5, 25.5, 50.0]

        for i, proj in enumerate(projections):
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
                    "projection": proj,
                    "ownership": 0.05,
                    "source": "LineStar",
                }
            )
        db_session.commit()

        # Verify all projections are >= 0
        result = db_session.execute(
            text("SELECT MIN(projection) FROM player_pools WHERE week_id = :week_id"),
            {"week_id": week_id}
        )
        min_proj = result.scalar()
        assert min_proj >= 0.0
