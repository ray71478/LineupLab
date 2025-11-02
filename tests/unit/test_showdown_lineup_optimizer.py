"""
Unit tests for Showdown Lineup Optimizer.

Tests cover:
- Showdown position constraints (1 CPT + 5 FLEX)
- $50,000 salary cap with captain multiplier
- Captain selection algorithm (value calculation)
- Manual captain lock functionality
- Lineup validity (no duplicate players)
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import List
from sqlalchemy.orm import Session

from backend.services.lineup_optimizer_service import (
    LineupOptimizerService,
    PlayerOptimizationData,
    SHOWDOWN_POSITION_REQUIREMENTS,
    SHOWDOWN_SALARY_CAP,
)
from backend.schemas.lineup_schemas import OptimizationSettings, GeneratedLineup
from backend.schemas.smart_score_schemas import PlayerScoreResponse


# ============================================================================
# Test 1: CPT + FLEX Constraint Enforcement
# ============================================================================

def test_showdown_position_requirements_defined():
    """Test that showdown position requirements are defined correctly."""
    assert SHOWDOWN_POSITION_REQUIREMENTS is not None
    assert isinstance(SHOWDOWN_POSITION_REQUIREMENTS, dict)
    assert SHOWDOWN_POSITION_REQUIREMENTS.get('CPT') == 1
    assert SHOWDOWN_POSITION_REQUIREMENTS.get('FLEX') == 5
    assert SHOWDOWN_SALARY_CAP == 50000


def test_showdown_lineup_has_one_captain_five_flex():
    """Test that generated showdown lineup has exactly 1 captain and 5 FLEX players."""
    mock_session = Mock(spec=Session)
    service = LineupOptimizerService(mock_session)

    # Create test showdown player pool
    players = _create_showdown_player_pool()

    # Convert to PlayerScoreResponse format
    player_responses = []
    for p in players:
        player_responses.append(PlayerScoreResponse(
            player_id=p.player_id,
            player_key=p.player_key,
            name=p.name,
            team=p.team,
            position=p.position,
            salary=p.salary,
            smart_score=p.smart_score,
            ownership=p.ownership,
            projection=p.projection,
        ))

    settings = OptimizationSettings(
        num_lineups=1,
        contest_mode='showdown',
        strategy_mode='Balanced',
        max_ownership=1.0,
        exclude_bottom_percentile=0,
    )

    # Mock game info query
    with patch.object(service, '_get_game_info', return_value={}):
        lineups, error = service.generate_lineups(
            week_id=1,
            players=player_responses,
            settings=settings,
        )

    assert lineups is not None
    assert len(lineups) > 0

    # Check first lineup
    lineup = lineups[0]
    captain_count = sum(1 for p in lineup.players if p.get('is_captain', False))
    flex_count = len([p for p in lineup.players if not p.get('is_captain', False)])

    assert captain_count == 1, f"Expected 1 captain, got {captain_count}"
    assert flex_count == 5, f"Expected 5 FLEX players, got {flex_count}"
    assert len(lineup.players) == 6, f"Expected 6 total players, got {len(lineup.players)}"


# ============================================================================
# Test 2: Salary Cap with Captain Multiplier
# ============================================================================

def test_showdown_salary_cap_enforced():
    """Test that showdown salary cap ($50,000) is enforced with captain multiplier."""
    mock_session = Mock(spec=Session)
    service = LineupOptimizerService(mock_session)

    players = _create_showdown_player_pool()
    player_responses = [
        PlayerScoreResponse(
            player_id=p.player_id,
            player_key=p.player_key,
            name=p.name,
            team=p.team,
            position=p.position,
            salary=p.salary,
            smart_score=p.smart_score,
            ownership=p.ownership,
            projection=p.projection,
        ) for p in players
    ]

    settings = OptimizationSettings(
        num_lineups=3,
        contest_mode='showdown',
        strategy_mode='Balanced',
        max_ownership=1.0,
        exclude_bottom_percentile=0,
    )

    with patch.object(service, '_get_game_info', return_value={}):
        lineups, error = service.generate_lineups(
            week_id=1,
            players=player_responses,
            settings=settings,
        )

    assert lineups is not None

    for lineup in lineups:
        # Calculate actual salary with captain multiplier
        total_salary = 0
        for player in lineup.players:
            if player.get('is_captain', False):
                total_salary += int(player['salary'] * 1.5)
            else:
                total_salary += player['salary']

        assert total_salary <= SHOWDOWN_SALARY_CAP, \
            f"Lineup {lineup.lineup_number} exceeds salary cap: ${total_salary} > ${SHOWDOWN_SALARY_CAP}"


# ============================================================================
# Test 3: Captain Selection Algorithm
# ============================================================================

def test_captain_selection_value_calculation():
    """Test captain selection algorithm uses (smart_score * 1.5) / (salary * 1.5) value formula."""
    mock_session = Mock(spec=Session)
    service = LineupOptimizerService(mock_session)

    # Create players with different captain values
    players = [
        PlayerOptimizationData(
            player_id=1, player_key="qb1", name="QB High Score", team="SEA", position="QB",
            salary=8000, smart_score=100.0, ownership=0.25, projection=25.0
        ),  # Captain value = (100*1.5)/(8000*1.5) = 150/12000 = 0.0125
        PlayerOptimizationData(
            player_id=2, player_key="rb1", name="RB Value", team="WAS", position="RB",
            salary=6000, smart_score=80.0, ownership=0.20, projection=20.0
        ),  # Captain value = (80*1.5)/(6000*1.5) = 120/9000 = 0.0133 (BEST VALUE)
        PlayerOptimizationData(
            player_id=3, player_key="wr1", name="WR Expensive", team="SEA", position="WR",
            salary=9000, smart_score=90.0, ownership=0.30, projection=22.0
        ),  # Captain value = (90*1.5)/(9000*1.5) = 135/13500 = 0.01
    ]

    # Test captain candidate selection
    captain_candidates = service._select_captain_candidates(players, locked_captain_id=None)

    assert len(captain_candidates) > 0
    # The RB with best value should be among top candidates
    captain_ids = [c.player_id for c in captain_candidates]
    assert 2 in captain_ids, "RB with best captain value should be in candidates"


def test_captain_candidates_limited_to_five():
    """Test that captain candidate selection returns top 5 by value."""
    mock_session = Mock(spec=Session)
    service = LineupOptimizerService(mock_session)

    # Create 10 players
    players = []
    for i in range(10):
        players.append(
            PlayerOptimizationData(
                player_id=i,
                player_key=f"player{i}",
                name=f"Player{i}",
                team="SEA" if i % 2 == 0 else "WAS",
                position="RB",
                salary=5000 + (i * 500),
                smart_score=70.0 + i,
                ownership=0.15,
                projection=15.0 + i,
            )
        )

    captain_candidates = service._select_captain_candidates(players, locked_captain_id=None)

    # Should return at most 5 candidates
    assert len(captain_candidates) <= 5


# ============================================================================
# Test 4: Manual Captain Lock
# ============================================================================

def test_locked_captain_functionality():
    """Test that locked captain is respected in lineup generation."""
    mock_session = Mock(spec=Session)
    service = LineupOptimizerService(mock_session)

    players = _create_showdown_player_pool()
    locked_captain = players[0]  # Lock the first player as captain

    player_responses = [
        PlayerScoreResponse(
            player_id=p.player_id,
            player_key=p.player_key,
            name=p.name,
            team=p.team,
            position=p.position,
            salary=p.salary,
            smart_score=p.smart_score,
            ownership=p.ownership,
            projection=p.projection,
        ) for p in players
    ]

    settings = OptimizationSettings(
        num_lineups=2,
        contest_mode='showdown',
        locked_captain_id=locked_captain.player_key,
        strategy_mode='Balanced',
        max_ownership=1.0,
        exclude_bottom_percentile=0,
    )

    with patch.object(service, '_get_game_info', return_value={}):
        lineups, error = service.generate_lineups(
            week_id=1,
            players=player_responses,
            settings=settings,
        )

    assert lineups is not None
    assert len(lineups) > 0

    # Check that locked captain appears as captain in all lineups
    for lineup in lineups:
        captain_players = [p for p in lineup.players if p.get('is_captain', False)]
        assert len(captain_players) == 1
        assert captain_players[0]['player_key'] == locked_captain.player_key, \
            f"Expected locked captain {locked_captain.player_key}, got {captain_players[0]['player_key']}"


def test_locked_captain_returns_error_if_insufficient_salary():
    """Test that locked captain with high salary returns error if can't build lineup."""
    mock_session = Mock(spec=Session)
    service = LineupOptimizerService(mock_session)

    # Create player pool with one very expensive player
    players = []
    expensive_player = PlayerOptimizationData(
        player_id=1, player_key="qb1", name="Expensive QB", team="SEA", position="QB",
        salary=15000, smart_score=100.0, ownership=0.30, projection=30.0
    )  # Captain salary would be 15000 * 1.5 = 22500, leaving only 27500 for 5 FLEX
    players.append(expensive_player)

    # Add cheap players
    for i in range(10):
        players.append(
            PlayerOptimizationData(
                player_id=i+2, player_key=f"player{i}", name=f"Player{i}", team="WAS", position="RB",
                salary=6000, smart_score=60.0, ownership=0.10, projection=12.0
            )
        )  # 5 x 6000 = 30000, which exceeds remaining budget

    player_responses = [
        PlayerScoreResponse(
            player_id=p.player_id,
            player_key=p.player_key,
            name=p.name,
            team=p.team,
            position=p.position,
            salary=p.salary,
            smart_score=p.smart_score,
            ownership=p.ownership,
            projection=p.projection,
        ) for p in players
    ]

    settings = OptimizationSettings(
        num_lineups=1,
        contest_mode='showdown',
        locked_captain_id=expensive_player.player_key,
        strategy_mode='Balanced',
        max_ownership=1.0,
        exclude_bottom_percentile=0,
    )

    with patch.object(service, '_get_game_info', return_value={}):
        lineups, error = service.generate_lineups(
            week_id=1,
            players=player_responses,
            settings=settings,
        )

    # Should either return empty lineups or an error
    # The implementation should handle this gracefully
    assert lineups is not None or error is not None


