"""
ESPNService for fetching free NFL data from ESPN public APIs.

Provides methods for:
- Fetching opponent information for teams in a given week
- Fetching injury data by team
- Getting game schedules

Note: ESPN APIs are unofficial but publicly accessible.
No authentication required, but rate limits may apply.
"""

import logging
import httpx
from typing import Optional, Dict, List, Any
from datetime import datetime, date
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ESPNService:
    """Service for fetching data from ESPN public APIs."""

    def __init__(self, db_session: Optional[Session] = None):
        """
        Initialize ESPNService.

        Args:
            db_session: SQLAlchemy Session for database operations (optional)
        """
        self.db = db_session
        self.base_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
        self.client = httpx.AsyncClient(timeout=30.0)
        self.logger = logger

    async def fetch_week_schedule(self, year: int, week: int) -> List[Dict[str, Any]]:
        """
        Fetch NFL schedule for a specific week.

        Args:
            year: Season year (e.g., 2025)
            week: Week number (1-18)

        Returns:
            List of game dictionaries with:
            - home_team: Team abbreviation
            - away_team: Team abbreviation
            - game_id: ESPN game ID
            - date: Game date
        """
        try:
            # ESPN uses the scoreboard endpoint with week parameter
            url = f"{self.base_url}/scoreboard"
            params = {
                "seasontype": 2,  # Regular season (1=preseason, 2=regular, 3=postseason)
                "week": week,
            }

            self.logger.debug(f"Fetching ESPN schedule for {year} week {week}")
            response = await self.client.get(url, params=params)

            if response.status_code != 200:
                self.logger.warning(f"ESPN API returned {response.status_code} for week {week}")
                return []

            data = response.json()
            games = []

            for event in data.get("events", []):
                try:
                    competition = event.get("competitions", [{}])[0]
                    competitors = competition.get("competitors", [])

                    if len(competitors) < 2:
                        continue

                    # Determine home/away
                    home_team = None
                    away_team = None

                    for competitor in competitors:
                        team_abbr = competitor.get("team", {}).get("abbreviation", "")
                        if competitor.get("homeAway") == "home":
                            home_team = team_abbr
                        else:
                            away_team = team_abbr

                    if not home_team or not away_team:
                        continue

                    game_date = competition.get("date", "")

                    games.append({
                        "home_team": home_team.upper(),
                        "away_team": away_team.upper(),
                        "game_id": event.get("id", ""),
                        "date": game_date,
                    })

                except Exception as e:
                    self.logger.debug(f"Error parsing game event: {e}")
                    continue

            self.logger.info(f"Fetched {len(games)} games from ESPN for week {week}")
            return games

        except Exception as e:
            self.logger.error(f"Error fetching ESPN schedule: {e}")
            return []

    async def get_opponent_for_team(self, team: str, year: int, week: int) -> Optional[str]:
        """
        Get opponent team abbreviation for a given team in a specific week.

        Args:
            team: Team abbreviation (e.g., "KC")
            year: Season year
            week: Week number

        Returns:
            Opponent team abbreviation (e.g., "BUF") or None if not found
        """
        try:
            team = team.upper()
            games = await self.fetch_week_schedule(year, week)

            for game in games:
                if game["home_team"] == team:
                    return game["away_team"]
                elif game["away_team"] == team:
                    return game["home_team"]

            self.logger.debug(f"No opponent found for {team} in week {week}")
            return None

        except Exception as e:
            self.logger.error(f"Error getting opponent for {team} in week {week}: {e}")
            return None

    async def fetch_team_injuries(self, team: str) -> List[Dict[str, Any]]:
        """
        Fetch injury data for a specific team from ESPN.

        Args:
            team: Team abbreviation (e.g., "KC")

        Returns:
            List of injury dictionaries with:
            - player_name: Full player name
            - position: Player position
            - injury_status: Injury status (e.g., "Questionable", "Doubtful", "Out")
            - injury_details: Injury description
        """
        try:
            team = team.upper()
            url = f"{self.base_url}/injuries"
            params = {"team": team}

            self.logger.debug(f"Fetching ESPN injuries for {team}")
            response = await self.client.get(url, params=params)

            if response.status_code != 200:
                self.logger.warning(f"ESPN API returned {response.status_code} for injuries")
                return []

            data = response.json()
            injuries = []

            # ESPN injury structure: uses "athlete" and "status" directly
            for injury_entry in data.get("injuries", []):
                try:
                    athlete = injury_entry.get("athlete", {})
                    status = injury_entry.get("status", "")

                    player_name = athlete.get("displayName", "")
                    if not player_name:
                        # Fallback to firstName + lastName
                        first_name = athlete.get("firstName", "")
                        last_name = athlete.get("lastName", "")
                        player_name = f"{first_name} {last_name}".strip()
                    
                    if not player_name:
                        continue

                    # Map ESPN status to our format
                    # ESPN uses: "Active", "Questionable", "Doubtful", "Out", etc.
                    status_mapping = {
                        "Questionable": "QUESTIONABLE",
                        "Doubtful": "DOUBTFUL",
                        "Out": "OUT",
                        "Probable": "PROBABLE",
                        "Active": "PROBABLE",  # Active means likely playing
                    }
                    normalized_status = status_mapping.get(status, status.upper())
                    
                    # Get position from athlete if available, or try to extract from comment
                    position = ""  # ESPN injuries don't always include position
                    injury_details = injury_entry.get("shortComment", "") or injury_entry.get("longComment", "")

                    injuries.append({
                        "player_name": player_name,
                        "position": position,
                        "team": team,
                        "injury_status": normalized_status,
                        "injury_details": injury_details,
                    })

                except Exception as e:
                    self.logger.debug(f"Error parsing injury entry: {e}")
                    continue

            self.logger.info(f"Fetched {len(injuries)} injuries from ESPN for {team}")
            return injuries

        except Exception as e:
            self.logger.error(f"Error fetching ESPN injuries for {team}: {e}")
            return []

    async def fetch_all_injuries(self) -> List[Dict[str, Any]]:
        """
        Fetch injury data for all teams.

        Returns:
            List of all injury dictionaries across all teams
        """
        nfl_teams = [
            "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE",
            "DAL", "DEN", "DET", "GB", "HOU", "IND", "JAX", "KC",
            "LV", "LAC", "LAR", "MIA", "MIN", "NE", "NO", "NYG",
            "NYJ", "PHI", "PIT", "SF", "SEA", "TB", "TEN", "WAS"
        ]

        all_injuries = []
        for team in nfl_teams:
            injuries = await self.fetch_team_injuries(team)
            all_injuries.extend(injuries)

        return all_injuries

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

