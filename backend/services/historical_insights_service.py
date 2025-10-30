"""
HistoricalInsightsService for analyzing historical performance data.

Provides insights for lineup generation:
- Consistency metrics (CV, floor, ceiling)
- Opponent matchup history
- Salary efficiency trends
- Usage pattern warnings
- Stack correlation analysis
"""

import logging
from typing import Optional, Dict, List, Tuple, Any
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class HistoricalInsightsService:
    """Service for calculating historical performance insights."""

    def __init__(self, session: Session):
        """
        Initialize HistoricalInsightsService.

        Args:
            session: SQLAlchemy Session for database operations
        """
        self.session = session

    def get_player_consistency(
        self, player_key: str, season: int, weeks_back: int = 6
    ) -> Dict[str, float]:
        """
        Calculate consistency metrics for a player.

        Args:
            player_key: Player identifier
            season: Season year
            weeks_back: Number of recent weeks to analyze

        Returns:
            Dictionary with:
            - consistency_score: Coefficient of variation (stddev/mean)
            - floor: Minimum points over period
            - ceiling: Maximum points over period
            - avg_points: Average points
            - games_count: Number of games analyzed
        """
        try:
            query = text("""
                SELECT
                    actual_points,
                    week
                FROM historical_stats
                WHERE player_key = :player_key
                  AND season = :season
                  AND snaps >= 20
                  AND actual_points IS NOT NULL
                ORDER BY week DESC
                LIMIT :weeks_back
            """)

            rows = self.session.execute(
                query,
                {
                    "player_key": player_key,
                    "season": season,
                    "weeks_back": weeks_back,
                },
            ).fetchall()

            if not rows or len(rows) < 2:
                return {
                    "consistency_score": None,
                    "floor": None,
                    "ceiling": None,
                    "avg_points": None,
                    "games_count": len(rows),
                }

            points = [float(row[0]) for row in rows if row[0] is not None]

            if not points:
                return {
                    "consistency_score": None,
                    "floor": None,
                    "ceiling": None,
                    "avg_points": None,
                    "games_count": len(rows),
                }

            import statistics

            avg_points = statistics.mean(points)
            stddev = statistics.stdev(points) if len(points) > 1 else 0.0

            # Coefficient of variation (lower is more consistent)
            consistency_score = stddev / avg_points if avg_points > 0 else None

            return {
                "consistency_score": consistency_score,
                "floor": min(points),
                "ceiling": max(points),
                "avg_points": avg_points,
                "games_count": len(points),
            }

        except Exception as e:
            logger.warning(f"Error calculating consistency for {player_key}: {e}")
            self.session.rollback()
            return {
                "consistency_score": None,
                "floor": None,
                "ceiling": None,
                "avg_points": None,
                "games_count": 0,
            }

    def get_opponent_matchup_history(
        self, player_key: str, opponent: str, season: int
    ) -> Dict[str, float]:
        """
        Get historical performance vs specific opponent.

        Args:
            player_key: Player identifier
            opponent: Opponent team abbreviation
            season: Season year

        Returns:
            Dictionary with:
            - avg_points: Average points vs this opponent
            - games_count: Number of games vs opponent
            - best_game: Best game points
            - worst_game: Worst game points
        """
        try:
            query = text("""
                SELECT
                    actual_points,
                    week
                FROM historical_stats
                WHERE player_key = :player_key
                  AND season = :season
                  AND opponent = :opponent
                  AND snaps >= 20
                  AND actual_points IS NOT NULL
                ORDER BY week DESC
            """)

            rows = self.session.execute(
                query,
                {
                    "player_key": player_key,
                    "season": season,
                    "opponent": opponent.upper(),
                },
            ).fetchall()

            if not rows:
                return {
                    "avg_points": None,
                    "games_count": 0,
                    "best_game": None,
                    "worst_game": None,
                }

            points = [float(row[0]) for row in rows if row[0] is not None]

            if not points:
                return {
                    "avg_points": None,
                    "games_count": len(rows),
                    "best_game": None,
                    "worst_game": None,
                }

            import statistics

            return {
                "avg_points": statistics.mean(points),
                "games_count": len(points),
                "best_game": max(points),
                "worst_game": min(points),
            }

        except Exception as e:
            logger.warning(
                f"Error getting matchup history for {player_key} vs {opponent}: {e}"
            )
            self.session.rollback()
            return {
                "avg_points": None,
                "games_count": 0,
                "best_game": None,
                "worst_game": None,
            }

    def get_salary_efficiency_trend(
        self, player_key: str, season: int, weeks_back: int = 6
    ) -> Dict[str, float]:
        """
        Calculate salary efficiency trend over recent weeks.

        Args:
            player_key: Player identifier
            season: Season year
            weeks_back: Number of recent weeks to analyze

        Returns:
            Dictionary with:
            - avg_value_score: Average value score (points / salary * 1000)
            - trend: 'up', 'down', or 'stable' based on recent trend
            - recent_avg: Average value score over last 3 weeks
            - earlier_avg: Average value score over weeks 4-6
        """
        try:
            query = text("""
                SELECT
                    actual_points,
                    salary,
                    week
                FROM historical_stats
                WHERE player_key = :player_key
                  AND season = :season
                  AND snaps >= 20
                  AND actual_points IS NOT NULL
                  AND salary IS NOT NULL
                  AND salary > 0
                ORDER BY week DESC
                LIMIT :weeks_back
            """)

            rows = self.session.execute(
                query,
                {
                    "player_key": player_key,
                    "season": season,
                    "weeks_back": weeks_back,
                },
            ).fetchall()

            if not rows or len(rows) < 2:
                return {
                    "avg_value_score": None,
                    "trend": None,
                    "recent_avg": None,
                    "earlier_avg": None,
                }

            # Calculate value scores: (points / salary) * 1000
            value_scores = []
            for row in rows:
                if row[0] is not None and row[1] is not None and row[1] > 0:
                    value_score = (float(row[0]) / float(row[1])) * 1000
                    value_scores.append((value_score, row[2]))  # (value, week)

            if not value_scores:
                return {
                    "avg_value_score": None,
                    "trend": None,
                    "recent_avg": None,
                    "earlier_avg": None,
                }

            import statistics

            all_values = [v[0] for v in value_scores]
            avg_value_score = statistics.mean(all_values)

            # Determine trend: compare last 3 weeks vs previous 3 weeks
            if len(value_scores) >= 6:
                recent = [v[0] for v in value_scores[:3]]
                earlier = [v[0] for v in value_scores[3:6]]
                recent_avg = statistics.mean(recent)
                earlier_avg = statistics.mean(earlier)

                if recent_avg > earlier_avg * 1.1:
                    trend = "up"
                elif recent_avg < earlier_avg * 0.9:
                    trend = "down"
                else:
                    trend = "stable"
            elif len(value_scores) >= 3:
                recent = [v[0] for v in value_scores[:3]]
                recent_avg = statistics.mean(recent)
                earlier_avg = None
                trend = "stable"  # Not enough data for trend
            else:
                recent_avg = None
                earlier_avg = None
                trend = None

            return {
                "avg_value_score": avg_value_score,
                "trend": trend,
                "recent_avg": recent_avg,
                "earlier_avg": earlier_avg,
            }

        except Exception as e:
            logger.warning(f"Error calculating salary efficiency for {player_key}: {e}")
            self.session.rollback()
            return {
                "avg_value_score": None,
                "trend": None,
                "recent_avg": None,
                "earlier_avg": None,
            }

    def get_usage_pattern_warnings(
        self, player_key: str, season: int, current_week: int
    ) -> Dict[str, any]:
        """
        Detect usage pattern warnings (declining snaps/touches).

        Args:
            player_key: Player identifier
            season: Season year
            current_week: Current week number

        Returns:
            Dictionary with:
            - has_warning: Boolean indicating if warning exists
            - warnings: List of warning strings
            - snap_trend: 'declining', 'stable', or 'increasing'
            - touch_trend: 'declining', 'stable', or 'increasing'
            - recent_snaps_avg: Average snaps over last 2 weeks
            - earlier_snaps_avg: Average snaps over weeks 3-4
        """
        try:
            query = text("""
                SELECT
                    snaps,
                    touches,
                    week
                FROM historical_stats
                WHERE player_key = :player_key
                  AND season = :season
                  AND week < :current_week
                  AND snaps IS NOT NULL
                ORDER BY week DESC
                LIMIT 4
            """)

            rows = self.session.execute(
                query,
                {
                    "player_key": player_key,
                    "season": season,
                    "current_week": current_week,
                },
            ).fetchall()

            if not rows or len(rows) < 2:
                return {
                    "has_warning": False,
                    "warnings": [],
                    "snap_trend": None,
                    "touch_trend": None,
                    "recent_snaps_avg": None,
                    "earlier_snaps_avg": None,
                }

            warnings = []

            # Analyze snap trend
            snaps_data = [(row[0], row[2]) for row in rows if row[0] is not None]
            if len(snaps_data) >= 4:
                recent_snaps = [s[0] for s in snaps_data[:2]]
                earlier_snaps = [s[0] for s in snaps_data[2:4]]

                import statistics

                recent_snaps_avg = statistics.mean(recent_snaps)
                earlier_snaps_avg = statistics.mean(earlier_snaps)

                if recent_snaps_avg < earlier_snaps_avg * 0.85:  # 15% decline
                    snap_trend = "declining"
                    warnings.append(
                        f"Snap count declining ({recent_snaps_avg:.0f} vs {earlier_snaps_avg:.0f} avg)"
                    )
                elif recent_snaps_avg > earlier_snaps_avg * 1.15:
                    snap_trend = "increasing"
                else:
                    snap_trend = "stable"
            elif len(snaps_data) >= 2:
                snap_trend = "stable"
                recent_snaps_avg = statistics.mean([s[0] for s in snaps_data[:2]])
                earlier_snaps_avg = None
            else:
                snap_trend = None
                recent_snaps_avg = None
                earlier_snaps_avg = None

            # Analyze touch trend (for RB/WR/TE)
            touches_data = [(row[1], row[2]) for row in rows if row[1] is not None]
            if len(touches_data) >= 4:
                recent_touches = [t[0] for t in touches_data[:2]]
                earlier_touches = [t[0] for t in touches_data[2:4]]

                import statistics

                recent_touches_avg = statistics.mean(recent_touches)
                earlier_touches_avg = statistics.mean(earlier_touches)

                if recent_touches_avg < earlier_touches_avg * 0.85:  # 15% decline
                    touch_trend = "declining"
                    warnings.append(
                        f"Touches declining ({recent_touches_avg:.1f} vs {earlier_touches_avg:.1f} avg)"
                    )
                elif recent_touches_avg > earlier_touches_avg * 1.15:
                    touch_trend = "increasing"
                else:
                    touch_trend = "stable"
            elif len(touches_data) >= 2:
                touch_trend = "stable"
            else:
                touch_trend = None

            return {
                "has_warning": len(warnings) > 0,
                "warnings": warnings,
                "snap_trend": snap_trend,
                "touch_trend": touch_trend,
                "recent_snaps_avg": recent_snaps_avg,
                "earlier_snaps_avg": earlier_snaps_avg,
            }

        except Exception as e:
            logger.warning(f"Error analyzing usage patterns for {player_key}: {e}")
            self.session.rollback()
            return {
                "has_warning": False,
                "warnings": [],
                "snap_trend": None,
                "touch_trend": None,
                "recent_snaps_avg": None,
                "earlier_snaps_avg": None,
            }

    def get_stack_correlation(
        self, qb_player_key: str, wr_player_key: str, team: str, season: int
    ) -> Dict[str, float]:
        """
        Calculate correlation between QB and WR from same team.

        Args:
            qb_player_key: QB player identifier
            wr_player_key: WR player identifier
            team: Team abbreviation (for validation)
            season: Season year

        Returns:
            Dictionary with:
            - correlation: Pearson correlation coefficient (-1 to 1)
            - games_count: Number of games analyzed
            - avg_qb_points: Average QB points
            - avg_wr_points: Average WR points
        """
        try:
            query = text("""
                SELECT
                    qb.week,
                    qb.actual_points as qb_points,
                    wr.actual_points as wr_points
                FROM historical_stats qb
                INNER JOIN historical_stats wr
                    ON qb.week = wr.week
                    AND qb.season = wr.season
                    AND qb.team = wr.team
                WHERE qb.player_key = :qb_key
                  AND wr.player_key = :wr_key
                  AND qb.season = :season
                  AND qb.team = :team
                  AND qb.snaps >= 20
                  AND wr.snaps >= 20
                  AND qb.actual_points IS NOT NULL
                  AND wr.actual_points IS NOT NULL
                ORDER BY qb.week DESC
            """)

            rows = self.session.execute(
                query,
                {
                    "qb_key": qb_player_key,
                    "wr_key": wr_player_key,
                    "season": season,
                    "team": team.upper(),
                },
            ).fetchall()

            if not rows or len(rows) < 3:
                return {
                    "correlation": None,
                    "games_count": len(rows),
                    "avg_qb_points": None,
                    "avg_wr_points": None,
                }

            qb_points = [float(row[1]) for row in rows]
            wr_points = [float(row[2]) for row in rows]

            import statistics

            # Calculate Pearson correlation
            if len(qb_points) < 3:
                correlation = None
            else:
                try:
                    # Manual Pearson correlation calculation
                    qb_mean = statistics.mean(qb_points)
                    wr_mean = statistics.mean(wr_points)
                    
                    numerator = sum((qb_points[i] - qb_mean) * (wr_points[i] - wr_mean) for i in range(len(qb_points)))
                    qb_var = sum((x - qb_mean) ** 2 for x in qb_points)
                    wr_var = sum((x - wr_mean) ** 2 for x in wr_points)
                    
                    if qb_var > 0 and wr_var > 0:
                        correlation = numerator / ((qb_var * wr_var) ** 0.5)
                    else:
                        correlation = None
                except Exception:
                    correlation = None

    def get_top_stack_partners(
        self, player_key: str, position: str, team: str, season: int, week_id: int, limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get top stack correlation partners for a player.
        
        For QBs: Returns top WRs/TEs from same team with highest correlation
        For WRs/TEs: Returns QB from same team with correlation
        
        Args:
            player_key: Player identifier
            position: Player position (QB, WR, TE)
            team: Team abbreviation
            season: Season year
            week_id: Current week ID (to get partner names from player_pools)
            limit: Maximum number of partners to return
            
        Returns:
            List of dictionaries with:
            - partner_key: Partner player key
            - partner_name: Partner player name (from current week's player pool)
            - partner_position: Partner position
            - correlation: Correlation coefficient
            - games_count: Number of games analyzed
        """
        try:
            if position == "QB":
                # For QBs: Find WRs/TEs on same team with highest correlation
                query = text("""
                    SELECT DISTINCT
                        wr.player_key as partner_key,
                        COUNT(*) as games_overlap
                    FROM historical_stats qb
                    INNER JOIN historical_stats wr
                        ON qb.week = wr.week
                        AND qb.season = wr.season
                        AND qb.team = wr.team
                    WHERE qb.player_key = :player_key
                      AND wr.player_key != :player_key
                      AND qb.season = :season
                      AND qb.team = :team
                      AND wr.position IN ('WR', 'TE')
                      AND qb.snaps >= 20
                      AND wr.snaps >= 20
                      AND qb.actual_points IS NOT NULL
                      AND wr.actual_points IS NOT NULL
                    GROUP BY wr.player_key
                    HAVING COUNT(*) >= 3
                    ORDER BY games_overlap DESC
                    LIMIT :limit
                """)
                
                rows = self.session.execute(
                    query,
                    {
                        "player_key": player_key,
                        "season": season,
                        "team": team.upper(),
                        "limit": limit,
                    },
                ).fetchall()
                
                partners = []
                for row in rows:
                    partner_key = row[0]
                    games_count = row[1]
                    
                    # Get correlation for this pair
                    correlation_data = self.get_stack_correlation(
                        player_key, partner_key, team, season
                    )
                    
                    if correlation_data.get("correlation") is not None:
                        # Get partner name from current week's player pool
                        partner_name_query = text("""
                            SELECT name, position
                            FROM player_pools
                            WHERE player_key = :partner_key AND week_id = :week_id
                            LIMIT 1
                        """)
                        partner_info = self.session.execute(
                            partner_name_query,
                            {"partner_key": partner_key, "week_id": week_id}
                        ).fetchone()
                        
                        partner_name = partner_info[0] if partner_info else partner_key
                        partner_pos = partner_info[1] if partner_info else "WR"
                        
                        partners.append({
                            "partner_key": partner_key,
                            "partner_name": partner_name,
                            "partner_position": partner_pos,
                            "correlation": correlation_data["correlation"],
                            "games_count": correlation_data["games_count"],
                        })
                
                # Sort by correlation descending
                partners.sort(key=lambda x: x["correlation"] if x["correlation"] is not None else -1, reverse=True)
                return partners[:limit]
                
            elif position in ("WR", "TE"):
                # For WRs/TEs: Find QB on same team
                query = text("""
                    SELECT DISTINCT
                        qb.player_key as partner_key,
                        COUNT(*) as games_overlap
                    FROM historical_stats wr
                    INNER JOIN historical_stats qb
                        ON wr.week = qb.week
                        AND wr.season = qb.season
                        AND wr.team = qb.team
                    WHERE wr.player_key = :player_key
                      AND qb.player_key != :player_key
                      AND wr.season = :season
                      AND wr.team = :team
                      AND qb.position = 'QB'
                      AND wr.snaps >= 20
                      AND qb.snaps >= 20
                      AND wr.actual_points IS NOT NULL
                      AND qb.actual_points IS NOT NULL
                    GROUP BY qb.player_key
                    HAVING COUNT(*) >= 3
                    ORDER BY games_overlap DESC
                    LIMIT 1
                """)
                
                rows = self.session.execute(
                    query,
                    {
                        "player_key": player_key,
                        "season": season,
                        "team": team.upper(),
                        "limit": 1,
                    },
                ).fetchall()
                
                if not rows:
                    return []
                
                partner_key = rows[0][0]
                games_count = rows[0][1]
                
                # Get correlation for this pair (swapped for WR-QB)
                correlation_data = self.get_stack_correlation(
                    partner_key, player_key, team, season
                )
                
                if correlation_data.get("correlation") is not None:
                    # Get partner name from current week's player pool
                    partner_name_query = text("""
                        SELECT name
                        FROM player_pools
                        WHERE player_key = :partner_key AND week_id = :week_id
                        LIMIT 1
                    """)
                    partner_info = self.session.execute(
                        partner_name_query,
                        {"partner_key": partner_key, "week_id": week_id}
                    ).fetchone()
                    
                    partner_name = partner_info[0] if partner_info else partner_key
                    
                    return [{
                        "partner_key": partner_key,
                        "partner_name": partner_name,
                        "partner_position": "QB",
                        "correlation": correlation_data["correlation"],
                        "games_count": correlation_data["games_count"],
                    }]
                
                return []
                
            else:
                # RB, DST don't have stack partners
                return []
                
        except Exception as e:
            logger.warning(f"Error getting stack partners for {player_key}: {e}")
            self.session.rollback()
            return []

