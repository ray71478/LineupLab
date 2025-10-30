/**
 * Lineups Page
 * Lineup generator and management
 */

import React from 'react'
import { Container, Box, Typography } from '@mui/material'

export const LineupsPage: React.FC = () => {
  return (
    <Container maxWidth="lg">
      <Box sx={{ py: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, mb: 2 }}>
          Lineup Generator
        </Typography>
        <Typography variant="body1" sx={{ color: 'text.secondary' }}>
          Lineup Generator - Coming Soon
        </Typography>
      </Box>
    </Container>
  )
}

export default LineupsPage
