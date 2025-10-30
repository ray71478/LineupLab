/**
 * FuzzyMatchSuggestions Component
 *
 * Displays list of fuzzy-matched player suggestions with similarity scores.
 * Highlights selected suggestion with color-coded scores.
 *
 * Performance Optimizations:
 * - Memoized component to prevent unnecessary re-renders
 * - useCallback for event handlers
 * - Efficient list rendering
 *
 * Accessibility Features:
 * - ARIA labels for each suggestion
 * - Color-coded scores with text fallback
 * - Keyboard navigation support
 * - Screen reader friendly list items
 *
 * Mobile Optimized:
 * - Responsive touch buttons (44x44px minimum)
 * - Proper spacing and padding on mobile
 */

import React, { useCallback, useMemo } from 'react';
import {
  List,
  ListItemButton,
  Box,
  Typography,
  Stack,
  Chip,
  CircularProgress,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import CheckIcon from '@mui/icons-material/Check';

export interface PlayerSuggestion {
  id?: number;
  player_key: string;
  name: string;
  team: string;
  position: string;
  salary?: number;
  similarity_score: number;
}

export interface FuzzyMatchSuggestionsProps {
  suggestions: PlayerSuggestion[];
  selectedPlayer?: PlayerSuggestion;
  onSelectSuggestion: (player: PlayerSuggestion) => void;
  isLoading?: boolean;
}

/**
 * Get color based on similarity score
 * Green for high (0.85+), yellow for medium (0.7-0.84), red for low (<0.7)
 */
const getScoreColor = (score: number): string => {
  if (score >= 0.85) return '#4caf50'; // Green
  if (score >= 0.7) return '#ff9800'; // Orange/Yellow
  return '#ff5722'; // Red
};

/**
 * Get score interpretation for screen readers
 */
const getScoreInterpretation = (score: number): string => {
  if (score >= 0.85) return 'high confidence match';
  if (score >= 0.7) return 'medium confidence match';
  return 'low confidence match';
};

const SuggestionListItem = React.memo<{
  suggestion: PlayerSuggestion;
  isSelected: boolean;
  onClick: () => void;
  isMobile: boolean;
}>(({ suggestion, isSelected, onClick, isMobile }) => {
  const scoreColor = useMemo(() => getScoreColor(suggestion.similarity_score), [suggestion.similarity_score]);
  const scoreInterpretation = useMemo(
    () => getScoreInterpretation(suggestion.similarity_score),
    [suggestion.similarity_score]
  );

  return (
    <ListItemButton
      onClick={onClick}
      selected={isSelected}
      aria-label={`Select ${suggestion.name} from ${suggestion.team} at ${suggestion.position} - ${scoreInterpretation}`}
      aria-pressed={isSelected}
      sx={{
        backgroundColor: isSelected
          ? 'rgba(255, 140, 66, 0.15)'
          : 'transparent',
        borderLeft: isSelected ? '4px solid #ff8c42' : '4px solid transparent',
        transition: 'all 0.2s ease-in-out',
        '@media (hover: hover)': {
          '&:hover': {
            backgroundColor: 'rgba(255, 140, 66, 0.1)',
          },
        },
        padding: isMobile ? '12px 12px' : '12px 16px',
        minHeight: isMobile ? '48px' : '44px',
        marginBottom: '4px',
      }}
      role="option"
      aria-selected={isSelected}
    >
      <Stack
        direction="row"
        spacing={1}
        sx={{
          width: '100%',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: isMobile ? 1 : 1.5,
        }}
      >
        <Stack
          spacing={0.5}
          sx={{
            flex: 1,
            minWidth: 0,
          }}
        >
          {/* Player Info */}
          <Stack
            direction="row"
            spacing={1}
            sx={{
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: isMobile ? 0.75 : 1,
            }}
          >
            <Typography
              variant="body2"
              sx={{
                color: '#ffffff',
                fontWeight: 500,
                fontSize: isMobile ? '0.85rem' : '0.95rem',
              }}
            >
              {suggestion.name}
            </Typography>

            {/* Team and Position Badges */}
            <Box
              sx={{
                display: 'flex',
                gap: 0.5,
              }}
            >
              <Chip
                label={suggestion.team}
                size="small"
                variant="outlined"
                sx={{
                  height: isMobile ? '18px' : '20px',
                  fontSize: isMobile ? '0.65rem' : '0.7rem',
                  color: '#e5e7eb',
                  borderColor: 'rgba(255, 255, 255, 0.2)',
                }}
              />
              <Chip
                label={suggestion.position}
                size="small"
                variant="outlined"
                sx={{
                  height: isMobile ? '18px' : '20px',
                  fontSize: isMobile ? '0.65rem' : '0.7rem',
                  color: '#e5e7eb',
                  borderColor: 'rgba(255, 255, 255, 0.2)',
                }}
              />
            </Box>
          </Stack>

          {/* Salary (if available) */}
          {suggestion.salary && (
            <Typography
              variant="caption"
              sx={{
                color: '#9ca3af',
                fontSize: isMobile ? '0.7rem' : '0.75rem',
              }}
            >
              Salary: ${suggestion.salary.toLocaleString()}
            </Typography>
          )}
        </Stack>

        {/* Score Badge and Selection Indicator */}
        <Stack
          spacing={0.5}
          sx={{
            alignItems: 'flex-end',
            flexShrink: 0,
          }}
        >
          {/* Similarity Score */}
          <Box
            sx={{
              backgroundColor: scoreColor,
              color: '#ffffff',
              padding: isMobile ? '3px 6px' : '4px 8px',
              borderRadius: '4px',
              fontSize: isMobile ? '0.75rem' : '0.8rem',
              fontWeight: 600,
              whiteSpace: 'nowrap',
              minWidth: '40px',
              textAlign: 'center',
            }}
            role="status"
            aria-label={`Match confidence: ${(suggestion.similarity_score * 100).toFixed(0)}%`}
          >
            {(suggestion.similarity_score * 100).toFixed(0)}%
          </Box>

          {/* Selected Indicator */}
          {isSelected && (
            <CheckIcon
              sx={{
                color: '#ff8c42',
                fontSize: isMobile ? '1rem' : '1.25rem',
              }}
              aria-hidden="true"
            />
          )}
        </Stack>
      </Stack>
    </ListItemButton>
  );
});

SuggestionListItem.displayName = 'SuggestionListItem';

export const FuzzyMatchSuggestions: React.FC<FuzzyMatchSuggestionsProps> = React.memo(({
  suggestions,
  selectedPlayer,
  onSelectSuggestion,
  isLoading = false,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const handleSelectSuggestion = useCallback(
    (player: PlayerSuggestion) => {
      onSelectSuggestion(player);
    },
    [onSelectSuggestion]
  );

  if (isLoading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '200px',
        }}
        role="status"
        aria-label="Loading suggestions"
      >
        <CircularProgress sx={{ color: '#ff8c42' }} />
      </Box>
    );
  }

  if (suggestions.length === 0) {
    return (
      <Box
        sx={{
          padding: isMobile ? '16px' : '24px',
          textAlign: 'center',
          backgroundColor: 'rgba(255, 255, 255, 0.05)',
          borderRadius: '8px',
        }}
        role="status"
      >
        <Typography
          variant="body2"
          sx={{
            color: '#9ca3af',
            fontSize: isMobile ? '0.85rem' : '0.9rem',
          }}
        >
          No suggestions found. You can search manually or skip this player.
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Typography
        variant="subtitle2"
        sx={{
          color: '#e5e7eb',
          marginBottom: '12px',
          fontWeight: 600,
          fontSize: isMobile ? '0.85rem' : '0.9rem',
        }}
        id="suggestions-label"
      >
        Suggested Matches ({suggestions.length})
      </Typography>

      <List
        sx={{
          backgroundColor: 'rgba(255, 255, 255, 0.02)',
          borderRadius: '8px',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          maxHeight: isMobile ? '250px' : '300px',
          overflowY: 'auto',
          '&::-webkit-scrollbar': {
            width: '6px',
          },
          '&::-webkit-scrollbar-track': {
            backgroundColor: 'rgba(255, 255, 255, 0.05)',
          },
          '&::-webkit-scrollbar-thumb': {
            backgroundColor: 'rgba(255, 140, 66, 0.3)',
            borderRadius: '3px',
            '&:hover': {
              backgroundColor: 'rgba(255, 140, 66, 0.5)',
            },
          },
        }}
        role="listbox"
        aria-labelledby="suggestions-label"
      >
        {suggestions.map((suggestion, index) => {
          const isSelected =
            selectedPlayer?.player_key === suggestion.player_key;

          return (
            <SuggestionListItem
              key={`${suggestion.player_key}-${index}`}
              suggestion={suggestion}
              isSelected={isSelected}
              onClick={() => handleSelectSuggestion(suggestion)}
              isMobile={isMobile}
            />
          );
        })}
      </List>
    </Box>
  );
});

FuzzyMatchSuggestions.displayName = 'FuzzyMatchSuggestions';

export default FuzzyMatchSuggestions;
