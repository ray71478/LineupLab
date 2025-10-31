"""
WeekManagementService for managing NFL weeks and seasons.

Provides core business logic for:
- Creating weeks for a season from NFL schedule
- Retrieving weeks with metadata and status
- Getting the current active week
- Locking weeks (preventing modifications after import)
- Validating week immutability
- Updating week status with manual overrides
"""

import logging
from datetime import datetime, date, time
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.exceptions import CortexException

logger = logging.getLogger(__name__)


class WeekLockedError(CortexException):
    """Raised when trying to modify a locked week."""

    def __init__(self, week_number: int):
        """
        Initialize WeekLockedError.

        Args:
            week_number: The week number that is locked
        """
        super().__init__(
            f"Week {week_number} is locked due to imported data. "
            f"Cannot modify weeks with imported player pools.",
            status_code=409
        )


class WeekNotFoundError(CortexException):
    """Raised when a week doesn't exist."""

    def __init__(self, week_id: int):
        """
        Initialize WeekNotFoundError.

        Args:
            week_id: The week ID that was not found
        """
        super().__init__(
            f"Week {week_id} not found",
            status_code=404
        )


class InvalidYearError(CortexException):
    """Raised when year is invalid."""

    def __init__(self, year: int):
        """
        Initialize InvalidYearError.

        Args:
            year: The invalid year
        """
        super().__init__(
            f"Year {year} is invalid. Must be between 2025 and 2030.",
            status_code=400
        )