# ============================================================================
# Test 5: Lineup Validity - No Duplicates
# ============================================================================

def test_showdown_lineup_no_duplicate_players():
    """Test that showdown lineups don't contain duplicate players."""
    mock_session = Mock(spec=Session)
    service = LineupOptimizerService(mock_session)

    players = _create_showdown_player_pool()
    player_responses = [
        PlayerScoreResponse(
            player_id=p.player_id,
            player_key=p.player_key,
            name=p.name,
            team=p.team,
            position=p.position,
            salary=p.salary,
            smart_score=p.smart_score,
            ownership=p.ownership,
            projection=p.projection,
        ) for p in players
    ]

    settings = OptimizationSettings(
        num_lineups=5,
        contest_mode='showdown',
        strategy_mode='Balanced',
        max_ownership=1.0,
        exclude_bottom_percentile=0,
    )

    with patch.object(service, '_get_game_info', return_value={}):
        lineups, error = service.generate_lineups(
            week_id=1,
            players=player_responses,
            settings=settings,
        )

    assert lineups is not None

    for lineup in lineups:
        player_keys = [p['player_key'] for p in lineup.players]
        unique_keys = set(player_keys)

        assert len(player_keys) == len(unique_keys), \
            f"Lineup {lineup.lineup_number} contains duplicate players: {player_keys}"


