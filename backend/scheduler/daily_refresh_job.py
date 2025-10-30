"""
DailyDataRefreshJob for orchestrating Vegas lines data refresh.

Coordinates API calls and stores results in database:
- Vegas lines → vegas_lines (game totals from TheOddsAPI)

Handles ALL upcoming weeks, not just the current one, by mapping games
from TheOddsAPI to their correct week_id based on game commence_time.

Includes error handling, logging, and status tracking.
"""

import logging
import asyncio
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.services.theoddsapi_service import TheOddsAPIService

logger = logging.getLogger(__name__)


class DailyDataRefreshJob:
    """Orchestrates daily Vegas lines refresh from TheOddsAPI."""

    def __init__(self, db_session: Session):
        """
        Initialize DailyDataRefreshJob.

        Args:
            db_session: SQLAlchemy Session for database operations
        """
        self.db = db_session
        self.service: Optional[TheOddsAPIService] = None
        self.logger = logger
        self.start_time: Optional[datetime] = None
        self.results: Dict[str, Any] = {}

    async def execute(self) -> Dict[str, Any]:
        """
        Execute complete daily data refresh workflow.

        Orchestrates API call to fetch Vegas lines:
        1. Fetch games with over/under totals from TheOddsAPI
        2. Store game totals in vegas_lines table

        Stores results in database and returns summary.

        Returns:
            Dictionary with execution summary:
            {
                'success': bool,
                'start_time': datetime,
                'end_time': datetime,
                'duration_seconds': float,
                'games': {
                    'fetched': int,
                    'stored': int,
                    'errors': int,
                },
                'errors': [str, ...],
            }
        """
        self.start_time = datetime.utcnow()
        self.logger.info(f"Starting daily Vegas lines refresh at {self.start_time}")

        # Initialize service
        try:
            self.service = TheOddsAPIService(self.db)
        except ValueError as e:
            self.logger.error(f"Failed to initialize TheOddsAPIService: {str(e)}")
            return {
                "success": False,
                "start_time": self.start_time,
                "end_time": datetime.utcnow(),
                "duration_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
                "errors": [str(e)],
            }

        try:
            # Execute refresh step
            await self._fetch_and_store_games()

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
                f"Games: {result.get('games', {}).get('stored', 0)} game totals stored"
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

    async def _fetch_and_store_games(self) -> None:
        """Fetch games with all odds and store in vegas_lines for ALL upcoming weeks."""
        try:
            self.logger.info("Fetching games with all odds from TheOddsAPI...")

            games = await self.service.fetch_games_with_odds()

            if not games:
                self.results["games"] = {
                    "fetched": 0,
                    "stored": 0,
                    "errors": 0,
                }
                return

            # Get upcoming weeks to map games to correct week_id
            upcoming_weeks = self._get_upcoming_weeks()
            if not upcoming_weeks:
                self.logger.warning("No upcoming weeks found in database")
                self.results["games"] = {
                    "fetched": len(games),
                    "stored": 0,
                    "errors": len(games),
                }
                return

            # Store in database
            stored = await self._store_vegas_lines(games, upcoming_weeks)

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

    def _get_upcoming_weeks(self) -> List[Tuple[int, date]]:
        """
        Get all upcoming weeks with their NFL slate dates.

        Returns:
            List of tuples (week_id, nfl_slate_date) for all upcoming weeks.
            Sorted by slate_date ascending.
        """
        try:
            today = date.today()
            result = self.db.execute(text("""
                SELECT id, nfl_slate_date
                FROM weeks
                WHERE nfl_slate_date >= :today
                ORDER BY nfl_slate_date ASC
            """), {"today": today})

            weeks = result.fetchall()
            self.logger.info(f"Found {len(weeks)} upcoming weeks")
            return weeks if weeks else []
        except Exception as e:
            self.logger.error(f"Error fetching upcoming weeks: {str(e)}")
            return []

    def _map_game_to_week(self, game_commence_time: Optional[datetime], upcoming_weeks: List[Tuple[int, date]]) -> Optional[int]:
        """
        Map a game to its correct week based on commence_time and week slate dates.

        NFL weeks typically span Thursday-Monday, with games starting Thursday or Sunday.
        We match the game's commence_time to the week that contains it.

        Args:
            game_commence_time: When the game is scheduled to start (UTC)
            upcoming_weeks: List of (week_id, nfl_slate_date) tuples

        Returns:
            week_id if match found, None otherwise
        """
        if not game_commence_time or not upcoming_weeks:
            return None

        # Convert commence_time to date
        game_date = game_commence_time.date() if hasattr(game_commence_time, 'date') else game_commence_time

        # Find the week containing this game
        # Game belongs to the week where its date matches the nfl_slate_date
        # or is within a few days after the slate date
        for week_id, slate_date in upcoming_weeks:
            # Weeks typically span slate_date to slate_date + 6 days
            # (covers Thu, Fri, Sat, Sun, Mon, Tue, Wed)
            week_end = slate_date + timedelta(days=6)
            if slate_date <= game_date <= week_end:
                return week_id

        return None

    async def _store_vegas_lines(self, games: list, upcoming_weeks: List[Tuple[int, date]]) -> int:
        """
        Store Vegas game totals and multi-sportsbook odds for all upcoming weeks.

        Args:
            games: List of game dictionaries from TheOddsAPI with sportsbooks array
            upcoming_weeks: List of (week_id, nfl_slate_date) tuples for matching games to weeks

        Returns:
            Number of games successfully stored
        """
        stored = 0

        for game in games:
            try:
                away_team = game.get("away_team", "")
                home_team = game.get("home_team", "")
                game_total = game.get("game_total")
                sportsbooks = game.get("sportsbooks", [])
                commence_time = game.get("commence_time")

                if not away_team or not home_team:
                    continue

                if game_total is None:
                    self.logger.debug(f"No game total for {away_team} vs {home_team}")
                    continue

                # Map game to its correct week based on commence_time
                week_id = self._map_game_to_week(commence_time, upcoming_weeks)
                if not week_id:
                    self.logger.debug(
                        f"Could not map {away_team} vs {home_team} to any upcoming week "
                        f"(commence_time: {commence_time})"
                    )
                    continue

                # Store consensus odds from first sportsbook in vegas_lines (for backwards compatibility)
                if sportsbooks:
                    first_book = sportsbooks[0]
                    away_spread = first_book.get("away_spread")
                    home_spread = first_book.get("home_spread")
                    away_moneyline = first_book.get("away_moneyline")
                    home_moneyline = first_book.get("home_moneyline")

                    # Calculate true implied team totals using spread
                    # ITT = (game_total - team_spread) / 2
                    # Negative spread means favored, so they get higher ITT
                    # Positive spread means underdog, so they get lower ITT
                    away_itt = None
                    home_itt = None

                    if away_spread is not None:
                        away_itt = (game_total - away_spread) / 2

                    if home_spread is not None:
                        home_itt = (game_total - home_spread) / 2

                    # Upsert away team with all odds
                    self.db.execute(text("""
                        INSERT INTO vegas_lines
                        (week_id, team, opponent, implied_team_total, spread, over_under, moneyline_odds, home_team, fetched_at, created_at, updated_at)
                        VALUES (:week_id, :team, :opponent, :itt, :spread, :over_under, :moneyline, :home_team, :now, :now, :now)
                        ON CONFLICT (week_id, team) DO UPDATE SET
                            opponent = EXCLUDED.opponent,
                            implied_team_total = EXCLUDED.implied_team_total,
                            spread = EXCLUDED.spread,
                            over_under = EXCLUDED.over_under,
                            moneyline_odds = EXCLUDED.moneyline_odds,
                            updated_at = EXCLUDED.updated_at
                    """), {
                        "week_id": week_id,
                        "team": away_team,
                        "opponent": home_team,
                        "itt": away_itt,
                        "spread": away_spread,
                        "over_under": game_total,
                        "moneyline": away_moneyline,
                        "home_team": False,
                        "now": datetime.utcnow(),
                    })

                    # Upsert home team with all odds
                    self.db.execute(text("""
                        INSERT INTO vegas_lines
                        (week_id, team, opponent, implied_team_total, spread, over_under, moneyline_odds, home_team, fetched_at, created_at, updated_at)
                        VALUES (:week_id, :team, :opponent, :itt, :spread, :over_under, :moneyline, :home_team, :now, :now, :now)
                        ON CONFLICT (week_id, team) DO UPDATE SET
                            opponent = EXCLUDED.opponent,
                            implied_team_total = EXCLUDED.implied_team_total,
                            spread = EXCLUDED.spread,
                            over_under = EXCLUDED.over_under,
                            moneyline_odds = EXCLUDED.moneyline_odds,
                            updated_at = EXCLUDED.updated_at
                    """), {
                        "week_id": week_id,
                        "team": home_team,
                        "opponent": away_team,
                        "itt": home_itt,
                        "spread": home_spread,
                        "over_under": game_total,
                        "moneyline": home_moneyline,
                        "home_team": True,
                        "now": datetime.utcnow(),
                    })

                    stored += 1

                # Store all sportsbook odds in sportsbook_odds table
                for book in sportsbooks:
                    book_name = book.get("name", "Unknown")

                    # Store away team odds
                    if book.get("away_spread") is not None or book.get("away_moneyline"):
                        self.db.execute(text("""
                            INSERT INTO sportsbook_odds
                            (week_id, team, opponent, sportsbook, spread, moneyline_odds, over_under, home_team, fetched_at, created_at, updated_at)
                            VALUES (:week_id, :team, :opponent, :sportsbook, :spread, :moneyline, :over_under, :home_team, :now, :now, :now)
                            ON CONFLICT (week_id, team, sportsbook) DO UPDATE SET
                                spread = EXCLUDED.spread,
                                moneyline_odds = EXCLUDED.moneyline_odds,
                                over_under = EXCLUDED.over_under,
                                updated_at = EXCLUDED.updated_at
                        """), {
                            "week_id": week_id,
                            "team": away_team,
                            "opponent": home_team,
                            "sportsbook": book_name,
                            "spread": book.get("away_spread"),
                            "moneyline": book.get("away_moneyline"),
                            "over_under": book.get("over_under"),
                            "home_team": False,
                            "now": datetime.utcnow(),
                        })

                    # Store home team odds
                    if book.get("home_spread") is not None or book.get("home_moneyline"):
                        self.db.execute(text("""
                            INSERT INTO sportsbook_odds
                            (week_id, team, opponent, sportsbook, spread, moneyline_odds, over_under, home_team, fetched_at, created_at, updated_at)
                            VALUES (:week_id, :team, :opponent, :sportsbook, :spread, :moneyline, :over_under, :home_team, :now, :now, :now)
                            ON CONFLICT (week_id, team, sportsbook) DO UPDATE SET
                                spread = EXCLUDED.spread,
                                moneyline_odds = EXCLUDED.moneyline_odds,
                                over_under = EXCLUDED.over_under,
                                updated_at = EXCLUDED.updated_at
                        """), {
                            "week_id": week_id,
                            "team": home_team,
                            "opponent": away_team,
                            "sportsbook": book_name,
                            "spread": book.get("home_spread"),
                            "moneyline": book.get("home_moneyline"),
                            "over_under": book.get("over_under"),
                            "home_team": True,
                            "now": datetime.utcnow(),
                        })

            except Exception as e:
                self.logger.debug(
                    f"Error storing game odds for {game.get('away_team')} vs "
                    f"{game.get('home_team')}: {str(e)}"
                )

        try:
            self.db.commit()
        except Exception as e:
            self.logger.error(f"Error committing vegas odds updates: {str(e)}")
            self.db.rollback()
            stored = 0

        return stored
