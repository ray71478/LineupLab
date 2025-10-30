/**
 * Aurora Background Component
 * Inspired by Aceternity UI - Aurora Background
 * 
 * Creates a subtle animated gradient background effect
 * Perfect for hero sections and landing pages
 */

import React from 'react';
import { Box, keyframes } from '@mui/material';

const auroraAnimation = keyframes`
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
`;

export interface AuroraBackgroundProps {
  children?: React.ReactNode;
  intensity?: number; // 0-1, controls opacity
}

export const AuroraBackground: React.FC<AuroraBackgroundProps> = ({
  children,
  intensity = 0.15,
}) => {
  return (
    <Box
      sx={{
        position: 'relative',
        width: '100%',
        height: '100%',
        overflow: 'hidden',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: `
            radial-gradient(ellipse at top, rgba(255, 107, 53, ${intensity * 0.6}) 0%, transparent 50%),
            radial-gradient(ellipse at bottom right, rgba(255, 107, 53, ${intensity * 0.3}) 0%, transparent 50%),
            radial-gradient(ellipse at bottom left, rgba(255, 107, 53, ${intensity * 0.2}) 0%, transparent 50%)
          `,
          backgroundSize: '200% 200%',
          animation: `${auroraAnimation} 15s ease infinite`,
          pointerEvents: 'none',
          zIndex: 0,
        },
        '&::after': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: `
            radial-gradient(circle at 20% 50%, rgba(255, 107, 53, ${intensity * 0.2}) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(255, 107, 53, ${intensity * 0.15}) 0%, transparent 50%)
          `,
          backgroundSize: '300% 300%',
          animation: `${auroraAnimation} 20s ease infinite reverse`,
          pointerEvents: 'none',
          zIndex: 0,
        },
      }}
    >
      {children && (
        <Box sx={{ position: 'relative', zIndex: 1 }}>{children}</Box>
      )}
    </Box>
  );
};

export default AuroraBackground;

