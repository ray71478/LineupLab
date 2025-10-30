"""
Unit tests for NFLScheduleService.

Tests the NFL schedule service functionality including:
- Getting NFL schedule for a year
- Retrieving week metadata
- Generating ESPN schedule links
"""

import pytest
from datetime import date, time
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.services.nfl_schedule_service import NFLScheduleService


class TestGetNFLSchedule:
    """Tests for get_nfl_schedule() method."""

    def test_get_nfl_schedule_returns_all_weeks_for_year(self, db_session: Session):
        """Test that get_nfl_schedule() returns all 18 weeks for a year."""
        service = NFLScheduleService(db_session)

        # Get schedule for 2025
        schedule = service.get_nfl_schedule(2025)

        # Should return 18 weeks
        assert len(schedule) == 18
        assert all(isinstance(week, dict) for week in schedule)

    def test_get_nfl_schedule_returns_correct_fields(self, db_session: Session):
        """Test that get_nfl_schedule() returns all required fields."""
        service = NFLScheduleService(db_session)

        schedule = service.get_nfl_schedule(2025)

        # Check first week has required fields
        week1 = schedule[0]
        assert "week" in week1
        assert "slate_date" in week1
        assert "kickoff_time" in week1
        assert "game_count" in week1

    def test_get_nfl_schedule_sorted_by_week(self, db_session: Session):
        """Test that get_nfl_schedule() returns weeks sorted by week number."""
        service = NFLScheduleService(db_session)

        schedule = service.get_nfl_schedule(2025)

        # Verify weeks are in order 1-18
        week_numbers = [week["week"] for week in schedule]
        assert week_numbers == list(range(1, 19))

    def test_get_nfl_schedule_week_1_details(self, db_session: Session):
        """Test that Week 1 has correct details."""
        service = NFLScheduleService(db_session)

        schedule = service.get_nfl_schedule(2025)
        week1 = schedule[0]

        assert week1["week"] == 1
        assert week1["slate_date"] == date(2025, 9, 7)
        assert week1["kickoff_time"] == time(13, 0)
        assert week1["game_count"] == 16

    def test_get_nfl_schedule_week_12_thanksgiving(self, db_session: Session):
        """Test that Week 12 (Thanksgiving) has correct kickoff time."""
        service = NFLScheduleService(db_session)

        schedule = service.get_nfl_schedule(2025)
        week12 = schedule[11]

        assert week12["week"] == 12
        # Thanksgiving has earlier kickoff
        assert week12["kickoff_time"] == time(12, 30)

    def test_get_nfl_schedule_year_2026(self, db_session: Session):
        """Test that get_nfl_schedule() works for different years."""
        service = NFLScheduleService(db_session)

        schedule = service.get_nfl_schedule(2026)

        assert len(schedule) == 18
        # First week should be in September 2026
        week1 = schedule[0]
        assert week1["week"] == 1
        assert week1["slate_date"].year == 2026
        assert week1["slate_date"].month == 9


