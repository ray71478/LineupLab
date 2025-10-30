"""
Data import API endpoints for LineStar, DraftKings, and Comprehensive Stats.

Handles file uploads, validation, fuzzy matching, and database insertion
with comprehensive error handling and transaction management.
"""

import logging
import re
from typing import Optional, Any

from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.exceptions import DataImportError
from backend.services.data_importer import DataImporter
from backend.services.import_history_tracker import ImportHistoryTracker
from backend.services.player_matcher import PlayerMatcher

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/import", tags=["import"])


# Placeholder - will be overridden by main.py
get_db = None


# Create a function that returns the current get_db function
# This is needed because Depends() captures the function at decoration time,
# so we need a wrapper that returns the latest get_db at runtime
def _get_current_db_dependency():
    """Get the current database dependency function."""
    import sys
    current_module = sys.modules[__name__]
    if current_module.get_db is None:
        raise RuntimeError("get_db not initialized. Make sure main.py has set up the dependency.")
    # Return the generator from get_db
    yield from current_module.get_db()


def detect_week_from_filename(filename: str, source: str) -> Optional[int]:
    """
    Detect week number from filename based on source type.

    Args:
        filename: Name of uploaded file
        source: Source type ('linestar', 'draftkings', 'comprehensive_stats')

    Returns:
        Week number (1-18) if detected, None otherwise
    """
    try:
        if source.lower() == "linestar":
            # Pattern: WK8, WK9, etc.
            match = re.search(r"WK(\d+)", filename, re.IGNORECASE)
            if match:
                return int(match.group(1))

        elif source.lower() == "draftkings":
            # Pattern: Week 8, Week 9, etc.
            match = re.search(r"Week\s+(\d+)", filename, re.IGNORECASE)
            if match:
                return int(match.group(1))

        elif source.lower() == "comprehensive_stats":
            # Pattern: throughWeek8, throughWeek9, etc.
            match = re.search(r"throughWeek(\d+)", filename, re.IGNORECASE)
            if match:
                return int(match.group(1))

    except Exception as e:
        logger.warning(f"Failed to detect week from filename '{filename}': {str(e)}")

    return None


def validate_week_number(week: int) -> None:
    """Validate week is in valid range (1-18)."""
    if not (1 <= week <= 18):
        raise DataImportError(f"Invalid week number: {week}. Must be between 1 and 18.")


def validate_file_extension(filename: str) -> None:
    """Validate file is .xlsx format."""
    if not filename.lower().endswith(".xlsx"):
        raise DataImportError("File must be .xlsx format")