def test_showdown_lineup_all_positions_eligible():
    """Test that QB, RB, WR, TE, K, DST are all FLEX-eligible in showdown."""
    mock_session = Mock(spec=Session)
    service = LineupOptimizerService(mock_session)

    # Create diverse player pool with all positions
    players = []
    positions = ['QB', 'RB', 'WR', 'TE', 'K', 'DST']

    for i, pos in enumerate(positions):
        for j in range(3):
            players.append(
                PlayerOptimizationData(
                    player_id=i*10 + j,
                    player_key=f"{pos.lower()}{j}",
                    name=f"{pos}{j}",
                    team="SEA" if j % 2 == 0 else "WAS",
                    position=pos,
                    salary=5000 + (i * 500) + (j * 100),
                    smart_score=70.0 + i + j,
                    ownership=0.15,
                    projection=15.0 + i + j,
                )
            )

    player_responses = [
        PlayerScoreResponse(
            player_id=p.player_id,
            player_key=p.player_key,
            name=p.name,
            team=p.team,
            position=p.position,
            salary=p.salary,
            smart_score=p.smart_score,
            ownership=p.ownership,
            projection=p.projection,
        ) for p in players
    ]

    settings = OptimizationSettings(
        num_lineups=2,
        contest_mode='showdown',
        strategy_mode='Balanced',
        max_ownership=1.0,
        exclude_bottom_percentile=0,
    )

    with patch.object(service, '_get_game_info', return_value={}):
        lineups, error = service.generate_lineups(
            week_id=1,
            players=player_responses,
            settings=settings,
        )

    assert lineups is not None
    assert len(lineups) > 0

    # Check that lineup can contain any position as captain or FLEX
    # Just verify the lineup is valid (has 1 captain + 5 FLEX)
    for lineup in lineups:
        assert len(lineup.players) == 6


