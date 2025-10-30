/**
 * Dashboard Page
 * Main dashboard view for the Cortex DFS Lineup Optimizer
 */

import React from 'react'
import { Container, Box, Typography } from '@mui/material'

export const DashboardPage: React.FC = () => {
  return (
    <Container maxWidth="lg">
      <Box sx={{ py: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, mb: 2 }}>
          Dashboard
        </Typography>
        <Typography variant="body1" sx={{ color: 'text.secondary' }}>
          Dashboard - Coming Soon
        </Typography>
      </Box>
    </Container>
  )
}

export default DashboardPage
