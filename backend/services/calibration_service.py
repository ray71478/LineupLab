"""
CalibrationService for managing projection calibration calculations.

Provides methods for:
- Retrieving calibration factors for a week
- Applying calibration to player projection data
- Calculating calibrated values using adjustment percentages
"""

import logging
from typing import Dict, List, Tuple, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class CalibrationService:
    """Service for calibration calculations and application."""

    def __init__(self, session: Session):
        """
        Initialize CalibrationService.

        Args:
            session: SQLAlchemy Session for database operations
        """
        self.session = session

    def get_calibration_for_week(
        self, week_id: int, db: Session
    ) -> Dict[str, Tuple[float, float, float]]:
        """
        Query active calibration factors for a week.

        Args:
            week_id: Week ID to get calibration for
            db: Database session

        Returns:
            Dict mapping position -> (floor_adj, median_adj, ceiling_adj)
            Example: {'QB': (5.0, 0.0, -5.0), 'RB': (10.0, 8.0, -10.0)}
        """
        result = db.execute(
            text("""
                SELECT position, floor_adjustment_percent,
                       median_adjustment_percent, ceiling_adjustment_percent
                FROM projection_calibration
                WHERE week_id = :week_id AND is_active = true
            """),
            {"week_id": week_id}
        )
        rows = result.fetchall()

        # Create lookup dict by position
        calibration_map = {
            row[0]: (row[1], row[2], row[3])
            for row in rows
        }

        logger.info(
            f"Retrieved calibration for week {week_id}: "
            f"{len(calibration_map)} positions configured"
        )

        return calibration_map

    def calculate_calibrated_value(
        self, original: Optional[float], adjustment_percent: float
    ) -> Optional[float]:
        """
        Calculate calibrated value using formula.

        Formula: calibrated = original * (1 + adjustment_percent / 100)

        Args:
            original: Original projection value (can be None)
            adjustment_percent: Percentage adjustment (-50 to +50)

        Returns:
            Calibrated value rounded to 2 decimal places, or None if original is None.
            Returns 0 if result is negative.
        """
        if original is None:
            return None

        # Apply calibration formula
        calibrated = original * (1 + adjustment_percent / 100)

        # Ensure non-negative result
        if calibrated < 0:
            logger.warning(
                f"Calibration produced negative value: {original} * "
                f"(1 + {adjustment_percent}/100) = {calibrated}. Setting to 0."
            )
            calibrated = 0.0

        # Round to 2 decimal places
        return round(calibrated, 2)

    def apply_calibration(
        self, players: List[dict], week_id: int, db: Session
    ) -> List[dict]:
        """
        Apply calibration to player projections.

        Implementation based on spec pseudocode (lines 193-249).

        Args:
            players: List of player dictionaries with projection data
            week_id: Week ID for calibration lookup
            db: Database session

        Returns:
            List of player dictionaries with calibrated projection fields added
        """
        # Query active calibration factors for this week
        calibration_map = self.get_calibration_for_week(week_id, db)

        if not calibration_map:
            logger.info(
                f"No active calibration found for week {week_id}. "
                f"Copying original to calibrated values."
            )

        calibrated_count = 0
        skipped_count = 0

        for player in players:
            position = player.get('position')

            # Store original values
            player['projection_floor_original'] = player.get('floor')
            player['projection_median_original'] = player.get('projection')
            player['projection_ceiling_original'] = player.get('ceiling')

            # Apply calibration if exists for this position
            if position in calibration_map:
                floor_adj, median_adj, ceiling_adj = calibration_map[position]

                # Calculate calibrated values (handles NULL gracefully)
                player['projection_floor_calibrated'] = self.calculate_calibrated_value(
                    player['projection_floor_original'], floor_adj
                )

                player['projection_median_calibrated'] = self.calculate_calibrated_value(
                    player['projection_median_original'], median_adj
                )

                player['projection_ceiling_calibrated'] = self.calculate_calibrated_value(
                    player['projection_ceiling_original'], ceiling_adj
                )

                player['calibration_applied'] = True
                calibrated_count += 1
            else:
                # No calibration - copy original to calibrated
                player['projection_floor_calibrated'] = player['projection_floor_original']
                player['projection_median_calibrated'] = player['projection_median_original']
                player['projection_ceiling_calibrated'] = player['projection_ceiling_original']
                player['calibration_applied'] = False
                skipped_count += 1

        logger.info(
            f"Calibration applied to {calibrated_count} players, "
            f"{skipped_count} players skipped (no calibration for position)"
        )

        return players
