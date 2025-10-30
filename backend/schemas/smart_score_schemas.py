"""
Pydantic schemas for Smart Score Engine API.

Defines request and response models for Smart Score calculation and weight profile management.
"""
from typing import Optional, Literal, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class WeightProfile(BaseModel):
    """Schema for weight profile with W1-W8 weights."""
    
    W1: float = Field(ge=0.0, le=1.0, description="W1: Projection Factor weight")
    W2: float = Field(ge=0.0, le=1.0, description="W2: Ceiling Factor weight")
    W3: float = Field(ge=0.0, le=1.0, description="W3: Ownership Penalty weight")
    W4: float = Field(ge=0.0, le=1.0, description="W4: Value Score weight")
    W5: float = Field(ge=0.0, le=1.0, description="W5: Trend Adjustment weight")
    W6: float = Field(ge=0.0, le=1.0, description="W6: Regression Penalty weight")
    W7: float = Field(ge=0.0, le=1.0, description="W7: Vegas Context weight")
    W8: float = Field(ge=0.0, le=1.0, description="W8: Matchup Adjustment weight")
    
    class Config:
        from_attributes = True


class ScoreConfig(BaseModel):
    """Schema for Smart Score calculation configuration."""
    
    projection_source: Literal["ETR", "LineStar"] = Field(
        default="ETR",
        description="Projection source to use (ETR or LineStar)"
    )
    eighty_twenty_enabled: bool = Field(
        default=True,
        description="Enable 80-20 regression rule for WR players"
    )
    eighty_twenty_threshold: float = Field(
        default=20.0,
        ge=0.0,
        description="Points threshold for regression risk detection"
    )
    
    class Config:
        from_attributes = True


class ScoreBreakdown(BaseModel):
    """Schema for detailed Smart Score breakdown by factor."""
    
    W1_value: float = Field(..., description="W1: Projection Factor contribution")
    W2_value: float = Field(..., description="W2: Ceiling Factor contribution")
    W3_value: float = Field(..., description="W3: Ownership Penalty contribution")
    W4_value: float = Field(..., description="W4: Value Score contribution")
    W5_value: float = Field(..., description="W5: Trend Adjustment contribution")
    W6_value: float = Field(..., description="W6: Regression Penalty contribution")
    W7_value: float = Field(..., description="W7: Vegas Context contribution")
    W8_value: float = Field(..., description="W8: Matchup Adjustment contribution")
    smart_score: float = Field(..., description="Final Smart Score")
    
    # Optional metadata
    missing_data_indicators: Optional[Dict[str, bool]] = Field(
        default=None,
        description="Indicators for which factors used default values"
    )
    
    class Config:
        from_attributes = True


class CalculateScoreRequest(BaseModel):
    """Request schema for Smart Score calculation."""
    
    week_id: int = Field(..., ge=1, description="Week ID for calculation")
    weights: WeightProfile = Field(..., description="Weight profile (W1-W8)")
    config: ScoreConfig = Field(default_factory=ScoreConfig, description="Calculation configuration")
    
    class Config:
        from_attributes = True


class PlayerScoreResponse(BaseModel):
    """Response schema for a player with Smart Score."""

    player_id: int = Field(..., description="Player pool ID")
    player_key: str = Field(..., description="Player key")
    name: str = Field(..., description="Player name")
    team: str = Field(..., description="Team abbreviation")
    position: str = Field(..., description="Position")
    salary: int = Field(..., description="Salary")
    projection: Optional[float] = Field(None, description="Projection")
    ownership: Optional[float] = Field(None, description="Ownership (0-1)")
    smart_score: Optional[float] = Field(None, description="Calculated Smart Score")
    projection_source: Optional[str] = Field(None, description="Projection source")
    opponent_rank_category: Optional[str] = Field(None, description="Opponent rank category")
    games_with_20_plus_snaps: Optional[int] = Field(None, description="Games with 20+ snaps")
    regression_risk: bool = Field(default=False, description="Regression risk flag (WR only)")
    score_breakdown: Optional[ScoreBreakdown] = Field(None, description="Detailed score breakdown")

    # Vegas context data
    implied_team_total: Optional[float] = Field(None, description="Vegas implied team total (ITT) - team's expected scoring")
    over_under: Optional[float] = Field(None, description="Vegas game total (over/under)")

    # Historical insights
    consistency_score: Optional[float] = Field(None, description="Consistency score (CV, lower is more consistent)")
    opponent_matchup_avg: Optional[float] = Field(None, description="Average points vs this week's opponent")
    salary_efficiency_trend: Optional[str] = Field(None, description="Salary efficiency trend: 'up', 'down', or 'stable'")
    usage_warnings: Optional[List[str]] = Field(None, description="Usage pattern warnings (declining snaps/touches)")

    # Stack correlation metadata (not affecting Smart Score)
    stack_partners: Optional[List[Dict[str, Any]]] = Field(None, description="Top stack correlation partners (e.g., QB-WR pairs with correlation > 0.5)")

    class Config:
        from_attributes = True


class WeightProfileResponse(BaseModel):
    """Response schema for a weight profile."""
    
    id: int = Field(..., description="Profile ID")
    name: str = Field(..., description="Profile name")
    weights: WeightProfile = Field(..., description="Weight values (W1-W8)")
    config: ScoreConfig = Field(..., description="Configuration")
    is_default: bool = Field(..., description="Is default profile")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class CreateProfileRequest(BaseModel):
    """Request schema for creating a weight profile."""
    
    name: str = Field(..., min_length=1, max_length=100, description="Profile name")
    weights: WeightProfile = Field(..., description="Weight values (W1-W8)")
    config: ScoreConfig = Field(default_factory=ScoreConfig, description="Configuration")
    is_default: Optional[bool] = Field(default=False, description="Set as default profile")
    
    class Config:
        from_attributes = True


class UpdateProfileRequest(BaseModel):
    """Request schema for updating a weight profile."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Profile name")
    weights: Optional[WeightProfile] = Field(None, description="Weight values (W1-W8)")
    config: Optional[ScoreConfig] = Field(None, description="Configuration")
    is_default: Optional[bool] = Field(None, description="Set as default profile")
    
    class Config:
        from_attributes = True


class CalculateScoreResponse(BaseModel):
    """Response schema for Smart Score calculation."""
    
    success: bool = Field(..., description="Success flag")
    players: list[PlayerScoreResponse] = Field(..., description="List of players with scores")
    total_players: int = Field(..., description="Total number of players calculated")
    calculation_time_ms: Optional[float] = Field(None, description="Calculation time in milliseconds")
    
    class Config:
        from_attributes = True


class WeightProfileListResponse(BaseModel):
    """Response schema for list of weight profiles."""
    
    success: bool = Field(..., description="Success flag")
    profiles: list[WeightProfileResponse] = Field(..., description="List of weight profiles")
    default_profile_id: Optional[int] = Field(None, description="ID of default profile")
    
    class Config:
        from_attributes = True

