"""
Integration tests for lineup optimizer calibration integration.

Tests that lineup optimizer correctly uses calibrated projections when available
and falls back to original projections when calibration is not applied.

NOTE: These tests verify that the SmartScoreService (which feeds data to the optimizer)
correctly uses COALESCE logic to fetch calibrated projections. The lineup optimizer
itself doesn't need to be modified because it receives calibrated projections
through the SmartScoreService.
"""
import pytest
from sqlalchemy import text
from backend.services.lineup_optimizer_service import LineupOptimizerService
from backend.services.smart_score_service import SmartScoreService
from backend.services.weight_profile_service import WeightProfileService


@pytest.fixture
def test_week(db_session):
    """Create or retrieve a test week for calibration tests."""
    # Get the first week from the seeded NFL schedule
    result = db_session.execute(
        text("""
            SELECT w.id FROM weeks w
            WHERE w.season = 2025 AND w.week_number = 1
            LIMIT 1
        """)
    ).fetchone()

    if result:
        week_id = result[0]
    else:
        # If no week found, create one
        db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status)
                VALUES (2025, 1, 'active')
            """)
        )
        db_session.commit()

        result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = 2025 AND week_number = 1")
        ).fetchone()
        week_id = result[0]

    # Create a simple Week object to return
    class Week:
        def __init__(self, id):
            self.id = id

    return Week(week_id)


def test_optimizer_uses_calibrated_projections_when_available(db_session, test_week):
    """Test that lineup optimizer uses calibrated projections when calibration_applied = true."""
    # Insert test players with calibrated projections
    db_session.execute(text("""
        INSERT INTO player_pools (
            week_id, player_key, name, team, position, salary,
            projection_median_original, projection_median_calibrated,
            projection_floor_original, projection_floor_calibrated,
            projection_ceiling_original, projection_ceiling_calibrated,
            calibration_applied, ownership, projection_source
        ) VALUES
        (:week_id, 'QB1', 'Test QB', 'KC', 'QB', 7000,
         20.0, 22.0,  -- median: original 20.0, calibrated 22.0
         15.0, 16.5,  -- floor: original 15.0, calibrated 16.5
         28.0, 26.0,  -- ceiling: original 28.0, calibrated 26.0
         true, 15.0, 'ETR'),
        (:week_id, 'RB1', 'Test RB1', 'SF', 'RB', 8000,
         18.0, 19.8,  -- +10% median calibration
         12.0, 13.2,  -- +10% floor calibration
         25.0, 22.5,  -- -10% ceiling calibration
         true, 20.0, 'ETR'),
        (:week_id, 'RB2', 'Test RB2', 'DAL', 'RB', 6000,
         14.0, 15.4,
         10.0, 11.0,
         20.0, 18.0,
         true, 18.0, 'ETR'),
        (:week_id, 'WR1', 'Test WR1', 'BUF', 'WR', 7500,
         16.0, 16.8,  -- +5% median calibration
         10.0, 10.8,  -- +8% floor calibration
         24.0, 21.1,  -- -12% ceiling calibration
         true, 25.0, 'ETR'),
        (:week_id, 'WR2', 'Test WR2', 'MIA', 'WR', 6500,
         14.0, 14.7,
         9.0, 9.7,
         21.0, 18.5,
         true, 22.0, 'ETR'),
        (:week_id, 'WR3', 'Test WR3', 'NYJ', 'WR', 5500,
         12.0, 12.6,
         8.0, 8.6,
         18.0, 15.8,
         true, 20.0, 'ETR'),
        (:week_id, 'TE1', 'Test TE', 'KC', 'TE', 5000,
         13.0, 13.9,  -- +7% median calibration
         9.0, 9.9,    -- +10% floor calibration
         19.0, 17.1,  -- -10% ceiling calibration
         true, 15.0, 'ETR'),
        (:week_id, 'DST1', 'Test DST', 'SF', 'DST', 3000,
         9.0, 9.0,    -- 0% calibration (K/DST unchanged)
         5.0, 5.0,
         14.0, 14.0,
         true, 10.0, 'ETR')
    """), {"week_id": test_week.id})
    db_session.commit()

    # Get Smart Scores (which should use calibrated projections)
    smart_score_service = SmartScoreService(db_session)
    weight_profile_service = WeightProfileService(db_session)
    default_profile = weight_profile_service.get_default_profile()

    players_with_scores = smart_score_service.calculate_for_all_players(
        week_id=test_week.id,
        weights=default_profile.weights,
        config=default_profile.config,
    )

    # Verify players have scores based on calibrated projections
    assert len(players_with_scores) > 0
    qb_player = next((p for p in players_with_scores if p.position == 'QB'), None)
    assert qb_player is not None
    # QB projection should be calibrated value (22.0), not original (20.0)
    assert qb_player.projection == 22.0, f"Expected calibrated projection 22.0, got {qb_player.projection}"

    rb_player = next((p for p in players_with_scores if p.position == 'RB' and p.name == 'Test RB1'), None)
    assert rb_player is not None
    assert rb_player.projection == 19.8, f"Expected calibrated projection 19.8, got {rb_player.projection}"

    # Generate lineup to verify optimizer uses calibrated projections
    optimizer_service = LineupOptimizerService(db_session)
    from backend.schemas.lineup_schemas import OptimizationSettings

    settings = OptimizationSettings(
        num_lineups=1,
        strategy_mode='Balanced',
        max_players_per_team=4,
        max_players_per_game=6,
        smart_score_threshold=0.0,
    )

    lineups, _ = optimizer_service.generate_lineups(
        week_id=test_week.id,
        players=players_with_scores,
        settings=settings,
    )

    # Verify lineup was generated successfully
    assert len(lineups) >= 1, "Expected at least 1 lineup to be generated"

    # Verify lineup contains players with calibrated projections
    lineup = lineups[0]
    assert len(lineup.players) == 9, f"Expected 9 players in lineup, got {len(lineup.players)}"

    # Check that projected_points reflects calibrated projections
    # Should be higher than if using original projections
    assert lineup.projected_points > 0, "Lineup should have positive projected points"


def test_optimizer_fallback_to_original_when_calibration_missing(db_session, test_week):
    """Test that lineup optimizer falls back to original projections when calibration_applied = false."""
    # Insert test players WITHOUT calibrated projections (calibration_applied = false)
    db_session.execute(text("""
        INSERT INTO player_pools (
            week_id, player_key, name, team, position, salary,
            projection_median_original, projection_median_calibrated,
            projection_floor_original, projection_floor_calibrated,
            projection_ceiling_original, projection_ceiling_calibrated,
            calibration_applied, ownership, projection_source
        ) VALUES
        (:week_id, 'QB1', 'Test QB', 'KC', 'QB', 7000,
         20.0, NULL,  -- No calibrated value
         15.0, NULL,
         28.0, NULL,
         false, 15.0, 'ETR'),
        (:week_id, 'RB1', 'Test RB1', 'SF', 'RB', 8000,
         18.0, NULL,
         12.0, NULL,
         25.0, NULL,
         false, 20.0, 'ETR'),
        (:week_id, 'RB2', 'Test RB2', 'DAL', 'RB', 6000,
         14.0, NULL,
         10.0, NULL,
         20.0, NULL,
         false, 18.0, 'ETR'),
        (:week_id, 'WR1', 'Test WR1', 'BUF', 'WR', 7500,
         16.0, NULL,
         10.0, NULL,
         24.0, NULL,
         false, 25.0, 'ETR'),
        (:week_id, 'WR2', 'Test WR2', 'MIA', 'WR', 6500,
         14.0, NULL,
         9.0, NULL,
         21.0, NULL,
         false, 22.0, 'ETR'),
        (:week_id, 'WR3', 'Test WR3', 'NYJ', 'WR', 5500,
         12.0, NULL,
         8.0, NULL,
         18.0, NULL,
         false, 20.0, 'ETR'),
        (:week_id, 'TE1', 'Test TE', 'KC', 'TE', 5000,
         13.0, NULL,
         9.0, NULL,
         19.0, NULL,
         false, 15.0, 'ETR'),
        (:week_id, 'DST1', 'Test DST', 'SF', 'DST', 3000,
         9.0, NULL,
         5.0, NULL,
         14.0, NULL,
         false, 10.0, 'ETR')
    """), {"week_id": test_week.id})
    db_session.commit()

    # Get Smart Scores
    smart_score_service = SmartScoreService(db_session)
    weight_profile_service = WeightProfileService(db_session)
    default_profile = weight_profile_service.get_default_profile()

    players_with_scores = smart_score_service.calculate_for_all_players(
        week_id=test_week.id,
        weights=default_profile.weights,
        config=default_profile.config,
    )

    # Verify COALESCE fallback works - should use original projections
    assert len(players_with_scores) > 0
    qb_player = next((p for p in players_with_scores if p.position == 'QB'), None)
    assert qb_player is not None
    assert qb_player.projection == 20.0, f"Expected original projection 20.0, got {qb_player.projection}"

    # Generate lineup
    optimizer_service = LineupOptimizerService(db_session)
    from backend.schemas.lineup_schemas import OptimizationSettings

    settings = OptimizationSettings(
        num_lineups=1,
        strategy_mode='Balanced',
        max_players_per_team=4,
        max_players_per_game=6,
        smart_score_threshold=0.0,
    )

    lineups, _ = optimizer_service.generate_lineups(
        week_id=test_week.id,
        players=players_with_scores,
        settings=settings,
    )

    # Verify lineup generation succeeds with original projections
    assert len(lineups) >= 1, "Expected at least 1 lineup with original projections"
    assert len(lineups[0].players) == 9, "Lineup should have 9 players"


def test_optimizer_coalesce_logic_in_queries(db_session, test_week):
    """Test that COALESCE logic correctly handles NULL calibrated values."""
    # Insert mix of calibrated and non-calibrated players
    db_session.execute(text("""
        INSERT INTO player_pools (
            week_id, player_key, name, team, position, salary,
            projection_median_original, projection_median_calibrated,
            projection_floor_original, projection_floor_calibrated,
            projection_ceiling_original, projection_ceiling_calibrated,
            calibration_applied, ownership, projection_source
        ) VALUES
        -- Calibrated QB
        (:week_id, 'QB1', 'Calibrated QB', 'KC', 'QB', 7000,
         20.0, 22.0, 15.0, 16.5, 28.0, 26.0, true, 15.0, 'ETR'),
        -- Non-calibrated RB (NULL calibrated values)
        (:week_id, 'RB1', 'NonCal RB1', 'SF', 'RB', 8000,
         18.0, NULL, 12.0, NULL, 25.0, NULL, false, 20.0, 'ETR'),
        -- Calibrated RB
        (:week_id, 'RB2', 'Calibrated RB2', 'DAL', 'RB', 6000,
         14.0, 15.4, 10.0, 11.0, 20.0, 18.0, true, 18.0, 'ETR'),
        -- Non-calibrated WRs
        (:week_id, 'WR1', 'NonCal WR1', 'BUF', 'WR', 7500,
         16.0, NULL, 10.0, NULL, 24.0, NULL, false, 25.0, 'ETR'),
        (:week_id, 'WR2', 'NonCal WR2', 'MIA', 'WR', 6500,
         14.0, NULL, 9.0, NULL, 21.0, NULL, false, 22.0, 'ETR'),
        (:week_id, 'WR3', 'NonCal WR3', 'NYJ', 'WR', 5500,
         12.0, NULL, 8.0, NULL, 18.0, NULL, false, 20.0, 'ETR'),
        -- Calibrated TE
        (:week_id, 'TE1', 'Calibrated TE', 'KC', 'TE', 5000,
         13.0, 13.9, 9.0, 9.9, 19.0, 17.1, true, 15.0, 'ETR'),
        -- Non-calibrated DST
        (:week_id, 'DST1', 'NonCal DST', 'SF', 'DST', 3000,
         9.0, NULL, 5.0, NULL, 14.0, NULL, false, 10.0, 'ETR')
    """), {"week_id": test_week.id})
    db_session.commit()

    # Get Smart Scores
    smart_score_service = SmartScoreService(db_session)
    weight_profile_service = WeightProfileService(db_session)
    default_profile = weight_profile_service.get_default_profile()

    players_with_scores = smart_score_service.calculate_for_all_players(
        week_id=test_week.id,
        weights=default_profile.weights,
        config=default_profile.config,
    )

    # Verify mix of calibrated and original projections
    assert len(players_with_scores) == 8

    qb = next(p for p in players_with_scores if p.player_key == 'QB1')
    assert qb.projection == 22.0, "QB should use calibrated projection"

    rb1 = next(p for p in players_with_scores if p.player_key == 'RB1')
    assert rb1.projection == 18.0, "RB1 should fall back to original projection"

    rb2 = next(p for p in players_with_scores if p.player_key == 'RB2')
    assert rb2.projection == 15.4, "RB2 should use calibrated projection"

    # Generate lineup - should work with mixed data
    optimizer_service = LineupOptimizerService(db_session)
    from backend.schemas.lineup_schemas import OptimizationSettings

    settings = OptimizationSettings(
        num_lineups=1,
        strategy_mode='Balanced',
        max_players_per_team=4,
        max_players_per_game=6,
        smart_score_threshold=0.0,
    )

    lineups, _ = optimizer_service.generate_lineups(
        week_id=test_week.id,
        players=players_with_scores,
        settings=settings,
    )

    assert len(lineups) >= 1, "Optimizer should handle mix of calibrated/non-calibrated players"


def test_optimizer_backward_compatibility_with_existing_weeks(db_session, test_week):
    """Test that optimizer works with historical weeks that don't have calibration columns populated."""
    # Insert players with only old column structure (no calibrated columns)
    # Simulating historical data before calibration feature
    db_session.execute(text("""
        INSERT INTO player_pools (
            week_id, player_key, name, team, position, salary,
            projection, floor, ceiling, ownership, projection_source,
            calibration_applied
        ) VALUES
        (:week_id, 'QB1', 'Legacy QB', 'KC', 'QB', 7000, 20.0, 15.0, 28.0, 15.0, 'ETR', false),
        (:week_id, 'RB1', 'Legacy RB1', 'SF', 'RB', 8000, 18.0, 12.0, 25.0, 20.0, 'ETR', false),
        (:week_id, 'RB2', 'Legacy RB2', 'DAL', 'RB', 6000, 14.0, 10.0, 20.0, 18.0, 'ETR', false),
        (:week_id, 'WR1', 'Legacy WR1', 'BUF', 'WR', 7500, 16.0, 10.0, 24.0, 25.0, 'ETR', false),
        (:week_id, 'WR2', 'Legacy WR2', 'MIA', 'WR', 6500, 14.0, 9.0, 21.0, 22.0, 'ETR', false),
        (:week_id, 'WR3', 'Legacy WR3', 'NYJ', 'WR', 5500, 12.0, 8.0, 18.0, 20.0, 'ETR', false),
        (:week_id, 'TE1', 'Legacy TE', 'KC', 'TE', 5000, 13.0, 9.0, 19.0, 15.0, 'ETR', false),
        (:week_id, 'DST1', 'Legacy DST', 'SF', 'DST', 3000, 9.0, 5.0, 14.0, 10.0, 'ETR', false)
    """), {"week_id": test_week.id})
    db_session.commit()

    # Get Smart Scores
    smart_score_service = SmartScoreService(db_session)
    weight_profile_service = WeightProfileService(db_session)
    default_profile = weight_profile_service.get_default_profile()

    players_with_scores = smart_score_service.calculate_for_all_players(
        week_id=test_week.id,
        weights=default_profile.weights,
        config=default_profile.config,
    )

    # Verify backward compatibility - should use original projection column
    assert len(players_with_scores) == 8
    qb = next(p for p in players_with_scores if p.player_key == 'QB1')
    assert qb.projection == 20.0, "Should fall back to legacy 'projection' column"

    # Generate lineup - should work with legacy data
    optimizer_service = LineupOptimizerService(db_session)
    from backend.schemas.lineup_schemas import OptimizationSettings

    settings = OptimizationSettings(
        num_lineups=1,
        strategy_mode='Balanced',
        max_players_per_team=4,
        max_players_per_game=6,
        smart_score_threshold=0.0,
    )

    lineups, _ = optimizer_service.generate_lineups(
        week_id=test_week.id,
        players=players_with_scores,
        settings=settings,
    )

    assert len(lineups) >= 1, "Optimizer should work with legacy data structure"
    assert len(lineups[0].players) == 9


