/**
 * Not Found Page (404)
 * Displayed when user navigates to unknown route
 */

import React from 'react'
import { Container, Box, Typography, Button } from '@mui/material'
import { useNavigate } from 'react-router-dom'

export const NotFoundPage: React.FC = () => {
  const navigate = useNavigate()

  return (
    <Container maxWidth="lg">
      <Box
        sx={{
          py: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '60vh',
        }}
      >
        <Typography variant="h1" sx={{ fontWeight: 700, mb: 2, fontSize: '4rem' }}>
          404
        </Typography>
        <Typography variant="h4" sx={{ fontWeight: 600, mb: 2 }}>
          Page Not Found
        </Typography>
        <Typography variant="body1" sx={{ color: 'text.secondary', mb: 4 }}>
          The page you are looking for does not exist.
        </Typography>
        <Button
          variant="contained"
          color="primary"
          onClick={() => navigate('/dashboard')}
          sx={{ textTransform: 'none', px: 4, py: 1.5 }}
        >
          Return to Dashboard
        </Button>
      </Box>
    </Container>
  )
}

export default NotFoundPage