@router.post("/linestar")
async def import_linestar(
    file: UploadFile = File(...),
    week_id: int = Form(...),
    detected_week: Optional[int] = Form(None),
    db: Any = Depends(_get_current_db_dependency),
) -> dict:
    """
    Import LineStar player data from XLSX file.

    Args:
        file: XLSX file upload
        week_id: Selected week number (1-18) from header
        detected_week: Week detected from filename (optional)
        db: Database session

    Returns:
        Import summary with player count and changes
    """
    try:
        # Validate inputs
        logger.info(f"Import request received: week_id={week_id} (type: {type(week_id)}), filename={file.filename}")
        validate_week_number(week_id)
        validate_file_extension(file.filename)

        # Find the week in any season (prefer most recent season)
        logger.info(f"Looking for week_number={week_id} in database")
        
        # Test database connection first
        try:
            test_result = db.execute(text("SELECT COUNT(*) FROM weeks")).scalar()
            logger.info(f"Database connection test: Found {test_result} total weeks")
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
        
        week_result = db.execute(
            text("""
                SELECT id, season FROM weeks
                WHERE week_number = :week_number
                ORDER BY season DESC
                LIMIT 1
            """),
            {"week_number": week_id}
        ).fetchone()
        
        # Debug: check what fetchone() actually returns
        logger.info(f"fetchone() result type: {type(week_result)}, value: {week_result}")
        
        if not week_result:
            # Log what weeks exist for debugging
            try:
                all_weeks = db.execute(
                    text("SELECT week_number, season FROM weeks ORDER BY season DESC, week_number ASC")
                ).fetchall()
                logger.warning(f"Week {week_id} not found. Available weeks: {all_weeks}")
            except Exception as e:
                logger.error(f"Error querying available weeks: {e}")
            return {
                "success": False,
                "error": f"Week {week_id} not found in database. Please ensure the week exists before importing.",
            }
        
        actual_week_id = week_result[0]
        season = week_result[1]
        logger.info(f"Found week {week_id}: id={actual_week_id}, season={season}")

        # Check for week mismatch
        detected = detect_week_from_filename(file.filename, "linestar")
        if detected and detected != week_id and detected_week is None:
            return {
                "success": False,
                "warning": "week_mismatch",
                "message": f"Filename suggests Week {detected}, but Week {week_id} selected",
                "detected_week": detected,
                "selected_week": week_id,
                "requires_confirmation": True,
            }

        # Initialize services
        importer = DataImporter(db)
        history_tracker = ImportHistoryTracker(db)
        matcher = PlayerMatcher(db)

        # Parse and validate file
        df = await importer.parse_xlsx(file, "linestar")
        df = importer.validate_data(df, "linestar")

        # Normalize players
        players = importer.normalize_players(df, "linestar")
        unmatched_count = 0

        # Fuzzy match players and handle unmatched
        matched_players = []
        for player in players:
            # Get existing players for matching
            stmt = text("""
                SELECT DISTINCT player_key, name, team, position
                FROM player_pools
                WHERE team = :team AND position = :position
            """)
            existing = db.execute(
                stmt,
                {"team": player.get("team"), "position": player.get("position")}
            ).fetchall()

            existing_list = [
                {
                    "player_key": row[0],
                    "name": row[1],
                    "team": row[2],
                    "position": row[3],
                }
                for row in existing
            ]

            # If no existing players, generate a player_key and import directly
            if not existing_list:
                player_key = matcher.generate_player_key(
                    player.get("name", ""),
                    player.get("team", ""),
                    player.get("position", ""),
                )
                player["player_key"] = player_key
                matched_players.append(player)
            else:
                # Try fuzzy match against existing players
                matched_key, similarity = matcher.fuzzy_match(
                    player["name"],
                    player["team"],
                    player["position"],
                    existing_list,
                    threshold=0.85,
                )

                if matched_key:
                    player["player_key"] = matched_key
                    matched_players.append(player)
                else:
                    # Store unmatched player
                    unmatched_stmt = text("""
                        INSERT INTO unmatched_players
                        (import_id, imported_name, team, position, suggested_player_key,
                         similarity_score, status)
                        VALUES (gen_random_uuid(), :imported_name, :team, :position,
                                :suggested_player_key, :similarity_score, 'pending')
                    """)
                    # Note: import_id will be set after import record creation
                    unmatched_count += 1

        # Delete existing LineStar data for this week
        stmt = text("""
            DELETE FROM player_pools
            WHERE week_id = :week_id AND source = 'LineStar'
        """)
        db.execute(stmt, {"week_id": actual_week_id})

        # Bulk insert matched players
        if matched_players:
            insert_stmt = text("""
                INSERT INTO player_pools
                (week_id, player_key, name, team, position, salary, projection,
                 ownership, ceiling, floor, notes, source, uploaded_at, projection_source, opponent_rank_category)
                VALUES (:week_id, :player_key, :name, :team, :position, :salary,
                        :projection, :ownership, :ceiling, :floor, :notes, :source,
                        CURRENT_TIMESTAMP, :projection_source, :opponent_rank_category)
            """)

            for player in matched_players:
                db.execute(
                    insert_stmt,
                    {
                        "week_id": actual_week_id,
                        "player_key": player.get("player_key", ""),
                        "name": player.get("name", ""),
                        "team": player.get("team", ""),
                        "position": player.get("position", ""),
                        "salary": player.get("salary", 0),
                        "projection": player.get("projection", 0.0),
                        "ownership": player.get("ownership", 0.0),
                        "ceiling": player.get("ceiling"),
                        "floor": player.get("floor"),
                        "notes": player.get("notes"),
                        "source": "LineStar",
                        "projection_source": player.get("projection_source"),
                        "opponent_rank_category": player.get("opponent_rank_category"),
                    },
                )

        # Create import history record
        import_id = history_tracker.create_import_record(
            week_id=actual_week_id,
            source="LineStar",
            file_name=file.filename,
            player_count=len(matched_players),
        )

        # Snapshot players
        if matched_players:
            history_tracker.snapshot_players(import_id, matched_players)

        # Get previous import for delta calculation
        changes = None
        stmt = text("""
            SELECT id FROM import_history
            WHERE week_id = :week_id AND source = 'LineStar'
            AND id != :current_id
            ORDER BY imported_at DESC
            LIMIT 1
        """)
        previous = db.execute(
            stmt,
            {"week_id": actual_week_id, "current_id": import_id}
        ).scalar()

        if previous:
            changes = history_tracker.calculate_deltas(import_id, previous)

        db.commit()

        return {
            "success": True,
            "import_id": str(import_id),
            "message": f"{len(matched_players)} players imported successfully",
            "player_count": len(matched_players),
            "changes_from_previous": changes,
            "unmatched_count": unmatched_count,
        }

    except DataImportError as e:
        db.rollback()
        return {
            "success": False,
            "error": e.message,
        }
    except Exception as e:
        db.rollback()
        error_msg = str(e)
        error_type = type(e).__name__
        logger.error(f"LineStar import failed: {error_type}: {error_msg}", exc_info=True)
        # Return more specific error message for debugging
        if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
            return {
                "success": False,
                "error": f"Week {week_id} not found in database. Please ensure the week exists before importing. Error: {error_type}: {error_msg}",
            }
        return {
            "success": False,
            "error": f"An unexpected error occurred during import: {error_type}: {error_msg}. Please try again.",
        }
    finally:
        db.close()


