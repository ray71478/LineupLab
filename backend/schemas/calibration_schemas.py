"""
Pydantic schemas for Calibration API.

Defines request and response models for calibration-related endpoints.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class PositionEnum(str, Enum):
    """Valid NFL positions for calibration."""
    QB = "QB"
    RB = "RB"
    WR = "WR"
    TE = "TE"
    K = "K"
    DST = "DST"


class CalibrationBase(BaseModel):
    """Base model for calibration with common fields."""

    position: PositionEnum = Field(..., description="NFL position (QB, RB, WR, TE, K, DST)")
    floor_adjustment_percent: float = Field(
        ...,
        description="Floor adjustment percentage (-50 to +50)",
        ge=-50.0,
        le=50.0
    )
    median_adjustment_percent: float = Field(
        ...,
        description="Median adjustment percentage (-50 to +50)",
        ge=-50.0,
        le=50.0
    )
    ceiling_adjustment_percent: float = Field(
        ...,
        description="Ceiling adjustment percentage (-50 to +50)",
        ge=-50.0,
        le=50.0
    )
    is_active: bool = Field(True, description="Whether calibration is active")

    @field_validator('floor_adjustment_percent', 'median_adjustment_percent', 'ceiling_adjustment_percent')
    @classmethod
    def validate_percentage_range(cls, v: float) -> float:
        """Validate adjustment percentages are within valid range."""
        if v < -50.0 or v > 50.0:
            raise ValueError('Adjustment percentage must be between -50 and +50')
        return v


class CalibrationCreate(CalibrationBase):
    """Schema for creating a new calibration."""
    pass


class CalibrationUpdate(BaseModel):
    """Schema for updating an existing calibration (all fields optional)."""

    position: Optional[PositionEnum] = Field(None, description="NFL position")
    floor_adjustment_percent: Optional[float] = Field(
        None,
        description="Floor adjustment percentage (-50 to +50)",
        ge=-50.0,
        le=50.0
    )
    median_adjustment_percent: Optional[float] = Field(
        None,
        description="Median adjustment percentage (-50 to +50)",
        ge=-50.0,
        le=50.0
    )
    ceiling_adjustment_percent: Optional[float] = Field(
        None,
        description="Ceiling adjustment percentage (-50 to +50)",
        ge=-50.0,
        le=50.0
    )
    is_active: Optional[bool] = Field(None, description="Whether calibration is active")

    @field_validator('floor_adjustment_percent', 'median_adjustment_percent', 'ceiling_adjustment_percent')
    @classmethod
    def validate_percentage_range(cls, v: Optional[float]) -> Optional[float]:
        """Validate adjustment percentages are within valid range."""
        if v is not None and (v < -50.0 or v > 50.0):
            raise ValueError('Adjustment percentage must be between -50 and +50')
        return v


class CalibrationResponse(CalibrationBase):
    """Schema for calibration response with database fields."""

    id: int = Field(..., description="Database ID")
    week_id: int = Field(..., description="Week ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class CalibrationStatusResponse(BaseModel):
    """Schema for calibration status response."""

    success: bool = Field(..., description="Success flag")
    week_id: int = Field(..., description="Week ID")
    is_active: bool = Field(..., description="Whether calibration is active for this week")
    positions_configured: int = Field(..., description="Number of positions with active calibration")
    total_positions: int = Field(6, description="Total number of positions (always 6)")

    class Config:
        from_attributes = True


class CalibrationBatchRequest(BaseModel):
    """Schema for batch calibration update request."""

    calibrations: List[CalibrationCreate] = Field(
        ...,
        description="List of calibrations to create/update"
    )

    @field_validator('calibrations')
    @classmethod
    def validate_calibrations_list(cls, v: List[CalibrationCreate]) -> List[CalibrationCreate]:
        """Validate calibrations list is not empty and has no duplicates."""
        if not v:
            raise ValueError('Calibrations list cannot be empty')

        # Check for duplicate positions
        positions = [cal.position for cal in v]
        if len(positions) != len(set(positions)):
            raise ValueError('Calibrations list contains duplicate positions')

        return v


class CalibrationListResponse(BaseModel):
    """Schema for list of calibrations response."""

    success: bool = Field(..., description="Success flag")
    week_id: int = Field(..., description="Week ID")
    calibrations: List[CalibrationResponse] = Field(..., description="List of calibrations")

    class Config:
        from_attributes = True


class CalibrationResetResponse(BaseModel):
    """Schema for calibration reset response."""

    success: bool = Field(..., description="Success flag")
    message: str = Field(..., description="Success message")
    calibrations: List[CalibrationResponse] = Field(..., description="Reset calibrations")

    class Config:
        from_attributes = True
