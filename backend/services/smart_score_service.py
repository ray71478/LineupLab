"""
SmartScoreService for calculating Smart Scores using 8-factor formula.

Provides methods for:
- Calculating Smart Score for individual players
- Calculating Smart Scores for all players in a week
- Handling missing data with intelligent defaults
- Position-specific trend calculations
- Vegas context calculations
- Regression risk detection
- Real injury data integration from MySportsFeeds
- Real Vegas ITT data integration
- Real defensive ranking data integration

Smart Score Formula:
  Smart Score = (projection × W1) +
                ((ceiling - floor) × W2) +
                (-(ownership × W3)) +
                (((projection × 100000) / salary) × W4) +
                (trend_percentage × W5) +
                (-(regression_penalty × W6)) +  // 0 in MVP
                (((team_itt / league_avg_itt) × W7)) +
                (matchup_category_value × W8)
"""

import logging
import json
import hashlib
from typing import Optional, Dict, Tuple, List, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.schemas.smart_score_schemas import (
    WeightProfile,
    ScoreConfig,
    ScoreBreakdown,
    PlayerScoreResponse,
)
from backend.services.historical_insights_service import HistoricalInsightsService

logger = logging.getLogger(__name__)


@dataclass
class PlayerData:
    """Data structure for player information used in calculations."""
    player_id: int
    player_key: str
    name: str
    team: str
    position: str
    salary: int
    projection: Optional[float]
    ownership: Optional[float]
    ceiling: Optional[float]
    floor: Optional[float]
    projection_source: Optional[str]
    opponent_rank_category: Optional[str]
    injury_status: Optional[str] = None  # NEW: PROBABLE, QUESTIONABLE, DOUBTFUL, OUT


@dataclass
class FactorResult:
    """Result of a single factor calculation."""
    value: float
    used_default: bool = False
    breakdown_info: Optional[str] = None