@router.post("/draftkings")
async def import_draftkings(
    file: UploadFile = File(...),
    week_id: int = Form(...),
    detected_week: Optional[int] = Form(None),
    db: Any = Depends(_get_current_db_dependency),
) -> dict:
    """
    Import DraftKings player data from XLSX file.

    Note: DraftKings imports replace ALL existing data for the week.

    Args:
        file: XLSX file upload
        week_id: Selected week ID from header
        detected_week: Week detected from filename (optional)
        db: Database session

    Returns:
        Import summary with player count and changes
    """
    try:
        # Validate inputs
        validate_week_number(week_id)
        validate_file_extension(file.filename)

        # Check for week mismatch
        detected = detect_week_from_filename(file.filename, "draftkings")
        if detected and detected != week_id and detected_week is None:
            return {
                "success": False,
                "warning": "week_mismatch",
                "message": f"Filename suggests Week {detected}, but Week {week_id} selected",
                "detected_week": detected,
                "selected_week": week_id,
                "requires_confirmation": True,
            }

        # Initialize services
        importer = DataImporter(db)
        history_tracker = ImportHistoryTracker(db)
        matcher = PlayerMatcher(db)

        # Parse and validate file
        df = await importer.parse_xlsx(file, "draftkings")
        df = importer.validate_data(df, "draftkings")

        # Normalize players
        players = importer.normalize_players(df, "draftkings")
        unmatched_count = 0

        # Fuzzy match players and handle unmatched
        matched_players = []
        for player in players:
            # Get existing players for matching
            stmt = text("""
                SELECT DISTINCT player_key, name, team, position
                FROM player_pools
                WHERE team = :team AND position = :position
            """)
            existing = db.execute(
                stmt,
                {"team": player.get("team"), "position": player.get("position")}
            ).fetchall()

            existing_list = [
                {
                    "player_key": row[0],
                    "name": row[1],
                    "team": row[2],
                    "position": row[3],
                }
                for row in existing
            ]

            # If no existing players, generate a player_key and import directly
            if not existing_list:
                player_key = matcher.generate_player_key(
                    player.get("name", ""),
                    player.get("team", ""),
                    player.get("position", ""),
                )
                player["player_key"] = player_key
                matched_players.append(player)
            else:
                # Try fuzzy match against existing players
                matched_key, similarity = matcher.fuzzy_match(
                    player["name"],
                    player["team"],
                    player["position"],
                    existing_list,
                    threshold=0.85,
                )

                if matched_key:
                    player["player_key"] = matched_key
                    matched_players.append(player)
                else:
                    unmatched_count += 1

        # Delete ALL existing players for this week (DraftKings replaces everything)
        stmt = text("DELETE FROM player_pools WHERE week_id = :week_id")
        db.execute(stmt, {"week_id": week_id})

        # Bulk insert matched players
        if matched_players:
            insert_stmt = text("""
                INSERT INTO player_pools
                (week_id, player_key, name, team, position, salary, projection,
                 ownership, ceiling, floor, notes, source, uploaded_at)
                VALUES (:week_id, :player_key, :name, :team, :position, :salary,
                        :projection, :ownership, :ceiling, :floor, :notes, :source,
                        CURRENT_TIMESTAMP)
            """)

            for player in matched_players:
                db.execute(
                    insert_stmt,
                    {
                        "week_id": week_id,
                        "player_key": player.get("player_key", ""),
                        "name": player.get("name", ""),
                        "team": player.get("team", ""),
                        "position": player.get("position", ""),
                        "salary": player.get("salary", 0),
                        "projection": player.get("projection", 0.0),
                        "ownership": player.get("ownership", 0.0),
                        "ceiling": player.get("ceiling"),
                        "floor": player.get("floor"),
                        "notes": player.get("notes"),
                        "source": "DraftKings",
                    },
                )

        # Create import history record
        import_id = history_tracker.create_import_record(
            week_id=week_id,
            source="DraftKings",
            file_name=file.filename,
            player_count=len(matched_players),
        )

        # Snapshot players
        if matched_players:
            history_tracker.snapshot_players(import_id, matched_players)

        # Get previous DraftKings import for delta calculation
        changes = None
        stmt = text("""
            SELECT id FROM import_history
            WHERE week_id = :week_id AND source = 'DraftKings'
            AND id != :current_id
            ORDER BY imported_at DESC
            LIMIT 1
        """)
        previous = db.execute(
            stmt,
            {"week_id": week_id, "current_id": import_id}
        ).scalar()

        if previous:
            changes = history_tracker.calculate_deltas(import_id, previous)

        db.commit()

        return {
            "success": True,
            "import_id": str(import_id),
            "message": f"{len(matched_players)} players imported successfully",
            "player_count": len(matched_players),
            "changes_from_previous": changes,
            "unmatched_count": unmatched_count,
        }

    except DataImportError as e:
        db.rollback()
        return {
            "success": False,
            "error": e.message,
        }
    except Exception as e:
        db.rollback()
        logger.error(f"DraftKings import failed: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": "An unexpected error occurred during import. Please try again.",
        }
    finally:
        db.close()


