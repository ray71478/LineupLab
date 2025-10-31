"""
Smart Score API endpoints for calculation and weight profile management.

Provides REST API endpoints for:
- Calculating Smart Scores for players
- Managing weight profiles (CRUD operations)
- Retrieving default profile
"""

import logging
import time
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.services.smart_score_service import SmartScoreService
from backend.services.weight_profile_service import (
    WeightProfileService,
    ProfileNotFoundError,
    ProfileNameExistsError,
    CannotDeleteDefaultError,
)
from backend.schemas.smart_score_schemas import (
    CalculateScoreRequest,
    CalculateScoreResponse,
    WeightProfileResponse,
    WeightProfileListResponse,
    CreateProfileRequest,
    UpdateProfileRequest,
    PlayerScoreResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/smart-score", tags=["smart-score"])

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


@router.post("/calculate", response_model=CalculateScoreResponse)
async def calculate_smart_scores(
    request: CalculateScoreRequest,
    db: Any = Depends(_get_current_db_dependency),
) -> CalculateScoreResponse:
    """
    Calculate Smart Scores for all players in a week.

    Args:
        request: CalculateScoreRequest with week_id, weights, and config
        db: Database session

    Returns:
        CalculateScoreResponse: Players with calculated Smart Scores
    """
    start_time = time.time()

    try:
        service = SmartScoreService(db)
        players = service.calculate_for_all_players(
            week_id=request.week_id,
            weights=request.weights,
            config=request.config,
        )

        # Service already returns PlayerScoreResponse objects
        calculation_time_ms = (time.time() - start_time) * 1000

        logger.info(
            f"Calculated Smart Scores for {len(players)} players in {calculation_time_ms:.2f}ms"
        )

        return CalculateScoreResponse(
            success=True,
            players=players,
            total_players=len(players),
            calculation_time_ms=calculation_time_ms,
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Error calculating Smart Scores: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate Smart Scores: {str(e)}",
        )


@router.get("/profiles", response_model=WeightProfileListResponse)
async def list_weight_profiles(
    db: Any = Depends(_get_current_db_dependency),
) -> WeightProfileListResponse:
    """
    List all weight profiles.

    Args:
        db: Database session

    Returns:
        WeightProfileListResponse: List of profiles with default profile ID
    """
    try:
        service = WeightProfileService(db)
        profiles = service.list_profiles()

        # Find default profile ID
        default_profile_id = None
        for profile in profiles:
            if profile.is_default:
                default_profile_id = profile.id
                break

        return WeightProfileListResponse(
            success=True,
            profiles=profiles,
            default_profile_id=default_profile_id,
        )

    except Exception as e:
        logger.error(f"Error listing weight profiles: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list weight profiles: {str(e)}",
        )


@router.get("/profiles/default", response_model=WeightProfileResponse)
async def get_default_weight_profile(
    db: Any = Depends(_get_current_db_dependency),
) -> WeightProfileResponse:
    """
    Get the default weight profile.

    Args:
        db: Database session

    Returns:
        WeightProfileResponse: Default profile

    Raises:
        HTTPException: 404 if no default profile exists
    """
    try:
        service = WeightProfileService(db)
        return service.get_default_profile()

    except ProfileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No default weight profile found",
        )
    except Exception as e:
        logger.error(f"Error getting default weight profile: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get default weight profile: {str(e)}",
        )


@router.get("/profiles/{profile_id}", response_model=WeightProfileResponse)
async def get_weight_profile(
    profile_id: int,
    db: Any = Depends(_get_current_db_dependency),
) -> WeightProfileResponse:
    """
    Get a specific weight profile by ID.

    Args:
        profile_id: Profile ID
        db: Database session

    Returns:
        WeightProfileResponse: Profile data

    Raises:
        HTTPException: 404 if profile not found
    """
    try:
        service = WeightProfileService(db)
        return service.get_profile(profile_id)

    except ProfileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except Exception as e:
        logger.error(f"Error getting weight profile: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get weight profile: {str(e)}",
        )


@router.post("/profiles", response_model=WeightProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_weight_profile(
    request: CreateProfileRequest,
    db: Any = Depends(_get_current_db_dependency),
) -> WeightProfileResponse:
    """
    Create a new weight profile.

    Args:
        request: CreateProfileRequest with name, weights, config
        db: Database session

    Returns:
        WeightProfileResponse: Created profile

    Raises:
        HTTPException: 400 if name already exists
    """
    try:
        service = WeightProfileService(db)
        return service.create_profile(
            name=request.name,
            weights=request.weights,
            config=request.config,
            is_default=request.is_default or False,
        )

    except ProfileNameExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )
    except Exception as e:
        logger.error(f"Error creating weight profile: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create weight profile: {str(e)}",
        )


@router.put("/profiles/{profile_id}", response_model=WeightProfileResponse)
async def update_weight_profile(
    profile_id: int,
    request: UpdateProfileRequest,
    db: Any = Depends(_get_current_db_dependency),
) -> WeightProfileResponse:
    """
    Update a weight profile.

    Args:
        profile_id: Profile ID
        request: UpdateProfileRequest with optional fields to update
        db: Database session

    Returns:
        WeightProfileResponse: Updated profile

    Raises:
        HTTPException: 404 if profile not found, 400 if name conflict
    """
    try:
        service = WeightProfileService(db)
        return service.update_profile(
            profile_id=profile_id,
            name=request.name,
            weights=request.weights,
            config=request.config,
            is_default=request.is_default,
        )

    except ProfileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except ProfileNameExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )
    except Exception as e:
        logger.error(f"Error updating weight profile: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update weight profile: {str(e)}",
        )


@router.delete("/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_weight_profile(
    profile_id: int,
    db: Any = Depends(_get_current_db_dependency),
) -> None:
    """
    Delete a weight profile.

    Args:
        profile_id: Profile ID
        db: Database session

    Raises:
        HTTPException: 404 if profile not found, 400 if attempting to delete default
    """
    try:
        service = WeightProfileService(db)
        service.delete_profile(profile_id)

    except ProfileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except CannotDeleteDefaultError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )
    except Exception as e:
        logger.error(f"Error deleting weight profile: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete weight profile: {str(e)}",
        )


@router.post("/cache/invalidate")
async def invalidate_smart_score_cache(
    week_id: Optional[int] = None,
    db: Any = Depends(_get_current_db_dependency),
) -> dict:
    """
    Invalidate Smart Score calculation cache.

    This endpoint clears cached Smart Score calculations so that fresh calculations
    are performed with the latest weights/data. Use this after:
    - Updating weight profiles
    - Refreshing Vegas data
    - Loading new player data

    Args:
        week_id: Optional - clear cache for specific week only. If None, clears all cache.
        db: Database session

    Returns:
        Dictionary with success status and message
    """
    try:
        service = SmartScoreService(db)
        service.invalidate_cache(week_id=week_id)

        if week_id:
            message = f"Cleared Smart Score cache for week {week_id}"
        else:
            message = "Cleared all Smart Score cache"

        logger.info(message)

        return {
            "success": True,
            "message": message,
        }

    except Exception as e:
        logger.error(f"Error invalidating Smart Score cache: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invalidate cache: {str(e)}",
        )

