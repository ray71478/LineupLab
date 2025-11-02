"""
Pydantic schemas for Player Management API.

Defines request and response models for player-related endpoints.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class PlayerResponse(BaseModel):
    """Response model for a player in the player pool."""

    id: int = Field(..., description="Database ID")
    player_key: str = Field(..., description="Composite unique identifier (name_team_position)")
    name: str = Field(..., description="Player name")
    team: str = Field(..., description="Team abbreviation (e.g., KC, LAR)")
    position: str = Field(..., description="Position (QB, RB, WR, TE, DST)")
    salary: int = Field(..., description="Salary in cents (e.g., 8000 = $80.00)")
    projection: Optional[float] = Field(None, description="Projected points")
    ownership: Optional[float] = Field(None, description="Ownership percentage (0-1)")
    ceiling: Optional[float] = Field(None, description="Ceiling projection")
    floor: Optional[float] = Field(None, description="Floor projection")
    notes: Optional[str] = Field(None, description="Notes or comments")
    source: str = Field(..., description="Import source (LineStar, DraftKings, etc.)")
    status: str = Field(..., description="Match status (matched or unmatched)")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    contest_mode: str = Field(default='main', description="Contest mode (main or showdown)")

    # Calibrated projection fields for dual-value display
    projection_floor_original: Optional[float] = Field(None, description="Original floor projection")
    projection_floor_calibrated: Optional[float] = Field(None, description="Calibrated floor projection")
    projection_median_original: Optional[float] = Field(None, description="Original median projection")
    projection_median_calibrated: Optional[float] = Field(None, description="Calibrated median projection")
    projection_ceiling_original: Optional[float] = Field(None, description="Original ceiling projection")
    projection_ceiling_calibrated: Optional[float] = Field(None, description="Calibrated ceiling projection")
    calibration_applied: bool = Field(False, description="Whether calibration was applied to this player")

    class Config:
        from_attributes = True


class UnmatchedPlayerResponse(BaseModel):
    """Response model for an unmatched player."""

    id: int = Field(..., description="Database ID")
    imported_name: str = Field(..., description="Name as imported")
    team: str = Field(..., description="Team abbreviation")
    position: str = Field(..., description="Position")
    salary: Optional[int] = Field(None, description="Salary in cents")
    similarity_score: Optional[float] = Field(None, description="Similarity score (0-1)")
    status: str = Field(..., description="Status (pending, mapped, ignored)")
    suggestions: Optional[List[PlayerResponse]] = Field(None, description="Fuzzy match suggestions")

    class Config:
        from_attributes = True


class PlayerSearchResult(BaseModel):
    """Response model for player search results."""

    player_key: str = Field(..., description="Composite unique identifier")
    name: str = Field(..., description="Player name")
    team: str = Field(..., description="Team abbreviation")
    position: str = Field(..., description="Position")
    weeks: List[int] = Field(..., description="Weeks this player appears in")
    latest_salary: Optional[int] = Field(None, description="Most recent salary")
    latest_projection: Optional[float] = Field(None, description="Most recent projection")

    class Config:
        from_attributes = True


class PlayerFilters(BaseModel):
    """Request model for player filters."""

    positions: Optional[List[str]] = Field(None, description="Position filter (QB, RB, WR, TE, DST)")
    teams: Optional[List[str]] = Field(None, description="Team filter (NFL team abbreviations)")
    unmatched_only: bool = Field(False, description="Show only unmatched players")
    search_query: Optional[str] = Field(None, description="Search query for player name")

    class Config:
        from_attributes = True


class PlayerListResponse(BaseModel):
    """Response model for list of players."""

    success: bool = Field(..., description="Success flag")
    players: List[PlayerResponse] = Field(..., description="List of players")
    total: int = Field(..., description="Total count of players")
    unmatched_count: int = Field(..., description="Count of unmatched players")

    class Config:
        from_attributes = True


class UnmatchedPlayerListResponse(BaseModel):
    """Response model for list of unmatched players."""

    success: bool = Field(..., description="Success flag")
    unmatched_players: List[UnmatchedPlayerResponse] = Field(..., description="List of unmatched players")
    total_unmatched: int = Field(..., description="Total count of unmatched players")

    class Config:
        from_attributes = True


class PlayerSearchResponse(BaseModel):
    """Response model for player search."""

    success: bool = Field(..., description="Success flag")
    results: List[PlayerSearchResult] = Field(..., description="Search results")

    class Config:
        from_attributes = True


class PlayerSuggestionsResponse(BaseModel):
    """Response model for player suggestions."""

    success: bool = Field(..., description="Success flag")
    unmatched_player: Optional[UnmatchedPlayerResponse] = Field(None, description="Unmatched player")
    suggestions: List[PlayerResponse] = Field(..., description="Fuzzy match suggestions")

    class Config:
        from_attributes = True
