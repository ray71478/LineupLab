"""
TheOddsAPI Service for fetching NFL Vegas lines (game totals).

Provides methods for:
- Fetching current week games with over/under totals
- Extracting implied team totals (ITT) from game totals
- Storing results in database

Authentication: API Key via query parameter
API Version: v4
Free Tier: 500 requests/month
"""

import logging
import httpx
import os
from typing import Optional, Dict, List, Any
from datetime import datetime
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Map full team names from TheOddsAPI to NFL abbreviations
TEAM_NAME_MAP = {
    "Baltimore Ravens": "BAL",
    "Miami Dolphins": "MIA",
    "Atlanta Falcons": "ATL",
    "New England Patriots": "NE",
    "Carolina Panthers": "CAR",
    "Green Bay Packers": "GB",
    "Chicago Bears": "CHI",
    "Cincinnati Bengals": "CIN",
    "Denver Broncos": "DEN",
    "Houston Texans": "HOU",
    "Indianapolis Colts": "IND",
    "Jacksonville Jaguars": "JAX",
    "Kansas City Chiefs": "KC",
    "Los Angeles Chargers": "LAC",
    "Los Angeles Rams": "LAR",
    "Las Vegas Raiders": "LV",
    "Minnesota Vikings": "MIN",
    "Detroit Lions": "DET",
    "New Orleans Saints": "NO",
    "Tampa Bay Buccaneers": "TB",
    "Tennessee Titans": "TEN",
    "New York Jets": "NYJ",
    "Buffalo Bills": "BUF",
    "New York Giants": "NYG",
    "Philadelphia Eagles": "PHI",
    "Washington Commanders": "WAS",
    "Dallas Cowboys": "DAL",
    "Pittsburgh Steelers": "PIT",
    "Cleveland Browns": "CLE",
    "San Francisco 49ers": "SF",
    "Seattle Seahawks": "SEA",
    "Arizona Cardinals": "ARI",
}


