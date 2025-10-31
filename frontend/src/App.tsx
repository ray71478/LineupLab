/**
 * Navigation Menu Component
 * Displays navigation links in the header
 */
const NavigationMenu: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()

  const isActive = (path: string) => location.pathname === path

  const navLinks = [
    { label: 'Smart Score', path: '/smart-score' },
    { label: 'Lineups', path: '/lineups' },
  ]

  return (
    <Stack direction="row" spacing={1} sx={{ display: { xs: 'none', md: 'flex' } }}>
      {navLinks.map((link) => (
        <Button
          key={link.path}
          onClick={() => !link.disabled && navigate(link.path)}
          disabled={link.disabled}
          sx={{
            color: isActive(link.path) ? '#ff6b35' : '#ffffff',
            fontWeight: isActive(link.path) ? 600 : 400,
            textTransform: 'none',
            fontSize: '0.9375rem',
            px: 2,
            py: 1,
            borderRadius: '8px',
            '&:hover': {
              backgroundColor: 'rgba(255, 107, 53, 0.1)',
            },
            '&.Mui-disabled': {
              opacity: 0.5,
            },
          }}
        >
          {link.label}
        </Button>
      ))}
    </Stack>
  )
}

/**
 * Main Application Component
 *
 * Integrates:
 * - React Router v6 for client-side routing
 * - MainLayout for consistent header and navigation
 * - Clean week selector in header
 * - Error boundary for graceful error handling
 * - Lazy-loaded route components for code splitting
 */

import React, { Suspense, useEffect } from 'react'
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom'
import { Box, CircularProgress, Button, Stack } from '@mui/material'
import MainLayout from './components/layout/MainLayout'
import ImportDataButton from '@/components/import/ImportDataButton'
import { RefreshMySportsFeedsButton } from '@/components/refresh/RefreshMySportsFeedsButton'
import WeekSelector from '@/components/layout/WeekSelector'
import { useWeeks } from '@/hooks/useWeeks'
import { useWeekStore } from '@/store/weekStore'
import { useCurrentWeek } from '@/hooks/useCurrentWeek'

// Lazy load page components for code splitting
const HomePage = React.lazy(() => import('./pages/HomePage'))
const PlayersPage = React.lazy(() => import('./pages/PlayersPage'))
const SmartScorePage = React.lazy(() => import('./pages/SmartScorePage'))
const PlayerSelectionPage = React.lazy(() => import('./pages/PlayerSelectionPage'))
const LineupsPage = React.lazy(() => import('./pages/LineupsPage'))
const NotFoundPage = React.lazy(() => import('./pages/NotFoundPage'))

// Loading fallback component
const LoadingFallback: React.FC = () => (
  <Box
    sx={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '60vh',
    }}
  >
    <CircularProgress sx={{ color: '#ff6b35' }} />
  </Box>
)

/**
 * Main App Component
 *
 * Provides:
 * - Layout wrapper with header containing simplified WeekSelector and ImportDataButton
 * - Route definitions for all main pages
 * - Default route shows HomePage (landing page)
 * - Error boundary via Suspense
 */
function App() {
  const currentYear = useWeekStore((state) => state.currentYear)
  const currentWeekNumber = useWeekStore((state) => state.currentWeek)
  const setCurrentWeek = useWeekStore((state) => state.setCurrentWeek)
  const weeks = useWeekStore((state) => state.weeks)

  const { isLoading, error } = useWeeks(currentYear)
  const { data: currentWeekData } = useCurrentWeek()

  // Auto-select a week when weeks are loaded and no week is selected
  useEffect(() => {
    if (!isLoading && weeks && weeks.length > 0 && !currentWeekNumber) {
      console.log('Auto-selecting week. Available weeks:', weeks.length);
      // Try to select the current active week, or fallback to first week
      const activeWeek = weeks.find((w) => w.status === 'active')
      const weekToSelect = activeWeek?.week_number || weeks[0]?.week_number

      if (weekToSelect) {
        console.log('Setting currentWeek to:', weekToSelect);
        setCurrentWeek(weekToSelect)
      }
    }
  }, [isLoading, weeks, currentWeekNumber, setCurrentWeek])

  const handleImportSuccess = (importId: string) => {
    console.log('Import successful:', importId)
  }

  const handleImportError = (error: string) => {
    console.error('Import failed:', error)
  }

  // Loading state
  if (isLoading) {
    return <LoadingFallback />
  }

  // Error state
  if (error) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh',
          backgroundColor: '#000000',
          color: '#ffffff',
          px: 3,
        }}
      >
        <p>Error loading application: {error}</p>
      </Box>
    )
  }

  // Render main layout with routes
  return (
    <MainLayout
      menuItems={
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <NavigationMenu />
          <WeekSelector onWeekChange={undefined} showMetadata={false} />
          <RefreshMySportsFeedsButton onSuccess={handleImportSuccess} onError={handleImportError} />
          <ImportDataButton onSuccess={handleImportSuccess} onError={handleImportError} />
        </Box>
      }
    >
      <Suspense fallback={<LoadingFallback />}>
        <Routes>
          {/* Default route shows home page */}
          <Route path="/" element={<HomePage />} />

          {/* Main routes */}
          <Route path="/players" element={<PlayersPage />} />
          <Route path="/smart-score" element={<SmartScorePage />} />
          <Route path="/player-selection" element={<PlayerSelectionPage />} />
          <Route path="/lineups" element={<LineupsPage />} />

          {/* Legacy redirect */}
          <Route path="/dashboard" element={<Navigate to="/" replace />} />

          {/* 404 - Not found */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Suspense>
    </MainLayout>
  )
}

export default App
