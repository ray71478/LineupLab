"""
Lineup Optimizer Service for generating optimal DraftKings lineups.

Uses PuLP linear programming to solve constrained optimization problem:
- Maximize Smart Score across lineups
- Enforce DraftKings constraints (positions, salary cap)
- Apply user settings (strategy mode, exposure limits, stacking rules)
- Generate diverse lineups (minimize overlap)
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
POSITION_REQUIREMENTS = {
    'QB': 1,
    'RB': 2,
    'WR': 3,
    'TE': 1,
    'FLEX': 1,  # RB/WR/TE
    'DST': 1,
}
TOTAL_POSITIONS = sum(POSITION_REQUIREMENTS.values())  # 9


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
        Identify elite players by position based on Milly Winner research.
        
        CRITICAL: Uses SMART SCORE (not projection) to identify elite players.
        This allows us to tune W1-W8 weights to surface the right players.
        
        Research shows winners heavily favor top-finishing players:
        - QB: Top 3 in 6/8 lineups (75%)
        - RB: Top 5 account for 76% of slots, #1 RB in EVERY winner
        - WR: Top 5 account for 77% of slots
        - TE: Top 5 in every lineup but 1
        - DST: Top 3 in 6/8 lineups (75%)
        
        Returns:
            Dict mapping position to list of elite players (sorted by Smart Score)
        """
        elite_counts = {
            'QB': 3,   # Top 3 QBs by Smart Score
            'RB': 5,   # Top 5 RBs by Smart Score (emphasis on #1)
            'WR': 5,   # Top 5 WRs by Smart Score
            'TE': 5,   # Top 5 TEs by Smart Score
            'DST': 3,  # Top 3 DSTs by Smart Score
        }
        
        elite_by_position = {}
        
        for position, count in elite_counts.items():
            # Get all players at this position
            pos_players = [p for p in players if p.position == position]
            
            # Sort by SMART SCORE (descending) - this is what we tune via W1-W8
            # This ensures our weight adjustments directly influence elite identification
            pos_players_sorted = sorted(
                pos_players,
                key=lambda p: p.smart_score,
                reverse=True
            )
            
            # Take top N players by Smart Score
            elite_players = pos_players_sorted[:count]
            elite_by_position[position] = elite_players
            
            # Log elite players for debugging
            if elite_players:
                logger.info(f"Elite {position} players (top {count} by Smart Score):")
                for i, player in enumerate(elite_players, 1):
                    proj = player.projection if player.projection is not None else 0
                    logger.info(f"  #{i}: {player.name} ({player.team}) - SS: {player.smart_score:.1f}, Proj: {proj:.1f}")
        
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
        
        Then generates N user-requested lineups with diversity constraints.
        
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
        
        # Identify elite players for reduced diversity penalties and bonuses
        logger.info("=" * 80)
        logger.info("IDENTIFYING ELITE PLAYERS (based on Milly Winner research)")
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
        
        # NOW: Generate each user-requested lineup iteratively with diversity penalty
        # Try to generate as many as possible, even if some fail
        consecutive_failures = 0
        max_consecutive_failures = 3  # Stop after 3 consecutive failures
        
        for lineup_num in range(1, settings.num_lineups + 1):
            try:
                lineup = self._generate_single_lineup(
                    opt_players=opt_players,
                    players_by_position=players_by_position,
                    players_by_team=players_by_team,
                    game_info=game_info,
                    settings=settings,
                    previous_lineups=generated_lineups,
                    lineup_number=lineup_num,
                    elite_by_position=elite_by_position,
                )
                
                if lineup:
                    generated_lineups.append(lineup)
                    consecutive_failures = 0  # Reset failure counter
                    logger.info(f"Successfully generated lineup {lineup_num}/{settings.num_lineups}")
                else:
                    consecutive_failures += 1
                    logger.warning(
                        f"Failed to generate lineup {lineup_num} - optimization may be infeasible "
                        f"({consecutive_failures} consecutive failures)"
                    )
                    
                    # If we can't generate even the first lineup, log detailed info
                    if lineup_num == 1:
                        logger.error(
                            f"Could not generate first lineup. "
                            f"Position counts: {position_counts}, "
                            f"Total players: {len(opt_players)}, "
                            f"Settings: {settings}"
                        )
                        # Still return position counts for error message, but try to generate more
                    
                    # Stop if too many consecutive failures
                    if consecutive_failures >= max_consecutive_failures:
                        logger.warning(
                            f"Stopping after {consecutive_failures} consecutive failures. "
                            f"Generated {len(generated_lineups)} lineups out of {settings.num_lineups} requested."
                        )
                        break
                    
                    # Continue trying more lineups even after a failure
                    
            except Exception as e:
                consecutive_failures += 1
                logger.error(f"Error generating lineup {lineup_num}: {e}", exc_info=True)
                if lineup_num == 1:
                    logger.error(
                        f"Exception on first lineup. "
                        f"Position counts: {position_counts}, "
                        f"Total players: {len(opt_players)}"
                    )
                
                # Stop if too many consecutive failures
                if consecutive_failures >= max_consecutive_failures:
                    logger.warning(
                        f"Stopping after {consecutive_failures} consecutive failures. "
                        f"Generated {len(generated_lineups)} lineups out of {settings.num_lineups} requested."
                    )
                    break
        
        # Return whatever we successfully generated, along with position counts if empty
        if generated_lineups:
            baseline_count = sum(1 for l in generated_lineups if l.lineup_number < 0)
            regular_count = sum(1 for l in generated_lineups if l.lineup_number > 0)
            logger.info(f"Successfully generated {len(generated_lineups)} lineups ({baseline_count} baselines + {regular_count} user-requested)")
            
            # Sort lineups: baselines first (negative numbers), then regular lineups by Smart Score (highest first)
            # This shows the best lineups first, making it easy to identify top performers
            generated_lineups.sort(key=lambda x: (
                x.lineup_number >= 0,  # Baselines first (False sorts before True)
                -x.projected_score if x.lineup_number >= 0 else abs(x.lineup_number)  # Regular lineups by Smart Score DESC, baselines by number
            ))
            
            return generated_lineups, None
        else:
            # No lineups generated - return position counts for error message
            return [], position_counts
    
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
            # NOTE: These are VERY SOFT filters - only filter obviously bad players
            # The optimization bonuses will handle the preference for ITT > 18.5 and ownership < 20%
            # We don't want to filter out players if it would make lineups impossible
            if strategy_mode == 'Tournament':
                # Ownership conversion: Handle both decimal (0-1) and percentage (0-100) formats
                ownership_raw = player.ownership or 0.0
                if ownership_raw > 1.0:
                    # Already a percentage (0-100), use as-is
                    ownership_pct = ownership_raw
                else:
                    # Decimal format (0-1), convert to percentage
                    ownership_pct = ownership_raw * 100.0
                
                # Very soft ITT filter: Only filter if ITT is extremely low (< 12) to avoid obviously bad teams
                # Allow null ITT values through (they'll be penalized in optimization but not excluded)
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
                
                # Very soft ownership filter: Only filter if ownership is extremely high (> 50%) to avoid obvious chalk
                # RB chalk is always OK
                # Allow null/zero ownership through (they'll be preferred in optimization)
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
            
            # Detailed breakdown of tournament filters
            if skipped_tournament_filter > 0:
                logger.warning(f"TOURNAMENT FILTER BREAKDOWN:")
                logger.warning(f"  Filtered by ITT < 12: {len(filtered_by_itt)} players")
                logger.warning(f"  Filtered by Ownership >= 50% (non-RB): {len(filtered_by_ownership)} players")
                
                # Group by position
                by_position = {}
                for p in filtered_by_itt + filtered_by_ownership:
                    pos = p['position']
                    if pos not in by_position:
                        by_position[pos] = []
                    by_position[pos].append(p)
                
                for position, players in by_position.items():
                    logger.warning(f"  {position} filtered: {len(players)} players")
                    # Show first 5 examples
                    for p in players[:5]:
                        logger.warning(
                            f"    - {p['name']} ({p['team']}): "
                            f"ITT={p['itt']}, Own={p['ownership']:.1f}%, Score={p['smart_score']:.1f}"
                        )
                    if len(players) > 5:
                        logger.warning(f"    ... and {len(players) - 5} more")

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
        
        This is the core optimization logic that sets up constraints and solves.
        """
        # Create PuLP problem
        prob = pulp.LpProblem(f"Lineup_{lineup_number}", pulp.LpMaximize)
        
        # Create decision variables: 1 if player is selected, 0 otherwise
        player_vars = {}
        for player in opt_players:
            var_name = f"player_{player.player_id}"
            player_vars[player.player_id] = pulp.LpVariable(var_name, cat='Binary')
        
        # Objective: Maximize Smart Score + bonus for using salary cap efficiently
        # Primary: Smart Score (dominant factor)
        # Calculate elite player bonuses FIRST
        elite_player_ids = self._get_elite_player_ids(elite_by_position)
        elite_bonuses = {}
        for position, elite_players in elite_by_position.items():
            bonus_structures = {
                'RB': [500.0, 400.0, 300.0, 200.0, 100.0],
                'WR': [500.0, 400.0, 300.0, 200.0, 100.0],
                'TE': [500.0, 400.0, 300.0, 200.0, 100.0],
                'QB': [500.0, 400.0, 300.0],
                'DST': [500.0, 400.0, 300.0],
            }
            bonuses = bonus_structures.get(position, [])
            for i, player in enumerate(elite_players):
                if i < len(bonuses):
                    elite_bonuses[player.player_id] = bonuses[i]
                    logger.info(
                        f"Elite bonus: {player.name} ({position} #{i+1}) gets +{bonuses[i]:.1f} points"
                    )
        
        # Objective: Maximize Smart Score + Elite Bonuses + Salary Bonus
        # Build complete objective function in ONE statement
        salary_sum = pulp.lpSum([
            player.salary * player_vars[player.player_id]
            for player in opt_players
        ])
        
        MIN_SALARY = SALARY_CAP - 1000  # $49,000 minimum
        salary_bonus_multiplier = 0.05
        
        # SINGLE objective function with ALL components
        # Log the actual coefficients being used for elite players
        for player in opt_players:
            bonus = elite_bonuses.get(player.player_id, 0)
            if bonus > 0:
                total_coefficient = player.smart_score + bonus + (player.salary / 1000) * 0.6
                logger.info(
                    f"OBJECTIVE COEFFICIENT: {player.name} = {player.smart_score:.1f} (SS) + {bonus:.1f} (elite) + {(player.salary / 1000) * 0.6:.1f} (salary) = {total_coefficient:.1f} total"
                )
        
        prob += pulp.lpSum([
            # Base Smart Score
            player.smart_score * player_vars[player.player_id]
            # Elite player bonus (if applicable)
            + elite_bonuses.get(player.player_id, 0) * player_vars[player.player_id]
            # Salary bonus
            + (player.salary / 1000) * 0.6 * player_vars[player.player_id]
            for player in opt_players
        ]) + (salary_sum - MIN_SALARY) * salary_bonus_multiplier
        
        # Apply strategy mode adjustments
        self._apply_strategy_mode(prob, opt_players, player_vars, settings.strategy_mode)
        
        # CRITICAL: Apply elite bonuses AFTER strategy mode to ensure they override any penalties
        # Elite players should appear frequently regardless of ownership or other strategy adjustments
        for player_id, bonus in elite_bonuses.items():
            prob += player_vars[player_id] * bonus
            logger.info(f"FINAL elite bonus applied: player_id={player_id}, bonus={bonus}")
        
        # Position constraints
        self._add_position_constraints(prob, players_by_position, player_vars, settings)
        
        # Salary cap constraint: Must be within $1K of $50K budget (at least $49K, at most $50K)
        prob += salary_sum >= MIN_SALARY  # At least $49K (increased from $48K)
        prob += salary_sum <= SALARY_CAP  # At most $50K
        
        # Team limit constraint
        self._add_team_constraints(prob, players_by_team, player_vars, settings)
        
        # Game limit constraint
        self._add_game_constraints(prob, opt_players, game_info, player_vars, settings)
        
        # Exposure limits
        self._add_exposure_constraints(prob, opt_players, player_vars, settings, previous_lineups)
        
        # Stacking rules
        self._add_stacking_constraints(prob, opt_players, game_info, player_vars, settings)
        
        # Snap count adjustments (boost 28+ snap players, penalize low-snap players except elite)
        # Note: elite_player_ids already calculated above when building objective function
        self._add_snap_count_adjustments(prob, opt_players, player_vars, elite_player_ids)
        
        # Diversity penalty (minimize overlap with previous lineups)
        # Elite players get 75% reduced penalties
        if previous_lineups:
            self._add_diversity_penalty(prob, opt_players, player_vars, previous_lineups, elite_player_ids)
        
        # Solve
        # TEMPORARILY ENABLE VERBOSE OUTPUT FOR DEBUGGING
        solver = pulp.PULP_CBC_CMD(msg=1)  # Verbose mode - will show constraint details
        prob.solve(solver)

        # Log detailed problem info for first lineup
        if lineup_number == 1:
            logger.info(f"=== LINEUP OPTIMIZER DEBUG INFO ===")
            logger.info(f"Total players in optimization: {len(opt_players)}")
            logger.info(f"Total constraints: {len(prob.constraints)}")
            logger.info(f"Solver status: {prob.status} ({pulp.LpStatus[prob.status]})")

            # Log sample players
            logger.info("Sample players (first 5 by position):")
            sample_by_pos = {}
            for p in opt_players[:20]:
                if p.position not in sample_by_pos:
                    sample_by_pos[p.position] = []
                if len(sample_by_pos[p.position]) < 3:
                    sample_by_pos[p.position].append(
                        f"{p.name} ({p.team}) ${p.salary} score:{p.smart_score:.1f}"
                    )
            for pos, players in sample_by_pos.items():
                for player_str in players:
                    logger.info(f"  {pos}: {player_str}")

        if prob.status != pulp.LpStatusOptimal:
            # Log detailed constraint info for debugging
            logger.warning(
                f"Optimization failed with status: {prob.status}. "
                f"Position counts: {dict((pos, len(players)) for pos, players in players_by_position.items())}, "
                f"Total players: {len(opt_players)}, "
                f"Settings: max_team={settings.max_players_per_team}, max_game={settings.max_players_per_game}, "
                f"QB+WR stack={settings.stacking_rules.qb_wr_stack_enabled if settings.stacking_rules else False}, "
                f"Bring-back={settings.stacking_rules.bring_back_enabled if settings.stacking_rules else False}"
            )
            
            # Try to identify which constraint might be causing issues
            if settings.stacking_rules:
                if settings.stacking_rules.qb_wr_stack_enabled:
                    qb_players = [p for p in opt_players if p.position == 'QB']
                    wr_players = [p for p in opt_players if p.position == 'WR']
                    qb_teams_with_wrs = {}
                    for qb in qb_players:
                        team_wrs = [wr for wr in wr_players if wr.team == qb.team]
                        qb_teams_with_wrs[qb.team] = len(team_wrs)
                    logger.warning(f"QB+WR stack check - QBs with WRs from same team: {qb_teams_with_wrs}")
                
                if settings.stacking_rules.bring_back_enabled:
                    logger.warning(f"Bring-back enabled - game_info has {len(game_info)} teams")
            
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
                total_projection += player.projection
                total_ownership += player.ownership
        
        # Validate lineup
        if not self._validate_lineup(selected_players, total_salary):
            logger.warning(f"Generated invalid lineup {lineup_number}")
            return None
        
        avg_ownership = total_ownership / len(selected_players) if selected_players else 0.0

        # Convert ownership from percentage (0-100) to decimal (0-1) if needed
        if avg_ownership > 1.0:
            avg_ownership = avg_ownership / 100.0

        logger.info(f"Lineup {lineup_number}: {len(selected_players)} players, salary=${total_salary}, score={total_smart_score:.1f}, proj={total_projection:.1f}, avg_own={avg_ownership:.3f}")

        try:
            return GeneratedLineup(
                lineup_number=lineup_number,
                players=selected_players,
                total_salary=total_salary,
                projected_score=total_smart_score,
                projected_points=total_projection,
                avg_ownership=avg_ownership,
            )
        except Exception as e:
            logger.error(f"Pydantic validation error creating GeneratedLineup: {e}")
            logger.error(f"  lineup_number={lineup_number}, players={len(selected_players)}, total_salary={total_salary}, projected_score={total_smart_score}, projected_points={total_projection}, avg_ownership={avg_ownership}")
            raise
    
    def _apply_strategy_mode(
        self,
        prob: pulp.LpProblem,
        players: List[PlayerOptimizationData],
        player_vars: Dict[int, pulp.LpVariable],
        strategy_mode: str,
    ):
        """
        Apply strategy mode adjustments to objective function.
        
        Different strategies optimize for different goals:
        - Balanced: Pure Smart Score optimization
        - Chalk: Favor high-ownership players (safer, tournament-winning upside)
        - Contrarian: Favor low-ownership players (differentiation, GPP strategy)
        """
        if strategy_mode == 'Chalk':
            # Boost high ownership players - they're popular for a reason
            # Add bonus to objective for players with high ownership
            for player in players:
                if player.ownership > 0.15:  # Above 15% ownership
                    # Bonus increases with ownership
                    ownership_bonus = player.ownership * 2.0  # 2 points per 1% ownership
                    prob += player_vars[player.player_id] * ownership_bonus
                    
        elif strategy_mode == 'Contrarian':
            # Penalize high ownership players to create unique lineups
            # This is valuable in GPPs where you need differentiation to win
            for player in players:
                if player.ownership > 0.10:  # Above 10% ownership
                    # Penalty increases exponentially with ownership
                    ownership_penalty = (player.ownership ** 1.5) * -150
                    prob += player_vars[player.player_id] * ownership_penalty
                    
            # Also boost low-ownership players
            for player in players:
                if player.ownership < 0.05:  # Below 5% ownership
                    # Bonus for low-owned players
                    contrarian_bonus = (0.05 - player.ownership) * 50
                    prob += player_vars[player.player_id] * contrarian_bonus
                    
        elif strategy_mode == 'Tournament':
            # Tournament mode: Optimize for ceiling + ownership leverage
            # Based on research: 47% of winners scored above CEILING
            # Only 28% of winners were owned 20%+ (mostly RBs)
            # Target: High Smart Score with low ownership (except RB)
            
            for player in players:
                # Handle ownership format (decimal 0-1 or percentage 0-100)
                ownership_raw = player.ownership or 0.0
                if ownership_raw > 1.0:
                    ownership_pct = ownership_raw  # Already percentage
                    ownership_decimal = ownership_raw / 100.0  # Convert to decimal for calculations
                else:
                    ownership_pct = ownership_raw * 100.0  # Convert to percentage
                    ownership_decimal = ownership_raw  # Already decimal
                
                # RB chalk is OK - don't penalize high-owned RBs
                if player.position == 'RB':
                    # RBs can be chalk - just optimize Smart Score
                    continue
                
                # For non-RBs: optimize for ownership leverage
                # Leverage = Smart Score / Ownership (higher is better)
                if ownership_decimal > 0.01:  # Avoid division by zero
                    leverage_score = player.smart_score / ownership_decimal
                    # Boost players with high leverage (high Smart Score, low ownership)
                    leverage_bonus = leverage_score * 0.5  # 0.5 bonus per leverage point
                    prob += player_vars[player.player_id] * leverage_bonus
                
                # Penalize high-owned non-RBs (without ceiling upside)
                # Research shows only 28% of winners owned 20%+, and most were RBs
                if ownership_pct >= 20.0:
                    ownership_penalty = (ownership_pct - 20.0) * -2.0  # -2 per % above 20%
                    prob += player_vars[player.player_id] * ownership_penalty
                    
        # Balanced: No additional adjustments - pure Smart Score optimization
    
    def _add_position_constraints(
        self,
        prob: pulp.LpProblem,
        players_by_position: Dict[str, List[PlayerOptimizationData]],
        player_vars: Dict[int, pulp.LpVariable],
        settings: OptimizationSettings,
    ):
        """Add position requirement constraints."""
        # QB: Exactly 1
        qb_players = players_by_position.get('QB', [])
        if qb_players:
            prob += pulp.lpSum([player_vars[p.player_id] for p in qb_players]) == 1
        
        # RB: At least 2, but FLEX can be RB so total RB/WR/TE = 7 (2 RB + 3 WR + 1 TE + 1 FLEX)
        rb_players = players_by_position.get('RB', [])
        wr_players = players_by_position.get('WR', [])
        te_players = players_by_position.get('TE', [])
        flex_players = rb_players + wr_players + te_players
        
        # RB: At least 2
        if rb_players:
            prob += pulp.lpSum([player_vars[p.player_id] for p in rb_players]) >= 2
        
        # WR: At least 3
        if wr_players:
            prob += pulp.lpSum([player_vars[p.player_id] for p in wr_players]) >= 3
        
        # TE: At least 1
        if te_players:
            prob += pulp.lpSum([player_vars[p.player_id] for p in te_players]) >= 1
        
        # Total RB/WR/TE/FLEX: Exactly 7 (2 RB + 3 WR + 1 TE + 1 FLEX)
        if flex_players:
            prob += pulp.lpSum([player_vars[p.player_id] for p in flex_players]) == 7
        
        # DST: Exactly 1
        dst_players = players_by_position.get('DST', [])
        if dst_players:
            prob += pulp.lpSum([player_vars[p.player_id] for p in dst_players]) == 1
        
        # Total: 9 players (1 QB + 7 RB/WR/TE/FLEX + 1 DST)
        all_players = sum(players_by_position.values(), [])
        prob += pulp.lpSum([player_vars[p.player_id] for p in all_players]) == TOTAL_POSITIONS
    
    def _add_team_constraints(
        self,
        prob: pulp.LpProblem,
        players_by_team: Dict[str, List[PlayerOptimizationData]],
        player_vars: Dict[int, pulp.LpVariable],
        settings: OptimizationSettings,
    ):
        """Add max players per team constraint."""
        max_team = settings.max_players_per_team
        
        for team, team_players in players_by_team.items():
            if team_players:
                prob += pulp.lpSum([player_vars[p.player_id] for p in team_players]) <= max_team
    
    def _add_game_constraints(
        self,
        prob: pulp.LpProblem,
        players: List[PlayerOptimizationData],
        game_info: Dict[str, Dict],
        player_vars: Dict[int, pulp.LpVariable],
        settings: OptimizationSettings,
    ):
        """Add max players per game constraint."""
        max_game = settings.max_players_per_game
        
        # Group players by game
        games: Dict[str, List[PlayerOptimizationData]] = defaultdict(list)
        
        for player in players:
            opponent = game_info.get(player.team, {}).get('opponent')
            if opponent:
                # Create game key (alphabetically sorted teams)
                game_key = tuple(sorted([player.team, opponent]))
                games[game_key].append(player)
        
        for game_players in games.values():
            if len(game_players) > max_game:
                prob += pulp.lpSum([player_vars[p.player_id] for p in game_players]) <= max_game
    
    def _add_exposure_constraints(
        self,
        prob: pulp.LpProblem,
        players: List[PlayerOptimizationData],
        player_vars: Dict[int, pulp.LpVariable],
        settings: OptimizationSettings,
        previous_lineups: List[GeneratedLineup],
    ):
        """Add player exposure limit constraints."""
        if not settings.player_exposure_limits:
            return
        
        # Count current exposure
        exposure_count: Dict[int, int] = defaultdict(int)
        
        for lineup in previous_lineups:
            for player_data in lineup.players:
                # Find player_id from player_key
                for player in players:
                    if player.player_key == player_data['player_key']:
                        exposure_count[player.player_id] += 1
                        break
        
        # Apply min/max constraints
        for player_key, limits in settings.player_exposure_limits.items():
            for player in players:
                if player.player_key == player_key:
                    current_exposure = exposure_count[player.player_id]
                    
                    # Min constraint: must appear in at least X lineups
                    if limits.min is not None and current_exposure < limits.min:
                        # This is a soft constraint - we'll enforce it as we can
                        pass
                    
                    # Max constraint: cannot appear in more than X lineups
                    if limits.max is not None:
                        max_allowed = limits.max - current_exposure
                        if max_allowed <= 0:
                            # Already at max, force exclusion
                            prob += player_vars[player.player_id] == 0
                        elif max_allowed < len(previous_lineups) + 1:
                            # Limit remaining appearances
                            prob += player_vars[player.player_id] <= max_allowed
    
    def _add_stacking_constraints(
        self,
        prob: pulp.LpProblem,
        players: List[PlayerOptimizationData],
        game_info: Dict[str, Dict],
        player_vars: Dict[int, pulp.LpVariable],
        settings: OptimizationSettings,
    ):
        """Add stacking rule constraints."""
        if not settings.stacking_rules:
            return
        
        # QB + WR/TE stack rule (FLEXIBLE)
        # If stacking enabled, require QB to stack with AT LEAST ONE pass catcher (WR or TE)
        # This allows QB+WR, QB+TE, or QB+WR+TE combinations
        if settings.stacking_rules.qb_wr_stack_enabled:
            qb_players = [p for p in players if p.position == 'QB']
            wr_players = [p for p in players if p.position == 'WR']
            te_players = [p for p in players if p.position == 'TE']
            
            # For each QB, ensure at least one pass catcher (WR or TE) from same team
            for qb in qb_players:
                qb_team_wrs = [wr for wr in wr_players if wr.team == qb.team]
                qb_team_tes = [te for te in te_players if te.team == qb.team]
                qb_team_pass_catchers = qb_team_wrs + qb_team_tes
                
                if qb_team_pass_catchers:
                    # If QB selected, at least one pass catcher (WR or TE) from same team must be selected
                    # This is more flexible than requiring specifically a WR
                    prob += pulp.lpSum([
                        player_vars[pc.player_id] for pc in qb_team_pass_catchers
                    ]) >= player_vars[qb.player_id]
                else:
                    # No pass catchers from same team available
                    logger.warning(
                        f"QB+pass catcher stack enabled but no WRs/TEs from {qb.team} available for QB {qb.name}. "
                        f"Skipping stack constraint for this QB to avoid infeasibility."
                    )
        
        # Bring-back constraint (opponent team player)
        # TEMPORARILY DISABLED - This constraint is making the problem infeasible
        # TODO: Fix bring-back logic to be less restrictive
        if False and settings.stacking_rules.bring_back_enabled:
            pass  # Disabled for now
            # Group players by their game (team + opponent)
            games: Dict[tuple, List[PlayerOptimizationData]] = defaultdict(list)
            
            for player in players:
                opponent = game_info.get(player.team, {}).get('opponent')
                if opponent:
                    # Create game key (alphabetically sorted teams)
                    game_key = tuple(sorted([player.team, opponent]))
                    games[game_key].append(player)
            
            if not games:
                logger.warning(
                    "Bring-back enabled but no opponent data available in game_info. "
                    "Skipping bring-back constraint to avoid infeasibility."
                )
                return
            
            logger.info(f"Applying bring-back constraint to {len(games)} games")
            
            # Simplified bring-back: If you select players from a game, you must have at least one from each team
            # This is less restrictive than requiring it for every game
            # Instead, we'll use a simpler approach: if any player from a game is selected, 
            # ensure at least one from each team
            for (team_a, team_b), game_players in games.items():
                team_a_players = [p for p in game_players if p.team == team_a]
                team_b_players = [p for p in game_players if p.team == team_b]
                
                if not team_a_players or not team_b_players:
                    # Skip if we don't have players from both teams
                    continue
                
                # Count total players selected from this game
                game_total = pulp.lpSum([player_vars[p.player_id] for p in game_players])
                
                # If any players are selected from this game, ensure at least one from each team
                # Simplified: if game_total >= 1, then team_a_selected >= 1 AND team_b_selected >= 1
                # We'll use a binary indicator
                has_game_players = pulp.LpVariable(f"has_game_{team_a}_{team_b}", cat='Binary')
                team_a_selected = pulp.lpSum([player_vars[p.player_id] for p in team_a_players])
                team_b_selected = pulp.lpSum([player_vars[p.player_id] for p in team_b_players])
                
                # If game_total >= 1, then has_game_players = 1
                max_game_players = len(game_players)
                prob += game_total <= max_game_players * has_game_players
                prob += has_game_players <= game_total
                
                # If has_game_players = 1, then both teams must have at least 1
                prob += team_a_selected >= has_game_players
                prob += team_b_selected >= has_game_players
    
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
        
        Args:
            lineup_number: -1 for Smart Score baseline, -2 for Projection baseline
            optimize_for: 'smart_score' or 'projection'
        """
        prob = pulp.LpProblem(f"Baseline_{optimize_for}", pulp.LpMaximize)
        
        # Create binary variables for each player
        player_vars = {}
        for player in opt_players:
            var_name = f"player_{player.player_id}"
            player_vars[player.player_id] = pulp.LpVariable(var_name, cat='Binary')
        
        # Objective: Maximize Smart Score OR Projection ONLY (pure optimization)
        # No salary bonus - we want to see the absolute best possible Smart Score or Projection
        # The salary constraint ($48K-$50K) ensures budget usage without affecting optimization
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
        
        # Position constraints (required for valid DraftKings lineups)
        self._add_position_constraints(prob, players_by_position, player_vars, settings)
        
        # Salary constraint: Must be within $2K of $50K budget (at least $48K, at most $50K)
        salary_cap = 50000
        min_salary = salary_cap - 2000  # $48,000 minimum
        salary_sum = pulp.lpSum([
            player.salary * player_vars[player.player_id]
            for player in opt_players
        ])
        prob += salary_sum >= min_salary  # At least $48K
        prob += salary_sum <= salary_cap  # At most $50K
        
        # NO team constraints for baselines (completely unconstrained)
        # NO game constraints for baselines (completely unconstrained)
        # NO stacking rules for baselines (completely unconstrained)
        # NO diversity penalties for baselines (completely unconstrained)
        
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
        total_projection = sum(p.projection for p in selected_players)
        avg_ownership = sum(p.ownership for p in selected_players) / len(selected_players)
        
        # Convert ownership from percentage (0-100) to decimal (0-1) if needed
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
        
        # Create lineup with special lineup_number
        lineup = GeneratedLineup(
            lineup_number=lineup_number,  # -1 or -2 for baselines
            players=player_dicts,
            total_salary=total_salary,
            projected_score=total_smart_score,
            projected_points=total_projection,
            avg_ownership=avg_ownership,
        )
        
        return lineup
    
    def _add_elite_player_bonuses(
        self,
        prob: pulp.LpProblem,
        players: List[PlayerOptimizationData],
        player_vars: Dict[int, pulp.LpVariable],
        elite_by_position: Dict[str, List[PlayerOptimizationData]],
    ):
        """
        Add bonuses for elite players to counteract diversity penalties.
        
        Based on Milly Winner research showing top players dominate winning lineups:
        - RB #1 appears in EVERY winner → biggest bonus (2.0 points)
        - Top 3-5 at each position appear 75-77% of the time → scaled bonuses
        
        This ensures elite players (by Smart Score) overcome diversity penalties
        and appear frequently in generated lineups.
        """
        # Position-specific bonus structures based on research
        # SIGNIFICANTLY INCREASED to overcome diversity penalties and constraints
        # These bonuses need to be large enough to make elite players appear 5-10 times
        bonus_structures = {
            'RB': [10.0, 7.0, 5.0, 3.0, 2.0],  # Top 5 RBs, #1 gets 10.0 (appears in every winner)
            'WR': [8.0, 6.0, 5.0, 3.0, 2.0],   # Top 5 WRs, #1 gets 8.0
            'TE': [6.0, 4.0, 3.0, 2.0, 1.0],   # Top 5 TEs
            'QB': [8.0, 5.0, 3.0],              # Top 3 QBs
            'DST': [5.0, 3.0, 2.0],             # Top 3 DSTs
        }
        
        for position, elite_players in elite_by_position.items():
            bonuses = bonus_structures.get(position, [])
            
            for i, player in enumerate(elite_players):
                if i < len(bonuses):
                    bonus = bonuses[i]
                    # Add bonus to objective function
                    prob += player_vars[player.player_id] * bonus
                    logger.debug(
                        f"Elite bonus: {player.name} ({position} #{i+1}) gets +{bonus:.1f} points"
                    )
    
    def _add_snap_count_adjustments(
        self,
        prob: pulp.LpProblem,
        players: List[PlayerOptimizationData],
        player_vars: Dict[int, pulp.LpVariable],
        elite_player_ids: Set[int],
    ):
        """
        Add adjustments based on snap count history.
        
        Research shows Milly Winners had 28+ snaps (with rare exceptions).
        - Players with consistent 28+ snaps: +0.5 bonus
        - Players with <28 snaps: -1.0 penalty (unless elite)
        - Elite players exempt from penalties (they're elite for a reason)
        
        Uses games_with_20_plus_snaps as proxy:
        - 3+ games with 20+ snaps = likely 28+ snap player
        - 0-2 games = risky, penalize
        """
        for player in players:
            # Skip DST (no snap counts)
            if player.position == 'DST':
                continue
            
            # Elite players are exempt from snap count penalties
            # (their Smart Score already accounts for their value)
            is_elite = player.player_id in elite_player_ids
            
            snap_games = player.games_with_20_plus_snaps or 0
            
            if snap_games >= 3:
                # Consistent high-snap player: small bonus
                bonus = 0.5
                prob += player_vars[player.player_id] * bonus
                logger.debug(
                    f"Snap bonus: {player.name} has {snap_games} games with 20+ snaps, +{bonus:.1f}"
                )
            elif snap_games < 3 and not is_elite:
                # Low snap count, not elite: penalty
                penalty = -1.0
                prob += player_vars[player.player_id] * penalty
                logger.debug(
                    f"Snap penalty: {player.name} has only {snap_games} games with 20+ snaps, {penalty:.1f}"
                )
    
    def _add_diversity_penalty(
        self,
        prob: pulp.LpProblem,
        players: List[PlayerOptimizationData],
        player_vars: Dict[int, pulp.LpVariable],
        previous_lineups: List[GeneratedLineup],
        elite_player_ids: Set[int],
    ):
        """
        Add penalty for overlapping with previous lineups to ensure uniqueness.
        
        ELITE PLAYER PROTECTION: Elite players (top by Smart Score) get 75% reduced penalties.
        This allows proven winners to dominate lineups as shown in Milly Winner research.
        
        This penalizes players who appeared in previous lineups, forcing the optimizer
        to find different combinations while still maximizing Smart Score.
        """
        # Count how many times each player appeared in previous lineups
        player_overlap_count: Dict[int, int] = defaultdict(int)
        
        for lineup in previous_lineups:
            for player_data in lineup.players:
                for player in players:
                    if player.player_key == player_data['player_key']:
                        player_overlap_count[player.player_id] += 1
                        break
        
        # Apply diversity penalty by reducing the effective smart score
        # ELITE PLAYERS get 75% reduced penalty (0.025 vs 0.1)
        # This allows top Smart Score players to appear in most/all lineups
        base_penalty_elite = 0.025      # Elite players: minimal penalty
        base_penalty_regular = 0.1      # Regular players: standard penalty
        
        for player in players:
            overlap_count = player_overlap_count.get(player.player_id, 0)
            if overlap_count > 0:
                # Check if player is elite (top by Smart Score at their position)
                is_elite = player.player_id in elite_player_ids
                
                # Apply appropriate penalty
                penalty_rate = base_penalty_elite if is_elite else base_penalty_regular
                penalty = penalty_rate * overlap_count
                
                # Subtract penalty from this player's contribution to the objective
                prob += player_vars[player.player_id] * (-penalty)
                
                if is_elite:
                    logger.debug(
                        f"Elite diversity penalty: {player.name} appeared {overlap_count}x, "
                        f"penalty = {penalty:.2f} (reduced)"
                    )
        
        # HARD uniqueness constraint: Maximum 7 out of 9 players can overlap with any previous lineup
        # This guarantees at least 2 different players per lineup (22% uniqueness)
        # INCREASED from 6 to 7 to allow more elite player repetition per Milly Winner research
        max_overlap_per_lineup = 7
        
        for prev_lineup in previous_lineups:
            prev_player_ids = set()
            for player_data in prev_lineup.players:
                for player in players:
                    if player.player_key == player_data['player_key']:
                        prev_player_ids.add(player.player_id)
                        break
            
            # Constraint: sum of overlapping players <= 6 (at least 3 must be different)
            if prev_player_ids:
                overlap_vars = [player_vars[pid] for pid in prev_player_ids if pid in player_vars]
                if overlap_vars:
                    prob += pulp.lpSum(overlap_vars) <= max_overlap_per_lineup
    
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
        
        # Check position requirements (minimums, not exact counts due to FLEX)
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
        
        # FLEX: Should be 1 RB/WR/TE (already counted above)
        # Total RB/WR/TE should be 7 (2 RB + 3 WR + 1 TE + 1 FLEX)
        rb_wr_te_count = pos_counts.get('RB', 0) + pos_counts.get('WR', 0) + pos_counts.get('TE', 0)
        if rb_wr_te_count != 7:
            return False
        
        return True

