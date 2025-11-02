/**
 * Lineup Optimizer Types
 *
 * TypeScript types for lineup generation and management
 */

import type { WeightProfile, ScoreConfig } from './smartScore.types';

export interface PlayerExposureLimits {
  min?: number;
  max?: number;
}

export interface StackingRules {
  qb_wr_stack_enabled: boolean;
  bring_back_enabled: boolean;
}

export interface OptimizationSettings {
  num_lineups: number;
  strategy_mode: 'Chalk' | 'Balanced' | 'Contrarian' | 'Tournament';
  max_players_per_team: number;
  max_players_per_game: number;
  player_exposure_limits?: Record<string, PlayerExposureLimits>;
  stacking_rules?: StackingRules;
  exclude_bottom_percentile?: number;
  max_ownership?: number;
  locked_captain_id?: string | null; // Showdown mode: force specific player as captain
}

export interface LineupPlayer {
  position: string;
  player_key: string;
  name: string;
  team: string;
  salary: number;
  smart_score: number;
  ownership: number;
  projection?: number;
  is_captain?: boolean;
}

export interface GeneratedLineup {
  lineup_number: number; // 1-N for regular lineups, -1 for "Best Smart Score", -2 for "Best Projection"
  players: LineupPlayer[];
  total_salary: number;
  projected_score: number;
  projected_points: number;
  avg_ownership: number;
}

export interface LineupOptimizationRequest {
  week_id: number;
  settings: OptimizationSettings;
  selected_player_ids?: number[];
  weights?: WeightProfile;
  config?: ScoreConfig;
  contest_mode?: 'main' | 'showdown';
  locked_captain_id?: string;
}

export interface LineupOptimizationResponse {
  week_id: number;
  lineups: GeneratedLineup[];
  settings: OptimizationSettings;
  generation_time_ms: number;
}

export interface SaveLineupsRequest {
  week_id: number;
  lineups: GeneratedLineup[];
  weight_profile_id?: number;
  strategy_mode?: string;
  contest_mode?: 'main' | 'showdown';
}

export interface SaveLineupsResponse {
  saved_count: number;
  lineups: SavedLineup[];
}

export interface SavedLineup {
  id: number;
  week_id: number;
  lineup_number: number;
  players: LineupPlayer[];
  total_salary: number;
  projected_score: number;
  avg_ownership?: number;
  strategy_mode: string;
  weight_profile_id?: number;
  created_at: string;
  contest_mode?: 'main' | 'showdown';
}