class SmartScoreService:
    """Service for calculating Smart Scores using 8-factor formula."""

    # Position-based default ranges for ceiling/floor estimation
    POSITION_DEFAULT_RANGES = {
        "WR": 5.0,  # ±5 points
        "RB": 4.0,  # ±4 points
        "QB": 6.0,  # ±6 points
        "TE": 4.0,  # ±4 points
        "DST": 3.0,  # ±3 points
    }

    # Default league average ITT
    DEFAULT_LEAGUE_AVG_ITT = 22.5

    # Injury status values for filtering (unavailable players)
    UNAVAILABLE_INJURY_STATUSES = {"OUT", "DOUBTFUL"}

    def __init__(self, session: Session):
        """
        Initialize SmartScoreService.

        Args:
            session: SQLAlchemy Session for database operations
        """
        self.session = session
        self._defaults_cache: Dict[int, Dict[str, float]] = {}
        # Cache for calculation results: (cache_key, (results, timestamp))
        self._calculation_cache: Dict[str, Tuple[List[PlayerScoreResponse], datetime]] = {}
        self._cache_ttl = timedelta(minutes=5)  # 5 minute TTL
        self._insights_service = HistoricalInsightsService(session)

    def is_player_available(self, injury_status: Optional[str]) -> bool:
        """
        Check if player is available based on injury status.

        Filters out OUT and DOUBTFUL players. PROBABLE and QUESTIONABLE are playable.

        Args:
            injury_status: Injury status from player_pools.injury_status

        Returns:
            True if player is available (not OUT/DOUBTFUL), False otherwise
        """
        if injury_status is None:
            return True  # No injury data means available

        return injury_status not in self.UNAVAILABLE_INJURY_STATUSES

    def calculate_smart_score(
        self,
        player: PlayerData,
        week_id: int,
        weights: WeightProfile,
        config: ScoreConfig,
    ) -> Tuple[float, ScoreBreakdown, int, bool]:
        """
        Calculate Smart Score for a single player.

        Args:
            player: Player data for calculation
            week_id: Week ID for context
            weights: Weight profile (W1-W8)
            config: Calculation configuration

        Returns:
            Tuple of (smart_score, score_breakdown, games_with_20_plus_snaps, regression_risk)
        """
        # Get defaults for missing data (cache per week)
        defaults = self._get_missing_data_defaults(week_id)

        # Calculate each factor
        w1_result = self._calculate_w1_projection(player, weights.W1)
        w2_result = self._calculate_w2_ceiling_factor(
            player, weights.W2, week_id, defaults
        )
        w3_result = self._calculate_w3_ownership_penalty(
            player, weights.W3, defaults
        )
        w4_result = self._calculate_w4_value_score(player, weights.W4)
        w5_result, games_with_20_plus_snaps = self._calculate_w5_trend_adjustment(
            player, week_id, weights.W5
        )
        # W6: Regression Penalty - Only applies to WRs who had big weeks
        regression_risk, has_regression_data = self._calculate_w6_regression_risk(
            player, week_id, config
        )
        w6_result = self._calculate_w6_regression_penalty(
            player, regression_risk, weights.W6
        )
        w7_result = self._calculate_w7_vegas_context(
            player, week_id, weights.W7, defaults
        )
        w8_result = self._calculate_w8_matchup_adjustment(
            player, week_id, weights.W8
        )

        # Calculate final Smart Score
        smart_score = (
            w1_result.value +
            w2_result.value +
            w3_result.value +  # Already negative
            w4_result.value +
            w5_result.value +
            w6_result.value +  # Already negative, 0 in MVP
            w7_result.value +
            w8_result.value
        )

        # Build breakdown
        breakdown = ScoreBreakdown(
            W1_value=w1_result.value,
            W2_value=w2_result.value,
            W3_value=w3_result.value,
            W4_value=w4_result.value,
            W5_value=w5_result.value,
            W6_value=w6_result.value,
            W7_value=w7_result.value,
            W8_value=w8_result.value,
            smart_score=smart_score,
            missing_data_indicators={
                "W1": w1_result.used_default,
                "W2": w2_result.used_default,
                "W3": w3_result.used_default,
                "W4": w4_result.used_default,
                "W5": w5_result.used_default,
                "W6": w6_result.used_default,
                "W7": w7_result.used_default,
                "W8": w8_result.used_default,
            },
        )

        return smart_score, breakdown, games_with_20_plus_snaps, regression_risk

    def _calculate_w1_projection(
        self, player: PlayerData, weight: float
    ) -> FactorResult:
        """
        Calculate W1: Projection Factor.

        Formula: projection × W1

        Args:
            player: Player data
            weight: W1 weight

        Returns:
            FactorResult with calculated value
        """
        if player.projection is None or player.projection <= 0:
            return FactorResult(value=0.0, used_default=True)

        value = player.projection * weight
        return FactorResult(value=value, used_default=False)

    def _calculate_w2_ceiling_factor(
        self,
        player: PlayerData,
        weight: float,
        week_id: int,
        defaults: Dict[str, float],
    ) -> FactorResult:
        """
        Calculate W2: Ceiling Factor - Differential boost for high-ceiling players.

        Players with higher ceilings (higher upside) get proportionally larger boosts.
        This is differential: a player with ceiling 30 vs floor 15 gets MORE boost
        than a player with ceiling 25 vs floor 20 when weight is increased.

        Formula when ceiling/floor available:
        ceiling_range = (ceiling - floor) × weight
        Higher ceiling_range = larger additive boost to smart score

        If missing: Estimate based on position defaults

        Args:
            player: Player data
            weight: W2 weight
            week_id: Week ID for context
            defaults: Default values cache

        Returns:
            FactorResult with calculated value
        """
        if player.ceiling is not None and player.floor is not None:
            # Differential: higher ceiling gets more benefit
            ceiling_range = player.ceiling - player.floor
            value = ceiling_range * weight
            return FactorResult(value=value, used_default=False)

        # Estimate based on position defaults
        if player.projection is not None and player.projection > 0:
            default_range = self.POSITION_DEFAULT_RANGES.get(
                player.position, 5.0
            )
            estimated_range = default_range * 2  # Total range (ceiling - floor)
            value = estimated_range * weight
            return FactorResult(
                value=value,
                used_default=True,
                breakdown_info=f"Estimated using position default range: ±{default_range}",
            )

        # No projection available
        return FactorResult(value=0.0, used_default=True)

    def _calculate_w3_ownership_penalty(
        self,
        player: PlayerData,
        weight: float,
        defaults: Dict[str, float],
    ) -> FactorResult:
        """
        Calculate W3: Ownership Penalty.

        Formula: -(ownership × W3)
        Missing ownership: Use league average

        Args:
            player: Player data
            weight: W3 weight
            defaults: Default values cache

        Returns:
            FactorResult with calculated value (already negative)
        """
        ownership = player.ownership
        if ownership is None:
            ownership = defaults.get("league_avg_ownership", 0.0)

        # Penalty is negative (subtracted from score)
        value = -(ownership * weight)
        used_default = player.ownership is None

        return FactorResult(value=value, used_default=used_default)

    def _calculate_w4_value_score(
        self, player: PlayerData, weight: float
    ) -> FactorResult:
        """
        Calculate W4: Value Score.

        Formula: ((projection × 100000) / salary) × W4

        Args:
            player: Player data
            weight: W4 weight

        Returns:
            FactorResult with calculated value
        """
        if player.projection is None or player.projection <= 0:
            return FactorResult(value=0.0, used_default=True)

        if player.salary <= 0:
            return FactorResult(value=0.0, used_default=True)

        # Value score: (projection × 100000) / salary
        value_score = (player.projection * 100000) / player.salary
        value = value_score * weight

        return FactorResult(value=value, used_default=False)

    def _calculate_w5_trend_adjustment(
        self, player: PlayerData, week_id: int, weight: float
    ) -> Tuple[FactorResult, int]:
        """
        Calculate W5: Trend Adjustment (position-specific).

        Uses real historical game data from MySportsFeeds API backfill.

        Formula: trend_percentage × W5
        Position-specific metrics:
        - WR/TE: target_share trend
        - RB: snap_pct trend
        - QB: pass_attempts trend (or derive from pass_yards)
        - DST: Skip (return 0)

        Args:
            player: Player data
            week_id: Week ID for context
            weight: W5 weight

        Returns:
            Tuple of (FactorResult with calculated value, games_with_20_plus_snaps count)
        """
        # DST doesn't have trend calculation
        if player.position == "DST":
            return FactorResult(value=0.0, used_default=False), 0

        # Get current week info to determine season
        try:
            week_info = self.session.execute(
                text("SELECT season FROM weeks WHERE id = :week_id"),
                {"week_id": week_id},
            ).fetchone()
        except Exception as e:
            logger.warning(f"Error querying weeks table: {e}")
            self.session.rollback()
            return FactorResult(value=0.0, used_default=True), 0

        if not week_info:
            return FactorResult(value=0.0, used_default=True), 0

        season = week_info.season

        # Query historical stats for last 2-4 games with snaps >= 20
        # Note: Using week number from historical_stats, not week_id
        # We need to get the current week number first
        try:
            current_week_info = self.session.execute(
                text("SELECT week_number FROM weeks WHERE id = :week_id"),
                {"week_id": week_id},
            ).fetchone()
        except Exception as e:
            logger.warning(f"Error querying weeks table for week_number: {e}")
            self.session.rollback()
            return FactorResult(value=0.0, used_default=True), 0

        if not current_week_info:
            return FactorResult(value=0.0, used_default=True), 0

        current_week = current_week_info.week_number

        # Query historical stats for games with 20+ snaps
        # Get up to 4 games, ordered by week descending
        hist_query = text("""
            SELECT
                week,
                target_share,
                snap_pct,
                targets,
                rush_attempts,
                receptions,
                rec_yards
            FROM historical_stats
            WHERE player_key = :player_key
              AND season = :season
              AND week < :current_week
              AND snaps >= 20
              AND snaps IS NOT NULL
            ORDER BY week DESC
            LIMIT 4
        """)

        rows = self.session.execute(
            hist_query,
            {
                "player_key": player.player_key,
                "season": season,
                "current_week": current_week,
            },
        ).fetchall()

        games_count = len(rows)

        # Need minimum 2 games for trend calculation
        if games_count < 2:
            return FactorResult(value=0.0, used_default=True), games_count

        # Calculate trend based on position
        if player.position in ("WR", "TE"):
            # Use target_share trend
            trend_percentage = self._calculate_trend_percentage(
                rows, "target_share"
            )
        elif player.position == "RB":
            # Use snap_pct trend
            trend_percentage = self._calculate_trend_percentage(
                rows, "snap_pct"
            )
        elif player.position == "QB":
            # Use targets as proxy for pass attempts trend
            # If targets not available, try to derive from receptions/rec_yards
            trend_percentage = self._calculate_trend_percentage(
                rows, "targets"
            )
        else:
            trend_percentage = 0.0

        value = trend_percentage * weight
        return FactorResult(value=value, used_default=False), games_count

    def _calculate_trend_percentage(
        self, rows: List, metric_field: str
    ) -> float:
        """
        Calculate percentage change trend from historical data.

        Formula: (most_recent - oldest) / oldest

        Args:
            rows: List of historical stat rows (ordered DESC by week)
            metric_field: Field name to calculate trend for

        Returns:
            Trend percentage (e.g., 0.05 for 5% increase)
        """
        if len(rows) < 2:
            return 0.0

        # Get most recent and oldest values
        most_recent = getattr(rows[0], metric_field, None)
        oldest = getattr(rows[-1], metric_field, None)

        if most_recent is None or oldest is None:
            return 0.0

        if oldest == 0:
            # Avoid division by zero
            return 0.0

        trend_percentage = (most_recent - oldest) / oldest
        return trend_percentage

    def _calculate_w6_regression_risk(
        self,
        player: PlayerData,
        week_id: int,
        config: ScoreConfig,
    ) -> Tuple[bool, bool]:
        """
        Detect regression risk for WR players (80-20 rule).

        MVP: Visual flag only, no penalty calculation

        Args:
            player: Player data
            week_id: Week ID for context
            config: Calculation configuration (includes threshold)

        Returns:
            Tuple of (regression_risk: bool, has_data: bool)
        """
        # Only check WR players
        if player.position != "WR":
            return False, True

        if not config.eighty_twenty_enabled:
            return False, True

        # Get current week info to determine previous week
        try:
            week_info = self.session.execute(
                text("SELECT week_number, season FROM weeks WHERE id = :week_id"),
                {"week_id": week_id},
            ).fetchone()
        except Exception as e:
            logger.warning(f"Error querying weeks table for regression risk: {e}")
            self.session.rollback()
            return False, False

        if not week_info:
            return False, False

        current_week = week_info.week_number
        season = week_info.season

        # Calculate previous week
        previous_week = current_week - 1

        if previous_week < 1:
            # First week of season, no previous week data
            return False, False

        # Query historical_stats for previous week's actual_points
        try:
            result = self.session.execute(
                text("""
                    SELECT actual_points
                    FROM historical_stats
                    WHERE player_key = :player_key
                      AND week = :previous_week
                      AND season = :season
                """),
                {
                    "player_key": player.player_key,
                    "previous_week": previous_week,
                    "season": season,
                },
            ).fetchone()

            if result and result.actual_points is not None:
                actual_points = result.actual_points
                threshold = config.eighty_twenty_threshold
                regression_risk = actual_points >= threshold
                return regression_risk, True
            else:
                # No historical data available
                return False, False

        except Exception as e:
            logger.warning(f"Error checking regression risk for {player.player_key}: {e}")
            self.session.rollback()
            return False, False

    def _calculate_w6_regression_penalty(
        self,
        player: PlayerData,
        regression_risk: bool,
        weight: float,
    ) -> FactorResult:
        """
        Calculate W6: Regression Penalty for WR players only.

        Penalizes WRs who had big weeks (triggered 80-20 rule) because they're
        likely to regress toward their mean. Non-WR positions return 0 penalty.

        Formula for WRs with regression_risk=True:
        value = -weight (negative adjustment)

        For all other cases: value = 0

        Args:
            player: Player data
            regression_risk: Whether this player has regression risk (only set for WRs)
            weight: W6 weight

        Returns:
            FactorResult with calculated penalty (negative)
        """
        # Only apply regression penalty to WRs
        if player.position != "WR":
            return FactorResult(value=0.0, used_default=False)

        # Apply penalty only if regression risk detected
        if regression_risk:
            # Negative penalty (reduces smart score)
            value = -weight
            return FactorResult(
                value=value,
                used_default=False,
                breakdown_info="WR had big week, regression expected"
            )

        # No regression risk
        return FactorResult(value=0.0, used_default=False)

    def _calculate_w7_vegas_context(
        self,
        player: PlayerData,
        week_id: int,
        weight: float,
        defaults: Dict[str, float],
    ) -> FactorResult:
        """
        Calculate W7: Vegas Context based on Implied Team Total (ITT).

        Vegas implied team totals are the market's estimate of team scoring.
        Higher ITT = Vegas expects more points from the team = better opportunities.

        Formula: ((team_itt - league_avg_itt) / league_avg_itt) × weight

        This creates a differential boost where:
        - Teams with ITT > 22.5: Get positive boost proportional to how high
        - Teams with ITT = 22.5: Get 0 boost (neutral)
        - Teams with ITT < 22.5: Get negative adjustment (unfavorable matchup)

        Args:
            player: Player data
            week_id: Week ID for context
            weight: W7 weight
            defaults: Default values cache

        Returns:
            FactorResult with calculated value
        """
        league_avg_itt = defaults.get("league_avg_itt", self.DEFAULT_LEAGUE_AVG_ITT)

        try:
            # Get team's implied team total
            itt_result = self.session.execute(
                text("""
                    SELECT implied_team_total
                    FROM vegas_lines
                    WHERE week_id = :week_id
                      AND team = :team
                      AND implied_team_total IS NOT NULL
                    ORDER BY updated_at DESC
                    LIMIT 1
                """),
                {"week_id": week_id, "team": player.team},
            ).fetchone()

            team_itt = itt_result.implied_team_total if itt_result and itt_result.implied_team_total else league_avg_itt
            used_default = not itt_result or not itt_result.implied_team_total

        except Exception as e:
            logger.warning(f"Error querying Vegas data for {player.team}: {e}")
            self.session.rollback()
            team_itt = league_avg_itt
            used_default = True

        if league_avg_itt <= 0:
            # Avoid division by zero
            return FactorResult(value=0.0, used_default=True)

        # ITT Differential: (team_itt - avg) / avg
        # Positive when team_itt > avg (favorable)
        # Negative when team_itt < avg (unfavorable)
        itt_differential = (team_itt - league_avg_itt) / league_avg_itt

        # Apply weight to differential
        # This means different players benefit differently based on their team's ITT
        value = itt_differential * weight

        breakdown_info = f"ITT:{team_itt:.2f} vs Avg:{league_avg_itt:.2f}"

        return FactorResult(value=value, used_default=used_default, breakdown_info=breakdown_info)

    def _calculate_w8_matchup_adjustment(
        self, player: PlayerData, week_id: int, weight: float
    ) -> FactorResult:
        """
        Calculate W8: Matchup Adjustment - DISABLED

        This factor is currently disabled pending:
        - Access to reliable opponent defensive ranking data
        - Clearer methodology for matchup quality assessment

        W8 weight slider exists for future use but currently has no effect.

        Args:
            player: Player data
            week_id: Week ID for Vegas data lookup (unused currently)
            weight: W8 weight (unused currently)

        Returns:
            FactorResult with 0 value
        """
        # DISABLED: Returns 0 regardless of weight
        # The slider exists for future use when matchup data is properly configured
        return FactorResult(
            value=0.0,
            used_default=False,
            breakdown_info="Matchup Adjustment currently disabled"
        )

    def categorize_opponent_rank(self, opp_rank: Optional[int]) -> str:
        """
        Categorize opponent defensive rank into top_5, middle, bottom_5.

        Args:
            opp_rank: Opponent rank (1-32, where 1 is best defense)

        Returns:
            Category string: "top_5", "middle", or "bottom_5"
        """
        if opp_rank is None:
            return "middle"

        # Rank 1-5 = top_5 (best defenses)
        if opp_rank <= 5:
            return "top_5"
        # Rank 28-32 = bottom_5 (worst defenses)
        elif opp_rank >= 28:
            return "bottom_5"
        # Everything else is middle
        else:
            return "middle"

    def _get_missing_data_defaults(self, week_id: int) -> Dict[str, float]:
        """
        Get default values for missing data (cached per week).

        Args:
            week_id: Week ID for context

        Returns:
            Dictionary of default values
        """
        if week_id in self._defaults_cache:
            return self._defaults_cache[week_id]

        defaults = {}

        # Calculate league average ownership
        try:
            result = self.session.execute(
                text("""
                    SELECT AVG(ownership) as avg_ownership
                    FROM player_pools
                    WHERE week_id = :week_id AND ownership IS NOT NULL
                """),
                {"week_id": week_id},
            ).fetchone()

            defaults["league_avg_ownership"] = (
                result.avg_ownership if result and result.avg_ownership else 0.0
            )
        except Exception as e:
            logger.warning(f"Error calculating league avg ownership: {e}")
            # Rollback to clear the failed transaction state
            self.session.rollback()
            defaults["league_avg_ownership"] = 0.0

        # Calculate league average ITT from real API data
        try:
            result = self.session.execute(
                text("""
                    SELECT AVG(implied_team_total) as avg_itt
                    FROM vegas_lines
                    WHERE week_id = :week_id AND implied_team_total IS NOT NULL
                """),
                {"week_id": week_id},
            ).fetchone()

            defaults["league_avg_itt"] = (
                result.avg_itt if result and result.avg_itt else self.DEFAULT_LEAGUE_AVG_ITT
            )
        except Exception as e:
            logger.warning(f"Error calculating league avg ITT: {e}")
            # Rollback to clear the failed transaction state
            self.session.rollback()
            defaults["league_avg_itt"] = self.DEFAULT_LEAGUE_AVG_ITT

        # Cache defaults
        self._defaults_cache[week_id] = defaults
        return defaults

    def _generate_cache_key(
        self, week_id: int, weights: WeightProfile, config: ScoreConfig
    ) -> str:
        """
        Generate cache key for calculation results.

        Args:
            week_id: Week ID
            weights: Weight profile
            config: Score configuration

        Returns:
            Cache key string
        """
        # Create deterministic hash from inputs
        cache_data = {
            "week_id": week_id,
            "weights": weights.dict(),
            "config": config.dict(),
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()

    def calculate_for_all_players(
        self,
        week_id: int,
        weights: WeightProfile,
        config: ScoreConfig,
    ) -> List[PlayerScoreResponse]:
        """
        Calculate Smart Scores for all available players in a week.

        Filters out unavailable players (OUT, DOUBTFUL) based on real injury data.
        Uses caching to avoid redundant calculations for same week/weights/config.

        Args:
            week_id: Week ID to calculate scores for
            weights: Weight profile (W1-W8)
            config: Calculation configuration

        Returns:
            List of PlayerScoreResponse with calculated scores
        """
        # Check cache first
        cache_key = self._generate_cache_key(week_id, weights, config)
        if cache_key in self._calculation_cache:
            cached_results, timestamp = self._calculation_cache[cache_key]
            if datetime.now() - timestamp < self._cache_ttl:
                logger.debug(f"Cache HIT for week {week_id}")
                return cached_results
            else:
                # Cache expired, remove it
                del self._calculation_cache[cache_key]

        logger.debug(f"Cache MISS for week {week_id}, calculating...")

        # Fetch all players for the week including injury status
        players_query = text("""
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
                projection_source,
                opponent_rank_category,
                COALESCE(injury_status, NULL) as injury_status
            FROM player_pools
            WHERE week_id = :week_id
            ORDER BY position, name
        """)

        rows = self.session.execute(
            players_query, {"week_id": week_id}
        ).fetchall()

        # Get season and week_number for insights
        try:
            week_info = self.session.execute(
                text("SELECT season, week_number FROM weeks WHERE id = :week_id"),
                {"week_id": week_id},
            ).fetchone()
            season = week_info.season if week_info else None
            current_week_num = week_info.week_number if week_info else None
        except Exception as e:
            logger.warning(f"Error getting week info: {e}")
            self.session.rollback()
            season = None
            current_week_num = None

        results = []
        excluded_players: List[Tuple[str, str]] = []  # (name, reason)

        for row in rows:
            # Check injury status and filter unavailable players
            injury_status = row.injury_status
            if not self.is_player_available(injury_status):
                excluded_players.append((row.name, f"Unavailable ({injury_status})"))
                logger.debug(f"Excluding {row.name} ({row.team}) - {injury_status}")
                continue

            player_data = PlayerData(
                player_id=row.id,
                player_key=row.player_key,
                name=row.name,
                team=row.team,
                position=row.position,
                salary=row.salary,
                projection=row.projection,
                ownership=row.ownership,
                ceiling=row.ceiling,
                floor=row.floor,
                projection_source=row.projection_source,
                opponent_rank_category=row.opponent_rank_category,
                injury_status=row.injury_status,
            )

            smart_score, breakdown, games_count, regression_risk = self.calculate_smart_score(
                player_data, week_id, weights, config
            )

            # Calculate historical insights
            consistency_score = None
            opponent_matchup_avg = None
            salary_efficiency_trend = None
            usage_warnings = None
            stack_partners = None

            if season:
                # Consistency score
                consistency = self._insights_service.get_player_consistency(
                    player_data.player_key, season, weeks_back=6
                )
                consistency_score = consistency.get("consistency_score")

                # Salary efficiency trend
                efficiency = self._insights_service.get_salary_efficiency_trend(
                    player_data.player_key, season, weeks_back=6
                )
                salary_efficiency_trend = efficiency.get("trend")

                # Usage warnings
                if current_week_num:
                    usage = self._insights_service.get_usage_pattern_warnings(
                        player_data.player_key, season, current_week_num
                    )
                    usage_warnings = usage.get("warnings") if usage.get("has_warning") else None

                # Stack partners (metadata only - does NOT affect Smart Score)
                # Only for QB, WR, TE positions
                if player_data.position in ("QB", "WR", "TE"):
                    stack_partners = self._insights_service.get_top_stack_partners(
                        player_data.player_key,
                        player_data.position,
                        player_data.team,
                        season,
                        week_id,
                        limit=3
                    )
                    # Only include if we have at least one partner with correlation > 0.5
                    if stack_partners:
                        stack_partners = [
                            p for p in stack_partners
                            if p.get("correlation") is not None and p.get("correlation", 0) > 0.5
                        ]
                        if not stack_partners:
                            stack_partners = None

                # Opponent matchup history (optional - need to get opponent)
                # For now, skip if we don't have opponent info readily available
                # TODO: Enhance to lookup opponent from NFL schedule

                # Vegas context data
                implied_team_total = None
                over_under = None
                try:
                    vegas_result = self.session.execute(
                        text("""
                            SELECT implied_team_total, over_under
                            FROM vegas_lines
                            WHERE week_id = :week_id AND team = :team
                            LIMIT 1
                        """),
                        {"week_id": week_id, "team": player_data.team},
                    ).fetchone()

                    if vegas_result:
                        implied_team_total, over_under = vegas_result
                except Exception as e:
                    logger.debug(f"Could not fetch Vegas data for {player_data.name}: {e}")

            # Create response
            player_response = PlayerScoreResponse(
                player_id=player_data.player_id,
                player_key=player_data.player_key,
                name=player_data.name,
                team=player_data.team,
                position=player_data.position,
                salary=player_data.salary,
                projection=player_data.projection,
                ownership=player_data.ownership,
                smart_score=smart_score,
                projection_source=player_data.projection_source,
                opponent_rank_category=player_data.opponent_rank_category,
                games_with_20_plus_snaps=games_count,
                regression_risk=regression_risk,
                score_breakdown=breakdown,
                implied_team_total=implied_team_total,
                over_under=over_under,
                consistency_score=consistency_score,
                opponent_matchup_avg=opponent_matchup_avg,
                salary_efficiency_trend=salary_efficiency_trend,
                usage_warnings=usage_warnings,
                stack_partners=stack_partners,
            )

            results.append(player_response)

        # Log excluded players
        if excluded_players:
            logger.info(f"Excluded {len(excluded_players)} unavailable players from Smart Score calculations:")
            for name, reason in excluded_players[:10]:  # Log first 10
                logger.debug(f"  - {name}: {reason}")
            if len(excluded_players) > 10:
                logger.debug(f"  ... and {len(excluded_players) - 10} more")

        # Cache results
        self._calculation_cache[cache_key] = (results, datetime.now())

        # Clean up expired cache entries periodically
        if len(self._calculation_cache) > 100:  # Limit cache size
            self._cleanup_expired_cache()

        logger.info(f"Calculated Smart Scores for {len(results)} available players (excluded {len(excluded_players)})")
        return results

    def _cleanup_expired_cache(self):
        """Remove expired cache entries."""
        now = datetime.now()
        expired_keys = [
            key for key, (_, timestamp) in self._calculation_cache.items()
            if now - timestamp >= self._cache_ttl
        ]
        for key in expired_keys:
            del self._calculation_cache[key]
        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

    def invalidate_cache(self, week_id: Optional[int] = None):
        """
        Invalidate calculation cache.

        Args:
            week_id: If provided, invalidate only for this week. Otherwise, clear all cache.
        """
        if week_id is None:
            self._calculation_cache.clear()
            logger.info("Cleared all calculation cache")
        else:
            # Remove all cache entries for this week
            # Simple approach: clear all cache (can be optimized later)
            self._calculation_cache.clear()
            logger.info(f"Cleared calculation cache for week {week_id}")
