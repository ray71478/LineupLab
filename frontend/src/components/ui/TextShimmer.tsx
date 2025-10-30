/**
 * Text Shimmer Component
 * Inspired by Motion Primitives - Text Shimmer
 * 
 * Creates an animated shimmer effect on text
 * Perfect for hero titles and important CTAs
 */

import React from 'react';
import { Typography, TypographyProps, keyframes } from '@mui/material';

const shimmerAnimation = keyframes`
  0% {
    background-position: -200% center;
  }
  100% {
    background-position: 200% center;
  }
`;

export interface TextShimmerProps extends TypographyProps {
  children: React.ReactNode;
  enabled?: boolean;
  color?: string;
}

export const TextShimmer: React.FC<TextShimmerProps> = ({
  children,
  enabled = true,
  color = '#ff6b35',
  sx,
  ...props
}) => {
  if (!enabled) {
    return <Typography {...props} sx={sx}>{children}</Typography>;
  }

  return (
    <Typography
      {...props}
      sx={{
        ...sx,
        background: `linear-gradient(90deg, #ffffff 0%, ${color} 50%, #ffffff 100%)`,
        backgroundSize: '200% auto',
        backgroundClip: 'text',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        animation: `${shimmerAnimation} 3s linear infinite`,
        display: 'inline-block',
      }}
    >
      {children}
    </Typography>
  );
};

export default TextShimmer;

