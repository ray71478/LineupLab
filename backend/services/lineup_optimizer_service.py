"""
Lineup Optimizer Service for generating optimal DraftKings lineups.

Uses PuLP linear programming to solve constrained optimization problem:
- Maximize Smart Score across lineups
- Enforce DraftKings constraints (positions, salary cap)
- Apply user settings (strategy mode, exposure limits, stacking rules)
- Generate diverse lineups (portfolio optimization with elite appearance constraints)
"""

import logging
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict

import pulp
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.schemas.smart_score_schemas import PlayerScoreResponse
from backend.schemas.lineup_schemas import (
    OptimizationSettings,
    GeneratedLineup,
)

logger = logging.getLogger(__name__)

# DraftKings constraints
SALARY_CAP = 50000
MIN_SALARY = SALARY_CAP - 1000  # $49,000 minimum
POSITION_REQUIREMENTS = {
    'QB': 1,
    'RB': 2,
    'WR': 3,
    'TE': 1,
    'FLEX': 1,  # RB/WR/TE
    'DST': 1,
}
TOTAL_POSITIONS = sum(POSITION_REQUIREMENTS.values())  # 9

# Elite Appearance Targets based on Milly Winner research (8-week analysis)
# Structure: Dict[position, List[Tuple[min_appearances, max_appearances]]] for ranks 1-15
# Index 0 = rank 1 (top player), index 1 = rank 2, etc.
ELITE_APPEARANCE_TARGETS = {
    'RB': [
        (10, 10),  # Rank 1: Must appear in all 10 lineups
        (8, 10),   # Rank 2
        (7, 9),    # Rank 3
        (6, 8),    # Rank 4
        (5, 7),    # Rank 5
        (4, 6),    # Rank 6
        (3, 5),    # Rank 7
        (2, 4),    # Rank 8
        (1, 3),    # Rank 9
        (0, 2),    # Rank 10
        (0, 2),    # Rank 11
        (0, 2),    # Rank 12
        (0, 1),    # Rank 13
        (0, 1),    # Rank 14
        (0, 1),    # Rank 15
    ],
    'WR': [
        (8, 10),   # Rank 1
        (7, 9),    # Rank 2
        (6, 8),    # Rank 3
        (5, 7),    # Rank 4
        (4, 6),    # Rank 5
        (3, 5),    # Rank 6
        (2, 4),    # Rank 7
        (1, 3),    # Rank 8
        (1, 2),    # Rank 9
        (0, 2),    # Rank 10
        (0, 1),    # Rank 11
        (0, 1),    # Rank 12
        (0, 1),    # Rank 13
        (0, 1),    # Rank 14
        (0, 1),    # Rank 15
    ],
    'QB': [
        (8, 10),   # Rank 1
        (7, 9),    # Rank 2
        (6, 8),    # Rank 3
        (4, 6),    # Rank 4
        (2, 4),    # Rank 5
        (1, 3),    # Rank 6
        (0, 2),    # Rank 7
        (0, 1),    # Rank 8
        (0, 1),    # Rank 9
        (0, 1),    # Rank 10
        (0, 1),    # Rank 11
        (0, 1),    # Rank 12
        (0, 1),    # Rank 13
        (0, 1),    # Rank 14
        (0, 1),    # Rank 15
    ],
    'TE': [
        (9, 10),   # Rank 1
        (8, 10),   # Rank 2
        (7, 9),    # Rank 3
        (6, 8),    # Rank 4
        (5, 7),    # Rank 5
        (3, 5),    # Rank 6
        (2, 4),    # Rank 7
        (1, 3),    # Rank 8
        (0, 2),    # Rank 9
        (0, 1),    # Rank 10
        (0, 1),    # Rank 11
        (0, 1),    # Rank 12
        (0, 1),    # Rank 13
        (0, 1),    # Rank 14
        (0, 1),    # Rank 15
    ],
    'DST': [
        (5, 7),    # Rank 1
        (4, 6),    # Rank 2
        (3, 5),    # Rank 3
        (2, 4),    # Rank 4
        (1, 3),    # Rank 5
        (1, 2),    # Rank 6
        (0, 2),    # Rank 7
        (0, 1),    # Rank 8
        (0, 1),    # Rank 9
        (0, 1),    # Rank 10
        (0, 1),    # Rank 11
        (0, 1),    # Rank 12
        (0, 1),    # Rank 13
        (0, 1),    # Rank 14
        (0, 1),    # Rank 15
    ],
}


@dataclass
class PlayerOptimizationData:
    """Player data for optimization."""
    player_id: int
    player_key: str
    name: str
    team: str
    position: str
    salary: int
    smart_score: float
    ownership: float
    projection: Optional[float]
    implied_team_total: Optional[float] = None  # Vegas ITT for tournament filtering
    games_with_20_plus_snaps: Optional[int] = None  # Snap count history for elite player identification


