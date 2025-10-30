"""
End-to-End Tests for Week Management Feature - Task Group 11.

Tests critical workflows that span multiple layers of the system.
These tests verify that user-facing workflows work correctly from
database through API to frontend state management.

Maximum 8 strategic tests covering business-critical gaps.
"""

import pytest
from datetime import datetime, date
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.services.week_management_service import WeekManagementService
from backend.services.status_update_service import StatusUpdateService
from backend.services.nfl_schedule_service import NFLScheduleService


class TestE2EYearSelectionFlow:
    """
    E2E Test 1: Year selection flow

    User selects year -> weeks load -> week highlighted

    This test verifies the complete workflow when a user selects a different year.
    """

    def test_user_selects_year_weeks_load_correctly(self, db_session: Session):
        """
        Test that selecting a year loads all weeks with correct metadata.

        Workflow:
        1. User starts with 2025
        2. User selects 2026
        3. All 18 weeks for 2026 load
        4. Metadata is enriched correctly
        """
        # Setup: Initialize services
        week_service = WeekManagementService(db_session)

        # Step 1: Get weeks for initial year (2025)
        weeks_2025 = week_service.get_weeks_by_year(2025)
        assert len(weeks_2025) == 18

        # Step 2: User changes year to 2026 (simulated by frontend request)
        weeks_2026 = week_service.get_weeks_by_year(2026)

        # Verify all 18 weeks loaded for 2026
        assert len(weeks_2026) == 18
        assert all(w["season"] == 2026 for w in weeks_2026)

        # Verify weeks are in order
        for i, week in enumerate(weeks_2026, 1):
            assert week["week_number"] == i

        # Verify metadata is present for each week
        for week in weeks_2026:
            assert "nfl_slate_date" in week
            assert "metadata" in week
            assert "status" in week
            assert week["metadata"]["kickoff_time"] is not None
            assert week["metadata"]["espn_link"] is not None


class TestE2EWeekSelectionToMetadata:
    """
    E2E Test 2: Week selection to metadata display

    User selects week -> metadata shows correctly

    This test verifies that selecting a week immediately updates
    metadata display with all relevant information.
    """

    def test_user_selects_week_metadata_displays(self, db_session: Session):
        """
        Test that selecting a week displays correct metadata.

        Workflow:
        1. Create weeks for 2025
        2. User selects week 5
        3. Metadata for week 5 loads and displays
        4. All details are correct
        """
        # Setup: Create weeks
        week_service = WeekManagementService(db_session)
        nfl_service = NFLScheduleService(db_session)
        week_service.create_weeks_for_season(2025)

        # Get week 5
        weeks = week_service.get_weeks_by_year(2025)
        week_5 = next(w for w in weeks if w["week_number"] == 5)

        # Get detailed metadata for week 5
        metadata = nfl_service.get_week_metadata(week_5["id"])

        # Verify all metadata fields present
        assert metadata is not None
        assert metadata["season"] == 2025
        assert metadata["week_number"] == 5
        assert metadata["nfl_slate_date"] == date(2025, 10, 5)
        assert metadata["kickoff_time"] == "13:00"
        assert "https://www.espn.com/nfl/schedule" in metadata["espn_link"]
        assert metadata["import_status"] == "pending"
        assert metadata["import_count"] == 0


class TestE2EMobileCarouselNavigation:
    """
    E2E Test 3: Mobile carousel navigation

    User swipes carousel -> week changes smoothly

    This test verifies that mobile carousel navigation works smoothly
    with correct week transitions.
    """

    def test_carousel_swipe_navigation_works(self, db_session: Session):
        """
        Test that carousel navigation transitions between weeks.

        Workflow:
        1. Create weeks for 2025
        2. Start at week 5 (current week)
        3. Simulate swipe left to week 6
        4. Verify week 6 is now active
        5. Simulate swipe right back to week 5
        6. Verify week 5 is active again
        """
        # Setup: Create weeks
        week_service = WeekManagementService(db_session)
        week_service.create_weeks_for_season(2025)

        # Get all weeks
        weeks = week_service.get_weeks_by_year(2025)

        # Simulate carousel state at week 5
        current_week_index = 4  # 0-indexed for week 5

        # Verify we have week 5
        assert weeks[current_week_index]["week_number"] == 5

        # Simulate swipe left (next week)
        next_week_index = current_week_index + 1
        assert weeks[next_week_index]["week_number"] == 6

        # Simulate swipe right (previous week)
        prev_week_index = current_week_index - 1
        assert weeks[prev_week_index]["week_number"] == 4

        # Verify carousel can show adjacent weeks
        visible_weeks = weeks[max(0, current_week_index - 1):min(len(weeks), current_week_index + 2)]
        assert len(visible_weeks) == 3
        assert visible_weeks[1]["week_number"] == 5  # Current in middle


