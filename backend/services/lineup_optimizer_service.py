"""
Lineup Optimizer Service for generating optimal DraftKings lineups.

Uses PuLP linear programming to solve constrained optimization problem:
- Maximize Smart Score across lineups
- Enforce DraftKings constraints (positions, salary cap)
- Apply user settings (strategy mode, exposure limits, stacking rules)
- Generate diverse lineups (portfolio optimization with elite appearance constraints)
- Supports both Main Slate and Showdown contest modes

Performance Optimizations (Task 15):
- Captain candidate caching to avoid recalculation
- Performance timing and logging
- Optimized database queries with proper indexing
"""

import logging
import time
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict
from functools import lru_cache

import pulp
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.schemas.smart_score_schemas import PlayerScoreResponse
from backend.schemas.lineup_schemas import (
    OptimizationSettings,
    GeneratedLineup,
)

logger = logging.getLogger(__name__)

# DraftKings Main Slate constraints
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

# DraftKings Showdown constraints
SHOWDOWN_SALARY_CAP = 50000
SHOWDOWN_MIN_SALARY = SHOWDOWN_SALARY_CAP - 3000  # $47,000 minimum
SHOWDOWN_POSITION_REQUIREMENTS = {
    'CPT': 1,   # Captain (any position)
    'FLEX': 5,  # FLEX (QB/RB/WR/TE/K/DST)
}
SHOWDOWN_TOTAL_POSITIONS = sum(SHOWDOWN_POSITION_REQUIREMENTS.values())  # 6
CAPTAIN_MULTIPLIER = 1.5  # Captain earns 1.5x salary and 1.5x points

