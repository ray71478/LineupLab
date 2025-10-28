"""
Import history and comparison API endpoints.

Provides endpoints for listing import history and comparing imports
to track ownership and projection changes over time.
"""

import logging
from typing import Optional, Any
from uuid import UUID

from fastapi import APIRouter, Query, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/import-history", tags=["import-history"])


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


@router.get("")
async def get_import_history(
    week_id: int = Query(..., description="Required: Week ID"),
    source: Optional[str] = Query(None, description="Optional: Filter by source (LineStar, DraftKings, ComprehensiveStats)"),
    db: Any = Depends(_get_current_db_dependency),
) -> dict:
    """
    Get import history for a specific week.

    Args:
        week_id: Required week ID (1-18)
        source: Optional source filter
        db: Database session

    Returns:
        List of imports with summaries
    """
    try:
        # Validate week_id
        if not (1 <= week_id <= 18):
            return {
                "success": False,
                "error": f"Invalid week_id: {week_id}. Must be between 1 and 18.",
            }

        # Build query
        stmt = text("""
            SELECT id, week_id, source, file_name, player_count,
                   import_summary, imported_at
            FROM import_history
            WHERE week_id = :week_id
        """)
        params = {"week_id": week_id}

        # Apply source filter if provided
        if source:
            stmt = text("""
                SELECT id, week_id, source, file_name, player_count,
                       import_summary, imported_at
                FROM import_history
                WHERE week_id = :week_id AND source = :source
            """)
            params["source"] = source

        # Order by most recent first
        if source:
            stmt = text("""
                SELECT id, week_id, source, file_name, player_count,
                       import_summary, imported_at
                FROM import_history
                WHERE week_id = :week_id AND source = :source
                ORDER BY imported_at DESC
            """)
        else:
            stmt = text("""
                SELECT id, week_id, source, file_name, player_count,
                       import_summary, imported_at
                FROM import_history
                WHERE week_id = :week_id
                ORDER BY imported_at DESC
            """)

        results = db.execute(stmt, params).fetchall()

        imports = []
        for i, row in enumerate(results):
            import_record = {
                "id": str(row[0]),
                "week_id": row[1],
                "source": row[2],
                "file_name": row[3],
                "player_count": row[4],
                "imported_at": row[6].isoformat() if row[6] else None,
                "changes_from_previous": None,
            }

            # Get changes from previous import if available
            if i < len(results) - 1:  # Not the last (oldest) import
                from backend.services.import_history_tracker import ImportHistoryTracker
                tracker = ImportHistoryTracker(db)
                previous_id = results[i + 1][0]
                try:
                    import_record["changes_from_previous"] = tracker.calculate_deltas(
                        row[0], previous_id
                    )
                except Exception as e:
                    logger.warning(f"Could not calculate deltas: {str(e)}")

            imports.append(import_record)

        db.close()

        return {
            "success": True,
            "imports": imports,
        }

    except Exception as e:
        logger.error(f"Failed to get import history: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": "An unexpected error occurred. Please try again.",
        }