@router.post("/nfl-stats")
async def import_nfl_stats(
    file: UploadFile = File(...),
    db: Any = Depends(_get_current_db_dependency),
) -> dict:
    """
    Import NFL Comprehensive Stats data from XLSX file.

    Note: This endpoint replaces ALL existing historical stats data and creates a backup.

    Args:
        file: XLSX file upload
        db: Database session

    Returns:
        Import summary with record count
    """
    try:
        # Validate input
        validate_file_extension(file.filename)

        # Initialize services
        importer = DataImporter(db)
        history_tracker = ImportHistoryTracker(db)

        # Parse and validate file
        df = await importer.parse_xlsx(file, "comprehensive_stats")
        df = importer.validate_data(df, "comprehensive_stats")

        # Normalize players
        records = importer.normalize_players(df, "comprehensive_stats")

        # Backup existing data
        db.execute(text("""
            DELETE FROM historical_stats_backup;
            INSERT INTO historical_stats_backup
            SELECT * FROM historical_stats;
        """))

        # Delete all existing historical stats
        db.execute(text("DELETE FROM historical_stats"))

        # Bulk insert new records
        if records:
            insert_stmt = text("""
                INSERT INTO historical_stats
                (player_key, week, season, team, opponent, snaps, snap_pct,
                 rush_attempts, rush_yards, rush_tds, targets, target_share,
                 receptions, rec_yards, rec_tds, total_tds, touches,
                 actual_points, salary)
                VALUES (:player_key, :week, :season, :team, :opponent, :snaps,
                        :snap_pct, :rush_attempts, :rush_yards, :rush_tds,
                        :targets, :target_share, :receptions, :rec_yards,
                        :rec_tds, :total_tds, :touches, :actual_points, :salary)
            """)

            matcher = PlayerMatcher(db)
            for record in records:
                # Generate player_key from name, team, position if not present
                if "player_key" not in record:
                    player_key = matcher.generate_player_key(
                        record.get("player_name", ""),
                        record.get("team", ""),
                        record.get("position", ""),
                    )
                    record["player_key"] = player_key

                db.execute(
                    insert_stmt,
                    {
                        "player_key": record.get("player_key", ""),
                        "week": record.get("week"),
                        "season": 2024,  # Current season - can be made dynamic
                        "team": record.get("team", ""),
                        "opponent": record.get("opponent"),
                        "snaps": record.get("snaps"),
                        "snap_pct": record.get("snap_pct"),
                        "rush_attempts": record.get("rush_attempts"),
                        "rush_yards": record.get("rush_yards"),
                        "rush_tds": record.get("rush_tds"),
                        "targets": record.get("targets"),
                        "target_share": record.get("target_share"),
                        "receptions": record.get("receptions"),
                        "rec_yards": record.get("rec_yards"),
                        "rec_tds": record.get("rec_tds"),
                        "total_tds": record.get("total_tds"),
                        "touches": record.get("touches"),
                        "actual_points": record.get("actual_points"),
                        "salary": record.get("salary"),
                    },
                )

        # Create import history record
        import_id = history_tracker.create_import_record(
            week_id=None,  # Stats are cross-season, no specific week
            source="ComprehensiveStats",
            file_name=file.filename,
            player_count=len(records),
        )

        db.commit()

        return {
            "success": True,
            "import_id": str(import_id),
            "message": f"{len(records)} records imported successfully",
            "record_count": len(records),
            "backup_created": True,
        }

    except DataImportError as e:
        db.rollback()
        return {
            "success": False,
            "error": e.message,
        }
    except Exception as e:
        db.rollback()
        logger.error(f"NFL Stats import failed: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": "An unexpected error occurred during import. Please try again.",
        }
    finally:
        db.close()
