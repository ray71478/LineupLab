## CSS best practices

### General Principles
- **Consistent Methodology**: Use Material-UI (MUI) theming system exclusively; avoid custom CSS files
- **Avoid Overriding Framework Styles**: Work with MUI's patterns and customization APIs rather than fighting against them
- **Maintain Design System**: Follow Cortex's Material Design 3 dark mode design tokens
- **Minimize Custom CSS**: Leverage MUI components and `sx` prop for styling; avoid separate CSS files
- **Performance Considerations**: MUI handles CSS-in-JS optimization automatically

### Cortex Design System

#### Color Palette (Dark Mode)
```typescript
// theme.ts
import { createTheme } from '@mui/material/styles';

export const cortexTheme = createTheme({
  palette: {
    mode: 'dark',
    background: {
      default: '#0f0f1a',  // Deep navy/black
      paper: '#1a1a2e',    // Surface panels
    },
    primary: {
      main: '#00d4ff',     // Cyan - data emphasis
      light: '#33ddff',
      dark: '#00a8cc',
    },
    secondary: {
      main: '#7c3aed',     // Purple - AI features
      light: '#9d5eff',
      dark: '#5b21b6',
    },
    text: {
      primary: '#e5e7eb',  // Light gray
      secondary: '#9ca3af',
    },
    success: {
      main: '#10b981',     // Green
    },
    warning: {
      main: '#f59e0b',     // Amber
    },
    error: {
      main: '#ef4444',     // Red
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: { fontSize: '2.5rem', fontWeight: 700 },
    h2: { fontSize: '2rem', fontWeight: 600 },
    h3: { fontSize: '1.75rem', fontWeight: 600 },
    h4: { fontSize: '1.5rem', fontWeight: 600 },
    h5: { fontSize: '1.25rem', fontWeight: 600 },
    h6: { fontSize: '1rem', fontWeight: 600 },
    body1: { fontSize: '1rem', lineHeight: 1.5 },
    body2: { fontSize: '0.875rem', lineHeight: 1.5 },
  },
  spacing: 8, // Base spacing unit (8px)
  shape: {
    borderRadius: 8, // Rounded corners for panels
  },
});
```

#### Using MUI Theme
```typescript
// App.tsx
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { cortexTheme } from './theme';

function App() {
  return (
    <ThemeProvider theme={cortexTheme}>
      <CssBaseline /> {/* Normalize CSS + dark mode background */}
      {/* Your app components */}
    </ThemeProvider>
  );
}
```

#### Styling Components with `sx` Prop
```typescript
// GOOD: Use sx prop for component-specific styles
<Box
  sx={{
    backgroundColor: 'background.paper',
    borderRadius: 2,
    padding: 3,
    boxShadow: 3,
  }}
>
  <Typography variant="h5" color="primary">
    Player Pool
  </Typography>
</Box>

// BAD: Don't create separate CSS files
// ❌ Avoid: import './PlayerPool.css'
```

#### Custom Component Styling
```typescript
// For reusable styled components, use MUI's styled() API
import { styled } from '@mui/material/styles';
import { Paper } from '@mui/material';

const StyledCard = styled(Paper)(({ theme }) => ({
  backgroundColor: theme.palette.background.paper,
  padding: theme.spacing(3),
  borderRadius: theme.shape.borderRadius,
  border: `1px solid ${theme.palette.divider}`,
  '&:hover': {
    boxShadow: theme.shadows[6],
    borderColor: theme.palette.primary.main,
  },
}));

// Usage
<StyledCard>
  <Typography>Content</Typography>
</StyledCard>
```

#### Responsive Styling
```typescript
// Use theme breakpoints for responsive design
<Box
  sx={{
    display: 'flex',
    flexDirection: { xs: 'column', md: 'row' }, // Mobile: column, Desktop: row
    gap: { xs: 2, md: 4 },
    padding: { xs: 2, sm: 3, md: 4 },
  }}
>
  {/* Content */}
</Box>
```

