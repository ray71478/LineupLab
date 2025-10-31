/**
 * Home Page - Modern, Dynamic Landing Page
 *
 * Clean landing page inspired by Factory.ai
 * Focus: Dynamic typography, visual hierarchy, modern animations
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  Stack,
  Button,
  useTheme,
  useMediaQuery,
  alpha,
} from '@mui/material';
import { AuroraBackground, BackgroundBeams } from '../components/ui/index';

export const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const handleNavigate = (route: string) => {
    navigate(route);
  };

  return (
    <AuroraBackground intensity={0.12}>
      <BackgroundBeams beamCount={3} intensity={0.03}>
        <Box
          sx={{
            minHeight: '100vh',
            backgroundColor: '#000000',
            color: '#ffffff',
            position: 'relative',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
          }}
        >
          {/* Hero Content */}
          <Container
            maxWidth="lg"
            sx={{
              position: 'relative',
              zIndex: 1,
              textAlign: 'center',
              px: { xs: 2, sm: 4, md: 6 },
              pt: { xs: 2, sm: 4, md: 6 },
            }}
          >
            {/* Main Heading - Dynamic Typography */}
            <Box sx={{ mb: { xs: 3, sm: 4, md: 5 } }}>
              <Typography
                variant="h1"
                sx={{
                  fontSize: { xs: '3rem', sm: '4.5rem', md: '6rem' },
                  fontWeight: 900,
                  letterSpacing: '-0.04em',
                  lineHeight: 1.05,
                  mb: 1.5,
                  animation: 'fadeInUp 0.8s ease-out 0.2s both',
                  '@keyframes fadeInUp': {
                    from: {
                      opacity: 0,
                      transform: 'translateY(30px)',
                    },
                    to: {
                      opacity: 1,
                      transform: 'translateY(0)',
                    },
                  },
                }}
              >
                {/* Split heading with enhanced effects */}
                <Box
                  component="span"
                  sx={{
                    display: 'block',
                    color: '#ffffff',
                    position: 'relative',
                    textShadow: '0 0 30px rgba(255, 107, 53, 0.3)',
                    mb: 0.5,
                  }}
                >
                  Build Winning
                </Box>
                <Box
                  component="span"
                  sx={{
                    display: 'block',
                    position: 'relative',
                    background: 'linear-gradient(135deg, #ff6b35 0%, #ffa05c 50%, #ff6b35 100%)',
                    backgroundSize: '200% 200%',
                    backgroundClip: 'text',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    animation: 'gradientShift 3s ease infinite',
                    '@keyframes gradientShift': {
                      '0%, 100%': {
                        backgroundPosition: '0% 50%',
                      },
                      '50%': {
                        backgroundPosition: '100% 50%',
                      },
                    },
                    textShadow: '0 0 40px rgba(255, 107, 53, 0.4)',
                    '&::after': {
                      content: '""',
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      bottom: 0,
                      background: 'linear-gradient(135deg, rgba(255, 107, 53, 0.3) 0%, transparent 50%)',
                      borderRadius: '4px',
                      filter: 'blur(20px)',
                      zIndex: -1,
                    },
                  }}
                >
                  DFS Lineups
                </Box>
              </Typography>

              {/* Enhanced Subtitle */}
              <Typography
                variant="body1"
                sx={{
                  fontSize: { xs: '1.125rem', sm: '1.375rem', md: '1.625rem' },
                  fontWeight: 400,
                  color: '#b0b0b0',
                  maxWidth: '720px',
                  mx: 'auto',
                  lineHeight: 1.6,
                  mb: { xs: 4, sm: 6, md: 7 },
                  animation: 'fadeInUp 0.8s ease-out 0.4s both',
                  '@keyframes fadeInUp': {
                    from: {
                      opacity: 0,
                      transform: 'translateY(30px)',
                    },
                    to: {
                      opacity: 1,
                      transform: 'translateY(0)',
                    },
                  },
                  position: 'relative',
                  '&::before': {
                    content: '""',
                    position: 'absolute',
                    left: '50%',
                    top: -20,
                    transform: 'translateX(-50%)',
                    width: '60px',
                    height: '2px',
                    background: 'linear-gradient(90deg, transparent, #ff6b35, transparent)',
                    borderRadius: '2px',
                  },
                }}
              >
                Optimize your fantasy strategy with{' '}
                <Box
                  component="span"
                  sx={{
                    color: '#ff6b35',
                    fontWeight: 600,
                    position: 'relative',
                    '&::after': {
                      content: '""',
                      position: 'absolute',
                      bottom: 2,
                      left: 0,
                      right: 0,
                      height: '2px',
                      background: `linear-gradient(90deg, transparent, ${alpha('#ff6b35', 0.4)}, transparent)`,
                      borderRadius: '1px',
                    },
                  }}
                >
                  real-time data
                </Box>
                {' '}analysis and{' '}
                <Box
                  component="span"
                  sx={{
                    color: '#ff6b35',
                    fontWeight: 600,
                    position: 'relative',
                    '&::after': {
                      content: '""',
                      position: 'absolute',
                      bottom: 2,
                      left: 0,
                      right: 0,
                      height: '2px',
                      background: `linear-gradient(90deg, transparent, ${alpha('#ff6b35', 0.4)}, transparent)`,
                      borderRadius: '1px',
                    },
                  }}
                >
                  intelligent lineup generation
                </Box>
              </Typography>
            </Box>

            {/* CTA Button */}
            <Button
              onClick={() => handleNavigate('/lineups')}
              sx={{
                px: { xs: 4, sm: 5, md: 6 },
                py: { xs: 2, sm: 2.5, md: 3 },
                borderRadius: '12px',
                fontSize: { xs: '1.0625rem', sm: '1.125rem', md: '1.25rem' },
                fontWeight: 700,
                textTransform: 'none',
                background: 'linear-gradient(135deg, #ff6b35 0%, #ffa05c 100%)',
                color: '#ffffff',
                border: 'none',
                cursor: 'pointer',
                boxShadow: `0 20px 40px ${alpha('#ff6b35', 0.25)}`,
                transition: 'all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)',
                animation: 'fadeInUp 0.8s ease-out 0.6s both',
                '@keyframes fadeInUp': {
                  from: {
                    opacity: 0,
                    transform: 'translateY(30px)',
                  },
                  to: {
                    opacity: 1,
                    transform: 'translateY(0)',
                  },
                },
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: `0 30px 60px ${alpha('#ff6b35', 0.35)}`,
                },
                '&:active': {
                  transform: 'translateY(-2px)',
                },
              }}
            >
              Start Building Lineups
            </Button>
          </Container>
        </Box>
      </BackgroundBeams>
    </AuroraBackground>
  );
};

export default HomePage;
