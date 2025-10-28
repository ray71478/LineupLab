"""
Unmatched players management API endpoints.

Provides endpoints for reviewing, mapping, and ignoring players that
failed fuzzy matching during import.
"""

import logging
from typing import Optional, Any
from uuid import UUID

from fastapi import APIRouter, Query, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/unmatched-players", tags=["unmatched-players"])


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


class MapPlayerRequest(BaseModel):
    """Request body for mapping unmatched player to canonical player."""
    unmatched_player_id: int
    canonical_player_key: str


class IgnorePlayerRequest(BaseModel):
    """Request body for ignoring unmatched player."""
    unmatched_player_id: int


@router.get("")
async def get_unmatched_players(
    import_id: str = Query(..., description="Required: Import ID (UUID)"),
    status: Optional[str] = Query(None, description="Optional: Filter by status (pending, mapped, ignored)"),
    db: Any = Depends(_get_current_db_dependency),
) -> dict:
    """
    Get unmatched players from a specific import.

    Args:
        import_id: UUID of import to fetch unmatched players for
        status: Optional status filter
        db: Database session

    Returns:
        List of unmatched players
    """
    try:
        # Validate UUID format
        try:
            import_uuid = UUID(import_id)
        except ValueError:
            return {
                "success": False,
                "error": "Invalid import_id format. Must be valid UUID.",
            }

        # Validate status if provided
        if status and status not in ["pending", "mapped", "ignored"]:
            return {
                "success": False,
                "error": f"Invalid status: {status}. Must be 'pending', 'mapped', or 'ignored'.",
            }

        # Build query
        if status:
            stmt = text("""
                SELECT id, imported_name, team, position, suggested_player_key,
                       similarity_score, status
                FROM unmatched_players
                WHERE import_id = :import_id AND status = :status
                ORDER BY imported_name
            """)
            result = db.execute(
                stmt,
                {"import_id": import_uuid, "status": status}
            ).fetchall()
        else:
            stmt = text("""
                SELECT id, imported_name, team, position, suggested_player_key,
                       similarity_score, status
                FROM unmatched_players
                WHERE import_id = :import_id
                ORDER BY imported_name
            """)
            result = db.execute(stmt, {"import_id": import_uuid}).fetchall()

        unmatched_players = [
            {
                "id": row[0],
                "imported_name": row[1],
                "team": row[2],
                "position": row[3],
                "suggested_player_key": row[4],
                "similarity_score": float(row[5]) if row[5] else None,
                "status": row[6],
            }
            for row in result
        ]

        db.close()

        return {
            "success": True,
            "unmatched_players": unmatched_players,
        }

    except Exception as e:
        logger.error(f"Failed to get unmatched players: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": "An unexpected error occurred. Please try again.",
        }


@router.post("/map")
async def map_unmatched_player(
    request: MapPlayerRequest,
    db: Any = Depends(_get_current_db_dependency),
) -> dict:
    """
    Map an unmatched player to a canonical player by creating an alias.

    Args:
        request: MapPlayerRequest with unmatched_player_id and canonical_player_key
        db: Database session

    Returns:
        Success message
    """
    try:
        # Validate unmatched player exists
        unmatched_stmt = text("""
            SELECT id, imported_name, team, position
            FROM unmatched_players
            WHERE id = :id
        """)
        unmatched = db.execute(
            unmatched_stmt,
            {"id": request.unmatched_player_id}
        ).fetchone()

        if not unmatched:
            return {
                "success": False,
                "error": f"Unmatched player with ID {request.unmatched_player_id} not found.",
            }

        # Validate canonical player exists
        canonical_stmt = text("""
            SELECT player_key FROM player_pools
            WHERE player_key = :player_key
            LIMIT 1
        """)
        canonical = db.execute(
            canonical_stmt,
            {"player_key": request.canonical_player_key}
        ).scalar()

        if not canonical:
            return {
                "success": False,
                "error": f"Canonical player with key {request.canonical_player_key} not found.",
            }

        # Create alias
        alias_stmt = text("""
            INSERT INTO player_aliases (alias_name, canonical_player_key)
            VALUES (:alias_name, :canonical_player_key)
            ON CONFLICT (alias_name) DO UPDATE
            SET canonical_player_key = :canonical_player_key
        """)
        db.execute(
            alias_stmt,
            {
                "alias_name": unmatched[1],  # imported_name
                "canonical_player_key": request.canonical_player_key,
            }
        )

        # Update unmatched player status
        update_stmt = text("""
            UPDATE unmatched_players
            SET status = 'mapped', suggested_player_key = :player_key
            WHERE id = :id
        """)
        db.execute(
            update_stmt,
            {
                "id": request.unmatched_player_id,
                "player_key": request.canonical_player_key,
            }
        )

        db.commit()
        db.close()

        logger.info(
            f"Mapped unmatched player '{unmatched[1]}' to '{request.canonical_player_key}'"
        )

        return {
            "success": True,
            "message": "Alias mapped successfully",
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to map unmatched player: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": "An unexpected error occurred. Please try again.",
        }
    finally:
        db.close()


@router.post("/ignore")
async def ignore_unmatched_player(
    request: IgnorePlayerRequest,
    db: Any = Depends(_get_current_db_dependency),
) -> dict:
    """
    Mark an unmatched player as ignored.

    Args:
        request: IgnorePlayerRequest with unmatched_player_id
        db: Database session

    Returns:
        Success message
    """
    try:
        # Validate unmatched player exists
        unmatched_stmt = text("""
            SELECT id, imported_name
            FROM unmatched_players
            WHERE id = :id
        """)
        unmatched = db.execute(
            unmatched_stmt,
            {"id": request.unmatched_player_id}
        ).fetchone()

        if not unmatched:
            return {
                "success": False,
                "error": f"Unmatched player with ID {request.unmatched_player_id} not found.",
            }

        # Update status to ignored
        update_stmt = text("""
            UPDATE unmatched_players
            SET status = 'ignored'
            WHERE id = :id
        """)
        db.execute(update_stmt, {"id": request.unmatched_player_id})

        db.commit()
        db.close()

        logger.info(f"Ignored unmatched player '{unmatched[1]}'")

        return {
            "success": True,
            "message": "Player ignored",
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to ignore unmatched player: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": "An unexpected error occurred. Please try again.",
        }
    finally:
        db.close()
