/**
 * MainLayout Component
 *
 * Ultra-modern, minimal header design
 * Focus: Clean, elegant, minimal visual weight
 * Inspired by Factory.ai and modern SaaS products
 */

import React, { ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Box,
  Stack,
  useMediaQuery,
  useTheme,
  Typography,
  alpha,
} from '@mui/material';
import { LineupLabIcon } from './LineupLabIcon';

export interface MainLayoutProps {
  children?: ReactNode;
  logo?: ReactNode;
  menuItems?: ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({
  children,
  logo,
  menuItems,
}) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const isDesktop = useMediaQuery(theme.breakpoints.up('md'));
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const handleLogoClick = () => {
    navigate('/');
  };

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100vh',
        backgroundColor: '#000000',
        color: '#ffffff',
      }}
    >
      {/* Header/AppBar */}
      <AppBar
        position="static"
        elevation={0}
        sx={{
          backgroundColor: '#000000',
          borderBottom: `1px solid ${alpha('#ffffff', 0.08)}`,
          boxShadow: 'none',
          backdropFilter: 'blur(10px)',
        }}
      >
        <Toolbar
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            minHeight: { xs: 64, sm: 72 },
            px: { xs: 3, sm: 4, md: 6 },
            maxWidth: '1400px',
            mx: 'auto',
            width: '100%',
          }}
        >
          {/* Left Side: Logo/Branding */}
          <Stack
            direction="row"
            alignItems="center"
            spacing={1.5}
            onClick={handleLogoClick}
            sx={{
              minWidth: 'fit-content',
              cursor: 'pointer',
              transition: 'opacity 0.2s ease',
              '&:hover': {
                opacity: 0.8,
              },
            }}
          >
            {logo ? (
              logo
            ) : (
              <>
                <Box
                  sx={{
                    width: 36,
                    height: 36,
                    borderRadius: '10px',
                    backgroundColor: alpha('#ff6b35', 0.1),
                    border: `1px solid ${alpha('#ff6b35', 0.2)}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    transition: 'all 0.2s ease',
                    position: 'relative',
                    overflow: 'hidden',
                    '&::before': {
                      content: '""',
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      bottom: 0,
                      background: `linear-gradient(135deg, ${alpha('#ff6b35', 0.15)} 0%, transparent 100%)`,
                      pointerEvents: 'none',
                    },
                    '&:hover': {
                      borderColor: alpha('#ff6b35', 0.4),
                      backgroundColor: alpha('#ff6b35', 0.15),
                      transform: 'translateY(-1px)',
                      boxShadow: `0 4px 12px ${alpha('#ff6b35', 0.2)}`,
                    },
                  }}
                >
                  <LineupLabIcon size={22} color="#ff6b35" />
                </Box>
                <Typography
                  variant="h6"
                  sx={{
                    fontWeight: 600,
                    fontSize: { xs: '1rem', sm: '1.125rem' },
                    letterSpacing: '-0.01em',
                    color: '#ffffff',
                  }}
                >
                  Lineup Lab
                </Typography>
              </>
            )}
          </Stack>

          {/* Right Side: Menu Items */}
          {menuItems && (
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: { xs: 1.5, sm: 2 },
                marginLeft: 'auto',
              }}
            >
              {menuItems}
            </Box>
          )}
        </Toolbar>
      </AppBar>

      {/* Main Content Area */}
      <Box
        component="main"
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          width: '100%',
          backgroundColor: '#000000',
        }}
      >
        {children}
      </Box>
    </Box>
  );
};

export default MainLayout;
