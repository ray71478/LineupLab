"""
Pydantic schemas for Lineup Optimizer API.

Defines request and response models for lineup generation and management.
"""
from typing import Optional, List, Dict, Literal, Any
from datetime import datetime
from pydantic import BaseModel, Field
from backend.schemas.smart_score_schemas import WeightProfile, ScoreConfig


class PlayerExposureLimits(BaseModel):
    """Schema for player exposure limits."""
    
    min: Optional[int] = Field(None, ge=0, description="Minimum lineups player must appear in")
    max: Optional[int] = Field(None, ge=0, description="Maximum lineups player can appear in")
    
    class Config:
        from_attributes = True


class StackingRules(BaseModel):
    """Schema for stacking rules."""
    
    qb_wr_stack_enabled: bool = Field(
        default=True,  # Default ON for tournaments
        description="Require QB + at least 1 WR from same team"
    )
    bring_back_enabled: bool = Field(
        default=True,  # Default ON for tournaments
        description="Require bring-back (opposing team player) when stacking"
    )
    
    class Config:
        from_attributes = True


class OptimizationSettings(BaseModel):
    """Schema for optimization settings."""
    
    num_lineups: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Number of lineups to generate"
    )
    strategy_mode: Literal['Chalk', 'Balanced', 'Contrarian', 'Tournament'] = Field(
        default='Tournament',
        description="Strategy mode: Chalk (high ownership), Balanced (mixed), Contrarian (low ownership), Tournament (ceiling + ownership leverage)"
    )
    max_players_per_team: int = Field(
        default=4,
        ge=1,
        le=9,
        description="Maximum players from single team"
    )
    max_players_per_game: int = Field(
        default=5,
        ge=1,
        le=9,
        description="Maximum players from single game"
    )
    player_exposure_limits: Optional[Dict[str, PlayerExposureLimits]] = Field(
        default=None,
        description="Player exposure limits (key: player_key, value: min/max limits)"
    )
    stacking_rules: Optional[StackingRules] = Field(
        default_factory=StackingRules,
        description="Stacking rules configuration"
    )
    smart_score_threshold: Optional[float] = Field(
        default=5.0,
        ge=0,
        description="Minimum Smart Score threshold (exclude players below). Default 5.0 filters out low-quality players."
    )
    
    class Config:
        from_attributes = True


class LineupPlayer(BaseModel):
    """Schema for a player in a lineup."""
    
    position: str = Field(..., description="Position")
    player_key: str = Field(..., description="Player key")
    name: str = Field(..., description="Player name")
    team: str = Field(..., description="Team abbreviation")
    salary: int = Field(..., description="Salary")
    smart_score: float = Field(..., description="Smart Score")
    ownership: float = Field(..., description="Ownership (0-1)")
    projection: Optional[float] = Field(None, description="Projection")
    
    class Config:
        from_attributes = True


class GeneratedLineup(BaseModel):
    """Schema for a generated lineup."""
    
    lineup_number: int = Field(..., description="Lineup number (1-N, or -1/-2 for baselines)")
    players: List[Dict[str, Any]] = Field(..., description="List of players in lineup")
    total_salary: int = Field(..., ge=0, le=50000, description="Total salary")
    projected_score: float = Field(..., ge=0, description="Total Smart Score")
    projected_points: float = Field(..., ge=0, description="Total projected fantasy points")
    avg_ownership: float = Field(..., ge=0, le=1, description="Average ownership %")
    
    class Config:
        from_attributes = True


class LineupOptimizationRequest(BaseModel):
    """Request schema for lineup optimization."""
    
    week_id: int = Field(..., ge=1, description="Week ID")
    settings: OptimizationSettings = Field(
        default_factory=OptimizationSettings,
        description="Optimization settings"
    )
    selected_player_ids: Optional[List[int]] = Field(
        default=None,
        description="Optional list of player IDs to use for optimization. If provided, only these players will be considered."
    )
    weights: Optional[WeightProfile] = Field(
        default=None,
        description="Optional custom weight profile. If not provided, uses default profile."
    )
    config: Optional[ScoreConfig] = Field(
        default=None,
        description="Optional custom score config. If not provided, uses default config."
    )
    
    class Config:
        from_attributes = True


class LineupOptimizationResponse(BaseModel):
    """Response schema for lineup optimization."""
    
    week_id: int = Field(..., description="Week ID")
    lineups: List[GeneratedLineup] = Field(..., description="Generated lineups")
    settings: OptimizationSettings = Field(..., description="Settings used")
    generation_time_ms: float = Field(..., description="Generation time in milliseconds")
    
    class Config:
        from_attributes = True


class SavedLineup(BaseModel):
    """Schema for a saved lineup in database."""
    
    id: int = Field(..., description="Lineup ID")
    week_id: int = Field(..., description="Week ID")
    lineup_number: int = Field(..., description="Lineup number")
    players: List[Dict[str, Any]] = Field(..., description="Players JSON")
    total_salary: int = Field(..., description="Total salary")
    projected_score: float = Field(..., description="Projected score")
    avg_ownership: Optional[float] = Field(None, description="Average ownership")
    strategy_mode: str = Field(..., description="Strategy mode")
    weight_profile_id: Optional[int] = Field(None, description="Weight profile ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True


class SaveLineupsRequest(BaseModel):
    """Request schema for saving lineups."""
    
    week_id: int = Field(..., ge=1, description="Week ID")
    lineups: List[GeneratedLineup] = Field(..., description="Lineups to save")
    weight_profile_id: Optional[int] = Field(None, description="Weight profile ID used")
    strategy_mode: Optional[str] = Field(None, description="Strategy mode used")
    
    class Config:
        from_attributes = True


class SaveLineupsResponse(BaseModel):
    """Response schema for saving lineups."""
    
    saved_count: int = Field(..., description="Number of lineups saved")
    lineups: List[SavedLineup] = Field(..., description="Saved lineups")
    
    class Config:
        from_attributes = True