class TheOddsAPIService:
    """Service for fetching NFL game totals from TheOddsAPI."""

    def __init__(self, db_session: Session, api_key: Optional[str] = None):
        """
        Initialize TheOddsAPIService.

        Args:
            db_session: SQLAlchemy Session for database operations
            api_key: TheOddsAPI key (optional, loads from env if not provided)

        Raises:
            ValueError: If API key not provided and not in environment
        """
        self.db = db_session
        self.api_key = api_key or os.getenv("TheOddsAPI")

        if not self.api_key:
            raise ValueError(
                "TheOddsAPI not found in environment variables. "
                "Please set TheOddsAPI in .env file."
            )

        self.base_url = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds"
        self.client = httpx.AsyncClient(timeout=30.0)
        self.logger = logger

    async def fetch_games_with_odds(self) -> List[Dict[str, Any]]:
        """
        Fetch NFL games with all available odds from all sportsbooks.

        Makes request to TheOddsAPI odds endpoint with markets=totals,spreads,h2h
        and extracts game schedule and betting lines from multiple sportsbooks.

        Returns:
            List of dictionaries with structure:
            [
                {
                    'away_team': str (abbreviation),
                    'home_team': str (abbreviation),
                    'commence_time': datetime or None,
                    'game_total': float or None,  # Over/Under total (from first book)
                    'sportsbooks': [  # All sportsbooks with their odds
                        {
                            'name': str,
                            'away_spread': float or None,
                            'away_moneyline': float or None,
                            'home_spread': float or None,
                            'home_moneyline': float or None,
                            'over_under': float or None,
                        },
                        ...
                    ]
                }
            ]
            Empty list if fetch fails.
        """
        try:
            params = {
                "apiKey": self.api_key,
                "regions": "us",
                "markets": "totals,spreads,h2h",
            }

            self.logger.debug("Fetching games with all odds from TheOddsAPI")

            response = await self.client.get(self.base_url, params=params)

            if response.status_code != 200:
                self.logger.error(
                    f"TheOddsAPI returned status {response.status_code}: {response.text[:200]}"
                )
                return []

            data = response.json()
            games = []
            game_list = data if isinstance(data, list) else data.get("games", [])

            for game in game_list:
                try:
                    # Extract teams and convert to abbreviations
                    away_team_full = game.get("away_team", "")
                    home_team_full = game.get("home_team", "")

                    away_team = TEAM_NAME_MAP.get(away_team_full, "")
                    home_team = TEAM_NAME_MAP.get(home_team_full, "")

                    if not away_team or not home_team:
                        self.logger.debug(
                            f"Skipping game - could not map team names: "
                            f"{away_team_full} vs {home_team_full}"
                        )
                        continue

                    # Extract start time
                    commence_time_str = game.get("commence_time")
                    commence_time = None
                    if commence_time_str:
                        try:
                            commence_time = datetime.fromisoformat(
                                commence_time_str.replace("Z", "+00:00")
                            )
                        except Exception as e:
                            self.logger.debug(f"Could not parse start time: {commence_time_str}")

                    # Extract odds from all sportsbooks
                    game_total = None
                    sportsbooks_data = []

                    bookmakers = game.get("bookmakers", [])
                    if bookmakers:
                        # Get game total from first book that has it
                        for bookmaker in bookmakers:
                            markets = bookmaker.get("markets", [])
                            for market in markets:
                                if market.get("key") == "totals" and market.get("outcomes"):
                                    game_total = market["outcomes"][0].get("point")
                                    break
                            if game_total:
                                break

                        # Collect odds from each sportsbook
                        for bookmaker in bookmakers:
                            book_name = bookmaker.get("title", "Unknown")
                            markets = bookmaker.get("markets", [])

                            away_spread = None
                            home_spread = None
                            away_moneyline = None
                            home_moneyline = None
                            over_under = None

                            for market in markets:
                                market_key = market.get("key")
                                outcomes = market.get("outcomes", [])

                                if market_key == "totals" and outcomes:
                                    over_under = outcomes[0].get("point")

                                elif market_key == "spreads" and outcomes:
                                    # Extract spreads for both teams
                                    for outcome in outcomes:
                                        team_name = outcome.get("name", "")
                                        spread_point = outcome.get("point")

                                        if team_name == away_team_full:
                                            away_spread = spread_point
                                        elif team_name == home_team_full:
                                            home_spread = spread_point

                                elif market_key == "h2h" and outcomes:
                                    # Extract moneyline for both teams
                                    for outcome in outcomes:
                                        team_name = outcome.get("name", "")
                                        odds = outcome.get("price")

                                        if team_name == away_team_full:
                                            away_moneyline = odds
                                        elif team_name == home_team_full:
                                            home_moneyline = odds

                            sportsbooks_data.append({
                                "name": book_name,
                                "away_spread": away_spread,
                                "away_moneyline": away_moneyline,
                                "home_spread": home_spread,
                                "home_moneyline": home_moneyline,
                                "over_under": over_under,
                            })

                    games.append({
                        "away_team": away_team.upper(),
                        "home_team": home_team.upper(),
                        "commence_time": commence_time,
                        "game_total": game_total,
                        "sportsbooks": sportsbooks_data,
                    })

                except Exception as e:
                    self.logger.debug(f"Error parsing game data: {str(e)}")
                    continue

            # Count sportsbooks coverage
            total_sportsbook_entries = sum(
                len(g.get('sportsbooks', [])) for g in games
            )

            self.logger.info(
                f"Fetched {len(games)} games from {total_sportsbook_entries} sportsbook entries. "
                f"Games with totals: {sum(1 for g in games if g['game_total'] is not None)}"
            )

            return games

        except Exception as e:
            self.logger.error(f"Error in fetch_games_with_odds: {str(e)}")
            return []

    async def close(self):
        """Close the HTTP client connection."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