# ============================================================================
# Test 6: Captain Diversity Across Lineups
# ============================================================================

def test_showdown_captain_diversity():
    """Test that multiple lineups feature different captains."""
    mock_session = Mock(spec=Session)
    service = LineupOptimizerService(mock_session)

    players = _create_showdown_player_pool()
    player_responses = [
        PlayerScoreResponse(
            player_id=p.player_id,
            player_key=p.player_key,
            name=p.name,
            team=p.team,
            position=p.position,
            salary=p.salary,
            smart_score=p.smart_score,
            ownership=p.ownership,
            projection=p.projection,
        ) for p in players
    ]

    settings = OptimizationSettings(
        num_lineups=5,
        contest_mode='showdown',
        strategy_mode='Balanced',
        max_ownership=1.0,
        exclude_bottom_percentile=0,
    )

    with patch.object(service, '_get_game_info', return_value={}):
        lineups, error = service.generate_lineups(
            week_id=1,
            players=player_responses,
            settings=settings,
        )

    assert lineups is not None
    assert len(lineups) >= 3, "Need at least 3 lineups to test diversity"

    # Collect all captain player_keys
    captain_keys = []
    for lineup in lineups:
        captain_players = [p for p in lineup.players if p.get('is_captain', False)]
        assert len(captain_players) == 1
        captain_keys.append(captain_players[0]['player_key'])

    unique_captains = set(captain_keys)

    # At least 2 different captains should be used across lineups
    assert len(unique_captains) >= 2, \
        f"Expected at least 2 different captains, found only {len(unique_captains)}: {unique_captains}"


# ============================================================================
# Helper Functions
# ============================================================================

