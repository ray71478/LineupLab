"""
StatusUpdateService for managing automatic week status updates.

Provides core business logic for:
- Determining week status based on NFL slate dates and current date
- Applying manual status overrides
- Updating all week statuses for a season
- Handling timezone-aware date comparisons (ET)
"""

import logging
from datetime import datetime, date
from typing import Optional
from pytz import timezone
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Eastern Time timezone
ET = timezone('America/New_York')


class StatusUpdateService:
    """Service for managing and determining week statuses."""

    def __init__(self, session: Session):
        """
        Initialize StatusUpdateService.

        Args:
            session: SQLAlchemy Session for database operations
        """
        self.session = session

    def _parse_date(self, value) -> Optional[date]:
        """
        Parse a date value that might be string, date, or datetime.

        Args:
            value: Value to parse (string, date, or datetime)

        Returns:
            date object or None if value is None
        """
        if value is None:
            return None

        if isinstance(value, date) and not isinstance(value, datetime):
            return value

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, str):
            try:
                # Try parsing as ISO date format
                return datetime.fromisoformat(value).date()
            except (ValueError, TypeError):
                try:
                    # Try parsing as YYYY-MM-DD
                    return datetime.strptime(value, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse date value: {value}")
                    return None

        return None

    def determine_week_status(self, week_id: int, current_date: Optional[date] = None) -> str:
        """
        Determine the status of a week based on its NFL slate date.

        Compares the current_date to the week's nfl_slate_date to determine:
        - 'completed': if nfl_slate_date is in the past (before current_date)
        - 'active': if nfl_slate_date is today or within the current week
        - 'upcoming': if nfl_slate_date is in the future (after current_date)

        Uses Eastern Time (ET) timezone for date comparisons.

        Args:
            week_id: ID of the week to determine status for
            current_date: Date to compare against (defaults to today in ET)

        Returns:
            Status string: 'completed', 'active', or 'upcoming'

        Raises:
            Exception: If week is not found
        """
        if current_date is None:
            # Get current date in ET timezone
            current_date = datetime.now(ET).date()

        # Query the week's NFL slate date
        result = self.session.execute(
            text("SELECT nfl_slate_date FROM weeks WHERE id = :week_id"),
            {"week_id": week_id}
        )
        row = result.fetchone()

        if not row:
            raise Exception(f"Week {week_id} not found")

        nfl_slate_date = self._parse_date(row[0])

        # If no slate date, default to upcoming
        if nfl_slate_date is None:
            return "upcoming"

        # Compare dates
        if nfl_slate_date < current_date:
            return "completed"
        elif nfl_slate_date == current_date:
            return "active"
        else:
            return "upcoming"

    def apply_manual_overrides(self, week_id: int, nfl_slate_date: Optional[date], current_date: Optional[date] = None) -> str:
        """
        Apply manual status overrides if they exist, otherwise determine status automatically.

        Checks the week_status_overrides table for a manual override. If an override exists,
        returns that status. Otherwise, determines status based on nfl_slate_date.

        Args:
            week_id: ID of the week
            nfl_slate_date: NFL slate date for the week
            current_date: Date to use for status calculation (defaults to today in ET)

        Returns:
            Final status string: either override status or auto-determined status
        """
        # Check for manual override
        result = self.session.execute(
            text("SELECT override_status FROM week_status_overrides WHERE week_id = :week_id"),
            {"week_id": week_id}
        )
        override_row = result.fetchone()

        if override_row:
            return override_row[0]

        # No override, determine status automatically
        return self.determine_week_status(week_id, current_date)

    def update_all_statuses(self, season: int, current_date: Optional[date] = None) -> int:
        """
        Update status for all weeks in a season.

        Queries all weeks for the given season, determines status for each based on
        nfl_slate_date, checks for manual overrides, and updates the database.

        Args:
            season: NFL season year (e.g., 2025)
            current_date: Date to use for status calculations (defaults to today in ET)

        Returns:
            Count of updated weeks

        Raises:
            Exception: If season has no weeks
        """
        if current_date is None:
            current_date = datetime.now(ET).date()

        # Get all weeks for season
        result = self.session.execute(
            text("""
                SELECT id, nfl_slate_date, status_override
                FROM weeks
                WHERE season = :season
                ORDER BY week_number ASC
            """),
            {"season": season}
        )
        weeks_rows = result.fetchall()

        if not weeks_rows:
            logger.warning(f"No weeks found for season {season}")
            return 0

        updated_count = 0

        for week_row in weeks_rows:
            week_id, nfl_slate_date, status_override = week_row

            # Parse the nfl_slate_date
            parsed_slate_date = self._parse_date(nfl_slate_date)

            # Determine the status for this week
            calculated_status = self.determine_week_status(week_id, current_date)

            # Check if there's a manual override
            override_status = self.apply_manual_overrides(week_id, parsed_slate_date, current_date)

            # Update the week's status
            self.session.execute(
                text("""
                    UPDATE weeks
                    SET status = :status, updated_at = :updated_at
                    WHERE id = :week_id
                """),
                {
                    "week_id": week_id,
                    "status": override_status,
                    "updated_at": datetime.now(),
                }
            )
            self.session.commit()
            updated_count += 1

        logger.info(f"Updated statuses for {updated_count} weeks in season {season}")
        return updated_count