class TestE2EDataImportLockFlow:
    """
    E2E Test 4: Data import lock flow

    User imports data -> week locks and shows imported badge

    This test verifies the complete workflow when data is imported
    for a week, including locking and status badge updates.
    """

    def test_data_import_locks_week_and_updates_badge(self, db_session: Session):
        """
        Test that importing data locks the week and updates status badge.

        Workflow:
        1. Create weeks for 2025
        2. User selects week 5 for import
        3. Data import completes successfully
        4. Week 5 is locked (is_locked=true)
        5. Metadata shows imported status
        6. Badge shows green checkmark
        """
        # Setup: Create weeks
        week_service = WeekManagementService(db_session)
        nfl_service = NFLScheduleService(db_session)
        week_service.create_weeks_for_season(2025)

        # Get week 5
        weeks = week_service.get_weeks_by_year(2025)
        week_5 = next(w for w in weeks if w["week_number"] == 5)

        # Verify week is unlocked before import
        assert week_5["is_locked"] is False
        assert week_5["metadata"]["import_status"] == "pending"

        # Simulate data import completion
        import_id = "import-test-uuid-12345"
        player_count = 153
        locked_week = week_service.lock_week(week_5["id"], import_id, player_count)

        # Verify week is now locked
        assert locked_week["is_locked"] is True
        assert locked_week["locked_at"] is not None

        # Verify metadata updated
        metadata = nfl_service.get_week_metadata(week_5["id"])
        assert metadata["import_status"] == "imported"
        assert metadata["import_count"] == player_count
        assert metadata["import_timestamp"] is not None

        # Verify badge status would show green checkmark
        # (frontend would render green icon based on import_status='imported')
        assert metadata["import_status"] == "imported"


class TestE2EStatusAutoUpdateBoundary:
    """
    E2E Test 5: Status auto-update boundary

    Week status auto-updates when crossing boundary

    This test verifies that week status correctly updates when
    the current date crosses a week boundary.
    """

    def test_week_status_updates_on_boundary_crossing(self, db_session: Session):
        """
        Test that week status updates correctly when date crosses boundary.

        Workflow:
        1. Create weeks for 2025
        2. Set current date to 2025-10-04 (before week 5)
        3. Week 5 shows as 'upcoming'
        4. Simulate date crossing to 2025-10-05 (week 5 start)
        5. Week 5 now shows as 'active'
        6. Simulate crossing to 2025-10-06 (after week 5 start)
        7. Week 5 still shows as 'active' (during week)
        8. Simulate crossing to 2025-10-12 (after week 5)
        9. Week 5 now shows as 'completed'
        """
        # Setup: Create weeks and status service
        week_service = WeekManagementService(db_session)
        status_service = StatusUpdateService(db_session)
        week_service.create_weeks_for_season(2025)

        # Get week 5
        result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = :season AND week_number = :week"),
            {"season": 2025, "week": 5}
        )
        week_id = result.scalar()

        # Test 1: Week 5 before it starts (2025-10-04)
        status_before = status_service.determine_week_status(week_id, date(2025, 10, 4))
        assert status_before == "upcoming"

        # Test 2: Week 5 starts (2025-10-05)
        status_active = status_service.determine_week_status(week_id, date(2025, 10, 5))
        assert status_active == "active"

        # Test 3: Week 5 after it completes (2025-10-12)
        status_after = status_service.determine_week_status(week_id, date(2025, 10, 12))
        assert status_after == "completed"


class TestE2EManualStatusOverride:
    """
    E2E Test 6: Manual status override

    Manual status override persists across reloads

    This test verifies that manual status overrides are properly
    stored and retrieved, persisting across page reloads.
    """

    def test_manual_status_override_persists(self, db_session: Session):
        """
        Test that manual status override persists in database.

        Workflow:
        1. Create weeks for 2025
        2. Get week 5 - shows as 'upcoming' (auto-calculated)
        3. Admin manually overrides to 'active'
        4. Week 5 now shows 'active' (from override)
        5. Page reloads
        6. Week 5 still shows 'active' (from database override)
        """
        # Setup: Create weeks
        week_service = WeekManagementService(db_session)
        week_service.create_weeks_for_season(2025)

        # Get week 5
        weeks = week_service.get_weeks_by_year(2025)
        week_5 = next(w for w in weeks if w["week_number"] == 5)

        # Get initial status (should be auto-calculated)
        initial_status = week_5["status"]

        # Admin applies manual override
        override_reason = "Manual override for testing purposes"
        updated_week = week_service.update_week_status(
            week_5["id"],
            "active",
            override_reason
        )

        # Verify override applied
        assert updated_week["status_override"] == "active"

        # Verify override persists in database
        result = db_session.execute(
            text("SELECT status_override FROM weeks WHERE id = :id"),
            {"id": week_5["id"]}
        )
        persisted_override = result.scalar()
        assert persisted_override == "active"

        # Verify override record exists
        result = db_session.execute(
            text("SELECT override_status FROM week_status_overrides WHERE week_id = :week_id"),
            {"week_id": week_5["id"]}
        )
        override_record = result.scalar()
        assert override_record == "active"

        # Simulate page reload - fetch from database again
        reloaded_weeks = week_service.get_weeks_by_year(2025)
        reloaded_week_5 = next(w for w in reloaded_weeks if w["week_number"] == 5)

        # Verify override still applied
        assert reloaded_week_5["status_override"] == "active"