# Elite Appearance Targets - Updated to be less restrictive
# Structure: Dict[position, List[Tuple[min_appearances, max_appearances]]] for ranks 1-15
# Index 0 = rank 1 (top player), index 1 = rank 2, etc.
#
# Updated constraints:
# - Max appearance capped at 5 (half of 10 lineups) for top players
# - Reduced minimums to allow more flexibility
# - All based on Smart Score ranking (not projection)
ELITE_APPEARANCE_TARGETS = {
    'RB': [
        (3, 5),   # Rank 1: 3-5 appearances (max half of lineups)
        (2, 4),   # Rank 2: 2-4 appearances
        (2, 3),   # Rank 3: 2-3 appearances
        (1, 3),   # Rank 4: 1-3 appearances
        (1, 2),   # Rank 5: 1-2 appearances
        (0, 2),   # Rank 6: 0-2 appearances
        (0, 2),   # Rank 7: 0-2 appearances
        (0, 1),   # Rank 8: 0-1 appearances
        (0, 1),   # Rank 9: 0-1 appearances
        (0, 1),   # Rank 10: 0-1 appearances
        (0, 1),   # Rank 11: 0-1 appearances
        (0, 1),   # Rank 12: 0-1 appearances
        (0, 1),   # Rank 13: 0-1 appearances
        (0, 1),   # Rank 14: 0-1 appearances
        (0, 1),   # Rank 15: 0-1 appearances
    ],
    'WR': [
        (3, 5),   # Rank 1: 3-5 appearances (max half of lineups)
        (2, 4),   # Rank 2: 2-4 appearances
        (2, 3),   # Rank 3: 2-3 appearances
        (1, 3),   # Rank 4: 1-3 appearances
        (1, 2),   # Rank 5: 1-2 appearances
        (0, 2),   # Rank 6: 0-2 appearances
        (0, 2),   # Rank 7: 0-2 appearances
        (0, 1),   # Rank 8: 0-1 appearances
        (0, 1),   # Rank 9: 0-1 appearances
        (0, 1),   # Rank 10: 0-1 appearances
        (0, 1),   # Rank 11: 0-1 appearances
        (0, 1),   # Rank 12: 0-1 appearances
        (0, 1),   # Rank 13: 0-1 appearances
        (0, 1),   # Rank 14: 0-1 appearances
        (0, 1),   # Rank 15: 0-1 appearances
    ],
    'QB': [
        (3, 5),   # Rank 1: 3-5 appearances (max half of lineups)
        (2, 4),   # Rank 2: 2-4 appearances
        (2, 3),   # Rank 3: 2-3 appearances
        (1, 2),   # Rank 4: 1-2 appearances
        (0, 2),   # Rank 5: 0-2 appearances
        (0, 2),   # Rank 6: 0-2 appearances
        (0, 1),   # Rank 7: 0-1 appearances
        (0, 1),   # Rank 8: 0-1 appearances
        (0, 1),   # Rank 9: 0-1 appearances
        (0, 1),   # Rank 10: 0-1 appearances
        (0, 1),   # Rank 11: 0-1 appearances
        (0, 1),   # Rank 12: 0-1 appearances
        (0, 1),   # Rank 13: 0-1 appearances
        (0, 1),   # Rank 14: 0-1 appearances
        (0, 1),   # Rank 15: 0-1 appearances
    ],
    'TE': [
        (3, 5),   # Rank 1: 3-5 appearances (max half of lineups)
        (2, 4),   # Rank 2: 2-4 appearances
        (2, 3),   # Rank 3: 2-3 appearances
        (1, 3),   # Rank 4: 1-3 appearances
        (1, 2),   # Rank 5: 1-2 appearances
        (0, 2),   # Rank 6: 0-2 appearances
        (0, 2),   # Rank 7: 0-2 appearances
        (0, 1),   # Rank 8: 0-1 appearances
        (0, 1),   # Rank 9: 0-1 appearances
        (0, 1),   # Rank 10: 0-1 appearances
        (0, 1),   # Rank 11: 0-1 appearances
        (0, 1),   # Rank 12: 0-1 appearances
        (0, 1),   # Rank 13: 0-1 appearances
        (0, 1),   # Rank 14: 0-1 appearances
        (0, 1),   # Rank 15: 0-1 appearances
    ],
    'DST': [
        (2, 4),   # Rank 1: 2-4 appearances (DST less concentrated)
        (2, 3),   # Rank 2: 2-3 appearances
        (1, 2),   # Rank 3: 1-2 appearances
        (1, 2),   # Rank 4: 1-2 appearances
        (0, 2),   # Rank 5: 0-2 appearances
        (0, 1),   # Rank 6: 0-1 appearances
        (0, 1),   # Rank 7: 0-1 appearances
        (0, 1),   # Rank 8: 0-1 appearances
        (0, 1),   # Rank 9: 0-1 appearances
        (0, 1),   # Rank 10: 0-1 appearances
        (0, 1),   # Rank 11: 0-1 appearances
        (0, 1),   # Rank 12: 0-1 appearances
        (0, 1),   # Rank 13: 0-1 appearances
        (0, 1),   # Rank 14: 0-1 appearances
        (0, 1),   # Rank 15: 0-1 appearances
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
        # Cache for captain candidates to avoid recalculation (Task 15.2)
        self._captain_candidates_cache: Optional[List[PlayerOptimizationData]] = None
        self._cache_player_hash: Optional[str] = None

    def _get_player_pool_hash(self, players: List[PlayerOptimizationData]) -> str:
        """
        Generate a hash of the player pool for cache invalidation.

        Performance optimization (Task 15.2): Cache captain candidates across lineup generation.
        """
        # Use player IDs sorted to create a stable hash
        return ','.join(sorted(str(p.player_id) for p in players))

    def _select_captain_candidates(
        self,
        players: List[PlayerOptimizationData],
        locked_captain_id: Optional[str] = None,
    ) -> List[PlayerOptimizationData]:
        """
        Select captain candidates based on value calculation.

        Performance optimization (Task 15.2):
        - Caches captain candidates to avoid recalculation across multiple lineups
        - Pre-calculates captain values for all players once

        If locked_captain_id is provided, returns only that player.
        Otherwise, returns top 5 players by captain value.

        Captain value formula: (smart_score * 1.5) / (salary * 1.5) = smart_score / salary

        Args:
            players: List of all available players
            locked_captain_id: Optional player_key to lock as captain

        Returns:
            List of captain candidate players (1 if locked, up to 5 otherwise)
        """
        # Performance timing (Task 15.1)
        start_time = time.time()

        if locked_captain_id:
            # Find locked captain
            locked_player = next((p for p in players if p.player_key == locked_captain_id), None)
            if locked_player:
                logger.info(f"Using locked captain: {locked_player.name} ({locked_player.position})")
                return [locked_player]
            else:
                logger.warning(f"Locked captain {locked_captain_id} not found in player pool")
                return []

        # Check cache (Task 15.2 optimization)
        player_hash = self._get_player_pool_hash(players)
        if self._captain_candidates_cache and self._cache_player_hash == player_hash:
            elapsed = (time.time() - start_time) * 1000
            logger.info(f"Using cached captain candidates (cache hit, {elapsed:.2f}ms)")
            return self._captain_candidates_cache

        # Calculate captain value for each player: smart_score / salary (multipliers cancel out)
        # Pre-calculate all values at once (Task 15.2 optimization)
        captain_values = [
            (player, player.smart_score / player.salary)
            for player in players
            if player.salary > 0  # Avoid division by zero
        ]

        # Sort by value (descending) and take top 5
        captain_values.sort(key=lambda x: x[1], reverse=True)
        top_candidates = [player for player, value in captain_values[:5]]

        # Cache results (Task 15.2)
        self._captain_candidates_cache = top_candidates
        self._cache_player_hash = player_hash

        elapsed = (time.time() - start_time) * 1000
        logger.info(f"Captain candidate selection completed in {elapsed:.2f}ms (cache miss)")
        logger.info(f"Selected top {len(top_candidates)} captain candidates:")
        for player in top_candidates:
            value = player.smart_score / player.salary
            logger.info(
                f"  {player.name} ({player.position}): value={value:.6f}, "
                f"SS={player.smart_score:.1f}, salary=${player.salary}"
            )

        return top_candidates

    def _validate_showdown_lineup_feasibility(
        self,
        players: List[PlayerOptimizationData],
        locked_captain_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Pre-check if showdown lineup is feasible before optimization.

        Args:
            players: Available player pool
            locked_captain_id: Optional locked captain player_key

        Returns:
            Tuple of (is_feasible, error_message)
        """
        if len(players) < SHOWDOWN_TOTAL_POSITIONS:
            return False, f"Not enough players: {len(players)} available, need {SHOWDOWN_TOTAL_POSITIONS}"

        if locked_captain_id:
            # Find locked captain
            locked_captain = next((p for p in players if p.player_key == locked_captain_id), None)
            if not locked_captain:
                return False, f"Locked captain '{locked_captain_id}' not found in player pool"

            # Check if remaining salary supports 5 FLEX players
            captain_salary = int(locked_captain.salary * CAPTAIN_MULTIPLIER)
            remaining_salary = SHOWDOWN_SALARY_CAP - captain_salary

            # Get 5 cheapest non-captain players
            other_players = [p for p in players if p.player_key != locked_captain_id]
            other_players_sorted = sorted(other_players, key=lambda p: p.salary)

            if len(other_players_sorted) < 5:
                return False, "Not enough non-captain players for 5 FLEX positions"

            min_flex_cost = sum(p.salary for p in other_players_sorted[:5])

            if min_flex_cost > remaining_salary:
                return False, (
                    f"Captain lock prevents valid lineup construction: "
                    f"Captain {locked_captain.name} costs ${captain_salary} (${locked_captain.salary} * 1.5), "
                    f"leaving ${remaining_salary} for 5 FLEX players, but minimum cost is ${min_flex_cost}"
                )

            logger.info(
                f"Locked captain validation passed: {locked_captain.name} (${captain_salary}), "
                f"remaining ${remaining_salary}, min FLEX cost ${min_flex_cost}"
            )

        else:
            # Check if ANY captain + 5 FLEX combination exists under cap
            # Sort players by salary
            players_sorted = sorted(players, key=lambda p: p.salary)

            # Try cheapest 6 players
            if len(players_sorted) < 6:
                return False, f"Not enough players for 6-player showdown lineup"

            cheapest_6 = players_sorted[:6]

            # Try making cheapest player captain (worst case)
            min_captain_salary = int(cheapest_6[0].salary * CAPTAIN_MULTIPLIER)
            min_flex_salary = sum(p.salary for p in cheapest_6[1:6])
            min_total = min_captain_salary + min_flex_salary

            if min_total > SHOWDOWN_SALARY_CAP:
                return False, (
                    f"Cannot fit any captain + 5 FLEX under ${SHOWDOWN_SALARY_CAP} cap: "
                    f"minimum possible cost is ${min_total}"
                )

        return True, None

    def generate_lineups(
        self,
        week_id: int,
        players: List[PlayerScoreResponse],
        settings: OptimizationSettings,
    ) -> Tuple[List[GeneratedLineup], Optional[Dict[str, int]]]:
        """
        Generate optimized lineups based on Smart Scores and constraints.

        Performance monitoring (Task 15.1 & 15.5):
        - Logs lineup generation time
        - Tracks performance metrics for monitoring

        Supports both Main Slate and Showdown contest modes.

        Main Slate:
        - Always generates 2 baseline lineups first:
          1. "Best Smart Score" - Pure Smart Score optimization (lineup_number = -1)
          2. "Best Projection" - Pure projection optimization (lineup_number = -2)
        - Then generates N user-requested lineups using portfolio optimization

        Showdown:
        - Always generates 2 baseline lineups first:
          1. "Best Smart Score" - Pure Smart Score optimization (lineup_number = -1)
          2. "Best Projection" - Pure projection optimization (lineup_number = -2)
        - Then generates N user-requested lineups with 1 CPT + 5 FLEX format
        - Captain selection based on value: smart_score / salary
        - Different captains across lineups for diversity

        Args:
            week_id: Week ID
            players: List of players with Smart Scores
            settings: Optimization settings (strategy, exposure limits, contest_mode, etc.)

        Returns:
            Tuple of (list of GeneratedLineup objects, position_counts dict if failed)
        """
        # Performance timing (Task 15.1 & 15.5)
        generation_start_time = time.time()

        if not players:
            logger.warning("No players provided for optimization")
            return [], {}

        # Route to showdown optimizer if contest_mode is 'showdown'
        if settings.contest_mode == 'showdown':
            result = self._generate_showdown_lineups(week_id, players, settings)

            # Log performance metrics (Task 15.5)
            generation_time = time.time() - generation_start_time
            logger.info(f"[PERFORMANCE] Showdown lineup generation completed in {generation_time:.2f}s")

            return result

        # Otherwise, use main slate optimizer (existing logic)
        result = self._generate_main_slate_lineups(week_id, players, settings)

        # Log performance metrics (Task 15.5)
        generation_time = time.time() - generation_start_time
        logger.info(f"[PERFORMANCE] Main slate lineup generation completed in {generation_time:.2f}s")

        return result

    def _generate_showdown_lineups(
        self,
        week_id: int,
        players: List[PlayerScoreResponse],
        settings: OptimizationSettings,
    ) -> Tuple[List[GeneratedLineup], Optional[Dict[str, int]]]:
        """
        Generate showdown lineups (1 CPT + 5 FLEX format).

        Performance optimizations (Task 15.2):
        - Captain candidates are cached
        - Lineup generation is optimized with efficient data structures

        Args:
            week_id: Week ID
            players: List of players with Smart Scores
            settings: Optimization settings

        Returns:
            Tuple of (list of GeneratedLineup objects, position_counts dict if failed)
        """
        logger.info("=" * 80)
        logger.info("GENERATING SHOWDOWN LINEUPS")
        logger.info(f"Players: {len(players)}, Lineups: {settings.num_lineups}")
        logger.info("=" * 80)

        # Performance timing (Task 15.1)
        showdown_start_time = time.time()

        # Filter players by Smart Score percentile if set
        filtered_players = self._filter_by_percentile(players, settings.exclude_bottom_percentile)

        logger.info(
            f"After Smart Score percentile filtering: {len(filtered_players)} players "
            f"(from {len(players)} total, exclude bottom {settings.exclude_bottom_percentile}%)"
        )

        if len(filtered_players) < SHOWDOWN_TOTAL_POSITIONS:
            logger.warning(f"Not enough players ({len(filtered_players)}) for {SHOWDOWN_TOTAL_POSITIONS} positions")
            return [], {}

        # Convert to optimization data
        opt_players = self._prepare_players(
            filtered_players,
            strategy_mode=settings.strategy_mode,
        )

        logger.info(
            f"After preparing players (removing null Smart Scores): {len(opt_players)} players "
            f"(from {len(filtered_players)} filtered)"
        )

        if len(opt_players) < SHOWDOWN_TOTAL_POSITIONS:
            logger.warning(f"Not enough valid players ({len(opt_players)}) for showdown lineup")
            return [], {}

        # Validate lineup feasibility
        is_feasible, error_msg = self._validate_showdown_lineup_feasibility(
            opt_players,
            locked_captain_id=settings.locked_captain_id,
        )

        if not is_feasible:
            logger.error(f"Showdown lineup not feasible: {error_msg}")
            return [], {}

        # Generate baseline lineups first (Best Smart Score and Best Projection)
        generated_lineups = []
        
        # Baseline 1: Best Smart Score (lineup_number = -1)
        try:
            logger.info("Attempting to generate showdown 'Best Smart Score' baseline...")
            baseline_smart_score = self._generate_baseline_showdown_lineup(
                opt_players=opt_players,
                settings=settings,
                lineup_number=-1,
                optimize_for='smart_score',
            )
            if baseline_smart_score:
                generated_lineups.append(baseline_smart_score)
                logger.info(
                    f"✓ Generated showdown baseline 'Best Smart Score': "
                    f"captain={baseline_smart_score.players[0]['name'] if baseline_smart_score.players else 'N/A'}, "
                    f"salary=${baseline_smart_score.total_salary}, "
                    f"score={baseline_smart_score.projected_score:.1f}, proj={baseline_smart_score.projected_points:.1f}"
                )
            else:
                logger.error(
                    "✗ Failed to generate showdown 'Best Smart Score' baseline lineup. "
                    "Check logs above for optimization failure reason."
                )
        except Exception as e:
            logger.error(
                f"✗ Exception generating showdown 'Best Smart Score' baseline: {e}", 
                exc_info=True
            )

        # Baseline 2: Best Projection (lineup_number = -2)
        try:
            logger.info("Attempting to generate showdown 'Best Projection' baseline...")
            baseline_projection = self._generate_baseline_showdown_lineup(
                opt_players=opt_players,
                settings=settings,
                lineup_number=-2,
                optimize_for='projection',
            )
            if baseline_projection:
                generated_lineups.append(baseline_projection)
                logger.info(
                    f"✓ Generated showdown baseline 'Best Projection': "
                    f"captain={baseline_projection.players[0]['name'] if baseline_projection.players else 'N/A'}, "
                    f"salary=${baseline_projection.total_salary}, "
                    f"score={baseline_projection.projected_score:.1f}, proj={baseline_projection.projected_points:.1f}"
                )
            else:
                logger.warning("✗ Failed to generate showdown 'Best Projection' baseline lineup")
        except Exception as e:
            logger.error(f"✗ Error generating showdown 'Best Projection' baseline: {e}", exc_info=True)

        # Select captain candidates (uses cache from Task 15.2)
        captain_selection_start = time.time()
        captain_candidates = self._select_captain_candidates(
            opt_players,
            locked_captain_id=settings.locked_captain_id,
        )
        captain_selection_time = (time.time() - captain_selection_start) * 1000
        logger.info(f"[PERFORMANCE] Captain selection: {captain_selection_time:.2f}ms")

        if not captain_candidates:
            logger.error("No captain candidates found")
            # Return baseline lineups if we have them, even if no candidates found
            if generated_lineups:
                logger.info(f"Returning {len(generated_lineups)} baseline showdown lineups")
                return generated_lineups, None
            return [], {}

        # Generate regular lineups with different captains
        lineup_gen_times = []

        for lineup_idx in range(settings.num_lineups):
            lineup_start = time.time()

            # Rotate through captain candidates to ensure diversity
            captain = captain_candidates[lineup_idx % len(captain_candidates)]

            lineup = self._generate_single_showdown_lineup(
                opt_players=opt_players,
                captain=captain,
                settings=settings,
                lineup_number=lineup_idx + 1,
            )

            lineup_time = (time.time() - lineup_start) * 1000
            lineup_gen_times.append(lineup_time)

            if lineup:
                generated_lineups.append(lineup)
                logger.info(
                    f"Generated showdown lineup {lineup_idx + 1}/{settings.num_lineups}: "
                    f"captain={captain.name}, salary=${lineup.total_salary}, "
                    f"score={lineup.projected_score:.1f}, time={lineup_time:.2f}ms"
                )
            else:
                logger.warning(f"Failed to generate showdown lineup {lineup_idx + 1}")

        # Performance metrics (Task 15.5)
        total_time = (time.time() - showdown_start_time)
        avg_lineup_time = sum(lineup_gen_times) / len(lineup_gen_times) if lineup_gen_times else 0

        logger.info(f"[PERFORMANCE] Showdown generation summary:")
        logger.info(f"  Total time: {total_time:.2f}s")
        logger.info(f"  Lineups generated: {len(generated_lineups)}/{settings.num_lineups}")
        logger.info(f"  Average per lineup: {avg_lineup_time:.2f}ms")
        logger.info(f"  Captain selection time: {captain_selection_time:.2f}ms")

        if generated_lineups:
            logger.info(f"Successfully generated {len(generated_lineups)} showdown lineups")
            return generated_lineups, None
        else:
            logger.error("Failed to generate any showdown lineups")
            return [], {}

    def _generate_single_showdown_lineup(
        self,
        opt_players: List[PlayerOptimizationData],
        captain: PlayerOptimizationData,
        settings: OptimizationSettings,
        lineup_number: int,
    ) -> Optional[GeneratedLineup]:
        """
        Generate a single showdown lineup with specified captain.

        Args:
            opt_players: All available players
            captain: Player to use as captain
            settings: Optimization settings
            lineup_number: Lineup number

        Returns:
            GeneratedLineup object or None if failed
        """
        # Create PuLP problem
        prob = pulp.LpProblem(f"Showdown_Lineup_{lineup_number}", pulp.LpMaximize)

        # Create binary variables for each player as FLEX (exclude captain from FLEX)
        flex_vars = {}
        for player in opt_players:
            if player.player_id != captain.player_id:
                var_name = f"flex_{player.player_id}"
                flex_vars[player.player_id] = pulp.LpVariable(var_name, cat='Binary')

        # Objective: Maximize (captain Smart Score * 1.5) + sum(FLEX Smart Scores)
        objective_terms = [captain.smart_score * CAPTAIN_MULTIPLIER]

        for player in opt_players:
            if player.player_id != captain.player_id:
                objective_terms.append(
                    player.smart_score * flex_vars[player.player_id]
                )

        prob += pulp.lpSum(objective_terms)

        # Constraint: Exactly 5 FLEX players
        prob += pulp.lpSum([flex_vars[p.player_id] for p in opt_players if p.player_id != captain.player_id]) == 5

        # Constraint: Total salary <= $50,000 (DraftKings Showdown cap)
        # Captain salary = base_salary * 1.5
        captain_salary = int(captain.salary * CAPTAIN_MULTIPLIER)
        flex_salary_sum = pulp.lpSum([
            player.salary * flex_vars[player.player_id]
            for player in opt_players if player.player_id != captain.player_id
        ])
        # Total salary = (captain base salary * 1.5) + sum(FLEX base salaries) <= $50,000
        prob += captain_salary + flex_salary_sum <= SHOWDOWN_SALARY_CAP

        # Constraint: Total salary >= $48,000 (use most of budget)
        prob += captain_salary + flex_salary_sum >= SHOWDOWN_MIN_SALARY

        # Ownership constraint (if set)
        if settings.max_ownership and settings.max_ownership > 0:
            # Calculate average ownership including captain
            # Captain counts as 1 position out of 6
            captain_ownership = self._normalize_ownership(captain.ownership or 0.0)
            flex_ownership_sum = pulp.lpSum([
                self._normalize_ownership(player.ownership or 0.0) * flex_vars[player.player_id]
                for player in opt_players if player.player_id != captain.player_id
            ])
            total_ownership = captain_ownership + flex_ownership_sum
            max_total_ownership = settings.max_ownership * SHOWDOWN_TOTAL_POSITIONS
            prob += total_ownership <= max_total_ownership

        # Solve with reduced timeout for faster individual lineup generation (Task 15.2)
        prob.solve(pulp.PULP_CBC_CMD(msg=0, timeLimit=15))  # 15s timeout per lineup

        if prob.status != pulp.LpStatusOptimal:
            logger.warning(
                f"Showdown lineup optimization failed with status: {pulp.LpStatus[prob.status]} "
                f"(captain={captain.name})"
            )
            return None

        # Extract selected players
        selected_players = []
        total_salary = captain_salary
        total_smart_score = captain.smart_score * CAPTAIN_MULTIPLIER
        total_projection = (captain.projection * CAPTAIN_MULTIPLIER) if captain.projection else 0
        total_ownership = captain.ownership or 0.0

        # Add captain
        selected_players.append({
            'position': captain.position,
            'player_key': captain.player_key,
            'name': captain.name,
            'team': captain.team,
            'salary': captain.salary,
            'smart_score': captain.smart_score,
            'ownership': captain.ownership,
            'projection': captain.projection,
            'is_captain': True,
        })

        # Add FLEX players
        for player in opt_players:
            if player.player_id != captain.player_id:
                if flex_vars[player.player_id].varValue == 1:
                    selected_players.append({
                        'position': player.position,
                        'player_key': player.player_key,
                        'name': player.name,
                        'team': player.team,
                        'salary': player.salary,
                        'smart_score': player.smart_score,
                        'ownership': player.ownership,
                        'projection': player.projection,
                        'is_captain': False,
                    })
                    total_salary += player.salary
                    total_smart_score += player.smart_score
                    total_projection += player.projection if player.projection else 0
                    total_ownership += player.ownership or 0.0

        # Validate lineup structure: Must have exactly 1 Captain + 5 FLEX = 6 total players
        captain_count = sum(1 for p in selected_players if p.get('is_captain', False))
        flex_count = sum(1 for p in selected_players if not p.get('is_captain', False))
        
        if len(selected_players) != SHOWDOWN_TOTAL_POSITIONS:
            logger.warning(f"Invalid showdown lineup: {len(selected_players)} players (expected {SHOWDOWN_TOTAL_POSITIONS})")
            return None
        
        if captain_count != 1:
            logger.warning(f"Invalid showdown lineup: {captain_count} captains (expected 1)")
            return None
        
        if flex_count != 5:
            logger.warning(f"Invalid showdown lineup: {flex_count} FLEX players (expected 5)")
            return None
        
        # Validate salary cap: total_salary should be <= $50,000
        # total_salary = (captain base salary * 1.5) + sum(FLEX base salaries)
        if total_salary > SHOWDOWN_SALARY_CAP:
            logger.warning(
                f"Invalid showdown lineup salary: ${total_salary} exceeds ${SHOWDOWN_SALARY_CAP} cap "
                f"(captain=${captain_salary}, flex=${total_salary - captain_salary})"
            )
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

    def _generate_baseline_showdown_lineup(
        self,
        opt_players: List[PlayerOptimizationData],
        settings: OptimizationSettings,
        lineup_number: int,
        optimize_for: str,  # 'smart_score' or 'projection'
    ) -> Optional[GeneratedLineup]:
        """
        Generate a baseline showdown lineup optimizing purely for Smart Score or Projection.
        
        For baseline lineups:
        - Selects best captain for the optimization objective
        - Optimizes 5 FLEX positions for the same objective
        - No ownership constraints
        - Pure optimization without diversity penalties
        
        Args:
            opt_players: All available players
            settings: Optimization settings
            lineup_number: Lineup number (-1 for best smart score, -2 for best projection)
            optimize_for: 'smart_score' or 'projection'
        
        Returns:
            GeneratedLineup object or None if failed
        """
        # For baseline lineups, we need to try all feasible captains and pick the one that
        # maximizes total projection/smart_score when combined with optimal FLEX players
        # This is more complex but ensures we get the true maximum
        
        best_lineup_result = None  # Will be set for projection case
        
        if optimize_for == 'smart_score':
            # For smart_score: Select captain based on value (smart_score / salary)
            captain_candidates = []
            
            for player in opt_players:
                captain_salary = int(player.salary * CAPTAIN_MULTIPLIER)
                remaining_salary = SHOWDOWN_SALARY_CAP - captain_salary
                
                # Check if we can fit 5 cheapest FLEX players
                other_players = [p for p in opt_players if p.player_id != player.player_id]
                if len(other_players) < 5:
                    continue
                
                other_players_sorted = sorted(other_players, key=lambda p: p.salary)
                min_flex_cost = sum(p.salary for p in other_players_sorted[:5])
                
                if min_flex_cost > remaining_salary:
                    continue  # This captain is not feasible
                
                # Use smart_score / salary (captain multiplier cancels out)
                captain_value = player.smart_score / player.salary if player.salary > 0 else 0
                captain_candidates.append((player, captain_value))
            
            if not captain_candidates:
                logger.warning(f"Baseline showdown {optimize_for}: No feasible captains found")
                return None
            
            # Select captain with best value
            captain_candidates.sort(key=lambda x: x[1], reverse=True)
            best_captain = captain_candidates[0][0]
            
        else:  # 'projection'
            # For projection: Try all feasible captains, optimize FLEX for each, pick best total
            # This ensures we get the lineup with maximum total projection, not just best value
            best_total_projection = -1
            best_captain = None
            best_lineup_result = None
            
            captain_candidates = []
            for player in opt_players:
                if not player.projection:
                    continue
                    
                captain_salary = int(player.salary * CAPTAIN_MULTIPLIER)
                remaining_salary = SHOWDOWN_SALARY_CAP - captain_salary
                
                # Check if we can fit 5 cheapest FLEX players
                other_players = [p for p in opt_players if p.player_id != player.player_id]
                if len(other_players) < 5:
                    continue
                
                other_players_sorted = sorted(other_players, key=lambda p: p.salary)
                min_flex_cost = sum(p.salary for p in other_players_sorted[:5])
                
                if min_flex_cost > remaining_salary:
                    continue  # This captain is not feasible
                
                captain_candidates.append(player)
            
            if not captain_candidates:
                logger.warning(f"Baseline showdown {optimize_for}: No feasible captains found")
                return None
            
            # Try each feasible captain and optimize FLEX to maximize total projection
            for candidate_captain in captain_candidates:
                # Create temporary problem to test this captain
                test_prob = pulp.LpProblem(f"Test_Projection_Captain_{candidate_captain.player_id}", pulp.LpMaximize)
                
                # Create binary variables for FLEX positions
                flex_vars_test = {}
                for player in opt_players:
                    if player.player_id != candidate_captain.player_id:
                        var_name = f"flex_{player.player_id}"
                        flex_vars_test[player.player_id] = pulp.LpVariable(var_name, cat='Binary')
                
                # Objective: Maximize total projection (captain * 1.5 + sum(FLEX))
                objective_terms_test = [candidate_captain.projection * CAPTAIN_MULTIPLIER]
                for player in opt_players:
                    if player.player_id != candidate_captain.player_id:
                        if player.projection:
                            objective_terms_test.append(
                                player.projection * flex_vars_test[player.player_id]
                            )
                
                test_prob += pulp.lpSum(objective_terms_test)
                
                # Constraint: Exactly 5 FLEX players
                test_prob += pulp.lpSum([flex_vars_test[p.player_id] for p in opt_players if p.player_id != candidate_captain.player_id]) == 5
                
                # Constraint: Total salary <= $50,000
                captain_salary_test = int(candidate_captain.salary * CAPTAIN_MULTIPLIER)
                flex_salary_sum_test = pulp.lpSum([
                    player.salary * flex_vars_test[player.player_id]
                    for player in opt_players if player.player_id != candidate_captain.player_id
                ])
                test_prob += captain_salary_test + flex_salary_sum_test <= SHOWDOWN_SALARY_CAP
                test_prob += captain_salary_test + flex_salary_sum_test >= SHOWDOWN_MIN_SALARY
                
                # Solve
                test_prob.solve(pulp.PULP_CBC_CMD(msg=0))
                
                if test_prob.status == pulp.LpStatusOptimal:
                    # Calculate total projection for this captain
                    test_total_projection = candidate_captain.projection * CAPTAIN_MULTIPLIER
                    for player in opt_players:
                        if player.player_id != candidate_captain.player_id:
                            if flex_vars_test[player.player_id].varValue == 1 and player.projection:
                                test_total_projection += player.projection
                    
                    if test_total_projection > best_total_projection:
                        best_total_projection = test_total_projection
                        best_captain = candidate_captain
                        # Store the optimal flex selection for later use
                        best_lineup_result = {p.player_id: flex_vars_test[p.player_id].varValue 
                                            for p in opt_players if p.player_id != candidate_captain.player_id}
            
            if best_captain is None:
                logger.warning(f"Baseline showdown {optimize_for}: No optimal captain found after testing all candidates")
                return None
            
            # For projection case, we've already solved and found the optimal lineup
            # Use the stored flex_vars from the test problem
            logger.info(
                f"Baseline showdown {optimize_for}: Selected captain {best_captain.name} "
                f"(max_total_projection={best_total_projection:.1f})"
            )
        
        # Log captain selection for smart_score case
        if optimize_for == 'smart_score':
            logger.info(
                f"Baseline showdown {optimize_for}: Selected captain {best_captain.name} "
                f"(value={captain_candidates[0][1]:.4f})"
            )
        
        # For projection case, skip solving again - use results from test problems
        if optimize_for == 'projection' and best_lineup_result is not None:
            # Use the already-solved flex selection
            flex_vars_result = best_lineup_result
        else:
            # For smart_score or if projection test failed, solve normally
            # Create PuLP problem
            prob = pulp.LpProblem(f"Baseline_Showdown_{optimize_for}", pulp.LpMaximize)
            
            # Create binary variables for FLEX positions (exclude captain)
            flex_vars = {}
            for player in opt_players:
                if player.player_id != best_captain.player_id:
                    var_name = f"flex_{player.player_id}"
                    flex_vars[player.player_id] = pulp.LpVariable(var_name, cat='Binary')
            
            # Objective: Maximize (captain objective * 1.5) + sum(FLEX objectives)
            if optimize_for == 'smart_score':
                objective_terms = [best_captain.smart_score * CAPTAIN_MULTIPLIER]
                for player in opt_players:
                    if player.player_id != best_captain.player_id:
                        objective_terms.append(
                            player.smart_score * flex_vars[player.player_id]
                        )
            else:  # 'projection' (fallback case)
                if not best_captain.projection:
                    logger.warning(f"Baseline showdown {optimize_for}: Captain has no projection")
                    return None
                objective_terms = [best_captain.projection * CAPTAIN_MULTIPLIER]
                for player in opt_players:
                    if player.player_id != best_captain.player_id:
                        if player.projection:
                            objective_terms.append(
                                player.projection * flex_vars[player.player_id]
                            )
            
            prob += pulp.lpSum(objective_terms)
            
            # Constraint: Exactly 5 FLEX players
            prob += pulp.lpSum([flex_vars[p.player_id] for p in opt_players if p.player_id != best_captain.player_id]) == 5
            
            # Constraint: Total salary <= $50,000
            captain_salary = int(best_captain.salary * CAPTAIN_MULTIPLIER)
            flex_salary_sum = pulp.lpSum([
                player.salary * flex_vars[player.player_id]
                for player in opt_players if player.player_id != best_captain.player_id
            ])
            prob += captain_salary + flex_salary_sum <= SHOWDOWN_SALARY_CAP
            
            # Constraint: Total salary >= $47,000
            prob += captain_salary + flex_salary_sum >= SHOWDOWN_MIN_SALARY
            
            # No ownership constraints for baseline - pure optimization
            
            # Solve
            prob.solve(pulp.PULP_CBC_CMD(msg=0))
            
            if prob.status != pulp.LpStatusOptimal:
                logger.error(
                    f"Baseline showdown {optimize_for} optimization failed with status: {pulp.LpStatus[prob.status]} "
                    f"(captain={best_captain.name}, players={len(opt_players)})"
                )
                return None
            
            # Extract flex_vars results
            flex_vars_result = {p.player_id: flex_vars[p.player_id].varValue 
                               for p in opt_players if p.player_id != best_captain.player_id}
        
        # Extract selected players
        selected_players = []
        captain_salary = int(best_captain.salary * CAPTAIN_MULTIPLIER)
        total_salary = captain_salary
        
        # Calculate totals based on optimization objective
        if optimize_for == 'smart_score':
            total_smart_score = best_captain.smart_score * CAPTAIN_MULTIPLIER
            total_projection = (best_captain.projection * CAPTAIN_MULTIPLIER) if best_captain.projection else 0
        else:  # 'projection'
            total_projection = best_captain.projection * CAPTAIN_MULTIPLIER
            # Also calculate smart score for display
            total_smart_score = best_captain.smart_score * CAPTAIN_MULTIPLIER
        
        total_ownership = best_captain.ownership or 0.0
        
        # Add captain
        selected_players.append({
            'position': best_captain.position,
            'player_key': best_captain.player_key,
            'name': best_captain.name,
            'team': best_captain.team,
            'salary': best_captain.salary,
            'smart_score': best_captain.smart_score,
            'ownership': best_captain.ownership,
            'projection': best_captain.projection,
            'is_captain': True,
        })
        
        # Add FLEX players using flex_vars_result (works for both cases)
        for player in opt_players:
            if player.player_id != best_captain.player_id:
                # Check if this player was selected (flex_vars_result contains 1.0 for selected, 0.0 or None for not)
                is_selected = flex_vars_result.get(player.player_id, 0) == 1 or flex_vars_result.get(player.player_id, 0) == 1.0
                if is_selected:
                    selected_players.append({
                        'position': player.position,
                        'player_key': player.player_key,
                        'name': player.name,
                        'team': player.team,
                        'salary': player.salary,
                        'smart_score': player.smart_score,
                        'ownership': player.ownership,
                        'projection': player.projection,
                        'is_captain': False,
                    })
                    total_salary += player.salary
                    total_smart_score += player.smart_score
                    if player.projection:
                        total_projection += player.projection
                    total_ownership += player.ownership or 0.0
        
        # Validate lineup
        if len(selected_players) != SHOWDOWN_TOTAL_POSITIONS:
            logger.warning(f"Baseline showdown {optimize_for}: Invalid lineup size {len(selected_players)} (expected {SHOWDOWN_TOTAL_POSITIONS})")
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

    def _generate_main_slate_lineups(
        self,
        week_id: int,
        players: List[PlayerScoreResponse],
        settings: OptimizationSettings,
    ) -> Tuple[List[GeneratedLineup], Optional[Dict[str, int]]]:
        """
        Generate main slate lineups (original 9-position format).

        This is the original lineup generation logic, preserved for main slate mode.
        """
        # Filter players by Smart Score percentile if set
        filtered_players = self._filter_by_percentile(players, settings.exclude_bottom_percentile)

        logger.info(
            f"After Smart Score percentile filtering: {len(filtered_players)} players "
            f"(from {len(players)} total, exclude bottom {settings.exclude_bottom_percentile}%)"
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
        opt_players = self._prepare_players(
            filtered_players,
            strategy_mode=settings.strategy_mode,
        )

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
                f"Position validation failed after Smart Score percentile filtering (exclude bottom {settings.exclude_bottom_percentile}%). "
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

    def _identify_elite_players(
        self,
        players: List[PlayerOptimizationData],
    ) -> Dict[str, List[PlayerOptimizationData]]:
        """
        Identify elite players by position based on Smart Score ranking.

        Uses Smart Score (not projection) to identify elite players based on
        the customized scoring formula weights.

        Identifies top 15 players per position based on Smart Score:
        - These players form the elite pool for appearance constraints
        - Smart Score reflects the user's customized weight preferences

        Args:
            players: List of all available players

        Returns:
            Dict mapping position to list of elite players (sorted by Smart Score, highest first)
        """
        elite_counts = {
            'QB': 15,   # Top 15 QBs by Smart Score
            'RB': 15,   # Top 15 RBs by Smart Score
            'WR': 15,   # Top 15 WRs by Smart Score
            'TE': 15,   # Top 15 TEs by Smart Score
            'DST': 15,  # Top 15 DSTs by Smart Score
        }

        elite_by_position = {}

        for position, count in elite_counts.items():
            # Get all players at this position
            pos_players = [p for p in players if p.position == position]

            # Sort by SMART SCORE (descending) - reflects customized weights
            # Players with null Smart Scores will be sorted to the end (treated as 0)
            pos_players_sorted = sorted(
                pos_players,
                key=lambda p: p.smart_score if p.smart_score is not None else 0,
                reverse=True
            )

            # Take top N players by Smart Score
            elite_players = pos_players_sorted[:count]
            elite_by_position[position] = elite_players

            # Log elite players for debugging
            if elite_players:
                logger.info(f"Elite {position} players (top {count} by Smart Score):")
                for i, player in enumerate(elite_players, 1):
                    ss = player.smart_score if player.smart_score is not None else 0
                    proj = player.projection if player.projection is not None else 0
                    logger.info(f"  #{i}: {player.name} ({player.team}) - SS: {ss:.1f}, Proj: {proj:.1f}")

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

            # Average ownership constraint (per lineup)
            self._add_avg_ownership_constraint(prob, opt_players, lineup_vars, settings, lineup_idx)

        logger.info(f"Applied per-lineup constraints for 10 lineups")

        # Elite appearance constraints - now based on Smart Score ranking with reduced limits
        # Max appearance capped at 5 (half of 10 lineups) for top players
        constraint_metadata = self._add_elite_appearance_constraints(
            prob, player_vars, elite_by_position, opt_players
        )
        logger.info(f"Added {len(constraint_metadata)} elite appearance constraints (Smart Score-based, max 5 appearances)")

        # Solve with elite constraints
        logger.info("Starting portfolio optimization solve...")
        logger.info(f"Problem has {len(prob.constraints)} total constraints")
        start_solve_time = time.time()
        # Enable solver messages temporarily for debugging (msg=1)
        prob.solve(pulp.PULP_CBC_CMD(msg=1, timeLimit=300))  # 5 minute timeout
        solve_duration = time.time() - start_solve_time
        logger.info(f"Portfolio optimization solve completed in {solve_duration:.2f} seconds with status: {pulp.LpStatus[prob.status]}")

        # Performance logging (Task 15.5)
        logger.info(f"[PERFORMANCE] Portfolio optimization: {solve_duration:.2f}s")

        if prob.status != pulp.LpStatusOptimal:
            logger.warning(f"Portfolio optimization failed with status: {pulp.LpStatus[prob.status]}")
            return None

        # Extract lineups from solution
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
                    total_ownership += player.ownership or 0.0

            if not selected_players:
                logger.warning(f"Lineup {lineup_idx + 1} has no players")
                continue

            avg_ownership = total_ownership / len(selected_players) if selected_players else 0.0
            if avg_ownership > 1.0:
                avg_ownership = avg_ownership / 100.0

            lineups.append(GeneratedLineup(
                lineup_number=lineup_idx + 1,
                players=selected_players,
                total_salary=total_salary,
                projected_score=total_smart_score,
                projected_points=total_projection,
                avg_ownership=avg_ownership,
            ))

        logger.info(f"Generated {len(lineups)} lineups with Smart Score-based elite constraints")
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

    def _filter_by_percentile(
        self,
        players: List[PlayerScoreResponse],
        exclude_bottom_percentile: Optional[float]
    ) -> List[PlayerScoreResponse]:
        """
        Filter players by Smart Score percentile.

        Excludes bottom X% of players based on their Smart Score ranking.
        This adapts to the actual score distribution, unlike a fixed threshold.

        Args:
            players: List of players with Smart Scores
            exclude_bottom_percentile: Percentile to exclude (0-100). 0 = no filtering.

        Returns:
            Filtered list of players
        """
        if exclude_bottom_percentile is None or exclude_bottom_percentile <= 0:
            return players

        # Filter out players with no Smart Score first
        players_with_scores = [p for p in players if p.smart_score is not None]
        if len(players_with_scores) == 0:
            logger.warning("No players with Smart Scores to filter")
            return players

        # Sort by Smart Score (descending)
        sorted_players = sorted(players_with_scores, key=lambda p: p.smart_score or 0, reverse=True)

        # Calculate how many players to exclude from bottom
        total_count = len(sorted_players)
        exclude_count = int(total_count * (exclude_bottom_percentile / 100))

        # Take top (100 - exclude_bottom_percentile)%
        if exclude_count >= total_count:
            logger.warning(f"Exclude percentile ({exclude_bottom_percentile}%) would exclude all players, filtering none")
            return players

        filtered = sorted_players[:-exclude_count] if exclude_count > 0 else sorted_players

        # Log score distribution info
        if len(filtered) > 0:
            min_score = min(p.smart_score for p in filtered if p.smart_score is not None)
            max_score = max(p.smart_score for p in filtered if p.smart_score is not None)
            logger.info(
                f"Filtered {len(players)} players to {len(filtered)} "
                f"(excluded bottom {exclude_bottom_percentile}%, "
                f"score range: {min_score:.2f} - {max_score:.2f})"
            )

        return filtered

    def _prepare_players(
        self,
        players: List[PlayerScoreResponse],
        strategy_mode: str = 'Balanced',
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
            
            # Note: $100 minimum salary players are allowed (no minimum threshold filter)
            # Only null/zero salaries are filtered out to allow Showdown mode low-priced players

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
        """
        Get game information for stacking constraints.

        Performance optimization (Task 15.3):
        - Uses composite index on (week_id, team) for efficient queries
        """
        # Query vegas_lines to get opponent info
        # This query benefits from composite index created in Task 1.2
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

        # Average ownership constraint
        self._add_avg_ownership_constraint(prob, opt_players, player_vars, settings)

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

    def _add_avg_ownership_constraint(
        self,
        prob: pulp.LpProblem,
        players: List[PlayerOptimizationData],
        player_vars: Dict[int, pulp.LpVariable],
        settings: OptimizationSettings,
        lineup_idx: Optional[int] = None,
    ):
        """
        Add constraint limiting average ownership of the lineup.

        Constraint: sum(ownership[i] * player_vars[i]) / 9 <= max_ownership
        Rewritten as: sum(ownership[i] * player_vars[i]) <= max_ownership * 9

        This ensures the overall lineup average ownership is below the threshold.
        Ownership values are normalized to 0-1 format before applying constraint.
        """
        if settings.max_ownership is None or settings.max_ownership <= 0:
            return

        suffix = f"_lineup_{lineup_idx}" if lineup_idx is not None else ""

        # Calculate sum of ownership for selected players
        # Normalize ownership to 0-1 format if needed (ownership might be stored as 0-100)
        ownership_sum = pulp.lpSum([
            self._normalize_ownership(player.ownership or 0.0) * player_vars[player.player_id]
            for player in players
        ])

        # Constraint: average ownership <= max_ownership
        # Since we have exactly 9 players: sum(ownership) / 9 <= max_ownership
        # Rewritten as: sum(ownership) <= max_ownership * 9
        max_total_ownership = settings.max_ownership * TOTAL_POSITIONS
        prob += ownership_sum <= max_total_ownership, f"avg_ownership{suffix}"

        logger.debug(
            f"Added avg ownership constraint: sum <= {max_total_ownership:.3f} "
            f"(max avg: {settings.max_ownership * 100:.1f}%)"
        )

    def _normalize_ownership(self, ownership: float) -> float:
        """
        Normalize ownership value to 0-1 format.

        Handles both formats:
        - 0-1 format (decimal): returns as-is
        - 0-100 format (percentage): divides by 100
        """
        if ownership > 1.0:
            return ownership / 100.0
        return ownership

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

        # Average ownership constraint (if set)
        self._add_avg_ownership_constraint(prob, opt_players, player_vars, settings)

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
