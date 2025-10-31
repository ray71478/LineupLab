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
        
        # Get default weight profile and config
        default_profile = weight_profile_service.get_default_profile()
        weights = WeightProfile(**default_profile.weights)
        config = ScoreConfig(**default_profile.config)
        
        # Calculate Smart Scores
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
                f"Filtered to {len(players_with_scores)} players from {len(selected_ids_set)} selected IDs"
            )
        
        # Generate lineups
        optimizer_service = LineupOptimizerService(db)
        generated_lineups = optimizer_service.generate_lineups(
            week_id=request.week_id,
            players=players_with_scores,
            settings=request.settings,
        )
        
        if not generated_lineups:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to generate lineups. Check constraints and player pool.",
            )
        
        generation_time_ms = (time.time() - start_time) * 1000
        
        logger.info(
            f"Generated {len(generated_lineups)} lineups for week {request.week_id} in {generation_time_ms:.2f}ms"
        )
        
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

