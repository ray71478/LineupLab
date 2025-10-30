"""
MySportsFeedsService for fetching and managing external NFL data.

Provides methods for:
- Fetching current week player injuries
- Fetching weekly games with Vegas Implied Team Total (ITT)
- Fetching seasonal team defensive statistics
- Fetching daily player gamelogs for trend analysis

Authentication: HTTP Basic Auth with MySportsFeeds token
API Version: v2.1
"""

import logging
import asyncio
import httpx
import os
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class MySportsFeedsService:
    """Service for fetching data from MySportsFeeds v2.1 API."""

    def __init__(self, db_session: Session, token: Optional[str] = None):
        """
        Initialize MySportsFeedsService.

        Args:
            db_session: SQLAlchemy Session for database operations
            token: MySportsFeeds API token (optional, loads from env if not provided)

        Raises:
            ValueError: If token not provided and not in environment
        """
        self.db = db_session
        self.token = token or os.getenv("MYSPORTSFEEDS_TOKEN")

        if not self.token:
            raise ValueError(
                "MYSPORTSFEEDS_TOKEN not found in environment variables. "
                "Please set MYSPORTSFEEDS_TOKEN in .env file."
            )

        self.base_url = "https://api.mysportsfeeds.com/v2.1/pull/nfl"
        self.client = httpx.AsyncClient(timeout=30.0)
        self.logger = logger
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.retry_backoffs = [5, 10, 20]  # seconds

    async def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request to MySportsFeeds API with retry logic.

        Implements exponential backoff for retries (5s, 10s, 20s).
        Respects 429 (rate limit) responses with Retry-After header.
        Logs all requests and errors.

        Args:
            endpoint: API endpoint path (e.g., "/injuries.json")
            params: Query parameters as dictionary

        Returns:
            Parsed JSON response as dictionary, or None if request fails after retries
        """
        url = f"{self.base_url}{endpoint}"

        # Create Basic Auth header
        auth_string = f"{self.token}:MYSPORTSFEEDS"
        headers = {
            "Authorization": f"Basic {self._encode_basic_auth(auth_string)}"
        }

        for attempt in range(self.max_retries + 1):
            try:
                self.logger.debug(f"Requesting {endpoint} (attempt {attempt + 1}/{self.max_retries + 1})")

                response = await self.client.get(url, params=params, headers=headers)

                # Handle 429 (rate limit)
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", "60"))
                    self.logger.warning(
                        f"Rate limited on {endpoint}. "
                        f"Waiting {retry_after}s before retry."
                    )
                    if attempt < self.max_retries:
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        self.logger.error(
                            f"Rate limited on {endpoint}. "
                            f"Max retries exceeded after {retry_after}s wait."
                        )
                        return None

                # Handle 401 (unauthorized)
                if response.status_code == 401:
                    self.logger.error(
                        f"Unauthorized access to {endpoint}. "
                        f"Check MYSPORTSFEEDS_TOKEN validity."
                    )
                    raise ValueError("Invalid MySportsFeeds token")

                # Handle 4xx errors (except 429 and 401)
                if 400 <= response.status_code < 429 or response.status_code > 429:
                    if response.status_code < 500:
                        self.logger.warning(
                            f"Client error {response.status_code} on {endpoint}: "
                            f"{response.text[:200]}"
                        )
                        return None

                # Handle 5xx errors with retry
                if response.status_code >= 500:
                    if attempt < self.max_retries:
                        backoff = self.retry_backoffs[min(attempt, len(self.retry_backoffs) - 1)]
                        self.logger.warning(
                            f"Server error {response.status_code} on {endpoint}. "
                            f"Retrying in {backoff}s..."
                        )
                        await asyncio.sleep(backoff)
                        continue
                    else:
                        self.logger.error(
                            f"Server error {response.status_code} on {endpoint}. "
                            f"Max retries exceeded."
                        )
                        return None

                # Success
                if response.status_code == 200:
                    try:
                        data = response.json()
                        self.logger.debug(f"Successfully fetched {endpoint}")
                        return data
                    except Exception as e:
                        self.logger.error(
                            f"JSON decode error on {endpoint}: {str(e)}"
                        )
                        return None

                # Unexpected status code
                self.logger.warning(
                    f"Unexpected status {response.status_code} on {endpoint}"
                )
                return None

            except httpx.TimeoutException as e:
                self.logger.warning(
                    f"Timeout on {endpoint} (attempt {attempt + 1}): {str(e)}"
                )
                if attempt < self.max_retries:
                    backoff = self.retry_backoffs[min(attempt, len(self.retry_backoffs) - 1)]
                    await asyncio.sleep(backoff)
                else:
                    self.logger.error(f"Timeout on {endpoint}. Max retries exceeded.")
                    return None

            except httpx.ConnectError as e:
                self.logger.warning(
                    f"Connection error on {endpoint} (attempt {attempt + 1}): {str(e)}"
                )
                if attempt < self.max_retries:
                    backoff = self.retry_backoffs[min(attempt, len(self.retry_backoffs) - 1)]
                    await asyncio.sleep(backoff)
                else:
                    self.logger.error(f"Connection error on {endpoint}. Max retries exceeded.")
                    return None

            except Exception as e:
                self.logger.error(f"Unexpected error on {endpoint}: {str(e)}")
                return None

        return None

    @staticmethod
    def _encode_basic_auth(auth_string: str) -> str:
        """
        Encode string for HTTP Basic Auth.

        Args:
            auth_string: String in format "username:password"

        Returns:
            Base64 encoded string
        """
        import base64
        return base64.b64encode(auth_string.encode()).decode()

    async def fetch_current_week_injuries(self) -> List[Dict[str, Any]]:
        """
        Fetch current week player injury data from MySportsFeeds.

        Makes request to /injuries.json?season=current endpoint and extracts:
        - Player name, position, team
        - Current injury status and playing probability

        Returns:
            List of dictionaries with structure:
            [
                {
                    'player_first_name': str,
                    'player_last_name': str,
                    'position': str,
                    'team': str,
                    'playing_probability': str (PROBABLE|QUESTIONABLE|DOUBTFUL|OUT),
                    'injury': str (optional),
                }
            ]
            Empty list if fetch fails or no injuries found.
        """
        try:
            response = await self._make_request(
                "/injuries.json",
                params={"season": "current"}
            )

            if not response:
                self.logger.warning("No injury data received from API")
                return []

            injuries = []
            players = response.get("players", [])

            for player_entry in players:
                try:
                    player = player_entry.get("player", {})
                    current_injury = player_entry.get("currentInjury", {})

                    # Extract required fields
                    first_name = player.get("firstName", "")
                    last_name = player.get("lastName", "")
                    position = player.get("position", "")
                    team_data = player.get("team", {})
                    team = team_data.get("abbr", "")

                    # Extract playing probability, default to PROBABLE if missing
                    playing_prob = current_injury.get("playingProbability", "PROBABLE")

                    # Extract injury details (optional)
                    injury = current_injury.get("playerInjury", "")

                    # Validate required fields
                    if not first_name or not last_name or not team:
                        self.logger.debug(
                            f"Skipping player entry with missing required fields: "
                            f"{first_name} {last_name} ({team})"
                        )
                        continue

                    injuries.append({
                        "player_first_name": first_name,
                        "player_last_name": last_name,
                        "position": position,
                        "team": team.upper(),
                        "playing_probability": playing_prob,
                        "injury": injury,
                    })

                except Exception as e:
                    self.logger.debug(f"Error parsing injury entry: {str(e)}")
                    continue

            self.logger.info(
                f"Fetched injuries for {len(injuries)} players. "
                f"Status breakdown: "
                f"OUT={sum(1 for i in injuries if i['playing_probability'] == 'OUT')}, "
                f"DOUBTFUL={sum(1 for i in injuries if i['playing_probability'] == 'DOUBTFUL')}, "
                f"QUESTIONABLE={sum(1 for i in injuries if i['playing_probability'] == 'QUESTIONABLE')}, "
                f"PROBABLE={sum(1 for i in injuries if i['playing_probability'] == 'PROBABLE')}"
            )

            return injuries

        except Exception as e:
            self.logger.error(f"Error in fetch_current_week_injuries: {str(e)}")
            return []

    async def fetch_weekly_games(
        self,
        season: Optional[int] = None,
        week: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch weekly games and extract Vegas Implied Team Total (ITT).

        Makes request to /{season}/week/{week}/games.json and extracts:
        - Game schedule (start time, teams)
        - Game scores (if final)
        - Vegas Implied Team Total (ITT) for Vegas Context (W7)

        Args:
            season: NFL season year (defaults to current from database)
            week: NFL week number 1-18 (defaults to current from database)

        Returns:
            List of dictionaries with structure:
            [
                {
                    'away_team': str,
                    'home_team': str,
                    'start_time': datetime or None,
                    'away_score': int or None,
                    'home_score': int or None,
                    'away_team_itt': float or None,
                    'home_team_itt': float or None,
                }
            ]
            Empty list if fetch fails.
        """
        try:
            # Query database for current season/week if not provided
            if season is None or week is None:
                current_week = self._get_current_week_info()
                if not current_week:
                    self.logger.warning("Could not determine current season/week")
                    return []
                season = current_week.get("season") if season is None else season
                week = current_week.get("week") if week is None else week

            self.logger.debug(f"Fetching games for season {season}, week {week}")

            response = await self._make_request(
                f"/{season}/week/{week}/games.json"
            )

            if not response:
                self.logger.warning(f"No games data received for week {week}")
                return []

            games = []
            game_list = response.get("games", [])

            for game in game_list:
                try:
                    schedule = game.get("schedule", {})
                    score = game.get("score", {})

                    # Extract teams
                    away_team = schedule.get("awayTeam", {}).get("abbr", "")
                    home_team = schedule.get("homeTeam", {}).get("abbr", "")

                    if not away_team or not home_team:
                        self.logger.debug("Skipping game with missing team data")
                        continue

                    # Extract start time
                    start_time_str = schedule.get("startTime")
                    start_time = None
                    if start_time_str:
                        try:
                            start_time = datetime.fromisoformat(
                                start_time_str.replace("Z", "+00:00")
                            )
                        except Exception as e:
                            self.logger.debug(f"Could not parse start time: {start_time_str}")

                    # Extract scores (may be None if not final)
                    away_score = score.get("awayScore")
                    home_score = score.get("homeScore")

                    # Extract ITT (may be in various locations)
                    away_team_itt = None
                    home_team_itt = None

                    # Check in scoring references
                    scoring = game.get("scoring", {})
                    if scoring:
                        # Look for ITT in scoring data
                        away_team_itt = scoring.get("awayTeamTotal")
                        home_team_itt = scoring.get("homeTeamTotal")

                    # Check in game metadata/custom fields
                    if not away_team_itt:
                        # Try alternative field names
                        away_team_itt = game.get("awayTeamImpliedTotal")
                    if not home_team_itt:
                        home_team_itt = game.get("homeTeamImpliedTotal")

                    games.append({
                        "away_team": away_team.upper(),
                        "home_team": home_team.upper(),
                        "start_time": start_time,
                        "away_score": away_score,
                        "home_score": home_score,
                        "away_team_itt": away_team_itt,
                        "home_team_itt": home_team_itt,
                    })

                except Exception as e:
                    self.logger.debug(f"Error parsing game data: {str(e)}")
                    continue

            self.logger.info(
                f"Fetched {len(games)} games for week {week}. "
                f"Games with ITT: "
                f"{sum(1 for g in games if g['away_team_itt'] or g['home_team_itt'])}"
            )

            return games

        except Exception as e:
            self.logger.error(f"Error in fetch_weekly_games: {str(e)}")
            return []

    async def fetch_team_defensive_stats(
        self,
        season: Optional[int] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Fetch seasonal team defensive statistics and rankings.

        Makes request to /{season}/team_stats_totals.json and extracts:
        - Pass defense ranking
        - Rush defense ranking
        - Categorizes as top_5, middle, or bottom_5

        Args:
            season: NFL season year (defaults to current from database)

        Returns:
            Dictionary with structure:
            {
                'team_abbr': {
                    'pass_defense_rank': int or None,
                    'rush_defense_rank': int or None,
                    'rank_category': str (top_5|middle|bottom_5),
                }
            }
            Empty dict if fetch fails.
        """
        try:
            # Query database for current season if not provided
            if season is None:
                current_week = self._get_current_week_info()
                if not current_week:
                    self.logger.warning("Could not determine current season")
                    return {}
                season = current_week.get("season")

            self.logger.debug(f"Fetching team defensive stats for season {season}")

            response = await self._make_request(
                f"/{season}/team_stats_totals.json"
            )

            if not response:
                self.logger.warning(f"No team stats data received for season {season}")
                return {}

            team_stats = {}
            stat_totals = response.get("teamStatTotals", [])

            for team_entry in stat_totals:
                try:
                    team = team_entry.get("team", {})
                    team_abbr = team.get("abbr", "")

                    if not team_abbr:
                        self.logger.debug("Skipping team entry with missing abbreviation")
                        continue

                    stats = team_entry.get("stats", {})

                    # Extract defensive rankings
                    # Field names may vary: passingDefensePassYardsAllowedPerGameRank, etc.
                    pass_defense_rank = (
                        stats.get("passingDefensePassYardsAllowedPerGameRank") or
                        stats.get("passingDefenseRank") or
                        None
                    )
                    rush_defense_rank = (
                        stats.get("rushingDefenseRushYardsAllowedPerGameRank") or
                        stats.get("rushingDefenseRank") or
                        None
                    )

                    # Categorize ranks: 1-5 = top_5, 6-27 = middle, 28-32 = bottom_5
                    rank_category = "middle"
                    if pass_defense_rank:
                        if pass_defense_rank <= 5:
                            rank_category = "top_5"
                        elif pass_defense_rank >= 28:
                            rank_category = "bottom_5"

                    team_stats[team_abbr.upper()] = {
                        "pass_defense_rank": pass_defense_rank,
                        "rush_defense_rank": rush_defense_rank,
                        "rank_category": rank_category,
                    }

                except Exception as e:
                    self.logger.debug(f"Error parsing team stats: {str(e)}")
                    continue

            self.logger.info(
                f"Fetched defensive stats for {len(team_stats)} teams. "
                f"Teams with pass defense rank: "
                f"{sum(1 for t in team_stats.values() if t['pass_defense_rank'])}"
            )

            return team_stats

        except Exception as e:
            self.logger.error(f"Error in fetch_team_defensive_stats: {str(e)}")
            return {}

    async def fetch_player_gamelogs(
        self,
        season: Optional[int] = None,
        date: Optional[str] = None,
        team_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch daily player gamelogs for trend analysis and historical stats backfill.

        Makes request to /{season}/date/{date}/player_gamelogs.json and extracts:
        - Player performance stats (snaps, targets, receptions)
        - Passing/rushing/receiving yards
        - Game date and opponent context

        Args:
            season: NFL season year (defaults to current from database)
            date: Game date in YYYY-MM-DD format (defaults to yesterday)
            team_filter: Filter by team (optional)

        Returns:
            List of dictionaries with structure:
            [
                {
                    'player_first_name': str,
                    'player_last_name': str,
                    'position': str,
                    'team': str,
                    'game_date': str (YYYY-MM-DD),
                    'snaps': int or None,
                    'snap_percentage': float or None,
                    'targets': int or None,
                    'receptions': int or None,
                    'passing_yards': float or None,
                    'rushing_yards': float or None,
                    'receiving_yards': float or None,
                    'receiving_td': int or None,
                    'rushing_td': int or None,
                    'passing_td': int or None,
                }
            ]
            Empty list if fetch fails.
        """
        try:
            # Query database for current season if not provided
            if season is None:
                current_week = self._get_current_week_info()
                if not current_week:
                    self.logger.warning("Could not determine current season")
                    return []
                season = current_week.get("season")

            # Default to yesterday if not provided
            if date is None:
                date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

            self.logger.debug(f"Fetching gamelogs for {date} (season {season})")

            # API requires at least one filter parameter
            params = {}
            if team_filter:
                params["team"] = team_filter.upper()
            else:
                # Use a broad filter if no specific team provided
                # The API seems to require at least one team filter for daily gamelogs
                # Try fetching without filter first, fallback if needed
                pass

            response = await self._make_request(
                f"/{season}/date/{date}/player_gamelogs.json",
                params=params if params else None
            )

            if not response:
                self.logger.warning(f"No gamelogs data received for {date}")
                return []

            gamelogs = []
            gamelog_list = response.get("gamelogs", [])

            for gamelog in gamelog_list:
                try:
                    player = gamelog.get("player", {})
                    game = gamelog.get("game", {})
                    stats = gamelog.get("stats", {})

                    # Extract player info
                    first_name = player.get("firstName", "")
                    last_name = player.get("lastName", "")
                    position = player.get("position", "")
                    team_data = player.get("team", {})
                    team = team_data.get("abbr", "")

                    if not first_name or not last_name or not team:
                        self.logger.debug("Skipping gamelog entry with missing player data")
                        continue

                    # Extract game date
                    game_date = game.get("date", date)

                    # Extract stats (use None for missing values)
                    snaps = stats.get("offensiveSnapsPlayed")
                    snap_percentage = stats.get("snapCountPercentage")
                    targets = stats.get("receivingTargets")
                    receptions = stats.get("receivingReceptions")
                    passing_yards = stats.get("passingYards")
                    rushing_yards = stats.get("rushingYards")
                    receiving_yards = stats.get("receivingYards")
                    receiving_td = stats.get("receivingTouchdowns")
                    rushing_td = stats.get("rushingTouchdowns")
                    passing_td = stats.get("passingTouchdowns")

                    gamelogs.append({
                        "player_first_name": first_name,
                        "player_last_name": last_name,
                        "position": position,
                        "team": team.upper(),
                        "game_date": game_date,
                        "snaps": snaps,
                        "snap_percentage": snap_percentage,
                        "targets": targets,
                        "receptions": receptions,
                        "passing_yards": passing_yards,
                        "rushing_yards": rushing_yards,
                        "receiving_yards": receiving_yards,
                        "receiving_td": receiving_td,
                        "rushing_td": rushing_td,
                        "passing_td": passing_td,
                    })

                except Exception as e:
                    self.logger.debug(f"Error parsing gamelog entry: {str(e)}")
                    continue

            self.logger.info(
                f"Fetched {len(gamelogs)} player gamelogs for {date}. "
                f"Players with snap counts: "
                f"{sum(1 for g in gamelogs if g['snaps'])}"
            )

            return gamelogs

        except Exception as e:
            self.logger.error(f"Error in fetch_player_gamelogs: {str(e)}")
            return []

    def _get_current_week_info(self) -> Optional[Dict[str, Any]]:
        """
        Query database for current NFL season and week.

        Returns:
            Dictionary with 'season' and 'week' keys, or None if not found
        """
        try:
            from sqlalchemy import text

            result = self.db.execute(text("""
                SELECT season, week_number
                FROM week_metadata
                WHERE status = 'current'
                LIMIT 1
            """))

            row = result.first()
            if row:
                return {
                    "season": row[0],
                    "week": row[1],
                }

            # Fallback: get most recent week
            result = self.db.execute(text("""
                SELECT season, week_number
                FROM week_metadata
                ORDER BY week_id DESC
                LIMIT 1
            """))

            row = result.first()
            if row:
                return {
                    "season": row[0],
                    "week": row[1],
                }

            self.logger.warning("Could not determine current season/week from database")
            return None

        except Exception as e:
            self.logger.warning(f"Error querying current week info: {str(e)}")
            return None

    async def close(self):
        """Close the HTTP client connection."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
