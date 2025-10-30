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
            }}
          >
            {/* Main Heading - Dynamic Typography */}
            <Box sx={{ mb: { xs: 3, sm: 4, md: 5 } }}>
              <Typography
                variant="h1"
                sx={{
                  fontSize: { xs: '2.75rem', sm: '4rem', md: '5.5rem' },
                  fontWeight: 900,
                  letterSpacing: '-0.03em',
                  lineHeight: 1.1,
                  color: '#ffffff',
                  mb: 2,
                  // Add subtle animation on load
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
                {/* Split heading for visual interest */}
                <span>Build Winning</span>
                <br />
                <span
                  style={{
                    background: 'linear-gradient(135deg, #ff6b35 0%, #ffa05c 100%)',
                    backgroundClip: 'text',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                  }}
                >
                  DFS Lineups
                </span>
              </Typography>

              {/* Subtitle with better visual hierarchy */}
              <Typography
                variant="body1"
                sx={{
                  fontSize: { xs: '1.125rem', sm: '1.375rem', md: '1.5rem' },
                  fontWeight: 400,
                  color: '#a0a0a0',
                  maxWidth: '800px',
                  mx: 'auto',
                  lineHeight: 1.7,
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
                }}
              >
                Leverage AI-powered insights and real-time data analysis to optimize your fantasy sports strategy
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
