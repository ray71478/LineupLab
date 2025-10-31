/**
 * LineupLabIcon Component
 *
 * Custom icon for Lineup Lab - represents roster/lineup structure
 * Features:
 * - Grid structure representing roster positions
 * - Layered/stacked effect suggesting optimization
 * - Modern, distinctive design
 * - Orange accent color (#ff6b35)
 */

import React from 'react';
import { Box } from '@mui/material';

export interface LineupLabIconProps {
  size?: number;
  color?: string;
}

export const LineupLabIcon: React.FC<LineupLabIconProps> = ({
  size = 20,
  color = '#ff6b35',
}) => {
  return (
    <Box
      sx={{
        width: size,
        height: size,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Grid background - represents roster structure */}
        <g opacity="0.3">
          {/* Vertical lines */}
          <line x1="6" y1="4" x2="6" y2="20" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
          <line x1="12" y1="4" x2="12" y2="20" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
          <line x1="18" y1="4" x2="18" y2="20" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
          {/* Horizontal lines */}
          <line x1="4" y1="8" x2="20" y2="8" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
          <line x1="4" y1="12" x2="20" y2="12" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
          <line x1="4" y1="16" x2="20" y2="16" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
        </g>

        {/* Top layer - selected/optimized cells (highlighted) */}
        <g opacity="0.9">
          {/* First row highlight */}
          <rect x="4" y="4" width="8" height="4" fill={color} rx="1" />
          {/* Second row highlight */}
          <rect x="6" y="8" width="6" height="4" fill={color} rx="1" />
          {/* Third row highlight */}
          <rect x="12" y="12" width="8" height="4" fill={color} rx="1" />
          {/* Bottom highlight */}
          <rect x="14" y="16" width="6" height="4" fill={color} rx="1" />
        </g>

        {/* Accent dots - suggests data points/optimization */}
        <g opacity="0.8">
          <circle cx="6" cy="6" r="1.5" fill={color} />
          <circle cx="18" cy="14" r="1.5" fill={color} />
          <circle cx="16" cy="18" r="1.5" fill={color} />
        </g>

        {/* Outer glow effect */}
        <rect
          x="4"
          y="4"
          width="16"
          height="16"
          fill="none"
          stroke={color}
          strokeWidth="0.5"
          opacity="0.2"
          rx="2"
        />
      </svg>
    </Box>
  );
};

export default LineupLabIcon;

