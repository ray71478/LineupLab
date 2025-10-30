/**
 * Player Management Types
 *
 * TypeScript types for player-related data and API responses
 */

export interface PlayerResponse {
  id: number;
  player_key: string;
  name: string;
  team: string;
  position: string;
  salary: number;
  projection?: number | null;
  ownership?: number | null;
  ceiling?: number | null;
  floor?: number | null;
  notes?: string | null;
  source: string;
  status: 'matched' | 'unmatched';
  uploaded_at: string;
}

export interface UnmatchedPlayerResponse {
  id: number;
  imported_name: string;
  team: string;
  position: string;
  salary?: number | null;
  similarity_score?: number | null;
  status: 'pending' | 'mapped' | 'ignored';
  suggestions?: PlayerResponse[];
}

export interface PlayerFilters {
  positions: string[];
  teams: string[];
  unmatchedOnly: boolean;
  searchQuery: string;
}

export interface SortState {
  sortColumn: string | null;
  sortDirection: 'asc' | 'desc';
}

export interface MappingPayload {
  unmatched_player_id: number;
  canonical_player_key: string;
}

export interface MappingResponse {
  success: boolean;
  message?: string;
  error?: string;
}
