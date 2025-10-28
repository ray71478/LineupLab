"""
Pydantic schemas for Week Management API endpoints.

Provides request/response validation and serialization for all week-related
API endpoints including weeks, status updates, and imports.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime


class WeekMetadataResponse(BaseModel):
    """Metadata for a single week."""

    model_config = ConfigDict(from_attributes=True)

    season: int = Field(..., description="NFL season year")
    week_number: int = Field(..., ge=1, le=18, description="Week number 1-18")
    nfl_slate_date: str = Field(..., description="NFL slate date (YYYY-MM-DD)")
    kickoff_time: str = Field(..., description="Kickoff time (HH:MM)")
    espn_link: Optional[str] = Field(None, description="ESPN schedule link")
    slate_start: Optional[str] = Field(None, description="Slate start timestamp")
    slate_end: Optional[str] = Field(None, description="Slate end timestamp")
    import_status: str = Field(default="pending", description="Import status: pending|imported|error")
    import_count: int = Field(default=0, description="Number of players imported")
    import_timestamp: Optional[str] = Field(None, description="When data was imported (ISO format)")
    error_message: Optional[str] = Field(None, description="Error message if import failed")
    is_locked: bool = Field(default=False, description="Whether week is locked")
    locked_at: Optional[str] = Field(None, description="When week was locked (ISO format)")


class WeekResponse(BaseModel):
    """Response for a single week with all details."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Week ID")
    season: int = Field(..., description="NFL season year")
    week_number: int = Field(..., ge=1, le=18, description="Week number 1-18")
    status: str = Field(..., description="Week status: active|upcoming|completed")
    status_override: Optional[str] = Field(None, description="Manual status override")
    nfl_slate_date: str = Field(..., description="NFL slate date (YYYY-MM-DD)")
    is_locked: bool = Field(default=False, description="Whether week is locked")
    locked_at: Optional[str] = Field(None, description="When week was locked (ISO format)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Week metadata")


class WeekListResponse(BaseModel):
    """Response for GET /api/weeks endpoint."""

    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(default=True, description="Whether request succeeded")
    year: int = Field(..., description="NFL season year")
    weeks: List[WeekResponse] = Field(..., description="List of 18 weeks")
    current_week: int = Field(..., ge=1, le=18, description="Current active week number")
    current_date: str = Field(..., description="Current date/time (ISO format)")


class CurrentWeekResponse(BaseModel):
    """Response for GET /api/current-week endpoint."""

    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(default=True, description="Whether request succeeded")
    current_week: int = Field(..., ge=1, le=18, description="Current active week number")
    current_date: str = Field(..., description="Current date/time (ISO format)")
    week_details: WeekResponse = Field(..., description="Full details of current week")


class WeekMetadataDetailsResponse(BaseModel):
    """Response for GET /api/weeks/{id}/metadata endpoint."""

    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(default=True, description="Whether request succeeded")
    week_id: int = Field(..., description="Week ID")
    metadata: WeekMetadataResponse = Field(..., description="Full metadata for week")


class StatusUpdateRequest(BaseModel):
    """Request body for PUT /api/weeks/{id}/status endpoint."""

    model_config = ConfigDict(from_attributes=True)

    status: str = Field(..., description="New status: active|upcoming|completed")
    reason: Optional[str] = Field(None, description="Reason for manual override")


class StatusUpdateResponse(BaseModel):
    """Response for PUT /api/weeks/{id}/status endpoint."""

    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(default=True, description="Whether request succeeded")
    message: str = Field(..., description="Status update message")
    week: WeekResponse = Field(..., description="Updated week object")


class GenerateWeeksRequest(BaseModel):
    """Request body for POST /api/weeks/generate endpoint."""

    model_config = ConfigDict(from_attributes=True)

    year: int = Field(..., ge=2025, le=2030, description="NFL season year to generate")
    force_regenerate: bool = Field(default=False, description="Force regenerate if already exists")


class GenerateWeeksResponse(BaseModel):
    """Response for POST /api/weeks/generate endpoint."""

    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(default=True, description="Whether request succeeded")
    message: str = Field(..., description="Generation message")
    weeks_created: int = Field(..., ge=0, le=18, description="Number of weeks created")
    year: int = Field(..., description="NFL season year")


class NFLScheduleItemResponse(BaseModel):
    """Single week in NFL schedule."""

    model_config = ConfigDict(from_attributes=True)

    week: int = Field(..., ge=1, le=18, description="Week number")
    slate_date: str = Field(..., description="Slate date (YYYY-MM-DD)")
    kickoff_time: str = Field(..., description="Kickoff time (HH:MM)")
    is_playoff: bool = Field(default=False, description="Whether playoff week")
    game_count: int = Field(..., ge=0, description="Number of games")


class NFLScheduleResponse(BaseModel):
    """Response for GET /api/nfl-schedule endpoint."""

    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(default=True, description="Whether request succeeded")
    year: int = Field(..., description="NFL season year")
    schedule: List[NFLScheduleItemResponse] = Field(..., description="All weeks in schedule")


class LockWeekRequest(BaseModel):
    """Request body for PUT /api/weeks/{id}/lock endpoint."""

    model_config = ConfigDict(from_attributes=True)

    import_id: str = Field(..., description="Import ID (UUID)")
    player_count: int = Field(..., ge=0, description="Number of players imported")


class LockWeekResponse(BaseModel):
    """Response for PUT /api/weeks/{id}/lock endpoint."""

    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(default=True, description="Whether request succeeded")
    message: str = Field(..., description="Lock message")
    week: WeekResponse = Field(..., description="Updated week object")


class ImportStatusRequest(BaseModel):
    """Request body for PUT /api/weeks/{id}/import-status endpoint."""

    model_config = ConfigDict(from_attributes=True)

    status: str = Field(..., description="Import status: pending|imported|error")
    import_count: int = Field(default=0, description="Number of players imported")
    import_timestamp: Optional[str] = Field(None, description="Import timestamp (ISO format)")
    error_message: Optional[str] = Field(None, description="Error message if status=error")


class ImportStatusResponse(BaseModel):
    """Response for PUT /api/weeks/{id}/import-status endpoint."""

    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(default=True, description="Whether request succeeded")
    message: str = Field(..., description="Status update message")
    week: WeekResponse = Field(..., description="Updated week object")


class ErrorResponse(BaseModel):
    """Standard error response for all endpoints."""

    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(default=False, description="Whether request succeeded")
    error: str = Field(..., description="Error message")
