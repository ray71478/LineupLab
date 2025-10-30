"""
NFLScheduleService for managing NFL schedule data and metadata.

Provides core business logic for:
- Retrieving NFL schedule data for a season
- Getting week metadata with kickoff times and ESPN links
- Generating ESPN schedule links for weeks
"""

import logging
from datetime import date, time as time_type
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class NFLScheduleService:
    """Service for managing NFL schedule data."""

    def __init__(self, session: Session):
        """
        Initialize NFLScheduleService.

        Args:
            session: SQLAlchemy Session for database operations
        """
        self.session = session

    def get_nfl_schedule(self, year: int) -> List[Dict[str, Any]]:
        """
        Get NFL schedule for a given year.

        Retrieves all weeks from the nfl_schedule table for the specified season,
        including slate dates, kickoff times, and game counts.

        Args:
            year: NFL season year (e.g., 2025)

        Returns:
            List of dictionaries containing:
            - week: Week number (1-18)
            - slate_date: Date object of the NFL slate
            - kickoff_time: Time object of kickoff
            - game_count: Number of games in the week
            Sorted by week number in ascending order

        Raises:
            Exception: If no schedule found for the year
        """
        result = self.session.execute(
            text("""
                SELECT season, week, slate_date, kickoff_time, game_count, is_playoff
                FROM nfl_schedule
                WHERE season = :season
                ORDER BY week ASC
            """),
            {"season": year}
        )
        rows = result.fetchall()

        if not rows:
            logger.warning(f"No NFL schedule found for season {year}")
            return []

        schedule = []
        for row in rows:
            season, week, slate_date, kickoff_time, game_count, is_playoff = row

            # Parse the kickoff_time to ensure it's a time object
            if isinstance(kickoff_time, str):
                # Parse "HH:MM" format
                time_parts = kickoff_time.split(":")
                kickoff_time = time_type(int(time_parts[0]), int(time_parts[1]))

            # Parse the slate_date to ensure it's a date object
            if isinstance(slate_date, str):
                slate_date = date.fromisoformat(slate_date)

            schedule.append({
                "week": week,
                "slate_date": slate_date,
                "kickoff_time": kickoff_time,
                "game_count": game_count,
            })

        logger.info(f"Retrieved {len(schedule)} weeks from NFL schedule for season {year}")
        return schedule

    def get_week_metadata(self, week_id: int) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific week.

        Retrieves complete metadata for a week including NFL slate date,
        kickoff time, ESPN link, and import status information.

        Args:
            week_id: ID of the week

        Returns:
            Dictionary containing:
            - season: NFL season year
            - week_number: Week number (1-18)
            - nfl_slate_date: Date object
            - kickoff_time: Time object or string "HH:MM"
            - espn_link: ESPN schedule URL
            - import_status: Status of data import (pending/imported/error)
            - import_count: Number of players imported
            - import_timestamp: Timestamp of when import occurred
            - error_message: Error message if import failed (optional)
            Or None if week_metadata not found

        Raises:
            Exception: If week_id doesn't exist
        """
        # Verify week exists
        week_result = self.session.execute(
            text("SELECT id FROM weeks WHERE id = :week_id"),
            {"week_id": week_id}
        )
        if not week_result.scalar():
            logger.warning(f"Week {week_id} not found")
            return None

        # Get week_metadata
        result = self.session.execute(
            text("""
                SELECT season, week_number, nfl_slate_date, kickoff_time,
                       espn_schedule_url, import_status, import_count, import_timestamp, import_error_message
                FROM week_metadata
                WHERE week_id = :week_id
            """),
            {"week_id": week_id}
        )
        row = result.fetchone()

        if not row:
            logger.warning(f"No metadata found for week {week_id}")
            return None

        season, week_number, nfl_slate_date, kickoff_time, espn_link, import_status, import_count, import_timestamp, error_message = row

        # Parse the kickoff_time to ensure it's a string in "HH:MM" format
        if isinstance(kickoff_time, time_type):
            kickoff_time = f"{kickoff_time.hour:02d}:{kickoff_time.minute:02d}"
        elif isinstance(kickoff_time, str) and ":" not in kickoff_time:
            # Convert numeric time to "HH:MM" format if needed
            try:
                t = time_type.fromisoformat(kickoff_time)
                kickoff_time = f"{t.hour:02d}:{t.minute:02d}"
            except (ValueError, TypeError):
                pass

        # Parse the nfl_slate_date to ensure it's a date object
        if isinstance(nfl_slate_date, str):
            nfl_slate_date = date.fromisoformat(nfl_slate_date)

        # Convert import_timestamp to ISO format if it exists
        import_timestamp_str = None
        if import_timestamp:
            if isinstance(import_timestamp, str):
                import_timestamp_str = import_timestamp
            else:
                import_timestamp_str = import_timestamp.isoformat()

        metadata = {
            "season": season,
            "week_number": week_number,
            "nfl_slate_date": nfl_slate_date,
            "kickoff_time": kickoff_time,
            "espn_link": espn_link,
            "import_status": import_status or "pending",
            "import_count": import_count or 0,
            "import_timestamp": import_timestamp_str,
        }

        # Add error_message only if it exists
        if error_message:
            metadata["error_message"] = error_message

        logger.info(f"Retrieved metadata for week {week_number} (week_id={week_id})")
        return metadata

    def generate_espn_link(self, week_number: int, season: int) -> str:
        """
        Generate ESPN schedule link for a week.

        Creates a properly formatted ESPN schedule URL for the given week and season.

        Args:
            week_number: Week number (1-18)
            season: NFL season year (e.g., 2025)

        Returns:
            ESPN schedule URL as string
            Format: https://www.espn.com/nfl/schedule/_/week/{week}/year/{season}

        Example:
            >>> service.generate_espn_link(5, 2025)
            'https://www.espn.com/nfl/schedule/_/week/5/year/2025'
        """
        url = f"https://www.espn.com/nfl/schedule/_/week/{week_number}/year/{season}"
        logger.debug(f"Generated ESPN link for week {week_number}, season {season}: {url}")
        return url
