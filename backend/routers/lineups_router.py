"""
Lineup Optimizer API endpoints for generating and managing optimized lineups.

Provides REST API endpoints for:
- Generating optimized lineups
- Saving selected lineups to database
- Retrieving saved lineups
"""
import logging
import time
import json
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.services.lineup_optimizer_service import LineupOptimizerService
from backend.services.smart_score_service import SmartScoreService
from backend.services.weight_profile_service import WeightProfileService
from backend.schemas.lineup_schemas import (
    LineupOptimizationRequest,
    LineupOptimizationResponse,
    SaveLineupsRequest,
    SaveLineupsResponse,
    SavedLineup,
    OptimizationSettings,
)
from backend.schemas.smart_score_schemas import WeightProfile, ScoreConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/lineups", tags=["lineups"])

# Placeholder - will be overridden by main.py
get_db = None


def _get_current_db_dependency():
    """Get the current database dependency function."""
    import sys
    current_module = sys.modules[__name__]
    if current_module.get_db is None:
        raise RuntimeError("get_db not initialized. Make sure main.py has set up the dependency.")
    yield from current_module.get_db()


@router.post("/generate", response_model=LineupOptimizationResponse)
async def generate_lineups(
    request: LineupOptimizationRequest,
    db: Any = Depends(_get_current_db_dependency),
) -> LineupOptimizationResponse:
    """
    Generate optimized lineups for a week.
    
    Requires Smart Scores to be calculated first. Will use default weight profile
    if no weights are provided in request.
    
    Args:
        request: LineupOptimizationRequest with week_id and settings
        db: Database session
    
    Returns:
        LineupOptimizationResponse with generated lineups
    """
    start_time = time.time()
    
    try:
        # Get Smart Scores for players
        smart_score_service = SmartScoreService(db)
        weight_profile_service = WeightProfileService(db)
        
        # Use provided weights/config if available, otherwise use default profile
        if request.weights is not None and request.config is not None:
            # Use customized weights/config from frontend
            weights = request.weights
            config = request.config
            logger.info("Using custom weights/config from request for Smart Score calculation")
        else:
            # Fall back to default profile if no custom weights provided
            default_profile = weight_profile_service.get_default_profile()
            weights = default_profile.weights  # Already a WeightProfile object
            config = default_profile.config  # Already a ScoreConfig object
            logger.info("Using default weight profile for Smart Score calculation")
        
        # Calculate Smart Scores with the selected weights/config
        players_with_scores = smart_score_service.calculate_for_all_players(
            week_id=request.week_id,
            weights=weights,
            config=config,
        )
        
        if not players_with_scores:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No players with Smart Scores found for week {request.week_id}",
            )
        
        # Filter by selected player IDs if provided
        if request.selected_player_ids is not None and len(request.selected_player_ids) > 0:
            selected_ids_set = set(request.selected_player_ids)

            logger.info(
                f"Filtering to {len(selected_ids_set)} selected player IDs from {len(players_with_scores)} total players"
            )

            before_count = len(players_with_scores)
            players_with_scores = [
                p for p in players_with_scores
                if p.player_id in selected_ids_set
            ]

            if not players_with_scores:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"No matching players found for selected player IDs",
                )

            logger.info(
                f"Filtered {before_count} → {len(players_with_scores)} players "
                f"({len(selected_ids_set) - len(players_with_scores)} selected IDs not found in player pool)"
            )

            # Log position breakdown and score distribution after filtering
            pos_counts = {}
            score_ranges = {'0.0': 0, '0.1-5.0': 0, '5.1-10.0': 0, '10.1-20.0': 0, '20.1-30.0': 0, '30+': 0}
            for p in players_with_scores:
                pos_counts[p.position] = pos_counts.get(p.position, 0) + 1
                # Track score distribution
                if p.smart_score == 0.0:
                    score_ranges['0.0'] += 1
                elif p.smart_score <= 5.0:
                    score_ranges['0.1-5.0'] += 1
                elif p.smart_score <= 10.0:
                    score_ranges['5.1-10.0'] += 1
                elif p.smart_score <= 20.0:
                    score_ranges['10.1-20.0'] += 1
                elif p.smart_score <= 30.0:
                    score_ranges['20.1-30.0'] += 1
                else:
                    score_ranges['30+'] += 1
            
            logger.info(f"Position breakdown after filter: {pos_counts}")
            logger.info(f"Smart Score distribution: {score_ranges}")
            logger.info(f"Players with score 0.0: {score_ranges['0.0']} (these will be filtered out by optimizer)")
        
        # Generate lineups
        optimizer_service = LineupOptimizerService(db)
        
        logger.info(
            f"Attempting to generate {request.settings.num_lineups} lineups "
            f"from {len(players_with_scores)} players for week {request.week_id}"
        )
        
        generated_lineups, position_counts = optimizer_service.generate_lineups(
            week_id=request.week_id,
            players=players_with_scores,
            settings=request.settings,
        )
        
        # If we got some lineups but not all requested, log a warning but return success
        if generated_lineups and len(generated_lineups) < request.settings.num_lineups:
            logger.warning(
                f"Generated {len(generated_lineups)} lineups out of {request.settings.num_lineups} requested. "
                f"Some lineups may have failed due to constraint conflicts."
            )
        
        # Only raise error if NO lineups were generated
        if not generated_lineups:
            # Use position counts from optimizer if available (after filtering)
            if position_counts:
                position_detail = ", ".join([f"{pos}: {count}" for pos, count in sorted(position_counts.items())])
                
                # Check if we have enough players at each position
                required_positions = {'QB': 1, 'RB': 2, 'WR': 3, 'TE': 1, 'DST': 1}
                has_enough_players = all(
                    position_counts.get(pos, 0) >= min_count 
                    for pos, min_count in required_positions.items()
                )
                
                if has_enough_players:
                    # Enough players but solver failed - constraints likely too restrictive
                    threshold_info = f" (Smart Score threshold: {request.settings.smart_score_threshold})" if request.settings.smart_score_threshold else ""
                    error_msg = (
                        f"Failed to generate lineups. Optimization solver could not find a feasible solution. "
                        f"Available players: {position_detail}. "
                        f"Required: QB: 1, RB: 2, WR: 3, TE: 1, DST: 1.{threshold_info} "
                        f"Try relaxing constraints (stacking rules, max players per team/game) or reducing Smart Score threshold."
                    )
                else:
                    # Not enough players at required positions
                    threshold_info = f" (Smart Score threshold: {request.settings.smart_score_threshold})" if request.settings.smart_score_threshold else ""
                    error_msg = (
                        f"Failed to generate lineups. Not enough players at required positions after filtering{threshold_info}. "
                        f"Available (after Smart Score threshold): {position_detail}. "
                        f"Required: QB: 1, RB: 2, WR: 3, TE: 1, DST: 1. "
                        f"Try reducing Smart Score threshold or selecting more players."
                    )
            else:
                # Fallback to counting before filtering
                position_counts = {}
                for player in players_with_scores:
                    pos = player.position
                    position_counts[pos] = position_counts.get(pos, 0) + 1
                position_detail = ", ".join([f"{pos}: {count}" for pos, count in sorted(position_counts.items())])
                error_msg = (
                    f"Failed to generate lineups. Not enough players at required positions. "
                    f"Available: {position_detail}. "
                    f"Required: QB: 1, RB: 2, WR: 3, TE: 1, DST: 1. "
                    f"Try reducing Smart Score threshold or selecting more players."
                )
            
            logger.error(
                f"Lineup generation returned empty list. "
                f"Players: {len(players_with_scores)}, "
                f"Settings: {request.settings}, "
                f"Position counts: {position_counts}"
            )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )
        
        generation_time_ms = (time.time() - start_time) * 1000
        
        requested_count = request.settings.num_lineups
        generated_count = len(generated_lineups)
        
        if generated_count < requested_count:
            logger.info(
                f"Generated {generated_count} lineups out of {requested_count} requested "
                f"for week {request.week_id} in {generation_time_ms:.2f}ms"
            )
        else:
            logger.info(
                f"Generated {generated_count} lineups for week {request.week_id} in {generation_time_ms:.2f}ms"
            )
        
        # Log lineup details
        baseline_count = sum(1 for l in generated_lineups if l.lineup_number < 0)
        regular_count = sum(1 for l in generated_lineups if l.lineup_number > 0)
        logger.info(f"Returning {len(generated_lineups)} total lineups: {baseline_count} baselines + {regular_count} regular")
        
        # Log each lineup number for debugging
        lineup_numbers = [l.lineup_number for l in generated_lineups]
        logger.info(f"Lineup numbers being returned: {lineup_numbers}")
        
        return LineupOptimizationResponse(
            week_id=request.week_id,
            lineups=generated_lineups,
            settings=request.settings,
            generation_time_ms=generation_time_ms,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error generating lineups: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate lineups: {str(e)}",
        )


