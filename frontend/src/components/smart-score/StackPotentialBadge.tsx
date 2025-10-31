/**
 * StackPotentialBadge Component
 *
 * Displays stack correlation partners for a player (QB shows WRs, WR/TE shows QB).
 * This is metadata only - does NOT affect Smart Score.
 */

import React from 'react';
import { Chip, Tooltip, Box } from '@mui/material';
import { StackPartner } from '../../types/smartScore.types';

interface StackPotentialBadgeProps {
  stackPartners?: StackPartner[] | null;
  position: string;
}

export const StackPotentialBadge: React.FC<StackPotentialBadgeProps> = ({
  stackPartners,
  position,
}) => {
  if (!stackPartners || stackPartners.length === 0) {
    return null;
  }

  // For QBs: show top partner correlation
  // For WRs/TEs: show QB correlation
  const topPartner = stackPartners[0];
  const correlation = topPartner.correlation;

  // Color coding: higher correlation = better stack potential
  const getColor = (corr: number): 'success' | 'warning' | 'info' => {
    if (corr >= 0.7) return 'success';
    if (corr >= 0.5) return 'warning';
    return 'info';
  };

  const getLabel = () => {
    if (position === 'QB') {
      return `${topPartner.partner_position} ${topPartner.correlation.toFixed(2)}`;
    } else {
      return `QB ${topPartner.correlation.toFixed(2)}`;
    }
  };

  const tooltipContent = (
    <Box>
      <strong>Stack Partners:</strong>
      <br />
      {stackPartners.map((partner, idx) => (
        <span key={partner.partner_key}>
          {idx > 0 && <br />}
          {partner.partner_name} ({partner.partner_position}): {partner.correlation.toFixed(2)} correlation
          {' '}({partner.games_count} games)
        </span>
      ))}
      <br />
      <br />
      <em>Note: This is metadata only and does not affect Smart Score.</em>
    </Box>
  );

  return (
    <Tooltip title={tooltipContent} arrow>
      <Chip
        label={getLabel()}
        color={getColor(correlation)}
        size="small"
        sx={{
          fontSize: '0.75rem',
          height: '20px',
          cursor: 'help',
        }}
      />
    </Tooltip>
  );
};