@router.get("/compare")
async def compare_imports(
    current_id: str = Query(..., description="Current import ID (UUID)"),
    previous_id: str = Query(..., description="Previous import ID (UUID)"),
    db: Any = Depends(_get_current_db_dependency),
) -> dict:
    """
    Compare two imports to show ownership and projection changes.

    Args:
        current_id: UUID of current (more recent) import
        previous_id: UUID of previous (older) import
        db: Database session

    Returns:
        Detailed comparison with changes
    """
    try:
        from backend.services.import_history_tracker import ImportHistoryTracker

        # Validate UUIDs
        try:
            current_uuid = UUID(current_id)
            previous_uuid = UUID(previous_id)
        except ValueError:
            return {
                "success": False,
                "error": "Invalid import ID format. Must be valid UUID.",
            }

        tracker = ImportHistoryTracker(db)

        # Verify imports exist
        stmt = text("""
            SELECT id, imported_at, player_count
            FROM import_history
            WHERE id = :id
        """)

        current_import = db.execute(stmt, {"id": current_uuid}).fetchone()
        previous_import = db.execute(stmt, {"id": previous_uuid}).fetchone()

        if not current_import or not previous_import:
            return {
                "success": False,
                "error": "One or both import IDs not found.",
            }

        # Get snapshots for both imports
        current_stmt = text("""
            SELECT player_key, salary, projection, ownership, ceiling, floor
            FROM player_pool_history
            WHERE import_id = :import_id
        """)

        current_players = db.execute(current_stmt, {"import_id": current_uuid}).fetchall()
        previous_stmt = text("""
            SELECT player_key, salary, projection, ownership, ceiling, floor
            FROM player_pool_history
            WHERE import_id = :import_id
        """)
        previous_players = db.execute(previous_stmt, {"import_id": previous_uuid}).fetchall()

        # Convert to dictionaries keyed by player_key
        current_dict = {
            row[0]: {
                "salary": row[1],
                "projection": row[2],
                "ownership": row[3],
                "ceiling": row[4],
                "floor": row[5],
            }
            for row in current_players
        }

        previous_dict = {
            row[0]: {
                "salary": row[1],
                "projection": row[2],
                "ownership": row[3],
                "ceiling": row[4],
                "floor": row[5],
            }
            for row in previous_players
        }

        # Find ownership changes
        ownership_changes = []
        for player_key in current_dict:
            if player_key in previous_dict:
                current_own = current_dict[player_key].get("ownership") or 0.0
                previous_own = previous_dict[player_key].get("ownership") or 0.0
                if current_own != previous_own:
                    # Get player name from player_pools
                    name_stmt = text("""
                        SELECT name FROM player_pools
                        WHERE player_key = :player_key
                        LIMIT 1
                    """)
                    name_result = db.execute(name_stmt, {"player_key": player_key}).scalar()

                    ownership_changes.append({
                        "player_key": player_key,
                        "name": name_result or player_key.replace("_", " "),
                        "previous_ownership": previous_own,
                        "current_ownership": current_own,
                        "delta": current_own - previous_own,
                    })

        # Find projection changes
        projection_changes = []
        for player_key in current_dict:
            if player_key in previous_dict:
                current_proj = current_dict[player_key].get("projection") or 0.0
                previous_proj = previous_dict[player_key].get("projection") or 0.0
                if current_proj != previous_proj:
                    name_stmt = text("""
                        SELECT name FROM player_pools
                        WHERE player_key = :player_key
                        LIMIT 1
                    """)
                    name_result = db.execute(name_stmt, {"player_key": player_key}).scalar()

                    projection_changes.append({
                        "player_key": player_key,
                        "name": name_result or player_key.replace("_", " "),
                        "previous_projection": previous_proj,
                        "current_projection": current_proj,
                        "delta": current_proj - previous_proj,
                    })

        # Find new players (in current but not in previous)
        new_players = []
        for player_key in current_dict:
            if player_key not in previous_dict:
                name_stmt = text("""
                    SELECT name, salary, projection FROM player_pools
                    WHERE player_key = :player_key
                    LIMIT 1
                """)
                name_result = db.execute(name_stmt, {"player_key": player_key}).fetchone()

                new_players.append({
                    "player_key": player_key,
                    "name": name_result[0] if name_result else player_key.replace("_", " "),
                    "salary": name_result[1] if name_result else None,
                    "projection": name_result[2] if name_result else None,
                })

        # Find removed players (in previous but not in current)
        removed_players = []
        for player_key in previous_dict:
            if player_key not in current_dict:
                name_stmt = text("""
                    SELECT name, salary, projection FROM player_pools
                    WHERE player_key = :player_key
                    LIMIT 1
                """)
                name_result = db.execute(name_stmt, {"player_key": player_key}).fetchone()

                removed_players.append({
                    "player_key": player_key,
                    "name": name_result[0] if name_result else player_key.replace("_", " "),
                    "salary": name_result[1] if name_result else None,
                    "projection": name_result[2] if name_result else None,
                })

        db.close()

        return {
            "success": True,
            "comparison": {
                "current": {
                    "id": current_id,
                    "imported_at": current_import[1].isoformat() if current_import[1] else None,
                    "player_count": current_import[2],
                },
                "previous": {
                    "id": previous_id,
                    "imported_at": previous_import[1].isoformat() if previous_import[1] else None,
                    "player_count": previous_import[2],
                },
                "ownership_changes": ownership_changes,
                "projection_changes": projection_changes,
                "new_players": new_players,
                "removed_players": removed_players,
            },
        }

    except Exception as e:
        logger.error(f"Failed to compare imports: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": "An unexpected error occurred. Please try again.",
        }