class TestGetWeekMetadata:
    """Tests for get_week_metadata() method."""

    def test_get_week_metadata_returns_all_fields(self, db_session: Session):
        """Test that get_week_metadata() returns all required metadata fields."""
        service = NFLScheduleService(db_session)

        # Create a week first
        db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status, nfl_slate_date)
                VALUES (:season, :week_number, :status, :nfl_slate_date)
            """),
            {
                "season": 2025,
                "week_number": 5,
                "status": "active",
                "nfl_slate_date": date(2025, 10, 5),
            }
        )
        db_session.commit()

        # Get the week ID
        result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = 2025 AND week_number = 5")
        )
        week_id = result.scalar()

        # Create week_metadata (use string format for time)
        db_session.execute(
            text("""
                INSERT INTO week_metadata
                (week_id, season, week_number, nfl_slate_date, kickoff_time, espn_schedule_url, import_status)
                VALUES (:week_id, :season, :week_number, :nfl_slate_date, :kickoff_time, :espn_url, :import_status)
            """),
            {
                "week_id": week_id,
                "season": 2025,
                "week_number": 5,
                "nfl_slate_date": date(2025, 10, 5),
                "kickoff_time": "13:00",  # Use string format for SQLite
                "espn_url": "https://www.espn.com/nfl/schedule/_/week/5/year/2025",
                "import_status": "imported",
            }
        )
        db_session.commit()

        # Get metadata
        metadata = service.get_week_metadata(week_id)

        assert metadata is not None
        assert "nfl_slate_date" in metadata
        assert "kickoff_time" in metadata
        assert "espn_link" in metadata
        assert "import_status" in metadata
        assert "import_count" in metadata
        assert "import_timestamp" in metadata

    def test_get_week_metadata_correct_kickoff_time(self, db_session: Session):
        """Test that get_week_metadata() returns correct kickoff time."""
        service = NFLScheduleService(db_session)

        # Create a week
        db_session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status, nfl_slate_date)
                VALUES (:season, :week_number, :status, :nfl_slate_date)
            """),
            {
                "season": 2025,
                "week_number": 3,
                "status": "upcoming",
                "nfl_slate_date": date(2025, 9, 21),
            }
        )
        db_session.commit()

        # Get the week ID
        result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = 2025 AND week_number = 3")
        )
        week_id = result.scalar()

        # Create week_metadata (use string format for time)
        db_session.execute(
            text("""
                INSERT INTO week_metadata
                (week_id, season, week_number, nfl_slate_date, kickoff_time, espn_schedule_url)
                VALUES (:week_id, :season, :week_number, :nfl_slate_date, :kickoff_time, :espn_url)
            """),
            {
                "week_id": week_id,
                "season": 2025,
                "week_number": 3,
                "nfl_slate_date": date(2025, 9, 21),
                "kickoff_time": "13:00",  # Use string format for SQLite
                "espn_url": "https://www.espn.com/nfl/schedule/_/week/3/year/2025",
            }
        )
        db_session.commit()

        # Get metadata
        metadata = service.get_week_metadata(week_id)

        assert metadata["kickoff_time"] == "13:00"
        assert metadata["nfl_slate_date"] == date(2025, 9, 21)


class TestGenerateESPNLink:
    """Tests for generate_espn_link() method."""

    def test_generate_espn_link_creates_valid_url_format(self, db_session: Session):
        """Test that generate_espn_link() creates valid URL format."""
        service = NFLScheduleService(db_session)

        link = service.generate_espn_link(week_number=5, season=2025)

        assert isinstance(link, str)
        assert "https://www.espn.com/nfl/schedule" in link
        assert "week/5" in link
        assert "year/2025" in link

    def test_generate_espn_link_exact_format(self, db_session: Session):
        """Test that generate_espn_link() produces exact expected format."""
        service = NFLScheduleService(db_session)

        link = service.generate_espn_link(week_number=5, season=2025)

        expected = "https://www.espn.com/nfl/schedule/_/week/5/year/2025"
        assert link == expected

    def test_generate_espn_link_week_1(self, db_session: Session):
        """Test that generate_espn_link() works for Week 1."""
        service = NFLScheduleService(db_session)

        link = service.generate_espn_link(week_number=1, season=2025)

        assert link == "https://www.espn.com/nfl/schedule/_/week/1/year/2025"

    def test_generate_espn_link_week_18(self, db_session: Session):
        """Test that generate_espn_link() works for Week 18."""
        service = NFLScheduleService(db_session)

        link = service.generate_espn_link(week_number=18, season=2025)

        assert link == "https://www.espn.com/nfl/schedule/_/week/18/year/2025"

    def test_generate_espn_link_different_year(self, db_session: Session):
        """Test that generate_espn_link() works for different years."""
        service = NFLScheduleService(db_session)

        link = service.generate_espn_link(week_number=5, season=2026)

        assert link == "https://www.espn.com/nfl/schedule/_/week/5/year/2026"
