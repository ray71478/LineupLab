/**
 * Home Page - Modern Landing Page
 * 
 * Ultra-modern landing page inspired by Factory.ai and modern SaaS products
 * Designed for tech-savvy users who appreciate clean, sophisticated interfaces
 * Focus: Maximum whitespace, refined typography, subtle interactions
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActionArea,
  Stack,
  useTheme,
  useMediaQuery,
  alpha,
} from '@mui/material';
import ScienceIcon from '@mui/icons-material/Science';
import GroupIcon from '@mui/icons-material/Group';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import BarChartIcon from '@mui/icons-material/BarChart';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import { AuroraBackground, Sparkles, TextShimmer, BackgroundBeams, MovingBorder } from '../components/ui';

interface FeatureCard {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  route: string;
  enabled: boolean;
}

export const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));

  const features: FeatureCard[] = [
    {
      id: 'players',
      title: 'Player Management',
      description: 'Manage your player database, review stats, and handle data imports with intelligent matching.',
      icon: <GroupIcon />,
      route: '/players',
      enabled: true,
    },
    {
      id: 'lineups',
      title: 'Lineup Builder',
      description: 'Build optimal lineups using advanced algorithms and real-time data analysis.',
      icon: <EmojiEventsIcon />,
      route: '/lineups',
      enabled: false,
    },
    {
      id: 'smart-score',
      title: 'Smart Score',
      description: 'AI-powered player scoring system that helps you identify the best value picks.',
      icon: <ScienceIcon />,
      route: '/smart-score',
      enabled: true,
    },
    {
      id: 'analytics',
      title: 'Analytics Dashboard',
      description: 'Comprehensive analytics and insights to track performance and trends.',
      icon: <BarChartIcon />,
      route: '/dashboard',
      enabled: false,
    },
  ];

  const handleCardClick = (route: string, enabled: boolean) => {
    if (enabled) {
      navigate(route);
    }
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
          }}
        >
          <Container
            maxWidth="lg"
            sx={{
              position: 'relative',
              zIndex: 1,
              py: { xs: 8, sm: 12, md: 16 },
              px: { xs: 3, sm: 4, md: 6 },
            }}
          >
            {/* Hero Section */}
            <Box
              sx={{
                textAlign: 'center',
                mb: { xs: 10, sm: 14, md: 16 },
                maxWidth: '900px',
                mx: 'auto',
              }}
            >
              {/* Logo/Icon with Sparkles */}
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'center',
                  mb: 4,
                }}
              >
                <Sparkles count={8} size={3} color="#ff6b35">
                  <Box
                    sx={{
                      width: { xs: 64, sm: 80, md: 96 },
                      height: { xs: 64, sm: 80, md: 96 },
                      borderRadius: '50%',
                      backgroundColor: alpha('#ff6b35', 0.08),
                      border: `1px solid ${alpha('#ff6b35', 0.2)}`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                      '&:hover': {
                        backgroundColor: alpha('#ff6b35', 0.12),
                        borderColor: alpha('#ff6b35', 0.4),
                        transform: 'scale(1.05)',
                      },
                    }}
                  >
                    <ScienceIcon
                      sx={{
                        fontSize: { xs: 32, sm: 40, md: 48 },
                        color: '#ff6b35',
                      }}
                    />
                  </Box>
                </Sparkles>
              </Box>

              {/* Title with Shimmer Effect */}
              <TextShimmer
                variant="h1"
                enabled={!isMobile}
                sx={{
                  fontSize: { xs: '3rem', sm: '4rem', md: '5.5rem' },
                  fontWeight: 800,
                  mb: 3,
                  letterSpacing: '-0.03em',
                  lineHeight: 1.1,
                  color: '#ffffff',
                  display: 'block',
                }}
              >
                Lineup Lab
              </TextShimmer>

          {/* Subtitle */}
          <Typography
            variant="h2"
            sx={{
              fontSize: { xs: '1.25rem', sm: '1.5rem', md: '1.75rem' },
              fontWeight: 400,
              color: '#a0a0a0',
              maxWidth: '700px',
              mx: 'auto',
              mb: 3,
              lineHeight: 1.5,
            }}
          >
            DFS Lineup Optimization Platform
          </Typography>

          {/* Description */}
          <Typography
            variant="body1"
            sx={{
              fontSize: { xs: '1rem', sm: '1.125rem', md: '1.25rem' },
              color: '#666666',
              maxWidth: '650px',
              mx: 'auto',
              lineHeight: 1.7,
              fontWeight: 300,
            }}
          >
            Build winning lineups with data-driven insights and intelligent player analysis
          </Typography>
        </Box>

            {/* Feature Cards Grid */}
            <Grid
              container
              spacing={{ xs: 3, sm: 4, md: 5 }}
              sx={{
                maxWidth: '1200px',
                mx: 'auto',
              }}
            >
              {features.map((feature, index) => (
                <Grid item xs={12} sm={6} key={feature.id}>
                  {feature.enabled ? (
                    <MovingBorder
                      borderColor="#ff6b35"
                      borderWidth={1}
                      borderRadius={16}
                      sx={{
                        height: '100%',
                        opacity: feature.enabled ? 1 : 0.5,
                      }}
                    >
                      <Card
                        sx={{
                          height: '100%',
                          backgroundColor: '#0a0a0a',
                          border: 'none',
                          borderRadius: '15px',
                          position: 'relative',
                          overflow: 'visible',
                          cursor: 'pointer',
                          transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                          '&:hover': {
                            transform: 'translateY(-8px)',
                            boxShadow: `0 20px 40px ${alpha('#ff6b35', 0.2)}`,
                            backgroundColor: '#0f0f0f',
                          },
                        }}
                      >
                        <CardActionArea
                          onClick={() => handleCardClick(feature.route, feature.enabled)}
                          sx={{
                            height: '100%',
                            '&:hover': {
                              backgroundColor: 'transparent',
                            },
                          }}
                        >
                          <CardContent
                            sx={{
                              p: { xs: 4, sm: 5, md: 6 },
                              height: '100%',
                              display: 'flex',
                              flexDirection: 'column',
                            }}
                          >
                            <Stack spacing={3}>
                              {/* Icon with Sparkles */}
                              <Sparkles count={4} size={2} color="#ff6b35">
                                <Box
                                  sx={{
                                    width: 56,
                                    height: 56,
                                    borderRadius: '12px',
                                    backgroundColor: alpha('#ff6b35', 0.1),
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    transition: 'all 0.3s ease',
                                    '.MuiCard-root:hover &': {
                                      backgroundColor: alpha('#ff6b35', 0.15),
                                      transform: 'scale(1.1)',
                                    },
                                  }}
                                >
                                  {React.cloneElement(feature.icon as React.ReactElement, {
                                    sx: {
                                      fontSize: 28,
                                      color: '#ff6b35',
                                    },
                                  })}
                                </Box>
                              </Sparkles>

                              {/* Title and Arrow */}
                              <Box>
                                <Stack
                                  direction="row"
                                  alignItems="center"
                                  justifyContent="space-between"
                                  spacing={1}
                                  sx={{ mb: 2 }}
                                >
                                  <Typography
                                    variant="h4"
                                    sx={{
                                      fontWeight: 600,
                                      color: '#ffffff',
                                      fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' },
                                      letterSpacing: '-0.01em',
                                      lineHeight: 1.2,
                                    }}
                                  >
                                    {feature.title}
                                  </Typography>
                                  <ArrowForwardIcon
                                    sx={{
                                      fontSize: 24,
                                      color: '#ff6b35',
                                      transition: 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                                      '.MuiCard-root:hover &': {
                                        transform: 'translateX(6px)',
                                      },
                                    }}
                                  />
                                </Stack>

                                {/* Description */}
                                <Typography
                                  variant="body1"
                                  sx={{
                                    color: '#a0a0a0',
                                    lineHeight: 1.7,
                                    fontSize: { xs: '0.95rem', sm: '1rem', md: '1.0625rem' },
                                    fontWeight: 300,
                                  }}
                                >
                                  {feature.description}
                                </Typography>
                              </Box>
                            </Stack>
                          </CardContent>
                        </CardActionArea>
                      </Card>
                    </MovingBorder>
                  ) : (
                    <Card
                      sx={{
                        height: '100%',
                        backgroundColor: '#0a0a0a',
                        border: `1px solid ${alpha('#ffffff', 0.08)}`,
                        borderRadius: '16px',
                        position: 'relative',
                        overflow: 'visible',
                        opacity: 0.5,
                        cursor: 'default',
                      }}
                    >
                      <CardActionArea
                        onClick={() => handleCardClick(feature.route, feature.enabled)}
                        disabled={true}
                        sx={{
                          height: '100%',
                          '&:hover': {
                            backgroundColor: 'transparent',
                          },
                          '&.Mui-disabled': {
                            cursor: 'default',
                          },
                        }}
                      >
                        <CardContent
                          sx={{
                            p: { xs: 4, sm: 5, md: 6 },
                            height: '100%',
                            display: 'flex',
                            flexDirection: 'column',
                          }}
                        >
                          <Stack spacing={3}>
                            {/* Icon */}
                            <Box
                              sx={{
                                width: 56,
                                height: 56,
                                borderRadius: '12px',
                                backgroundColor: alpha('#ff6b35', 0.1),
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                              }}
                            >
                              {React.cloneElement(feature.icon as React.ReactElement, {
                                sx: {
                                  fontSize: 28,
                                  color: '#ff6b35',
                                },
                              })}
                            </Box>

                            {/* Title and Coming Soon Badge */}
                            <Box>
                              <Stack
                                direction="row"
                                alignItems="center"
                                justifyContent="space-between"
                                spacing={1}
                                sx={{ mb: 2 }}
                              >
                                <Typography
                                  variant="h4"
                                  sx={{
                                    fontWeight: 600,
                                    color: '#ffffff',
                                    fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' },
                                    letterSpacing: '-0.01em',
                                    lineHeight: 1.2,
                                  }}
                                >
                                  {feature.title}
                                </Typography>
                              </Stack>

                              {/* Coming Soon Badge */}
                              <Box sx={{ mb: 2 }}>
                                <Typography
                                  variant="caption"
                                  sx={{
                                    px: 2,
                                    py: 0.75,
                                    borderRadius: '6px',
                                    backgroundColor: alpha('#ffffff', 0.08),
                                    color: '#a0a0a0',
                                    fontSize: '0.75rem',
                                    fontWeight: 500,
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.08em',
                                    display: 'inline-block',
                                  }}
                                >
                                  Coming Soon
                                </Typography>
                              </Box>

                              {/* Description */}
                              <Typography
                                variant="body1"
                                sx={{
                                  color: '#a0a0a0',
                                  lineHeight: 1.7,
                                  fontSize: { xs: '0.95rem', sm: '1rem', md: '1.0625rem' },
                                  fontWeight: 300,
                                }}
                              >
                                {feature.description}
                              </Typography>
                            </Box>
                          </Stack>
                        </CardContent>
                      </CardActionArea>
                    </Card>
                  )}
                </Grid>
              ))}
            </Grid>
          </Container>
        </Box>
      </BackgroundBeams>
    </AuroraBackground>
  );
};

export default HomePage;
