/**
 * Moving Border Component
 * Inspired by Aceternity UI - Moving Border
 * 
 * Creates an animated gradient border effect
 * Perfect for buttons and interactive cards
 */

import React from 'react';
import { Box, BoxProps, keyframes } from '@mui/material';

const borderAnimation = keyframes`
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

export interface MovingBorderProps extends BoxProps {
  children: React.ReactNode;
  borderColor?: string;
  borderWidth?: number;
  borderRadius?: number;
}

export const MovingBorder: React.FC<MovingBorderProps> = ({
  children,
  borderColor = '#ff6b35',
  borderWidth = 1,
  borderRadius = 12,
  sx,
  ...props
}) => {
  return (
    <Box
      {...props}
      sx={{
        position: 'relative',
        borderRadius: `${borderRadius}px`,
        padding: `${borderWidth}px`,
        background: `linear-gradient(90deg, ${borderColor}, transparent, ${borderColor})`,
        backgroundSize: '200% 200%',
        animation: `${borderAnimation} 3s ease infinite`,
        ...sx,
      }}
    >
      <Box
        sx={{
          position: 'relative',
          borderRadius: `${borderRadius - borderWidth}px`,
          backgroundColor: '#0a0a0a',
          width: '100%',
          height: '100%',
        }}
      >
        {children}
      </Box>
    </Box>
  );
};

export default MovingBorder;

