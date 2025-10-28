"""
Week Management API endpoints for NFL season and week management.

Provides REST API endpoints for:
- Retrieving weeks by year with metadata
- Getting current active week
- Managing week status (manual overrides)
- Locking weeks after data import
- Tracking import status
- Retrieving NFL schedule
"""

import logging
from datetime import datetime, date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from backend.services.week_management_service import (
    WeekManagementService,
    WeekLockedError,
    WeekNotFoundError,
    InvalidYearError,
)
from backend.services.nfl_schedule_service import NFLScheduleService
from backend.schemas.week_schemas import (
    WeekListResponse,
    CurrentWeekResponse,
    WeekMetadataDetailsResponse,
    StatusUpdateRequest,
    StatusUpdateResponse,
    GenerateWeeksRequest,
    GenerateWeeksResponse,
    NFLScheduleResponse,
    LockWeekRequest,
    LockWeekResponse,
    ImportStatusRequest,
    ImportStatusResponse,
    WeekResponse,
    ErrorResponse,
)
from backend.exceptions import CortexException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["weeks"])

# This will be overridden by main.py
get_db = None


def validate_year(year: int) -> None:
    """
    Validate year is within acceptable range.

    Args:
        year: Year to validate

    Raises:
        InvalidYearError: If year is not between 2025 and 2030
    """
    if not (2025 <= year <= 2030):
        raise InvalidYearError(year)


def validate_status(status: str) -> None:
    """
    Validate status is valid enum value.

    Args:
        status: Status to validate

    Raises:
        ValueError: If status not in valid list
    """
    valid_statuses = ["active", "upcoming", "completed"]
    if status not in valid_statuses:
        raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")


def validate_import_status(status: str) -> None:
    """
    Validate import status is valid enum value.

    Args:
        status: Status to validate

    Raises:
        ValueError: If status not in valid list
    """
    valid_statuses = ["pending", "imported", "error"]
    if status not in valid_statuses:
        raise ValueError(f"Import status must be one of: {', '.join(valid_statuses)}")


@router.get("/weeks", response_model=WeekListResponse)
async def get_weeks(
    year: int,
    include_metadata: bool = True,
    db=Depends(get_db),
) -> WeekListResponse:
    """
    Get all weeks for a given NFL season.

    Query Parameters:
        year: NFL season year (required, e.g., 2025)
        include_metadata: Include metadata in response (optional, default: true)

    Returns:
        WeekListResponse with 18 weeks for the year

    Raises:
        InvalidYearError: If year not between 2025-2030 (returns 400)
    """
    try:
        # Validate year
        validate_year(year)

        # Create service
        week_service = WeekManagementService(db)

        # Check if weeks exist for year, if not create them
        weeks = week_service.get_weeks_by_year(year)

        # Get current week and date
        current_week_data = week_service.get_current_week()
        current_week_num = current_week_data.get("week_number", 1)
        current_date = current_week_data.get("current_date", datetime.utcnow().isoformat())

        # Build response
        week_responses = []
        for week in weeks:
            week_responses.append(
                WeekResponse(
                    id=week["id"],
                    season=week["season"],
                    week_number=week["week_number"],
                    status=week["status"],
                    status_override=week.get("status_override"),
                    nfl_slate_date=str(week["nfl_slate_date"]),
                    is_locked=week.get("is_locked", False),
                    locked_at=week.get("locked_at"),
                    metadata=week.get("metadata", {}),
                )
            )

        return WeekListResponse(
            success=True,
            year=year,
            weeks=week_responses,
            current_week=current_week_num,
            current_date=current_date,
        )

    except InvalidYearError as e:
        logger.error(f"Invalid year: {year}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Error retrieving weeks for year {year}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve weeks")


