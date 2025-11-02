/**
 * Smart Score Engine Types
 *
 * TypeScript types for Smart Score calculation and weight profile management
 */

export interface WeightProfile {
  W1: number;
  W2: number;
  W3: number;
  W4: number;
  W5: number;
  W6: number;
  W7: number;
  W8: number;
}

export interface ScoreConfig {
  projection_source: 'ETR' | 'LineStar';
  eighty_twenty_enabled: boolean;
  eighty_twenty_threshold: number;
}

export interface ScoreBreakdown {
  W1_value: number;
  W2_value: number;
  W3_value: number;
  W4_value: number;
  W5_value: number;
  W6_value: number;
  W7_value: number;
  W8_value: number;
  smart_score: number;
  missing_data_indicators?: Record<string, boolean>;
}

export interface StackPartner {
  partner_key: string;
  partner_name: string;
  partner_position: string;
  correlation: number;
  games_count: number;
}

export interface PlayerScoreResponse {
  player_id: number;
  player_key: string;
  name: string;
  team: string;
  position: string;
  salary: number;
  projection?: number | null;
  ownership?: number | null;
  ceiling?: number | null;
  floor?: number | null;
  smart_score?: number | null;
  projection_source?: string | null;
  opponent_rank_category?: string | null;
  games_with_20_plus_snaps?: number | null;
  regression_risk: boolean;
  score_breakdown?: ScoreBreakdown | null;
  // Vegas context data
  implied_team_total?: number | null;
  over_under?: number | null;
  // Historical insights
  consistency_score?: number | null;
  opponent?: string | null;
  opponent_matchup_avg?: number | null;
  salary_efficiency_trend?: 'up' | 'down' | 'stable' | null;
  usage_warnings?: string[] | null;
  stack_partners?: StackPartner[] | null;
  injury_status?: string | null; // PROBABLE, QUESTIONABLE, DOUBTFUL, OUT
}

export interface WeightProfileResponse {
  id: number;
  name: string;
  weights: WeightProfile;
  config: ScoreConfig;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface CalculateScoreRequest {
  week_id: number;
  weights: WeightProfile;
  config: ScoreConfig;
}

export interface CalculateScoreResponse {
  success: boolean;
  players: PlayerScoreResponse[];
  total_players: number;
  calculation_time_ms?: number | null;
}

export interface WeightProfileListResponse {
  success: boolean;
  profiles: WeightProfileResponse[];
  default_profile_id?: number | null;
}

export interface CreateProfileRequest {
  name: string;
  weights: WeightProfile;
  config: ScoreConfig;
  is_default?: boolean;
}

export interface UpdateProfileRequest {
  name?: string;
  weights?: WeightProfile;
  config?: ScoreConfig;
  is_default?: boolean;
}

export interface ScoreChange {
  playerId: number;
  playerName: string;
  previousScore: number;
  newScore: number;
  delta: number;
  isTopChange: boolean;
  // Factor breakdown changes
  factorChanges?: {
    W1?: { previous: number; current: number; delta: number };
    W2?: { previous: number; current: number; delta: number };
    W3?: { previous: number; current: number; delta: number };
    W4?: { previous: number; current: number; delta: number };
    W5?: { previous: number; current: number; delta: number };
    W6?: { previous: number; current: number; delta: number };
    W7?: { previous: number; current: number; delta: number };
    W8?: { previous: number; current: number; delta: number };
  };
  // Player data for context (ownership, etc.)
  playerData?: {
    ownership?: number | null;
    projection?: number | null;
    salary?: number;
    position?: string;
  };
}

