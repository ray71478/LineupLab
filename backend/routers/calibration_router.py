"""
Projection Calibration API endpoints for managing position-based calibration factors.

Handles CRUD operations for calibration factors including:
- Retrieving calibration factors by week
- Creating/updating calibration factors
- Batch updates
- Calibration status
- Resetting to defaults
"""

import logging
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.schemas.calibration_schemas import (
    CalibrationResponse,
    CalibrationCreate,
    CalibrationListResponse,
    CalibrationStatusResponse,
    CalibrationBatchRequest,
    CalibrationResetResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/calibration", tags=["calibration"])


# Placeholder - will be overridden by main.py
get_db = None


# Create a function that returns the current get_db function
def _get_current_db_dependency():
    """Get the current database dependency function."""
    import sys
    current_module = sys.modules[__name__]
    if current_module.get_db is None:
        raise RuntimeError("get_db not initialized. Make sure main.py has set up the dependency.")
    # Return the generator from get_db
    yield from current_module.get_db()


# Default calibration values per position (from spec lines 253-263)
DEFAULT_CALIBRATIONS = {
    "QB": {"floor": 5.0, "median": 0.0, "ceiling": -5.0},
    "RB": {"floor": 10.0, "median": 8.0, "ceiling": -10.0},
    "WR": {"floor": 8.0, "median": 5.0, "ceiling": -12.0},
    "TE": {"floor": 10.0, "median": 7.0, "ceiling": -10.0},
    "K": {"floor": 0.0, "median": 0.0, "ceiling": 0.0},
    "DST": {"floor": 0.0, "median": 0.0, "ceiling": 0.0},
}


@router.get("/{week_id}", response_model=CalibrationListResponse)
async def get_calibrations(
    week_id: int,
    db: Any = Depends(_get_current_db_dependency),
) -> CalibrationListResponse:
    """
    Get all calibration factors for a specific week.

    Args:
        week_id: Week ID (from weeks table)
        db: Database session

    Returns:
        CalibrationListResponse with all calibrations for the week

    Example Response:
        {
            "success": true,
            "week_id": 8,
            "calibrations": [
                {
                    "id": 1,
                    "week_id": 8,
                    "position": "QB",
                    "floor_adjustment_percent": 5.0,
                    "median_adjustment_percent": 0.0,
                    "ceiling_adjustment_percent": -5.0,
                    "is_active": true,
                    "created_at": "2025-11-01T12:00:00",
                    "updated_at": "2025-11-01T12:00:00"
                },
                ...
            ]
        }
    """
    try:
        # Verify week exists
        week_exists = db.execute(
            text("SELECT id FROM weeks WHERE id = :week_id"),
            {"week_id": week_id}
        ).scalar()

        if not week_exists:
            raise HTTPException(status_code=404, detail=f"Week {week_id} not found")

        # Query all calibrations for this week
        result = db.execute(
            text("""
                SELECT id, week_id, position, floor_adjustment_percent,
                       median_adjustment_percent, ceiling_adjustment_percent,
                       is_active, created_at, updated_at
                FROM projection_calibration
                WHERE week_id = :week_id
                ORDER BY position
            """),
            {"week_id": week_id}
        ).fetchall()

        calibrations = [
            CalibrationResponse(
                id=row[0],
                week_id=row[1],
                position=row[2],
                floor_adjustment_percent=row[3],
                median_adjustment_percent=row[4],
                ceiling_adjustment_percent=row[5],
                is_active=row[6],
                created_at=row[7],
                updated_at=row[8],
            )
            for row in result
        ]

        return CalibrationListResponse(
            success=True,
            week_id=week_id,
            calibrations=calibrations,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get calibrations for week {week_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve calibrations: {str(e)}")


@router.post("/{week_id}", response_model=CalibrationResponse)
async def create_or_update_calibration(
    week_id: int,
    calibration: CalibrationCreate,
    db: Any = Depends(_get_current_db_dependency),
) -> CalibrationResponse:
    """
    Create or update calibration for a single position.

    Uses UPSERT logic (INSERT ON CONFLICT UPDATE) to handle both create and update.

    Args:
        week_id: Week ID (from weeks table)
        calibration: Calibration data (position, adjustments, is_active)
        db: Database session

    Returns:
        CalibrationResponse with created/updated calibration

    Example Request:
        {
            "position": "RB",
            "floor_adjustment_percent": 10.0,
            "median_adjustment_percent": 8.0,
            "ceiling_adjustment_percent": -10.0,
            "is_active": true
        }

    Example Response:
        {
            "id": 2,
            "week_id": 8,
            "position": "RB",
            "floor_adjustment_percent": 10.0,
            "median_adjustment_percent": 8.0,
            "ceiling_adjustment_percent": -10.0,
            "is_active": true,
            "created_at": "2025-11-01T12:00:00",
            "updated_at": "2025-11-01T12:00:00"
        }
    """
    try:
        # Verify week exists
        week_exists = db.execute(
            text("SELECT id FROM weeks WHERE id = :week_id"),
            {"week_id": week_id}
        ).scalar()

        if not week_exists:
            raise HTTPException(status_code=404, detail=f"Week {week_id} not found")

        # Upsert calibration
        db.execute(
            text("""
                INSERT INTO projection_calibration
                (week_id, position, floor_adjustment_percent,
                 median_adjustment_percent, ceiling_adjustment_percent, is_active)
                VALUES (:week_id, :position, :floor_adj, :median_adj, :ceiling_adj, :is_active)
                ON CONFLICT (week_id, position)
                DO UPDATE SET
                    floor_adjustment_percent = EXCLUDED.floor_adjustment_percent,
                    median_adjustment_percent = EXCLUDED.median_adjustment_percent,
                    ceiling_adjustment_percent = EXCLUDED.ceiling_adjustment_percent,
                    is_active = EXCLUDED.is_active,
                    updated_at = CURRENT_TIMESTAMP
            """),
            {
                "week_id": week_id,
                "position": calibration.position,
                "floor_adj": calibration.floor_adjustment_percent,
                "median_adj": calibration.median_adjustment_percent,
                "ceiling_adj": calibration.ceiling_adjustment_percent,
                "is_active": calibration.is_active,
            }
        )
        db.commit()

        # Retrieve the created/updated calibration
        result = db.execute(
            text("""
                SELECT id, week_id, position, floor_adjustment_percent,
                       median_adjustment_percent, ceiling_adjustment_percent,
                       is_active, created_at, updated_at
                FROM projection_calibration
                WHERE week_id = :week_id AND position = :position
            """),
            {"week_id": week_id, "position": calibration.position}
        ).fetchone()

        return CalibrationResponse(
            id=result[0],
            week_id=result[1],
            position=result[2],
            floor_adjustment_percent=result[3],
            median_adjustment_percent=result[4],
            ceiling_adjustment_percent=result[5],
            is_active=result[6],
            created_at=result[7],
            updated_at=result[8],
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create/update calibration: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save calibration: {str(e)}")


@router.post("/{week_id}/batch", response_model=CalibrationListResponse)
async def batch_update_calibrations(
    week_id: int,
    request: CalibrationBatchRequest,
    db: Any = Depends(_get_current_db_dependency),
) -> CalibrationListResponse:
    """
    Batch create or update calibrations for multiple positions.

    Executes all updates in a single transaction (all or nothing).

    Args:
        week_id: Week ID (from weeks table)
        request: Batch request with list of calibrations
        db: Database session

    Returns:
        CalibrationListResponse with all updated calibrations

    Example Request:
        {
            "calibrations": [
                {
                    "position": "QB",
                    "floor_adjustment_percent": 5.0,
                    "median_adjustment_percent": 0.0,
                    "ceiling_adjustment_percent": -5.0,
                    "is_active": true
                },
                {
                    "position": "RB",
                    "floor_adjustment_percent": 10.0,
                    "median_adjustment_percent": 8.0,
                    "ceiling_adjustment_percent": -10.0,
                    "is_active": true
                }
            ]
        }
    """
    try:
        # Verify week exists
        week_exists = db.execute(
            text("SELECT id FROM weeks WHERE id = :week_id"),
            {"week_id": week_id}
        ).scalar()

        if not week_exists:
            raise HTTPException(status_code=404, detail=f"Week {week_id} not found")

        # Batch upsert all calibrations in transaction
        for calibration in request.calibrations:
            db.execute(
                text("""
                    INSERT INTO projection_calibration
                    (week_id, position, floor_adjustment_percent,
                     median_adjustment_percent, ceiling_adjustment_percent, is_active)
                    VALUES (:week_id, :position, :floor_adj, :median_adj, :ceiling_adj, :is_active)
                    ON CONFLICT (week_id, position)
                    DO UPDATE SET
                        floor_adjustment_percent = EXCLUDED.floor_adjustment_percent,
                        median_adjustment_percent = EXCLUDED.median_adjustment_percent,
                        ceiling_adjustment_percent = EXCLUDED.ceiling_adjustment_percent,
                        is_active = EXCLUDED.is_active,
                        updated_at = CURRENT_TIMESTAMP
                """),
                {
                    "week_id": week_id,
                    "position": calibration.position,
                    "floor_adj": calibration.floor_adjustment_percent,
                    "median_adj": calibration.median_adjustment_percent,
                    "ceiling_adj": calibration.ceiling_adjustment_percent,
                    "is_active": calibration.is_active,
                }
            )

        db.commit()

        # Retrieve all calibrations for this week
        result = db.execute(
            text("""
                SELECT id, week_id, position, floor_adjustment_percent,
                       median_adjustment_percent, ceiling_adjustment_percent,
                       is_active, created_at, updated_at
                FROM projection_calibration
                WHERE week_id = :week_id
                ORDER BY position
            """),
            {"week_id": week_id}
        ).fetchall()

        calibrations = [
            CalibrationResponse(
                id=row[0],
                week_id=row[1],
                position=row[2],
                floor_adjustment_percent=row[3],
                median_adjustment_percent=row[4],
                ceiling_adjustment_percent=row[5],
                is_active=row[6],
                created_at=row[7],
                updated_at=row[8],
            )
            for row in result
        ]

        return CalibrationListResponse(
            success=True,
            week_id=week_id,
            calibrations=calibrations,
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to batch update calibrations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to batch update calibrations: {str(e)}")


@router.get("/{week_id}/status", response_model=CalibrationStatusResponse)
async def get_calibration_status(
    week_id: int,
    db: Any = Depends(_get_current_db_dependency),
) -> CalibrationStatusResponse:
    """
    Get calibration status for a specific week.

    Returns whether calibration is active and how many positions are configured.

    Args:
        week_id: Week ID (from weeks table)
        db: Database session

    Returns:
        CalibrationStatusResponse with status information

    Example Response:
        {
            "success": true,
            "week_id": 8,
            "is_active": true,
            "positions_configured": 4,
            "total_positions": 6
        }
    """
    try:
        # Verify week exists
        week_exists = db.execute(
            text("SELECT id FROM weeks WHERE id = :week_id"),
            {"week_id": week_id}
        ).scalar()

        if not week_exists:
            raise HTTPException(status_code=404, detail=f"Week {week_id} not found")

        # Count active calibrations
        active_count = db.execute(
            text("""
                SELECT COUNT(*)
                FROM projection_calibration
                WHERE week_id = :week_id AND is_active = true
            """),
            {"week_id": week_id}
        ).scalar() or 0

        # Count total calibrations (regardless of active status)
        total_configured = db.execute(
            text("""
                SELECT COUNT(DISTINCT position)
                FROM projection_calibration
                WHERE week_id = :week_id
            """),
            {"week_id": week_id}
        ).scalar() or 0

        # Calibration is active if at least one position has active calibration
        is_active = active_count > 0

        return CalibrationStatusResponse(
            success=True,
            week_id=week_id,
            is_active=is_active,
            positions_configured=total_configured,
            total_positions=6,  # QB, RB, WR, TE, K, DST
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get calibration status for week {week_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve calibration status: {str(e)}")


@router.post("/{week_id}/reset", response_model=CalibrationResetResponse)
async def reset_calibrations(
    week_id: int,
    db: Any = Depends(_get_current_db_dependency),
) -> CalibrationResetResponse:
    """
    Reset calibration factors to default values for all positions.

    Deletes existing calibrations and inserts default values.

    Args:
        week_id: Week ID (from weeks table)
        db: Database session

    Returns:
        CalibrationResetResponse with all default calibrations

    Example Response:
        {
            "success": true,
            "message": "Calibration reset to defaults for week 8",
            "calibrations": [
                {
                    "id": 1,
                    "week_id": 8,
                    "position": "QB",
                    "floor_adjustment_percent": 5.0,
                    "median_adjustment_percent": 0.0,
                    "ceiling_adjustment_percent": -5.0,
                    "is_active": true,
                    ...
                },
                ...
            ]
        }
    """
    try:
        # Verify week exists
        week_exists = db.execute(
            text("SELECT id FROM weeks WHERE id = :week_id"),
            {"week_id": week_id}
        ).scalar()

        if not week_exists:
            raise HTTPException(status_code=404, detail=f"Week {week_id} not found")

        # Delete existing calibrations for this week
        db.execute(
            text("DELETE FROM projection_calibration WHERE week_id = :week_id"),
            {"week_id": week_id}
        )

        # Insert default calibrations for all positions
        for position, defaults in DEFAULT_CALIBRATIONS.items():
            db.execute(
                text("""
                    INSERT INTO projection_calibration
                    (week_id, position, floor_adjustment_percent,
                     median_adjustment_percent, ceiling_adjustment_percent, is_active)
                    VALUES (:week_id, :position, :floor_adj, :median_adj, :ceiling_adj, true)
                """),
                {
                    "week_id": week_id,
                    "position": position,
                    "floor_adj": defaults["floor"],
                    "median_adj": defaults["median"],
                    "ceiling_adj": defaults["ceiling"],
                }
            )

        db.commit()

        # Retrieve all default calibrations
        result = db.execute(
            text("""
                SELECT id, week_id, position, floor_adjustment_percent,
                       median_adjustment_percent, ceiling_adjustment_percent,
                       is_active, created_at, updated_at
                FROM projection_calibration
                WHERE week_id = :week_id
                ORDER BY position
            """),
            {"week_id": week_id}
        ).fetchall()

        calibrations = [
            CalibrationResponse(
                id=row[0],
                week_id=row[1],
                position=row[2],
                floor_adjustment_percent=row[3],
                median_adjustment_percent=row[4],
                ceiling_adjustment_percent=row[5],
                is_active=row[6],
                created_at=row[7],
                updated_at=row[8],
            )
            for row in result
        ]

        return CalibrationResetResponse(
            success=True,
            message=f"Calibration reset to defaults for week {week_id}",
            calibrations=calibrations,
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to reset calibrations for week {week_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to reset calibrations: {str(e)}")