@router.get("/current-week", response_model=CurrentWeekResponse)
async def get_current_week(db=Depends(get_db)) -> CurrentWeekResponse:
    """
    Get the current active NFL week.

    Returns:
        CurrentWeekResponse with current week number and details

    Raises:
        CortexException: If unable to determine current week (returns 500)
    """
    try:
        # Create service
        week_service = WeekManagementService(db)

        # Get current week
        current_week_data = week_service.get_current_week()

        # Extract data
        week_number = current_week_data.get("week_number", 1)
        current_date = current_week_data.get("current_date", datetime.utcnow().isoformat())
        week_details_dict = current_week_data.get("week_details", {})

        # Build week response
        week_details = WeekResponse(
            id=week_details_dict.get("id", 0),
            season=week_details_dict.get("season", 2025),
            week_number=week_details_dict.get("week_number", week_number),
            status=week_details_dict.get("status", "active"),
            status_override=week_details_dict.get("status_override"),
            nfl_slate_date=str(week_details_dict.get("nfl_slate_date", "")),
            is_locked=week_details_dict.get("is_locked", False),
            locked_at=week_details_dict.get("locked_at"),
            metadata=week_details_dict.get("metadata", {}),
        )

        return CurrentWeekResponse(
            success=True,
            current_week=week_number,
            current_date=current_date,
            week_details=week_details,
        )

    except Exception as e:
        logger.error(f"Error retrieving current week: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve current week")


@router.get("/weeks/{week_id}/metadata", response_model=WeekMetadataDetailsResponse)
async def get_week_metadata(
    week_id: int,
    db=Depends(get_db),
) -> WeekMetadataDetailsResponse:
    """
    Get detailed metadata for a specific week.

    Path Parameters:
        week_id: ID of the week

    Returns:
        WeekMetadataDetailsResponse with full metadata

    Raises:
        WeekNotFoundError: If week not found (returns 404)
    """
    try:
        # Create service
        nfl_service = NFLScheduleService(db)

        # Get metadata
        metadata = nfl_service.get_week_metadata(week_id)

        if not metadata:
            raise WeekNotFoundError(week_id)

        return WeekMetadataDetailsResponse(
            success=True,
            week_id=week_id,
            metadata=metadata,
        )

    except WeekNotFoundError as e:
        logger.error(f"Week not found: {week_id}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Error retrieving week metadata for {week_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve week metadata")


