"""
PlayerManagementService for handling player data retrieval, filtering, and enrichment.

Provides methods for:
- Fetching players by week with filtering and sorting
- Getting unmatched players with optional suggestions
- Searching players by name across weeks
- Getting fuzzy match suggestions for unmatched players

Performance optimizations:
- Uses specific column selection (no SELECT *)
- Leverages database indexes for filtering
- Implements pagination with LIMIT/OFFSET
- Caches suggestions within request scope
"""

import logging
import time
from typing import Optional, List, Tuple, Dict
from sqlalchemy import text, and_
from sqlalchemy.orm import Session

from backend.services.player_matcher import PlayerMatcher
from backend.schemas.player_schemas import (
    PlayerResponse,
    UnmatchedPlayerResponse,
    PlayerSearchResult,
)

logger = logging.getLogger(__name__)


class PlayerManagementService:
    """Service for managing player data retrieval, filtering, and sorting."""

    def __init__(self, session: Session):
        """
        Initialize PlayerManagementService.

        Args:
            session: SQLAlchemy Session for database queries
        """
        self.session = session
        self.player_matcher = PlayerMatcher(session)
        self._suggestion_cache: Dict[str, List[PlayerResponse]] = {}

    def get_players_by_week(
        self,
        week_id: int,
        position: Optional[str] = None,
        team: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_dir: str = "asc",
        limit: int = 200,
        offset: int = 0,
        contest_mode: str = "main",
    ) -> Tuple[List[PlayerResponse], int, int]:
        """
        Fetch all players for a specific week with filtering and sorting.

        Uses indexed queries for optimal performance:
        - idx_player_pools_week_position_team for position/team filters
        - idx_player_pools_week_key for exact lookups
        - idx_player_pool_week_mode for mode filtering

        Args:
            week_id: Week ID to fetch players for
            position: Optional position filter (QB, RB, WR, TE, DST, K)
            team: Optional team filter (e.g., KC, LAR)
            sort_by: Column to sort by (optional)
            sort_dir: Sort direction (asc or desc)
            limit: Max results (1-200)
            offset: Pagination offset
            contest_mode: Contest mode filter ('main' or 'showdown')

        Returns:
            Tuple of (list of PlayerResponse, total count, unmatched count)
        """
        start_time = time.time()
        try:
            # Validate inputs
            limit = min(limit, 200)  # Max 200 per request
            offset = max(offset, 0)

            # Build base query with specific columns (no SELECT *)
            # Include calibrated projection fields with COALESCE fallback
            sql = """
                SELECT
                    p.id,
                    p.player_key,
                    p.name,
                    p.team,
                    p.position,
                    p.salary,
                    COALESCE(p.projection_median_calibrated, p.projection_median_original, p.projection) as projection,
                    p.ownership,
                    COALESCE(p.projection_ceiling_calibrated, p.projection_ceiling_original, p.ceiling) as ceiling,
                    COALESCE(p.projection_floor_calibrated, p.projection_floor_original, p.floor) as floor,
                    p.notes,
                    p.source,
                    CASE
                        WHEN u.id IS NULL THEN 'matched'
                        ELSE 'unmatched'
                    END as status,
                    p.uploaded_at,
                    p.projection_floor_original,
                    p.projection_floor_calibrated,
                    p.projection_median_original,
                    p.projection_median_calibrated,
                    p.projection_ceiling_original,
                    p.projection_ceiling_calibrated,
                    COALESCE(p.calibration_applied, false) as calibration_applied,
                    p.contest_mode
                FROM player_pools p
                LEFT JOIN unmatched_players u ON p.player_key = u.suggested_player_key
                WHERE p.week_id = :week_id AND p.contest_mode = :contest_mode
            """

            # Add filters (uses idx_player_pools_week_position_team)
            params = {"week_id": week_id, "contest_mode": contest_mode}
            if position:
                sql += " AND p.position = :position"
                params["position"] = position.upper()
            if team:
                sql += " AND p.team = :team"
                params["team"] = team.upper()

            # Add sorting
            valid_sort_columns = [
                "name",
                "team",
                "position",
                "salary",
                "projection",
                "ownership",
                "source",
                "uploaded_at",
            ]
            if sort_by and sort_by in valid_sort_columns:
                sort_dir = "ASC" if sort_dir.lower() == "asc" else "DESC"
                sql += f" ORDER BY p.{sort_by} {sort_dir}"
            else:
                sql += " ORDER BY p.name ASC"

            # Get total count (before pagination) - use same WHERE clause
            count_sql = """
                SELECT COUNT(*)
                FROM player_pools p
                LEFT JOIN unmatched_players u ON p.player_key = u.suggested_player_key
                WHERE p.week_id = :week_id AND p.contest_mode = :contest_mode
            """
            if position:
                count_sql += " AND p.position = :position"
            if team:
                count_sql += " AND p.team = :team"

            try:
                total_result = self.session.execute(text(count_sql), params).scalar()
                total = total_result if total_result else 0
            except Exception as e:
                logger.error(
                    f"Count SQL query failed: {str(e)}\n"
                    f"SQL: {count_sql}\n"
                    f"Params: {params}",
                    exc_info=True
                )
                raise

            # Get unmatched count (separate, cached in session)
            unmatched_sql = """
                SELECT COUNT(*)
                FROM unmatched_players
                WHERE status = 'pending'
                  AND suggested_player_key IS NULL
            """
            unmatched_result = self.session.execute(text(unmatched_sql)).scalar()
            unmatched_count = unmatched_result if unmatched_result else 0

            # Add pagination
            sql += " LIMIT :limit OFFSET :offset"
            # Ensure limit and offset are integers for PostgreSQL
            params["limit"] = int(limit)
            params["offset"] = int(offset)

            # Execute query with error handling
            try:
                result = self.session.execute(text(sql), params).fetchall()
            except Exception as e:
                logger.error(
                    f"SQL query failed: {str(e)}\n"
                    f"SQL: {sql}\n"
                    f"Params: {params}",
                    exc_info=True
                )
                raise

            # Convert to PlayerResponse objects
            players = []
            for row in result:
                player = PlayerResponse(
                    id=row[0],
                    player_key=row[1],
                    name=row[2],
                    team=row[3],
                    position=row[4],
                    salary=row[5],
                    projection=row[6],
                    ownership=row[7],
                    ceiling=row[8],
                    floor=row[9],
                    notes=row[10],
                    source=row[11],
                    status=row[12],
                    uploaded_at=row[13],
                    projection_floor_original=row[14],
                    projection_floor_calibrated=row[15],
                    projection_median_original=row[16],
                    projection_median_calibrated=row[17],
                    projection_ceiling_original=row[18],
                    projection_ceiling_calibrated=row[19],
                    calibration_applied=row[20],
                    contest_mode=row[21],
                )
                players.append(player)

            elapsed = time.time() - start_time
            logger.info(
                f"Fetched {len(players)} players for week {week_id} ({contest_mode} mode) in {elapsed:.2f}s"
            )

            return players, total, unmatched_count

        except Exception as e:
            logger.error(
                f"Error fetching players for week {week_id} ({contest_mode} mode): {str(e)}", exc_info=True
            )
            return [], 0, 0

    def get_unmatched_players(
        self,
        week_id: int,
        with_suggestions: bool = True,
        limit: int = 50,
    ) -> Tuple[List[UnmatchedPlayerResponse], int]:
        """
        Fetch only unmatched players for a week with optional fuzzy match suggestions.

        Uses indexed queries for optimal performance:
        - idx_unmatched_import_status for status filtering

        Args:
            week_id: Week ID
            with_suggestions: Include fuzzy match suggestions
            limit: Max unmatched players to return

        Returns:
            Tuple of (list of UnmatchedPlayerResponse, total unmatched count)
        """
        start_time = time.time()
        try:
            limit = min(limit, 100)  # Max 100 unmatched per request

            # Get unmatched players for this week (uses indexes)
            sql = """
                SELECT
                    u.id,
                    u.imported_name,
                    u.team,
                    u.position,
                    u.salary,
                    u.similarity_score,
                    u.status,
                    u.import_id
                FROM unmatched_players u
                INNER JOIN import_history ih ON u.import_id = ih.id
                INNER JOIN weeks w ON ih.week_id = w.id
                WHERE w.id = :week_id
                  AND u.status = 'pending'
                ORDER BY u.imported_name
                LIMIT :limit
            """

            result = self.session.execute(
                text(sql), {"week_id": week_id, "limit": limit}
            ).fetchall()

            # Get total unmatched count
            count_sql = """
                SELECT COUNT(*)
                FROM unmatched_players u
                INNER JOIN import_history ih ON u.import_id = ih.id
                INNER JOIN weeks w ON ih.week_id = w.id
                WHERE w.id = :week_id
                  AND u.status = 'pending'
            """
            total_result = self.session.execute(
                text(count_sql), {"week_id": week_id}
            ).scalar()
            total = total_result if total_result else 0

            # Convert to UnmatchedPlayerResponse objects
            unmatched_players = []
            for row in result:
                unmatched = UnmatchedPlayerResponse(
                    id=row[0],
                    imported_name=row[1],
                    team=row[2],
                    position=row[3],
                    salary=row[4],
                    similarity_score=row[5],
                    status=row[6],
                    suggestions=None,
                )

                # Get suggestions if requested
                if with_suggestions:
                    suggestions = self._get_suggestions_for_player(
                        imported_name=row[1],
                        team=row[2],
                        position=row[3],
                        limit=5,
                    )
                    unmatched.suggestions = suggestions

                unmatched_players.append(unmatched)

            elapsed = time.time() - start_time
            logger.info(
                f"Fetched {len(unmatched_players)} unmatched players for week {week_id} in {elapsed:.2f}s"
            )

            return unmatched_players, total

        except Exception as e:
            logger.error(
                f"Error fetching unmatched players for week {week_id}: {str(e)}",
                exc_info=True,
            )
            return [], 0

    def search_players(
        self,
        query: str,
        limit: int = 20,
        week_id: Optional[int] = None,
    ) -> List[PlayerSearchResult]:
        """
        Search for players by name across weeks.

        Uses idx_player_pools_name_pattern for efficient name search.

        Args:
            query: Search query (player name)
            limit: Max results (1-50)
            week_id: Optional filter to specific week

        Returns:
            List of PlayerSearchResult objects
        """
        start_time = time.time()
        try:
            if not query or len(query.strip()) == 0:
                return []

            limit = min(limit, 50)  # Max 50 results per search
            search_term = f"%{query}%"

            # Build search query (uses idx_player_pools_name_pattern)
            sql = """
                SELECT DISTINCT
                    p.player_key,
                    p.name,
                    p.team,
                    p.position,
                    ARRAY_AGG(DISTINCT p.week_id) as weeks,
                    MAX(p.salary) as latest_salary,
                    MAX(p.projection) as latest_projection
                FROM player_pools p
                WHERE LOWER(p.name) LIKE LOWER(:search_term)
            """

            params = {"search_term": search_term}

            if week_id:
                sql += " AND p.week_id = :week_id"
                params["week_id"] = week_id

            sql += """
                GROUP BY p.player_key, p.name, p.team, p.position
                ORDER BY p.name
                LIMIT :limit
            """
            params["limit"] = limit

            result = self.session.execute(text(sql), params).fetchall()

            # Convert to PlayerSearchResult objects
            results = []
            for row in result:
                result_obj = PlayerSearchResult(
                    player_key=row[0],
                    name=row[1],
                    team=row[2],
                    position=row[3],
                    weeks=list(row[4]) if row[4] else [],
                    latest_salary=row[5],
                    latest_projection=row[6],
                )
                results.append(result_obj)

            elapsed = time.time() - start_time
            logger.info(
                f"Searched for '{query}' and found {len(results)} players in {elapsed:.2f}s"
            )

            return results

        except Exception as e:
            logger.error(f"Error searching players with query '{query}': {str(e)}", exc_info=True)
            return []

    def get_player_suggestions(
        self,
        unmatched_player_id: int,
        limit: int = 5,
    ) -> Tuple[Optional[UnmatchedPlayerResponse], List[PlayerResponse]]:
        """
        Get fuzzy match suggestions for a specific unmatched player.

        Args:
            unmatched_player_id: ID of unmatched player
            limit: Max suggestions to return

        Returns:
            Tuple of (UnmatchedPlayerResponse, list of PlayerResponse suggestions)
        """
        start_time = time.time()
        try:
            # Get unmatched player details
            unmatched_sql = """
                SELECT
                    id,
                    imported_name,
                    team,
                    position,
                    salary,
                    similarity_score,
                    status
                FROM unmatched_players
                WHERE id = :id
            """
            unmatched_result = self.session.execute(
                text(unmatched_sql), {"id": unmatched_player_id}
            ).fetchone()

            if not unmatched_result:
                return None, []

            unmatched_player = UnmatchedPlayerResponse(
                id=unmatched_result[0],
                imported_name=unmatched_result[1],
                team=unmatched_result[2],
                position=unmatched_result[3],
                salary=unmatched_result[4],
                similarity_score=unmatched_result[5],
                status=unmatched_result[6],
            )

            # Get suggestions
            suggestions = self._get_suggestions_for_player(
                imported_name=unmatched_result[1],
                team=unmatched_result[2],
                position=unmatched_result[3],
                limit=limit,
            )

            elapsed = time.time() - start_time
            logger.info(
                f"Got {len(suggestions)} suggestions for unmatched player {unmatched_player_id} in {elapsed:.2f}s"
            )

            return unmatched_player, suggestions

        except Exception as e:
            logger.error(
                f"Error fetching suggestions for unmatched player {unmatched_player_id}: {str(e)}",
                exc_info=True,
            )
            return None, []

    def _get_suggestions_for_player(
        self,
        imported_name: str,
        team: str,
        position: str,
        limit: int = 5,
    ) -> List[PlayerResponse]:
        """
        Get fuzzy match suggestions for an unmatched player.

        Uses idx_player_pools_week_position_team for efficient filtering.

        Args:
            imported_name: Imported player name
            team: Team abbreviation
            position: Position
            limit: Max suggestions

        Returns:
            List of PlayerResponse suggestions sorted by similarity score
        """
        try:
            # Check cache first (within request scope)
            cache_key = f"{imported_name}_{team}_{position}"
            if cache_key in self._suggestion_cache:
                return self._suggestion_cache[cache_key][:limit]

            # Get all players with matching team and position (uses index)
            # Include calibrated projection fields
            sql = """
                SELECT
                    id,
                    player_key,
                    name,
                    team,
                    position,
                    salary,
                    projection,
                    ownership,
                    ceiling,
                    floor,
                    notes,
                    source,
                    uploaded_at,
                    projection_floor_original,
                    projection_floor_calibrated,
                    projection_median_original,
                    projection_median_calibrated,
                    projection_ceiling_original,
                    projection_ceiling_calibrated,
                    COALESCE(calibration_applied, false) as calibration_applied,
                    contest_mode
                FROM player_pools
                WHERE team = :team
                  AND position = :position
                ORDER BY name
            """

            candidates_result = self.session.execute(
                text(sql), {"team": team.upper(), "position": position.upper()}
            ).fetchall()

            # Convert to dict format for fuzzy matching
            candidates = [
                {
                    "name": row[2],
                    "player_key": row[1],
                    "team": row[3],
                    "position": row[4],
                }
                for row in candidates_result
            ]

            if not candidates:
                self._suggestion_cache[cache_key] = []
                return []

            # Use fuzzy matching to find similar players
            from rapidfuzz import fuzz, process

            candidate_names = [c["name"] for c in candidates]
            matches = process.extract(
                imported_name, candidate_names, scorer=fuzz.ratio, limit=limit
            )

            suggestions = []
            for match_name, score, _ in matches:
                # Find the full candidate record
                candidate = next(
                    (c for c in candidates if c["name"] == match_name), None
                )
                if candidate:
                    # Find the row with this candidate
                    for row in candidates_result:
                        if row[1] == candidate["player_key"]:  # player_key match
                            suggestion = PlayerResponse(
                                id=row[0],
                                player_key=row[1],
                                name=row[2],
                                team=row[3],
                                position=row[4],
                                salary=row[5],
                                projection=row[6],
                                ownership=row[7],
                                ceiling=row[8],
                                floor=row[9],
                                notes=row[10],
                                source=row[11],
                                status="matched",
                                uploaded_at=row[12],
                                projection_floor_original=row[13],
                                projection_floor_calibrated=row[14],
                                projection_median_original=row[15],
                                projection_median_calibrated=row[16],
                                projection_ceiling_original=row[17],
                                projection_ceiling_calibrated=row[18],
                                calibration_applied=row[19],
                                contest_mode=row[20],
                            )
                            suggestions.append(suggestion)
                            break

            # Cache results (within request scope)
            self._suggestion_cache[cache_key] = suggestions[:limit]

            return suggestions[:limit]

        except Exception as e:
            logger.error(
                f"Error getting suggestions for {imported_name}: {str(e)}", exc_info=True
            )
            return []
