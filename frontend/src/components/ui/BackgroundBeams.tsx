/**
 * Background Beams Component
 * Inspired by Aceternity UI - Background Beams
 * 
 * Creates subtle animated beam-like effects in the background
 * Perfect for adding depth to hero sections
 */

import React from 'react';
import { Box, keyframes } from '@mui/material';

const beamAnimation = keyframes`
  0% {
    transform: translateX(-100%) translateY(-100%) rotate(45deg);
  }
  100% {
    transform: translateX(100%) translateY(100%) rotate(45deg);
  }
`;

export interface BackgroundBeamsProps {
  children?: React.ReactNode;
  beamCount?: number;
  intensity?: number;
}

export const BackgroundBeams: React.FC<BackgroundBeamsProps> = ({
  children,
  beamCount = 3,
  intensity = 0.05,
}) => {
  return (
    <Box
      sx={{
        position: 'relative',
        width: '100%',
        height: '100%',
        overflow: 'hidden',
      }}
    >
      {Array.from({ length: beamCount }).map((_, i) => (
        <Box
          key={i}
          sx={{
            position: 'absolute',
            top: `${(i + 1) * (100 / (beamCount + 1))}%`,
            left: '-50%',
            width: '200%',
            height: '1px',
            background: `linear-gradient(90deg, transparent, rgba(255, 107, 53, ${intensity}), transparent)`,
            animation: `${beamAnimation} ${8 + i * 2}s linear infinite`,
            animationDelay: `${i * 0.5}s`,
            pointerEvents: 'none',
            zIndex: 0,
          }}
        />
      ))}
      {children && (
        <Box sx={{ position: 'relative', zIndex: 1 }}>{children}</Box>
      )}
    </Box>
  );
};

export default BackgroundBeams;

