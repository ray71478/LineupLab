"""
PlayerAliasService for managing player alias operations.

Provides methods for:
- Creating/updating player aliases
- Resolving aliases to canonical player keys
- Listing all aliases (for Phase 2)
- Handling alias conflicts and duplicates
"""

import logging
from datetime import datetime
from typing import Optional, List

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class PlayerAliasService:
    """Service for managing player aliases."""

    def __init__(self, session: Session):
        """
        Initialize PlayerAliasService.

        Args:
            session: SQLAlchemy Session for database queries
        """
        self.session = session

    def create_alias(
        self,
        alias_name: str,
        canonical_player_key: str,
    ) -> bool:
        """
        Create or update a player alias.

        Creates a new alias mapping from an imported player name to a canonical
        player key. If the alias already exists, updates the canonical_player_key.

        Args:
            alias_name: Imported player name to use as alias
            canonical_player_key: Canonical player key to map to

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if canonical player exists
            check_sql = """
                SELECT player_key FROM player_pools
                WHERE player_key = :player_key
                LIMIT 1
            """
            result = self.session.execute(
                text(check_sql), {"player_key": canonical_player_key}
            ).scalar()

            if not result:
                logger.warning(
                    f"Cannot create alias: canonical player '{canonical_player_key}' not found"
                )
                return False

            # Create or update alias
            sql = """
                INSERT INTO player_aliases (alias_name, canonical_player_key, created_at, updated_at)
                VALUES (:alias_name, :canonical_player_key, :created_at, :updated_at)
                ON CONFLICT (alias_name) DO UPDATE
                SET canonical_player_key = :canonical_player_key,
                    updated_at = :updated_at
            """

            now = datetime.utcnow()
            self.session.execute(
                text(sql),
                {
                    "alias_name": alias_name,
                    "canonical_player_key": canonical_player_key,
                    "created_at": now,
                    "updated_at": now,
                },
            )

            self.session.commit()

            logger.info(
                f"Created/updated alias '{alias_name}' -> '{canonical_player_key}'"
            )
            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to create alias: {str(e)}", exc_info=True)
            return False

    def resolve_alias(self, alias_name: str) -> Optional[str]:
        """
        Resolve an alias to its canonical player key.

        Looks up the alias in the player_aliases table and returns the
        associated canonical player key.

        Args:
            alias_name: Alias name to resolve

        Returns:
            Canonical player_key if alias exists, None otherwise
        """
        try:
            sql = """
                SELECT canonical_player_key
                FROM player_aliases
                WHERE alias_name = :alias_name
            """

            result = self.session.execute(
                text(sql), {"alias_name": alias_name}
            ).scalar()

            return result

        except Exception as e:
            logger.error(f"Failed to resolve alias '{alias_name}': {str(e)}", exc_info=True)
            return None

    def get_all_aliases(self) -> List[dict]:
        """
        Get all player aliases (for Phase 2 alias management UI).

        Returns:
            List of dicts with alias_name, canonical_player_key, created_at, updated_at
        """
        try:
            sql = """
                SELECT alias_name, canonical_player_key, created_at, updated_at
                FROM player_aliases
                ORDER BY created_at DESC
            """

            result = self.session.execute(text(sql)).fetchall()

            aliases = [
                {
                    "alias_name": row[0],
                    "canonical_player_key": row[1],
                    "created_at": row[2],
                    "updated_at": row[3],
                }
                for row in result
            ]

            return aliases

        except Exception as e:
            logger.error(f"Failed to get aliases: {str(e)}", exc_info=True)
            return []

    def delete_alias(self, alias_name: str) -> bool:
        """
        Delete a player alias (for Phase 2 alias management).

        Args:
            alias_name: Alias name to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            sql = """
                DELETE FROM player_aliases
                WHERE alias_name = :alias_name
            """

            result = self.session.execute(text(sql), {"alias_name": alias_name})
            self.session.commit()

            if result.rowcount == 0:
                logger.warning(f"Alias '{alias_name}' not found for deletion")
                return False

            logger.info(f"Deleted alias '{alias_name}'")
            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to delete alias '{alias_name}': {str(e)}", exc_info=True)
            return False

    def alias_exists(self, alias_name: str) -> bool:
        """
        Check if an alias exists.

        Args:
            alias_name: Alias name to check

        Returns:
            True if alias exists, False otherwise
        """
        try:
            sql = """
                SELECT 1 FROM player_aliases
                WHERE alias_name = :alias_name
                LIMIT 1
            """

            result = self.session.execute(
                text(sql), {"alias_name": alias_name}
            ).scalar()

            return result is not None

        except Exception as e:
            logger.error(f"Failed to check alias existence: {str(e)}", exc_info=True)
            return False