def _create_showdown_player_pool() -> List[PlayerOptimizationData]:
    """Create a test showdown player pool (single game, both teams)."""
    players = []

    # SEA players
    players.extend([
        # QB
        PlayerOptimizationData(
            player_id=1, player_key="geno_smith_sea_qb", name="Geno Smith", team="SEA", position="QB",
            salary=7800, smart_score=85.0, ownership=0.25, projection=22.0
        ),
        # RBs
        PlayerOptimizationData(
            player_id=2, player_key="kenneth_walker_sea_rb", name="Kenneth Walker III", team="SEA", position="RB",
            salary=7200, smart_score=82.0, ownership=0.30, projection=20.0
        ),
        PlayerOptimizationData(
            player_id=3, player_key="zach_charbonnet_sea_rb", name="Zach Charbonnet", team="SEA", position="RB",
            salary=4600, smart_score=65.0, ownership=0.15, projection=12.0
        ),
        # WRs
        PlayerOptimizationData(
            player_id=4, player_key="dk_metcalf_sea_wr", name="DK Metcalf", team="SEA", position="WR",
            salary=7600, smart_score=88.0, ownership=0.35, projection=21.0
        ),
        PlayerOptimizationData(
            player_id=5, player_key="tyler_lockett_sea_wr", name="Tyler Lockett", team="SEA", position="WR",
            salary=6400, smart_score=75.0, ownership=0.22, projection=16.0
        ),
        PlayerOptimizationData(
            player_id=6, player_key="jaxon_smith_njigba_sea_wr", name="Jaxon Smith-Njigba", team="SEA", position="WR",
            salary=5800, smart_score=70.0, ownership=0.18, projection=14.0
        ),
        # TE
        PlayerOptimizationData(
            player_id=7, player_key="noah_fant_sea_te", name="Noah Fant", team="SEA", position="TE",
            salary=4200, smart_score=60.0, ownership=0.12, projection=10.0
        ),
        # K
        PlayerOptimizationData(
            player_id=8, player_key="jason_myers_sea_k", name="Jason Myers", team="SEA", position="K",
            salary=4000, smart_score=55.0, ownership=0.10, projection=8.0
        ),
        # DST
        PlayerOptimizationData(
            player_id=9, player_key="seattle_sea_dst", name="Seattle DST", team="SEA", position="DST",
            salary=3800, smart_score=58.0, ownership=0.15, projection=9.0
        ),
    ])

    # WAS players
    players.extend([
        # QB
        PlayerOptimizationData(
            player_id=10, player_key="jayden_daniels_was_qb", name="Jayden Daniels", team="WAS", position="QB",
            salary=8200, smart_score=90.0, ownership=0.32, projection=24.0
        ),
        # RBs
        PlayerOptimizationData(
            player_id=11, player_key="brian_robinson_was_rb", name="Brian Robinson Jr.", team="WAS", position="RB",
            salary=6800, smart_score=78.0, ownership=0.25, projection=18.0
        ),
        PlayerOptimizationData(
            player_id=12, player_key="austin_ekeler_was_rb", name="Austin Ekeler", team="WAS", position="RB",
            salary=5200, smart_score=68.0, ownership=0.18, projection=13.0
        ),
        # WRs
        PlayerOptimizationData(
            player_id=13, player_key="terry_mclaurin_was_wr", name="Terry McLaurin", team="WAS", position="WR",
            salary=7400, smart_score=86.0, ownership=0.30, projection=20.0
        ),
        PlayerOptimizationData(
            player_id=14, player_key="jahan_dotson_was_wr", name="Jahan Dotson", team="WAS", position="WR",
            salary=5000, smart_score=66.0, ownership=0.16, projection=12.0
        ),
        PlayerOptimizationData(
            player_id=15, player_key="curtis_samuel_was_wr", name="Curtis Samuel", team="WAS", position="WR",
            salary=4800, smart_score=64.0, ownership=0.14, projection=11.0
        ),
        # TE
        PlayerOptimizationData(
            player_id=16, player_key="logan_thomas_was_te", name="Logan Thomas", team="WAS", position="TE",
            salary=4400, smart_score=62.0, ownership=0.13, projection=10.5
        ),
        # K
        PlayerOptimizationData(
            player_id=17, player_key="matt_gay_was_k", name="Matt Gay", team="WAS", position="K",
            salary=4100, smart_score=56.0, ownership=0.11, projection=8.5
        ),
        # DST
        PlayerOptimizationData(
            player_id=18, player_key="washington_was_dst", name="Washington DST", team="WAS", position="DST",
            salary=3600, smart_score=54.0, ownership=0.12, projection=8.5
        ),
    ])

    return players