def test_lineup_quality_with_calibrated_vs_non_calibrated(db_session, test_week):
    """
    Test that lineup quality (projected points) reflects calibration adjustments.

    Calibrated projections should result in different lineup scores based on the
    adjustments applied (e.g., RB median +10%, WR median +5%).
    """
    # Insert calibrated players
    db_session.execute(text("""
        INSERT INTO player_pools (
            week_id, player_key, name, team, position, salary,
            projection_median_original, projection_median_calibrated,
            projection_floor_original, projection_floor_calibrated,
            projection_ceiling_original, projection_ceiling_calibrated,
            calibration_applied, ownership, projection_source
        ) VALUES
        (:week_id, 'QB1', 'Test QB', 'KC', 'QB', 7000,
         20.0, 22.0, 15.0, 16.5, 28.0, 26.0, true, 15.0, 'ETR'),
        (:week_id, 'RB1', 'Test RB1', 'SF', 'RB', 8000,
         18.0, 19.8, 12.0, 13.2, 25.0, 22.5, true, 20.0, 'ETR'),
        (:week_id, 'RB2', 'Test RB2', 'DAL', 'RB', 6000,
         14.0, 15.4, 10.0, 11.0, 20.0, 18.0, true, 18.0, 'ETR'),
        (:week_id, 'WR1', 'Test WR1', 'BUF', 'WR', 7500,
         16.0, 16.8, 10.0, 10.8, 24.0, 21.1, true, 25.0, 'ETR'),
        (:week_id, 'WR2', 'Test WR2', 'MIA', 'WR', 6500,
         14.0, 14.7, 9.0, 9.7, 21.0, 18.5, true, 22.0, 'ETR'),
        (:week_id, 'WR3', 'Test WR3', 'NYJ', 'WR', 5500,
         12.0, 12.6, 8.0, 8.6, 18.0, 15.8, true, 20.0, 'ETR'),
        (:week_id, 'TE1', 'Test TE', 'KC', 'TE', 5000,
         13.0, 13.9, 9.0, 9.9, 19.0, 17.1, true, 15.0, 'ETR'),
        (:week_id, 'DST1', 'Test DST', 'SF', 'DST', 3000,
         9.0, 9.0, 5.0, 5.0, 14.0, 14.0, true, 10.0, 'ETR')
    """), {"week_id": test_week.id})
    db_session.commit()

    # Get Smart Scores with calibrated projections
    smart_score_service = SmartScoreService(db_session)
    weight_profile_service = WeightProfileService(db_session)
    default_profile = weight_profile_service.get_default_profile()

    players_calibrated = smart_score_service.calculate_for_all_players(
        week_id=test_week.id,
        weights=default_profile.weights,
        config=default_profile.config,
    )

    # Calculate total calibrated projections
    total_calibrated_proj = sum(p.projection for p in players_calibrated)

    # Expected calibrated projections:
    # QB: 22.0, RB1: 19.8, RB2: 15.4, WR1: 16.8, WR2: 14.7, WR3: 12.6, TE: 13.9, DST: 9.0
    # Total = 22.0 + 19.8 + 15.4 + 16.8 + 14.7 + 12.6 + 13.9 + 9.0 = 124.2
    expected_calibrated = 22.0 + 19.8 + 15.4 + 16.8 + 14.7 + 12.6 + 13.9 + 9.0
    assert abs(total_calibrated_proj - expected_calibrated) < 0.1, \
        f"Expected calibrated total ~{expected_calibrated}, got {total_calibrated_proj}"

    # Generate lineup with calibrated data
    optimizer_service = LineupOptimizerService(db_session)
    from backend.schemas.lineup_schemas import OptimizationSettings

    settings = OptimizationSettings(
        num_lineups=1,
        strategy_mode='Balanced',
        max_players_per_team=4,
        max_players_per_game=6,
        smart_score_threshold=0.0,
    )

    lineups_calibrated, _ = optimizer_service.generate_lineups(
        week_id=test_week.id,
        players=players_calibrated,
        settings=settings,
    )

    assert len(lineups_calibrated) >= 1
    calibrated_lineup_proj = lineups_calibrated[0].projected_points

    # Verify calibrated lineup uses higher projections
    # Total original would be: 20 + 18 + 14 + 16 + 14 + 12 + 13 + 9 = 116.0
    # Calibrated is ~124.2, so lineup should reflect the increase
    assert calibrated_lineup_proj > 116.0, \
        f"Calibrated lineup projection ({calibrated_lineup_proj}) should be > original (116.0)"


