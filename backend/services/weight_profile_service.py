"""
WeightProfileService for managing weight profiles for Smart Score calculations.

Provides methods for:
- Creating, reading, updating, and deleting weight profiles
- Managing default profile
- Validating profile data
"""

import logging
import json
from typing import Optional, List
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.schemas.smart_score_schemas import (
    WeightProfile,
    ScoreConfig,
    WeightProfileResponse,
    CreateProfileRequest,
    UpdateProfileRequest,
)
from backend.exceptions import CortexException, ValidationError

logger = logging.getLogger(__name__)


class ProfileNotFoundError(CortexException):
    """Raised when a weight profile is not found."""

    def __init__(self, profile_id: int):
        super().__init__(f"Weight profile with ID {profile_id} not found", status_code=404)


class ProfileNameExistsError(CortexException):
    """Raised when a profile name already exists."""

    def __init__(self, name: str):
        super().__init__(
            f"Weight profile with name '{name}' already exists", status_code=400
        )


class CannotDeleteDefaultError(CortexException):
    """Raised when attempting to delete the default profile."""

    def __init__(self):
        super().__init__(
            "Cannot delete the default 'Base' profile", status_code=400
        )


class WeightProfileService:
    """Service for managing weight profiles."""

    def __init__(self, session: Session):
        """
        Initialize WeightProfileService.

        Args:
            session: SQLAlchemy Session for database operations
        """
        self.session = session

    def create_profile(
        self,
        name: str,
        weights: WeightProfile,
        config: ScoreConfig,
        is_default: bool = False,
    ) -> WeightProfileResponse:
        """
        Create a new weight profile.

        Args:
            name: Profile name (must be unique)
            weights: Weight values (W1-W8)
            config: Score configuration
            is_default: Whether this is the default profile

        Returns:
            WeightProfileResponse: Created profile

        Raises:
            ProfileNameExistsError: If profile name already exists
            ValidationError: If data validation fails
        """
        # Validate name uniqueness
        existing = self.session.execute(
            text("SELECT id FROM weight_profiles WHERE name = :name"),
            {"name": name},
        ).fetchone()

        if existing:
            raise ProfileNameExistsError(name)

        # If setting as default, unset other defaults
        if is_default:
            self.session.execute(
                text("UPDATE weight_profiles SET is_default = false WHERE is_default = true")
            )

        # Convert weights and config to JSONB strings
        weights_json = json.dumps(weights.model_dump())
        config_json = json.dumps(config.model_dump())

        # Insert new profile - PostgreSQL will auto-cast JSON strings to JSONB
        result = self.session.execute(
            text("""
                INSERT INTO weight_profiles (name, weights, config, is_default, created_at, updated_at)
                VALUES (:name, :weights, :config, :is_default, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING id, created_at, updated_at
            """),
            {
                "name": name,
                "weights": weights_json,
                "config": config_json,
                "is_default": is_default,
            },
        )
        row = result.fetchone()
        self.session.commit()

        profile_id = row[0]
        created_at = row[1]
        updated_at = row[2]

        logger.info(f"Created weight profile: {name} (ID: {profile_id})")

        return WeightProfileResponse(
            id=profile_id,
            name=name,
            weights=weights,
            config=config,
            is_default=is_default,
            created_at=created_at,
            updated_at=updated_at,
        )

    def get_profile(self, profile_id: int) -> WeightProfileResponse:
        """
        Get a weight profile by ID.

        Args:
            profile_id: Profile ID

        Returns:
            WeightProfileResponse: Profile data

        Raises:
            ProfileNotFoundError: If profile not found
        """
        result = self.session.execute(
            text("""
                SELECT id, name, weights, config, is_default, created_at, updated_at
                FROM weight_profiles
                WHERE id = :profile_id
            """),
            {"profile_id": profile_id},
        )
        row = result.fetchone()

        if not row:
            raise ProfileNotFoundError(profile_id)

        return self._row_to_profile_response(row)

    def list_profiles(self) -> List[WeightProfileResponse]:
        """
        List all weight profiles.

        Returns:
            List[WeightProfileResponse]: List of profiles
        """
        result = self.session.execute(
            text("""
                SELECT id, name, weights, config, is_default, created_at, updated_at
                FROM weight_profiles
                ORDER BY is_default DESC, created_at DESC
            """)
        )
        rows = result.fetchall()

        return [self._row_to_profile_response(row) for row in rows]

    def update_profile(
        self,
        profile_id: int,
        name: Optional[str] = None,
        weights: Optional[WeightProfile] = None,
        config: Optional[ScoreConfig] = None,
        is_default: Optional[bool] = None,
    ) -> WeightProfileResponse:
        """
        Update a weight profile.

        Args:
            profile_id: Profile ID
            name: New profile name (optional)
            weights: New weights (optional)
            config: New config (optional)
            is_default: Whether to set as default (optional)

        Returns:
            WeightProfileResponse: Updated profile

        Raises:
            ProfileNotFoundError: If profile not found
            ProfileNameExistsError: If new name already exists
        """
        # Verify profile exists
        existing = self.get_profile(profile_id)

        # Check if name change conflicts with existing name
        if name and name != existing.name:
            name_check = self.session.execute(
                text("SELECT id FROM weight_profiles WHERE name = :name AND id != :profile_id"),
                {"name": name, "profile_id": profile_id},
            ).fetchone()

            if name_check:
                raise ProfileNameExistsError(name)

        # Build update query dynamically
        updates = []
        params = {"profile_id": profile_id}

        if name is not None:
            updates.append("name = :name")
            params["name"] = name

        if weights is not None:
            updates.append("weights = :weights")
            params["weights"] = json.dumps(weights.model_dump())

        if config is not None:
            updates.append("config = :config")
            params["config"] = json.dumps(config.model_dump())

        if is_default is not None:
            # If setting as default, unset other defaults
            if is_default:
                self.session.execute(
                    text("UPDATE weight_profiles SET is_default = false WHERE is_default = true AND id != :profile_id"),
                    {"profile_id": profile_id},
                )
            updates.append("is_default = :is_default")
            params["is_default"] = is_default

        if not updates:
            # No updates requested
            return existing

        updates.append("updated_at = CURRENT_TIMESTAMP")

        query = f"""
            UPDATE weight_profiles
            SET {', '.join(updates)}
            WHERE id = :profile_id
            RETURNING id, name, weights, config, is_default, created_at, updated_at
        """

        result = self.session.execute(text(query), params)
        row = result.fetchone()
        self.session.commit()

        logger.info(f"Updated weight profile: ID {profile_id}")

        return self._row_to_profile_response(row)

    def delete_profile(self, profile_id: int) -> None:
        """
        Delete a weight profile.

        Args:
            profile_id: Profile ID

        Raises:
            ProfileNotFoundError: If profile not found
            CannotDeleteDefaultError: If attempting to delete default profile
        """
        # Verify profile exists and check if it's default
        profile = self.get_profile(profile_id)

        if profile.is_default:
            raise CannotDeleteDefaultError()

        # Delete profile
        result = self.session.execute(
            text("DELETE FROM weight_profiles WHERE id = :profile_id RETURNING id"),
            {"profile_id": profile_id},
        )
        deleted = result.fetchone()

        if not deleted:
            raise ProfileNotFoundError(profile_id)

        self.session.commit()
        logger.info(f"Deleted weight profile: ID {profile_id}")

    def get_default_profile(self) -> WeightProfileResponse:
        """
        Get the default weight profile.

        Returns:
            WeightProfileResponse: Default profile

        Raises:
            ProfileNotFoundError: If no default profile exists
        """
        result = self.session.execute(
            text("""
                SELECT id, name, weights, config, is_default, created_at, updated_at
                FROM weight_profiles
                WHERE is_default = true
                LIMIT 1
            """)
        )
        row = result.fetchone()

        if not row:
            raise ProfileNotFoundError(0)  # Use 0 as placeholder for "not found"

        return self._row_to_profile_response(row)

    def _row_to_profile_response(self, row) -> WeightProfileResponse:
        """
        Convert database row to WeightProfileResponse.

        Args:
            row: Database row tuple

        Returns:
            WeightProfileResponse: Profile response object
        """
        profile_id, name, weights_json, config_json, is_default, created_at, updated_at = row

        # Parse JSONB fields
        weights_dict = json.loads(weights_json) if isinstance(weights_json, str) else weights_json
        config_dict = json.loads(config_json) if isinstance(config_json, str) else config_json

        weights = WeightProfile(**weights_dict)
        config = ScoreConfig(**config_dict)

        return WeightProfileResponse(
            id=profile_id,
            name=name,
            weights=weights,
            config=config,
            is_default=is_default,
            created_at=created_at,
            updated_at=updated_at,
        )

