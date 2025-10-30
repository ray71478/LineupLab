"""
Router for triggering manual MySportsFeeds API data refresh.

Provides endpoint to manually invoke the daily data refresh job,
allowing users to update Vegas lines, injuries, and defense stats
on-demand from a configuration screen.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.scheduler.daily_refresh_job import DailyDataRefreshJob

logger = logging.getLogger(__name__)

# get_db will be injected by main.py
get_db = None

router = APIRouter(prefix="/api/refresh", tags=["refresh"])


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


@router.post("/mysportsfeeds")
async def refresh_mysportsfeeds(db: Session = Depends(_get_current_db_dependency)) -> Dict[str, Any]:
    """
    Manually trigger MySportsFeeds API data refresh.

    This endpoint executes the same refresh job that runs daily at 5:00 AM EST,
    allowing users to fetch fresh Vegas lines, injuries, and defensive stats
    on-demand from the configuration screen.

    Process:
    1. Fetch current week injuries from MySportsFeeds
    2. Fetch weekly games (Vegas ITT data)
    3. Fetch team defensive statistics
    4. Fetch player game logs for trend analysis
    5. Store results in database

    Returns:
        Dictionary with refresh status:
        {
            'success': bool,
            'start_time': datetime string,
            'end_time': datetime string,
            'duration_seconds': float,
            'injuries': {
                'fetched': int,
                'stored': int,
                'errors': int,
            },
            'games': {
                'fetched': int,
                'stored': int,
                'errors': int,
            },
            'team_stats': {
                'fetched': int,
                'stored': int,
                'errors': int,
            },
            'gamelogs': {
                'fetched': int,
                'stored': int,
                'errors': int,
            },
            'errors': [str, ...],
        }

    Raises:
        HTTPException: 500 if refresh job fails unexpectedly
        HTTPException: 503 if MySportsFeeds API key not configured

    Examples:
        POST /api/refresh/mysportsfeeds
        Response: {
            "success": true,
            "start_time": "2025-10-30T10:15:00",
            "end_time": "2025-10-30T10:18:45",
            "duration_seconds": 225,
            "injuries": {"fetched": 52, "stored": 47, "errors": 5},
            "games": {"fetched": 16, "stored": 16, "errors": 0},
            "team_stats": {"fetched": 32, "stored": 32, "errors": 0},
            "gamelogs": {"fetched": 1200, "stored": 1150, "errors": 50},
            "errors": []
        }
    """
    try:
        logger.info("Manual MySportsFeeds refresh initiated from API")

        # Create and execute the refresh job
        job = DailyDataRefreshJob(db)
        result = await job.execute()

        # Log the result
        if result.get("success"):
            logger.info(
                f"Manual refresh completed successfully in {result.get('duration_seconds', 0):.1f}s"
            )
        else:
            logger.warning(
                f"Manual refresh completed with errors: {result.get('errors', [])}"
            )

        return result

    except ValueError as e:
        # MySportsFeeds token not configured
        error_msg = str(e)
        logger.error(f"Refresh failed - configuration error: {error_msg}")
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": error_msg,
                "message": "MySportsFeeds API key not configured. "
                "Please set MYSPORTSFEEDS_TOKEN in your environment.",
            },
        )

    except Exception as e:
        # Unexpected error
        error_msg = f"Unexpected error during refresh: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Refresh job failed",
                "message": error_msg,
            },
        )


@router.get("/mysportsfeeds/status")
async def refresh_status() -> Dict[str, Any]:
    """
    Get status of the last MySportsFeeds refresh.

    Returns:
        Dictionary with last refresh info:
        {
            'last_refresh': datetime string or null,
            'status': 'success' | 'failed' | 'never',
            'message': str
        }

    Note: Currently returns a placeholder response.
    In a future enhancement, this could track refresh history
    in the database for better monitoring.
    """
    return {
        "last_refresh": None,
        "status": "never",
        "message": "Refresh status tracking coming soon. "
        "Click the Refresh Data button to update now.",
    }
