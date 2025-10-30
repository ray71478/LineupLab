"""
DailyDataRefreshJob for orchestrating MySportsFeeds API data refresh.

Coordinates all four API calls and stores results in database:
- Player injuries → player_pools.injury_status
- Weekly games → vegas_lines (ITT data)
- Team stats → team_defense_stats (defensive rankings)
- Player gamelogs → historical_stats (trend data)

Includes error handling, logging, and status tracking.
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.services.mysportsfeeds_service import MySportsFeedsService

logger = logging.getLogger(__name__)


class DailyDataRefreshJob:
    """Orchestrates daily data refresh from MySportsFeeds API."""

    def __init__(self, db_session: Session):
        """
        Initialize DailyDataRefreshJob.

        Args:
            db_session: SQLAlchemy Session for database operations
        """
        self.db = db_session
        self.service: Optional[MySportsFeedsService] = None
        self.logger = logger
        self.start_time: Optional[datetime] = None
        self.results: Dict[str, Any] = {}

    async def execute(self) -> Dict[str, Any]:
        """
        Execute complete daily data refresh workflow.

        Orchestrates all four API calls in sequence:
        1. Fetch current week injuries
        2. Fetch weekly games (ITT)
        3. Fetch team defensive stats
        4. Fetch player gamelogs

        Stores results in database and returns summary.
        Errors in individual steps don't stop job execution.

        Returns:
            Dictionary with execution summary:
            {
                'success': bool,
                'start_time': datetime,
                'end_time': datetime,
                'duration_seconds': float,
                'injuries': {
                    'fetched': int,
                    'stored': int,
                    'errors': int,
                },
                'games': {
                    'fetched': int,
                    'stored': int,
                    'errors': int,
                },
                'team_stats': {
                    'fetched': int,
                    'stored': int,
                    'errors': int,
                },
                'gamelogs': {
                    'fetched': int,
                    'stored': int,
                    'errors': int,
                },
                'errors': [str, ...],
            }
        """
        self.start_time = datetime.utcnow()
        self.logger.info(f"Starting daily data refresh at {self.start_time}")

        # Initialize service
        try:
            self.service = MySportsFeedsService(self.db)
        except ValueError as e:
            self.logger.error(f"Failed to initialize MySportsFeedsService: {str(e)}")
            return {
                "success": False,
                "start_time": self.start_time,
                "end_time": datetime.utcnow(),
                "duration_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
                "errors": [str(e)],
            }

        try:
            # Execute all refresh steps
            await self._fetch_and_store_injuries()
            await self._fetch_and_store_games()
            await self._fetch_and_store_team_stats()
            await self._fetch_and_store_gamelogs()

            # Compile results
            end_time = datetime.utcnow()
            duration = (end_time - self.start_time).total_seconds()

            result = {
                "success": True,
                "start_time": self.start_time,
                "end_time": end_time,
                "duration_seconds": duration,
            }
            result.update(self.results)

            self.logger.info(
                f"Daily refresh completed in {duration:.1f}s. "
                f"Injuries: {result.get('injuries', {}).get('stored', 0)}, "
                f"Games: {result.get('games', {}).get('stored', 0)}, "
                f"Team Stats: {result.get('team_stats', {}).get('stored', 0)}, "
                f"Gamelogs: {result.get('gamelogs', {}).get('stored', 0)}"
            )

            return result

        except Exception as e:
            self.logger.error(f"Unexpected error during refresh: {str(e)}", exc_info=True)
            return {
                "success": False,
                "start_time": self.start_time,
                "end_time": datetime.utcnow(),
                "duration_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
                "errors": [str(e)],
            }

        finally:
            # Cleanup
            if self.service:
                await self.service.close()

    async def _fetch_and_store_injuries(self) -> None:
        """Fetch injuries and store in player_pools.injury_status."""
        try:
            self.logger.info("Fetching current week injuries...")

            injuries = await self.service.fetch_current_week_injuries()

            if not injuries:
                self.results["injuries"] = {
                    "fetched": 0,
                    "stored": 0,
                    "errors": 0,
                }
                return

            # Store in database
            stored = await self._store_injury_status(injuries)

            self.results["injuries"] = {
                "fetched": len(injuries),
                "stored": stored,
                "errors": len(injuries) - stored,
            }

        except Exception as e:
            self.logger.error(f"Error in _fetch_and_store_injuries: {str(e)}")
            self.results["injuries"] = {
                "fetched": 0,
                "stored": 0,
                "errors": 1,
            }

    async def _fetch_and_store_games(self) -> None:
        """Fetch weekly games and store ITT in vegas_lines."""
        try:
            self.logger.info("Fetching weekly games and ITT values...")

            games = await self.service.fetch_weekly_games()

            if not games:
                self.results["games"] = {
                    "fetched": 0,
                    "stored": 0,
                    "errors": 0,
                }
                return

            # Store in database
            stored = await self._store_vegas_lines(games)

            self.results["games"] = {
                "fetched": len(games),
                "stored": stored,
                "errors": len(games) - stored,
            }

        except Exception as e:
            self.logger.error(f"Error in _fetch_and_store_games: {str(e)}")
            self.results["games"] = {
                "fetched": 0,
                "stored": 0,
                "errors": 1,
            }

    async def _fetch_and_store_team_stats(self) -> None:
        """Fetch team defensive stats and store."""
        try:
            self.logger.info("Fetching team defensive statistics...")

            team_stats = await self.service.fetch_team_defensive_stats()

            if not team_stats:
                self.results["team_stats"] = {
                    "fetched": 0,
                    "stored": 0,
                    "errors": 0,
                }
                return

            # Store in database
            stored = await self._store_team_defense_stats(team_stats)

            self.results["team_stats"] = {
                "fetched": len(team_stats),
                "stored": stored,
                "errors": len(team_stats) - stored,
            }

        except Exception as e:
            self.logger.error(f"Error in _fetch_and_store_team_stats: {str(e)}")
            self.results["team_stats"] = {
                "fetched": 0,
                "stored": 0,
                "errors": 1,
            }

    async def _fetch_and_store_gamelogs(self) -> None:
        """Fetch player gamelogs and backfill historical_stats."""
        try:
            self.logger.info("Fetching player gamelogs...")

            gamelogs = await self.service.fetch_player_gamelogs()

            if not gamelogs:
                self.results["gamelogs"] = {
                    "fetched": 0,
                    "stored": 0,
                    "errors": 0,
                }
                return

            # Store in database
            stored = await self._store_player_gamelogs(gamelogs)

            self.results["gamelogs"] = {
                "fetched": len(gamelogs),
                "stored": stored,
                "errors": len(gamelogs) - stored,
            }

        except Exception as e:
            self.logger.error(f"Error in _fetch_and_store_gamelogs: {str(e)}")
            self.results["gamelogs"] = {
                "fetched": 0,
                "stored": 0,
                "errors": 1,
            }

    async def _store_injury_status(self, injuries: list) -> int:
        """
        Store injury status in player_pools.

        Args:
            injuries: List of injury dictionaries from API

        Returns:
            Number of injuries successfully stored
        """
        stored = 0

        for injury in injuries:
            try:
                # Find player in player_pools by name and team
                first_name = injury.get("player_first_name", "")
                last_name = injury.get("player_last_name", "")
                team = injury.get("team", "")
                status = injury.get("playing_probability", "PROBABLE")

                # Query for player
                result = self.db.execute(text("""
                    SELECT id FROM player_pools
                    WHERE first_name = :first_name
                    AND last_name = :last_name
                    AND team = :team
                    LIMIT 1
                """), {
                    "first_name": first_name,
                    "last_name": last_name,
                    "team": team,
                })

                player_row = result.first()

                if not player_row:
                    self.logger.debug(
                        f"Player not found in pool: {first_name} {last_name} ({team})"
                    )
                    continue

                player_id = player_row[0]

                # Update injury status
                self.db.execute(text("""
                    UPDATE player_pools
                    SET injury_status = :status, updated_at = :now
                    WHERE id = :player_id
                """), {
                    "status": status,
                    "now": datetime.utcnow(),
                    "player_id": player_id,
                })

                stored += 1

            except Exception as e:
                self.logger.debug(
                    f"Error storing injury for {injury.get('player_first_name')} "
                    f"{injury.get('player_last_name')}: {str(e)}"
                )

        try:
            self.db.commit()
        except Exception as e:
            self.logger.error(f"Error committing injury updates: {str(e)}")
            self.db.rollback()
            stored = 0

        return stored

    async def _store_vegas_lines(self, games: list) -> int:
        """
        Store Vegas ITT values in vegas_lines.

        Args:
            games: List of game dictionaries from API

        Returns:
            Number of games successfully stored
        """
        stored = 0

        # Get current week ID
        result = self.db.execute(text("""
            SELECT id FROM weeks
            ORDER BY id DESC
            LIMIT 1
        """))
        week_row = result.first()
        week_id = week_row[0] if week_row else None

        if not week_id:
            self.logger.warning("Could not find current week for ITT storage")
            return 0

        for game in games:
            try:
                away_team = game.get("away_team", "")
                home_team = game.get("home_team", "")
                away_itt = game.get("away_team_itt")
                home_itt = game.get("home_team_itt")

                if not away_team or not home_team:
                    continue

                # Update away team ITT
                if away_itt is not None:
                    self.db.execute(text("""
                        UPDATE vegas_lines
                        SET implied_team_total = :itt, opponent_team = :opponent, updated_at = :now
                        WHERE week_id = :week_id AND team = :team
                    """), {
                        "itt": away_itt,
                        "opponent": home_team,
                        "now": datetime.utcnow(),
                        "week_id": week_id,
                        "team": away_team,
                    })
                    stored += 1

                # Update home team ITT
                if home_itt is not None:
                    self.db.execute(text("""
                        UPDATE vegas_lines
                        SET implied_team_total = :itt, opponent_team = :opponent, updated_at = :now
                        WHERE week_id = :week_id AND team = :team
                    """), {
                        "itt": home_itt,
                        "opponent": away_team,
                        "now": datetime.utcnow(),
                        "week_id": week_id,
                        "team": home_team,
                    })
                    stored += 1

            except Exception as e:
                self.logger.debug(
                    f"Error storing ITT for {game.get('away_team')} vs "
                    f"{game.get('home_team')}: {str(e)}"
                )

        try:
            self.db.commit()
        except Exception as e:
            self.logger.error(f"Error committing vegas_lines updates: {str(e)}")
            self.db.rollback()
            stored = 0

        return stored

    async def _store_team_defense_stats(self, team_stats: dict) -> int:
        """
        Store team defensive statistics.

        Args:
            team_stats: Dictionary of team defensive stats from API

        Returns:
            Number of teams successfully stored
        """
        stored = 0

        # Get current season
        result = self.db.execute(text("""
            SELECT season FROM weeks
            ORDER BY id DESC
            LIMIT 1
        """))
        week_row = result.first()
        season = week_row[0] if week_row else None

        if not season:
            self.logger.warning("Could not determine current season for team stats storage")
            return 0

        for team_abbr, stats in team_stats.items():
            try:
                pass_rank = stats.get("pass_defense_rank")
                rush_rank = stats.get("rush_defense_rank")

                # Try to update existing record
                result = self.db.execute(text("""
                    UPDATE team_defense_stats
                    SET pass_defense_rank = :pass_rank,
                        rush_defense_rank = :rush_rank,
                        updated_at = :now
                    WHERE season = :season AND team_abbr = :team_abbr
                """), {
                    "pass_rank": pass_rank,
                    "rush_rank": rush_rank,
                    "now": datetime.utcnow(),
                    "season": season,
                    "team_abbr": team_abbr,
                })

                # If no rows updated, try to insert
                if result.rowcount == 0:
                    self.db.execute(text("""
                        INSERT INTO team_defense_stats
                        (season, team_abbr, pass_defense_rank, rush_defense_rank, created_at, updated_at)
                        VALUES (:season, :team_abbr, :pass_rank, :rush_rank, :now, :now)
                    """), {
                        "season": season,
                        "team_abbr": team_abbr,
                        "pass_rank": pass_rank,
                        "rush_rank": rush_rank,
                        "now": datetime.utcnow(),
                    })

                stored += 1

            except Exception as e:
                self.logger.debug(
                    f"Error storing defensive stats for {team_abbr}: {str(e)}"
                )

        try:
            self.db.commit()
        except Exception as e:
            self.logger.error(f"Error committing team_defense_stats updates: {str(e)}")
            self.db.rollback()
            stored = 0

        return stored

    async def _store_player_gamelogs(self, gamelogs: list) -> int:
        """
        Store player gamelogs in historical_stats.

        Args:
            gamelogs: List of gamelog dictionaries from API

        Returns:
            Number of gamelogs successfully stored
        """
        stored = 0

        for gamelog in gamelogs:
            try:
                first_name = gamelog.get("player_first_name", "")
                last_name = gamelog.get("player_last_name", "")
                team = gamelog.get("team", "")
                game_date = gamelog.get("game_date", "")

                # Find player in player_pools
                result = self.db.execute(text("""
                    SELECT id FROM player_pools
                    WHERE first_name = :first_name
                    AND last_name = :last_name
                    AND team = :team
                    LIMIT 1
                """), {
                    "first_name": first_name,
                    "last_name": last_name,
                    "team": team,
                })

                player_row = result.first()
                if not player_row:
                    self.logger.debug(
                        f"Player not found: {first_name} {last_name} ({team})"
                    )
                    continue

                player_id = player_row[0]

                # Determine week number from game date
                week_result = self.db.execute(text("""
                    SELECT id, week_number FROM weeks
                    WHERE nfl_slate_date = :date
                    LIMIT 1
                """), {"date": game_date})

                week_row = week_result.first()
                if not week_row:
                    self.logger.debug(f"Week not found for date: {game_date}")
                    continue

                week_id, week_number = week_row[0], week_row[1]

                # Extract stats
                snaps = gamelog.get("snaps")
                targets = gamelog.get("targets")
                receptions = gamelog.get("receptions")
                passing_yards = gamelog.get("passing_yards")
                rushing_yards = gamelog.get("rushing_yards")
                receiving_yards = gamelog.get("receiving_yards")

                # Check if record exists
                result = self.db.execute(text("""
                    SELECT id FROM historical_stats
                    WHERE player_id = :player_id AND week_id = :week_id
                    LIMIT 1
                """), {
                    "player_id": player_id,
                    "week_id": week_id,
                })

                stat_row = result.first()

                if stat_row:
                    # Update existing record
                    self.db.execute(text("""
                        UPDATE historical_stats
                        SET snaps = COALESCE(:snaps, snaps),
                            targets = COALESCE(:targets, targets),
                            receptions = COALESCE(:receptions, receptions),
                            passing_yards = COALESCE(:passing_yards, passing_yards),
                            rushing_yards = COALESCE(:rushing_yards, rushing_yards),
                            receiving_yards = COALESCE(:receiving_yards, receiving_yards),
                            updated_at = :now
                        WHERE id = :id
                    """), {
                        "snaps": snaps,
                        "targets": targets,
                        "receptions": receptions,
                        "passing_yards": passing_yards,
                        "rushing_yards": rushing_yards,
                        "receiving_yards": receiving_yards,
                        "now": datetime.utcnow(),
                        "id": stat_row[0],
                    })
                else:
                    # Insert new record
                    self.db.execute(text("""
                        INSERT INTO historical_stats
                        (player_id, week_id, snaps, targets, receptions,
                         passing_yards, rushing_yards, receiving_yards, created_at, updated_at)
                        VALUES (:player_id, :week_id, :snaps, :targets, :receptions,
                                :passing_yards, :rushing_yards, :receiving_yards, :now, :now)
                    """), {
                        "player_id": player_id,
                        "week_id": week_id,
                        "snaps": snaps,
                        "targets": targets,
                        "receptions": receptions,
                        "passing_yards": passing_yards,
                        "rushing_yards": rushing_yards,
                        "receiving_yards": receiving_yards,
                        "now": datetime.utcnow(),
                    })

                stored += 1

            except Exception as e:
                self.logger.debug(
                    f"Error storing gamelog for {gamelog.get('player_first_name')} "
                    f"{gamelog.get('player_last_name')}: {str(e)}"
                )

        try:
            self.db.commit()
        except Exception as e:
            self.logger.error(f"Error committing gamelogs updates: {str(e)}")
            self.db.rollback()
            stored = 0

        return stored