class WeekManagementService:
    """Service for managing NFL weeks and seasons."""

    def __init__(self, session: Session):
        """
        Initialize WeekManagementService.

        Args:
            session: SQLAlchemy Session for database operations
        """
        self.session = session

    def create_weeks_for_season(self, year: int) -> int:
        """
        Create 18 weeks for a given NFL season.

        Queries the nfl_schedule table for the year and creates Week records
        with associated week_metadata.

        Args:
            year: NFL season year (e.g., 2025)

        Returns:
            Count of created weeks (18 if successful)

        Raises:
            InvalidYearError: If year is not between 2025 and 2030
            CortexException: If weeks already exist for year (unless forced)
        """
        # Validate year
        if not (2025 <= year <= 2030):
            raise InvalidYearError(year)

        # Check if weeks already exist for this year
        result = self.session.execute(
            text("SELECT COUNT(*) FROM weeks WHERE season = :season"),
            {"season": year}
        )
        existing_count = result.scalar()
        if existing_count > 0:
            logger.warning(f"Weeks already exist for season {year}. Skipping creation.")
            return 0

        # Get NFL schedule for this year
        result = self.session.execute(
            text("""
                SELECT season, week, slate_date, kickoff_time, game_count, is_playoff
                FROM nfl_schedule
                WHERE season = :season
                ORDER BY week ASC
            """),
            {"season": year}
        )
        schedule_rows = result.fetchall()

        if not schedule_rows:
            logger.error(f"No NFL schedule data found for season {year}")
            raise CortexException(
                f"NFL schedule data not found for season {year}",
                status_code=500
            )

        # Create weeks
        created_count = 0
        for schedule_row in schedule_rows:
            season, week_num, slate_date, kickoff_time, game_count, is_playoff = schedule_row

            try:
                # Insert week
                result = self.session.execute(
                    text("""
                        INSERT INTO weeks (season, week_number, status, nfl_slate_date)
                        VALUES (:season, :week_number, :status, :nfl_slate_date)
                        RETURNING id
                    """),
                    {
                        "season": season,
                        "week_number": week_num,
                        "status": "upcoming",
                        "nfl_slate_date": slate_date,
                    }
                )
                self.session.commit()
                week_id = result.scalar()

                # Generate ESPN link
                espn_link = self._generate_espn_link(week_num, year)

                # Insert week_metadata
                self.session.execute(
                    text("""
                        INSERT INTO week_metadata
                        (week_id, season, week_number, nfl_slate_date, kickoff_time, espn_schedule_url)
                        VALUES (:week_id, :season, :week_number, :nfl_slate_date, :kickoff_time, :espn_url)
                    """),
                    {
                        "week_id": week_id,
                        "season": season,
                        "week_number": week_num,
                        "nfl_slate_date": slate_date,
                        "kickoff_time": kickoff_time,
                        "espn_url": espn_link,
                    }
                )
                self.session.commit()
                created_count += 1

            except Exception as e:
                self.session.rollback()
                logger.error(f"Error creating week {week_num} for season {year}: {str(e)}")
                raise

        logger.info(f"Created {created_count} weeks for season {year}")
        return created_count

    def get_weeks_by_year(self, year: int) -> List[Dict[str, Any]]:
        """
        Get all weeks for a given year with metadata and status.

        Retrieves all 18 weeks, enriches with metadata, calculates current status,
        and applies manual overrides.

        Args:
            year: NFL season year (e.g., 2025)

        Returns:
            List of week dictionaries sorted by week_number, each containing:
            - id, season, week_number, status, status_override, nfl_slate_date
            - is_locked, locked_at, metadata (with kickoff_time, espn_link, etc.)

        Raises:
            InvalidYearError: If year is not valid
        """
        # Validate year
        if not (2025 <= year <= 2030):
            raise InvalidYearError(year)

        # Query weeks with metadata and status overrides in a single query to avoid N+1 problem
        result = self.session.execute(
            text("""
                SELECT w.id, w.season, w.week_number, w.status, w.status_override,
                       w.nfl_slate_date, w.is_locked, w.locked_at,
                       wm.kickoff_time, wm.espn_schedule_url, wm.import_status, 
                       wm.import_count, wm.import_timestamp,
                       wso.override_status
                FROM weeks w
                LEFT JOIN week_metadata wm ON w.id = wm.week_id
                LEFT JOIN week_status_overrides wso ON w.id = wso.week_id
                WHERE w.season = :season
                ORDER BY w.week_number ASC
            """),
            {"season": year}
        )
        weeks_rows = result.fetchall()

        weeks = []
        for row in weeks_rows:
            week_id, season, week_number, status, status_override, nfl_slate_date, is_locked, locked_at, kickoff_time, espn_link, import_status, import_count, import_timestamp, override_status = row

            # Format kickoff_time to 12-hour format
            formatted_kickoff = None
            if kickoff_time:
                # kickoff_time is a time object, convert to 12-hour format
                hour = kickoff_time.hour
                minute = kickoff_time.minute
                period = "PM" if hour >= 12 else "AM"
                display_hour = hour if hour <= 12 else hour - 12
                if display_hour == 0:
                    display_hour = 12
                formatted_kickoff = f"{display_hour}:{minute:02d} {period} ET"
            
            if espn_link or import_status or import_count or import_timestamp:
                metadata = {
                    "kickoff_time": formatted_kickoff,
                    "espn_link": espn_link,
                    "import_status": import_status or "pending",
                    "import_count": import_count or 0,
                    "import_timestamp": self._to_iso_format(import_timestamp),
                }
            else:
                metadata = {
                    "kickoff_time": formatted_kickoff,
                    "espn_link": None,
                    "import_status": "pending",
                    "import_count": 0,
                    "import_timestamp": None,
                }

            # Apply status override (now from JOIN, no extra query needed)
            final_status = override_status if override_status else status
            # Still need to check date-based status calculation if no override
            if not override_status:
                final_status = self._calculate_status_from_date(nfl_slate_date, status)

            week_dict = {
                "id": week_id,
                "season": season,
                "week_number": week_number,
                "status": final_status,
                "status_override": status_override,
                "nfl_slate_date": str(nfl_slate_date) if nfl_slate_date else None,
                "is_locked": bool(is_locked),
                "locked_at": self._to_iso_format(locked_at),
                "metadata": metadata,
            }
            weeks.append(week_dict)

        return weeks

    def get_current_week(self) -> Optional[Dict[str, Any]]:
        """
        Get the current active week based on today's date.

        Queries nfl_schedule to find the week containing today's date,
        checks for status overrides, and returns full week details.

        Returns:
            Week dictionary with all details, or None if no current week found

        Raises:
            CortexException: If no weeks found for current year
        """
        today = date.today()
        current_year = today.year

        # If before September, use previous year's season
        if today.month < 9:
            current_year -= 1

        # Find week with current date in nfl_schedule
        result = self.session.execute(
            text("""
                SELECT season, week, slate_date
                FROM nfl_schedule
                WHERE season = :season
                AND slate_date <= :today
                ORDER BY slate_date DESC
                LIMIT 1
            """),
            {"season": current_year, "today": today}
        )
        schedule_row = result.fetchone()

        if not schedule_row:
            # No past weeks, find first week of season
            result = self.session.execute(
                text("""
                    SELECT season, week, slate_date
                    FROM nfl_schedule
                    WHERE season = :season
                    ORDER BY week ASC
                    LIMIT 1
                """),
                {"season": current_year}
            )
            schedule_row = result.fetchone()

        if not schedule_row:
            raise CortexException(
                f"No NFL schedule found for current season {current_year}",
                status_code=500
            )

        season, week_num, slate_date = schedule_row

        # Get week details
        result = self.session.execute(
            text("""
                SELECT w.id, w.season, w.week_number, w.status, w.status_override,
                       w.nfl_slate_date, w.is_locked, w.locked_at
                FROM weeks w
                WHERE w.season = :season AND w.week_number = :week_number
            """),
            {"season": season, "week_number": week_num}
        )
        week_row = result.fetchone()

        if not week_row:
            raise CortexException(
                f"Week {week_num} not found for season {season}",
                status_code=404
            )

        week_id, w_season, w_week_number, status, status_override, nfl_slate_date, is_locked, locked_at = week_row

        # Get week metadata
        metadata_result = self.session.execute(
            text("""
                SELECT kickoff_time, espn_schedule_url, import_status, import_count, import_timestamp
                FROM week_metadata
                WHERE week_id = :week_id
            """),
            {"week_id": week_id}
        )
        metadata_row = metadata_result.fetchone()

        if metadata_row:
            kickoff_time, espn_link, import_status, import_count, import_timestamp = metadata_row
            metadata = {
                "kickoff_time": str(kickoff_time) if kickoff_time else None,
                "espn_link": espn_link,
                "import_status": import_status,
                "import_count": import_count,
                "import_timestamp": self._to_iso_format(import_timestamp),
            }
        else:
            metadata = {
                "kickoff_time": None,
                "espn_link": None,
                "import_status": "pending",
                "import_count": 0,
                "import_timestamp": None,
            }

        # Apply status override
        final_status = self._apply_status_override(week_id, nfl_slate_date, status)

        return {
            "id": week_id,
            "season": w_season,
            "week_number": w_week_number,
            "status": final_status,
            "status_override": status_override,
            "nfl_slate_date": str(nfl_slate_date) if nfl_slate_date else None,
            "is_locked": bool(is_locked),
            "locked_at": self._to_iso_format(locked_at),
            "metadata": metadata,
        }

    def lock_week(self, week_id: int, import_id: str, player_count: int) -> Dict[str, Any]:
        """
        Lock a week to prevent modifications after data import.

        Sets is_locked=true, locked_at=NOW(), and updates week_metadata
        with import status.

        Args:
            week_id: ID of week to lock
            import_id: UUID of the import that triggered the lock
            player_count: Number of players imported

        Returns:
            Updated week dictionary with lock information

        Raises:
            WeekNotFoundError: If week doesn't exist
        """
        # Verify week exists
        result = self.session.execute(
            text("SELECT id, week_number FROM weeks WHERE id = :id"),
            {"id": week_id}
        )
        week_row = result.fetchone()

        if not week_row:
            raise WeekNotFoundError(week_id)

        week_number = week_row[1]

        # Lock the week
        self.session.execute(
            text("""
                UPDATE weeks
                SET is_locked = true, locked_at = :locked_at, updated_at = :updated_at
                WHERE id = :id
            """),
            {
                "id": week_id,
                "locked_at": datetime.now(),
                "updated_at": datetime.now(),
            }
        )
        self.session.commit()

        # Update week_metadata with import status
        self.session.execute(
            text("""
                UPDATE week_metadata
                SET import_status = :import_status,
                    import_count = :import_count,
                    import_timestamp = :import_timestamp,
                    updated_at = :updated_at
                WHERE week_id = :week_id
            """),
            {
                "week_id": week_id,
                "import_status": "imported",
                "import_count": player_count,
                "import_timestamp": datetime.now(),
                "updated_at": datetime.now(),
            }
        )
        self.session.commit()

        logger.info(f"Week {week_number} locked with import {import_id} ({player_count} players)")

        # Return updated week
        result = self.session.execute(
            text("""
                SELECT w.id, w.season, w.week_number, w.status, w.status_override,
                       w.nfl_slate_date, w.is_locked, w.locked_at
                FROM weeks w
                WHERE w.id = :id
            """),
            {"id": week_id}
        )
        week_row = result.fetchone()

        week_id, season, week_number, status, status_override, nfl_slate_date, is_locked, locked_at = week_row

        # Get updated metadata
        metadata_result = self.session.execute(
            text("""
                SELECT kickoff_time, espn_schedule_url, import_status, import_count, import_timestamp
                FROM week_metadata
                WHERE week_id = :week_id
            """),
            {"week_id": week_id}
        )
        metadata_row = metadata_result.fetchone()

        if metadata_row:
            kickoff_time, espn_link, import_status, import_count, import_timestamp = metadata_row
            metadata = {
                "kickoff_time": str(kickoff_time) if kickoff_time else None,
                "espn_link": espn_link,
                "import_status": import_status,
                "import_count": import_count,
                "import_timestamp": self._to_iso_format(import_timestamp),
            }
        else:
            metadata = {}

        final_status = self._apply_status_override(week_id, nfl_slate_date, status)

        return {
            "id": week_id,
            "season": season,
            "week_number": week_number,
            "status": final_status,
            "status_override": status_override,
            "nfl_slate_date": str(nfl_slate_date) if nfl_slate_date else None,
            "is_locked": bool(is_locked),
            "locked_at": self._to_iso_format(locked_at),
            "metadata": metadata,
        }

    def validate_week_immutability(self, week_id: int) -> None:
        """
        Validate that a week is not locked.

        Used by API endpoints before allowing modifications.

        Args:
            week_id: ID of week to validate

        Raises:
            WeekNotFoundError: If week doesn't exist
            WeekLockedError: If week is locked
        """
        result = self.session.execute(
            text("SELECT is_locked, week_number FROM weeks WHERE id = :id"),
            {"id": week_id}
        )
        row = result.fetchone()

        if not row:
            raise WeekNotFoundError(week_id)

        is_locked, week_number = row

        if is_locked:
            raise WeekLockedError(week_number)

    def update_week_status(self, week_id: int, new_status: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Update week status with manual override.

        Creates or updates a week_status_overrides record and updates
        the week's status_override column.

        Args:
            week_id: ID of week to update
            new_status: New status ('active', 'upcoming', 'completed')
            reason: Optional reason for override

        Returns:
            Updated week dictionary

        Raises:
            WeekNotFoundError: If week doesn't exist
            CortexException: If status is invalid
        """
        # Validate status
        valid_statuses = ["active", "upcoming", "completed"]
        if new_status not in valid_statuses:
            raise CortexException(
                f"Invalid status '{new_status}'. Must be one of: {', '.join(valid_statuses)}",
                status_code=400
            )

        # Verify week exists
        result = self.session.execute(
            text("SELECT id, week_number FROM weeks WHERE id = :id"),
            {"id": week_id}
        )
        week_row = result.fetchone()

        if not week_row:
            raise WeekNotFoundError(week_id)

        week_number = week_row[1]

        # Update week status_override column
        self.session.execute(
            text("""
                UPDATE weeks
                SET status_override = :status, updated_at = :updated_at
                WHERE id = :id
            """),
            {
                "id": week_id,
                "status": new_status,
                "updated_at": datetime.now(),
            }
        )
        self.session.commit()

        # Create or update week_status_overrides record
        existing_override = self.session.execute(
            text("SELECT id FROM week_status_overrides WHERE week_id = :week_id"),
            {"week_id": week_id}
        ).scalar()

        if existing_override:
            # Update existing override
            self.session.execute(
                text("""
                    UPDATE week_status_overrides
                    SET override_status = :status, reason = :reason, updated_at = :updated_at
                    WHERE week_id = :week_id
                """),
                {
                    "week_id": week_id,
                    "status": new_status,
                    "reason": reason,
                    "updated_at": datetime.now(),
                }
            )
        else:
            # Create new override
            self.session.execute(
                text("""
                    INSERT INTO week_status_overrides (week_id, override_status, reason)
                    VALUES (:week_id, :status, :reason)
                """),
                {
                    "week_id": week_id,
                    "status": new_status,
                    "reason": reason,
                }
            )

        self.session.commit()

        logger.info(f"Week {week_number} status override updated to '{new_status}'")

        # Return updated week
        result = self.session.execute(
            text("""
                SELECT w.id, w.season, w.week_number, w.status, w.status_override,
                       w.nfl_slate_date, w.is_locked, w.locked_at
                FROM weeks w
                WHERE w.id = :id
            """),
            {"id": week_id}
        )
        week_row = result.fetchone()

        week_id, season, week_number, status, status_override, nfl_slate_date, is_locked, locked_at = week_row

        # Get metadata
        metadata_result = self.session.execute(
            text("""
                SELECT kickoff_time, espn_schedule_url, import_status, import_count, import_timestamp
                FROM week_metadata
                WHERE week_id = :week_id
            """),
            {"week_id": week_id}
        )
        metadata_row = metadata_result.fetchone()

        if metadata_row:
            kickoff_time, espn_link, import_status, import_count, import_timestamp = metadata_row
            metadata = {
                "kickoff_time": str(kickoff_time) if kickoff_time else None,
                "espn_link": espn_link,
                "import_status": import_status,
                "import_count": import_count,
                "import_timestamp": self._to_iso_format(import_timestamp),
            }
        else:
            metadata = {}

        final_status = self._apply_status_override(week_id, nfl_slate_date, status)

        return {
            "id": week_id,
            "season": season,
            "week_number": week_number,
            "status": final_status,
            "status_override": status_override,
            "nfl_slate_date": str(nfl_slate_date) if nfl_slate_date else None,
            "is_locked": bool(is_locked),
            "locked_at": self._to_iso_format(locked_at),
            "metadata": metadata,
        }

    def _apply_status_override(self, week_id: int, nfl_slate_date: Optional[date], calculated_status: str) -> str:
        """
        Apply manual status override if it exists, otherwise use calculated status.

        Args:
            week_id: ID of week
            nfl_slate_date: NFL slate date for auto-calculation
            calculated_status: Auto-calculated status from database

        Returns:
            Final status (either override or calculated)
        """
        # Check for manual override
        result = self.session.execute(
            text("SELECT override_status FROM week_status_overrides WHERE week_id = :week_id"),
            {"week_id": week_id}
        )
        override_row = result.fetchone()

        if override_row:
            return override_row[0]

        return calculated_status
    
    def _calculate_status_from_date(self, nfl_slate_date: Optional[date], default_status: str) -> str:
        """
        Calculate status based on date if no override exists.
        
        Args:
            nfl_slate_date: NFL slate date for the week
            default_status: Default status from database
            
        Returns:
            Calculated status
        """
        if not nfl_slate_date:
            return default_status
        
        today = date.today()
        
        # If slate date is in the future, status is "upcoming"
        if nfl_slate_date > today:
            return "upcoming"
        # If slate date is today or in the past, status is "completed" or "active"
        elif nfl_slate_date < today:
            return "completed"
        else:
            return "active"

    def _generate_espn_link(self, week_number: int, year: int) -> str:
        """
        Generate ESPN schedule link for a week.

        Args:
            week_number: Week number (1-18)
            year: Season year (e.g., 2025)

        Returns:
            ESPN schedule URL
        """
        return f"https://www.espn.com/nfl/schedule/_/week/{week_number}/year/{year}"

    def _to_iso_format(self, value: Any) -> Optional[str]:
        """
        Convert a datetime value to ISO format string.

        Handles both datetime objects and string representations.

        Args:
            value: Datetime object or string to convert

        Returns:
            ISO format string or None if value is None
        """
        if value is None:
            return None

        if isinstance(value, str):
            # Already a string, try to parse and reformat
            try:
                # Try parsing as ISO format
                if 'T' in value:
                    dt = datetime.fromisoformat(value)
                else:
                    # Try other common formats
                    dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                return dt.isoformat()
            except Exception:
                # If parsing fails, return as-is
                return value

        if isinstance(value, datetime):
            return value.isoformat()

        # For other types, convert to string
        return str(value)
