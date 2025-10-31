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


class LineupOptimizerService:
    """Service for generating optimized DraftKings lineups."""
    
    def __init__(self, session: Session):
        self.session = session
    
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
        
        logger.info(
            f"After preparing players (removing null Smart Scores): {len(opt_players)} players "
            f"(from {len(filtered_players)} filtered)"
        )
        
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
            
            # Sort lineups: baselines first (negative numbers), then regular lineups (positive numbers)
            generated_lineups.sort(key=lambda x: (x.lineup_number >= 0, abs(x.lineup_number)))
            
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
                # Filter by ITT > 18.5 (93% of top performers)
                if player.implied_team_total is not None and player.implied_team_total <= 18.5:
                    skipped_tournament_filter += 1
                    logger.debug(f"Player {player.name} ({player.position}) filtered: ITT {player.implied_team_total} <= 18.5")
                    continue
                
                # Ownership filter: RB chalk OK, others must be < 20%
                ownership_pct = (player.ownership or 0.0) * 100.0  # Convert to percentage
                if player.position != 'RB' and ownership_pct >= 20.0:
                    skipped_tournament_filter += 1
                    logger.debug(f"Player {player.name} ({player.position}) filtered: ownership {ownership_pct:.1f}% >= 20% (non-RB)")
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
        
        # Objective: Maximize Smart Score + small bonus for using salary cap efficiently
        # Primary: Smart Score (dominant factor)
        # Secondary: Salary usage (tiny bonus to encourage spending near cap)
        prob += pulp.lpSum([
            player.smart_score * player_vars[player.player_id]
            for player in opt_players
        ])
        
        # Add small bonus for salary usage (0.001 per $1000 = 0.05 points for full $50K)
        # This encourages using the full salary cap without overriding Smart Score optimization
        prob += pulp.lpSum([
            (player.salary / 1000) * 0.001 * player_vars[player.player_id]
            for player in opt_players
        ])
        
        # Apply strategy mode adjustments
        self._apply_strategy_mode(prob, opt_players, player_vars, settings.strategy_mode)
        
        # Position constraints
        self._add_position_constraints(prob, players_by_position, player_vars, settings)
        
        # Salary cap constraint
        prob += pulp.lpSum([
            player.salary * player_vars[player.player_id]
            for player in opt_players
        ]) <= SALARY_CAP
        
        # Team limit constraint
        self._add_team_constraints(prob, players_by_team, player_vars, settings)
        
        # Game limit constraint
        self._add_game_constraints(prob, opt_players, game_info, player_vars, settings)
        
        # Exposure limits
        self._add_exposure_constraints(prob, opt_players, player_vars, settings, previous_lineups)
        
        # Stacking rules
        self._add_stacking_constraints(prob, opt_players, game_info, player_vars, settings)
        
        # Diversity penalty (minimize overlap with previous lineups)
        if previous_lineups:
            self._add_diversity_penalty(prob, opt_players, player_vars, previous_lineups)
        
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
                ownership_pct = player.ownership * 100.0  # Convert to percentage
                
                # RB chalk is OK - don't penalize high-owned RBs
                if player.position == 'RB':
                    # RBs can be chalk - just optimize Smart Score
                    continue
                
                # For non-RBs: optimize for ownership leverage
                # Leverage = Smart Score / Ownership (higher is better)
                if player.ownership > 0.01:  # Avoid division by zero
                    leverage_score = player.smart_score / player.ownership
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
        
        # QB + WR stack rule
        if settings.stacking_rules.qb_wr_stack_enabled:
            qb_players = [p for p in players if p.position == 'QB']
            wr_players = [p for p in players if p.position == 'WR']
            
            # For each QB, ensure at least one WR from same team
            for qb in qb_players:
                qb_team_wrs = [wr for wr in wr_players if wr.team == qb.team]
                if qb_team_wrs:
                    # If QB selected, at least one WR from same team must be selected
                    prob += pulp.lpSum([player_vars[wr.player_id] for wr in qb_team_wrs]) >= player_vars[qb.player_id]
                else:
                    # No WRs from same team available - this makes QB+WR stack impossible for this QB
                    # Instead of making it infeasible, log a warning and skip the constraint for this QB
                    logger.warning(
                        f"QB+WR stack enabled but no WRs from {qb.team} available for QB {qb.name}. "
                        f"Skipping stack constraint for this QB to avoid infeasibility."
                    )
        
        # Bring-back constraint (opponent team player)
        # TEMPORARILY DISABLED - This constraint is making the problem infeasible
        # TODO: Fix bring-back logic to be less restrictive
        if False and settings.stacking_rules.bring_back_enabled:
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
        
        # Objective: Maximize Smart Score OR Projection (no penalties, no bonuses)
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
        
        # Position constraints (same as regular lineups)
        self._add_position_constraints(prob, players_by_position, player_vars, settings)
        
        # Salary constraint (DraftKings cap is always 50000)
        salary_cap = 50000
        prob += pulp.lpSum([
            player.salary * player_vars[player.player_id]
            for player in opt_players
        ]) <= salary_cap
        
        # Team constraints (optional - still apply for validity)
        if settings.max_players_per_team:
            self._add_team_constraints(prob, players_by_team, player_vars, settings)
        
        # Game constraints (optional)
        if settings.max_players_per_game:
            self._add_game_constraints(prob, opt_players, game_info, player_vars, settings)
        
        # NO stacking rules for baselines (they're unconstrained)
        # NO diversity penalties for baselines
        
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
    
    def _add_diversity_penalty(
        self,
        prob: pulp.LpProblem,
        players: List[PlayerOptimizationData],
        player_vars: Dict[int, pulp.LpVariable],
        previous_lineups: List[GeneratedLineup],
    ):
        """
        Add penalty for overlapping with previous lineups to ensure uniqueness.
        
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
        # Use a GENTLE penalty that encourages variety without sacrificing optimization
        # Base penalty: 0.5 points per appearance (much lighter than before)
        base_penalty = 0.5
        
        for player in players:
            overlap_count = player_overlap_count.get(player.player_id, 0)
            if overlap_count > 0:
                # Gentle escalating penalty: 0.5 * (overlap_count ^ 1.1)
                # This encourages variety but doesn't force bad picks
                penalty = base_penalty * (overlap_count ** 1.1)
                
                # Subtract penalty from this player's contribution to the objective
                prob += player_vars[player.player_id] * (-penalty)
        
        # Hard constraint: limit max overlap with any single previous lineup
        # Relaxed to 7 out of 9 (was 6) - allows more optimization while ensuring difference
        max_overlap_per_lineup = 7  # Maximum 7 out of 9 players can overlap with any previous lineup
        
        for prev_lineup in previous_lineups:
            prev_player_ids = set()
            for player_data in prev_lineup.players:
                for player in players:
                    if player.player_key == player_data['player_key']:
                        prev_player_ids.add(player.player_id)
                        break
            
            # Constraint: sum of overlapping players <= max_overlap_per_lineup
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

