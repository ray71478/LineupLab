"""
ImportHistoryTracker service for tracking imports and calculating deltas.

Handles import history recording, player pool snapshots, and delta calculation
between successive imports to track ownership and projection changes.
"""

import json
import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ImportHistoryTracker:
    """Service for tracking import history and calculating deltas between imports."""

    def __init__(self, session: Session):
        """
        Initialize ImportHistoryTracker.

        Args:
            session: SQLAlchemy Session for database operations
        """
        self.session = session

    def create_import_record(
        self,
        week_id: int,
        source: str,
        file_name: Optional[str],
        player_count: int,
        import_summary: Optional[dict] = None,
    ) -> UUID:
        """
        Create an import history record in the database.

        Args:
            week_id: ID of the week being imported
            source: Import source ('LineStar', 'DraftKings', 'ComprehensiveStats')
            file_name: Name of the uploaded file (optional)
            player_count: Number of players/records imported
            import_summary: Summary data with changes (optional)

        Returns:
            UUID of the created import record
        """
        try:
            # Import here to avoid circular imports
            from sqlalchemy import insert
            from sqlalchemy import text

            # Build the insert statement for import_history
            import_summary_json = None
            if import_summary:
                import_summary_json = json.dumps(import_summary)

            # Execute insert using raw SQL to handle UUID generation
            stmt = text("""
                INSERT INTO import_history
                (week_id, source, file_name, player_count, import_summary)
                VALUES (:week_id, :source, :file_name, :player_count, :import_summary)
                RETURNING id
            """)

            result = self.session.execute(
                stmt,
                {
                    "week_id": week_id,
                    "source": source,
                    "file_name": file_name,
                    "player_count": player_count,
                    "import_summary": import_summary_json,
                },
            )

            import_id = result.scalar()

            if import_id is None:
                raise ValueError("Failed to create import record")

            self.session.flush()

            logger.info(
                f"Created import record {import_id} for week {week_id} "
                f"from {source} with {player_count} players"
            )

            return import_id

        except Exception as e:
            logger.error(f"Failed to create import record: {str(e)}")
            raise

    def snapshot_players(
        self, import_id: UUID, players: list[dict]
    ) -> int:
        """
        Create a snapshot of player pool data in player_pool_history.

        Takes the current player pool and stores it with the import ID for
        future comparison and delta calculation.

        Args:
            import_id: UUID of the import record
            players: List of player dicts with keys:
                    'player_key', 'salary', 'projection', 'ownership', 'ceiling', 'floor'

        Returns:
            Number of records inserted

        Raises:
            Exception: If snapshot creation fails
        """
        try:
            from sqlalchemy import insert, text

            if not players:
                logger.warning(f"No players to snapshot for import {import_id}")
                return 0

            # Prepare snapshot records
            snapshot_records = [
                {
                    "import_id": import_id,
                    "player_key": player.get("player_key"),
                    "salary": player.get("salary"),
                    "projection": player.get("projection"),
                    "ownership": player.get("ownership"),
                    "ceiling": player.get("ceiling"),
                    "floor": player.get("floor"),
                }
                for player in players
            ]

            # Bulk insert using raw SQL
            stmt = text("""
                INSERT INTO player_pool_history
                (import_id, player_key, salary, projection, ownership, ceiling, floor)
                VALUES (:import_id, :player_key, :salary, :projection, :ownership, :ceiling, :floor)
            """)

            for record in snapshot_records:
                self.session.execute(stmt, record)

            self.session.flush()

            logger.info(
                f"Snapshotted {len(snapshot_records)} players for import {import_id}"
            )

            return len(snapshot_records)

        except Exception as e:
            logger.error(f"Failed to snapshot players for import {import_id}: {str(e)}")
            raise

    def calculate_deltas(
        self, current_import_id: UUID, previous_import_id: Optional[UUID] = None
    ) -> dict:
        """
        Calculate deltas between current and previous import.

        Compares player ownership, projections, and player list changes
        between two import snapshots.

        Args:
            current_import_id: UUID of current import
            previous_import_id: UUID of previous import (None if first import)

        Returns:
            Dictionary with keys:
            - ownership_changes: int (number of ownership changes)
            - avg_ownership_delta: float (average absolute ownership change)
            - projection_changes: int (number of projection changes)
            - new_players: int (number of new players)
            - removed_players: int (number of removed players)
        """
        try:
            from sqlalchemy import select, text

            # If no previous import, return zeros
            if previous_import_id is None:
                return {
                    "ownership_changes": 0,
                    "avg_ownership_delta": 0.0,
                    "projection_changes": 0,
                    "new_players": 0,
                    "removed_players": 0,
                }

            # Fetch current snapshot
            current_stmt = text("""
                SELECT player_key, salary, projection, ownership, ceiling, floor
                FROM player_pool_history
                WHERE import_id = :import_id
            """)
            current_rows = self.session.execute(
                current_stmt, {"import_id": current_import_id}
            ).fetchall()

            current_dict = {
                row[0]: {
                    "salary": row[1],
                    "projection": row[2],
                    "ownership": row[3],
                    "ceiling": row[4],
                    "floor": row[5],
                }
                for row in current_rows
            }

            # Fetch previous snapshot
            previous_stmt = text("""
                SELECT player_key, salary, projection, ownership, ceiling, floor
                FROM player_pool_history
                WHERE import_id = :import_id
            """)
            previous_rows = self.session.execute(
                previous_stmt, {"import_id": previous_import_id}
            ).fetchall()

            previous_dict = {
                row[0]: {
                    "salary": row[1],
                    "projection": row[2],
                    "ownership": row[3],
                    "ceiling": row[4],
                    "floor": row[5],
                }
                for row in previous_rows
            }

            # Calculate ownership changes
            ownership_deltas = []
            for player_key in current_dict:
                if player_key in previous_dict:
                    current_own = current_dict[player_key].get("ownership")
                    previous_own = previous_dict[player_key].get("ownership")

                    # Handle None values
                    if (
                        current_own is not None
                        and previous_own is not None
                        and current_own != previous_own
                    ):
                        delta = abs(current_own - previous_own)
                        ownership_deltas.append(delta)

            # Calculate projection changes
            projection_changes = 0
            for player_key in current_dict:
                if player_key in previous_dict:
                    current_proj = current_dict[player_key].get("projection")
                    previous_proj = previous_dict[player_key].get("projection")

                    if (
                        current_proj is not None
                        and previous_proj is not None
                        and current_proj != previous_proj
                    ):
                        projection_changes += 1

            # Calculate new/removed players
            current_keys = set(current_dict.keys())
            previous_keys = set(previous_dict.keys())

            new_players = len(current_keys - previous_keys)
            removed_players = len(previous_keys - current_keys)

            # Calculate average ownership delta
            avg_ownership_delta = (
                sum(ownership_deltas) / len(ownership_deltas)
                if ownership_deltas
                else 0.0
            )

            result = {
                "ownership_changes": len(ownership_deltas),
                "avg_ownership_delta": round(avg_ownership_delta, 4),
                "projection_changes": projection_changes,
                "new_players": new_players,
                "removed_players": removed_players,
            }

            logger.info(f"Calculated deltas for import {current_import_id}: {result}")

            return result

        except Exception as e:
            logger.error(
                f"Failed to calculate deltas between {current_import_id} "
                f"and {previous_import_id}: {str(e)}"
            )
            raise