#### Typography Consistency
```typescript
// Use MUI Typography variants consistently
<Typography variant="h4" component="h1" gutterBottom>
  Week 9 Player Pool
</Typography>

<Typography variant="body1" color="text.secondary">
  153 players loaded
</Typography>

<Typography variant="body2" color="text.secondary">
  Last updated: 2 minutes ago
</Typography>
```

#### Icons
```typescript
// Use Material Icons from @mui/icons-material
import { Upload, Download, Settings, TrendingUp } from '@mui/icons-material';

<Button startIcon={<Upload />} variant="contained">
  Import Data
</Button>
```

### Component-Specific Patterns

#### Tables (TanStack Table + MUI)
```typescript
import { Table, TableBody, TableCell, TableHead, TableRow } from '@mui/material';

<Table sx={{ minWidth: 650 }}>
  <TableHead>
    <TableRow>
      <TableCell sx={{ fontWeight: 600 }}>Player</TableCell>
      <TableCell align="right">Salary</TableCell>
      <TableCell align="right">Smart Score</TableCell>
    </TableRow>
  </TableHead>
  <TableBody>
    {players.map((player) => (
      <TableRow
        key={player.player_key}
        sx={{
          '&:hover': { backgroundColor: 'action.hover' },
          cursor: 'pointer',
        }}
      >
        <TableCell>{player.name}</TableCell>
        <TableCell align="right">${player.salary.toLocaleString()}</TableCell>
        <TableCell align="right">{player.smart_score.toFixed(2)}</TableCell>
      </TableRow>
    ))}
  </TableBody>
</Table>
```

#### Forms (React Hook Form + MUI)
```typescript
import { TextField, Slider, Button } from '@mui/material';
import { Controller, useForm } from 'react-hook-form';

<Controller
  name="projectionWeight"
  control={control}
  render={({ field }) => (
    <Slider
      {...field}
      min={0}
      max={2}
      step={0.1}
      marks
      valueLabelDisplay="auto"
      sx={{ color: 'primary.main' }}
    />
  )}
/>
```

#### Loading States
```typescript
import { CircularProgress, Skeleton } from '@mui/material';

// Loading spinner
<Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
  <CircularProgress />
</Box>

// Skeleton placeholders
<Skeleton variant="rectangular" width="100%" height={60} />
<Skeleton variant="text" width="80%" />
```

### Performance Best Practices

**Avoid Inline Style Objects:**
```typescript
// BAD: Creates new object on every render
<Box style={{ padding: 16, backgroundColor: '#1a1a2e' }}>

// GOOD: Use sx prop (MUI optimizes this)
<Box sx={{ p: 2, bgcolor: 'background.paper' }}>
```

**Memoize Styled Components:**
```typescript
// For components that re-render frequently
import { memo } from 'react';

const PlayerRow = memo(({ player }) => (
  <TableRow>
    <TableCell>{player.name}</TableCell>
  </TableRow>
));
```

**Use Theme Tokens:**
```typescript
// GOOD: Use theme tokens (consistent, maintainable)
<Box sx={{ color: 'primary.main', bgcolor: 'background.paper' }}>

// BAD: Hardcode colors (breaks theming)
<Box sx={{ color: '#00d4ff', bgcolor: '#1a1a2e' }}>
```

### Mobile-Specific Considerations

**Touch-Friendly Sizing:**
```typescript
// Minimum 44x44px tap targets
<Button
  sx={{
    minWidth: 44,
    minHeight: 44,
    padding: { xs: 1.5, md: 1 }, // Larger padding on mobile
  }}
>
  Generate
</Button>
```

**Responsive Font Sizes:**
```typescript
// Use responsive typography
<Typography
  variant="h4"
  sx={{
    fontSize: { xs: '1.5rem', md: '2rem' }, // Smaller on mobile
  }}
>
  Smart Score Configuration
</Typography>
```

### No Custom CSS Files
- **Do NOT create**: `*.css`, `*.scss`, `*.module.css` files
- **Use instead**: MUI's `sx` prop, `styled()` API, or theme customization
- **Exception**: Global CSS reset is handled by MUI's `<CssBaseline />` component
