"""
Backend services module for Cortex application.

Provides core business logic services for:
- Data import and validation
- Player matching and normalization
- Import history tracking
- Week management
"""

__all__ = [
    "DataImporter",
    "PlayerMatcher",
    "ImportHistoryTracker",
    "ValidationService",
    "WeekManagementService",
]


def __getattr__(name):
    """Lazy load services to avoid circular dependencies."""
    if name == "DataImporter":
        from backend.services.data_importer import DataImporter
        return DataImporter
    elif name == "PlayerMatcher":
        from backend.services.player_matcher import PlayerMatcher
        return PlayerMatcher
    elif name == "ImportHistoryTracker":
        from backend.services.import_history_tracker import ImportHistoryTracker
        return ImportHistoryTracker
    elif name == "ValidationService":
        from backend.services.validation_service import ValidationService
        return ValidationService
    elif name == "WeekManagementService":
        from backend.services.week_management_service import WeekManagementService
        return WeekManagementService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
