"""
Historical Insights API endpoints.

Provides endpoints for accessing historical performance insights:
- Player consistency metrics
- Opponent matchup history
- Salary efficiency trends
- Usage pattern warnings
- Stack correlation analysis
"""

import logging
from typing import Optional, Any
from fastapi import APIRouter, Query, Depends, HTTPException

from backend.services.historical_insights_service import HistoricalInsightsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/insights", tags=["insights"])

# Placeholder - will be overridden by main.py
get_db = None


def _get_current_db_dependency():
    """Get the current database dependency function."""
    import sys
    current_module = sys.modules[__name__]
    if current_module.get_db is None:
        raise RuntimeError("get_db not initialized. Make sure main.py has set up the dependency.")
    yield from current_module.get_db()


@router.get("/player/{player_key}/consistency")
async def get_player_consistency(
    player_key: str,
    season: int = Query(2025, description="Season year"),
    weeks_back: int = Query(6, ge=2, le=10, description="Number of weeks to analyze"),
    db: Any = Depends(_get_current_db_dependency),
) -> dict:
    """
    Get consistency metrics for a player.

    Returns:
        Dictionary with consistency_score, floor, ceiling, avg_points, games_count
    """
    try:
        service = HistoricalInsightsService(db)
        result = service.get_player_consistency(player_key, season, weeks_back)
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Error getting consistency for {player_key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/player/{player_key}/matchup-history")
async def get_matchup_history(
    player_key: str,
    opponent: str = Query(..., description="Opponent team abbreviation"),
    season: int = Query(2025, description="Season year"),
    db: Any = Depends(_get_current_db_dependency),
) -> dict:
    """
    Get historical performance vs specific opponent.

    Returns:
        Dictionary with avg_points, games_count, best_game, worst_game
    """
    try:
        service = HistoricalInsightsService(db)
        result = service.get_opponent_matchup_history(player_key, opponent, season)
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Error getting matchup history for {player_key} vs {opponent}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/player/{player_key}/salary-efficiency")
async def get_salary_efficiency(
    player_key: str,
    season: int = Query(2025, description="Season year"),
    weeks_back: int = Query(6, ge=2, le=10, description="Number of weeks to analyze"),
    db: Any = Depends(_get_current_db_dependency),
) -> dict:
    """
    Get salary efficiency trend for a player.

    Returns:
        Dictionary with avg_value_score, trend, recent_avg, earlier_avg
    """
    try:
        service = HistoricalInsightsService(db)
        result = service.get_salary_efficiency_trend(player_key, season, weeks_back)
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Error getting salary efficiency for {player_key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/player/{player_key}/usage-warnings")
async def get_usage_warnings(
    player_key: str,
    current_week: int = Query(..., ge=1, le=18, description="Current week number"),
    season: int = Query(2025, description="Season year"),
    db: Any = Depends(_get_current_db_dependency),
) -> dict:
    """
    Get usage pattern warnings for a player.

    Returns:
        Dictionary with has_warning, warnings, snap_trend, touch_trend
    """
    try:
        service = HistoricalInsightsService(db)
        result = service.get_usage_pattern_warnings(player_key, season, current_week)
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Error getting usage warnings for {player_key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/stack-correlation")
async def get_stack_correlation(
    qb_player_key: str = Query(..., description="QB player key"),
    wr_player_key: str = Query(..., description="WR player key"),
    team: str = Query(..., description="Team abbreviation"),
    season: int = Query(2025, description="Season year"),
    db: Any = Depends(_get_current_db_dependency),
) -> dict:
    """
    Get correlation between QB and WR from same team.

    Returns:
        Dictionary with correlation, games_count, avg_qb_points, avg_wr_points
    """
    try:
        service = HistoricalInsightsService(db)
        result = service.get_stack_correlation(qb_player_key, wr_player_key, team, season)
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Error getting stack correlation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