class LineupOptimizerService:
    """Service for generating optimized DraftKings lineups."""

    def __init__(self, session: Session):
        self.session = session

    def _identify_elite_players(
        self,
        players: List[PlayerOptimizationData],
    ) -> Dict[str, List[PlayerOptimizationData]]:
        """
        Identify elite players by position based on projection ranking.

        Updated for portfolio optimization: Uses PROJECTION (not Smart Score) to identify
        elite players. This provides a more objective measure of expected performance.

        Identifies top 15 players per position based on Milly Winner research showing
        winners heavily favor top-finishing players:
        - RB: #1 RB in 100% of winners, Top 4 = 76% of slots
        - WR: Top 5 = 77% of slots
        - QB: Top 3 in 75% of lineups
        - TE: Top 5 in 90% of lineups
        - DST: Top 3 in 75% of lineups

        Args:
            players: List of all available players

        Returns:
            Dict mapping position to list of elite players (sorted by projection, highest first)
        """
        elite_counts = {
            'QB': 15,   # Top 15 QBs by projection
            'RB': 15,   # Top 15 RBs by projection
            'WR': 15,   # Top 15 WRs by projection
            'TE': 15,   # Top 15 TEs by projection
            'DST': 15,  # Top 15 DSTs by projection
        }

        elite_by_position = {}

        for position, count in elite_counts.items():
            # Get all players at this position
            pos_players = [p for p in players if p.position == position]

            # Sort by PROJECTION (descending) - most objective measure of expected performance
            # Players with null projections will be sorted to the end (treated as 0)
            pos_players_sorted = sorted(
                pos_players,
                key=lambda p: p.projection if p.projection is not None else 0,
                reverse=True
            )

            # Take top N players by projection
            elite_players = pos_players_sorted[:count]
            elite_by_position[position] = elite_players

            # Log elite players for debugging
            if elite_players:
                logger.info(f"Elite {position} players (top {count} by projection):")
                for i, player in enumerate(elite_players, 1):
                    proj = player.projection if player.projection is not None else 0
                    logger.info(f"  #{i}: {player.name} ({player.team}) - Proj: {proj:.1f}, SS: {player.smart_score:.1f}")

        return elite_by_position

    def _get_elite_player_ids(
        self,
        elite_by_position: Dict[str, List[PlayerOptimizationData]],
    ) -> Set[int]:
        """
        Get set of all elite player IDs for quick lookup.

        Args:
            elite_by_position: Dict from _identify_elite_players

        Returns:
            Set of player_id values for all elite players
        """
        elite_ids = set()
        for elite_players in elite_by_position.values():
            for player in elite_players:
                elite_ids.add(player.player_id)
        return elite_ids

    def _get_elite_appearance_target(
        self,
        position: str,
        rank: int,
    ) -> Tuple[int, int]:
        """
        Get elite appearance target for a specific position and rank.

        Args:
            position: Player position (QB, RB, WR, TE, DST)
            rank: Player rank (0-indexed, 0 = #1 player)

        Returns:
            Tuple of (min_appearances, max_appearances)
        """
        if position not in ELITE_APPEARANCE_TARGETS:
            logger.warning(f"Position {position} not in ELITE_APPEARANCE_TARGETS, returning default")
            return (0, 10)

        targets = ELITE_APPEARANCE_TARGETS[position]
        if rank < 0 or rank >= len(targets):
            logger.debug(f"Rank {rank} out of bounds for {position}, returning default")
            return (0, 10)

        return targets[rank]

    def generate_lineups(
        self,
        week_id: int,
        players: List[PlayerScoreResponse],
        settings: OptimizationSettings,
    ) -> Tuple[List[GeneratedLineup], Optional[Dict[str, int]]]:
        """
        Generate optimized lineups based on Smart Scores and constraints.

        Always generates 2 baseline lineups first:
        1. "Best Smart Score" - Pure Smart Score optimization (lineup_number = -1)
        2. "Best Projection" - Pure projection optimization (lineup_number = -2)

        Then generates N user-requested lineups using portfolio optimization with
        elite appearance constraints for improved distribution of top players.

        Args:
            week_id: Week ID
            players: List of players with Smart Scores
            settings: Optimization settings (strategy, exposure limits, etc.)

        Returns:
            Tuple of (list of GeneratedLineup objects, position_counts dict if failed)
        """
        if not players:
            logger.warning("No players provided for optimization")
            return [], {}

        # Filter players by Smart Score threshold if set
        filtered_players = self._filter_by_threshold(players, settings.smart_score_threshold)

        logger.info(
            f"After Smart Score threshold filtering: {len(filtered_players)} players "
            f"(from {len(players)} total, threshold: {settings.smart_score_threshold})"
        )

        if len(filtered_players) < TOTAL_POSITIONS:
            logger.warning(f"Not enough players ({len(filtered_players)}) for {TOTAL_POSITIONS} positions")
            # Count positions before returning
            position_counts = {}
            for player in filtered_players:
                pos = player.position
                position_counts[pos] = position_counts.get(pos, 0) + 1
            return [], position_counts

        # Convert to optimization data
        opt_players = self._prepare_players(filtered_players, strategy_mode=settings.strategy_mode)

        # Log position breakdown BEFORE filtering
        pre_filter_positions = {}
        for player in filtered_players:
            if player.smart_score is not None and player.smart_score > 0:
                pre_filter_positions[player.position] = pre_filter_positions.get(player.position, 0) + 1

        logger.info(f"Position breakdown BEFORE Tournament filters: {pre_filter_positions}")

        logger.info(
            f"After preparing players (removing null Smart Scores): {len(opt_players)} players "
            f"(from {len(filtered_players)} filtered)"
        )

        # Log position breakdown AFTER filtering
        post_filter_positions = {}
        for player in opt_players:
            post_filter_positions[player.position] = post_filter_positions.get(player.position, 0) + 1

        logger.info(f"Position breakdown AFTER Tournament filters: {post_filter_positions}")

        # Show which positions lost players
        for pos in ['QB', 'RB', 'WR', 'TE', 'DST']:
            before = pre_filter_positions.get(pos, 0)
            after = post_filter_positions.get(pos, 0)
            lost = before - after
            if lost > 0:
                logger.warning(f"  {pos}: {before} → {after} (lost {lost} players to Tournament filters)")

        # Group players by position and team for constraints
        players_by_position = self._group_by_position(opt_players)
        players_by_team = self._group_by_team(opt_players)

        # Validate we have enough players in each position
        required_positions = {'QB': 1, 'RB': 2, 'WR': 3, 'TE': 1, 'DST': 1}
        missing_positions = []
        position_counts = {}
        for pos, min_count in required_positions.items():
            available = len(players_by_position.get(pos, []))
            position_counts[pos] = available
            if available < min_count:
                missing_positions.append(f"{pos}: {available} available, {min_count} required")
                logger.warning(f"Not enough {pos} players: {available} available, {min_count} required")

        if missing_positions:
            logger.error(
                f"Position validation failed after Smart Score threshold ({settings.smart_score_threshold}). "
                f"Counts: {position_counts}. Missing: {', '.join(missing_positions)}"
            )
            return [], position_counts

        # Get game info for stacking constraints
        game_info = self._get_game_info(week_id, opt_players)
        logger.info(f"Retrieved game info for {len(game_info)} teams")

        # Identify elite players for portfolio optimization
        logger.info("=" * 80)
        logger.info("IDENTIFYING ELITE PLAYERS (based on projection ranking)")
        logger.info("=" * 80)
        elite_by_position = self._identify_elite_players(opt_players)
        elite_player_ids = self._get_elite_player_ids(elite_by_position)
        logger.info(f"Total elite players identified: {len(elite_player_ids)}")
        logger.info("=" * 80)

        generated_lineups = []

        # FIRST: Generate 2 baseline lineups (unconstrained, no diversity penalties)
        logger.info("=" * 80)
        logger.info("GENERATING BASELINE LINEUPS (unconstrained optimization)")
        logger.info(f"Available players: {len(opt_players)}")
        logger.info(f"Salary cap: $50000")
        logger.info("=" * 80)

        # Baseline 1: Best Smart Score (lineup_number = -1)
        try:
            logger.info("Attempting to generate 'Best Smart Score' baseline...")
            baseline_smart_score = self._generate_baseline_lineup(
                opt_players=opt_players,
                players_by_position=players_by_position,
                players_by_team=players_by_team,
                game_info=game_info,
                settings=settings,
                lineup_number=-1,
                optimize_for='smart_score',
            )
            if baseline_smart_score:
                generated_lineups.append(baseline_smart_score)
                logger.info(f"✓ Generated baseline 'Best Smart Score': ${baseline_smart_score.total_salary/1000:.1f}K, score={baseline_smart_score.projected_score:.1f}, proj={baseline_smart_score.projected_points:.1f}")
            else:
                logger.warning("✗ Failed to generate 'Best Smart Score' baseline lineup (optimization returned None)")
        except Exception as e:
            logger.error(f"✗ Error generating 'Best Smart Score' baseline: {e}", exc_info=True)

        # Baseline 2: Best Projection (lineup_number = -2)
        try:
            logger.info("Attempting to generate 'Best Projection' baseline...")
            baseline_projection = self._generate_baseline_lineup(
                opt_players=opt_players,
                players_by_position=players_by_position,
                players_by_team=players_by_team,
                game_info=game_info,
                settings=settings,
                lineup_number=-2,
                optimize_for='projection',
            )
            if baseline_projection:
                generated_lineups.append(baseline_projection)
                logger.info(f"✓ Generated baseline 'Best Projection': ${baseline_projection.total_salary/1000:.1f}K, score={baseline_projection.projected_score:.1f}, proj={baseline_projection.projected_points:.1f}")
            else:
                logger.warning("✗ Failed to generate 'Best Projection' baseline lineup (optimization returned None)")
        except Exception as e:
            logger.error(f"✗ Error generating 'Best Projection' baseline: {e}", exc_info=True)

        logger.info("=" * 80)
        logger.info(f"Baseline generation complete. Generated {len(generated_lineups)} baseline lineups.")
        logger.info("=" * 80)

        # NOW: Generate 10 user-requested lineups using portfolio optimization
        logger.info("=" * 80)
        logger.info("GENERATING PORTFOLIO LINEUPS (10 lineups simultaneously with elite constraints)")
        logger.info("=" * 80)

        try:
            portfolio_lineups = self._generate_portfolio_lineups(
                opt_players=opt_players,
                players_by_position=players_by_position,
                players_by_team=players_by_team,
                game_info=game_info,
                settings=settings,
                elite_by_position=elite_by_position,
            )

            if portfolio_lineups:
                generated_lineups.extend(portfolio_lineups)
                logger.info(f"✓ Successfully generated {len(portfolio_lineups)} portfolio lineups")
            else:
                logger.warning("✗ Portfolio optimization failed, falling back to iterative generation")
                # Fallback to iterative generation
                portfolio_lineups = self._fallback_iterative_generation(
                    opt_players=opt_players,
                    players_by_position=players_by_position,
                    players_by_team=players_by_team,
                    game_info=game_info,
                    settings=settings,
                    generated_lineups=generated_lineups,
                    elite_by_position=elite_by_position,
                )
                generated_lineups.extend(portfolio_lineups)

        except Exception as e:
            logger.error(f"✗ Error generating portfolio lineups: {e}", exc_info=True)
            # Fallback to iterative generation
            logger.warning("Falling back to iterative generation due to exception")
            portfolio_lineups = self._fallback_iterative_generation(
                opt_players=opt_players,
                players_by_position=players_by_position,
                players_by_team=players_by_team,
                game_info=game_info,
                settings=settings,
                generated_lineups=generated_lineups,
                elite_by_position=elite_by_position,
            )
            generated_lineups.extend(portfolio_lineups)

        # Return whatever we successfully generated
        if generated_lineups:
            baseline_count = sum(1 for l in generated_lineups if l.lineup_number < 0)
            regular_count = sum(1 for l in generated_lineups if l.lineup_number > 0)
            logger.info(f"Successfully generated {len(generated_lineups)} lineups ({baseline_count} baselines + {regular_count} user-requested)")

            # Sort lineups: baselines first (negative numbers), then regular lineups by Smart Score (highest first)
            generated_lineups.sort(key=lambda x: (
                x.lineup_number >= 0,  # Baselines first (False sorts before True)
                -x.projected_score if x.lineup_number >= 0 else abs(x.lineup_number)  # Regular lineups by Smart Score DESC, baselines by number
            ))

            return generated_lineups, None
        else:
            # No lineups generated - return position counts for error message
            return [], position_counts

    def _fallback_iterative_generation(
        self,
        opt_players: List[PlayerOptimizationData],
        players_by_position: Dict[str, List[PlayerOptimizationData]],
        players_by_team: Dict[str, List[PlayerOptimizationData]],
        game_info: Dict[str, Dict],
        settings: OptimizationSettings,
        generated_lineups: List[GeneratedLineup],
        elite_by_position: Dict[str, List[PlayerOptimizationData]],
    ) -> List[GeneratedLineup]:
        """
        Fallback to iterative single-lineup generation if portfolio optimization fails.

        This ensures we always return some lineups even if portfolio optimization is infeasible.
        """
        logger.info("Using iterative generation as fallback")
        fallback_lineups = []
        consecutive_failures = 0
        max_consecutive_failures = 3

        for lineup_num in range(1, settings.num_lineups + 1):
            try:
                lineup = self._generate_single_lineup(
                    opt_players=opt_players,
                    players_by_position=players_by_position,
                    players_by_team=players_by_team,
                    game_info=game_info,
                    settings=settings,
                    previous_lineups=generated_lineups + fallback_lineups,
                    lineup_number=lineup_num,
                    elite_by_position=elite_by_position,
                )

                if lineup:
                    fallback_lineups.append(lineup)
                    consecutive_failures = 0
                    logger.info(f"Successfully generated fallback lineup {lineup_num}/{settings.num_lineups}")
                else:
                    consecutive_failures += 1
                    logger.warning(f"Failed to generate fallback lineup {lineup_num}")

                    if consecutive_failures >= max_consecutive_failures:
                        logger.warning(f"Stopping after {consecutive_failures} consecutive failures")
                        break

            except Exception as e:
                consecutive_failures += 1
                logger.error(f"Error generating fallback lineup {lineup_num}: {e}", exc_info=True)

                if consecutive_failures >= max_consecutive_failures:
                    logger.warning(f"Stopping after {consecutive_failures} consecutive failures")
                    break

        return fallback_lineups

    def _generate_portfolio_lineups(
        self,
        opt_players: List[PlayerOptimizationData],
        players_by_position: Dict[str, List[PlayerOptimizationData]],
        players_by_team: Dict[str, List[PlayerOptimizationData]],
        game_info: Dict[str, Dict],
        settings: OptimizationSettings,
        elite_by_position: Dict[str, List[PlayerOptimizationData]],
    ) -> Optional[List[GeneratedLineup]]:
        """
        Generate all 10 lineups simultaneously using portfolio optimization.

        This is the core of the elite player distribution system. Instead of generating
        lineups one at a time, we solve for all 10 lineups simultaneously with constraints
        ensuring elite players appear with the correct frequency.

        Args:
            opt_players: All available players
            players_by_position: Players grouped by position
            players_by_team: Players grouped by team
            game_info: Game information for stacking
            settings: Optimization settings
            elite_by_position: Elite players identified by position

        Returns:
            List of 10 GeneratedLineup objects, or None if optimization failed
        """
        logger.info("Setting up portfolio optimization problem for 10 lineups")

        # Create PuLP problem
        prob = pulp.LpProblem("Portfolio_10_Lineups", pulp.LpMaximize)

        # Create decision variables: 10 × N variables (10 lineups × N players)
        # Structure: player_vars[lineup_idx][player_id] = binary variable
        player_vars = {}
        for lineup_idx in range(10):
            player_vars[lineup_idx] = {}
            for player in opt_players:
                var_name = f"lineup_{lineup_idx}_player_{player.player_id}"
                player_vars[lineup_idx][player.player_id] = pulp.LpVariable(var_name, cat='Binary')

        logger.info(f"Created {10 * len(opt_players)} decision variables")

        # Objective: Maximize sum of Smart Scores across all 10 lineups
        # Also include salary bonus to encourage using full budget
        objective_terms = []

        for lineup_idx in range(10):
            # Smart Score component
            for player in opt_players:
                objective_terms.append(
                    player.smart_score * player_vars[lineup_idx][player.player_id]
                )

            # Salary bonus: reward for using salary efficiently
            lineup_salary = pulp.lpSum([
                player.salary * player_vars[lineup_idx][player.player_id]
                for player in opt_players
            ])
            objective_terms.append((lineup_salary - MIN_SALARY) * 0.05)

        prob += pulp.lpSum(objective_terms)
        logger.info("Portfolio objective function created")

        # Apply per-lineup constraints (each lineup must be valid independently)
        for lineup_idx in range(10):
            lineup_vars = player_vars[lineup_idx]

            # Position constraints
            self._add_position_constraints(prob, players_by_position, lineup_vars, settings, lineup_idx)

            # Salary cap constraint
            lineup_salary = pulp.lpSum([
                player.salary * lineup_vars[player.player_id]
                for player in opt_players
            ])
            prob += lineup_salary >= MIN_SALARY, f"lineup_{lineup_idx}_min_salary"
            prob += lineup_salary <= SALARY_CAP, f"lineup_{lineup_idx}_max_salary"

            # Team constraints
            self._add_team_constraints(prob, players_by_team, lineup_vars, settings, lineup_idx)

            # Game constraints
            self._add_game_constraints(prob, opt_players, game_info, lineup_vars, settings, lineup_idx)

            # Stacking constraints
            self._add_stacking_constraints(prob, opt_players, game_info, lineup_vars, settings, lineup_idx)

        logger.info(f"Applied per-lineup constraints for 10 lineups")

        # Add elite appearance constraints (portfolio-level)
        constraint_metadata = self._add_elite_appearance_constraints(
            prob, player_vars, elite_by_position, opt_players
        )
        logger.info(f"Added {len(constraint_metadata)} elite appearance constraints")

        # Solve with progressive relaxation if needed
        lineups = self._solve_with_relaxation(
            prob, player_vars, opt_players, elite_by_position, constraint_metadata
        )

        return lineups

    def _add_elite_appearance_constraints(
        self,
        prob: pulp.LpProblem,
        player_vars: Dict[int, Dict[int, pulp.LpVariable]],
        elite_by_position: Dict[str, List[PlayerOptimizationData]],
        opt_players: List[PlayerOptimizationData],
    ) -> List[Dict]:
        """
        Add elite appearance constraints to portfolio optimization.

        For each elite player, add min/max appearance constraints across all 10 lineups.

        Args:
            prob: PuLP problem
            player_vars: Nested dict of decision variables [lineup_idx][player_id]
            elite_by_position: Elite players by position
            opt_players: All players

        Returns:
            List of constraint metadata dicts for relaxation tracking
        """
        constraint_metadata = []

        for position, elite_players in elite_by_position.items():
            for rank, player in enumerate(elite_players):
                # Get appearance targets for this rank
                min_app, max_app = self._get_elite_appearance_target(position, rank)

                # Count total appearances of this player across all 10 lineups
                total_appearances = pulp.lpSum([
                    player_vars[lineup_idx][player.player_id]
                    for lineup_idx in range(10)
                ])

                # Min constraint
                constraint_name_min = f"elite_{position}_rank_{rank}_player_{player.player_id}_min"
                prob += total_appearances >= min_app, constraint_name_min
                constraint_metadata.append({
                    'name': constraint_name_min,
                    'position': position,
                    'rank': rank,
                    'player_id': player.player_id,
                    'player_name': player.name,
                    'type': 'min',
                    'value': min_app,
                })

                # Max constraint
                constraint_name_max = f"elite_{position}_rank_{rank}_player_{player.player_id}_max"
                prob += total_appearances <= max_app, constraint_name_max
                constraint_metadata.append({
                    'name': constraint_name_max,
                    'position': position,
                    'rank': rank,
                    'player_id': player.player_id,
                    'player_name': player.name,
                    'type': 'max',
                    'value': max_app,
                })

                logger.debug(
                    f"Elite constraint: {player.name} ({position} #{rank+1}) must appear {min_app}-{max_app} times"
                )

        return constraint_metadata

    def _solve_with_relaxation(
        self,
        prob: pulp.LpProblem,
        player_vars: Dict[int, Dict[int, pulp.LpVariable]],
        opt_players: List[PlayerOptimizationData],
        elite_by_position: Dict[str, List[PlayerOptimizationData]],
        constraint_metadata: List[Dict],
    ) -> Optional[List[GeneratedLineup]]:
        """
        Solve portfolio optimization with progressive relaxation if needed.

        If initial solve is infeasible, progressively relax elite constraints starting
        from lowest-ranked elite players (rank 15 -> 14 -> ... -> 2).
        Rank 1 (top player) constraints are never relaxed.

        Args:
            prob: PuLP problem
            player_vars: Decision variables
            opt_players: All players
            elite_by_position: Elite players by position
            constraint_metadata: Constraint tracking info

        Returns:
            List of 10 GeneratedLineup objects, or None if failed
        """
        # Initial solve
        logger.info("Attempting initial portfolio optimization solve...")
        # Set 90-second timeout for portfolio optimization (large problem: 10 lineups × ~137 players)
        solver = pulp.PULP_CBC_CMD(msg=1, timeLimit=90)  # Verbose for debugging, 90s timeout
        prob.solve(solver)

        if prob.status == pulp.LpStatusOptimal:
            logger.info("✓ Portfolio optimization succeeded on first attempt")
            return self._extract_lineups_from_portfolio(prob, player_vars, opt_players)
        elif prob.status == pulp.LpStatusNotSolved:
            # Timeout or other issue - try to extract solution anyway if feasible
            logger.warning(f"Portfolio optimization timed out or not solved (status: {pulp.LpStatus[prob.status]}), attempting to extract solution")
            lineups = self._extract_lineups_from_portfolio(prob, player_vars, opt_players)
            if lineups:
                logger.info(f"✓ Extracted {len(lineups)} lineups despite timeout")
                return lineups
            logger.warning("No valid solution found after timeout, beginning relaxation")
        else:
            # Infeasible - begin progressive relaxation
            logger.warning(f"Portfolio optimization infeasible (status: {pulp.LpStatus[prob.status]}), beginning relaxation")

        # Relax constraints from rank 14 down to rank 1 (but never relax rank 0)
        for relaxation_rank in range(14, -1, -1):  # 14, 13, 12, ..., 1, 0
            logger.info(f"Relaxing constraints for rank {relaxation_rank + 1} (0-indexed: {relaxation_rank})")

            # Remove constraints for this rank
            constraints_removed = 0
            for constraint_info in constraint_metadata:
                if constraint_info['rank'] == relaxation_rank:
                    constraint_name = constraint_info['name']
                    if constraint_name in prob.constraints:
                        del prob.constraints[constraint_name]
                        constraints_removed += 1
                        logger.debug(
                            f"Removed constraint: {constraint_info['player_name']} "
                            f"({constraint_info['position']} #{relaxation_rank+1}) "
                            f"{constraint_info['type']}={constraint_info['value']}"
                        )

            logger.info(f"Removed {constraints_removed} constraints for rank {relaxation_rank + 1}")

            # Re-solve with timeout
            prob.solve(solver)

            if prob.status == pulp.LpStatusOptimal:
                logger.info(f"✓ Portfolio optimization succeeded after relaxing rank {relaxation_rank + 1}")
                return self._extract_lineups_from_portfolio(prob, player_vars, opt_players)
            elif prob.status == pulp.LpStatusNotSolved:
                # Timeout - try to extract solution anyway
                logger.warning(f"Portfolio optimization timed out after relaxing rank {relaxation_rank + 1}, attempting to extract solution")
                lineups = self._extract_lineups_from_portfolio(prob, player_vars, opt_players)
                if lineups:
                    logger.info(f"✓ Extracted {len(lineups)} lineups despite timeout")
                    return lineups
                logger.warning(f"Still no valid solution after timeout and relaxing rank {relaxation_rank + 1}")
            else:
                logger.warning(f"Still infeasible after relaxing rank {relaxation_rank + 1}")

        # All relaxations exhausted
        logger.error("Portfolio optimization failed even after relaxing all elite constraints")
        return None

    def _extract_lineups_from_portfolio(
        self,
        prob: pulp.LpProblem,
        player_vars: Dict[int, Dict[int, pulp.LpVariable]],
        opt_players: List[PlayerOptimizationData],
    ) -> List[GeneratedLineup]:
        """
        Extract 10 lineups from solved portfolio optimization.

        Args:
            prob: Solved PuLP problem
            player_vars: Decision variables
            opt_players: All players

        Returns:
            List of 10 GeneratedLineup objects
        """
        lineups = []

        for lineup_idx in range(10):
            selected_players = []
            total_salary = 0
            total_smart_score = 0.0
            total_projection = 0.0
            total_ownership = 0.0

            for player in opt_players:
                if player_vars[lineup_idx][player.player_id].varValue == 1:
                    selected_players.append({
                        'position': player.position,
                        'player_key': player.player_key,
                        'name': player.name,
                        'team': player.team,
                        'salary': player.salary,
                        'smart_score': player.smart_score,
                        'ownership': player.ownership,
                        'projection': player.projection,
                    })
                    total_salary += player.salary
                    total_smart_score += player.smart_score
                    total_projection += player.projection if player.projection else 0
                    total_ownership += player.ownership

            # Validate lineup
            if not self._validate_lineup(selected_players, total_salary):
                logger.warning(f"Generated invalid lineup {lineup_idx + 1} in portfolio")
                continue

            avg_ownership = total_ownership / len(selected_players) if selected_players else 0.0
            if avg_ownership > 1.0:
                avg_ownership = avg_ownership / 100.0

            lineup = GeneratedLineup(
                lineup_number=lineup_idx + 1,
                players=selected_players,
                total_salary=total_salary,
                projected_score=total_smart_score,
                projected_points=total_projection,
                avg_ownership=avg_ownership,
            )

            lineups.append(lineup)
            logger.info(
                f"Portfolio lineup {lineup_idx + 1}: {len(selected_players)} players, "
                f"salary=${total_salary}, score={total_smart_score:.1f}, proj={total_projection:.1f}"
            )

        return lineups

    def _filter_by_threshold(
        self,
        players: List[PlayerScoreResponse],
        threshold: Optional[float]
    ) -> List[PlayerScoreResponse]:
        """Filter players by Smart Score threshold."""
        if threshold is None or threshold <= 0:
            return players

        filtered = [p for p in players if p.smart_score is not None and p.smart_score >= threshold]
        logger.info(f"Filtered {len(players)} players to {len(filtered)} (threshold: {threshold})")
        return filtered

    def _prepare_players(
        self,
        players: List[PlayerScoreResponse],
        strategy_mode: str = 'Balanced'
    ) -> List[PlayerOptimizationData]:
        """
        Convert PlayerScoreResponse to PlayerOptimizationData.

        Filters out invalid players:
        - Null or zero Smart Score (no projection/not playing)
        - Null or zero salary (data issues)
        - Missing projection (can't score points)

        For Tournament mode, applies additional filters:
        - ITT > 18.5 (93% of top performers)
        - Ownership filters (RB chalk OK, others < 20%)
        """
        opt_players = []
        skipped_null_score = 0
        skipped_zero_score = 0
        skipped_null_salary = 0
        skipped_zero_salary = 0
        skipped_no_projection = 0
        skipped_tournament_filter = 0

        # Track filtered players by reason for debugging
        filtered_by_itt = []
        filtered_by_ownership = []

        for player in players:
            # Skip players with null smart score
            if player.smart_score is None:
                skipped_null_score += 1
                continue

            # Skip players with zero smart score (likely not playing or missing data)
            if player.smart_score <= 0:
                logger.debug(f"Player {player.name} ({player.position}) has Smart Score {player.smart_score} - skipping")
                skipped_zero_score += 1
                continue

            # Skip players with no projection (can't score fantasy points)
            if player.projection is None or player.projection <= 0:
                logger.debug(f"Player {player.name} ({player.position}) has no projection - skipping")
                skipped_no_projection += 1
                continue

            # Check for data issues
            if player.salary is None:
                logger.warning(f"Player {player.name} has NULL salary - skipping")
                skipped_null_salary += 1
                continue

            if player.salary == 0:
                logger.warning(f"Player {player.name} has ZERO salary - skipping")
                skipped_zero_salary += 1
                continue

            # Tournament mode filters (based on research)
            if strategy_mode == 'Tournament':
                # Ownership conversion: Handle both decimal (0-1) and percentage (0-100) formats
                ownership_raw = player.ownership or 0.0
                if ownership_raw > 1.0:
                    ownership_pct = ownership_raw
                else:
                    ownership_pct = ownership_raw * 100.0

                # Very soft ITT filter: Only filter if ITT is extremely low (< 12)
                if player.implied_team_total is not None and player.implied_team_total < 12.0:
                    skipped_tournament_filter += 1
                    filtered_by_itt.append({
                        'name': player.name,
                        'position': player.position,
                        'team': player.team,
                        'itt': player.implied_team_total,
                        'ownership': ownership_pct,
                        'smart_score': player.smart_score,
                    })
                    logger.warning(
                        f"TOURNAMENT FILTER: {player.name} ({player.position}, {player.team}) - "
                        f"ITT {player.implied_team_total} < 12.0, Ownership: {ownership_pct:.1f}%, Smart Score: {player.smart_score:.1f}"
                    )
                    continue

                # Very soft ownership filter: Only filter if ownership is extremely high (> 50%)
                if player.position != 'RB' and ownership_pct >= 50.0:
                    skipped_tournament_filter += 1
                    filtered_by_ownership.append({
                        'name': player.name,
                        'position': player.position,
                        'team': player.team,
                        'itt': player.implied_team_total,
                        'ownership': ownership_pct,
                        'smart_score': player.smart_score,
                    })
                    logger.warning(
                        f"TOURNAMENT FILTER: {player.name} ({player.position}, {player.team}) - "
                        f"Ownership {ownership_pct:.1f}% >= 50% (non-RB), ITT: {player.implied_team_total}, Smart Score: {player.smart_score:.1f}"
                    )
                    continue

            opt_players.append(PlayerOptimizationData(
                player_id=player.player_id,
                player_key=player.player_key,
                name=player.name,
                team=player.team,
                position=player.position,
                salary=player.salary,
                smart_score=player.smart_score,
                ownership=player.ownership or 0.0,
                projection=player.projection,
                implied_team_total=player.implied_team_total,
                games_with_20_plus_snaps=player.games_with_20_plus_snaps,
            ))

        total_skipped = skipped_null_score + skipped_zero_score + skipped_null_salary + skipped_zero_salary + skipped_no_projection + skipped_tournament_filter
        if total_skipped > 0:
            logger.warning(
                f"Skipped {total_skipped} players: "
                f"{skipped_null_score} null scores, "
                f"{skipped_zero_score} zero/negative scores, "
                f"{skipped_no_projection} no projection, "
                f"{skipped_null_salary} null salaries, "
                f"{skipped_zero_salary} zero salaries"
                + (f", {skipped_tournament_filter} tournament filters" if skipped_tournament_filter > 0 else "")
            )

        return opt_players

    def _group_by_position(
        self,
        players: List[PlayerOptimizationData]
    ) -> Dict[str, List[PlayerOptimizationData]]:
        """Group players by position."""
        grouped = defaultdict(list)
        for player in players:
            grouped[player.position].append(player)
        return dict(grouped)

    def _group_by_team(
        self,
        players: List[PlayerOptimizationData]
    ) -> Dict[str, List[PlayerOptimizationData]]:
        """Group players by team."""
        grouped = defaultdict(list)
        for player in players:
            grouped[player.team].append(player)
        return dict(grouped)

    def _get_game_info(
        self,
        week_id: int,
        players: List[PlayerOptimizationData]
    ) -> Dict[str, Dict]:
        """Get game information for stacking constraints."""
        # Query vegas_lines to get opponent info
        query = text("""
            SELECT team, opponent
            FROM vegas_lines
            WHERE week_id = :week_id
        """)

        rows = self.session.execute(query, {"week_id": week_id}).fetchall()

        game_info = {}
        for row in rows:
            game_info[row.team] = {
                'opponent': row.opponent,
            }

        return game_info

    def _generate_single_lineup(
        self,
        opt_players: List[PlayerOptimizationData],
        players_by_position: Dict[str, List[PlayerOptimizationData]],
        players_by_team: Dict[str, List[PlayerOptimizationData]],
        game_info: Dict[str, Dict],
        settings: OptimizationSettings,
        previous_lineups: List[GeneratedLineup],
        lineup_number: int,
        elite_by_position: Dict[str, List[PlayerOptimizationData]],
    ) -> Optional[GeneratedLineup]:
        """
        Generate a single optimized lineup using PuLP.

        This is used for fallback when portfolio optimization fails.
        """
        # Create PuLP problem
        prob = pulp.LpProblem(f"Lineup_{lineup_number}", pulp.LpMaximize)

        # Create decision variables: 1 if player is selected, 0 otherwise
        player_vars = {}
        for player in opt_players:
            var_name = f"player_{player.player_id}"
            player_vars[player.player_id] = pulp.LpVariable(var_name, cat='Binary')

        # Objective: Maximize Smart Score + salary bonus
        salary_sum = pulp.lpSum([
            player.salary * player_vars[player.player_id]
            for player in opt_players
        ])

        prob += pulp.lpSum([
            player.smart_score * player_vars[player.player_id]
            for player in opt_players
        ]) + (salary_sum - MIN_SALARY) * 0.05

        # Position constraints
        self._add_position_constraints(prob, players_by_position, player_vars, settings)

        # Salary cap constraint
        prob += salary_sum >= MIN_SALARY
        prob += salary_sum <= SALARY_CAP

        # Team limit constraint
        self._add_team_constraints(prob, players_by_team, player_vars, settings)

        # Game limit constraint
        self._add_game_constraints(prob, opt_players, game_info, player_vars, settings)

        # Stacking rules
        self._add_stacking_constraints(prob, opt_players, game_info, player_vars, settings)

        # Solve
        prob.solve(pulp.PULP_CBC_CMD(msg=0))

        if prob.status != pulp.LpStatusOptimal:
            logger.warning(f"Single lineup optimization failed with status: {pulp.LpStatus[prob.status]}")
            return None

        # Extract selected players
        selected_players = []
        total_salary = 0
        total_smart_score = 0.0
        total_projection = 0.0
        total_ownership = 0.0

        for player in opt_players:
            if player_vars[player.player_id].varValue == 1:
                selected_players.append({
                    'position': player.position,
                    'player_key': player.player_key,
                    'name': player.name,
                    'team': player.team,
                    'salary': player.salary,
                    'smart_score': player.smart_score,
                    'ownership': player.ownership,
                    'projection': player.projection,
                })
                total_salary += player.salary
                total_smart_score += player.smart_score
                total_projection += player.projection if player.projection else 0
                total_ownership += player.ownership

        # Validate lineup
        if not self._validate_lineup(selected_players, total_salary):
            logger.warning(f"Generated invalid lineup {lineup_number}")
            return None

        avg_ownership = total_ownership / len(selected_players) if selected_players else 0.0
        if avg_ownership > 1.0:
            avg_ownership = avg_ownership / 100.0

        return GeneratedLineup(
            lineup_number=lineup_number,
            players=selected_players,
            total_salary=total_salary,
            projected_score=total_smart_score,
            projected_points=total_projection,
            avg_ownership=avg_ownership,
        )

    def _add_position_constraints(
        self,
        prob: pulp.LpProblem,
        players_by_position: Dict[str, List[PlayerOptimizationData]],
        player_vars: Dict[int, pulp.LpVariable],
        settings: OptimizationSettings,
        lineup_idx: Optional[int] = None,
    ):
        """Add position requirement constraints."""
        suffix = f"_lineup_{lineup_idx}" if lineup_idx is not None else ""

        # QB: Exactly 1
        qb_players = players_by_position.get('QB', [])
        if qb_players:
            prob += pulp.lpSum([player_vars[p.player_id] for p in qb_players]) == 1, f"qb_count{suffix}"

        # RB: At least 2
        rb_players = players_by_position.get('RB', [])
        wr_players = players_by_position.get('WR', [])
        te_players = players_by_position.get('TE', [])
        flex_players = rb_players + wr_players + te_players

        if rb_players:
            prob += pulp.lpSum([player_vars[p.player_id] for p in rb_players]) >= 2, f"rb_min{suffix}"

        # WR: At least 3
        if wr_players:
            prob += pulp.lpSum([player_vars[p.player_id] for p in wr_players]) >= 3, f"wr_min{suffix}"

        # TE: At least 1
        if te_players:
            prob += pulp.lpSum([player_vars[p.player_id] for p in te_players]) >= 1, f"te_min{suffix}"

        # Total RB/WR/TE/FLEX: Exactly 7
        if flex_players:
            prob += pulp.lpSum([player_vars[p.player_id] for p in flex_players]) == 7, f"flex_total{suffix}"

        # DST: Exactly 1
        dst_players = players_by_position.get('DST', [])
        if dst_players:
            prob += pulp.lpSum([player_vars[p.player_id] for p in dst_players]) == 1, f"dst_count{suffix}"

        # Total: 9 players
        all_players = sum(players_by_position.values(), [])
        prob += pulp.lpSum([player_vars[p.player_id] for p in all_players]) == TOTAL_POSITIONS, f"total_players{suffix}"

    def _add_team_constraints(
        self,
        prob: pulp.LpProblem,
        players_by_team: Dict[str, List[PlayerOptimizationData]],
        player_vars: Dict[int, pulp.LpVariable],
        settings: OptimizationSettings,
        lineup_idx: Optional[int] = None,
    ):
        """Add max players per team constraint."""
        suffix = f"_lineup_{lineup_idx}" if lineup_idx is not None else ""
        max_team = settings.max_players_per_team

        for team, team_players in players_by_team.items():
            if team_players:
                prob += pulp.lpSum([player_vars[p.player_id] for p in team_players]) <= max_team, f"team_{team}{suffix}"

    def _add_game_constraints(
        self,
        prob: pulp.LpProblem,
        players: List[PlayerOptimizationData],
        game_info: Dict[str, Dict],
        player_vars: Dict[int, pulp.LpVariable],
        settings: OptimizationSettings,
        lineup_idx: Optional[int] = None,
    ):
        """Add max players per game constraint."""
        suffix = f"_lineup_{lineup_idx}" if lineup_idx is not None else ""
        max_game = settings.max_players_per_game

        # Group players by game
        games: Dict[str, List[PlayerOptimizationData]] = defaultdict(list)

        for player in players:
            opponent = game_info.get(player.team, {}).get('opponent')
            if opponent:
                # Create game key (alphabetically sorted teams)
                game_key = tuple(sorted([player.team, opponent]))
                games[game_key].append(player)

        for game_key, game_players in games.items():
            if len(game_players) > max_game:
                game_str = "_".join(game_key)
                prob += pulp.lpSum([player_vars[p.player_id] for p in game_players]) <= max_game, f"game_{game_str}{suffix}"

    def _add_stacking_constraints(
        self,
        prob: pulp.LpProblem,
        players: List[PlayerOptimizationData],
        game_info: Dict[str, Dict],
        player_vars: Dict[int, pulp.LpVariable],
        settings: OptimizationSettings,
        lineup_idx: Optional[int] = None,
    ):
        """Add stacking rule constraints."""
        if not settings.stacking_rules:
            return

        suffix = f"_lineup_{lineup_idx}" if lineup_idx is not None else ""

        # QB + WR/TE stack rule
        if settings.stacking_rules.qb_wr_stack_enabled:
            qb_players = [p for p in players if p.position == 'QB']
            wr_players = [p for p in players if p.position == 'WR']
            te_players = [p for p in players if p.position == 'TE']

            for qb in qb_players:
                qb_team_wrs = [wr for wr in wr_players if wr.team == qb.team]
                qb_team_tes = [te for te in te_players if te.team == qb.team]
                qb_team_pass_catchers = qb_team_wrs + qb_team_tes

                if qb_team_pass_catchers:
                    prob += pulp.lpSum([
                        player_vars[pc.player_id] for pc in qb_team_pass_catchers
                    ]) >= player_vars[qb.player_id], f"qb_stack_{qb.team}{suffix}"

    def _generate_baseline_lineup(
        self,
        opt_players: List[PlayerOptimizationData],
        players_by_position: Dict[str, List[PlayerOptimizationData]],
        players_by_team: Dict[str, List[PlayerOptimizationData]],
        game_info: Dict[str, Dict[str, str]],
        settings: OptimizationSettings,
        lineup_number: int,
        optimize_for: str,  # 'smart_score' or 'projection'
    ) -> Optional[GeneratedLineup]:
        """
        Generate a single baseline lineup optimizing for either Smart Score or Projection.

        No diversity penalties, no overlap constraints - pure optimization.
        """
        prob = pulp.LpProblem(f"Baseline_{optimize_for}", pulp.LpMaximize)

        # Create binary variables for each player
        player_vars = {}
        for player in opt_players:
            var_name = f"player_{player.player_id}"
            player_vars[player.player_id] = pulp.LpVariable(var_name, cat='Binary')

        # Objective: Maximize Smart Score OR Projection ONLY
        if optimize_for == 'smart_score':
            prob += pulp.lpSum([
                player.smart_score * player_vars[player.player_id]
                for player in opt_players
            ])
        else:  # 'projection'
            prob += pulp.lpSum([
                player.projection * player_vars[player.player_id]
                for player in opt_players
            ])

        # Position constraints
        self._add_position_constraints(prob, players_by_position, player_vars, settings)

        # Salary constraint
        min_salary = SALARY_CAP - 2000
        salary_sum = pulp.lpSum([
            player.salary * player_vars[player.player_id]
            for player in opt_players
        ])
        prob += salary_sum >= min_salary
        prob += salary_sum <= SALARY_CAP

        # Solve
        prob.solve(pulp.PULP_CBC_CMD(msg=0))

        if prob.status != pulp.LpStatusOptimal:
            logger.warning(f"Baseline {optimize_for} optimization failed with status: {pulp.LpStatus[prob.status]}")
            return None

        # Extract selected players
        selected_players = [
            player for player in opt_players
            if player_vars[player.player_id].varValue == 1
        ]

        if not selected_players:
            logger.warning(f"Baseline {optimize_for}: No players selected")
            return None

        # Calculate totals
        total_salary = sum(p.salary for p in selected_players)
        total_smart_score = sum(p.smart_score for p in selected_players)
        total_projection = sum(p.projection if p.projection else 0 for p in selected_players)
        avg_ownership = sum(p.ownership for p in selected_players) / len(selected_players)

        if avg_ownership > 1.0:
            avg_ownership = avg_ownership / 100.0

        # Convert to player dicts
        player_dicts = [
            {
                'player_key': p.player_key,
                'name': p.name,
                'position': p.position,
                'team': p.team,
                'salary': p.salary,
                'projection': p.projection,
                'smart_score': p.smart_score,
                'ownership': p.ownership,
            }
            for p in selected_players
        ]

        lineup = GeneratedLineup(
            lineup_number=lineup_number,
            players=player_dicts,
            total_salary=total_salary,
            projected_score=total_smart_score,
            projected_points=total_projection,
            avg_ownership=avg_ownership,
        )

        return lineup

    def _validate_lineup(
        self,
        players: List[Dict],
        total_salary: int
    ) -> bool:
        """Validate that lineup meets all constraints."""
        if len(players) != TOTAL_POSITIONS:
            return False

        if total_salary > SALARY_CAP:
            return False

        # Count positions
        pos_counts = defaultdict(int)
        for player in players:
            pos_counts[player['position']] += 1

        # Check position requirements
        if pos_counts.get('QB', 0) != 1:
            return False
        if pos_counts.get('RB', 0) < 2:
            return False
        if pos_counts.get('WR', 0) < 3:
            return False
        if pos_counts.get('TE', 0) < 1:
            return False
        if pos_counts.get('DST', 0) != 1:
            return False

        # Total RB/WR/TE should be 7
        rb_wr_te_count = pos_counts.get('RB', 0) + pos_counts.get('WR', 0) + pos_counts.get('TE', 0)
        if rb_wr_te_count != 7:
            return False

        return True
