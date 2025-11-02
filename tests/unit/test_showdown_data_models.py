"""
Tests for Showdown Mode Pydantic schema changes.

Tests the updated Pydantic models to support showdown mode:
- PlayerResponse schema with contest_mode field
- LineupPlayer schema with is_captain field
- LineupConfiguration schema with locked_captain_id and contest_mode fields
- Schema validation for captain constraints
- Serialization/deserialization

This test module covers Task 2.1 from the Showdown Mode implementation.
"""

import pytest
from typing import Dict, Any, List
from pydantic import ValidationError

from backend.schemas.player_schemas import PlayerResponse
from backend.schemas.lineup_schemas import (
    LineupPlayer,
    OptimizationSettings,
    LineupOptimizationRequest,
    GeneratedLineup,
)


class TestPlayerResponseSchema:
    """Tests for PlayerResponse schema with contest_mode field."""

    def test_player_response_defaults_to_main_mode(self):
        """Test that PlayerResponse contest_mode defaults to 'main'."""
        player_data = {
            "id": 1,
            "player_key": "P_Mahomes_KC_QB",
            "name": "Patrick Mahomes",
            "team": "KC",
            "position": "QB",
            "salary": 8000,
            "projection": 22.5,
            "ownership": 0.25,
            "ceiling": 30.0,
            "floor": 15.0,
            "notes": None,
            "source": "LineStar",
            "status": "matched",
            "uploaded_at": "2025-11-02T10:00:00",
        }

        player = PlayerResponse(**player_data)

        assert player.contest_mode == "main", "contest_mode should default to 'main'"
        assert player.name == "Patrick Mahomes"
        assert player.salary == 8000

    def test_player_response_accepts_showdown_mode(self):
        """Test that PlayerResponse accepts 'showdown' contest_mode."""
        player_data = {
            "id": 2,
            "player_key": "T_Kelce_KC_TE",
            "name": "Travis Kelce",
            "team": "KC",
            "position": "TE",
            "salary": 7000,
            "projection": 15.5,
            "ownership": 0.18,
            "ceiling": 22.0,
            "floor": 10.0,
            "notes": None,
            "source": "LineStar",
            "status": "matched",
            "uploaded_at": "2025-11-02T10:00:00",
            "contest_mode": "showdown",
        }

        player = PlayerResponse(**player_data)

        assert player.contest_mode == "showdown", "contest_mode should be 'showdown'"
        assert player.name == "Travis Kelce"

    def test_player_response_serializes_contest_mode(self):
        """Test that PlayerResponse serializes contest_mode correctly."""
        player_data = {
            "id": 3,
            "player_key": "J_Allen_BUF_QB",
            "name": "Josh Allen",
            "team": "BUF",
            "position": "QB",
            "salary": 8200,
            "projection": 24.0,
            "ownership": 0.30,
            "ceiling": 32.0,
            "floor": 16.0,
            "notes": None,
            "source": "LineStar",
            "status": "matched",
            "uploaded_at": "2025-11-02T10:00:00",
            "contest_mode": "showdown",
        }

        player = PlayerResponse(**player_data)
        player_dict = player.model_dump()

        assert "contest_mode" in player_dict, "contest_mode should be in serialized dict"
        assert player_dict["contest_mode"] == "showdown"