@router.post("/save", response_model=SaveLineupsResponse)
async def save_lineups(
    request: SaveLineupsRequest,
    db: Any = Depends(_get_current_db_dependency),
) -> SaveLineupsResponse:
    """
    Save selected lineups to database.
    
    This endpoint expects lineups to be passed in the request body.
    The lineups should have been generated previously via /generate endpoint.
    
    Args:
        request: SaveLineupsRequest with week_id, lineup_numbers, and lineups data
        db: Database session
    
    Returns:
        SaveLineupsResponse with saved lineups
    """
    try:
        saved_lineups = []
        
        # Get strategy mode from settings (passed in request)
        strategy_mode = request.strategy_mode or 'Balanced'
        
        # Insert each lineup
        for lineup_data in request.lineups:
            query = text("""
                INSERT INTO generated_lineups (
                    week_id,
                    lineup_number,
                    players,
                    total_salary,
                    projected_score,
                    avg_ownership,
                    strategy_mode,
                    weight_profile_id,
                    optimization_settings
                )
                VALUES (
                    :week_id,
                    :lineup_number,
                    :players::jsonb,
                    :total_salary,
                    :projected_score,
                    :avg_ownership,
                    :strategy_mode::strategy_mode_enum,
                    :weight_profile_id,
                    :optimization_settings::jsonb
                )
                RETURNING id, created_at
            """)
            
            result = db.execute(query, {
                "week_id": request.week_id,
                "lineup_number": lineup_data.lineup_number,
                "players": json.dumps([dict(p) for p in lineup_data.players]),  # Convert list of dicts to JSON
                "total_salary": lineup_data.total_salary,
                "projected_score": lineup_data.projected_score,
                "avg_ownership": lineup_data.avg_ownership,
                "strategy_mode": strategy_mode,
                "weight_profile_id": request.weight_profile_id,
                "optimization_settings": json.dumps({}),  # Store settings as JSONB
            })
            
            row = result.fetchone()
            db.commit()
            
            saved_lineups.append(SavedLineup(
                id=row.id,
                week_id=request.week_id,
                lineup_number=lineup_data.lineup_number,
                players=lineup_data.players,
                total_salary=lineup_data.total_salary,
                projected_score=lineup_data.projected_score,
                avg_ownership=lineup_data.avg_ownership,
                strategy_mode=strategy_mode,
                weight_profile_id=request.weight_profile_id,
                created_at=row.created_at,
            ))
        
        return SaveLineupsResponse(
            saved_count=len(saved_lineups),
            lineups=saved_lineups,
        )
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving lineups: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save lineups: {str(e)}",
        )


