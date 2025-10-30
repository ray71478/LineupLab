"""
Pydantic schemas for Cortex API endpoints.

Schemas are organized by domain:
- week_schemas: Week management and NFL schedule schemas
- player_schemas: Player management schemas
- smart_score_schemas: Smart Score Engine schemas
"""

from .smart_score_schemas import (
    WeightProfile,
    ScoreConfig,
    ScoreBreakdown,
    CalculateScoreRequest,
    PlayerScoreResponse,
    WeightProfileResponse,
    CreateProfileRequest,
    UpdateProfileRequest,
    CalculateScoreResponse,
    WeightProfileListResponse,
)

__all__ = [
    "WeightProfile",
    "ScoreConfig",
    "ScoreBreakdown",
    "CalculateScoreRequest",
    "PlayerScoreResponse",
    "WeightProfileResponse",
    "CreateProfileRequest",
    "UpdateProfileRequest",
    "CalculateScoreResponse",
    "WeightProfileListResponse",
]
