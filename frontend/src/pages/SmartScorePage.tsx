/**
 * Smart Score Page
 * Smart Score configuration and weighting
 */

import React from 'react'
import { Container, Box, Typography } from '@mui/material'

export const SmartScorePage: React.FC = () => {
  return (
    <Container maxWidth="lg">
      <Box sx={{ py: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, mb: 2 }}>
          Smart Score
        </Typography>
        <Typography variant="body1" sx={{ color: 'text.secondary' }}>
          Smart Score - Coming Soon
        </Typography>
      </Box>
    </Container>
  )
}

export default SmartScorePage
