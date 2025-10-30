/**
 * Sparkles Component
 * Inspired by Aceternity UI - Sparkles
 * 
 * Creates animated sparkle particles around content
 * Perfect for CTAs and key interactive elements
 */

import React, { useEffect, useState } from 'react';
import { Box, keyframes } from '@mui/material';

const sparklePulse = keyframes`
  0%, 100% {
    opacity: 0;
    transform: scale(0);
  }
  50% {
    opacity: 1;
    transform: scale(1);
  }
`;

interface Sparkle {
  id: number;
  x: number;
  y: number;
  delay: number;
  duration: number;
}

export interface SparklesProps {
  children: React.ReactNode;
  count?: number;
  size?: number;
  color?: string;
}

export const Sparkles: React.FC<SparklesProps> = ({
  children,
  count = 12,
  size = 4,
  color = '#ff6b35',
}) => {
  const [sparkles, setSparkles] = useState<Sparkle[]>([]);

  useEffect(() => {
    const newSparkles: Sparkle[] = Array.from({ length: count }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      delay: Math.random() * 3,
      duration: 2 + Math.random() * 2,
    }));
    setSparkles(newSparkles);
  }, [count]);

  return (
    <Box
      sx={{
        position: 'relative',
        display: 'inline-block',
        '& > *': {
          position: 'relative',
          zIndex: 1,
        },
      }}
    >
      {sparkles.map((sparkle) => (
        <Box
          key={sparkle.id}
          sx={{
            position: 'absolute',
            left: `${sparkle.x}%`,
            top: `${sparkle.y}%`,
            width: `${size}px`,
            height: `${size}px`,
            borderRadius: '50%',
            backgroundColor: color,
            boxShadow: `0 0 ${size * 2}px ${color}`,
            animation: `${sparklePulse} ${sparkle.duration}s ease-in-out infinite`,
            animationDelay: `${sparkle.delay}s`,
            pointerEvents: 'none',
            zIndex: 0,
          }}
        />
      ))}
      {children}
    </Box>
  );
};

export default Sparkles;

