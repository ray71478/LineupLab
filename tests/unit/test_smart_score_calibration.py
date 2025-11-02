"""
Unit tests for Smart Score calibration integration.

Tests ensure Smart Score calculations use calibrated projections when calibration_applied = true,
and fall back to original projections when calibration_applied = false or calibrated values are NULL.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.services.smart_score_service import SmartScoreService, PlayerData
from backend.schemas.smart_score_schemas import WeightProfile, ScoreConfig


@pytest.fixture
def smart_score_service(db_session: Session):
    """Create SmartScoreService instance for testing."""
    return SmartScoreService(db_session)


@pytest.fixture
def default_weights():
    """Default weight profile for testing."""
    return WeightProfile(
        W1=1.0,  # Projection
        W2=0.5,  # Ceiling factor
        W3=0.2,  # Ownership penalty
        W4=0.3,  # Value score
        W5=0.0,  # Trend (skip for simplicity)
        W6=0.0,  # Regression (skip for simplicity)
        W7=0.0,  # Vegas (skip for simplicity)
        W8=0.0,  # Matchup (skip for simplicity)
    )


@pytest.fixture
def default_config():
    """Default score configuration for testing."""
    return ScoreConfig(
        projection_source="ETR",
        eighty_twenty_enabled=False,
        eighty_twenty_threshold=20.0,
    )


def test_smart_score_uses_calibrated_projections_when_active(
    db_session: Session, smart_score_service: SmartScoreService, default_weights, default_config
):
    """Test that Smart Score uses calibrated projections when calibration_applied = true."""
    # Create a week
    db_session.execute(
        text("""
            INSERT INTO weeks (id, season, week_number, status)
            VALUES (100, 2025, 9, 'active')
        """)
    )
    db_session.commit()

    # Insert player with both original and calibrated projections
    db_session.execute(
        text("""
            INSERT INTO player_pools (
                week_id, player_key, name, team, position, salary,
                projection_floor_original, projection_median_original, projection_ceiling_original,
                projection_floor_calibrated, projection_median_calibrated, projection_ceiling_calibrated,
                projection, floor, ceiling,
                calibration_applied, ownership, source, injury_status
            )
            VALUES (
                100, 'test-player-1', 'Test Player', 'KC', 'RB', 7000,
                10.0, 15.0, 25.0,
                11.0, 16.2, 22.5,
                16.2, 11.0, 22.5,
                true, 0.10, 'LineStar', NULL
            )
        """)
    )
    db_session.commit()

    # Calculate Smart Score
    results = smart_score_service.calculate_for_all_players(100, default_weights, default_config)

    # Verify results
    assert len(results) == 1
    player = results[0]
    assert player.name == "Test Player"
    assert player.projection == 16.2  # Should use calibrated median

    # Verify Smart Score calculation used calibrated projections
    # W1 = projection * W1 = 16.2 * 1.0 = 16.2
    # W2 = (ceiling - floor) * W2 = (22.5 - 11.0) * 0.5 = 5.75
    # W3 = -(ownership * W3) = -(10.0 * 0.2) = -2.0
    # W4 = ((projection * 100000) / salary) * W4 = ((16.2 * 100000) / 7000) * 0.3 = 69.43
    # Expected score ≈ 16.2 + 5.75 - 2.0 + 69.43 = 89.38
    expected_score = 16.2 + 5.75 - 2.0 + 69.43
    assert abs(player.smart_score - expected_score) < 0.1


def test_smart_score_uses_original_projections_when_not_calibrated(
    db_session: Session, smart_score_service: SmartScoreService, default_weights, default_config
):
    """Test that Smart Score uses original projections when calibration_applied = false."""
    # Create a week
    db_session.execute(
        text("""
            INSERT INTO weeks (id, season, week_number, status)
            VALUES (101, 2025, 9, 'active')
        """)
    )
    db_session.commit()

    # Insert player with calibration_applied = false
    db_session.execute(
        text("""
            INSERT INTO player_pools (
                week_id, player_key, name, team, position, salary,
                projection_floor_original, projection_median_original, projection_ceiling_original,
                projection_floor_calibrated, projection_median_calibrated, projection_ceiling_calibrated,
                projection, floor, ceiling,
                calibration_applied, ownership, source, injury_status
            )
            VALUES (
                101, 'test-player-2', 'No Calibration Player', 'KC', 'RB', 7000,
                10.0, 15.0, 25.0,
                10.0, 15.0, 25.0,
                15.0, 10.0, 25.0,
                false,0.10, 'LineStar'
            )
        """)
    )
    db_session.commit()

    # Calculate Smart Score
    results = smart_score_service.calculate_for_all_players(101, default_weights, default_config)

    # Verify results
    assert len(results) == 1
    player = results[0]
    assert player.name == "No Calibration Player"
    assert player.projection == 15.0  # Should use original median

    # Verify Smart Score calculation used original projections
    # W1 = projection * W1 = 15.0 * 1.0 = 15.0
    # W2 = (ceiling - floor) * W2 = (25.0 - 10.0) * 0.5 = 7.5
    # W3 = -(ownership * W3) = -(10.0 * 0.2) = -2.0
    # W4 = ((projection * 100000) / salary) * W4 = ((15.0 * 100000) / 7000) * 0.3 = 64.29
    # Expected score ≈ 15.0 + 7.5 - 2.0 + 64.29 = 84.79
    expected_score = 15.0 + 7.5 - 2.0 + 64.29
    assert abs(player.smart_score - expected_score) < 0.1


def test_smart_score_coalesce_fallback_for_null_calibrated_values(
    db_session: Session, smart_score_service: SmartScoreService, default_weights, default_config
):
    """Test that Smart Score falls back to original values when calibrated values are NULL."""
    # Create a week
    db_session.execute(
        text("""
            INSERT INTO weeks (id, season, week_number, status)
            VALUES (102, 2025, 9, 'active')
        """)
    )
    db_session.commit()

    # Insert player with NULL calibrated projections but calibration_applied = true
    db_session.execute(
        text("""
            INSERT INTO player_pools (
                week_id, player_key, name, team, position, salary,
                projection_floor_original, projection_median_original, projection_ceiling_original,
                projection_floor_calibrated, projection_median_calibrated, projection_ceiling_calibrated,
                projection, floor, ceiling,
                calibration_applied, ownership, source, injury_status
            )
            VALUES (
                102, 'test-player-3', 'NULL Calibrated Player', 'KC', 'RB', 7000,
                10.0, 15.0, 25.0,
                NULL, NULL, NULL,
                15.0, 10.0, 25.0,
                true, 0.10, 'LineStar', NULL
            )
        """)
    )
    db_session.commit()

    # Calculate Smart Score
    results = smart_score_service.calculate_for_all_players(102, default_weights, default_config)

    # Verify results - should fall back to original values via COALESCE
    assert len(results) == 1
    player = results[0]
    assert player.name == "NULL Calibrated Player"
    assert player.projection == 15.0  # Should use original median via COALESCE

    # Verify Smart Score calculation used original projections (fallback)
    expected_score = 15.0 + 7.5 - 2.0 + 64.29
    assert abs(player.smart_score - expected_score) < 0.1


def test_smart_score_calculation_accuracy_with_calibrated_data(
    db_session: Session, smart_score_service: SmartScoreService
):
    """Test accuracy of Smart Score calculations with calibrated projections."""
    # Create a week
    db_session.execute(
        text("""
            INSERT INTO weeks (id, season, week_number, status)
            VALUES (103, 2025, 9, 'active')
        """)
    )
    db_session.commit()

    # Insert multiple players with different calibration scenarios
    db_session.execute(
        text("""
            INSERT INTO player_pools (
                week_id, player_key, name, team, position, salary,
                projection_floor_original, projection_median_original, projection_ceiling_original,
                projection_floor_calibrated, projection_median_calibrated, projection_ceiling_calibrated,
                projection, floor, ceiling,
                calibration_applied, ownership, source, injury_status
            )
            VALUES
                (103, 'qb-1', 'QB Calibrated', 'KC', 'QB', 8000, 18.0, 22.0, 30.0, 18.9, 22.0, 28.5, 22.0, 18.9, 28.5, true, 15.0),
                (103, 'rb-1', 'RB Calibrated', 'BUF', 'RB', 7500, 12.0, 16.0, 24.0, 13.2, 17.28, 21.6, 17.28, 13.2, 21.6, true, 12.0),
                (103, 'wr-1', 'WR Not Calibrated', 'MIA', 'WR', 6500, 10.0, 14.0, 22.0, 10.0, 14.0, 22.0, 14.0, 10.0, 22.0, false, 8.0)
        """)
    )
    db_session.commit()

    # Use specific weights for accuracy test
    weights = WeightProfile(
        W1=1.0,  # Projection
        W2=0.5,  # Ceiling factor
        W3=0.2,  # Ownership penalty
        W4=0.3,  # Value score
        W5=0.0,  # Trend
        W6=0.0,  # Regression
        W7=0.0,  # Vegas
        W8=0.0,  # Matchup
    )
    config = ScoreConfig(
        projection_source="ETR",
        eighty_twenty_enabled=False,
        eighty_twenty_threshold=20.0,
    )

    # Calculate Smart Scores
    results = smart_score_service.calculate_for_all_players(103, weights, config)

    # Verify 3 players calculated
    assert len(results) == 3

    # Verify each player's Smart Score uses correct projection values
    qb = next(p for p in results if p.player_key == "qb-1")
    assert qb.projection == 22.0  # Calibrated
    # QB: W1=22.0, W2=(28.5-18.9)*0.5=4.8, W3=-15*0.2=-3.0, W4=(22*100000/8000)*0.3=82.5
    qb_expected = 22.0 + 4.8 - 3.0 + 82.5
    assert abs(qb.smart_score - qb_expected) < 0.2

    rb = next(p for p in results if p.player_key == "rb-1")
    assert rb.projection == 17.28  # Calibrated
    # RB: W1=17.28, W2=(21.6-13.2)*0.5=4.2, W3=-12*0.2=-2.4, W4=(17.28*100000/7500)*0.3=69.12
    rb_expected = 17.28 + 4.2 - 2.4 + 69.12
    assert abs(rb.smart_score - rb_expected) < 0.2

    wr = next(p for p in results if p.player_key == "wr-1")
    assert wr.projection == 14.0  # Not calibrated (original)
    # WR: W1=14.0, W2=(22.0-10.0)*0.5=6.0, W3=-8*0.2=-1.6, W4=(14*100000/6500)*0.3=64.62
    wr_expected = 14.0 + 6.0 - 1.6 + 64.62
    assert abs(wr.smart_score - wr_expected) < 0.2


def test_smart_score_backward_compatibility_with_non_calibrated_pools(
    db_session: Session, smart_score_service: SmartScoreService, default_weights, default_config
):
    """Test backward compatibility: Smart Score works with player pools that have no calibration columns."""
    # Create a week
    db_session.execute(
        text("""
            INSERT INTO weeks (id, season, week_number, status)
            VALUES (104, 2025, 9, 'active')
        """)
    )
    db_session.commit()

    # Insert legacy player with only old columns (simulating pre-calibration data)
    # Note: In reality, migration backfilled these columns, but we test the query behavior
    db_session.execute(
        text("""
            INSERT INTO player_pools (
                week_id, player_key, name, team, position, salary,
                projection, floor, ceiling,
                calibration_applied, ownership, source, injury_status
            )
            VALUES (
                104, 'legacy-player', 'Legacy Player', 'KC', 'RB', 7000,
                15.0, 10.0, 25.0,
                false,0.10, 'LineStar'
            )
        """)
    )
    db_session.commit()

    # Calculate Smart Score - should work without errors
    results = smart_score_service.calculate_for_all_players(104, default_weights, default_config)

    # Verify results
    assert len(results) == 1
    player = results[0]
    assert player.name == "Legacy Player"
    assert player.projection == 15.0

    # Verify Smart Score calculated correctly using legacy columns
    expected_score = 15.0 + 7.5 - 2.0 + 64.29
    assert abs(player.smart_score - expected_score) < 0.1


def test_smart_score_respects_calibration_flag(
    db_session: Session, smart_score_service: SmartScoreService, default_weights, default_config
):
    """Test that Smart Score respects calibration_applied flag for each player independently."""
    # Create a week
    db_session.execute(
        text("""
            INSERT INTO weeks (id, season, week_number, status)
            VALUES (105, 2025, 9, 'active')
        """)
    )
    db_session.commit()

    # Insert mix of calibrated and non-calibrated players
    db_session.execute(
        text("""
            INSERT INTO player_pools (
                week_id, player_key, name, team, position, salary,
                projection_floor_original, projection_median_original, projection_ceiling_original,
                projection_floor_calibrated, projection_median_calibrated, projection_ceiling_calibrated,
                projection, floor, ceiling,
                calibration_applied, ownership, source, injury_status
            )
            VALUES
                (105, 'player-cal-1', 'Calibrated 1', 'KC', 'RB', 7000, 10.0, 15.0, 25.0, 11.0, 16.2, 22.5, 16.2, 11.0, 22.5, true,0.10, 'LineStar'),
                (105, 'player-no-cal-1', 'Not Calibrated 1', 'BUF', 'RB', 7000, 10.0, 15.0, 25.0, 10.0, 15.0, 25.0, 15.0, 10.0, 25.0, false,0.10, 'LineStar'),
                (105, 'player-cal-2', 'Calibrated 2', 'MIA', 'WR', 6500, 9.0, 13.0, 20.0, 9.72, 13.65, 17.6, 13.65, 9.72, 17.6, true,0.08, 'LineStar')
        """)
    )
    db_session.commit()

    # Calculate Smart Scores
    results = smart_score_service.calculate_for_all_players(105, default_weights, default_config)

    # Verify 3 players
    assert len(results) == 3

    # Verify calibrated players use calibrated values
    cal_1 = next(p for p in results if p.player_key == "player-cal-1")
    assert cal_1.projection == 16.2

    cal_2 = next(p for p in results if p.player_key == "player-cal-2")
    assert cal_2.projection == 13.65

    # Verify non-calibrated player uses original values
    no_cal = next(p for p in results if p.player_key == "player-no-cal-1")
    assert no_cal.projection == 15.0


def test_smart_score_ceiling_floor_factor_with_calibrated_values(
    db_session: Session, smart_score_service: SmartScoreService
):
    """Test that W2 (ceiling factor) correctly uses calibrated ceiling and floor values."""
    # Create a week
    db_session.execute(
        text("""
            INSERT INTO weeks (id, season, week_number, status)
            VALUES (106, 2025, 9, 'active')
        """)
    )
    db_session.commit()

    # Insert player with significant difference between original and calibrated ranges
    db_session.execute(
        text("""
            INSERT INTO player_pools (
                week_id, player_key, name, team, position, salary,
                projection_floor_original, projection_median_original, projection_ceiling_original,
                projection_floor_calibrated, projection_median_calibrated, projection_ceiling_calibrated,
                projection, floor, ceiling,
                calibration_applied, ownership, source, injury_status
            )
            VALUES (
                106, 'range-test', 'Range Test Player', 'KC', 'RB', 7000,
                8.0, 15.0, 28.0,
                8.8, 16.2, 25.2,
                16.2, 8.8, 25.2,
                true, 0.10, 'LineStar', NULL
            )
        """)
    )
    db_session.commit()

    # Calculate with high W2 weight to emphasize ceiling factor
    weights = WeightProfile(
        W1=1.0,
        W2=1.0,  # High weight for ceiling factor
        W3=0.0,
        W4=0.0,
        W5=0.0,
        W6=0.0,
        W7=0.0,
        W8=0.0,
    )
    config = ScoreConfig(
        projection_source="ETR",
        eighty_twenty_enabled=False,
        eighty_twenty_threshold=20.0,
    )

    results = smart_score_service.calculate_for_all_players(106, weights, config)

    # Verify results
    assert len(results) == 1
    player = results[0]

    # W1 = 16.2 * 1.0 = 16.2
    # W2 = (25.2 - 8.8) * 1.0 = 16.4 (uses calibrated ceiling and floor)
    # Expected score = 16.2 + 16.4 = 32.6
    expected_score = 16.2 + 16.4
    assert abs(player.smart_score - expected_score) < 0.1

    # Verify score breakdown shows correct W2 value
    assert player.score_breakdown is not None
    assert abs(player.score_breakdown.W2_value - 16.4) < 0.1