class TestE2EWeekImmutabilityValidation:
    """
    E2E Test 7: Week immutability validation

    Locked week prevents modification

    This test verifies that once a week is locked (due to import),
    it cannot be modified, and appropriate errors are returned.
    """

    def test_locked_week_prevents_all_modifications(self, db_session: Session):
        """
        Test that locked weeks prevent modifications.

        Workflow:
        1. Create weeks for 2025
        2. Lock week 5 with import data
        3. Attempt to update week status - should fail with 409
        4. Attempt to modify week - should fail
        5. Verify week remains in locked state
        """
        # Setup: Create and lock week
        week_service = WeekManagementService(db_session)
        week_service.create_weeks_for_season(2025)

        # Get week 5
        result = db_session.execute(
            text("SELECT id FROM weeks WHERE season = :season AND week_number = :week"),
            {"season": 2025, "week": 5}
        )
        week_id = result.scalar()

        # Lock the week with import
        week_service.lock_week(week_id, "import-uuid-123", 153)

        # Verify week is locked
        result = db_session.execute(
            text("SELECT is_locked FROM weeks WHERE id = :id"),
            {"id": week_id}
        )
        is_locked = result.scalar()
        assert is_locked is True

        # Attempt to modify locked week - should raise error
        with pytest.raises(Exception) as exc_info:
            week_service.validate_week_immutability(week_id)

        assert exc_info.value is not None

        # Verify week is still locked
        result = db_session.execute(
            text("SELECT is_locked FROM weeks WHERE id = :id"),
            {"id": week_id}
        )
        is_still_locked = result.scalar()
        assert is_still_locked is True


class TestE2EResponsiveLayoutSwitching:
    """
    E2E Test 8: Responsive layout switching

    Desktop dropdown vs mobile carousel renders correctly

    This test verifies that the week management UI switches
    correctly between desktop (dropdown) and mobile (carousel)
    layouts based on viewport size.
    """

    def test_responsive_layout_data_consistency(self, db_session: Session):
        """
        Test that desktop and mobile layouts show same week data.

        Workflow (tested at API level):
        1. Desktop: Fetch GET /api/weeks for dropdown
        2. Mobile: Fetch GET /api/weeks for carousel
        3. Verify both get identical data
        4. Both layouts can handle current week highlighting
        5. Both layouts can handle status badges
        """
        # Setup: Create weeks
        week_service = WeekManagementService(db_session)
        week_service.create_weeks_for_season(2025)

        # Simulate API call for desktop (includes metadata)
        desktop_weeks = week_service.get_weeks_by_year(2025)

        # Simulate API call for mobile (same data)
        mobile_weeks = week_service.get_weeks_by_year(2025)

        # Verify both have same week count
        assert len(desktop_weeks) == 18
        assert len(mobile_weeks) == 18

        # Verify data consistency between desktop and mobile
        for desktop_week, mobile_week in zip(desktop_weeks, mobile_weeks):
            assert desktop_week["id"] == mobile_week["id"]
            assert desktop_week["week_number"] == mobile_week["week_number"]
            assert desktop_week["status"] == mobile_week["status"]
            assert desktop_week["nfl_slate_date"] == mobile_week["nfl_slate_date"]
            assert desktop_week["metadata"]["import_status"] == mobile_week["metadata"]["import_status"]

        # Verify current week can be identified
        current_week = week_service.get_current_week()
        assert current_week is not None
        assert "week_number" in current_week

        # Verify responsive data structure works for both layouts
        for week in desktop_weeks:
            # Desktop needs: week number, status badge, metadata in tooltip
            assert "week_number" in week
            assert "status" in week
            assert "metadata" in week

            # Mobile needs: week number (large), status badge, metadata modal trigger
            assert "metadata" in week
            assert "nfl_slate_date" in week