@router.put("/weeks/{week_id}/status", response_model=StatusUpdateResponse)
async def update_week_status(
    week_id: int,
    request: StatusUpdateRequest,
    db=Depends(get_db),
) -> StatusUpdateResponse:
    """
    Update the status of a week with manual override.

    Path Parameters:
        week_id: ID of the week

    Request Body:
        status: New status (active|upcoming|completed)
        reason: Optional reason for override

    Returns:
        StatusUpdateResponse with updated week

    Raises:
        WeekNotFoundError: If week not found (returns 404)
        WeekLockedError: If week is locked (returns 409)
        ValueError: If status invalid (returns 400)
    """
    try:
        # Validate status
        validate_status(request.status)

        # Create service
        week_service = WeekManagementService(db)

        # Check week exists
        from sqlalchemy import text
        result = db.execute(
            text("SELECT id FROM weeks WHERE id = :id"),
            {"id": week_id}
        )
        if not result.scalar():
            raise WeekNotFoundError(week_id)

        # Check week is not locked
        from sqlalchemy import text
        result = db.execute(
            text("SELECT is_locked FROM weeks WHERE id = :id"),
            {"id": week_id}
        )
        is_locked = result.scalar()
        if is_locked:
            # Get week number for error message
            result = db.execute(
                text("SELECT week_number FROM weeks WHERE id = :id"),
                {"id": week_id}
            )
            week_number = result.scalar()
            raise WeekLockedError(week_number)

        # Update status
        updated_week = week_service.update_week_status(
            week_id,
            request.status,
            request.reason or "Manual override"
        )

        # Build response
        week_response = WeekResponse(
            id=updated_week["id"],
            season=updated_week["season"],
            week_number=updated_week["week_number"],
            status=updated_week["status"],
            status_override=updated_week.get("status_override"),
            nfl_slate_date=str(updated_week["nfl_slate_date"]),
            is_locked=updated_week.get("is_locked", False),
            locked_at=updated_week.get("locked_at"),
            metadata=updated_week.get("metadata", {}),
        )

        return StatusUpdateResponse(
            success=True,
            message="Week status updated",
            week=week_response,
        )

    except WeekNotFoundError as e:
        logger.error(f"Week not found: {week_id}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except WeekLockedError as e:
        logger.error(f"Week locked: {week_id}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except ValueError as e:
        logger.error(f"Invalid status for week {week_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating week status for {week_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update week status")


@router.post("/weeks/generate", response_model=GenerateWeeksResponse)
async def generate_weeks(
    request: GenerateWeeksRequest,
    db=Depends(get_db),
) -> GenerateWeeksResponse:
    """
    Generate 18 weeks for a given NFL season.

    Request Body:
        year: NFL season year (2025-2030)
        force_regenerate: Force regenerate if already exists (optional, default: false)

    Returns:
        GenerateWeeksResponse with count of created weeks

    Raises:
        InvalidYearError: If year invalid (returns 400)
        CortexException: If weeks already exist and force_regenerate=false (returns 409)
    """
    try:
        # Validate year
        validate_year(request.year)

        # Create service
        week_service = WeekManagementService(db)

        # Check if weeks already exist
        from sqlalchemy import text
        result = db.execute(
            text("SELECT COUNT(*) FROM weeks WHERE season = :season"),
            {"season": request.year}
        )
        existing_count = result.scalar()

        if existing_count > 0 and not request.force_regenerate:
            raise CortexException(
                f"Weeks already exist for season {request.year}. "
                f"Set force_regenerate=true to override.",
                status_code=409
            )

        # If force regenerate, delete existing weeks
        if existing_count > 0 and request.force_regenerate:
            db.execute(
                text("DELETE FROM weeks WHERE season = :season"),
                {"season": request.year}
            )
            db.commit()

        # Create weeks
        weeks_created = week_service.create_weeks_for_season(request.year)

        return GenerateWeeksResponse(
            success=True,
            message=f"{weeks_created} weeks generated for {request.year}",
            weeks_created=weeks_created,
            year=request.year,
        )

    except InvalidYearError as e:
        logger.error(f"Invalid year: {request.year}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except CortexException as e:
        logger.error(f"Error generating weeks for {request.year}: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Error generating weeks for {request.year}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate weeks")


@router.get("/nfl-schedule", response_model=NFLScheduleResponse)
async def get_nfl_schedule(
    year: Optional[int] = None,
    db=Depends(get_db),
) -> NFLScheduleResponse:
    """
    Get the NFL schedule for a given year.

    Query Parameters:
        year: NFL season year (optional, default: current year)

    Returns:
        NFLScheduleResponse with 18 weeks of schedule data

    Raises:
        InvalidYearError: If year invalid (returns 400)
    """
    try:
        # Default to current year if not provided
        if year is None:
            year = datetime.utcnow().year

        # Validate year
        validate_year(year)

        # Create service
        nfl_service = NFLScheduleService(db)

        # Get schedule
        schedule = nfl_service.get_nfl_schedule(year)

        return NFLScheduleResponse(
            success=True,
            year=year,
            schedule=schedule,
        )

    except InvalidYearError as e:
        logger.error(f"Invalid year: {year}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Error retrieving NFL schedule for {year}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve NFL schedule")


@router.put("/weeks/{week_id}/lock", response_model=LockWeekResponse)
async def lock_week(
    week_id: int,
    request: LockWeekRequest,
    db=Depends(get_db),
) -> LockWeekResponse:
    """
    Lock a week after successful data import.

    Path Parameters:
        week_id: ID of the week

    Request Body:
        import_id: Import transaction ID (UUID)
        player_count: Number of players imported

    Returns:
        LockWeekResponse with updated week

    Raises:
        WeekNotFoundError: If week not found (returns 404)
        CortexException: If week already locked (returns 409)
    """
    try:
        # Create service
        week_service = WeekManagementService(db)

        # Check week exists and get its status
        from sqlalchemy import text
        result = db.execute(
            text("SELECT id, is_locked, week_number FROM weeks WHERE id = :id"),
            {"id": week_id}
        )
        week_data = result.fetchone()
        if not week_data:
            raise WeekNotFoundError(week_id)

        week_id_result, is_locked, week_number = week_data
        if is_locked:
            raise CortexException(
                f"Week {week_number} is already locked",
                status_code=409
            )

        # Lock the week
        updated_week = week_service.lock_week(
            week_id,
            request.import_id,
            request.player_count
        )

        # Build response
        week_response = WeekResponse(
            id=updated_week["id"],
            season=updated_week["season"],
            week_number=updated_week["week_number"],
            status=updated_week["status"],
            status_override=updated_week.get("status_override"),
            nfl_slate_date=str(updated_week["nfl_slate_date"]),
            is_locked=updated_week.get("is_locked", False),
            locked_at=updated_week.get("locked_at"),
            metadata=updated_week.get("metadata", {}),
        )

        return LockWeekResponse(
            success=True,
            message="Week locked",
            week=week_response,
        )

    except WeekNotFoundError as e:
        logger.error(f"Week not found: {week_id}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except CortexException as e:
        logger.error(f"Error locking week {week_id}: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Error locking week {week_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to lock week")


@router.put("/weeks/{week_id}/import-status", response_model=ImportStatusResponse)
async def update_import_status(
    week_id: int,
    request: ImportStatusRequest,
    db=Depends(get_db),
) -> ImportStatusResponse:
    """
    Update the import status of a week.

    Path Parameters:
        week_id: ID of the week

    Request Body:
        status: Import status (pending|imported|error)
        import_count: Number of players imported
        import_timestamp: When import occurred (ISO format)
        error_message: Error message if status=error

    Returns:
        ImportStatusResponse with updated week

    Raises:
        WeekNotFoundError: If week not found (returns 404)
        ValueError: If status invalid (returns 400)
    """
    try:
        # Validate import status
        validate_import_status(request.status)

        # Check week exists
        from sqlalchemy import text
        result = db.execute(
            text("SELECT id FROM weeks WHERE id = :id"),
            {"id": week_id}
        )
        if not result.scalar():
            raise WeekNotFoundError(week_id)

        # Update week_metadata with import status
        db.execute(
            text("""
                UPDATE week_metadata
                SET import_status = :status,
                    import_count = :count,
                    import_timestamp = :timestamp,
                    import_error_message = :error_message,
                    updated_at = CURRENT_TIMESTAMP
                WHERE week_id = :week_id
            """),
            {
                "status": request.status,
                "count": request.import_count,
                "timestamp": request.import_timestamp,
                "error_message": request.error_message,
                "week_id": week_id,
            }
        )
        db.commit()

        # Get updated week
        result = db.execute(
            text("""
                SELECT w.id, w.season, w.week_number, w.status, w.status_override,
                       w.nfl_slate_date, w.is_locked, w.locked_at
                FROM weeks w
                WHERE w.id = :id
            """),
            {"id": week_id}
        )
        week_data = result.fetchone()

        if not week_data:
            raise WeekNotFoundError(week_id)

        week_id_result, season, week_number, status, status_override, nfl_slate_date, is_locked, locked_at = week_data

        # Get metadata
        nfl_service = NFLScheduleService(db)
        metadata = nfl_service.get_week_metadata(week_id)

        # Build response
        week_response = WeekResponse(
            id=week_id_result,
            season=season,
            week_number=week_number,
            status=status,
            status_override=status_override,
            nfl_slate_date=str(nfl_slate_date),
            is_locked=is_locked,
            locked_at=locked_at,
            metadata=metadata if metadata else {},
        )

        return ImportStatusResponse(
            success=True,
            message="Import status updated",
            week=week_response,
        )

    except WeekNotFoundError as e:
        logger.error(f"Week not found: {week_id}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except ValueError as e:
        logger.error(f"Invalid import status for week {week_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating import status for week {week_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update import status")