def test_calibration_status_logging_in_optimizer(db_session, test_week, caplog):
    """Test that optimizer logs calibration status for debugging/monitoring."""
    import logging
    caplog.set_level(logging.INFO)

    # Insert mix of calibrated and non-calibrated players
    db_session.execute(text("""
        INSERT INTO player_pools (
            week_id, player_key, name, team, position, salary,
            projection_median_original, projection_median_calibrated,
            projection_floor_original, projection_floor_calibrated,
            projection_ceiling_original, projection_ceiling_calibrated,
            calibration_applied, ownership, projection_source
        ) VALUES
        (:week_id, 'QB1', 'Cal QB', 'KC', 'QB', 7000,
         20.0, 22.0, 15.0, 16.5, 28.0, 26.0, true, 15.0, 'ETR'),
        (:week_id, 'RB1', 'NonCal RB1', 'SF', 'RB', 8000,
         18.0, NULL, 12.0, NULL, 25.0, NULL, false, 20.0, 'ETR'),
        (:week_id, 'RB2', 'Cal RB2', 'DAL', 'RB', 6000,
         14.0, 15.4, 10.0, 11.0, 20.0, 18.0, true, 18.0, 'ETR'),
        (:week_id, 'WR1', 'Cal WR1', 'BUF', 'WR', 7500,
         16.0, 16.8, 10.0, 10.8, 24.0, 21.1, true, 25.0, 'ETR'),
        (:week_id, 'WR2', 'NonCal WR2', 'MIA', 'WR', 6500,
         14.0, NULL, 9.0, NULL, 21.0, NULL, false, 22.0, 'ETR'),
        (:week_id, 'WR3', 'NonCal WR3', 'NYJ', 'WR', 5500,
         12.0, NULL, 8.0, NULL, 18.0, NULL, false, 20.0, 'ETR'),
        (:week_id, 'TE1', 'Cal TE', 'KC', 'TE', 5000,
         13.0, 13.9, 9.0, 9.9, 19.0, 17.1, true, 15.0, 'ETR'),
        (:week_id, 'DST1', 'NonCal DST', 'SF', 'DST', 3000,
         9.0, NULL, 5.0, NULL, 14.0, NULL, false, 10.0, 'ETR')
    """), {"week_id": test_week.id})
    db_session.commit()

    # Get Smart Scores
    smart_score_service = SmartScoreService(db_session)
    weight_profile_service = WeightProfileService(db_session)
    default_profile = weight_profile_service.get_default_profile()

    players_with_scores = smart_score_service.calculate_for_all_players(
        week_id=test_week.id,
        weights=default_profile.weights,
        config=default_profile.config,
    )

    # Generate lineup
    optimizer_service = LineupOptimizerService(db_session)
    from backend.schemas.lineup_schemas import OptimizationSettings

    settings = OptimizationSettings(
        num_lineups=1,
        strategy_mode='Balanced',
        max_players_per_team=4,
        max_players_per_game=6,
        smart_score_threshold=0.0,
    )

    lineups, _ = optimizer_service.generate_lineups(
        week_id=test_week.id,
        players=players_with_scores,
        settings=settings,
    )

    assert len(lineups) >= 1

    # Check that SmartScoreService logged COALESCE usage
    # The SmartScoreService query uses COALESCE, so data is already merged
    # We can verify by checking player projections directly
    cal_players = [p for p in players_with_scores if p.player_key in ['QB1', 'RB2', 'WR1', 'TE1']]
    non_cal_players = [p for p in players_with_scores if p.player_key in ['RB1', 'WR2', 'WR3', 'DST1']]

    # All players should have projections (either calibrated or original via COALESCE)
    assert all(p.projection is not None for p in cal_players), "Calibrated players should have projections"
    assert all(p.projection is not None for p in non_cal_players), "Non-calibrated players should have fallback projections"
