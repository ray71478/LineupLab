/**
 * UnmatchedPlayersReview Component
 *
 * Post-import review screen showing unmatched players that couldn't be fuzzy-matched
 * with confidence above the threshold (85%).
 *
 * Features:
 * - Lists all unmatched players with import details
 * - Shows suggested matches with similarity scores
 * - Map to suggested button for accepting suggestions
 * - Ignore button for skipping players
 * - Save mappings button to persist actions
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Grid,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';
import PersonIcon from '@mui/icons-material/Person';
import CheckIcon from '@mui/icons-material/Check';
import CloseIcon from '@mui/icons-material/Close';

export interface UnmatchedPlayer {
  id: number;
  imported_name: string;
  team: string;
  position: string;
  suggested_player_key: string | null;
  similarity_score: number | null;
  status: 'pending' | 'mapped' | 'ignored';
}

export interface UnmatchedPlayersReviewProps {
  importId: string;
  onClose?: () => void;
  onSave?: () => void;
}

interface PlayerAction {
  unmatched_player_id: number;
  action: 'map' | 'ignore';
  canonical_player_key?: string;
}

export const UnmatchedPlayersReview: React.FC<UnmatchedPlayersReviewProps> = ({
  importId,
  onClose,
  onSave,
}) => {
  const [players, setPlayers] = useState<UnmatchedPlayer[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [playerActions, setPlayerActions] = useState<Map<number, PlayerAction>>(new Map());
  const [isSaving, setIsSaving] = useState(false);
  const [showCreateNewDialog, setShowCreateNewDialog] = useState(false);
  const [createDialogPlayerId, setCreateDialogPlayerId] = useState<number | null>(null);
  const [newPlayerKey, setNewPlayerKey] = useState('');

  // Fetch unmatched players on mount
  useEffect(() => {
    const fetchUnmatchedPlayers = async () => {
      try {
        setIsLoading(true);
        const response = await fetch(
          `/api/unmatched-players?import_id=${importId}&status=pending`
        );

        if (!response.ok) {
          throw new Error('Failed to fetch unmatched players');
        }

        const data = await response.json();
        if (data.success && Array.isArray(data.unmatched_players)) {
          setPlayers(data.unmatched_players);
        } else {
          setError('Invalid response format');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load unmatched players');
      } finally {
        setIsLoading(false);
      }
    };

    fetchUnmatchedPlayers();
  }, [importId]);

  const handleMapToSuggested = (player: UnmatchedPlayer) => {
    if (player.suggested_player_key) {
      setPlayerActions((prev) => {
        const newMap = new Map(prev);
        newMap.set(player.id, {
          unmatched_player_id: player.id,
          action: 'map',
          canonical_player_key: player.suggested_player_key,
        });
        return newMap;
      });
    }
  };

  const handleIgnore = (playerId: number) => {
    setPlayerActions((prev) => {
      const newMap = new Map(prev);
      newMap.set(playerId, {
        unmatched_player_id: playerId,
        action: 'ignore',
      });
      return newMap;
    });
  };

  const handleCreateNew = (playerId: number) => {
    setCreateDialogPlayerId(playerId);
    setShowCreateNewDialog(true);
  };

  const handleCreateNewConfirm = () => {
    if (createDialogPlayerId && newPlayerKey) {
      setPlayerActions((prev) => {
        const newMap = new Map(prev);
        newMap.set(createDialogPlayerId, {
          unmatched_player_id: createDialogPlayerId,
          action: 'map',
          canonical_player_key: newPlayerKey,
        });
        return newMap;
      });
      setShowCreateNewDialog(false);
      setNewPlayerKey('');
      setCreateDialogPlayerId(null);
    }
  };

  const handleUndo = (playerId: number) => {
    setPlayerActions((prev) => {
      const newMap = new Map(prev);
      newMap.delete(playerId);
      return newMap;
    });
  };

  const handleSaveMappings = async () => {
    try {
      setIsSaving(true);
      const actions = Array.from(playerActions.values());

      for (const action of actions) {
        const endpoint =
          action.action === 'map'
            ? '/api/unmatched-players/map'
            : '/api/unmatched-players/ignore';

        const body =
          action.action === 'map'
            ? {
                unmatched_player_id: action.unmatched_player_id,
                canonical_player_key: action.canonical_player_key,
              }
            : {
                unmatched_player_id: action.unmatched_player_id,
              };

        const response = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });

        if (!response.ok) {
          throw new Error(`Failed to save mapping for player ${action.unmatched_player_id}`);
        }
      }

      // Clear actions and refresh
      setPlayerActions(new Map());
      onSave?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save mappings');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (players.length === 0) {
    return (
      <Box sx={{ py: 3 }}>
        <Alert severity="success">
          All players were matched successfully! No review needed.
        </Alert>
      </Box>
    );
  }

  const pendingActionCount = playerActions.size;
  const reviewedCount = players.filter((p) => playerActions.has(p.id)).length;

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 2 }}>
        Unmatched Players ({reviewedCount}/{players.length})
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ mb: 3 }}>
        <Typography variant="body2" color="text.secondary">
          These players couldn't be automatically matched. Review them below and choose an action
          for each.
        </Typography>
      </Box>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        {players.map((player) => {
          const action = playerActions.get(player.id);
          const isActioned = !!action;

          return (
            <Grid item xs={12} md={6} key={player.id}>
              <Card
                variant={isActioned ? 'outlined' : 'elevation'}
                sx={{
                  opacity: isActioned ? 0.7 : 1,
                  backgroundColor: isActioned
                    ? action.action === 'ignore'
                      ? '#f5f5f5'
                      : '#e8f5e9'
                    : 'inherit',
                  transition: 'all 0.2s',
                }}
              >
                <CardContent>
                  {/* Header with player info */}
                  <Box sx={{ display: 'flex', alignItems: 'start', gap: 1, mb: 2 }}>
                    <PersonIcon color="primary" />
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="h6">{player.imported_name}</Typography>
                      <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                        <Chip label={player.team} size="small" variant="outlined" />
                        <Chip label={player.position} size="small" variant="outlined" />
                      </Box>
                    </Box>
                    {isActioned && (
                      <Box>
                        {action.action === 'map' && (
                          <CheckIcon color="success" />
                        )}
                        {action.action === 'ignore' && (
                          <CloseIcon color="disabled" />
                        )}
                      </Box>
                    )}
                  </Box>

                  {/* Suggested match */}
                  {player.suggested_player_key && player.similarity_score ? (
                    <Box sx={{ mb: 2, p: 1.5, backgroundColor: '#f5f5f5', borderRadius: 1 }}>
                      <Typography variant="caption" color="text.secondary">
                        Suggested Match
                      </Typography>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace', mt: 0.5 }}>
                        {player.suggested_player_key}
                      </Typography>
                      <Typography variant="caption" color="primary" sx={{ display: 'block', mt: 0.5 }}>
                        {(player.similarity_score * 100).toFixed(0)}% match confidence
                      </Typography>
                    </Box>
                  ) : (
                    <Typography variant="caption" color="error" sx={{ display: 'block', mb: 2 }}>
                      No suggested match available
                    </Typography>
                  )}

                  {/* Action status */}
                  {isActioned && (
                    <Box sx={{ mb: 2, p: 1, backgroundColor: 'rgba(76, 175, 80, 0.1)', borderRadius: 1 }}>
                      <Typography variant="caption">
                        {action.action === 'map' ? (
                          <>
                            <CheckIcon sx={{ fontSize: 14, mr: 0.5, verticalAlign: 'middle' }} />
                            Mapped to: <strong>{action.canonical_player_key}</strong>
                          </>
                        ) : (
                          <>
                            <CloseIcon sx={{ fontSize: 14, mr: 0.5, verticalAlign: 'middle' }} />
                            Marked as ignored
                          </>
                        )}
                      </Typography>
                    </Box>
                  )}

                  {/* Action buttons */}
                  {!isActioned && (
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {player.suggested_player_key && (
                        <Button
                          variant="contained"
                          size="small"
                          onClick={() => handleMapToSuggested(player)}
                        >
                          Map to Suggested
                        </Button>
                      )}
                      <Button
                        variant="outlined"
                        size="small"
                        onClick={() => handleCreateNew(player.id)}
                      >
                        Create New
                      </Button>
                      <Button
                        variant="text"
                        size="small"
                        color="error"
                        onClick={() => handleIgnore(player.id)}
                      >
                        Ignore
                      </Button>
                    </Box>
                  )}

                  {isActioned && (
                    <Button
                      variant="text"
                      size="small"
                      onClick={() => handleUndo(player.id)}
                    >
                      Undo
                    </Button>
                  )}
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {/* Save button */}
      <Box sx={{ display: 'flex', gap: 1 }}>
        <Button
          variant="contained"
          disabled={pendingActionCount === 0 || isSaving}
          onClick={handleSaveMappings}
        >
          {isSaving ? 'Saving...' : `Save Mappings (${pendingActionCount})`}
        </Button>
        <Button variant="outlined" onClick={onClose}>
          Done
        </Button>
      </Box>

      {/* Create New Player Dialog */}
      <Dialog
        open={showCreateNewDialog}
        onClose={() => setShowCreateNewDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Create New Player Mapping</DialogTitle>
        <DialogContent sx={{ py: 2 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Enter the player key for the new player. Format: name_team_position (e.g., christian_mccaffrey_SF_RB)
          </Typography>
          <TextField
            autoFocus
            fullWidth
            label="Player Key"
            placeholder="christian_mccaffrey_SF_RB"
            value={newPlayerKey}
            onChange={(e) => setNewPlayerKey(e.target.value)}
            variant="outlined"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCreateNewDialog(false)}>Cancel</Button>
          <Button
            onClick={handleCreateNewConfirm}
            variant="contained"
            disabled={!newPlayerKey}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default UnmatchedPlayersReview;
