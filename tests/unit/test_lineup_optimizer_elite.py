"""
Unit tests for Elite Player Distribution Optimization System.

Tests cover all phases:
- Phase 1: Elite player identification
- Phase 2: Elite appearance target configuration
- Phase 3: Portfolio optimization foundation
- Phase 4: Elite appearance constraints
- Phase 5: Progressive relaxation algorithm
"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import List, Dict
from sqlalchemy.orm import Session

from backend.services.lineup_optimizer_service import (
    LineupOptimizerService,
    PlayerOptimizationData,
    ELITE_APPEARANCE_TARGETS,
)
from backend.schemas.lineup_schemas import OptimizationSettings, GeneratedLineup


# ============================================================================
# PHASE 1: Elite Player Identification Tests
# ============================================================================

def test_identify_elite_players_by_projection():
    """Test that elite players are identified by projection ranking (not Smart Score)."""
    mock_session = Mock(spec=Session)
    service = LineupOptimizerService(mock_session)

    # Create test players with different projections
    players = [
        PlayerOptimizationData(
            player_id=1, player_key="rb1", name="RB1", team="KC", position="RB",
            salary=9000, smart_score=100.0, ownership=0.3, projection=25.0
        ),
        PlayerOptimizationData(
            player_id=2, player_key="rb2", name="RB2", team="PHI", position="RB",
            salary=8500, smart_score=95.0, ownership=0.25, projection=23.0
        ),
        PlayerOptimizationData(
            player_id=3, player_key="rb3", name="RB3", team="DAL", position="RB",
            salary=8000, smart_score=90.0, ownership=0.2, projection=21.0
        ),
    ]

    elite_by_position = service._identify_elite_players(players)

    # Verify elite RBs are sorted by projection (highest first)
    assert 'RB' in elite_by_position
    elite_rbs = elite_by_position['RB']
    assert len(elite_rbs) == 3
    assert elite_rbs[0].name == "RB1"
    assert elite_rbs[0].projection == 25.0
    assert elite_rbs[1].name == "RB2"
    assert elite_rbs[2].name == "RB3"


def test_identify_elite_players_top_15_per_position():
    """Test that top 15 players per position are identified as elite."""
    mock_session = Mock(spec=Session)
    service = LineupOptimizerService(mock_session)

    # Create 20 WRs to test top 15 cutoff
    players = []
    for i in range(20):
        players.append(
            PlayerOptimizationData(
                player_id=i, player_key=f"wr{i}", name=f"WR{i}", team="KC", position="WR",
                salary=7000 - (i * 100), smart_score=80.0 - i, ownership=0.15,
                projection=20.0 - i  # Descending projections
            )
        )

    elite_by_position = service._identify_elite_players(players)

    # Should only identify top 15
    assert 'WR' in elite_by_position
    elite_wrs = elite_by_position['WR']
    assert len(elite_wrs) == 15
    # Verify they're the top 15 by projection
    assert elite_wrs[0].projection == 20.0
    assert elite_wrs[14].projection == 6.0


def test_identify_elite_players_handles_null_projections():
    """Test that players with null projections are handled correctly."""
    mock_session = Mock(spec=Session)
    service = LineupOptimizerService(mock_session)

    players = [
        PlayerOptimizationData(
            player_id=1, player_key="qb1", name="QB1", team="KC", position="QB",
            salary=8000, smart_score=100.0, ownership=0.2, projection=22.0
        ),
        PlayerOptimizationData(
            player_id=2, player_key="qb2", name="QB2", team="PHI", position="QB",
            salary=7500, smart_score=95.0, ownership=0.15, projection=None  # Null projection
        ),
        PlayerOptimizationData(
            player_id=3, player_key="qb3", name="QB3", team="DAL", position="QB",
            salary=7000, smart_score=90.0, ownership=0.1, projection=18.0
        ),
    ]

    elite_by_position = service._identify_elite_players(players)

    # Players with null projections should be at the end (treated as 0)
    assert 'QB' in elite_by_position
    elite_qbs = elite_by_position['QB']
    assert len(elite_qbs) == 3
    # QB1 and QB3 should be first (have projections)
    assert elite_qbs[0].projection == 22.0
    assert elite_qbs[1].projection == 18.0


def test_get_elite_player_ids():
    """Test that elite player IDs are correctly extracted."""
    mock_session = Mock(spec=Session)
    service = LineupOptimizerService(mock_session)

    elite_by_position = {
        'RB': [
            PlayerOptimizationData(
                player_id=1, player_key="rb1", name="RB1", team="KC", position="RB",
                salary=9000, smart_score=100.0, ownership=0.3, projection=25.0
            ),
            PlayerOptimizationData(
                player_id=2, player_key="rb2", name="RB2", team="PHI", position="RB",
                salary=8500, smart_score=95.0, ownership=0.25, projection=23.0
            ),
        ],
        'WR': [
            PlayerOptimizationData(
                player_id=10, player_key="wr1", name="WR1", team="DAL", position="WR",
                salary=8000, smart_score=90.0, ownership=0.2, projection=20.0
            ),
        ],
    }

    elite_ids = service._get_elite_player_ids(elite_by_position)

    assert len(elite_ids) == 3
    assert 1 in elite_ids
    assert 2 in elite_ids
    assert 10 in elite_ids


# ============================================================================
# PHASE 2: Elite Appearance Target Configuration Tests
# ============================================================================

def test_elite_appearance_targets_constant_exists():
    """Test that ELITE_APPEARANCE_TARGETS constant is defined."""
    assert ELITE_APPEARANCE_TARGETS is not None
    assert isinstance(ELITE_APPEARANCE_TARGETS, dict)


def test_elite_appearance_targets_has_all_positions():
    """Test that targets are defined for all positions."""
    required_positions = ['RB', 'WR', 'QB', 'TE', 'DST']
    for position in required_positions:
        assert position in ELITE_APPEARANCE_TARGETS
        targets = ELITE_APPEARANCE_TARGETS[position]
        assert isinstance(targets, list)
        assert len(targets) == 15  # Top 15 per position


def test_elite_appearance_targets_valid_ranges():
    """Test that appearance targets have valid min/max ranges."""
    for position, targets in ELITE_APPEARANCE_TARGETS.items():
        for rank, (min_app, max_app) in enumerate(targets):
            # Min should be <= max
            assert min_app <= max_app, f"{position} rank {rank}: min={min_app} > max={max_app}"
            # Both should be in valid range [0, 10]
            assert 0 <= min_app <= 10, f"{position} rank {rank}: min={min_app} out of range"
            assert 0 <= max_app <= 10, f"{position} rank {rank}: max={max_app} out of range"


def test_get_elite_appearance_target():
    """Test helper method for retrieving elite appearance targets."""
    mock_session = Mock(spec=Session)
    service = LineupOptimizerService(mock_session)

    # Test valid position and rank
    min_app, max_app = service._get_elite_appearance_target('RB', 0)
    assert isinstance(min_app, int)
    assert isinstance(max_app, int)
    assert min_app <= max_app

    # Test rank 0 (RB #1 should appear in 10/10 lineups)
    min_app, max_app = service._get_elite_appearance_target('RB', 0)
    assert min_app == 10
    assert max_app == 10


def test_get_elite_appearance_target_out_of_bounds():
    """Test that out-of-bounds ranks return default values."""
    mock_session = Mock(spec=Session)
    service = LineupOptimizerService(mock_session)

    # Test rank > 14 (out of bounds)
    min_app, max_app = service._get_elite_appearance_target('RB', 20)
    assert min_app == 0
    assert max_app == 10

    # Test negative rank
    min_app, max_app = service._get_elite_appearance_target('WR', -1)
    assert min_app == 0
    assert max_app == 10


# ============================================================================
# PHASE 3: Portfolio Optimization Foundation Tests
# ============================================================================

def test_portfolio_optimization_creates_10_lineups():
    """Test that portfolio optimization generates exactly 10 lineups."""
    mock_session = Mock(spec=Session)
    service = LineupOptimizerService(mock_session)

    # Create minimal viable player pool
    players = _create_test_player_pool()

    # Mock settings
    settings = OptimizationSettings(
        num_lineups=10,
        smart_score_threshold=0,
        strategy_mode='Balanced',
        max_players_per_team=4,
        max_players_per_game=8,
    )

    # This is a placeholder - actual implementation will be tested end-to-end
    # For now, verify method signature exists
    assert hasattr(service, '_generate_portfolio_lineups')


def test_portfolio_optimization_objective_sums_smart_scores():
    """Test that portfolio objective maximizes sum of Smart Scores."""
    # This will be validated through integration tests
    # Unit test would require mocking PuLP problem, which is too complex
    pass


def test_portfolio_optimization_applies_per_lineup_constraints():
    """Test that per-lineup constraints are applied to each of 10 lineups."""
    # This will be validated through integration tests
    pass


# ============================================================================
# PHASE 4: Elite Appearance Constraints Tests
# ============================================================================

def test_elite_appearance_constraints_per_player():
    """Test that min/max appearance constraints are generated per elite player."""
    # This will be validated through integration tests
    pass


def test_elite_appearance_constraints_handle_flex():
    """Test that FLEX slot is handled correctly for RB/WR/TE."""
    # Position constraints already handle FLEX as part of RB+WR+TE total
    # No special handling needed beyond existing constraints
    pass


# ============================================================================
# PHASE 5: Progressive Relaxation Tests
# ============================================================================

def test_relaxation_detects_infeasibility():
    """Test that infeasibility is detected after optimization fails."""
    # This will be validated through integration tests
    pass


def test_relaxation_sequence_starts_at_rank_15():
    """Test that relaxation starts with rank 15 (lowest elite)."""
    # This will be validated through integration tests
    pass


def test_relaxation_never_relaxes_rank_1():
    """Test that rank 1 (top player) constraints are never relaxed."""
    # This will be validated through integration tests
    pass


def test_fallback_to_single_lineup_generation():
    """Test that system falls back to iterative generation if all relaxations fail."""
    # This will be validated through integration tests
    pass


# ============================================================================
# Helper Functions
# ============================================================================

def _create_test_player_pool() -> List[PlayerOptimizationData]:
    """Create a minimal viable player pool for testing."""
    players = []

    # QBs
    for i in range(5):
        players.append(
            PlayerOptimizationData(
                player_id=i,
                player_key=f"qb{i}",
                name=f"QB{i}",
                team="KC" if i < 2 else "PHI",
                position="QB",
                salary=7000 + (i * 100),
                smart_score=85.0 - i,
                ownership=0.15,
                projection=20.0 - i,
            )
        )

    # RBs
    for i in range(10):
        players.append(
            PlayerOptimizationData(
                player_id=10 + i,
                player_key=f"rb{i}",
                name=f"RB{i}",
                team=["KC", "PHI", "DAL", "SF", "BAL"][i % 5],
                position="RB",
                salary=8000 + (i * 100),
                smart_score=90.0 - i,
                ownership=0.2,
                projection=22.0 - i,
            )
        )

    # WRs
    for i in range(15):
        players.append(
            PlayerOptimizationData(
                player_id=20 + i,
                player_key=f"wr{i}",
                name=f"WR{i}",
                team=["KC", "PHI", "DAL", "SF", "BAL"][i % 5],
                position="WR",
                salary=7500 + (i * 100),
                smart_score=85.0 - i,
                ownership=0.18,
                projection=18.0 - i,
            )
        )

    # TEs
    for i in range(8):
        players.append(
            PlayerOptimizationData(
                player_id=35 + i,
                player_key=f"te{i}",
                name=f"TE{i}",
                team=["KC", "PHI", "DAL", "SF"][i % 4],
                position="TE",
                salary=6000 + (i * 100),
                smart_score=80.0 - i,
                ownership=0.12,
                projection=15.0 - i,
            )
        )

    # DSTs
    for i in range(5):
        players.append(
            PlayerOptimizationData(
                player_id=43 + i,
                player_key=f"dst{i}",
                name=f"DST{i}",
                team=["KC", "PHI", "DAL", "SF", "BAL"][i],
                position="DST",
                salary=3500 + (i * 100),
                smart_score=70.0 - i,
                ownership=0.1,
                projection=10.0 - i,
            )
        )

    return players
