"""
Player Management API endpoints for viewing, filtering, and searching players.

Provides endpoints for:
- Fetching players by week with filtering and sorting
- Getting unmatched players with fuzzy match suggestions
- Searching players by name
- Getting fuzzy match suggestions for unmatched players
"""

import logging
from typing import Optional, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.services.player_management_service import PlayerManagementService
from backend.schemas.player_schemas import (
    PlayerListResponse,
    UnmatchedPlayerListResponse,
    PlayerSearchResponse,
    PlayerSuggestionsResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/players", tags=["players"])

# Placeholder - will be overridden by main.py
get_db = None


# Create a function that returns the current get_db function
# This is needed because Depends() captures the function at decoration time,
# so we need a wrapper that returns the latest get_db at runtime
def _get_current_db_dependency():
    """Get the current database dependency function."""
    import sys
    current_module = sys.modules[__name__]
    if current_module.get_db is None:
        raise RuntimeError("get_db not initialized. Make sure main.py has set up the dependency.")
    # Return the generator from get_db
    yield from current_module.get_db()


@router.get("/by-week/{week_id}", tags=["players"], response_model=PlayerListResponse)
async def get_players_by_week(
    week_id: int,
    position: Optional[str] = Query(None, description="Filter by position (QB, RB, WR, TE, DST)"),
    team: Optional[str] = Query(None, description="Filter by team abbreviation"),
    sort_by: Optional[str] = Query(None, description="Column to sort by"),
    sort_dir: Optional[str] = Query("asc", description="Sort direction (asc or desc)"),
    limit: int = Query(200, ge=1, le=200, description="Max results (default 200)"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Any = Depends(_get_current_db_dependency),
) -> PlayerListResponse:
    """
    Get all players for a specific week with optional filtering and sorting.

    Args:
        week_id: Week ID to fetch players for
        position: Optional position filter
        team: Optional team filter
        sort_by: Column to sort by
        sort_dir: Sort direction (asc or desc)
        limit: Max results (1-200)
        offset: Pagination offset

    Returns:
        {
            "success": true,
            "players": [...],
            "total": 150,
            "unmatched_count": 3
        }
    """
    try:
        service = PlayerManagementService(db)
        players, total, unmatched_count = service.get_players_by_week(
            week_id=week_id,
            position=position,
            team=team,
            sort_by=sort_by,
            sort_dir=sort_dir,
            limit=limit,
            offset=offset
        )

        return PlayerListResponse(
            success=True,
            players=players,
            total=total,
            unmatched_count=unmatched_count
        )
    except Exception as e:
        logger.error(f"Error fetching players for week {week_id}: {str(e)}", exc_info=True)
        return PlayerListResponse(
            success=False,
            players=[],
            total=0,
            unmatched_count=0
        )


@router.get("/unmatched/{week_id}", tags=["players"], response_model=UnmatchedPlayerListResponse)
async def get_unmatched_players(
    week_id: int,
    with_suggestions: bool = Query(True, description="Include fuzzy match suggestions"),
    limit: int = Query(50, ge=1, le=100, description="Max unmatched players"),
    db: Any = Depends(_get_current_db_dependency),
) -> UnmatchedPlayerListResponse:
    """
    Get unmatched players for a specific week with optional fuzzy match suggestions.

    Args:
        week_id: Week ID
        with_suggestions: Include fuzzy match suggestions
        limit: Max unmatched players to return

    Returns:
        {
            "success": true,
            "unmatched_players": [...],
            "total_unmatched": 3
        }
    """
    try:
        service = PlayerManagementService(db)
        unmatched_players, total = service.get_unmatched_players(
            week_id=week_id,
            with_suggestions=with_suggestions,
            limit=limit
        )

        return UnmatchedPlayerListResponse(
            success=True,
            unmatched_players=unmatched_players,
            total_unmatched=total
        )
    except Exception as e:
        logger.error(f"Error fetching unmatched players for week {week_id}: {str(e)}", exc_info=True)
        return UnmatchedPlayerListResponse(
            success=False,
            unmatched_players=[],
            total_unmatched=0
        )


@router.get("/search", tags=["players"], response_model=PlayerSearchResponse)
async def search_players(
    q: str = Query(..., description="Search query (player name)"),
    limit: int = Query(20, ge=1, le=50, description="Max results"),
    week_id: Optional[int] = Query(None, description="Optional: filter to specific week"),
    db: Any = Depends(_get_current_db_dependency),
) -> PlayerSearchResponse:
    """
    Search for players by name across weeks.

    Args:
        q: Search query (required)
        limit: Max results (1-50)
        week_id: Optional week filter

    Returns:
        {
            "success": true,
            "results": [...]
        }
    """
    try:
        if not q or len(q.strip()) == 0:
            return PlayerSearchResponse(
                success=False,
                results=[]
            )

        service = PlayerManagementService(db)
        results = service.search_players(
            query=q,
            limit=limit,
            week_id=week_id
        )

        return PlayerSearchResponse(
            success=True,
            results=results
        )
    except Exception as e:
        logger.error(f"Error searching players with query '{q}': {str(e)}", exc_info=True)
        return PlayerSearchResponse(
            success=False,
            results=[]
        )


@router.get("/suggestions/{unmatched_player_id}", tags=["players"], response_model=PlayerSuggestionsResponse)
async def get_player_suggestions(
    unmatched_player_id: int,
    limit: int = Query(5, ge=1, le=10, description="Max suggestions"),
    db: Any = Depends(_get_current_db_dependency),
) -> PlayerSuggestionsResponse:
    """
    Get fuzzy match suggestions for an unmatched player.

    Args:
        unmatched_player_id: ID of unmatched player
        limit: Max suggestions to return (1-10)

    Returns:
        {
            "success": true,
            "unmatched_player": {...},
            "suggestions": [...]
        }
    """
    try:
        service = PlayerManagementService(db)
        unmatched_player, suggestions = service.get_player_suggestions(
            unmatched_player_id=unmatched_player_id,
            limit=limit
        )

        return PlayerSuggestionsResponse(
            success=True,
            unmatched_player=unmatched_player,
            suggestions=suggestions
        )
    except Exception as e:
        logger.error(f"Error fetching suggestions for unmatched player {unmatched_player_id}: {str(e)}", exc_info=True)
        return PlayerSuggestionsResponse(
            success=False,
            unmatched_player=None,
            suggestions=[]
        )
