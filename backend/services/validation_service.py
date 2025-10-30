"""
ValidationService for data import validation.

Handles file-level, column-level, data type, and business rule validation
according to the Data Import System specification.
"""

import logging
import re
from typing import Optional

import pandas as pd
from fastapi import UploadFile

from backend.exceptions import DataImportError, ValidationError

logger = logging.getLogger(__name__)


class ValidationService:
    """Service for validating imported data against specification requirements."""

    # File-level constants
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    # Valid positions for DFS (QB, RB, WR, TE, DST)
    VALID_POSITIONS = {"QB", "RB", "WR", "TE", "DST"}

    # Salary range (in cents: 2000 = $20.00, 15000 = $150.00 in DraftKings)
    MIN_SALARY = 2000
    MAX_SALARY = 15000

    # Week range
    MIN_WEEK = 1
    MAX_WEEK = 18

    def validate_file(self, file: UploadFile) -> None:
        """
        Validate uploaded file format and size.

        Args:
            file: The uploaded file to validate

        Raises:
            DataImportError: If file format is invalid or size exceeds limit
        """
        # Check file extension
        if not file.filename.lower().endswith(".xlsx"):
            raise DataImportError("File must be .xlsx format")

        # Check file size
        if file.size and file.size > self.MAX_FILE_SIZE:
            raise DataImportError("File size exceeds 10MB limit")

    def validate_columns(self, df: pd.DataFrame, required_columns: list[str]) -> None:
        """
        Validate that all required columns exist in the DataFrame.

        Args:
            df: The DataFrame to validate
            required_columns: List of required column names

        Raises:
            DataImportError: If any required columns are missing
        """
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise DataImportError(
                f"Missing required columns: {', '.join(missing_columns)}"
            )

    def validate_data_types(self, df: pd.DataFrame, column_types: dict) -> None:
        """
        Validate and convert data types for specified columns.

        Args:
            df: The DataFrame to validate
            column_types: Dictionary mapping column names to expected types
                         ('int', 'float', 'str')

        Raises:
            DataImportError: If data type conversion fails

        Returns:
            None (modifies DataFrame in place)
        """
        for column, dtype in column_types.items():
            if column not in df.columns:
                continue

            try:
                if dtype == "int":
                    df[column] = pd.to_numeric(df[column], errors="coerce").astype(
                        "Int64"
                    )
                elif dtype == "float":
                    df[column] = pd.to_numeric(df[column], errors="coerce")
                elif dtype == "str":
                    df[column] = df[column].astype(str)
            except Exception as e:
                raise DataImportError(
                    f"Invalid data type in column '{column}': {str(e)}"
                )

    def validate_salary_range(self, salary: Optional[int], player_name: str) -> None:
        """
        Validate salary is not blank.

        Args:
            salary: The salary value to validate
            player_name: Player name for error message context

        Raises:
            DataImportError: If salary is None/blank
        """
        if salary is None:
            raise DataImportError(
                f"Invalid salary for {player_name}: salary cannot be blank"
            )

    def validate_projection(self, projection: Optional[float], player_name: str) -> None:
        """
        Validate projection is non-negative.

        Args:
            projection: The projection value to validate
            player_name: Player name for error message context

        Raises:
            DataImportError: If projection is negative
        """
        if projection is None:
            return

        if projection < 0:
            raise DataImportError(
                f"Invalid projection for {player_name}: {projection}. Must be >= 0"
            )

    def validate_ownership(self, ownership: Optional[float], player_name: str) -> None:
        """
        Validate ownership is not blank/null.

        Args:
            ownership: The ownership value to validate
            player_name: Player name for error message context

        Raises:
            DataImportError: If ownership is None/blank
        """
        # Ownership can be any value including 0, we just check it's not null
        # No range validation - accept whatever comes from the file
        pass

    def validate_position(self, position: Optional[str], player_name: str) -> None:
        """
        Validate position is in whitelist.

        Args:
            position: The position to validate
            player_name: Player name for error message context

        Raises:
            DataImportError: If position is not in whitelist
        """
        if position is None:
            return

        if position not in self.VALID_POSITIONS:
            raise DataImportError(
                f"Invalid position for {player_name}: '{position}'. "
                f"Must be {', '.join(sorted(self.VALID_POSITIONS))}"
            )

    def validate_week_range(self, week: Optional[int]) -> None:
        """
        Validate week number is in valid range.

        Args:
            week: The week number to validate

        Raises:
            DataImportError: If week is outside valid range
        """
        if week is None:
            return

        if not (self.MIN_WEEK <= week <= self.MAX_WEEK):
            raise DataImportError(
                f"Invalid week number: {week}. Must be between {self.MIN_WEEK} and {self.MAX_WEEK}"
            )

    def validate_ceiling_floor(
        self,
        player_name: str,
        ceiling: Optional[float],
        floor: Optional[float],
        projection: Optional[float],
    ) -> tuple[Optional[float], Optional[float]]:
        """
        Validate ceiling >= floor relationship.

        Issues a warning if ceiling < floor and uses projection as fallback.

        Args:
            player_name: Player name for logging context
            ceiling: The ceiling value to validate
            floor: The floor value to validate
            projection: The projection value to use as fallback

        Returns:
            Tuple of (ceiling, floor) with fallbacks applied if needed
        """
        if ceiling is None or floor is None:
            return ceiling, floor

        if ceiling < floor:
            logger.warning(
                f"Ceiling < Floor for {player_name} ({ceiling} < {floor}). "
                f"Using projection ({projection}) as both ceiling and floor"
            )
            return projection, projection

        return ceiling, floor

    def validate_player_data(self, player: dict) -> None:
        """
        Validate all player data against business rules.

        Args:
            player: Dictionary containing player data

        Raises:
            DataImportError: If any validation fails
            ValidationError: If validation rules are violated
        """
        player_name = player.get("name", "Unknown Player")

        # Validate salary
        if "salary" in player and player["salary"] is not None:
            self.validate_salary_range(player["salary"], player_name)

        # Validate projection
        if "projection" in player and player["projection"] is not None:
            self.validate_projection(player["projection"], player_name)

        # Validate ownership (after normalization)
        if "ownership" in player and player["ownership"] is not None:
            self.validate_ownership(player["ownership"], player_name)

        # Validate position
        if "position" in player and player["position"] is not None:
            self.validate_position(player["position"], player_name)

        # Validate ceiling >= floor relationship
        if "ceiling" in player and "floor" in player:
            ceiling, floor = self.validate_ceiling_floor(
                player_name,
                player.get("ceiling"),
                player.get("floor"),
                player.get("projection"),
            )
            player["ceiling"] = ceiling
            player["floor"] = floor