class TestLineupPlayerSchema:
    """Tests for LineupPlayer schema with is_captain field."""

    def test_lineup_player_defaults_is_captain_to_false(self):
        """Test that LineupPlayer is_captain defaults to False."""
        player_data = {
            "position": "QB",
            "player_key": "P_Mahomes_KC_QB",
            "name": "Patrick Mahomes",
            "team": "KC",
            "salary": 8000,
            "smart_score": 0.85,
            "ownership": 0.25,
            "projection": 22.5,
        }

        player = LineupPlayer(**player_data)

        assert player.is_captain is False, "is_captain should default to False"
        assert player.name == "Patrick Mahomes"
        assert player.salary == 8000

    def test_lineup_player_accepts_captain_flag(self):
        """Test that LineupPlayer accepts is_captain=True."""
        player_data = {
            "position": "QB",
            "player_key": "J_Allen_BUF_QB",
            "name": "Josh Allen",
            "team": "BUF",
            "salary": 8200,
            "smart_score": 0.90,
            "ownership": 0.30,
            "projection": 24.0,
            "is_captain": True,
        }

        player = LineupPlayer(**player_data)

        assert player.is_captain is True, "is_captain should be True"
        assert player.name == "Josh Allen"

    def test_lineup_player_computes_captain_salary(self):
        """Test that LineupPlayer provides captain_salary computed field (base * 1.5)."""
        player_data = {
            "position": "QB",
            "player_key": "P_Mahomes_KC_QB",
            "name": "Patrick Mahomes",
            "team": "KC",
            "salary": 8000,
            "smart_score": 0.85,
            "ownership": 0.25,
            "projection": 22.5,
            "is_captain": True,
        }

        player = LineupPlayer(**player_data)

        # Captain salary should be base * 1.5
        expected_captain_salary = 8000 * 1.5
        assert hasattr(player, "captain_salary"), "should have captain_salary property"
        assert player.captain_salary == expected_captain_salary, f"captain_salary should be {expected_captain_salary}"

    def test_lineup_player_computes_captain_points(self):
        """Test that LineupPlayer provides captain_points computed field (base * 1.5)."""
        player_data = {
            "position": "QB",
            "player_key": "J_Allen_BUF_QB",
            "name": "Josh Allen",
            "team": "BUF",
            "salary": 8200,
            "smart_score": 0.90,
            "ownership": 0.30,
            "projection": 24.0,
            "is_captain": True,
        }

        player = LineupPlayer(**player_data)

        # Captain points should be base * 1.5
        expected_captain_points = 24.0 * 1.5
        assert hasattr(player, "captain_points"), "should have captain_points property"
        assert player.captain_points == expected_captain_points, f"captain_points should be {expected_captain_points}"

    def test_lineup_player_serializes_is_captain(self):
        """Test that LineupPlayer serializes is_captain correctly."""
        player_data = {
            "position": "RB",
            "player_key": "C_McCaffrey_SF_RB",
            "name": "Christian McCaffrey",
            "team": "SF",
            "salary": 9000,
            "smart_score": 0.92,
            "ownership": 0.35,
            "projection": 20.0,
            "is_captain": True,
        }

        player = LineupPlayer(**player_data)
        player_dict = player.model_dump()

        assert "is_captain" in player_dict, "is_captain should be in serialized dict"
        assert player_dict["is_captain"] is True


class TestLineupOptimizationRequestSchema:
    """Tests for LineupOptimizationRequest schema with contest_mode and locked_captain_id."""

    def test_optimization_request_defaults_contest_mode_to_main(self):
        """Test that OptimizationSettings contest_mode defaults to 'main'."""
        request_data = {
            "week_id": 1,
            "settings": {
                "num_lineups": 10,
                "strategy_mode": "Tournament",
            }
        }

        request = LineupOptimizationRequest(**request_data)

        assert request.settings.contest_mode == "main", "contest_mode should default to 'main'"

    def test_optimization_request_accepts_showdown_mode(self):
        """Test that OptimizationSettings accepts 'showdown' contest_mode."""
        request_data = {
            "week_id": 1,
            "settings": {
                "num_lineups": 10,
                "strategy_mode": "Tournament",
                "contest_mode": "showdown",
            }
        }

        request = LineupOptimizationRequest(**request_data)

        assert request.settings.contest_mode == "showdown", "contest_mode should be 'showdown'"

    def test_optimization_request_accepts_locked_captain_id(self):
        """Test that OptimizationSettings accepts locked_captain_id."""
        request_data = {
            "week_id": 1,
            "settings": {
                "num_lineups": 10,
                "strategy_mode": "Tournament",
                "contest_mode": "showdown",
                "locked_captain_id": "P_Mahomes_KC_QB",
            }
        }

        request = LineupOptimizationRequest(**request_data)

        assert request.settings.locked_captain_id == "P_Mahomes_KC_QB", "locked_captain_id should be stored"

    def test_optimization_request_locked_captain_is_optional(self):
        """Test that locked_captain_id is optional and defaults to None."""
        request_data = {
            "week_id": 1,
            "settings": {
                "num_lineups": 10,
                "strategy_mode": "Tournament",
                "contest_mode": "showdown",
            }
        }

        request = LineupOptimizationRequest(**request_data)

        assert request.settings.locked_captain_id is None, "locked_captain_id should default to None"


