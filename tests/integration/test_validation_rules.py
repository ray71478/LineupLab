"""
Integration tests for validation rules across all import sources.

Tests validation of salary ranges, projections, ownership, positions,
and other business rule validations.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from tests.conftest import create_week


class TestSalaryValidation:
    """Tests for salary range validation (3000-10000)."""

    def test_salary_minimum_boundary(self, db_session: Session):
        """Test that salary minimum (3000) is enforced."""
        week_id = create_week(db_session, week_number=1)

        # Valid minimum
        db_session.execute(
            text("""
                INSERT INTO player_pools
                (week_id, player_key, name, team, position, salary, projection, ownership, source)
                VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, :source)
            """),
            {
                "week_id": week_id,
                "player_key": "player_min_KC_QB",
                "name": "PlayerMin",
                "team": "KC",
                "position": "QB",
                "salary": 3000,
                "projection": 10.0,
                "ownership": 0.05,
                "source": "Test",
            }
        )
        db_session.commit()

        # Verify
        result = db_session.execute(
            text("SELECT salary FROM player_pools WHERE week_id = :week_id AND salary = 3000"),
            {"week_id": week_id}
        )
        assert result.scalar() == 3000

    def test_salary_maximum_boundary(self, db_session: Session):
        """Test that salary maximum (10000) is enforced."""
        week_id = create_week(db_session, week_number=1)

        # Valid maximum
        db_session.execute(
            text("""
                INSERT INTO player_pools
                (week_id, player_key, name, team, position, salary, projection, ownership, source)
                VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, :source)
            """),
            {
                "week_id": week_id,
                "player_key": "player_max_KC_QB",
                "name": "PlayerMax",
                "team": "KC",
                "position": "QB",
                "salary": 10000,
                "projection": 10.0,
                "ownership": 0.05,
                "source": "Test",
            }
        )
        db_session.commit()

        # Verify
        result = db_session.execute(
            text("SELECT salary FROM player_pools WHERE week_id = :week_id AND salary = 10000"),
            {"week_id": week_id}
        )
        assert result.scalar() == 10000

    def test_salary_range_valid_values(self, db_session: Session):
        """Test various valid salary values."""
        week_id = create_week(db_session, week_number=1)

        valid_salaries = [3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]

        for i, salary in enumerate(valid_salaries):
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
                    "projection": 10.0,
                    "ownership": 0.05,
                    "source": "Test",
                }
            )
        db_session.commit()

        # Verify all inserted
        result = db_session.execute(
            text("SELECT COUNT(*) FROM player_pools WHERE week_id = :week_id"),
            {"week_id": week_id}
        )
        assert result.scalar() == len(valid_salaries)


class TestProjectionValidation:
    """Tests for projection field validation (>= 0)."""

    def test_projection_zero_allowed(self, db_session: Session):
        """Test that zero projection is allowed."""
        week_id = create_week(db_session, week_number=1)

        db_session.execute(
            text("""
                INSERT INTO player_pools
                (week_id, player_key, name, team, position, salary, projection, ownership, source)
                VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, :source)
            """),
            {
                "week_id": week_id,
                "player_key": "player_zero_KC_QB",
                "name": "PlayerZero",
                "team": "KC",
                "position": "QB",
                "salary": 5000,
                "projection": 0.0,
                "ownership": 0.05,
                "source": "Test",
            }
        )
        db_session.commit()

        result = db_session.execute(
            text("SELECT projection FROM player_pools WHERE week_id = :week_id AND projection = 0"),
            {"week_id": week_id}
        )
        assert result.scalar() == 0.0

    def test_projection_positive_values(self, db_session: Session):
        """Test that positive projections are stored correctly."""
        week_id = create_week(db_session, week_number=1)

        projections = [0.0, 5.5, 10.5, 15.75, 25.5, 50.0]

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
                    "source": "Test",
                }
            )
        db_session.commit()

        # Verify all positive
        result = db_session.execute(
            text("SELECT COUNT(*) FROM player_pools WHERE week_id = :week_id AND projection >= 0"),
            {"week_id": week_id}
        )
        assert result.scalar() == len(projections)


class TestOwnershipValidation:
    """Tests for ownership field validation (0-1 range)."""

    def test_ownership_minimum_boundary(self, db_session: Session):
        """Test that ownership minimum (0) is enforced."""
        week_id = create_week(db_session, week_number=1)

        db_session.execute(
            text("""
                INSERT INTO player_pools
                (week_id, player_key, name, team, position, salary, projection, ownership, source)
                VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, :source)
            """),
            {
                "week_id": week_id,
                "player_key": "player_own0_KC_QB",
                "name": "PlayerOwn0",
                "team": "KC",
                "position": "QB",
                "salary": 5000,
                "projection": 10.0,
                "ownership": 0.0,
                "source": "Test",
            }
        )
        db_session.commit()

        result = db_session.execute(
            text("SELECT ownership FROM player_pools WHERE week_id = :week_id AND ownership = 0"),
            {"week_id": week_id}
        )
        assert result.scalar() == 0.0

    def test_ownership_maximum_boundary(self, db_session: Session):
        """Test that ownership maximum (1) is enforced."""
        week_id = create_week(db_session, week_number=1)

        db_session.execute(
            text("""
                INSERT INTO player_pools
                (week_id, player_key, name, team, position, salary, projection, ownership, source)
                VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, :source)
            """),
            {
                "week_id": week_id,
                "player_key": "player_own1_KC_QB",
                "name": "PlayerOwn1",
                "team": "KC",
                "position": "QB",
                "salary": 5000,
                "projection": 10.0,
                "ownership": 1.0,
                "source": "Test",
            }
        )
        db_session.commit()

        result = db_session.execute(
            text("SELECT ownership FROM player_pools WHERE week_id = :week_id AND ownership = 1"),
            {"week_id": week_id}
        )
        assert result.scalar() == 1.0

    def test_ownership_range_values(self, db_session: Session):
        """Test various ownership values in valid range."""
        week_id = create_week(db_session, week_number=1)

        ownership_values = [0.0, 0.05, 0.1, 0.25, 0.5, 0.75, 0.95, 1.0]

        for i, own in enumerate(ownership_values):
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
                    "projection": 10.0,
                    "ownership": own,
                    "source": "Test",
                }
            )
        db_session.commit()

        # Verify all in range
        result = db_session.execute(
            text("""
                SELECT COUNT(*) FROM player_pools
                WHERE week_id = :week_id AND ownership >= 0 AND ownership <= 1
            """),
            {"week_id": week_id}
        )
        assert result.scalar() == len(ownership_values)


class TestPositionValidation:
    """Tests for position field validation (QB, RB, WR, TE, DST)."""

    def test_all_valid_positions(self, db_session: Session):
        """Test all valid position values."""
        week_id = create_week(db_session, week_number=1)

        valid_positions = ["QB", "RB", "WR", "TE", "DST"]

        for i, pos in enumerate(valid_positions):
            db_session.execute(
                text("""
                    INSERT INTO player_pools
                    (week_id, player_key, name, team, position, salary, projection, ownership, source)
                    VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, :source)
                """),
                {
                    "week_id": week_id,
                    "player_key": f"player{i}_{pos}_KC",
                    "name": f"Player{i}",
                    "team": "KC",
                    "position": pos,
                    "salary": 5000,
                    "projection": 10.0,
                    "ownership": 0.05,
                    "source": "Test",
                }
            )
        db_session.commit()

        # Verify all positions inserted
        result = db_session.execute(
            text("""
                SELECT COUNT(*) FROM player_pools
                WHERE week_id = :week_id AND position IN ('QB', 'RB', 'WR', 'TE', 'DST')
            """),
            {"week_id": week_id}
        )
        assert result.scalar() == len(valid_positions)

    def test_position_coverage(self, db_session: Session):
        """Test each position individually."""
        week_id = create_week(db_session, week_number=1)

        positions_with_names = {
            "QB": "Patrick Mahomes",
            "RB": "Derrick Henry",
            "WR": "Travis Kelce",
            "TE": "Mark Andrews",
            "DST": "Kansas City",
        }

        for pos, name in positions_with_names.items():
            db_session.execute(
                text("""
                    INSERT INTO player_pools
                    (week_id, player_key, name, team, position, salary, projection, ownership, source)
                    VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, :source)
                """),
                {
                    "week_id": week_id,
                    "player_key": f"{name.lower().replace(' ', '_')}_{pos}_KC",
                    "name": name,
                    "team": "KC",
                    "position": pos,
                    "salary": 5000 + len(pos),
                    "projection": 15.0,
                    "ownership": 0.1,
                    "source": "Test",
                }
            )
        db_session.commit()

        # Verify each position
        for pos in positions_with_names.keys():
            result = db_session.execute(
                text("SELECT COUNT(*) FROM player_pools WHERE week_id = :week_id AND position = :position"),
                {"week_id": week_id, "position": pos}
            )
            count = result.scalar()
            assert count == 1, f"Position {pos} not inserted"


class TestWeekValidation:
    """Tests for week number validation (1-18)."""

    def test_week_boundaries(self, db_session: Session):
        """Test week number boundaries."""
        # Create weeks 1 and 18
        for week in [1, 18]:
            db_session.execute(
                text("""
                    INSERT INTO weeks (season, week_number, status)
                    VALUES (:season, :week_number, :status)
                """),
                {
                    "season": 2024,
                    "week_number": week,
                    "status": "active",
                }
            )
        db_session.commit()

        # Verify weeks created
        result = db_session.execute(
            text("SELECT COUNT(*) FROM weeks WHERE week_number IN (1, 18)")
        )
        assert result.scalar() == 2

    def test_all_18_weeks(self, db_session: Session):
        """Test that all 18 weeks can be created."""
        for week in range(1, 19):
            db_session.execute(
                text("""
                    INSERT INTO weeks (season, week_number, status)
                    VALUES (:season, :week_number, :status)
                """),
                {
                    "season": 2024,
                    "week_number": week,
                    "status": "active",
                }
            )
        db_session.commit()

        result = db_session.execute(
            text("SELECT COUNT(*) FROM weeks WHERE season = 2024")
        )
        assert result.scalar() == 18


class TestCeilingFloorValidation:
    """Tests for ceiling/floor mismatch handling."""

    def test_ceiling_greater_than_floor(self, db_session: Session):
        """Test valid ceiling > floor relationship."""
        week_id = create_week(db_session, week_number=1)

        db_session.execute(
            text("""
                INSERT INTO player_pools
                (week_id, player_key, name, team, position, salary, projection, ownership, ceiling, floor, source)
                VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, :ceiling, :floor, :source)
            """),
            {
                "week_id": week_id,
                "player_key": "player_cf_KC_QB",
                "name": "PlayerCF",
                "team": "KC",
                "position": "QB",
                "salary": 5000,
                "projection": 20.0,
                "ownership": 0.05,
                "ceiling": 25.0,
                "floor": 15.0,
                "source": "Test",
            }
        )
        db_session.commit()

        result = db_session.execute(
            text("""
                SELECT ceiling, floor FROM player_pools
                WHERE week_id = :week_id AND player_key = 'player_cf_KC_QB'
            """),
            {"week_id": week_id}
        )
        ceiling, floor = result.fetchone()
        assert ceiling > floor
        assert ceiling == 25.0
        assert floor == 15.0

    def test_ceiling_floor_optional(self, db_session: Session):
        """Test that ceiling/floor are optional fields."""
        week_id = create_week(db_session, week_number=1)

        db_session.execute(
            text("""
                INSERT INTO player_pools
                (week_id, player_key, name, team, position, salary, projection, ownership, source)
                VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, :source)
            """),
            {
                "week_id": week_id,
                "player_key": "player_opt_KC_QB",
                "name": "PlayerOpt",
                "team": "KC",
                "position": "QB",
                "salary": 5000,
                "projection": 20.0,
                "ownership": 0.05,
                "source": "Test",
            }
        )
        db_session.commit()

        result = db_session.execute(
            text("""
                SELECT ceiling, floor FROM player_pools
                WHERE week_id = :week_id AND player_key = 'player_opt_KC_QB'
            """),
            {"week_id": week_id}
        )
        ceiling, floor = result.fetchone()
        assert ceiling is None
        assert floor is None


class TestErrorMessages:
    """Tests for clear, user-friendly error messages."""

    def test_salary_out_of_range_error(self, db_session: Session):
        """Test error message for invalid salary."""
        # This would normally be caught during validation
        # Here we test the database constraint
        week_id = create_week(db_session, week_number=1)

        try:
            db_session.execute(
                text("""
                    INSERT INTO player_pools
                    (week_id, player_key, name, team, position, salary, projection, ownership, source)
                    VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, :source)
                """),
                {
                    "week_id": week_id,
                    "player_key": "player_bad_KC_QB",
                    "name": "PlayerBad",
                    "team": "KC",
                    "position": "QB",
                    "salary": 2000,  # Below minimum
                    "projection": 10.0,
                    "ownership": 0.05,
                    "source": "Test",
                }
            )
            db_session.commit()
            # If we get here without error, that's a test failure
            assert False, "Expected database constraint violation"
        except Exception as e:
            # Constraint violation occurred as expected
            assert "salary" in str(e).lower() or "check" in str(e).lower()

    def test_ownership_out_of_range_error(self, db_session: Session):
        """Test error for ownership outside 0-1 range."""
        week_id = create_week(db_session, week_number=1)

        try:
            db_session.execute(
                text("""
                    INSERT INTO player_pools
                    (week_id, player_key, name, team, position, salary, projection, ownership, source)
                    VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, :source)
                """),
                {
                    "week_id": week_id,
                    "player_key": "player_own_bad_KC_QB",
                    "name": "PlayerOwnBad",
                    "team": "KC",
                    "position": "QB",
                    "salary": 5000,
                    "projection": 10.0,
                    "ownership": 1.5,  # Above maximum
                    "source": "Test",
                }
            )
            db_session.commit()
            assert False, "Expected database constraint violation"
        except Exception as e:
            assert "ownership" in str(e).lower() or "check" in str(e).lower()
