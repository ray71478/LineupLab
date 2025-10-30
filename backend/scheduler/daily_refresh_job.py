"""
DailyDataRefreshJob for orchestrating Vegas lines data refresh.

Coordinates API calls and stores results in database:
- Vegas lines → vegas_lines (game totals from TheOddsAPI)

Includes error handling, logging, and status tracking.
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
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
        """Fetch games with all odds and store in vegas_lines."""
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

    async def _store_vegas_lines(self, games: list) -> int:
        """
        Store Vegas game totals and multi-sportsbook odds.

        Args:
            games: List of game dictionaries from TheOddsAPI with sportsbooks array

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
            self.logger.warning("Could not find current week for game totals storage")
            return 0

        for game in games:
            try:
                away_team = game.get("away_team", "")
                home_team = game.get("home_team", "")
                game_total = game.get("game_total")
                sportsbooks = game.get("sportsbooks", [])

                if not away_team or not home_team:
                    continue

                # Calculate implied team total (ITT) from game total
                # ITT = game_total / 2 (approximately)
                itt = game_total / 2 if game_total else None

                if itt is None:
                    self.logger.debug(f"No game total for {away_team} vs {home_team}")
                    continue

                # Store consensus odds from first sportsbook in vegas_lines (for backwards compatibility)
                if sportsbooks:
                    first_book = sportsbooks[0]
                    away_spread = first_book.get("away_spread")
                    home_spread = first_book.get("home_spread")
                    away_moneyline = first_book.get("away_moneyline")
                    home_moneyline = first_book.get("home_moneyline")

                    # Update away team with all odds
                    self.db.execute(text("""
                        UPDATE vegas_lines
                        SET implied_team_total = :itt,
                            opponent = :opponent,
                            spread = :spread,
                            over_under = :over_under,
                            moneyline_odds = :moneyline,
                            updated_at = :now
                        WHERE week_id = :week_id AND team = :team
                    """), {
                        "itt": itt,
                        "opponent": home_team,
                        "spread": away_spread,
                        "over_under": game_total,
                        "moneyline": away_moneyline,
                        "now": datetime.utcnow(),
                        "week_id": week_id,
                        "team": away_team,
                    })

                    # Update home team with all odds
                    self.db.execute(text("""
                        UPDATE vegas_lines
                        SET implied_team_total = :itt,
                            opponent = :opponent,
                            spread = :spread,
                            over_under = :over_under,
                            moneyline_odds = :moneyline,
                            updated_at = :now
                        WHERE week_id = :week_id AND team = :team
                    """), {
                        "itt": itt,
                        "opponent": away_team,
                        "spread": home_spread,
                        "over_under": game_total,
                        "moneyline": home_moneyline,
                        "now": datetime.utcnow(),
                        "week_id": week_id,
                        "team": home_team,
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