class TestShowdownLineupValidation:
    """Tests for showdown lineup validation (exactly 1 captain per lineup)."""

    def test_generated_lineup_with_one_captain_is_valid(self):
        """Test that a showdown lineup with exactly 1 captain is valid."""
        lineup_data = {
            "lineup_number": 1,
            "players": [
                {
                    "position": "CPT",
                    "player_key": "P_Mahomes_KC_QB",
                    "name": "Patrick Mahomes",
                    "team": "KC",
                    "salary": 12000,  # Captain salary (8000 * 1.5)
                    "smart_score": 0.85,
                    "ownership": 0.25,
                    "projection": 33.75,  # Captain points (22.5 * 1.5)
                    "is_captain": True,
                },
                {
                    "position": "FLEX",
                    "player_key": "T_Kelce_KC_TE",
                    "name": "Travis Kelce",
                    "team": "KC",
                    "salary": 7000,
                    "smart_score": 0.80,
                    "ownership": 0.18,
                    "projection": 15.5,
                    "is_captain": False,
                },
                {
                    "position": "FLEX",
                    "player_key": "T_Hill_MIA_WR",
                    "name": "Tyreek Hill",
                    "team": "MIA",
                    "salary": 8000,
                    "smart_score": 0.82,
                    "ownership": 0.22,
                    "projection": 18.0,
                    "is_captain": False,
                },
                {
                    "position": "FLEX",
                    "player_key": "I_Pacheco_KC_RB",
                    "name": "Isiah Pacheco",
                    "team": "KC",
                    "salary": 6000,
                    "smart_score": 0.75,
                    "ownership": 0.15,
                    "projection": 12.0,
                    "is_captain": False,
                },
                {
                    "position": "FLEX",
                    "player_key": "R_Rice_KC_WR",
                    "name": "Rashee Rice",
                    "team": "KC",
                    "salary": 5000,
                    "smart_score": 0.70,
                    "ownership": 0.10,
                    "projection": 10.0,
                    "is_captain": False,
                },
                {
                    "position": "FLEX",
                    "player_key": "H_Butker_KC_K",
                    "name": "Harrison Butker",
                    "team": "KC",
                    "salary": 4000,
                    "smart_score": 0.65,
                    "ownership": 0.08,
                    "projection": 8.0,
                    "is_captain": False,
                },
            ],
            "total_salary": 42000,
            "projected_score": 97.25,
            "projected_points": 97.25,
            "avg_ownership": 0.165,
        }

        lineup = GeneratedLineup(**lineup_data)

        # Count captains
        captain_count = sum(1 for p in lineup.players if p.get("is_captain", False))

        assert captain_count == 1, "Showdown lineup should have exactly 1 captain"
        assert lineup.total_salary <= 50000, "Total salary should be under $50,000"


class TestSchemaSerializationDeserialization:
    """Tests for schema serialization and deserialization."""

    def test_player_response_round_trip_with_contest_mode(self):
        """Test PlayerResponse serialization and deserialization preserves contest_mode."""
        original_data = {
            "id": 1,
            "player_key": "P_Mahomes_KC_QB",
            "name": "Patrick Mahomes",
            "team": "KC",
            "position": "QB",
            "salary": 8000,
            "projection": 22.5,
            "ownership": 0.25,
            "ceiling": 30.0,
            "floor": 15.0,
            "notes": None,
            "source": "LineStar",
            "status": "matched",
            "uploaded_at": "2025-11-02T10:00:00",
            "contest_mode": "showdown",
        }

        # Serialize
        player = PlayerResponse(**original_data)
        serialized = player.model_dump()

        # Deserialize
        player_restored = PlayerResponse(**serialized)

        assert player_restored.contest_mode == "showdown", "contest_mode should be preserved"
        assert player_restored.name == "Patrick Mahomes"

    def test_lineup_player_round_trip_with_captain_flag(self):
        """Test LineupPlayer serialization and deserialization preserves is_captain."""
        original_data = {
            "position": "QB",
            "player_key": "J_Allen_BUF_QB",
            "name": "Josh Allen",
            "team": "BUF",
            "salary": 8200,
            "smart_score": 0.90,
            "ownership": 0.30,
            "projection": 24.0,
            "is_captain": True,
        }

        # Serialize
        player = LineupPlayer(**original_data)
        serialized = player.model_dump()

        # Deserialize
        player_restored = LineupPlayer(**serialized)

        assert player_restored.is_captain is True, "is_captain should be preserved"
        assert player_restored.name == "Josh Allen"