@router.get("/saved/{week_id}", response_model=List[SavedLineup])
async def get_saved_lineups(
    week_id: int,
    db: Any = Depends(_get_current_db_dependency),
) -> List[SavedLineup]:
    """
    Retrieve saved lineups for a week.
    
    Args:
        week_id: Week ID
        db: Database session
    
    Returns:
        List of SavedLineup objects
    """
    try:
        query = text("""
            SELECT 
                id,
                week_id,
                lineup_number,
                players,
                total_salary,
                projected_score,
                avg_ownership,
                strategy_mode,
                weight_profile_id,
                created_at
            FROM generated_lineups
            WHERE week_id = :week_id
            ORDER BY lineup_number, created_at DESC
        """)
        
        rows = db.execute(query, {"week_id": week_id}).fetchall()
        
        lineups = []
        for row in rows:
            lineups.append(SavedLineup(
                id=row.id,
                week_id=row.week_id,
                lineup_number=row.lineup_number,
                players=row.players,
                total_salary=row.total_salary,
                projected_score=row.projected_score,
                avg_ownership=row.avg_ownership,
                strategy_mode=row.strategy_mode,
                weight_profile_id=row.weight_profile_id,
                created_at=row.created_at,
            ))
        
        return lineups
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error retrieving saved lineups: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve saved lineups: {str(e)}",
        )


@router.delete("/saved/{lineup_id}")
async def delete_saved_lineup(
    lineup_id: int,
    db: Any = Depends(_get_current_db_dependency),
):
    """
    Delete a saved lineup.
    
    Args:
        lineup_id: Lineup ID
        db: Database session
    """
    try:
        query = text("DELETE FROM generated_lineups WHERE id = :lineup_id")
        result = db.execute(query, {"lineup_id": lineup_id})
        db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lineup {lineup_id} not found",
            )
        
        return {"message": f"Lineup {lineup_id} deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting lineup: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete lineup: {str(e)}",
        )

